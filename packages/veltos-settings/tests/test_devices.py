"""Tests for devices.py: parsing the tools' output and the commands it runs."""

import datetime
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakesystem import SCREENS, FakeSystem  # noqa: E402
from veltos_settings import devices  # noqa: E402


class TerseTests(unittest.TestCase):
    def test_escaped_colons(self):
        self.assertEqual(devices.split_terse("a\\:b:c::d"), ["a:b", "c", "", "d"])
        self.assertEqual(devices.split_terse("back\\\\slash"), ["back\\slash"])


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.system = FakeSystem()
        self.net = devices.Network(self.system)

    def test_state(self):
        state = self.net.state()
        self.assertTrue(state["available"])
        self.assertTrue(state["enabled"])
        self.assertEqual(state["connection"], {"type": "wifi", "name": "Home Net"})
        names = [n["ssid"] for n in state["networks"]]
        # Connected first, then by signal; duplicates and hidden networks dropped.
        self.assertEqual(names, ["Home Net", "New Net", "Cafe:Free", "Office"])
        home, new, cafe, office = state["networks"]
        self.assertTrue(home["active"] and home["saved"] and home["secure"])
        self.assertEqual(home["signal"], 82)
        self.assertTrue(cafe["saved"])
        self.assertFalse(cafe["secure"])
        self.assertTrue(office["enterprise"])
        self.assertFalse(new["saved"])

    def test_wifi_off_lists_nothing(self):
        system = FakeSystem({("nmcli", "-t", "-f", "WIFI", "radio"): "disabled\n"})
        state = devices.Network(system).state()
        self.assertFalse(state["enabled"])
        self.assertEqual(state["networks"], [])
        self.assertFalse(any("list" in c for c in system.commands))

    def test_no_wifi_adapter(self):
        system = FakeSystem({("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"):
                             "enp1s0:ethernet:connected:Wired connection 1\n"})
        state = devices.Network(system).state()
        self.assertFalse(state["available"])
        self.assertEqual(state["connection"], {"type": "ethernet", "name": "Wired connection 1"})

    def test_missing_nmcli(self):
        state = devices.Network(FakeSystem(fail={"nmcli"})).state()
        self.assertEqual(state, {"available": False, "enabled": False, "connection": {}, "networks": []})

    def test_new_network_key_goes_to_networkmanager_not_to_a_command(self):
        activated = []
        net = devices.Network(self.system, activate=lambda *args: activated.append(args) or True)
        self.assertTrue(net.connect("New Net", "correct horse", "WPA3"))
        self.assertTrue(net.connect("Old Router", "correct horse", "WPA1 WPA2"))
        self.assertEqual(activated, [("New Net", "correct horse", "sae"),
                                     ("Old Router", "correct horse", "wpa-psk")])
        for command in self.system.commands:
            self.assertNotIn("correct horse", " ".join(command))

    def test_wrong_key(self):
        net = devices.Network(self.system, activate=lambda *args: False)
        self.assertFalse(net.connect("New Net", "wrong key", "WPA2"))

    def test_without_networkmanager_bindings_connecting_fails_cleanly(self):
        # In the build container there is no system bus: no exception.
        self.assertIn(devices.nm_add_and_activate("New Net", "key", "wpa-psk", timeout=1), (False, True))

    def test_saved_and_open_networks(self):
        self.assertTrue(self.net.connect("Home Net"))
        self.assertIn(["nmcli", "connection", "up", "uuid", "1111-aaaa"], self.system.commands)
        self.assertTrue(self.net.connect("Library"))
        self.assertIn(["nmcli", "device", "wifi", "connect", "Library"], self.system.commands)

    def test_disconnect_and_forget(self):
        self.assertTrue(self.net.disconnect())
        self.assertIn(["nmcli", "device", "disconnect", "wlp2s0"], self.system.commands)
        self.assertTrue(self.net.forget("Cafe:Free"))
        self.assertIn(["nmcli", "connection", "delete", "uuid", "3333-cccc"], self.system.commands)
        self.assertFalse(self.net.forget("Unknown"))


class BluetoothTests(unittest.TestCase):
    def test_state(self):
        state = devices.Bluetooth(FakeSystem()).state()
        self.assertTrue(state["available"] and state["powered"])
        headset, mouse = state["devices"]
        self.assertEqual(headset, {"mac": "AA:BB:CC:DD:EE:FF", "name": "WH-1000XM4", "connected": True,
                                   "icon": "audio-headset", "battery": 80})
        self.assertFalse(mouse["connected"])
        self.assertEqual(mouse["battery"], -1)

    def test_no_adapter(self):
        system = FakeSystem({("bluetoothctl", "list"): ""})
        self.assertEqual(devices.Bluetooth(system).state(),
                         {"available": False, "powered": False, "devices": []})

    def test_no_adapter_in_the_kernel_skips_bluetoothctl(self):
        # bluetoothctl would wait for a bluetoothd that never starts.
        saved = devices.BLUETOOTH_SYSFS
        devices.BLUETOOTH_SYSFS = Path(tempfile.mkdtemp())
        try:
            system = FakeSystem()
            self.assertFalse(devices.Bluetooth(system).state()["available"])
            self.assertEqual(system.commands, [])
        finally:
            devices.BLUETOOTH_SYSFS = saved

    def test_actions(self):
        system = FakeSystem()
        bt = devices.Bluetooth(system)
        bt.set_powered(False)
        bt.connect("AA:BB:CC:DD:EE:FF", False)
        bt.remove("11:22:33:44:55:66")
        self.assertEqual(system.commands, [["bluetoothctl", "power", "off"],
                                           ["bluetoothctl", "disconnect", "AA:BB:CC:DD:EE:FF"],
                                           ["bluetoothctl", "remove", "11:22:33:44:55:66"]])


class SoundTests(unittest.TestCase):
    def test_state(self):
        state = devices.Sound(FakeSystem()).state()
        speakers, headset = state["outputs"]
        self.assertEqual(speakers["description"], "Speakers (Built-in Audio)")
        self.assertTrue(speakers["default"])
        self.assertEqual(speakers["volume"], 65)
        self.assertTrue(headset["muted"])
        self.assertEqual([d["name"] for d in state["inputs"]], ["alsa_input.pci-0000_00_1f.3.analog-stereo"])

    def test_bad_output(self):
        system = FakeSystem({("pactl", "--format=json", "list", "sinks"): "not json"})
        self.assertEqual(devices.Sound(system).state()["outputs"], [])

    def test_actions(self):
        system = FakeSystem()
        sound = devices.Sound(system)
        sound.set_volume("sink", 130)
        sound.set_muted("source", True)
        sound.set_default("sink", "bluez_output.AA_BB_CC_DD_EE_FF.1")
        self.assertEqual(system.commands, [
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"],
            ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "1"],
            ["pactl", "set-default-sink", "bluez_output.AA_BB_CC_DD_EE_FF.1"]])
        with self.assertRaises(ValueError):
            sound.set_volume("all", 10)


class DisplayTests(unittest.TestCase):
    def test_state(self):
        state = devices.Display(FakeSystem()).state()
        self.assertEqual(len(state["outputs"]), 1)
        screen = state["outputs"][0]
        self.assertEqual(screen["scale"], 1.25)
        self.assertEqual(screen["scales"], devices.SCALES)
        self.assertEqual(screen["currentMode"], "3")
        self.assertEqual(screen["currentLabel"], "1280 × 720")
        # One entry per resolution, the highest refresh rate, largest first.
        self.assertEqual([m["id"] for m in screen["modes"]], ["1", "3"])
        self.assertTrue(screen["modes"][0]["recommended"])

    def test_unusual_scale_is_offered(self):
        screens = {"outputs": [dict(SCREENS["outputs"][0], scale=1.05)]}
        system = FakeSystem({("kscreen-doctor", "--json"): json.dumps(screens)})
        screen = devices.Display(system).state()["outputs"][0]
        self.assertEqual(screen["scale"], 1.05)
        self.assertEqual(screen["scales"][:2], [1.0, 1.05])

    def test_actions(self):
        system = FakeSystem()
        display = devices.Display(system)
        display.set_scale(1, 1.5)
        display.set_mode(1, "1")
        self.assertFalse(display.set_mode(1, "1; rm -rf /"))
        self.assertEqual(system.commands, [["kscreen-doctor", "output.1.scale.1.5"],
                                           ["kscreen-doctor", "output.1.mode.1"]])


class PersonalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old_dirs = devices.WALLPAPER_DIRS
        self.old_config = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.tmp / "config")
        (self.tmp / "config").mkdir()
        walls = self.tmp / "wallpapers"
        for name, files in (("Next", ["1920x1080.png"]), ("VeltOS", ["1920x1080.png"]),
                            ("VeltOS-Flow", ["1920x1080.png"]),
                            ("Ocean", ["1920x1080.png", "3840x2160.png"]), ("Empty", [])):
            images = walls / name / "contents" / "images"
            images.mkdir(parents=True)
            for index, file in enumerate(files):
                (images / file).write_bytes(b"x" * (index + 1) * 10)
        devices.WALLPAPER_DIRS = [walls]

    def tearDown(self):
        devices.WALLPAPER_DIRS = self.old_dirs
        if self.old_config is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.old_config

    def test_wallpapers(self):
        walls = devices.Personalization(FakeSystem()).wallpapers()
        # VeltOS first, KDE's own "Next" left out.
        self.assertEqual([w["name"] for w in walls], ["VeltOS", "Ocean", "VeltOS-Flow"])
        self.assertTrue(walls[1]["preview"].endswith("3840x2160.png"))

    def test_current_wallpaper_and_accent(self):
        personal = devices.Personalization(FakeSystem())
        self.assertEqual(personal.current_wallpaper(), "")
        self.assertEqual(personal.accent(), "")
        config = self.tmp / "config"
        (config / "plasma-org.kde.plasma.desktop-appletsrc").write_text(
            "[Containments][1][Wallpaper][org.kde.image][General]\n"
            "Image=file:///usr/share/wallpapers/Next/\n", encoding="utf-8")
        (config / "kdeglobals").write_text(
            "[General]\nAccentColor=0,120,212\n\n[KDE]\nLookAndFeelPackage=org.veltos.light\n",
            encoding="utf-8")
        self.assertEqual(personal.current_wallpaper(), "/usr/share/wallpapers/Next")
        self.assertEqual(personal.accent(), "#0078D4")

    def test_actions(self):
        system = FakeSystem()
        personal = devices.Personalization(system)
        personal.set_wallpaper("/usr/share/wallpapers/Next")
        personal.set_accent("#0078D4")
        self.assertFalse(personal.set_accent("red; reboot"))
        self.assertEqual(system.commands, [["plasma-apply-wallpaperimage", "/usr/share/wallpapers/Next"],
                                           ["plasma-apply-colorscheme", "--accent-color", "#0078D4"],
                                           ["kwriteconfig6", "--file", "kdeglobals", "--group", "General",
                                            "--key", "AccentColor", "0,120,212"],
                                           # running programs (the taskbar) hear about it at once
                                           ["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
                                            "org.kde.KGlobalSettings.notifyChange", "int32:0", "int32:0"]])


class TimeTests(unittest.TestCase):
    def test_state(self):
        now = datetime.datetime(2026, 1, 15, 12, 0, tzinfo=datetime.timezone.utc)
        system = FakeSystem()
        time = devices.Time(system)
        status = time.status()
        self.assertEqual(status, {"timezone": "Europe/Istanbul", "automatic": True, "canAutomatic": True})
        zones = time.timezones(now)
        if devices.utc_offset("Europe/Istanbul", now) is None:
            self.skipTest("no time zone data")
        self.assertEqual([z["value"] for z in zones],
                         ["America/New_York", "Europe/London", "UTC", "Europe/Istanbul"])
        self.assertEqual(zones[0]["label"], "(UTC-05:00) New York (America)")
        self.assertEqual(zones[-1]["label"], "(UTC+03:00) Istanbul (Europe)")
        self.assertEqual(zones[2]["label"], "(UTC+00:00) UTC")

    def test_set_timezone_only_known_zones(self):
        system = FakeSystem()
        time = devices.Time(system)
        self.assertFalse(time.set_timezone("../../etc/passwd"))
        self.assertTrue(time.set_timezone("Europe/London"))
        self.assertIn(["timedatectl", "set-timezone", "Europe/London"], system.commands)
        time.set_automatic(False)
        self.assertEqual(system.commands[-1], ["timedatectl", "set-ntp", "false"])


class ThemeTests(unittest.TestCase):
    def test_current_theme(self):
        # Default desktop: no wallpaper or accent written yet.
        self.assertEqual(devices.current_theme("", False, ""), "veltos-light")
        self.assertEqual(devices.current_theme("VeltOS", True, ""), "veltos-dark")
        self.assertEqual(devices.current_theme("/usr/share/wallpapers/VeltOS-Ember/", True, "#d6243b"), "ember")
        self.assertEqual(devices.current_theme("/usr/share/wallpapers/VeltOS-Ember", False, "#D6243B"), "")
        self.assertEqual(devices.current_theme("/home/u/Pictures/cat.jpg", False, "#2F5EE6"), "")

    def test_themes_are_complete(self):
        ids = [t["id"] for t in devices.THEMES]
        self.assertEqual(len(ids), len(set(ids)))
        for theme in devices.THEMES:
            self.assertRegex(theme["accent"], r"^#[0-9A-F]{6}$")
            self.assertEqual(len(theme["title"]), 2)
            self.assertEqual(len(theme["colour"]), 2)
            self.assertTrue(theme["wallpaper"].startswith("VeltOS"))

    def test_apply_theme_order(self):
        system = FakeSystem()
        devices.Personalization(system).apply_theme("/usr/share/wallpapers/VeltOS-Tide", "#12949B",
                                                     ["sh", "-c", "mode"])
        self.assertEqual([c[0] for c in system.commands],
                         ["sh", "plasma-apply-wallpaperimage", "plasma-apply-colorscheme", "kwriteconfig6",
                          "dbus-send"])
        self.assertEqual(system.commands[-2][-2:], ["AccentColor", "18,148,155"])
        self.assertEqual(system.commands[-1], devices.PALETTE_CHANGED)       # the taskbar hears it at once


if __name__ == "__main__":
    unittest.main()
