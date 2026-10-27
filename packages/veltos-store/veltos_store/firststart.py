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
"""

import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot

from . import firstupdate, strings
from .firstupdate import marker

QML_DIR = Path(__file__).resolve().parent / "qml"
HIDE_AFTER = 20                  # seconds before "Continue in the background" appears
CLOSE_AFTER_READY = 4            # seconds "You're ready to go" stays


class FirstStart(QObject):
    changed = Signal()
    finished = Signal()

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
        return self.state in ("done", "offline", "failed")

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
        return not self.ready and time.monotonic() - self._started > HIDE_AFTER

    @Slot()
    def poll(self):
        self._data = firstupdate.read_status(self._status)
        if self.ready and self._ready_at is None:
            self._ready_at = time.monotonic()
        self.changed.emit()
        if self._ready_at is not None and time.monotonic() - self._ready_at > CLOSE_AFTER_READY:
            self.close()

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
