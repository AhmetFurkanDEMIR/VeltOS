"""Wi-Fi keys in Windows 11's style: the VeltOS network agent's requests
and replies (nmagent.py) and the key window (wifikey.py, WifiKey.qml)
offscreen in English and Turkish (product owner, 2026-10-31: no more KDE
"Wi-Fi password dialog")."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from veltos_settings import nmagent, wifikey  # noqa: E402

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

ASK = nmagent.ALLOW_INTERACTION
WIFI = {"connection": {"id": "Home"}, "802-11-wireless": {"ssid": list(b"VeltOS-Home")},
        "802-11-wireless-security": {"key-mgmt": "wpa-psk"}}


class AgentTests(unittest.TestCase):
    def test_wifi_keys(self):
        self.assertEqual(nmagent.question(WIFI, "802-11-wireless-security", ASK), ("psk", False))
        self.assertEqual(nmagent.question(WIFI, "802-11-wireless-security", ASK | nmagent.REQUEST_NEW),
                         ("psk", True))
        wpa3 = dict(WIFI, **{"802-11-wireless-security": {"key-mgmt": "sae"}})
        self.assertEqual(nmagent.question(wpa3, "802-11-wireless-security", ASK), ("psk", False))
        wep = dict(WIFI, **{"802-11-wireless-security": {"key-mgmt": "none", "wep-key-type": 1}})
        self.assertEqual(nmagent.question(wep, "802-11-wireless-security", ASK), ("wep", False))

    def test_enterprise_networks_ask_user_and_password(self):
        peap = dict(WIFI, **{"802-1x": {"eap": ["peap"], "identity": "ali"}})
        self.assertEqual(nmagent.question(peap, "802-1x", ASK), ("eap", False))
        tls = dict(WIFI, **{"802-1x": {"eap": ["tls"]}})
        self.assertIsNone(nmagent.question(tls, "802-1x", ASK))      # certificates: not asked

    def test_no_window_without_interaction_or_for_other_requests(self):
        self.assertIsNone(nmagent.question(WIFI, "802-11-wireless-security", 0))
        self.assertIsNone(nmagent.question({"vpn": {}}, "vpn", ASK))
        self.assertIsNone(nmagent.question({"gsm": {}}, "gsm", ASK))

    def test_network_name(self):
        self.assertEqual(nmagent.network_name(WIFI), "VeltOS-Home")
        self.assertEqual(nmagent.network_name({"802-11-wireless": {"ssid": b"Kafe \xc3\x87ay"}}), "Kafe Çay")
        self.assertEqual(nmagent.network_name({"connection": {"id": "Office"}}), "Office")

    def test_replies(self):
        self.assertEqual(nmagent.secrets("psk", "veltos1234"),
                         {"802-11-wireless-security": {"psk": ("s", "veltos1234")}})
        self.assertEqual(nmagent.secrets("wep", "abcde"),
                         {"802-11-wireless-security": {"wep-key0": ("s", "abcde")}})
        self.assertEqual(nmagent.secrets("eap", "ali\np@ss\nword"),
                         {"802-1x": {"identity": ("s", "ali"), "password": ("s", "p@ss\nword")}})

    def test_interface_is_networkmanagers_secret_agent(self):
        import xml.etree.ElementTree as ET
        interface = ET.fromstring(nmagent.INTERFACE).find("interface")
        self.assertEqual(interface.get("name"), "org.freedesktop.NetworkManager.SecretAgent")
        self.assertEqual(sorted(m.get("name") for m in interface.findall("method")),
                         ["CancelGetSecrets", "DeleteSecrets", "GetSecrets", "SaveSecrets"])

    def test_keys_networkmanager_takes(self):
        self.assertFalse(wifikey.valid_key("psk", "short"))
        self.assertTrue(wifikey.valid_key("psk", "veltos1234"))
        self.assertTrue(wifikey.valid_key("psk", "a" * 63))
        self.assertFalse(wifikey.valid_key("psk", "g" * 64))     # 64 characters must be hex
        self.assertTrue(wifikey.valid_key("psk", "0123456789abcdef" * 4))
        self.assertTrue(wifikey.valid_key("wep", "abcde"))
        self.assertTrue(wifikey.valid_key("wep", "0123456789"))
        self.assertFalse(wifikey.valid_key("wep", "abcdef"))


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

    def open(self, kind, retry=False):
        if getattr(self, "engine", None) is not None:
            self.drop_engine()
        self.messages.clear()
        self.backend = wifikey.KeyBackend(kind, "VeltOS-Home", retry, lang=self.lang, dark=False,
                                          accent="#2F5EE6")
        self.answers = []
        self.backend.answered.connect(lambda yes, value: self.answers.append((yes, value)))
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(wifikey.QML_DIR / "WifiKey.qml")))
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

    def test_key_must_be_long_enough(self):
        self.open("psk")
        self.assertIn("VeltOS-Home", self.find("networkName").property("text"))
        self.assertFalse(self.find("wrongKey").property("visible"))
        self.find("keyFieldInput").setProperty("text", "short")
        QMetaObject.invokeMethod(self.find("nextButton"), "clicked")
        self.assertEqual(self.answers, [])
        self.find("keyFieldInput").setProperty("text", "veltos1234")
        QMetaObject.invokeMethod(self.find("nextButton"), "clicked")
        self.window.close()                  # closing after the answer adds no "cancel"
        self.app.processEvents()
        self.assertEqual(self.answers, [(True, "veltos1234")])
        self.assertEqual(self.problems(), [])

    def test_wrong_key_is_said_and_cancel_answers_no(self):
        self.open("psk", retry=True)
        self.assertTrue(self.find("wrongKey").property("visible"))
        QMetaObject.invokeMethod(self.find("cancelButton"), "clicked")
        self.assertEqual(self.answers, [(False, "")])
        self.assertEqual(self.problems(), [])

    def test_enterprise_asks_user_name_and_password(self):
        self.open("eap")
        self.assertTrue(self.find("userField").property("visible"))
        self.find("userFieldInput").setProperty("text", "ali")
        self.find("keyFieldInput").setProperty("text", "secret")
        QMetaObject.invokeMethod(self.find("nextButton"), "clicked")
        self.assertEqual(self.answers, [(True, "ali\nsecret")])
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class TurkishWindowTests(WindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
