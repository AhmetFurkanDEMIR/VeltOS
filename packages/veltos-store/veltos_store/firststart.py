"""The first start's Welcome window: a normal window with a few animated
cards (Start and search, VeltOS AI, VeltOS Store, Windows programs, making
it yours) and "Get started". `veltos-store --first-start`, started at
sign-in by /etc/xdg/autostart/veltos-first-start.desktop.

Until 2026-11-01 the first start covered the screen with "We're getting
everything ready" while the update ran, and without a network it had to
ask for one. The product owner wanted that screen gone: the update now runs
in the background at the first internet connection after the installation
(veltos-first-update.service, firstupdate.py) and this window only says so
in one line under the cards.

should_show() decides without Qt (it runs at every sign-in): never in the
live system, once per user (~/.config/veltos/first-start-shown).
"""

import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot

from . import firstupdate, strings, themewatch
from .firstupdate import marker

QML_DIR = Path(__file__).resolve().parent / "qml"

# The cards: (id, icon, program to open it).
CARDS = [
    ("start", "start-here", ["dbus-send", "--session", "--type=method_call", "--dest=org.kde.plasmashell",
                               "/PlasmaShell", "org.kde.PlasmaShell.activateLauncherMenu"]),
    ("ai", "veltos-ai", ["veltos-ai", "--window"]),
    ("store", "veltos-store", ["veltos-store"]),
    ("windows", "application-x-ms-dos-executable", ["veltos-settings", "windows-apps"]),
    ("personalize", "preferences-desktop-theme", ["veltos-settings", "personalization"]),
]


class FirstStart(QObject):
    changed = Signal()
    lookChanged = Signal()
    finished = Signal()

    def __init__(self, lang=None, status=firstupdate.STATUS, done=firstupdate.DONE, interval=2000, shown=None,
                 dark=False, accent="", scale=1.0, start=None, follow=None):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._status, self._done, self._shown = status, done, shown or marker()
        self._start = start
        self._scale = scale
        # `follow` reads the system's look again (main()); tests give none.
        self._look = themewatch.ThemeWatch(follow, self, initial=(dark, accent))
        self._look.changed.connect(self.lookChanged)
        self._data = {}
        self._timer = QTimer(self)
        self._timer.setInterval(interval)
        self._timer.timeout.connect(self.poll)
        self._timer.start()
        self.poll()

    # Theme.qml reads backend.*
    # Light/dark and the accent follow the system while the window is open
    # (themewatch.py).
    @Property(bool, notify=lookChanged)
    def darkMode(self):
        return self._look.dark

    @Property(str, notify=lookChanged)
    def accent(self):
        return self._look.accent

    @Property(float, constant=True)
    def textScale(self):
        return self._scale

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property("QVariantList", constant=True)
    def cards(self):
        return [{"id": key, "icon": icon, "title": self._texts["wl_" + key],
                 "description": self._texts["wl_" + key + "_desc"]} for key, icon, _program in CARDS]

    @Property(str, notify=changed)
    def updateText(self):
        """One line about the background update."""
        state = self._data.get("state", "")
        if state == "done" or (not state and self._done.exists()):
            return self._texts["wl_update_done"]
        if state == "failed":
            return self._texts["wl_update_failed"]
        if state in ("lists", "download", "install", "bottles"):
            return self._texts["wl_update_working"]
        return self._texts["wl_update_network"]

    @Slot()
    def poll(self):
        self._data = firstupdate.read_status(self._status)
        self.changed.emit()

    @Slot(str)
    def open(self, card):
        program = next((p for key, _icon, p in CARDS if key == card), None)
        if program and self._start:
            self._start(program)

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


def main(app, engine_factory, start=None):
    from .app import accent, dark_mode, text_scale
    backend = FirstStart(dark=dark_mode(), accent=accent(), scale=text_scale(), start=start,
                         follow=lambda: (dark_mode(), accent()))
    app.setApplicationDisplayName(backend.texts["wl_window"])
    engine = engine_factory()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Welcome.qml")))
    if not engine.rootObjects():
        return 1
    backend.finished.connect(app.quit)
    code = app.exec()
    del engine
    return code
