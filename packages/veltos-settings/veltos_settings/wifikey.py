"""A network's key in Windows 11's style (the VeltOS network agent's window).

    veltos-settings --wifi-key psk NAME [retry]   WPA/WPA2/WPA3 personal key
    veltos-settings --wifi-key wep NAME [retry]   WEP key
    veltos-settings --wifi-key eap NAME [retry]   user name and password

Started by the VeltOS network agent (nmagent.py), which waits for the
answer: exit status 0 with the key (or "user name\\npassword") on standard
output, 1 = cancelled. Windows 11 asks "Enter the network security key" and,
after a wrong one, says "The network security key isn't correct"; KDE's
"Wi-Fi password dialog" asked before (product owner, 2026-10-31).
"""

import re
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from . import devices, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
KINDS = ("psk", "wep", "eap")


def valid_key(kind, key):
    """Keys NetworkManager takes: WPA 8-63 characters or 64 hex digits;
    WEP 5 or 13 characters or 10 or 26 hex digits."""
    if kind == "psk":
        return 8 <= len(key) <= 63 or bool(re.fullmatch(r"[0-9A-Fa-f]{64}", key))
    if kind == "wep":
        return len(key) in (5, 13) or bool(re.fullmatch(r"[0-9A-Fa-f]{10}|[0-9A-Fa-f]{26}", key))
    return bool(key)


class KeyBackend(QObject):
    answered = Signal(bool, str)

    def __init__(self, kind, name, retry=False, lang=None, dark=None, accent="", parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._kind = kind if kind in KINDS else "psk"
        self._name = name or "Wi-Fi"
        self._retry = bool(retry)
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

    @Property(bool, constant=True)
    def retry(self):
        return self._retry

    @Property(bool, constant=True)
    def darkMode(self):
        if self._dark is not None:
            return self._dark
        from . import sysinfo
        return sysinfo.dark_mode()

    @Property(str, constant=True)
    def accent(self):
        return self._accent or devices.Personalization().accent()

    @Slot(str, result=bool)
    def acceptable(self, key):
        return valid_key(self._kind, key)

    @Slot(bool, str, str)
    def answer(self, yes, user, key):
        if yes and self._kind == "eap":
            if not user.strip() or not key:
                return
            self.answered.emit(True, user.strip() + "\n" + key)
            return
        if yes and not valid_key(self._kind, key):
            return
        self.answered.emit(yes, key if yes else "")


def main(app, argv):
    args = argv[argv.index("--wifi-key") + 1:]
    kind = args[0] if args else ""
    name = args[1] if len(args) > 1 else ""
    retry = len(args) > 2 and args[2] == "retry"
    backend = KeyBackend(kind, name, retry)
    # The Wi-Fi icon on the taskbar and in the title bar (KWin takes it from
    # the desktop file named by the Wayland app id).
    from PySide6.QtGui import QIcon
    app.setDesktopFileName("veltos-wifi-key")
    app.setWindowIcon(QIcon.fromTheme("network-wireless"))
    result = {"code": 1, "done": False}

    def answered(yes, value):
        if result["done"]:
            return                # only the first answer counts
        result["done"] = True
        if yes and value:
            sys.stdout.write(value + "\n")
            sys.stdout.flush()
        result["code"] = 0 if yes else 1
        app.quit()
    backend.answered.connect(answered)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "WifiKey.qml")))
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
