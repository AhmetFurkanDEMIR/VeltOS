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

    def test_discover_lists_named_devices_in_range(self):
        # bluetoothctl's scan output (5.82, colours as it prints them): a new
        # device with a name, one seen again (RSSI), a nameless one (its
        # address as alias), one only in bluetoothd's cache (no line in this
        # scan) and a paired one.
        scan = ("Discovery started\n"
                "[\x1b[0;92mNEW\x1b[0m] Device 0C:AE:B0:11:22:33 JBL Flip 6\n"
                "[\x1b[0;93mCHG\x1b[0m] Device 66:77:88:99:AA:BB RSSI: 0xffffffc4 (-60)\n"
                "[\x1b[0;92mNEW\x1b[0m] Device 5D:4E:3F:2A:1B:0C 5D-4E-3F-2A-1B-0C\n"
                "[\x1b[0;93mCHG\x1b[0m] Device AA:BB:CC:DD:EE:FF RSSI: -40\n"
                "[\x1b[0;93mCHG\x1b[0m] Device 0C:AE:B0:11:22:33 RSSI: -71\n")
        system = FakeSystem({
            ("bluetoothctl", "--timeout", "8", "scan", "on"): scan,
            ("bluetoothctl", "info", "0C:AE:B0:11:22:33"):
                "Device 0C:AE:B0:11:22:33 (public)\n\tName: JBL Flip 6\n\tAlias: JBL Flip 6\n"
                "\tIcon: audio-card\n\tPaired: no\n\tBlocked: no\n",
            ("bluetoothctl", "info", "66:77:88:99:AA:BB"):
                "Device 66:77:88:99:AA:BB (public)\n\tName: Galaxy Buds2\n\tAlias: Galaxy Buds2\n"
                "\tIcon: audio-headset\n\tPaired: no\n",
            ("bluetoothctl", "info", "5D:4E:3F:2A:1B:0C"):
                "Device 5D:4E:3F:2A:1B:0C (random)\n\tAlias: 5D-4E-3F-2A-1B-0C\n\tPaired: no\n",
        })
        found = devices.Bluetooth(system).discover()
        self.assertEqual(found, [
            {"mac": "66:77:88:99:AA:BB", "name": "Galaxy Buds2", "rssi": -60, "icon": "audio-headset"},
            {"mac": "0C:AE:B0:11:22:33", "name": "JBL Flip 6", "rssi": -71, "icon": "audio-card"},
        ])

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


def two_screens(hdmi_enabled=False, hdmi_x=0):
    """A laptop's screen (eDP, KScreen type Panel) and a monitor on HDMI."""
    laptop = {"id": 1, "name": "eDP-1", "type": 7, "connected": True, "enabled": True, "priority": 1, "scale": 1.0,
              "pos": {"x": 0, "y": 0}, "rotation": 1, "currentModeId": "1", "preferredModes": ["1"],
              "modes": [{"id": "1", "refreshRate": 60.0, "size": {"width": 1920, "height": 1080}},
                        {"id": "2", "refreshRate": 60.0, "size": {"width": 1280, "height": 720}}]}
    monitor = {"id": 2, "name": "HDMI-A-1", "type": 8, "connected": True, "enabled": hdmi_enabled,
               "priority": 2 if hdmi_enabled else 0, "scale": 1.0, "pos": {"x": hdmi_x, "y": 0}, "rotation": 1,
               "currentModeId": "10" if hdmi_enabled else "", "preferredModes": ["10"],
               "modes": [{"id": "10", "refreshRate": 60.0, "size": {"width": 2560, "height": 1440}},
                         {"id": "11", "refreshRate": 144.0, "size": {"width": 1920, "height": 1080}},
                         {"id": "12", "refreshRate": 60.0, "size": {"width": 1920, "height": 1080}},
                         {"id": "13", "refreshRate": 59.94, "size": {"width": 1920, "height": 1080}}]}
    return [laptop, monitor]


class RearrangeTests(unittest.TestCase):
    """Settings > Display: a dragged display snaps to an edge of another."""

    @staticmethod
    def screens(*boxes):
        return [{"id": i + 1, "enabled": True, "x": x, "y": y, "width": w, "height": h}
                for i, (x, y, w, h) in enumerate(boxes)]

    def test_dropped_beside_below_and_above(self):
        outputs = self.screens((0, 0, 1920, 1080), (1920, 0, 1280, 1024))
        # Dropped to the left of display 1, a little low: it goes left, its
        # top lined up with display 1's top (within SNAP), and display 1
        # moves right so the left one starts at 0.
        self.assertEqual(devices.snap_position(outputs, 2, -1300, 25),
                         [{"id": 1, "x": 1280, "y": 0}, {"id": 2, "x": 0, "y": 0}])
        # Dropped under display 1, off to the right: below it, touching it.
        self.assertEqual(devices.snap_position(outputs, 2, 1200, 1300),
                         [{"id": 1, "x": 0, "y": 0}, {"id": 2, "x": 1200, "y": 1080}])
        # Dropped far above: on top, display 1 below it.
        self.assertEqual(devices.snap_position(outputs, 2, 300, -2000),
                         [{"id": 1, "x": 0, "y": 1024}, {"id": 2, "x": 300, "y": 0}])
        # Dropped on top of display 1: the nearest free edge, never covering it.
        placed = {p["id"]: p for p in devices.snap_position(outputs, 2, 500, 100)}
        a, b = placed[1], placed[2]
        overlap = (a["x"] < b["x"] + 1280 and b["x"] < a["x"] + 1920 and a["y"] < b["y"] + 1024
                   and b["y"] < a["y"] + 1080)
        self.assertFalse(overlap)

    def test_keeps_touching_and_ignores_unused_displays(self):
        outputs = self.screens((0, 0, 1920, 1080), (1920, 0, 1280, 1024))
        # Dropped far away to the right and below: still touching display 1.
        placed = devices.snap_position(outputs, 2, 5000, 3000)
        self.assertEqual(placed, [{"id": 1, "x": 0, "y": 0}, {"id": 2, "x": 1920, "y": 1079}])
        outputs.append({"id": 3, "enabled": False, "x": 0, "y": 0, "width": 800, "height": 600})
        self.assertEqual([p["id"] for p in devices.snap_position(outputs, 2, 1920, 0)], [1, 2])
        self.assertEqual(devices.snap_position(outputs[:1], 1, 50, 50), [{"id": 1, "x": 0, "y": 0}])

    def test_positions_in_one_kscreen_call(self):
        system = FakeSystem()
        display = devices.Display(system)
        self.assertTrue(display.set_positions([{"id": 1, "x": 1280, "y": 0}, {"id": 2, "x": 0, "y": 0}]))
        self.assertEqual(system.commands[-1],
                         ["kscreen-doctor", "output.1.position.1280,0", "output.2.position.0,0"])
        self.assertFalse(display.set_positions([]))


class MultipleDisplaysTests(unittest.TestCase):
    """Windows' Project choices (Windows + P, Settings > Display > Multiple
    displays) as kscreen-doctor arguments."""

    def test_modes_and_plans(self):
        outputs = two_screens()                      # monitor plugged in, still off
        self.assertEqual([o["name"] for o in devices.numbered(outputs)], ["eDP-1", "HDMI-A-1"])
        self.assertEqual(devices.project_mode(outputs), "pc")
        self.assertEqual(devices.project_plan(outputs, "extend"), [
            "output.1.enable", "output.1.mode.1", "output.1.position.0,0", "output.1.priority.1",
            "output.2.enable", "output.2.mode.10", "output.2.position.1920,0"])
        self.assertEqual(devices.project_plan(outputs, "second"), [
            "output.2.enable", "output.2.mode.10", "output.2.position.0,0", "output.2.priority.1",
            "output.1.disable"])
        # Duplicate: the largest resolution both have, at the same place.
        self.assertEqual(devices.project_plan(outputs, "duplicate"), [
            "output.1.enable", "output.1.mode.1", "output.1.position.0,0", "output.1.priority.1",
            "output.2.enable", "output.2.mode.11", "output.2.position.0,0"])
        extended = two_screens(True, 1920)
        self.assertEqual(devices.project_mode(extended), "extend")
        self.assertEqual(devices.project_plan(extended, "pc"), [
            "output.1.enable", "output.1.mode.1", "output.1.position.0,0", "output.1.priority.1",
            "output.2.disable"])
        self.assertEqual(devices.project_mode(two_screens(True, 0)), "duplicate")
        second = two_screens(True, 0)
        second[0]["enabled"] = False
        self.assertEqual(devices.project_mode(second), "second")
        self.assertEqual(devices.project_plan(outputs[:1], "extend"), [])      # one screen: nothing to do
        self.assertEqual(devices.project_plan(outputs, "rm -rf"), [])

    def test_numbers_stay_when_another_display_is_main(self):
        # Windows keeps display numbers; numbering by the main display made
        # Settings show display 1's settings after "Make this my main
        # display" on display 2 (VM 2026-10-25).
        outputs = two_screens(True, 1920)
        outputs[0]["type"], outputs[0]["name"] = 8, "DP-1"         # a desktop PC: no laptop screen
        outputs[0]["priority"], outputs[1]["priority"] = 2, 1
        self.assertEqual([o["name"] for o in devices.numbered(outputs)], ["DP-1", "HDMI-A-1"])
        self.assertEqual(devices.project_mode(outputs), "extend")
        # Extend again from Duplicate keeps the main display.
        for output in outputs:
            output["pos"] = {"x": 0, "y": 0}
        plan = devices.project_plan(outputs, "extend")
        self.assertIn("output.2.priority.1", plan)
        self.assertNotIn("output.1.priority.1", plan)
        # Second screen only: display 2 alone is still "second", not "pc".
        outputs[0]["enabled"], outputs[0]["priority"] = False, 0
        self.assertEqual(devices.project_mode(outputs), "second")
        # Extend from there: display 1 is the main one again.
        plan = devices.project_plan(outputs, "extend")
        self.assertIn("output.1.priority.1", plan)
        self.assertNotIn("output.2.priority.1", plan)

    def test_duplicate_stays_within_preferred_sizes(self):
        # Virtual screens (QEMU, VM 2026-10-25) list modes up to 5120x2160
        # whatever their preferred size: Duplicate drove both at 4096x2160.
        def virtual(ident, preferred, enabled, x):
            sizes = [(5120, 2160), (4096, 2160), (1920, 1080), (1024, 768), (800, 600)]
            modes = [{"id": f"{ident}{i}", "refreshRate": 60.0, "size": {"width": w, "height": h}}
                     for i, (w, h) in enumerate(sizes)]
            return {"id": ident, "name": f"Virtual-{ident}", "type": 0, "connected": True, "enabled": enabled,
                    "priority": ident, "scale": 1.0, "pos": {"x": x, "y": 0}, "rotation": 1,
                    "currentModeId": f"{ident}{sizes.index(preferred)}",
                    "preferredModes": [f"{ident}{sizes.index(preferred)}"], "modes": modes}
        outputs = [virtual(1, (1920, 1080), True, 0), virtual(2, (1024, 768), True, 1920)]
        self.assertEqual(devices.project_plan(outputs, "duplicate"), [
            "output.1.enable", "output.1.mode.13", "output.1.position.0,0", "output.1.priority.1",
            "output.2.enable", "output.2.mode.23", "output.2.position.0,0"])
        # Leaving Duplicate, every screen goes back to its preferred size.
        for output in outputs:
            output["pos"] = {"x": 0, "y": 0}
            output["currentModeId"] = f"{output['id']}3"
        self.assertEqual(devices.project_plan(outputs, "extend"), [
            "output.1.enable", "output.1.mode.12", "output.1.position.0,0", "output.1.priority.1",
            "output.2.enable", "output.2.mode.23", "output.2.position.1920,0"])

    def test_state_and_actions(self):
        system = FakeSystem({("kscreen-doctor", "--json"): json.dumps({"outputs": two_screens(True, 1920)})})
        display = devices.Display(system)
        state = display.state()
        self.assertEqual((state["count"], state["project"]), (2, "extend"))
        laptop, monitor = state["outputs"]
        self.assertEqual((laptop["number"], laptop["internal"], laptop["primary"]), (1, True, True))
        self.assertEqual((monitor["number"], monitor["x"], monitor["width"], monitor["height"]), (2, 1920, 2560, 1440))
        self.assertEqual(monitor["rotation"], "none")
        # Refresh rates of the current resolution, rounded and once each.
        rotated = two_screens(True, 1920)
        rotated[1]["currentModeId"] = "12"
        rotated[1]["rotation"] = 2
        system = FakeSystem({("kscreen-doctor", "--json"): json.dumps({"outputs": rotated})})
        monitor = devices.Display(system).state()["outputs"][1]
        self.assertEqual([r["label"] for r in monitor["rates"]], ["144 Hz", "60 Hz"])
        self.assertEqual((monitor["rotation"], monitor["width"], monitor["height"]), ("left", 1080, 1920))
        display = devices.Display(system)
        display.set_primary(2)
        display.set_rotation(2, "right")
        self.assertFalse(display.set_rotation(2, "upside"))
        display.project("pc")
        changes = [c for c in system.commands if c != ["kscreen-doctor", "--json"]]
        self.assertEqual(changes[-3:], [
            ["kscreen-doctor", "output.2.priority.1"], ["kscreen-doctor", "output.2.rotation.right"],
            ["kscreen-doctor", "output.1.enable", "output.1.mode.1", "output.1.position.0,0", "output.1.priority.1",
             "output.2.disable"]])


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
