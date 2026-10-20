"""VeltOS Calculator: Windows 11's Calculator on VeltOS.

The window (qml/Main.qml) shows Standard or Scientific mode with the
memory row, the History and Memory lists (beside the keypad when the
window is wide, over it when narrow), the navigation pane and Settings
(app theme). The arithmetic is in engine.py; this module connects it to
the window and to the desktop (theme, accent colour, clipboard, keep on
top).
"""

import configparser
import os
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QSettings, QTimer, QUrl, Property, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import engine, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
THEMES = ("light", "dark", "system")


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def kde_value(group, key):
    """A kdeglobals value as the session sees it (user, kdedefaults, /etc/xdg)."""
    home = config_home()
    for path in (home / "kdeglobals", home / "kdedefaults/kdeglobals", Path("/etc/xdg/kdeglobals")):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return ""


def system_dark():
    return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")


def system_accent():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def keep_above_script(pid, on):
    """KWin script that keeps this app's windows above the others (Wayland
    clients cannot ask for that themselves)."""
    return f"""// VeltOS Calculator: keep on top (generated).
var list = workspace.windowList();
for (var i = 0; i < list.length; ++i) {{
    if (list[i].pid === {int(pid)} && list[i].normalWindow) {{
        list[i].keepAbove = {"true" if on else "false"};
    }}
}}
"""


def run_kwin_script(source):
    """Load, run and unload a KWin script over D-Bus; False when KWin is
    not there (tests, other desktops)."""
    try:
        from PySide6.QtDBus import QDBusConnection, QDBusInterface
    except ImportError:
        return False
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        return False
    plugin = f"veltos-calculator-{os.getpid()}"
    script = Path(tempfile.mkdtemp(prefix="veltos-calculator-")) / "keep-above.js"
    script.write_text(source, encoding="utf-8")
    scripting = QDBusInterface("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", bus)
    if not scripting.isValid():
        return False
    scripting.call("unloadScript", plugin)
    reply = scripting.call("loadScript", str(script), plugin)
    arguments = reply.arguments()
    if not (arguments and isinstance(arguments[0], int) and arguments[0] >= 0):
        return False
    QDBusInterface("org.kde.KWin", f"/Scripting/Script{arguments[0]}", "org.kde.kwin.Script", bus).call("run")
    QTimer.singleShot(1000, lambda: scripting.call("unloadScript", plugin))
    return True


class Backend(QObject):
    changed = Signal()
    themeChanged = Signal()

    def __init__(self, lang=None, settings=None, kwin=run_kwin_script, parent=None):
        super().__init__(parent)
        self._lang = lang or strings.language()
        self._texts = strings.texts(self._lang)
        self._settings = settings if settings is not None else QSettings(
            str(config_home() / "veltos/calculator.conf"), QSettings.Format.IniFormat)
        self._kwin = kwin
        mode = str(self._settings.value("mode", "standard"))
        self.calc = engine.Calculator(self._lang, mode)
        angle = str(self._settings.value("angle", "deg"))
        self.calc.angle = angle if angle in engine.ANGLES else "deg"
        theme = str(self._settings.value("theme", "system"))
        self._theme = theme if theme in THEMES else "system"
        self._system_dark = system_dark()
        self._accent = system_accent()
        self._keep_on_top = False
        # Follow the system theme while open (VeltOS Settings writes kdeglobals).
        self._watcher = QFileSystemWatcher(self)
        for path in (config_home(), config_home() / "kdeglobals"):
            if path.exists():
                self._watcher.addPath(str(path))
        self._watcher.directoryChanged.connect(self._reread_theme)
        self._watcher.fileChanged.connect(self._reread_theme)

    def _reread_theme(self, *_args):
        dark, accent = system_dark(), system_accent()
        kdeglobals = str(config_home() / "kdeglobals")
        if kdeglobals not in self._watcher.files() and Path(kdeglobals).exists():
            self._watcher.addPath(kdeglobals)
        if (dark, accent) != (self._system_dark, self._accent):
            self._system_dark, self._accent = dark, accent
            self.themeChanged.emit()

    def _save(self, key, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    # --- properties --------------------------------------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(str, constant=True)
    def language(self):
        return self._lang

    @Property(str, notify=changed)
    def mode(self):
        return self.calc.mode

    @Property(str, notify=changed)
    def display(self):
        shown = self.calc.display()
        return self._texts[shown] if self.calc.error else shown

    @Property(bool, notify=changed)
    def isError(self):
        return bool(self.calc.error)

    @Property(str, notify=changed)
    def expression(self):
        return self.calc.expression()

    @Property("QStringList", notify=changed)
    def memory(self):
        return [self.calc.fmt(value) for value in self.calc.memory]

    @Property("QVariantList", notify=changed)
    def history(self):
        return [{"expression": expression, "result": self.calc.fmt(result)}
                for expression, result in self.calc.history]

    @Property(str, notify=changed)
    def angle(self):
        return self.calc.angle.upper()

    @Property(bool, notify=changed)
    def fixedExponent(self):
        return self.calc.fixed_exponent

    @Property(bool, notify=changed)
    def canClearEntry(self):
        """Scientific mode's clear key reads CE while a number is typed."""
        return self.calc.typing is not None and not self.calc.error and not self.calc.after_equals

    @Property(int, notify=changed)
    def openParens(self):
        return self.calc.open_parens()

    @Property(str, notify=themeChanged)
    def theme(self):
        return self._theme

    @Property(bool, notify=themeChanged)
    def darkMode(self):
        return self._system_dark if self._theme == "system" else self._theme == "dark"

    @Property(str, notify=themeChanged)
    def accent(self):
        return self._accent

    @Property(bool, notify=changed)
    def keepOnTop(self):
        return self._keep_on_top

    # --- actions -----------------------------------------------------------------------------

    @Slot(str)
    def press(self, key):
        self.calc.press(key)
        self.changed.emit()

    @Slot(str)
    def setMode(self, mode):
        if mode in engine.MODES and mode != self.calc.mode:
            self.calc.set_mode(mode)
            self._save("mode", mode)
            self.changed.emit()

    @Slot()
    def nextAngle(self):
        self.calc.next_angle()
        self._save("angle", self.calc.angle)
        self.changed.emit()

    @Slot()
    def toggleFixedExponent(self):
        self.calc.toggle_fixed_exponent()
        self.changed.emit()

    @Slot(int, str)
    def memoryItem(self, index, action):
        """"recall", "add", "subtract" or "clear" one memory item."""
        if action == "recall":
            self.calc.memory_recall(index)
        elif action in ("add", "subtract"):
            self.calc.memory_add(1 if action == "add" else -1, index)
        elif action == "clear":
            self.calc.memory_clear(index)
        self.changed.emit()

    @Slot(int)
    def useHistory(self, index):
        self.calc.use_history(index)
        self.changed.emit()

    @Slot()
    def clearHistory(self):
        self.calc.clear_history()
        self.changed.emit()

    @Slot()
    def clearMemory(self):
        self.calc.memory_clear()
        self.changed.emit()

    @Slot()
    def copy(self):
        if not self.calc.error:
            QGuiApplication.clipboard().setText(self.display)

    @Slot()
    def paste(self):
        if self.calc.paste(QGuiApplication.clipboard().text()):
            self.changed.emit()

    @Slot(str)
    def setTheme(self, theme):
        if theme in THEMES and theme != self._theme:
            self._theme = theme
            self._save("theme", theme)
            self.themeChanged.emit()

    @Slot(bool)
    def setKeepOnTop(self, on):
        self._keep_on_top = bool(on)
        if self._kwin is not None:
            self._kwin(keep_above_script(os.getpid(), self._keep_on_top))
        self.changed.emit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-calculator")
    app.setDesktopFileName("veltos-calculator")
    app.setWindowIcon(QIcon.fromTheme("veltos-calculator"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    qml = QQmlApplicationEngine()
    qml.rootContext().setContextProperty("backend", backend)
    qml.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not qml.rootObjects():
        return 1
    code = app.exec()
    # Qt may delete clipboard data after Python has shut down: leave at
    # once (see AGENTS.md, PySide6 clipboard).
    sys.stdout.flush()
    os._exit(code)
