"""VeltOS "open with" window: Windows 11's "Select an app to open this
file" instead of KDE's dialog.

    veltos-explorer --open-with FILE

Lists the installed apps that claim the file's type (then every app on
"More apps"); "Always" records the app as the default for the type in the
user's mimeapps.list (the freedesktop way, which Settings > Default apps
shows too), "Just once" only opens the file with it.
"""

import os
import re
import sys
from pathlib import Path

from PySide6.QtCore import Property, QMimeDatabase, QObject, QUrl, Signal, Slot

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
            if entry is None:
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


class Opener(QObject):
    """The apps for one file, for OpenWith.qml."""

    changed = Signal()
    done = Signal()

    def __init__(self, path, lang=None, start=ops.detached, config_home=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.path = str(path)
        self.start = start
        self.config_home = config_home
        self._dark = read_dark_mode()
        mime = QMimeDatabase().mimeTypeForFile(self.path)
        self.mime = mime.name()
        self.suffix = os.path.splitext(self.path)[1]
        self.claimed = places.applications_for(self.mime, self.lang)
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
        command = places.exec_command(app["path"], [self.path])
        if command:
            self.start(command)
        self.done.emit()


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


def run(argv):
    from PySide6.QtQml import QQmlApplicationEngine
    from .app import prepare_application

    files = [a for a in argv[1:] if a != "--open-with"]
    if not files:
        print("usage: veltos-explorer --open-with FILE", file=sys.stderr)
        return 2
    app = prepare_application([argv[0]], "veltos-explorer", "open_with")
    opener = Opener(os.path.abspath(files[0]))
    opener.done.connect(app.quit)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", opener)
    engine.rootContext().setContextProperty("opener", opener)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "OpenWith.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
