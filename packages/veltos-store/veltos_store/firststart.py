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

Since 2026-11-02 (product owner: "more beautiful and animated, like
Windows 11") the window has three pages, as Windows 11's Get Started app:
a greeting over drifting colours, "Make it yours" (light or dark mode and
the accent colour, applied at once through VeltOS Settings' own helpers),
and the cards with the update's line.

should_show() decides without Qt (it runs at every sign-in): never in the
live system, once per user (~/.config/veltos/first-start-shown).
"""

import threading
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


class SettingsLook:
    """Light/dark and the accent through VeltOS Settings' own helpers (the
    same commands as Settings > Personalization > Colours, so the taskbar
    and every open window follow)."""

    def __init__(self):
        from veltos_settings import devices
        from veltos_settings.app import APPLY_THEME, DESKTOP_THEME, LOOK_AND_FEEL
        self.devices = devices
        self.accents = list(devices.ACCENTS)
        self.command = lambda dark: ["sh", "-c", APPLY_THEME, "sh", LOOK_AND_FEEL[dark], DESKTOP_THEME[dark],
                                     "dark" if dark else "light"]

    def set_mode(self, dark):
        personal = self.devices.Personalization()
        return personal.set_mode(self.command(dark), personal.accent())

    def set_accent(self, colour):
        return self.devices.Personalization().set_accent(colour)


def settings_look():
    try:
        return SettingsLook()
    except ImportError:          # without VeltOS Settings: the card opens nothing more
        return None


class FirstStart(QObject):
    changed = Signal()
    lookChanged = Signal()
    finished = Signal()
    applyingChanged = Signal()
    _applied = Signal()

    def __init__(self, lang=None, status=firstupdate.STATUS, done=firstupdate.DONE, interval=2000, shown=None,
                 dark=False, accent="", scale=1.0, start=None, follow=None, look=None):
        super().__init__()
        self._settings = look
        self._applying = False
        self._applied.connect(self._done_applying)
        # What the user chose last: the work runs one change at a time and
        # always ends in this state (a quick Light-then-Dark ended in light
        # before: the second click compared with the old look and was
        # dropped; product owner, 2026-11-02).
        self._wanted_dark = dark
        self._pending = {}
        self._queue_lock = threading.Lock()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._status, self._done, self._shown = status, done, shown or marker()
        self._start = start
        self._scale = scale
        # `follow` reads the system's look again (main()); tests give none.
        self._look = themewatch.ThemeWatch(follow, self, initial=(dark, accent))
        self._look.changed.connect(self.lookChanged)
        self._look.changed.connect(self._follow_system)
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

    # --- Make it yours: light or dark, the accent ---------------------------------------------

    @Property(bool, constant=True)
    def canPersonalize(self):
        return self._settings is not None

    @Property("QVariantList", constant=True)
    def accents(self):
        return self._settings.accents if self._settings is not None else []

    @Property(bool, notify=applyingChanged)
    def applying(self):
        return self._applying

    @Property(bool, notify=applyingChanged)
    def wantedDark(self):
        """The mode the user chose (shown at once; the system follows)."""
        return self._wanted_dark

    def _request(self, key, value):
        """Queue a change; one worker applies the latest wish of each kind,
        the mode before the accent, until nothing is left (the mode switch
        takes seconds and runs off the window's thread)."""
        with self._queue_lock:
            self._pending[key] = value
            start = not self._applying
            self._applying = True
        self.applyingChanged.emit()
        if start:
            threading.Thread(target=self._work, daemon=True).start()

    def _work(self):
        while True:
            with self._queue_lock:
                if not self._pending:
                    self._applying = False
                    break
                key = "dark" if "dark" in self._pending else "accent"
                value = self._pending.pop(key)
            try:
                if key == "dark":
                    self._settings.set_mode(value)
                else:
                    self._settings.set_accent(value)
            except Exception:  # noqa: BLE001 - a failed change must not stop the queue
                pass
        self._applied.emit()

    def _done_applying(self):
        self.applyingChanged.emit()
        self._look.check()

    def _follow_system(self):
        """A mode chosen elsewhere (Settings) while nothing is queued here."""
        if not self._applying and self._wanted_dark != self._look.dark:
            self._wanted_dark = self._look.dark
            self.applyingChanged.emit()

    @Slot(bool)
    def setDarkMode(self, dark):
        if self._settings is None or dark == self._wanted_dark:
            return
        self._wanted_dark = dark
        self._request("dark", dark)

    @Slot(str)
    def setAccent(self, colour):
        if self._settings is not None:
            self._request("accent", colour)

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
                         follow=lambda: (dark_mode(), accent()), look=settings_look())
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
