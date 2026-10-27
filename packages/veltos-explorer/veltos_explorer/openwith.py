"""VeltOS "open with" window: Windows 11's "Select an app to open this
file" instead of KDE's dialog.

    veltos-explorer --open-with FILE
    veltos-explorer --open-with --choose [--type MIME] [--choices A,B] [FILE]

Lists the installed apps that claim the file's type (then every app on
"More apps"); "Always" records the app as the default for the type in the
user's mimeapps.list (the freedesktop way, which Settings > Default apps
shows too), "Just once" only opens the file with it. "Choose an app on
your PC" picks any program file, as on Windows 11: it gets a hidden
launcher of its own (choose_program) and joins the list.

--choose only answers: the chosen app's desktop file name goes to standard
output (an empty line when cancelled) and the caller opens the file. That
is how Firefox's "Choose an application" (veltos-desktop's Firefox
autoconfig, which replaces GTK's dialog) and the desktop portal's
AppChooser (portal.py) use this window (product owner, 2026-10-27).
"""

import json
import os
import re
import sys
from pathlib import Path

from PySide6.QtCore import Property, QMimeDatabase, QObject, QProcess, QUrl, Signal, Slot

from . import ops, places, strings

QML_DIR = Path(__file__).resolve().parent / "qml"


def all_applications(lang="en"):
    """Every visible app ([{id, name, icon, path}]), first one of a name wins."""
    seen, result = set(), []
    for directory in places.application_dirs():
        try:
            paths = sorted(directory.glob("*.desktop"))
        except OSError:
            continue
        for path in paths:
            if path.name in seen:
                continue
            seen.add(path.name)          # a hidden copy hides the original behind it
            entry = places.read_desktop_entry(path)
            # A handler hidden from Start (App Installer) only for its own types.
            if entry is None or (entry.get("NoDisplay") == "true" and entry.get(CHOSEN_KEY) != "true"):
                continue
            name = entry.get(f"Name[{lang}]") or entry.get("Name", path.stem)
            result.append({"id": path.name, "name": name, "icon": entry.get("Icon", ""), "path": str(path)})
    result.sort(key=lambda a: a["name"].casefold())
    return result


def set_default_app(mime, desktop_name, config_home=None):
    """Record `desktop_name` as the default app for `mime` in the user's
    mimeapps.list, keeping everything else in the file."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.desktop", desktop_name) or "/" not in mime:
        return False
    path = Path(config_home or places.config_home()) / "mimeapps.list"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = []
    out, group, done = [], None, False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            if group == "Default Applications" and not done:
                out.append(f"{mime}={desktop_name};")
                done = True
            group = stripped[1:-1]
        elif group == "Default Applications" and stripped.split("=", 1)[0].strip() == mime:
            if not done:
                out.append(f"{mime}={desktop_name};")
                done = True
            continue
        out.append(line)
    if not done:
        if group != "Default Applications":
            if out and out[-1].strip():
                out.append("")
            out.append("[Default Applications]")
        out.append(f"{mime}={desktop_name};")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return True


# The marker of launchers made for programs chosen with "Choose an app on
# your PC": hidden from Start (NoDisplay) but listed here
# (places.read_desktop_entry).
CHOSEN_KEY = "X-VeltOS-Chosen"


def desktop_quote(arg):
    """One Exec argument (Desktop Entry spec: quoted, with \\ " ` $ escaped;
    % doubled)."""
    arg = arg.replace("%", "%%")
    if re.fullmatch(r"[A-Za-z0-9_./+:@,=-]+", arg):
        return arg
    return '"' + re.sub(r'(["`$\\])', r"\\\1", arg) + '"'


def choose_program(path, mime, data_home=None):
    """A launcher for a program file the user picked ("Choose an app on your
    PC"): a .desktop file is used as it is (copied into the user's
    applications when it is elsewhere), an executable file gets a hidden
    launcher that opens files with it. Returns its desktop file name, or ""
    when the file is not a program."""
    path = Path(path)
    folder = Path(data_home or places.data_home()) / "applications"
    if path.suffix == ".desktop":
        entry = places.read_desktop_entry(path)
        if entry is None:
            return ""
        if any(path.parent == d for d in places.application_dirs()):
            return path.name
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / path.name
        target.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        return target.name
    if not path.is_file() or not os.access(path, os.X_OK):
        return ""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", path.stem).strip("-").lower() or "program"
    name = f"veltos-chosen-{slug}.desktop"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    number = 2
    while target.exists() and f"Exec={desktop_quote(str(path))} %F" not in target.read_text(encoding="utf-8",
                                                                                        errors="replace"):
        name = f"veltos-chosen-{slug}-{number}.desktop"
        target = folder / name
        number += 1
    types = set()
    if target.exists():
        for line in target.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("MimeType="):
                types.update(t for t in line[9:].split(";") if t)
    if mime and "/" in mime:
        types.add(mime)
    target.write_text("[Desktop Entry]\nType=Application\n"
                      f"Name={path.stem}\n"
                      f"Exec={desktop_quote(str(path))} %F\n"
                      "Icon=application-x-executable\n"
                      f"MimeType={''.join(t + ';' for t in sorted(types))}\n"
                      "NoDisplay=true\n"
                      f"{CHOSEN_KEY}=true\n", encoding="utf-8")
    return name


def app_for(desktop_name, lang="en"):
    """{id, name, icon, path} of an installed desktop file name, or None."""
    for directory in places.application_dirs():
        path = directory / desktop_name
        entry = places.read_desktop_entry(path)
        if entry:
            return {"id": desktop_name, "name": entry.get(f"Name[{lang}]") or entry.get("Name", path.stem),
                    "icon": entry.get("Icon", ""), "path": str(path)}
    return None


class Opener(QObject):
    """The apps for one file (or a file type), for OpenWith.qml."""

    changed = Signal()
    done = Signal()

    def __init__(self, path="", lang=None, start=ops.detached, config_home=None, parent=None, mime="",
                 choose=False, choices=(), out=None, data_home=None, picker=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.path = str(path or "")
        self.start = start
        self.config_home = config_home
        self.data_home = data_home
        self.choose = choose
        self.out = out or sys.stdout
        self.answered = False
        self._picker = picker or [sys.executable, "-m", "veltos_explorer", "--pick"]
        self._message = ""
        self._dark = read_dark_mode()
        database = QMimeDatabase()
        if mime:
            self.mime = mime
            suffix = database.mimeTypeForName(mime).preferredSuffix()
            self.suffix = os.path.splitext(self.path)[1] or ("." + suffix if suffix else "")
        else:
            self.mime = database.mimeTypeForFile(self.path).name()
            self.suffix = os.path.splitext(self.path)[1]
        claimed = places.applications_for(self.mime, self.lang)
        # The portal's candidates come first, in its order.
        first = []
        for choice in choices:
            name = choice if choice.endswith(".desktop") else choice + ".desktop"
            app = next((a for a in claimed if a["id"] == name), None) or app_for(name, self.lang)
            if app and app not in first:
                first.append(app)
        self.claimed = first + [a for a in claimed if a not in first]
        self._all = None
        self._more = not self.claimed
        self._selected = 0 if self.apps else -1

    def text(self, key):
        return strings.text(self.lang, key)

    # --- for QML ----------------------------------------------------------------------

    @Slot(str, result=str)
    def tr(self, key):
        return self.text(key)

    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(str, constant=True)
    def accentColor(self):
        from .app import Backend
        return Backend.read_accent_color()

    @Property(float, constant=True)
    def textScale(self):
        """Settings > Accessibility > Text size, as File Explorer reads it."""
        from .app import Backend
        return Backend.read_text_scale()

    @Property(str, constant=True)
    def heading(self):
        if self.suffix:
            return self.text("open_with_title").replace("{type}", self.suffix)
        return self.text("open_with_file").replace("{name}", os.path.basename(self.path))

    @Property(str, constant=True)
    def fileName(self):
        return os.path.basename(self.path)

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property("QVariantList", notify=changed)
    def apps(self):
        if self._more:
            if self._all is None:
                self._all = all_applications(self.lang)
            return self._all
        return self.claimed

    @Property(bool, notify=changed)
    def hasMore(self):
        return not self._more

    @Property(int, notify=changed)
    def selected(self):
        return self._selected

    @Slot(int)
    def select(self, index):
        self._selected = index
        self.changed.emit()

    @Slot()
    def showMore(self):
        chosen = self.apps[self._selected]["id"] if 0 <= self._selected < len(self.apps) else ""
        self._more = True
        apps = self.apps
        self._selected = next((i for i, a in enumerate(apps) if a["id"] == chosen), 0 if apps else -1)
        self.changed.emit()

    @Slot(int, bool)
    def open(self, index, always):
        apps = self.apps
        if not 0 <= index < len(apps):
            return
        app = apps[index]
        if always:
            set_default_app(self.mime, app["id"], self.config_home)
        if self.choose:
            self.answer(app["id"])
        else:
            command = places.exec_command(app["path"], [self.path])
            if command:
                self.start(command)
        self.done.emit()

    def answer(self, desktop_name):
        """--choose: tell the caller (once)."""
        if not self.answered:
            self.answered = True
            self.out.write(desktop_name + "\n")
            self.out.flush()

    @Slot()
    def cancel(self):
        if self.choose:
            self.answer("")
        self.done.emit()

    # --- "Choose an app on your PC" ------------------------------------------------------

    @Slot()
    def browse(self):
        """Opens the file dialog (Windows 11's, picker.py) in the programs'
        folder; the program chosen joins the list, selected."""
        process = QProcess(self)
        request = {"mode": "open", "title": self.text("choose_app_title"),
                   "accept_label": self.text("open_with"),
                   "current_folder": "/usr/bin" if os.path.isdir("/usr/bin") else str(Path.home())}

        def finished(_code, _status):
            data = bytes(process.readAllStandardOutput()).decode("utf-8", "replace").strip()
            process.deleteLater()
            try:
                paths = json.loads(data.splitlines()[-1]).get("paths", []) if data else []
            except (ValueError, AttributeError, IndexError):
                paths = []
            if paths:
                self.add_program(paths[0])

        process.finished.connect(finished)
        process.start(self._picker[0], self._picker[1:])
        process.write(json.dumps(request).encode())
        process.closeWriteChannel()

    @Slot(str)
    def add_program(self, path):
        name = choose_program(path, self.mime, self.data_home)
        if not name:
            self._message = self.text("not_a_program").replace("{name}", os.path.basename(path))
            self.changed.emit()
            return
        app = app_for(name, self.lang)
        if app is None:
            return
        self._message = ""
        apps = self.apps
        existing = next((i for i, a in enumerate(apps) if a["id"] == name), -1)
        if existing < 0:
            self.claimed.insert(0, app)
            if self._all is not None:
                self._all.insert(0, app)
            existing = 0
        self._selected = existing
        self.changed.emit()


def read_dark_mode():
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kdeglobals"
    for path in (config, Path("/etc/xdg/kdeglobals")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.startswith(("LookAndFeelPackage=", "ColorScheme=")):
                return "dark" in line.lower()
    return False


def parse_arguments(argv):
    """(file, mime, choose, choices) of the command line."""
    files, mime, choose, choices = [], "", False, []
    args = iter(argv[1:])
    for arg in args:
        if arg == "--open-with":
            continue
        if arg == "--choose":
            choose = True
        elif arg == "--type":
            mime = next(args, "")
        elif arg == "--choices":
            choices = [c for c in next(args, "").split(",") if c]
        else:
            files.append(QUrl(arg).toLocalFile() if arg.startswith("file://") else arg)
    return (os.path.abspath(files[0]) if files else ""), mime, choose, choices


def run(argv):
    from PySide6.QtQml import QQmlApplicationEngine
    from .app import prepare_application

    path, mime, choose, choices = parse_arguments(argv)
    if not path and not (choose and mime):
        print("usage: veltos-explorer --open-with [--choose] [--type MIME] FILE", file=sys.stderr)
        return 2
    app = prepare_application([argv[0]], "veltos-explorer", "open_with")
    opener = Opener(path, mime=mime, choose=choose, choices=choices)
    opener.done.connect(app.quit)
    # Closing the window is "cancel" (the caller is told).
    app.lastWindowClosed.connect(opener.cancel)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", opener)
    engine.rootContext().setContextProperty("opener", opener)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "OpenWith.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
