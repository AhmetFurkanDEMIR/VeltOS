"""Loads the real Settings window offscreen and visits every page.

Any QML warning or JavaScript error fails the test, so broken bindings are
caught at package build time, not by users.
"""

import locale
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
    from PySide6.QtCore import Q_ARG, QCoreApplication, QEvent, QMetaObject, QUrl, qInstallMessageHandler
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
        # Destroy the QML engine now, while its backend still exists: a
        # deferred deletion ran during a later test, after Python had freed
        # this test's backend, and its "backend is null" warnings failed
        # that test.
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.messages.clear()

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
                          ("personalization", "colours"), ("time", "datetime"),
                          ("system", "notifications"), ("system", "power"), ("system", "nightlight"),
                          ("system", "multitasking"), ("devices", "mouse"), ("devices", "touchpad"),
                          ("devices", "keyboard"), ("personalization", "lockscreen"),
                          ("apps", "defaultapps"), ("apps", "startup"), ("accounts", "yourinfo"),
                          ("accounts", "signin"), ("accounts", "otherusers"), ("time", "region"),
                          ("accessibility", "accessibility"), ("privacy", "searching"),
                          ("personalization", "themes"), ("personalization", "taskbar")):
            self.show(page, sub)
            self.assertEqual(self.window.property("subPage"), sub)
            self.assertEqual(self.problems(), [], sub)
        self.window.setProperty("query", "sound")
        self.app.processEvents()
        self.window.setProperty("query", "nothing matches this")
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_items_open_pages_and_actions(self):
        self.call("activate", {"action": "updates", "page": ""})
        self.call("activate", {"action": "website", "page": ""})
        self.call("activate", {"action": "graphics", "page": ""})
        self.call("activate", {"action": "", "page": "about", "pageId": "system"})
        self.assertEqual(self.started, [["veltos-store", "--updates"],
                                        ["xdg-open", "https://veltos.ahmetfurkandemir.com/"],
                                        ["veltos-graphics"]])
        self.assertEqual(self.window.property("subPage"), "about")

    def test_new_pages_change_settings(self):
        self.backend.setPref("lockAfter", 10)
        self.backend.setPref("nightLight", True)
        self.backend.setDoNotDisturb(True)
        self.backend.setLayouts(["tr", "us"])
        self.backend.setInput("leftHanded", True, "all")
        self.backend.setAnimations(False)
        self.app.processEvents()
        commands = [" ".join(c) for c in self.system.commands]
        for expected in ("kwriteconfig6 --notify --file kscreenlockerrc --group Daemon --key Timeout 10",
                         "kwriteconfig6 --notify --file kwinrc --group NightColor --type bool --key Active true",
                         "kwriteconfig6 --notify --file plasmanotifyrc --group DoNotDisturb --key Until 2999,12,31,0,0,0",
                         "kwriteconfig6 --notify --file kxkbrc --group Layout --key LayoutList tr,us",
                         "kwriteconfig6 --notify --file kdeglobals --group KDE --key AnimationDurationFactor 0"):
            self.assertIn(expected, commands)
        self.assertEqual(self.backend.prefs["lockAfter"], 10)
        self.assertTrue(self.backend.prefs["doNotDisturb"])
        results = []
        self.backend.accountResult.connect(lambda op, error: results.append((op, error)))
        self.backend.changePassword("old", "one", "two")
        self.backend.addUser("!!!", "", "pw", False)      # nothing a login name can be made of
        self.app.processEvents()
        self.assertEqual(results, [("password", "passwords_differ"), ("adduser", "bad_username")])
        self.assertEqual(self.problems(), [])

    def test_theme_switch_applies_global_theme(self):
        self.backend.setAccent("#E81123")
        self.system.commands.clear()
        self.backend.setDarkMode(True)
        self.app.processEvents()
        commands = self.system.commands
        command = next(c for c in commands if c[:2] == ["sh", "-c"])
        self.assertEqual(command[3:], ["sh", "org.veltos.dark", "VeltOS-Dark", "dark"])
        self.assertIn("plasma-apply-lookandfeel --apply", command[2])
        # The chosen accent again after the global theme, then the palette
        # notice for the running taskbar.
        joined = [" ".join(c) for c in commands]
        self.assertGreater(joined.index("plasma-apply-colorscheme --accent-color #E81123"), commands.index(command))
        self.assertIn("org.kde.KGlobalSettings.notifyChange", joined[-1])
        self.assertTrue(self.backend.darkMode)
        self.assertEqual(self.problems(), [])

    def test_appearance_changes_run_one_after_another(self):
        import threading
        from veltos_settings import app
        order, gate = [], threading.Event()
        backend = self.backend
        jobs = app.Jobs(threaded=True)
        backend.jobs = jobs

        def slow():
            order.append("mode-start")
            gate.wait(2)
            order.append("mode-end")

        backend._appearance(slow)
        backend._appearance(lambda: order.append("accent"))
        import time
        time.sleep(0.2)
        self.assertEqual(order, ["mode-start"])         # the accent waits
        gate.set()
        for _ in range(50):
            if len(order) == 3:
                break
            time.sleep(0.05)
        self.assertEqual(order, ["mode-start", "mode-end", "accent"])

    @unittest.skipUnless(os.name == "posix", "runs the theme command")
    def test_theme_command_writes_the_users_plasmarc(self):
        # The taskbar follows ~/.config/plasmarc; the command must write the
        # Plasma theme there whatever the file held before.
        import subprocess
        from veltos_settings.app import APPLY_THEME
        for before, after in (
                (None, "[Theme]\nname=VeltOS-Dark\n"),
                ("[Theme]\nname=VeltOS\n", "[Theme]\nname=VeltOS-Dark\n"),
                ("[PlasmaToolTips]\nDelay=700\n\n[Theme]\nother=1\n\n[X]\na=b\n",
                 "[PlasmaToolTips]\nDelay=700\n\n[Theme]\nother=1\n\nname=VeltOS-Dark\n[X]\na=b\n"),
                ("[X]\na=b\n", "[X]\na=b\n[Theme]\nname=VeltOS-Dark\n")):
            with tempfile.TemporaryDirectory() as home:
                bin_dir = Path(home, "bin")
                bin_dir.mkdir()
                fake = bin_dir / "plasma-apply-lookandfeel"
                fake.write_text("#!/bin/sh\nexit 0\n")
                fake.chmod(0o755)
                Path(home, ".config").mkdir()
                plasmarc = Path(home, ".config/plasmarc")
                if before is not None:
                    plasmarc.write_text(before)
                env = dict(os.environ, HOME=home, PATH=f"{bin_dir}:{os.environ['PATH']}")
                env.pop("XDG_CONFIG_HOME", None)
                subprocess.run(["sh", "-c", APPLY_THEME, "sh", "org.veltos.dark", "VeltOS-Dark", "dark"],
                               env=env, check=True)
                self.assertEqual(plasmarc.read_text(), after, before)

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
        self.backend.discoverBluetooth()
        self.app.processEvents()
        commands = [" ".join(c) for c in self.system.commands]
        for expected in ("nmcli radio wifi off", "bluetoothctl power off",
                         "pactl set-sink-volume @DEFAULT_SINK@ 30%", "kscreen-doctor output.1.scale.1.5",
                         "timedatectl set-ntp false", "timedatectl set-timezone Europe/London",
                         "plasma-apply-colorscheme --accent-color #0078D4"):
            self.assertIn(expected, commands)
        self.assertNotIn("secret key", " ".join(commands))
        self.assertEqual(self.activated, [("New Net", "secret key", "wpa-psk")])
        # Add a device is VeltOS' own dialog: nothing of KDE's is started.
        self.assertNotIn(["bluedevil-wizard"], self.started)
        self.assertIn("bluetoothctl --timeout 10 scan on", commands)
        self.assertEqual(self.backend.accent, "#0078D4")
        self.assertEqual(self.problems(), [])

    def test_themes_apply_wallpaper_mode_and_accent(self):
        self.show("personalization", "themes")
        ids = [t["id"] for t in self.backend.themes]
        self.assertEqual(ids[:2], ["veltos-light", "veltos-dark"])
        was_dark = self.backend.darkMode
        self.backend.applyTheme("ember")          # dark, red
        self.app.processEvents()
        commands = [" ".join(c) for c in self.system.commands]
        self.assertIn("plasma-apply-wallpaperimage /usr/share/wallpapers/VeltOS-Ember", commands)
        self.assertIn("plasma-apply-colorscheme --accent-color #D6243B", commands)
        # Mode first, then wallpaper, then accent (the scheme sets the accent).
        if not was_dark:
            mode = next(i for i, c in enumerate(self.system.commands) if c[:2] == ["sh", "-c"])
            wall = next(i for i, c in enumerate(self.system.commands) if c[0] == "plasma-apply-wallpaperimage")
            self.assertLess(mode, wall)
        self.assertTrue(self.backend.darkMode)
        self.assertEqual(self.backend.currentTheme, "ember")
        self.backend.setAccent("#0078D4")
        self.assertEqual(self.backend.currentTheme, "")         # custom mix
        self.assertEqual(self.problems(), [])

    def test_add_device_finds_and_pairs(self):
        self.system.outputs[("bluetoothctl", "devices")] = (
            "Device AA:BB:CC:DD:EE:FF WH-1000XM4\nDevice 77:88:99:AA:BB:CC Keyboard K380\n"
            "Device 12:34:56:78:9A:BC 12-34-56-78-9A-BC\n")
        self.system.outputs[("bluetoothctl", "info", "77:88:99:AA:BB:CC")] = "\tIcon: input-keyboard\n"
        self.show("devices", "bluetooth")
        self.backend.discoverBluetooth()
        self.app.processEvents()
        found = self.backend.bluetooth["found"]
        self.assertEqual([d["name"] for d in found], ["Keyboard K380"])   # not paired, named
        self.assertEqual(found[0]["icon"], "input-keyboard")
        self.backend.pairBluetooth("77:88:99:AA:BB:CC")
        self.app.processEvents()
        commands = [" ".join(c) for c in self.system.commands]
        for expected in ("bluetoothctl pair 77:88:99:AA:BB:CC", "bluetoothctl trust 77:88:99:AA:BB:CC",
                         "bluetoothctl connect 77:88:99:AA:BB:CC"):
            self.assertIn(expected, commands)
        self.assertEqual(self.backend.bluetooth["found"], [])
        self.assertEqual(self.backend.bluetooth["pairFailed"], "")
        self.assertEqual(self.problems(), [])

    def test_home_recommends_recently_used_settings(self):
        from veltos_settings import app as settings_app, devices
        # Other tests of this class open pages too (same config folder).
        (devices.config_home() / settings_app.RECENT_FILE).unlink(missing_ok=True)
        self.assertEqual(self.backend.recentSettings[0], ["time", "datetime"])   # Windows' defaults
        for _ in range(3):
            self.show("system", "sound")
        self.backend.changed.emit()
        self.assertEqual(self.backend.recentSettings[0], ["system", "sound"])
        self.assertEqual(len(self.backend.recentSettings), 3)
        self.show("home")
        self.assertIn(self.backend.text("last_checked").split("{")[0], self.backend.updateChecked)
        self.assertEqual(self.problems(), [])

    def test_start_page_argument(self):
        from veltos_settings import app as settings_app
        for start, page, sub in (("wifi", "network", "wifi"), ("devices", "devices", ""),
                                 ("about", "system", "about"), ("signin", "accounts", "signin")):
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
    """Turkish texts, in the Turkish C locale when it is installed (Turkish
    case rules broke PySide6 keyword arguments in File Explorer)."""
    lang = "tr"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.old_locale = locale.setlocale(locale.LC_ALL)
        for name in ("tr_TR.UTF-8", "tr_TR.utf8"):
            try:
                locale.setlocale(locale.LC_ALL, name)
                break
            except locale.Error:
                continue

    @classmethod
    def tearDownClass(cls):
        locale.setlocale(locale.LC_ALL, cls.old_locale)


if __name__ == "__main__":
    unittest.main()
