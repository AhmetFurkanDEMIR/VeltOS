"""The first start's "Getting everything ready" window (Windows 11's
out-of-box screens): full screen over the desktop while
veltos-first-update.service brings the new installation up to date
(firstupdate.py), then "You're ready to go" and it closes by itself.
`veltos-store --first-start`, started at sign-in by
/etc/xdg/autostart/veltos-first-start.desktop.

should_show() decides without Qt (it runs at every sign-in): never in the
live system, not once the update has finished more than SHOW_AFTER_DONE
ago, and once per user (~/.config/veltos/first-start-shown). "Continue in
the background" (after a while) closes the window; the update goes on.

Without a network ("offline") it asks to connect, as Windows 11's "Let's
connect you to a network": "Connect to Wi-Fi" opens VeltOS Settings at
Wi-Fi and steps aside; the window comes back when the PC is online (to show
the update) or when Settings is closed without a connection. "Continue
without internet" closes it; the update waits for a network by itself.
"""

import os
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QTimer, QUrl, Signal, Slot

from . import firstupdate, strings
from .firstupdate import marker

QML_DIR = Path(__file__).resolve().parent / "qml"
HIDE_AFTER = 20                  # seconds before "Continue in the background" appears
CLOSE_AFTER_READY = 4            # seconds "You're ready to go" stays


class FirstStart(QObject):
    changed = Signal()
    finished = Signal()
    hideWindow = Signal()
    showWindow = Signal()

    def __init__(self, lang=None, status=firstupdate.STATUS, done=firstupdate.DONE, interval=500, shown=None,
                 dark=True, accent="", scale=1.0):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._status, self._done, self._shown = status, done, shown or marker()
        self._data = {}
        self._started = time.monotonic()
        self._ready_at = None
        self._dark, self._accent, self._scale = dark, accent, scale
        self._away = False           # Settings is open for a network
        self._settings_pid = 0
        self._timer = QTimer(self)
        self._timer.setInterval(interval)
        self._timer.timeout.connect(self.poll)
        self._timer.start()
        self.poll()

    # Theme.qml reads backend.*
    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(str, constant=True)
    def accent(self):
        return self._accent

    @Property(float, constant=True)
    def textScale(self):
        return self._scale

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(str, notify=changed)
    def state(self):
        state = self._data.get("state", "")
        if not state and self._done.exists():
            return "done"
        return state or "network"

    @Property(bool, notify=changed)
    def ready(self):
        return self.state in ("done", "failed")

    @Property(bool, notify=changed)
    def offline(self):
        return self.state == "offline"

    @Property(bool, notify=changed)
    def bottles(self):
        return bool(self._data.get("bottles"))

    @Property(int, notify=changed)
    def percent(self):
        return int(self._data.get("percent", 0))

    @Property(str, notify=changed)
    def detail(self):
        state = self.state
        if state in ("download", "install"):
            return self._texts["fs_" + state].replace("{percent}", str(self.percent))
        return self._texts.get("fs_" + state, "")

    @Property(bool, notify=changed)
    def canHide(self):
        return not self.ready and not self.offline and time.monotonic() - self._started > HIDE_AFTER

    @Slot()
    def poll(self):
        self._data = firstupdate.read_status(self._status)
        if self.ready and self._ready_at is None:
            self._ready_at = time.monotonic()
        if self._away and (not self.offline or not running(self._settings_pid)):
            # Online now (the update shows), or back from Settings without one.
            self._away = False
            self.showWindow.emit()
        self.changed.emit()
        if self._ready_at is not None and time.monotonic() - self._ready_at > CLOSE_AFTER_READY:
            self.close()

    @Slot()
    def connectNetwork(self):
        """VeltOS Settings at Wi-Fi; the window steps aside meanwhile."""
        result = QProcess.startDetached("veltos-settings", ["wifi"])
        started, pid = result if isinstance(result, tuple) else (result, 0)
        if not started:
            return
        self._settings_pid = pid
        self._away = True
        self.hideWindow.emit()

    @Slot()
    def close(self):
        """Closes the window for good (this user is not shown it again)."""
        self._timer.stop()
        try:
            self._shown.parent.mkdir(parents=True, exist_ok=True)
            self._shown.write_text(time.strftime("%Y-%m-%d %H:%M:%S\n"), encoding="utf-8")
        except OSError:
            pass
        self.finished.emit()


def running(pid, proc=Path("/proc")):
    """Whether VeltOS Settings (pid, or any copy when the pid is unknown) runs."""
    if pid <= 0:
        for entry in proc.glob("[0-9]*/cmdline"):
            try:
                if b"veltos-settings" in entry.read_bytes():
                    return True
            except OSError:
                continue
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main(app, engine_factory):
    from .app import accent, dark_mode, text_scale
    backend = FirstStart(dark=dark_mode(), accent=accent(), scale=text_scale())
    engine = engine_factory()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "FirstStart.qml")))
    if not engine.rootObjects():
        return 1
    backend.finished.connect(app.quit)
    code = app.exec()
    del engine
    return code
