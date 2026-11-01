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
        self._applying = 0
        self._applied.connect(self._done_applying)
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

    # --- Make it yours: light or dark, the accent ---------------------------------------------

    @Property(bool, constant=True)
    def canPersonalize(self):
        return self._settings is not None

    @Property("QVariantList", constant=True)
    def accents(self):
        return self._settings.accents if self._settings is not None else []

    @Property(bool, notify=applyingChanged)
    def applying(self):
        return self._applying > 0

    def _apply(self, work):
        """Runs a look change off the window's thread (it takes seconds);
        one after the other, as Settings does."""
        self._applying += 1
        self.applyingChanged.emit()

        def run():
            with self._lock:
                try:
                    work()
                finally:
                    self._applied.emit()
        threading.Thread(target=run, daemon=True).start()

    _lock = threading.Lock()

    def _done_applying(self):
        self._applying = max(0, self._applying - 1)
        self.applyingChanged.emit()
        self._look.check()

    @Slot(bool)
    def setDarkMode(self, dark):
        if self._settings is not None and dark != self._look.dark:
            self._apply(lambda: self._settings.set_mode(dark))

    @Slot(str)
    def setAccent(self, colour):
        if self._settings is not None:
            self._apply(lambda: self._settings.set_accent(colour))

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
