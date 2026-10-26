"""Bluetooth pairing in Windows 11's style: the agent's questions and
replies (btagent.py) and the Add a device window (btpair.py,
BluetoothPair.qml) offscreen in English and Turkish."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from veltos_settings import btagent  # noqa: E402

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class AgentTests(unittest.TestCase):
    def test_questions(self):
        device = "/org/bluez/hci0/dev_00_AA_01_01_00_01"
        self.assertEqual(btagent.question("RequestConfirmation", (device, 123)), ("confirm", "000123"))
        self.assertEqual(btagent.question("DisplayPasskey", (device, 987654, 0)), ("display", "987654"))
        self.assertEqual(btagent.question("DisplayPinCode", (device, "0000")), ("display", "0000"))
        self.assertEqual(btagent.question("RequestPinCode", (device,)), ("pin", ""))
        self.assertEqual(btagent.question("RequestPasskey", (device,)), ("passkey", ""))
        self.assertEqual(btagent.question("RequestAuthorization", (device,)), ("authorize", ""))
        self.assertEqual(btagent.question("AuthorizeService", (device, "0000110b-...")), ("service", ""))
        self.assertIsNone(btagent.question("Cancel", ()))

    def test_replies(self):
        self.assertEqual(btagent.reply_value("RequestPinCode", "1234"), ("(s)", ("1234",)))
        self.assertEqual(btagent.reply_value("RequestPasskey", "000042"), ("(u)", (42,)))
        self.assertEqual(btagent.reply_value("RequestConfirmation", ""), (None, None))

    def test_interface_is_bluez_agent1(self):
        import xml.etree.ElementTree as ET
        interface = ET.fromstring(btagent.INTERFACE).find("interface")
        self.assertEqual(interface.get("name"), "org.bluez.Agent1")
        self.assertEqual(sorted(m.get("name") for m in interface.findall("method")),
                         ["AuthorizeService", "Cancel", "DisplayPasskey", "DisplayPinCode", "Release",
                          "RequestAuthorization", "RequestConfirmation", "RequestPasskey", "RequestPinCode"])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def open(self, kind, value=""):
        from veltos_settings import btpair
        if getattr(self, "engine", None) is not None:
            self.drop_engine()               # the previous window, before its backend goes
        self.messages.clear()
        self.backend = btpair.PairBackend(kind, "Galaxy Buds2", value, lang=self.lang, dark=False,
                                          accent="#2F5EE6")
        self.answers = []
        self.backend.answered.connect(lambda yes, typed: self.answers.append((yes, typed)))
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(btpair.QML_DIR / "BluetoothPair.qml")))
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.window.show()
        self.app.processEvents()

    def drop_engine(self):
        self.window.close()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.engine = None

    def tearDown(self):
        if getattr(self, "engine", None) is not None:
            self.drop_engine()

    def find(self, name):
        found = []

        def walk(item):
            if item.objectName() == name:
                found.append(item)
            for child in item.childItems():
                walk(child)
        walk(self.window.contentItem())
        return found[0]

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "warning" in m.lower()
                or "undefined" in m.lower() or "error" in m.lower()]

    def test_confirm_shows_the_pin_and_connect_answers_once(self):
        self.open("confirm", "000123")
        self.assertEqual(self.find("code").property("text"), "000 123")
        self.assertIn("Galaxy Buds2", self.find("message").property("text"))
        QMetaObject.invokeMethod(self.find("yesButton"), "clicked")
        self.window.close()                  # closing after the answer adds no "no"
        self.app.processEvents()
        self.assertEqual(self.answers, [(True, "")])
        self.assertEqual(self.problems(), [])

    def test_pin_needs_text_and_cancel_says_no(self):
        self.open("pin")
        QMetaObject.invokeMethod(self.find("yesButton"), "clicked")
        self.assertEqual(self.answers, [])   # nothing typed yet
        self.find("entry").setProperty("text", "0000")
        QMetaObject.invokeMethod(self.find("yesButton"), "clicked")
        self.assertEqual(self.answers, [(True, "0000")])
        self.open("authorize")
        QMetaObject.invokeMethod(self.find("noButton"), "clicked")
        self.assertEqual(self.answers, [(False, "")])
        self.assertEqual(self.problems(), [])

    def test_display_has_only_cancel(self):
        self.open("display", "987654")
        self.assertFalse(self.find("yesButton").property("visible"))
        self.assertEqual(self.find("code").property("text"), "987 654")
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class TurkishWindowTests(WindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
