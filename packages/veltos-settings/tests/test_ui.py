"""Loads the real Settings window offscreen and visits every page.

Any QML warning or JavaScript error fails the test, so broken bindings are
caught at package build time, not by users.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakesystem import FakeSystem  # noqa: E402
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Q_ARG, QMetaObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class SettingsWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()
        os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    def setUp(self):
        from veltos_settings import app as settings_app
        self.started = []
        self.messages.clear()
        self.system = FakeSystem()
        self.backend = settings_app.Backend(
            lang=self.lang, start=lambda command, env=None: self.started.append(command),
            system=settings_app.system_tools(self.system), threaded=False)
        self.activated = []
        self.backend.system.network.activate = lambda *args: self.activated.append(args) or True
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(settings_app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    lang = "en"

    def tearDown(self):
        self.engine.deleteLater()
        self.app.processEvents()

    def call(self, name, *args):
        """Call a JavaScript function of the window."""
        QMetaObject.invokeMethod(self.window, name, *[Q_ARG("QVariant", a) for a in args])
        self.app.processEvents()

    def show(self, page, sub=""):
        self.call("showPage", page, sub)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_every_page_loads(self):
        for page in self.backend.pages:
            self.show(page["id"])
            self.assertEqual(self.window.property("pageId"), page["id"])
        for page, sub in (("system", "about"), ("system", "storage"), ("apps", "windows-apps"),
                          ("system", "display"), ("system", "sound"), ("devices", "bluetooth"),
                          ("network", "wifi"), ("personalization", "background"),
                          ("personalization", "colours"), ("time", "datetime")):
            self.show(page, sub)
            self.assertEqual(self.window.property("subPage"), sub)
        self.window.setProperty("query", "sound")
        self.app.processEvents()
        self.window.setProperty("query", "nothing matches this")
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_items_open_modules_and_actions(self):
        self.call("activate", {"kcm": "kcm_pulseaudio", "action": "", "page": ""})
        self.call("activate", {"kcm": "", "action": "updates", "page": ""})
        self.call("activate", {"kcm": "", "action": "", "page": "about", "pageId": "system"})
        self.assertEqual(self.started, [["kcmshell6", "kcm_pulseaudio"],
                                        ["plasma-discover", "--mode", "update"]])
        self.assertEqual(self.window.property("subPage"), "about")

    def test_theme_switch_applies_global_theme(self):
        self.backend.setDarkMode(True)
        self.app.processEvents()
        command = self.started[-1]
        self.assertEqual(command[:2], ["sh", "-c"])
        self.assertEqual(command[3:], ["sh", "org.veltos.dark", "VeltOS-Dark"])
        self.assertIn("plasma-apply-lookandfeel --apply", command[2])
        self.assertIn("--key name --notify", command[2])
        self.assertTrue(self.backend.darkMode)
        self.assertEqual(self.problems(), [])

    def test_system_pages_read_the_system(self):
        for page, sub in (("network", "wifi"), ("devices", "bluetooth"), ("system", "sound"),
                          ("system", "display"), ("time", "datetime")):
            self.show(page, sub)
        self.assertEqual(self.problems(), [])
        self.assertEqual(self.backend.network["connection"], {"type": "wifi", "name": "Home Net"})
        self.assertEqual(len(self.backend.network["networks"]), 4)
        self.assertEqual(self.backend.bluetooth["devices"][0]["name"], "WH-1000XM4")
        self.assertEqual(self.backend.sound["outputs"][0]["volume"], 65)
        self.assertEqual(self.backend.display["outputs"][0]["currentMode"], "3")
        self.assertEqual(self.backend.time["timezone"], "Europe/Istanbul")

    def test_system_pages_change_settings(self):
        self.backend.setWifi(False)
        self.assertFalse(self.backend.network["enabled"])
        self.backend.connectWifi("New Net", "secret key", "WPA2")
        self.backend.setBluetooth(False)
        self.backend.setVolume("sink", 30)
        self.backend.setScale(1, 1.5)
        self.backend.setAutomaticTime(False)
        self.backend.setTimezone("Europe/London")
        self.backend.setAccent("#0078D4")
        self.backend.addBluetoothDevice()
        self.app.processEvents()
        commands = [" ".join(c) for c in self.system.commands]
        for expected in ("nmcli radio wifi off", "bluetoothctl power off",
                         "pactl set-sink-volume @DEFAULT_SINK@ 30%", "kscreen-doctor output.1.scale.1.5",
                         "timedatectl set-ntp false", "timedatectl set-timezone Europe/London",
                         "plasma-apply-colorscheme --accent-color #0078D4"):
            self.assertIn(expected, commands)
        self.assertNotIn("secret key", " ".join(commands))
        self.assertEqual(self.activated, [("New Net", "secret key", "wpa-psk")])
        self.assertEqual(self.started[-1], ["bluedevil-wizard"])
        self.assertEqual(self.backend.accent, "#0078D4")
        self.assertEqual(self.problems(), [])

    def test_start_page_argument(self):
        from veltos_settings import app as settings_app
        for start, page, sub in (("wifi", "network", "wifi"), ("devices", "devices", ""),
                                 ("about", "system", "about")):
            backend = settings_app.Backend(lang=self.lang, start=lambda c, env=None: None, start_page=start,
                                           system=settings_app.system_tools(FakeSystem()), threaded=False)
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("backend", backend)
            engine.load(QUrl.fromLocalFile(str(settings_app.QML_DIR / "Main.qml")))
            self.app.processEvents()
            window = engine.rootObjects()[0]
            self.assertEqual((window.property("pageId"), window.property("subPage")), (page, sub))
            engine.deleteLater()
            self.app.processEvents()

    def test_rename_rejects_bad_names(self):
        self.assertFalse(self.backend.renamePc("  "))
        self.assertTrue(self.backend.renamePc("Ofis PC"))
        self.assertEqual(self.started[-1], ["hostnamectl", "set-hostname", "Ofis PC"])


class TurkishWindowTests(SettingsWindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
