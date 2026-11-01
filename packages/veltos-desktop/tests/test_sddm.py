"""Loads the VeltOS sign-in screen (SDDM theme) offscreen with stand-ins for
SDDM's objects. A broken login screen would lock people out of their PC, so
any QML warning fails the package build.
"""

import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import (Property, QCoreApplication, QEvent, QMetaObject, QObject, Qt, QUrl,
                                Signal, Slot, qInstallMessageHandler)
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
            for name, real, *picture in users:
                item = QStandardItem()
                item.setData(name, Qt.UserRole + 1)
                item.setData(real, Qt.UserRole + 2)
                item.setData(picture[0] if picture else "", Qt.UserRole + 3)
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

    class FakeSessions(QStandardItemModel):
        """SDDM's session list: Plasma on X11 first, as SDDM may remember
        it after a start without a graphics driver, then Plasma on Wayland."""
        ROLES = {Qt.UserRole + 1: b"file", Qt.UserRole + 2: b"name"}

        def __init__(self):
            super().__init__()
            for file, name in (("plasmax11.desktop", "Plasma (X11)"), ("plasma.desktop", "Plasma (Wayland)")):
                item = QStandardItem()
                item.setData(file, Qt.UserRole + 1)
                item.setData(name, Qt.UserRole + 2)
                self.appendRow(item)

        def roleNames(self):
            return self.ROLES

        @Property(int, constant=True)
        def lastIndex(self):
            return 0


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
        # Delete the view now, while this test's fake objects still exist:
        # deleted later, its bindings read them after they were gone and the
        # next test saw "Cannot read property ... of null".
        self.view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_loads_and_signs_in_to_plasma_on_wayland(self):
        self.assertIsNotNone(self.root, self.messages)
        self.assertEqual(self.root.property("userName"), "velt")
        self.root.setProperty("signInView", True)
        # Type a password through the property the field exposes.
        password = self.find_password_field()
        password.setProperty("text", "secret")
        QMetaObject.invokeMethod(self.root, "signIn")
        self.app.processEvents()
        # Wayland, although SDDM remembers X11 (lastIndex 0) after a safe start.
        self.assertEqual(self.sddm.calls[-1], ("login", "velt", "secret", 1))
        self.sddm.loginFailed.emit()
        self.app.processEvents()
        self.assertEqual(password.property("text"), "")
        self.assertFalse(self.root.property("busy"))
        self.assertEqual(self.problems(), [])

    def test_three_wrong_passwords_wait(self):
        # 3 wrong: 30 s, 3 more: 1 min, then 2 min (product owner, 2026-11-01).
        self.root.setProperty("signInView", True)
        password = self.find_password_field()
        for _ in range(3):
            password.setProperty("text", "nope")
            QMetaObject.invokeMethod(self.root, "signIn")
            self.sddm.loginFailed.emit()
            self.app.processEvents()
        self.assertEqual(self.root.property("lockLeft"), 30)
        self.assertFalse(password.property("enabled"))
        calls = len(self.sddm.calls)
        password.setProperty("text", "secret")
        QMetaObject.invokeMethod(self.root, "signIn")
        self.assertEqual(len(self.sddm.calls), calls)          # nothing tried while it waits
        self.root.setProperty("lockLeft", 0)
        for _ in range(3):
            QMetaObject.invokeMethod(self.root, "signIn")
            self.sddm.loginFailed.emit()
        self.assertEqual(self.root.property("lockLeft"), 60)
        self.root.setProperty("lockLeft", 0)
        for _ in range(3):
            QMetaObject.invokeMethod(self.root, "signIn")
            self.sddm.loginFailed.emit()
        self.assertEqual(self.root.property("lockLeft"), 120)
        self.assertEqual(self.problems(), [])

    def wait_for(self, condition, seconds=5):
        import time
        deadline = time.monotonic() + seconds
        while not condition() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.02)
        return condition()

    def test_hint_and_password_reset_usb(self):
        # Forgotten passwords (product owner, 2026-11-01): the hint after a
        # wrong password; "Reset password" only for an account with a reset
        # USB; the USB first, then the new password. A stand-in for
        # veltos-auth's password-recovery service answers.
        import http.server
        import json
        import threading
        requests = []
        answers = {"/status": {"configured": True, "hint": "first cat"}, "/find": {"error": "no-drive"},
                   "/reset": {"error": ""}}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, body))
                data = json.dumps(answers[self.path]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *_args):
                pass
        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        self.root.setProperty("recoveryService", f"http://127.0.0.1:{server.server_address[1]}")
        QMetaObject.invokeMethod(self.root, "loadAccountHelp")
        self.assertTrue(self.wait_for(lambda: self.root.property("resetAvailable")))
        self.assertEqual(requests[-1], ("/status", {"user": "velt"}))
        self.root.setProperty("signInView", True)
        hint = self.root.findChild(QObject, "hintLine")
        # The sign-in box fades in (250 ms); the hint waits for a wrong password.
        self.assertTrue(self.wait_for(lambda: self.find_password_field().property("visible")))
        self.assertFalse(hint.property("visible"))
        password = self.find_password_field()
        password.setProperty("text", "nope")
        QMetaObject.invokeMethod(self.root, "signIn")
        self.sddm.loginFailed.emit()
        self.app.processEvents()
        self.assertTrue(self.wait_for(lambda: hint.property("visible")))
        self.assertEqual(hint.property("text"), "Hint: first cat")
        self.assertTrue(self.root.findChild(QObject, "resetLink").property("visible"))
        QMetaObject.invokeMethod(self.root, "startReset")
        self.assertEqual(self.root.property("resetStep"), "insert")
        QMetaObject.invokeMethod(self.root, "findDrive")
        self.assertTrue(self.wait_for(lambda: self.root.property("resetError") != ""))
        self.assertEqual(self.root.property("resetError"),
                         "No USB drive was found. Insert the password reset USB and try again.")
        answers["/find"] = {"error": ""}
        QMetaObject.invokeMethod(self.root, "findDrive")
        self.assertTrue(self.wait_for(lambda: self.root.property("resetStep") == "password"))
        fields = [self.root.findChild(QObject, name) for name in ("newPassword", "confirmPassword", "newHint")]
        self.assertTrue(all(f is not None and f.property("visible") for f in fields))
        fields[0].setProperty("text", "new one")
        fields[1].setProperty("text", "other")
        QMetaObject.invokeMethod(self.root, "applyReset")
        self.assertEqual(self.root.property("resetError"), "The passwords don't match.")
        fields[1].setProperty("text", "new one")
        fields[2].setProperty("text", "tea")
        QMetaObject.invokeMethod(self.root, "applyReset")
        self.assertTrue(self.wait_for(lambda: self.root.property("resetStep") == ""))
        self.assertIn(("/reset", {"user": "velt", "password": "new one", "hint": "tea"}), requests)
        self.assertEqual(self.root.property("resetStep"), "")
        self.assertEqual(self.root.property("failures"), 0)
        self.assertEqual(self.problems(), [])

    def test_no_reset_link_without_a_reset_usb(self):
        # The service answers nothing here (none runs): no link, no hint.
        self.root.setProperty("recoveryService", "http://127.0.0.1:9")
        QMetaObject.invokeMethod(self.root, "loadAccountHelp")
        self.app.processEvents()
        self.assertFalse(self.root.property("resetAvailable"))
        self.assertFalse(self.root.findChild(QObject, "resetLink").property("visible"))

    def test_signs_in_to_plasma_on_x11_without_a_graphics_driver(self):
        # The screen runs on X11 only at a start without a graphics driver
        # (veltos-recovery's safe-graphics); Wayland cannot run then.
        self.root.setProperty("onX11", True)
        self.root.setProperty("signInView", True)
        self.find_password_field().setProperty("text", "secret")
        QMetaObject.invokeMethod(self.root, "signIn")
        self.app.processEvents()
        self.assertEqual(self.sddm.calls[-1], ("login", "velt", "secret", 0))
        self.assertEqual(self.problems(), [])

    def test_user_list_shows_account_pictures(self):
        # Windows lists the other users at the bottom left with their
        # account pictures (product owner, 2026-10-23: only initials showed).
        import tempfile
        from PySide6.QtGui import QColor, QImage
        picture = Path(tempfile.mkdtemp()) / "ayse.png"
        image = QImage(64, 64, QImage.Format.Format_RGB32)
        image.fill(QColor("#4F7CFF"))
        self.assertTrue(image.save(str(picture)))
        self.view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.keep[1] = FakeUsers([("velt", "Velt"), ("ayse", "Ayşe", QUrl.fromLocalFile(str(picture)).toString())])
        self.view = QQuickView()
        context = self.view.rootContext()
        context.setContextProperty("sddm", self.sddm)
        context.setContextProperty("keyboard", self.keep[0])
        context.setContextProperty("userModel", self.keep[1])
        context.setContextProperty("sessionModel", self.keep[2])
        context.setContextProperty("config", self.config)
        self.view.setSource(QUrl.fromLocalFile(str(THEME)))
        self.root = self.view.rootObject()
        self.root.setProperty("signInView", True)
        for _ in range(20):
            self.app.processEvents()
        pictures = []

        def walk(item):
            if item.objectName() == "userListPicture":
                pictures.append(item)
            for child in item.childItems():
                walk(child)
        walk(self.root)
        self.assertEqual(len(pictures), 2)
        # Only Ayşe's picture loads (a loaded Image has its natural width).
        self.assertEqual([p.property("implicitWidth") > 0 for p in pictures].count(True), 1)
        self.assertEqual(self.problems(), [])

    def find_password_field(self):
        field = self.root.findChild(QObject, "passwordField")
        self.assertIsNotNone(field, "password field not found")
        return field

if __name__ == "__main__":
    unittest.main()
