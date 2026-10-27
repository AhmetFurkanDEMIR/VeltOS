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

from fakesystem import FakeSystem, HotspotRunner  # noqa: E402
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Q_ARG, QCoreApplication, QEvent, QMetaObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401  (the window is then a QQuickWindow with contentItem())
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
        self.hotspot = HotspotRunner()
        self.backend.system.hotspot.run = self.hotspot
        self.backend.system.hotspot.write = self.hotspot.write
        self.backend.system.hotspot.resolve = self.hotspot.resolve
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

    def items(self, name):
        """Visible items of that objectName (items in a Window, open popups
        included, are found through the item tree, not with findChild)."""
        found = []

        def walk(item):
            if item.objectName() == name and item.isVisible():
                found.append(item)
            for child in item.childItems():
                walk(child)
        walk(self.window.contentItem())
        return found

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_language_choices_put_turkish_and_english_first(self):
        self.assertEqual(self.backend.languageOptions, [
            {"value": "tr", "label": "Türkçe"},
            {"value": "en", "label": "English (United States)"},
        ])

    def test_location_privacy_disclosure_names_the_provider(self):
        self.show("privacy", "location")
        # Debian 13's GeoClue sends Wi-Fi networks to beaconDB (Mozilla's
        # service closed in 2024).
        self.assertIn("api.beacondb.net", self.backend.text("location_provider_note"))
        self.assertNotIn("Mozilla", self.backend.text("location_provider_note"))
        # The default location: set in Maps, shown and cleared here.
        place = Path(os.environ["XDG_CONFIG_HOME"]) / "veltos" / "location.json"
        place.parent.mkdir(parents=True, exist_ok=True)
        place.write_text('{"latitude": 39.925533, "longitude": 32.866287}')
        self.backend.refreshDefaultLocation()
        self.app.processEvents()
        self.assertEqual(self.backend.defaultLocation, {"set": True, "label": "39.9255° N, 32.8663° E"})
        self.backend.setDefaultLocation()
        self.assertIn(["veltos-maps", "--set-default-location"], self.started)
        self.backend.clearDefaultLocation()
        self.assertFalse(place.exists())
        self.assertFalse(self.backend.defaultLocation["set"])
        self.assertEqual(self.problems(), [])

    def test_power_page_offers_modes_for_plugged_in_and_on_battery(self):
        self.system.power.update(profiles=["power-saver", "balanced"])
        self.show("system", "power")
        self.backend.refreshPrefs()
        self.app.processEvents()
        self.assertEqual(self.backend.prefs["powerModes"], ["power-saver", "balanced"])
        self.assertEqual(self.backend.prefs["powerModeBattery"], "power-saver")
        self.backend.setPowerMode("battery", "balanced")
        self.app.processEvents()
        self.assertEqual(self.backend.prefs["powerModeBattery"], "balanced")
        self.assertFalse(self.backend.prefs["powerModeError"])
        # Best performance is shown but not offered on this PC.
        self.backend.setPowerMode("ac", "performance")
        self.app.processEvents()
        self.assertTrue(self.backend.prefs["powerModeError"])
        self.assertEqual(self.problems(), [])

    def test_veltos_ai_page_saves_a_service_without_showing_keys(self):
        import test_assistant
        from veltos_settings import assistant
        saved = (assistant.PROVIDERS, assistant.ORDER)
        assistant.PROVIDERS, assistant.ORDER = test_assistant.PROVIDERS, test_assistant.ORDER
        try:
            fake = test_assistant.FakeConfig()
            self.backend.system.assistant.config = fake
            self.show("apps", "veltosai")
            self.assertTrue(self.backend.assistant["available"])
            self.backend.saveAiService("claude", "sk-ant-test", "", "")
            self.app.processEvents()
            self.assertEqual(fake.saved["provider"], "claude")
            self.assertTrue(self.backend.assistant["ready"])
            self.assertNotIn("sk-ant-test", repr(self.backend.assistant))
            self.backend.openAssistant()
            self.assertIn(["veltos-ai", "--window"], self.started)
            self.backend.useLocalAi()
            self.app.processEvents()
            self.assertEqual(fake.saved["provider"], "local")
            self.assertEqual(self.problems(), [])
        finally:
            assistant.PROVIDERS, assistant.ORDER = saved

    def test_mobile_hotspot_page_turns_on_edits_and_lists_devices(self):
        self.show("network", "hotspot")
        state = self.backend.hotspot
        self.assertTrue(state["loaded"])
        self.assertEqual(state["reason"], "")
        self.backend.setHotspot(True)
        self.app.processEvents()
        self.assertTrue(self.backend.hotspot["active"])
        self.hotspot.stations = [("02:00:00:00:01:00", "10.42.0.126", "veltos-phone")]
        self.backend.configureHotspot("VeltOS Paylaşım", "kahve-1234", "bg")
        self.app.processEvents()
        state = self.backend.hotspot
        self.assertEqual((state["ssid"], state["password"], state["band"]), ("VeltOS Paylaşım", "kahve-1234", "bg"))
        self.assertEqual(state["clients"][0]["name"], "veltos-phone")
        self.backend.setHotspot(False)
        self.app.processEvents()
        self.assertFalse(self.backend.hotspot["active"])
        self.hotspot.ethernet = False
        self.backend.refreshHotspot()
        self.app.processEvents()
        self.assertEqual(self.backend.hotspot["reason"], "no-internet")
        self.assertEqual(self.problems(), [])

    def test_several_displays(self):
        # A laptop's screen and a monitor side by side: the arrangement,
        # Multiple displays, main display, orientation, refresh rate, and
        # Windows + P's flyout and Identify.
        import json
        from test_devices import two_screens
        from veltos_settings import devices, project
        self.system.outputs[("kscreen-doctor", "--json")] = json.dumps({"outputs": two_screens(True, 1920)})
        self.show("system", "display")
        self.backend.refreshDisplay()
        self.app.processEvents()
        self.assertEqual(self.backend.display["count"], 2)
        self.backend.setProject("pc")
        self.backend.setMainDisplay(2)
        self.backend.setRotation(2, "right")
        self.backend.identifyDisplays()
        self.app.processEvents()
        self.assertIn(["kscreen-doctor", "output.2.rotation.right"], self.system.commands)
        self.assertEqual(self.started[-1], ["veltos-settings", "--identify"])
        self.window.grabWindow()
        self.assertEqual(self.problems(), [])

        flyout = project.ProjectBackend(devices.Display(self.system), lang=self.lang, dark=True, accent="#2f5ee6",
                                        threaded=False)
        self.assertEqual(flyout.current, "extend")
        finished = []
        flyout.finished.connect(lambda: finished.append(True))
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", flyout)
        engine.load(QUrl.fromLocalFile(str(project.QML_DIR / "Project.qml")))
        self.assertTrue(engine.rootObjects(), self.messages)
        engine.rootObjects()[0].show()
        flyout.advance.emit()
        self.app.processEvents()
        flyout.choose("duplicate")
        self.assertEqual(flyout.current, "duplicate")
        self.assertEqual(finished, [True])
        self.assertEqual(self.system.commands[-1][:2], ["kscreen-doctor", "output.1.enable"])
        identify = QQmlApplicationEngine()
        identify.rootContext().setContextProperty("identify", project.IdentifyBackend(self.backend.display["outputs"]))
        identify.load(QUrl.fromLocalFile(str(project.QML_DIR / "Identify.qml")))
        self.assertTrue(identify.rootObjects(), self.messages)
        for item in (engine, identify):
            item.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        # Offscreen there is no Wayland: the layer shell says so and does nothing.
        self.assertEqual([m for m in self.problems() if "not a wayland window" not in m], [])

    def test_stacked_displays_fit_the_arrangement(self):
        # A monitor above the laptop's screen (a negative position, as
        # KScreen may report): both boxes inside the arrangement, which is
        # taller for stacked screens (they ran over the card before,
        # product owner 2026-10-26). A second drop before Apply works in
        # the page's shown positions.
        import json
        from test_devices import two_screens
        screens = two_screens(True, 0)
        screens[1]["pos"] = {"x": 0, "y": -1440}
        self.system.outputs[("kscreen-doctor", "--json")] = json.dumps({"outputs": screens})
        self.show("system", "display")
        self.backend.refreshDisplay()
        self.app.processEvents()
        self.window.grabWindow()
        boxes = self.items("displayBox")
        self.assertEqual(len(boxes), 2)
        area = boxes[0].parentItem()
        self.assertGreaterEqual(area.height(), 240)
        for box in boxes:
            self.assertGreaterEqual(box.x(), 0)
            self.assertGreaterEqual(box.y(), 0)
            self.assertLessEqual(box.x() + box.width(), area.width())
            self.assertLessEqual(box.y() + box.height(), area.height())
        shown = {"1": {"x": 0, "y": 1440}, "2": {"x": 0, "y": 0}}
        placed = self.backend.snapDisplay(1, 2600, 20, shown)
        self.assertEqual(sorted((p["id"], p["x"], p["y"]) for p in placed), [(1, 2560, 0), (2, 0, 0)])
        self.assertEqual(self.problems(), [])

    def test_display_follows_screens(self):
        # A monitor plugged in or Windows + P while Display is open: the page
        # reads the displays again, once for a burst of changes.
        import json
        import time
        from PySide6.QtCore import QObject, Signal
        from test_devices import two_screens

        class Screen(QObject):
            geometryChanged = Signal()

        class App(QObject):
            screenAdded = Signal(QObject)
            screenRemoved = Signal(QObject)
            primaryScreenChanged = Signal(QObject)

            def __init__(self):
                super().__init__()
                self.first = Screen()

            def screens(self):
                return [self.first]

        def reads():
            return self.system.commands.count(["kscreen-doctor", "--json"])

        def settle():
            for _ in range(5):
                time.sleep(0.02)
                self.app.processEvents()

        self.system.outputs[("kscreen-doctor", "--json")] = json.dumps({"outputs": two_screens(True, 1920)})
        fake = App()
        self.backend.follow_screens(fake, delay=1)
        fake.first.geometryChanged.emit()
        settle()
        self.assertEqual(reads(), 0)                     # Display never shown: nothing read
        self.backend.refreshDisplay()
        before = reads()
        fake.first.geometryChanged.emit()
        second = Screen()
        fake.screenAdded.emit(second)
        fake.primaryScreenChanged.emit(second)
        settle()
        self.assertEqual(reads(), before + 1)
        second.geometryChanged.emit()                     # the added screen is watched too
        settle()
        self.assertEqual(reads(), before + 2)

    def test_every_page_loads(self):
        for page in self.backend.pages:
            self.show(page["id"])
            self.assertEqual(self.window.property("pageId"), page["id"])
        for page, sub in (("system", "about"), ("system", "storage"), ("apps", "windows-apps"),
                          ("system", "display"), ("system", "sound"), ("devices", "bluetooth"),
                          ("network", "wifi"), ("network", "hotspot"), ("apps", "veltosai"), ("personalization", "background"),
                          ("personalization", "colours"), ("time", "datetime"),
                          ("system", "notifications"), ("system", "power"), ("system", "nightlight"),
                          ("system", "multitasking"), ("devices", "mouse"), ("devices", "touchpad"),
                          ("devices", "keyboard"), ("personalization", "lockscreen"),
                          ("apps", "defaultapps"), ("apps", "startup"), ("accounts", "yourinfo"),
                          ("accounts", "signin"), ("accounts", "otherusers"), ("time", "region"),
                          ("accessibility", "accessibility"), ("privacy", "searching"),
                          ("privacy", "location"),
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

    def test_turkish_q_is_offered_first_and_can_be_added(self):
        # Product owner, 2026-10-26: Turkish Q, at the top of "Add a keyboard",
        # was preselected, so choosing it did nothing and it was never added.
        self.backend.setLayouts(["us"])
        self.app.processEvents()
        self.show("time", "keyboard")
        combos = self.items("addKeyboard")
        self.assertEqual(len(combos), 1)
        combo = combos[0]
        self.assertEqual(combo.property("currentIndex"), -1)
        self.assertEqual(combo.property("options").toVariant()[0]["value"], "tr")
        QMetaObject.invokeMethod(combo, "open")
        self.app.processEvents()
        lists = self.items("comboList")
        self.assertEqual(len(lists), 1)
        QMetaObject.invokeMethod(lists[0], "choose", Q_ARG("QVariant", 0))
        self.app.processEvents()
        self.assertEqual(self.backend.prefs["layouts"], ["us", "tr"])
        commands = [" ".join(c) for c in self.system.commands]
        self.assertIn("kwriteconfig6 --notify --file kxkbrc --group Layout --key LayoutList us,tr", commands)
        # Turkish Q is now listed and no longer offered; Turkish F comes first.
        self.assertEqual(combo.property("options").toVariant()[0]["value"], "tr(f)")
        self.assertEqual(combo.property("currentIndex"), -1)
        self.assertEqual(self.problems(), [])

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
        # Chosen again: applied again (the taskbar may be in the other mode
        # while the global theme says dark).
        self.system.commands.clear()
        self.backend.setDarkMode(True)
        self.app.processEvents()
        self.assertTrue(any(c[:2] == ["sh", "-c"] for c in self.system.commands))
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
        self.assertIn("bluetoothctl --timeout 8 scan on", commands)
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
        # The scan's own lines (bluetoothctl 5.82): the paired headset seen
        # again, a keyboard, a nameless device.
        self.system.outputs[("bluetoothctl", "--timeout", "8", "scan", "on")] = (
            "[CHG] Device AA:BB:CC:DD:EE:FF RSSI: -50\n[NEW] Device 77:88:99:AA:BB:CC Keyboard K380\n"
            "[NEW] Device 12:34:56:78:9A:BC 12-34-56-78-9A-BC\n")
        self.system.outputs[("bluetoothctl", "info", "77:88:99:AA:BB:CC")] = (
            "\tName: Keyboard K380\n\tIcon: input-keyboard\n\tPaired: no\n")
        self.system.outputs[("bluetoothctl", "info", "12:34:56:78:9A:BC")] = "\tAlias: 12-34-56-78-9A-BC\n"
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
