"""VeltOS Settings window: Python backend for the QML user interface.

    veltos-settings [PAGE]      (PAGE: home, system, about, storage, ...)
"""

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from . import catalog, strings, sysinfo

QML_DIR = Path(__file__).resolve().parent / "qml"
LOOK_AND_FEEL = {False: "org.veltos.light", True: "org.veltos.dark"}


def detached(command, env=None):
    """Start a program that outlives Settings (its own session, no output)."""
    subprocess.Popen(command, env=env, start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


def windows_programs():
    """Records of Windows programs installed through veltos-run, if any."""
    try:
        from veltos_winapps.winenv import installed_apps
    except ImportError:
        return []
    apps = []
    for record in installed_apps():
        shortcuts = [s for s in record.get("shortcuts", []) if Path(s).exists()]
        apps.append({
            "name": record.get("name", ""),
            "publisher": record.get("publisher") or "",
            "version": record.get("version") or "",
            "installed": (record.get("installed_at") or "")[:10],
            "shortcut": shortcuts[0] if shortcuts else "",
        })
    return apps


class Backend(QObject):
    changed = Signal()

    def __init__(self, lang=None, start=detached, start_page="home"):
        super().__init__()
        self.lang = lang or strings.language()
        self._start = start
        self._dark = sysinfo.dark_mode()
        self._about = None
        self._storage = None
        self._windows_apps = None
        self._start_page = start_page

    # --- texts and structure ------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot(str, str, result=str)
    def format(self, key, value):
        """Text with one placeholder ({name}, {count}, {date}, ...) filled in."""
        template = strings.text(self.lang, key)
        field = template[template.index("{") + 1:template.index("}")]
        return template.replace("{" + field + "}", value)

    @Property("QVariantList", constant=True)
    def pages(self):
        return catalog.localized_pages(self.lang)

    @Property(str, constant=True)
    def startPage(self):
        return self._start_page

    @Slot(str, result="QVariantList")
    def search(self, query):
        return catalog.search(query, self.lang)

    # --- facts ----------------------------------------------------------------

    @Property("QVariantMap", notify=changed)
    def about(self):
        if self._about is None:
            self._about = sysinfo.about()
        return self._about

    @Property("QVariantList", notify=changed)
    def storage(self):
        if self._storage is None:
            self._storage = sysinfo.storage()
        return self._storage

    @Property("QVariantList", notify=changed)
    def windowsApps(self):
        if self._windows_apps is None:
            self._windows_apps = windows_programs()
        return self._windows_apps

    @Property(str, constant=True)
    def userName(self):
        return sysinfo.user_name()

    @Property(bool, notify=changed)
    def darkMode(self):
        return self._dark

    @Slot()
    def refresh(self):
        self._about = self._storage = self._windows_apps = None
        self._dark = sysinfo.dark_mode()
        self.changed.emit()

    # --- actions --------------------------------------------------------------

    @Slot(bool)
    def setDarkMode(self, dark):
        if dark == self._dark:
            return
        # The global theme switches colours, Plasma theme, window frames and
        # (through the kvantum / kvantum-dark style key) the application style.
        self._start(["plasma-apply-lookandfeel", "--apply", LOOK_AND_FEEL[dark]])
        self._dark = dark
        self.changed.emit()

    @Slot(str)
    def openModule(self, kcm):
        self._start(["kcmshell6", kcm])

    @Slot(str)
    def runAction(self, action):
        if action == "control-panel":
            self._start(["systemsettings"])
        elif action == "store":
            self._start(["plasma-discover"])
        elif action == "updates":
            self._start(["plasma-discover", "--mode", "update"])
        elif action == "disk-management":
            self._start(["partitionmanager"])
        elif action == "uninstall-windows":
            try:
                from veltos_winapps.winenv import Environment, wine_tool
            except ImportError:
                return
            environment = Environment()
            self._start([wine_tool("wine"), "uninstaller"], env=environment.env())
        else:
            raise ValueError(f"unknown action {action!r}")

    @Slot(str)
    def openWindowsApp(self, shortcut):
        if shortcut:
            self._start(["kioclient", "exec", shortcut])

    @Slot(str, result=bool)
    def renamePc(self, name):
        name = name.strip()
        if not sysinfo.valid_pc_name(name):
            return False
        # hostnamed asks for the administrator password through polkit.
        self._start(["hostnamectl", "set-hostname", name])
        if self._about is not None:
            self._about = dict(self._about, pcName=name)
            self.changed.emit()
        return True

    @Slot(str)
    def copyText(self, value):
        QGuiApplication.clipboard().setText(value)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    app.setApplicationName("veltos-settings")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-settings")
    app.setWindowIcon(QIcon.fromTheme("preferences-system"))
    start_page = argv[1] if len(argv) > 1 else "home"
    backend = Backend(start_page=start_page)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
