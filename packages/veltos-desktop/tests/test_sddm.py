"""Loads the VeltOS sign-in screen (SDDM theme) offscreen with stand-ins for
SDDM's objects. A broken login screen would lock people out of their PC, so
any QML warning fails the package build.
"""

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import (Property, QMetaObject, QObject, Qt, QUrl, Signal, Slot,
                                qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication, QStandardItem, QStandardItemModel
    from PySide6.QtQml import QQmlPropertyMap
    from PySide6.QtQuick import QQuickView
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

THEME = Path(__file__).resolve().parent.parent / "sddm/veltos/Main.qml"

if HAVE_QT:
    class FakeSddm(QObject):
        loginFailed = Signal()
        loginSucceeded = Signal()

        def __init__(self):
            super().__init__()
            self.calls = []

        @Property(bool, constant=True)
        def canSuspend(self):
            return True

        @Property(bool, constant=True)
        def canReboot(self):
            return True

        @Property(bool, constant=True)
        def canPowerOff(self):
            return True

        @Slot(str, str, int)
        def login(self, user, password, session):
            self.calls.append(("login", user, password, session))

        @Slot()
        def suspend(self):
            self.calls.append(("suspend",))

        @Slot()
        def reboot(self):
            self.calls.append(("reboot",))

        @Slot()
        def powerOff(self):
            self.calls.append(("powerOff",))

    class FakeKeyboard(QObject):
        @Property(bool, constant=True)
        def capsLock(self):
            return False

    class FakeUsers(QStandardItemModel):
        ROLES = {Qt.UserRole + 1: b"name", Qt.UserRole + 2: b"realName",
                 Qt.UserRole + 3: b"icon", Qt.UserRole + 4: b"homeDir"}

        def __init__(self, users):
            super().__init__()
            for name, real in users:
                item = QStandardItem()
                item.setData(name, Qt.UserRole + 1)
                item.setData(real, Qt.UserRole + 2)
                item.setData("", Qt.UserRole + 3)
                item.setData(f"/home/{name}", Qt.UserRole + 4)
                self.appendRow(item)

        def roleNames(self):
            return self.ROLES

        @Property(int, constant=True)
        def lastIndex(self):
            return 0

        @Property(int, constant=True)
        def count(self):
            return self.rowCount()

    class FakeSessions(QObject):
        @Property(int, constant=True)
        def lastIndex(self):
            return 1


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class SignInScreenTests(unittest.TestCase):
    def setUp(self):
        self.app = QGuiApplication.instance() or QGuiApplication([])
        self.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: self.messages.append(msg))
        self.sddm = FakeSddm()
        self.keep = [FakeKeyboard(), FakeUsers([("velt", "Velt"), ("ayse", "Ayşe")]), FakeSessions()]
        self.config = QQmlPropertyMap()
        self.config.insert("background", "")
        self.view = QQuickView()
        context = self.view.rootContext()
        context.setContextProperty("sddm", self.sddm)
        context.setContextProperty("keyboard", self.keep[0])
        context.setContextProperty("userModel", self.keep[1])
        context.setContextProperty("sessionModel", self.keep[2])
        context.setContextProperty("config", self.config)
        self.view.setSource(QUrl.fromLocalFile(str(THEME)))
        self.app.processEvents()
        self.root = self.view.rootObject()

    def tearDown(self):
        self.view.deleteLater()
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_loads_and_signs_in_with_the_last_session(self):
        self.assertIsNotNone(self.root, self.messages)
        self.assertEqual(self.root.property("userName"), "velt")
        self.root.setProperty("signInView", True)
        # Type a password through the property the field exposes.
        password = self.find_password_field()
        password.setProperty("text", "secret")
        QMetaObject.invokeMethod(self.root, "signIn")
        self.app.processEvents()
        self.assertEqual(self.sddm.calls[-1], ("login", "velt", "secret", 1))
        self.sddm.loginFailed.emit()
        self.app.processEvents()
        self.assertEqual(password.property("text"), "")
        self.assertFalse(self.root.property("busy"))
        self.assertEqual(self.problems(), [])

    def find_password_field(self):
        field = self.root.findChild(QObject, "passwordField")
        self.assertIsNotNone(field, "password field not found")
        return field

if __name__ == "__main__":
    unittest.main()
