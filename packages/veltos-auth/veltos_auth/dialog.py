"""The VeltOS authentication prompt window (Windows 11 "User Account
Control" layout), one process per polkit request.

    python3 -m veltos_auth.dialog < request.json

The request (from agent.py) names the cookie, the message, details and
the accounts that may answer. The window asks for the password, runs
polkit's helper with it (helper.py) and prints the verdict as its last
line: SUCCESS (polkit has been told by the helper), FAILURE or CANCELLED.
"""

import configparser
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import helper, strings

QML_DIR = Path(__file__).resolve().parent / "qml"


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


def accent_colour():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


class Prompt(QObject):
    """The request for QML and the password check."""

    changed = Signal()
    finished = Signal(str)          # SUCCESS, FAILURE or CANCELLED

    def __init__(self, request, lang=None, out=None, helper_command=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.out = out or sys.stdout
        self.request = request
        self.helper_command = helper_command or [helper.helper_path()]
        self._users = list(request.get("users") or [])
        self._index = 0
        self._error = ""
        self._info = ""
        self._busy = False
        self._attempts = 0
        self._password = ""
        self._process = None
        self._verdict = None

    def text(self, key):
        return strings.text(self.lang, key)

    # --- for QML ----------------------------------------------------------------------

    @Slot(str, result=str)
    def tr(self, key):
        return self.text(key)

    @Property(str, constant=True)
    def message(self):
        return str(self.request.get("message") or self.text("question"))

    @Property(str, constant=True)
    def description(self):
        return str(self.request.get("description") or "")

    @Property(str, constant=True)
    def program(self):
        return str(self.request.get("program") or "")

    @Property(str, constant=True)
    def action(self):
        return str(self.request.get("action") or "")

    @Property(str, constant=True)
    def icon(self):
        return str(self.request.get("icon") or "")

    @Property("QVariantList", constant=True)
    def details(self):
        return [[str(k), str(v)] for k, v in (self.request.get("details") or {}).items()]

    @Property("QVariantList", constant=True)
    def users(self):
        return self._users

    @Property(int, notify=changed)
    def userIndex(self):
        return self._index

    @Slot(int)
    def selectUser(self, index):
        if 0 <= index < len(self._users):
            self._index = index
            self._error = ""
            self.changed.emit()

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(str, notify=changed)
    def info(self):
        return self._info

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(bool, constant=True)
    def darkMode(self):
        return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")

    @Property(str, constant=True)
    def accent(self):
        return accent_colour()

    # --- the check ---------------------------------------------------------------------

    @Slot(str)
    def submit(self, password):
        if self._busy or not self._users:
            return
        self._password = password
        self._error = ""
        self._busy = True
        self.changed.emit()
        process = QProcess(self)
        process.setProgram(self.helper_command[0])
        process.setArguments(self.helper_command[1:] + [self._users[self._index]["name"]])
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._done)
        process.errorOccurred.connect(self._failed_to_start)
        self._process = process
        self._buffer = ""
        process.start()
        process.write((str(self.request.get("cookie", "")) + "\n").encode())

    def _read(self):
        self._buffer += bytes(self._process.readAllStandardOutput()).decode("utf-8", "replace")
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            parsed = helper.parse_line(line)
            if parsed is None:
                continue
            kind, text, _hidden = parsed
            if kind == "prompt":
                self._process.write((self._password + "\n").encode())
            elif kind == "error":
                self._error = text
                self.changed.emit()
            elif kind == "info":
                self._info = text
                self.changed.emit()

    def _failed_to_start(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._done(127, QProcess.ExitStatus.CrashExit)

    def _done(self, code, status):
        if self._process is None:
            return
        self._process.deleteLater()
        self._process = None
        self._password = ""
        self._busy = False
        if status == QProcess.ExitStatus.NormalExit and code == 0:
            self.finish("SUCCESS")
            return
        self._attempts += 1
        self._error = self.text("wrong_password")
        self.changed.emit()

    def finish(self, verdict):
        if self._verdict is not None:
            return
        self._verdict = verdict
        self.out.write(verdict + "\n")
        self.out.flush()
        self.finished.emit(verdict)

    @Slot()
    def cancel(self):
        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
        self.finish("CANCELLED")


def read_request(stream=None):
    stream = stream or sys.stdin
    try:
        data = json.loads(stream.read() or "{}")
    except (OSError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def main(argv=None):
    argv = sys.argv if argv is None else argv
    request = read_request()
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-auth")
    app.setDesktopFileName("veltos-auth")
    # The prompt's own icon (the VeltOS "V" on a shield with a padlock);
    # the file itself when the icon theme has not been refreshed.
    icon = QIcon.fromTheme("veltos-auth")
    if icon.isNull():
        icon = QIcon(str(Path("/usr/share/icons/hicolor/scalable/apps/veltos-auth.svg")))
    app.setWindowIcon(icon)
    prompt = Prompt(request)
    prompt.finished.connect(lambda _verdict: app.quit())
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("auth", prompt)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        prompt.finish("FAILURE")
        return 1
    app.exec()
    if prompt._verdict is None:
        prompt.finish("CANCELLED")
    sys.stdout.flush()
    return 0 if prompt._verdict == "SUCCESS" else 1


if __name__ == "__main__":
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    sys.exit(main())
