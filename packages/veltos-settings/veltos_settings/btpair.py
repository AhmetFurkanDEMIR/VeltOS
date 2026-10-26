"""Bluetooth pairing questions in Windows 11's "Add a device" style.

    veltos-settings --bt-pair confirm NAME PASSKEY   PIN shown on both: Connect / Cancel
    veltos-settings --bt-pair display NAME PIN       type this PIN on the device: Cancel
    veltos-settings --bt-pair pin NAME               enter the device's PIN (printed)
    veltos-settings --bt-pair passkey NAME           enter a number (printed)
    veltos-settings --bt-pair authorize NAME         the device wants to pair: Allow / Cancel
    veltos-settings --bt-pair service NAME           the device wants to connect: Allow / Cancel

Started by the VeltOS Bluetooth agent (btagent.py), which waits for the
answer: exit status 0 = yes (with the typed PIN on standard output), 1 = no.
Plasma's agent asked in a notification with KDE's wording ("veltos
(00:AA:...) is asking if the PIN is correct", "PIN correct / PIN
incorrect"); product owner, 2026-10-27: like Windows 11.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from . import devices, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
KINDS = ("confirm", "display", "pin", "passkey", "authorize", "service")


def spaced(number):
    """Windows writes a six-digit PIN as "123 456"."""
    text = str(number)
    return f"{text[:3]} {text[3:]}" if len(text) == 6 and text.isdigit() else text


class PairBackend(QObject):
    answered = Signal(bool, str)

    def __init__(self, kind, name, value="", lang=None, dark=None, accent="", parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._kind = kind if kind in KINDS else "authorize"
        self._name = name or "Bluetooth"
        self._value = value
        self._dark = dark
        self._accent = accent

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Property(str, constant=True)
    def kind(self):
        return self._kind

    @Property(str, constant=True)
    def name(self):
        return self._name

    @Property(str, constant=True)
    def code(self):
        if self._kind == "confirm":
            return spaced(str(self._value).zfill(6))
        return spaced(self._value)

    @Property(str, constant=True)
    def message(self):
        key = {"confirm": "pair_confirm", "display": "pair_display", "pin": "pair_enter",
               "passkey": "pair_enter", "authorize": "pair_authorize", "service": "pair_service"}[self._kind]
        return strings.text(self.lang, key).replace("{name}", self._name)

    @Property(bool, constant=True)
    def darkMode(self):
        if self._dark is not None:
            return self._dark
        from . import sysinfo
        return sysinfo.dark_mode()

    @Property(str, constant=True)
    def accent(self):
        return self._accent or devices.Personalization().accent()

    @Slot(bool, str)
    def answer(self, yes, typed):
        """A PIN must be what the device can take: 1-16 characters; a
        passkey a number up to 999999."""
        typed = typed.strip()
        if yes and self._kind == "pin" and not 1 <= len(typed) <= 16:
            return
        if yes and self._kind == "passkey" and not (typed.isdigit() and int(typed) <= 999999):
            return
        self.answered.emit(yes, typed)


def main(app, argv):
    args = argv[argv.index("--bt-pair") + 1:]
    kind = args[0] if args else ""
    name = args[1] if len(args) > 1 else ""
    value = args[2] if len(args) > 2 else ""
    backend = PairBackend(kind, name, value)
    # The Bluetooth app icon on the taskbar and in the title bar (KWin takes
    # it from the desktop file named by the Wayland app id).
    from PySide6.QtGui import QIcon
    app.setDesktopFileName("veltos-bluetooth-pair")
    app.setWindowIcon(QIcon.fromTheme("veltos-bluetooth"))
    result = {"code": 1, "done": False}

    def answered(yes, typed):
        if result["done"]:
            return                # only the first answer counts
        result["done"] = True
        if yes and typed:
            print(typed, flush=True)
        result["code"] = 0 if yes else 1
        app.quit()
    backend.answered.connect(answered)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "BluetoothPair.qml")))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    window.show()
    window.requestActivate()
    app.exec()
    del engine
    return result["code"]


if __name__ == "__main__":
    sys.exit(main(QGuiApplication(sys.argv), sys.argv))
