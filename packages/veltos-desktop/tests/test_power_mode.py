"""Tests for the power-mode helper: a mode for plugged in and one for
battery, switched with the power source (system/power-mode)."""

import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("power_mode", str(PKG / "system/power-mode"))
spec = importlib.util.spec_from_loader(loader.name, loader)
power_mode = importlib.util.module_from_spec(spec)
loader.exec_module(power_mode)


class PowerProfileRunner:
    """powerprofilesctl 0.30 (Debian 13) as seen in the dev VM."""

    def __init__(self, profiles, active="balanced", fail_set=False):
        self.profiles = profiles
        self.active = active
        self.fail_set = fail_set
        self.commands = []

    def __call__(self, command):
        self.commands.append(command)
        if command == ["powerprofilesctl", "list"]:
            output = "\n".join(
                f"{'* ' if profile == self.active else '  '}{profile}:"
                for profile in self.profiles)
            return 0, output, ""
        if command == ["powerprofilesctl", "get"]:
            return 0, self.active + "\n", ""
        if len(command) == 3 and command[:2] == ["powerprofilesctl", "set"]:
            if self.fail_set or command[2] not in self.profiles:
                return 1, "", "profile change failed"
            self.active = command[2]
            return 0, "", ""
        raise AssertionError(f"Unexpected command: {command}")


def supplies(root, battery=True, plugged=True):
    """A laptop's /sys/class/power_supply: BAT0, AC, and a mouse's battery."""
    root = Path(root)
    entries = {"hidpp_battery_0": {"type": "Battery", "scope": "Device", "present": "1"}}
    if battery:
        entries["BAT0"] = {"type": "Battery", "present": "1"}
    entries["AC"] = {"type": "Mains", "online": "1" if plugged else "0"}
    for name, values in entries.items():
        (root / name).mkdir(parents=True, exist_ok=True)
        for key, value in values.items():
            (root / name / key).write_text(value + "\n")
    return root


class PowerModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = self.tmp / "veltos" / "power-modes.json"

    def run_helper(self, args, runner, battery=True, plugged=True):
        root = supplies(self.tmp / ("sys-" + str(battery) + str(plugged)), battery, plugged)
        return power_mode.run(args, runner, config=self.config, supply_root=root)

    def test_profile_parser_reads_active_mode_and_ignores_unknown_profiles(self):
        profiles, active = power_mode.parse_profiles(
            "  performance:\n    Driver: placeholder\n"
            "* balanced:\n    Driver: placeholder\n"
            "  power-saver:\n")
        self.assertEqual(profiles, ["power-saver", "balanced", "performance"])
        self.assertEqual(active, "balanced")

    def test_power_source_from_sysfs(self):
        self.assertEqual(power_mode.power_source(supplies(self.tmp / "a", True, True)), ("ac", True))
        self.assertEqual(power_mode.power_source(supplies(self.tmp / "b", True, False)), ("battery", True))
        # A desktop PC (only a mouse's battery) is always plugged in.
        self.assertEqual(power_mode.power_source(supplies(self.tmp / "c", False, False)), ("ac", False))
        self.assertEqual(power_mode.power_source(self.tmp / "missing"), ("ac", False))

    def test_defaults_follow_the_source_and_fall_back_to_balanced(self):
        profiles = ["power-saver", "balanced"]
        self.assertEqual(power_mode.automatic_profile(False, profiles), "balanced")
        self.assertEqual(power_mode.automatic_profile(True, profiles), "power-saver")
        self.assertEqual(power_mode.automatic_profile(False, ["power-saver"]), "power-saver")
        self.assertEqual(power_mode.automatic_profile(True, []), "")

    def test_auto_applies_the_mode_chosen_for_each_source(self):
        runner = PowerProfileRunner(["power-saver", "balanced", "performance"])
        result = self.run_helper(["auto"], runner, plugged=False)
        self.assertTrue(result["success"])
        self.assertEqual((result["source"], result["active"]), ("battery", "power-saver"))
        result = self.run_helper(["auto"], runner, plugged=True)
        self.assertEqual((result["source"], result["active"]), ("ac", "performance"))
        # The battery model may name the source itself.
        result = self.run_helper(["auto", "battery"], runner, plugged=True)
        self.assertEqual(result["active"], "power-saver")

    def test_prefer_keeps_choices_per_source_and_applies_only_the_current_one(self):
        runner = PowerProfileRunner(["power-saver", "balanced", "performance"], active="performance")
        result = self.run_helper(["prefer", "battery", "balanced"], runner, plugged=True)
        self.assertTrue(result["success"])
        self.assertEqual(result["modes"], {"ac": "performance", "battery": "balanced"})
        self.assertEqual(result["active"], "performance")      # plugged in: unchanged
        self.assertNotIn(["powerprofilesctl", "set", "balanced"], runner.commands)
        result = self.run_helper(["auto"], runner, plugged=False)
        self.assertEqual(result["active"], "balanced")
        self.assertEqual(json.loads(self.config.read_text()), {"ac": "performance", "battery": "balanced"})

    def test_set_chooses_for_the_current_source(self):
        runner = PowerProfileRunner(["power-saver", "balanced", "performance"])
        result = self.run_helper(["set", "power-saver"], runner, plugged=True)
        self.assertEqual(result["modes"]["ac"], "power-saver")
        self.assertEqual(result["active"], "power-saver")

    def test_a_desktop_pc_uses_the_plugged_in_mode(self):
        runner = PowerProfileRunner(["power-saver", "balanced"])
        result = self.run_helper(["status"], runner, battery=False, plugged=False)
        self.assertEqual((result["source"], result["hasBattery"]), ("ac", False))
        result = self.run_helper(["auto"], runner, battery=False, plugged=False)
        self.assertEqual(result["active"], "balanced")          # no performance profile here

    def test_unsupported_modes_are_refused_and_failures_reported(self):
        runner = PowerProfileRunner(["balanced", "power-saver"], fail_set=True)
        result = self.run_helper(["set", "performance"], runner)
        self.assertFalse(result["success"])
        self.assertFalse(any(command[1:2] == ["set"] for command in runner.commands))
        self.assertFalse(self.config.exists())
        result = self.run_helper(["set", "power-saver"], runner)
        self.assertFalse(result["success"])
        self.assertIn("failed", result["error"])
        self.assertFalse(self.run_helper(["nonsense"], runner)["success"])

    def test_broken_choices_file_gives_the_defaults(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text("{not json")
        self.assertEqual(power_mode.load_modes(self.config), power_mode.DEFAULT_MODES)
        self.config.write_text(json.dumps({"ac": "turbo", "battery": "balanced"}))
        self.assertEqual(power_mode.load_modes(self.config), {"ac": "performance", "battery": "balanced"})


if __name__ == "__main__":
    unittest.main()
