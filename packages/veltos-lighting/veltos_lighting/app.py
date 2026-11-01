"""VeltOS Keyboard Lighting: a laptop keyboard's lights on or off, their
brightness, colour and effect, in the look of Windows 11's Dynamic
Lighting (product owner, 2026-10-27). PySide6 + QML.

leds.py reads the lights; changes go through the VeltOS helper
(helper.py as /usr/libexec/veltos/keyboard-light, pkexec without a
password for the signed-in user). The choices are kept per light in
~/.config/veltos/lighting.json and applied again at sign-in
(`veltos-lighting --restore`, which ends at once on a PC without keyboard
lights): many keyboards forget their colour when the PC restarts.

On an MSI laptop without a keyboard light, msi.py offers MSI's own driver
(veltos-msi-ec), which Debian's kernel lacks (product owner, 2026-10-28:
an MSI Katana's keyboard was not found).
"""

import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import leds, msi, strings, themewatch
from .config import (SWATCHES, accent, dark_mode, helper_command, load_settings, restore, run, save_settings,
                     text_scale)

QML_DIR = Path(__file__).resolve().parent / "qml"


class Backend(QObject):
    changed = Signal()
    lookChanged = Signal()

    def __init__(self, lang=None, root=leds.LEDS, runner=run, settings=None, apply_delay=250, accent_color=None,
                 msi_setup=None):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._root = root
        self._runner = runner
        self._settings_file = settings
        # A given accent (tests) stays; otherwise the system's, followed.
        self._scale = text_scale()
        self._look = themewatch.ThemeWatch(
            (lambda: (dark_mode(), accent())) if accent_color is None else None, self,
            initial=None if accent_color is None else (dark_mode(), accent_color))
        self._look.changed.connect(self.lookChanged)
        self._keyboards = []
        self._selected = 0
        self._choice = {}
        self._error = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(apply_delay)
        self._timer.timeout.connect(self.apply)
        self._msi = msi_setup or msi.MsiSetup(self._texts, self)
        self._msi.finished.connect(lambda ok: ok and self.refresh())
        self.refresh()

    # --- the theme (Theme.qml reads backend.*) --------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

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

    @Property("QVariantList", constant=True)
    def swatches(self):
        return SWATCHES

    # --- state --------------------------------------------------------------------------

    @Property(QObject, constant=True)
    def msi(self):
        return self._msi

    @Property("QVariantList", notify=changed)
    def keyboards(self):
        return self._keyboards

    @Property(int, notify=changed)
    def selected(self):
        return self._selected

    @Property("QVariantMap", notify=changed)
    def keyboard(self):
        return self._keyboards[self._selected] if self._keyboards else {}

    @Property("QVariantMap", notify=changed)
    def choice(self):
        return self._choice

    @Property(str, notify=changed)
    def error(self):
        return self._error

    def _led(self):
        return self._keyboards[self._selected] if self._keyboards else None

    def _initial_choice(self, led):
        saved = load_settings(self._settings_file).get(led["id"])
        if isinstance(saved, dict):
            choice = {"on": True, "brightness": 100, "color": "", "effect": "static", "speed": 1, "matchAccent": False}
            choice.update(saved)
            return choice
        percent = round(100 * led["brightness"] / led["max"]) if led["max"] else 0
        return {"on": led["brightness"] > 0, "brightness": percent or 100, "color": led["color"] or "#FFFFFF",
                "effect": "static", "speed": 1, "matchAccent": False}

    @Slot()
    def refresh(self):
        self._keyboards = leds.keyboards(self._root)
        self._selected = min(self._selected, max(0, len(self._keyboards) - 1))
        led = self._led()
        self._choice = self._initial_choice(led) if led else {}
        self.changed.emit()
        if not self._keyboards:
            self._msi.check()

    @Slot(int)
    def select(self, index):
        if 0 <= index < len(self._keyboards):
            self._selected = index
            self._choice = self._initial_choice(self._keyboards[index])
            self.changed.emit()

    def _update(self, **values):
        if not self._led():
            return
        self._choice = dict(self._choice, **values)
        self.changed.emit()
        self._timer.start()

    @Slot(bool)
    def setOn(self, on):
        self._update(on=bool(on))

    @Slot(int)
    def setBrightness(self, percent):
        self._update(brightness=max(1, min(100, int(percent))), on=True)

    @Slot(str)
    def setColor(self, color):
        if leds.parse_color(color):
            self._update(color=color.upper(), matchAccent=False, on=True)

    @Slot(str)
    def setEffect(self, effect):
        if effect in leds.EFFECTS:
            self._update(effect=effect)

    @Slot(int)
    def setSpeed(self, speed):
        self._update(speed=max(0, min(2, int(speed))))

    @Slot(bool)
    def setMatchAccent(self, match):
        values = {"matchAccent": bool(match)}
        if match and self._look.accent:
            values["color"] = self._look.accent
        self._update(**values)

    @Slot()
    def apply(self):
        """Writes the current choice through the helper and keeps it."""
        led = self._led()
        if not led:
            return
        self._timer.stop()
        ok = self._runner(helper_command(led, self._choice, led["colorKind"])) == 0
        saved = load_settings(self._settings_file)
        saved[led["id"]] = self._choice
        save_settings(saved, self._settings_file)
        self._error = "" if ok else self._texts["failed"]
        self.changed.emit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if "--restore" in argv[1:]:
        return 0 if restore() else 1
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-lighting")
    app.setDesktopFileName("veltos-lighting")
    app.setWindowIcon(QIcon.fromTheme("veltos-lighting"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(lambda: backend._timer.isActive() and backend.apply())
    code = app.exec()
    del engine
    return code
