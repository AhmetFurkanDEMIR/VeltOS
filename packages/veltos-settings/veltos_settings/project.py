"""Windows + P and Identify.

    veltos-settings --project    Windows 11's Project flyout: PC screen only,
                                 Duplicate, Extend, Second screen only
    veltos-settings --identify   each display shows its number for three
                                 seconds (Settings > Display > Identify)

The flyout is a layer-shell surface at the bottom right, above the
taskbar. Arrow keys and Windows + P again move the choice, Enter or a
click applies it (devices.Display.project), Escape or a click elsewhere
closes it. One flyout at a time: another start moves its choice on (a
local socket), as pressing P again with Windows held does on Windows.
"""

import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine

from . import devices, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
MODES = ("pc", "duplicate", "extend", "second")
TITLES = {"pc": "pc_screen_only", "duplicate": "duplicate", "extend": "extend", "second": "second_screen_only"}


def socket_name():
    return f"veltos-project-{os.getuid()}"


class ProjectBackend(QObject):
    changed = Signal()
    advance = Signal()
    finished = Signal()
    _applied = Signal(bool)

    def __init__(self, display=None, lang=None, dark=None, accent="", threaded=True, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.display = display or devices.Display()
        self._threaded = threaded
        self._dark = dark
        self._accent = accent
        state = self.display.state()
        self._count = state.get("count", 0)
        self._mode = state.get("project", "pc")
        self._outputs = state.get("outputs", [])
        self._busy = False
        self._applied.connect(self._on_applied)

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Property("QVariantList", constant=True)
    def modes(self):
        return [{"key": key, "title": strings.text(self.lang, TITLES[key])} for key in MODES]

    @Property(str, notify=changed)
    def current(self):
        return self._mode

    @Property(int, constant=True)
    def count(self):
        return self._count

    @Property("QVariantList", constant=True)
    def outputs(self):
        return self._outputs

    @Property(bool, constant=True)
    def darkMode(self):
        if self._dark is not None:
            return self._dark
        from . import sysinfo
        return sysinfo.dark_mode()

    @Property(str, constant=True)
    def accent(self):
        if self._accent:
            return self._accent
        return devices.Personalization().accent()

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Slot(str)
    def choose(self, mode):
        if mode not in MODES or self._busy:
            return
        if mode == self._mode or self._count < 2:
            self.finished.emit()
            return
        self._busy = True
        self._mode = mode
        self.changed.emit()

        def work():
            self._applied.emit(bool(self.display.project(mode)))
        if self._threaded:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    @Slot(bool)
    def _on_applied(self, _ok):
        self._busy = False
        self.changed.emit()
        self.finished.emit()

    @Slot()
    def openSettings(self):
        import subprocess
        subprocess.Popen(["veltos-settings", "display"], start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.finished.emit()


def hand_over():
    """Moves the running flyout's choice on; True if there was one."""
    socket = QLocalSocket()
    socket.connectToServer(socket_name())
    if not socket.waitForConnected(300):
        return False
    socket.write(b"next\n")
    socket.waitForBytesWritten(300)
    socket.disconnectFromServer()
    return True


def run_project(app):
    if hand_over():
        return 0
    backend = ProjectBackend()
    server = QLocalServer()
    QLocalServer.removeServer(socket_name())
    server.listen(socket_name())

    def on_connection():
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            connection.readyRead.connect(lambda: backend.advance.emit())
    server.newConnection.connect(on_connection)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Project.qml")))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    backend.finished.connect(app.quit)
    window.show()
    window.requestActivate()
    code = app.exec()
    del engine
    return code


class IdentifyBackend(QObject):
    def __init__(self, outputs, parent=None):
        super().__init__(parent)
        self._numbers = {o["name"]: o["number"] for o in outputs if o.get("enabled")}

    @Slot(str, result=int)
    def number(self, name):
        return self._numbers.get(name, 0)


def run_identify(app, seconds=3):
    state = devices.Display().state()
    backend = IdentifyBackend(state.get("outputs", []))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("identify", backend)
    windows = []
    for screen in app.screens():
        engine.load(QUrl.fromLocalFile(str(QML_DIR / "Identify.qml")))
        window = engine.rootObjects()[-1]
        window.setScreen(screen)
        window.setProperty("number", backend.number(screen.name()) or len(windows) + 1)
        window.show()
        windows.append(window)
    QTimer.singleShot(seconds * 1000, app.quit)
    code = app.exec()
    del engine
    return code


def main(app, argv):
    if "--identify" in argv:
        return run_identify(app)
    return run_project(app)


if __name__ == "__main__":
    sys.exit(main(QGuiApplication(sys.argv), sys.argv))
