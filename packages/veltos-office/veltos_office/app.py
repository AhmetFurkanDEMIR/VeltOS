"""VeltOS Office start pages: the Home / New / Open screen of Microsoft 365's
apps on Windows 11, in front of LibreOffice Writer, Calc and Impress.

    veltos-office word|sheet|slides [--blank] [FILE...]

With files, or with --blank, or when the user switched the start screen
off (Options), LibreOffice opens straight away; otherwise the start page
shows templates, recent and pinned files and opens the chosen one in
LibreOffice (`libreoffice --nologo --writer ...`), then closes.
"""

import configparser
import datetime
import json
import os
import pwd
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, QProcess, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon, QRegion
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import recent, strings, templates

QML_DIR = Path(__file__).resolve().parent / "qml"
KINDS = ("word", "sheet", "slides")
MODULES = {"word": "--writer", "sheet": "--calc", "slides": "--impress"}
# Microsoft 365's app colours (Fluent): Word blue, Excel green, PowerPoint orange.
ACCENTS = {"word": "#185ABD", "sheet": "#107C41", "slides": "#C43E1C"}
ACCENTS_DARK = {"word": "#4A8BE0", "sheet": "#3FA66B", "slides": "#E86A4A"}
DESKTOP_FILES = {"word": "libreoffice-writer", "sheet": "libreoffice-calc", "slides": "libreoffice-impress"}
PAGES = ("home", "new", "open", "account", "options")
FILTERS = {
    "word": ["*.docx", "*.doc", "*.docm", "*.dotx", "*.odt", "*.ott", "*.rtf", "*.txt"],
    "sheet": ["*.xlsx", "*.xls", "*.xlsm", "*.xltx", "*.ods", "*.ots", "*.csv"],
    "slides": ["*.pptx", "*.ppt", "*.pptm", "*.ppsx", "*.potx", "*.odp", "*.otp"],
}
# The start page stays while LibreOffice brings its window up (its start
# takes a few seconds the first time); then it leaves, as Office's does.
LEAVE_AFTER_MS = 2500


def kde_value(group, key):
    """A kdeglobals value as the session sees it (user, kdedefaults, /etc/xdg)."""
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (home / "kdeglobals", home / "kdedefaults/kdeglobals", Path("/etc/xdg/kdeglobals")):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return ""


def text_scale():
    """Settings > Accessibility > Text size (the KDE font size over 10 pt)."""
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def dark_mode():
    for key in ("LookAndFeelPackage", "ColorScheme"):
        value = kde_value("General", key)
        if value:
            return "dark" in value.lower()
    return False


def animations_on():
    try:
        return float(kde_value("KDE", "AnimationDurationFactor") or "1") > 0
    except ValueError:
        return True


def greeting_key(hour):
    if hour < 12:
        return "good_morning"
    if hour < 18:
        return "good_afternoon"
    return "good_evening"


def user_name():
    try:
        entry = pwd.getpwuid(os.getuid())
    except KeyError:
        return os.environ.get("USER", "")
    full = entry.pw_gecos.split(",")[0].strip()
    return full or entry.pw_name


def user_picture(home=None, user=None):
    """The account picture (~/.face.icon, ~/.face or AccountsService's)."""
    home = Path(home or Path.home())
    user = user or os.environ.get("USER") or pwd.getpwuid(os.getuid()).pw_name
    for path in (home / ".face.icon", home / ".face", Path("/var/lib/AccountsService/icons") / user):
        if path.is_file():
            return QUrl.fromLocalFile(str(path)).toString()
    return ""


def libreoffice_version(path="/usr/lib/libreoffice/program/bootstraprc"):
    """"25.2" from LibreOffice's bootstraprc (ProductKey=LibreOffice 25.2)."""
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("ProductKey="):
                return line.split("=", 1)[1].strip().split(" ")[-1]
    except OSError:
        pass
    return ""


def launch_command(kind, files=(), template=""):
    """The libreoffice command line: a blank document, a document from a
    template (-n) or the given files."""
    command = ["libreoffice", "--nologo", MODULES[kind]]
    if template:
        command += ["-n", template]
    command += list(files)
    return command


def start_detached(command):
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)


class Backend(QObject):
    settingsChanged = Signal()
    recentChanged = Signal()
    templatesChanged = Signal()
    pageChanged = Signal()
    busyChanged = Signal()
    message = Signal(str)
    leave = Signal()

    def __init__(self, kind, lang=None, store=None, launcher=None, home=None, xcu_path=None, template_dirs=None,
                 now=None):
        super().__init__()
        if kind not in KINDS:
            raise ValueError(kind)
        self.kind = kind
        self.lang = lang or strings.language()
        self.home = Path(home or Path.home())
        self.store = store or recent.Store(recent.config_file(kind))
        self.launcher = launcher or self._launch
        self.xcu_path = xcu_path
        self.template_dirs = template_dirs or {}
        self._now = now
        self._dark = dark_mode()
        self._scale = text_scale()
        self._animations = animations_on()
        self._page = "home"
        self._busy = False
        self._recent = []
        self._templates = []
        self._query = ""
        self.commands = []
        self.picker = None
        self.refresh()
        self._watch_settings()

    # --- settings ---------------------------------------------------------------------------------

    def _watch_settings(self):
        config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        paths = [str(p) for p in (config / "kdeglobals", config / "kdedefaults/kdeglobals") if p.exists()]
        self._watcher = QFileSystemWatcher(paths, self) if paths else None
        if self._watcher:
            self._watcher.fileChanged.connect(self._settings_changed)

    def _settings_changed(self, path=""):
        dark, scale, animations = dark_mode(), text_scale(), animations_on()
        if (dark, scale, animations) != (self._dark, self._scale, self._animations):
            self._dark, self._scale, self._animations = dark, scale, animations
            self.settingsChanged.emit()
        if self._watcher and path and path not in self._watcher.files() and os.path.exists(path):
            self._watcher.addPath(path)

    @Property(str, constant=True)
    def kindName(self):
        return self.kind

    @Property(str, constant=True)
    def appTitle(self):
        return strings.app_title(self.lang, self.kind)

    @Property(str, notify=settingsChanged)
    def accent(self):
        return ACCENTS_DARK[self.kind] if self._dark else ACCENTS[self.kind]

    @Property(str, constant=True)
    def brand(self):
        return ACCENTS[self.kind]

    @Property(bool, notify=settingsChanged)
    def darkMode(self):
        return self._dark

    @Property(float, notify=settingsChanged)
    def textScale(self):
        return self._scale

    @Property(bool, notify=settingsChanged)
    def animations(self):
        return self._animations

    @Property(str, constant=True)
    def greeting(self):
        now = self._now or datetime.datetime.now()
        return strings.text(self.lang, greeting_key(now.hour))

    @Property(str, constant=True)
    def userName(self):
        return user_name()

    @Property(str, constant=True)
    def userPicture(self):
        return user_picture(self.home)

    @Property(str, constant=True)
    def version(self):
        return libreoffice_version()

    @Property(str, constant=True)
    def appIcon(self):
        return DESKTOP_FILES[self.kind]

    @Property(str, constant=True)
    def fileIcon(self):
        return recent.ICONS[self.kind]

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot(str, str, str, result=str)
    def format(self, key, name, value):
        return strings.text(self.lang, key, **{name: value})

    @Property(str, constant=True)
    def blankName(self):
        return strings.text(self.lang, f"blank_{self.kind}")

    @Property(str, constant=True)
    def noRecentText(self):
        return strings.text(self.lang, {"word": "no_recent", "sheet": "no_recent_sheet", "slides": "no_recent_slides"}[self.kind])

    # --- pages -------------------------------------------------------------------------------------

    @Property(str, notify=pageChanged)
    def page(self):
        return self._page

    @Slot(str)
    def setPage(self, name):
        if name in PAGES and name != self._page:
            self._page = name
            self.pageChanged.emit()

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=settingsChanged)
    def showHome(self):
        return self.store.show_home

    @Slot(bool)
    def setShowHome(self, on):
        self.store.set_show_home(on)
        self.settingsChanged.emit()

    # --- recent files ------------------------------------------------------------------------------

    @Slot()
    def refresh(self):
        self._recent = recent.recent_files(self.kind, self.lang, self.store, xcu_path=self.xcu_path,
                                           now=self._now, home=self.home)
        self._templates = templates.catalogue(self.kind, self.lang, **self.template_dirs)
        self.recentChanged.emit()
        self.templatesChanged.emit()

    @Property(list, notify=recentChanged)
    def recent(self):
        return list(self._recent)

    @Property(list, notify=recentChanged)
    def pinned(self):
        return [item for item in self._recent if item["pinned"]]

    @Slot(str, result=list)
    def searchRecent(self, query):
        query = query.strip().casefold()
        if not query:
            return list(self._recent)
        return [item for item in self._recent if query in item["name"].casefold() or query in item["folder"].casefold()]

    @Slot(str, bool)
    def pin(self, path, on):
        self.store.pin(path, on)
        self.refresh()

    @Slot(str)
    def remove(self, path):
        self.store.forget(path)
        self.refresh()

    @Slot()
    def clearRecent(self):
        for item in self._recent:
            if not item["pinned"]:
                self.store.forget(item["path"])
        self.store.clear_recent()
        self.refresh()

    # --- templates ---------------------------------------------------------------------------------

    @Property(list, notify=templatesChanged)
    def templates(self):
        return list(self._templates)

    @Property(list, notify=templatesChanged)
    def featuredTemplates(self):
        """The Home page's row: VeltOS' first, then LibreOffice's (seven)."""
        return list(self._templates[:7])

    @Slot(str, result=list)
    def searchTemplates(self, query):
        return templates.search(self._templates, query)

    # --- opening -----------------------------------------------------------------------------------

    def _launch(self, command):
        start_detached(command)

    def _run(self, command):
        self.commands.append(command)
        self.launcher(command)
        self._busy = True
        self.busyChanged.emit()
        QTimer.singleShot(LEAVE_AFTER_MS, self.leave.emit)

    @Slot()
    def newBlank(self):
        self._run(launch_command(self.kind))

    @Slot(str)
    def newFromTemplate(self, path):
        if not os.path.exists(path):
            self.message.emit(strings.text(self.lang, "missing_file", name=Path(path).name))
            self.refresh()
            return
        self._run(launch_command(self.kind, template=path))

    @Slot(str)
    def openFile(self, path):
        if not os.path.exists(path):
            self.message.emit(strings.text(self.lang, "missing_file", name=Path(path).name))
            self.store.forget(path)
            self.refresh()
            return
        self.store.note_opened(path)
        self._run(launch_command(self.kind, files=[path]))

    @Slot()
    def browse(self):
        self._browse(self.home / "Documents")

    @Slot(str)
    def browseIn(self, folder):
        """The Open dialog in one of this PC's folders (Documents, Desktop...)."""
        self._browse(self.home / folder)

    def _browse(self, start):
        """The VeltOS Open dialog (File Explorer's --pick), asynchronously."""
        if self.picker is not None:
            return
        start = Path(start)
        request = {
            "mode": "open",
            "title": strings.text(self.lang, "open_dialog_title"),
            "current_folder": str(start if start.is_dir() else self.home),
            "filters": [
                {"name": strings.text(self.lang, f"filter_{self.kind}"), "patterns": FILTERS[self.kind]},
                {"name": strings.text(self.lang, "all_files"), "patterns": ["*"]},
            ],
        }
        process = QProcess(self)
        process.setProgram("veltos-explorer")
        process.setArguments(["--pick"])
        process.finished.connect(lambda code, status: self._picked(process))
        process.errorOccurred.connect(lambda error: self._picked(process))
        self.picker = process
        process.start()
        process.write(json.dumps(request).encode("utf-8"))
        process.closeWriteChannel()

    def _picked(self, process):
        if self.picker is not process:
            return
        self.picker = None
        out = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        process.deleteLater()
        lines = [line for line in out.strip().splitlines() if line.strip()]
        try:
            answer = json.loads(lines[-1]) if lines else {}
        except ValueError:
            answer = {}
        paths = [p for p in (answer.get("paths") or []) if isinstance(p, str)] if isinstance(answer, dict) else []
        if paths:
            for path in paths:
                self.store.note_opened(path)
            self._run(launch_command(self.kind, files=paths))

    @Slot(str)
    def openFileLocation(self, path):
        start_detached(["veltos-explorer", str(Path(path).parent)])

    @Slot(str)
    def copyPath(self, path):
        QGuiApplication.clipboard().setText(path)

    @Slot()
    def openAccount(self):
        start_detached(["veltos-settings", "accounts"])


def follow_frame(window):
    """Clicks on the drawn shadow around the window go to what is behind
    it: the input region is the frame only."""
    def update(*_args):
        margin = int(window.property("shadow") or 0)
        if margin:
            window.setMask(QRegion(margin, margin, max(1, window.width() - 2 * margin),
                                   max(1, window.height() - 2 * margin)))
        else:
            window.setMask(QRegion())
    for signal in (window.widthChanged, window.heightChanged, window.visibilityChanged):
        signal.connect(update)
    update()


def parse_args(argv):
    """(kind, files, blank) from the command line."""
    args = [a for a in argv[1:]]
    if not args or args[0] not in KINDS:
        raise SystemExit(f"usage: veltos-office {'|'.join(KINDS)} [--blank] [FILE...]")
    kind = args[0]
    blank = "--blank" in args[1:]
    files = [a for a in args[1:] if not a.startswith("--")]
    return kind, files, blank


def local_path(argument):
    """A file:// URL (desktop files pass %U) or a path."""
    if argument.startswith("file://"):
        return QUrl(argument).toLocalFile()
    return argument


def main(argv=None):
    argv = sys.argv if argv is None else argv
    kind, files, blank = parse_args(argv)
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
    if files:
        start_detached(launch_command(kind, files=[local_path(f) for f in files]))
        return 0
    store = recent.Store(recent.config_file(kind))
    if blank or not store.show_home:
        start_detached(launch_command(kind))
        return 0
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-office")
    app.setApplicationDisplayName(strings.app_title(strings.language(), kind))
    app.setDesktopFileName(DESKTOP_FILES[kind])
    app.setWindowIcon(QIcon.fromTheme(DESKTOP_FILES[kind]))
    backend = Backend(kind, store=store)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    follow_frame(window)
    backend.leave.connect(app.quit)
    code = app.exec()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
