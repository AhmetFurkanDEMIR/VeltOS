"""Tests for the AC/battery power-profile helper."""

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("power_mode", str(PKG / "system/power-mode"))
spec = importlib.util.spec_from_loader(loader.name, loader)
power_mode = importlib.util.module_from_spec(spec)
loader.exec_module(power_mode)


class PowerProfileRunner:
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


class PowerModeTests(unittest.TestCase):
    def test_profile_parser_reads_active_mode_and_ignores_unknown_profiles(self):
        profiles, active = power_mode.parse_profiles(
            "  performance:\n    Driver: placeholder\n"
            "* balanced:\n    Driver: placeholder\n"
            "  power-saver:\n")
        self.assertEqual(profiles, ["power-saver", "balanced", "performance"])
        self.assertEqual(active, "balanced")

    def test_automatic_selection_uses_supported_modes_and_balanced_fallback(self):
        profiles = ["power-saver", "balanced"]
        self.assertEqual(power_mode.automatic_profile(False, profiles), "balanced")
        self.assertEqual(power_mode.automatic_profile(True, profiles), "power-saver")
        self.assertEqual(power_mode.automatic_profile(False, ["power-saver"]), "power-saver")
        self.assertEqual(power_mode.automatic_profile(True, []), "")

    def test_automatic_mode_sets_supported_profile_and_verifies_it(self):
        runner = PowerProfileRunner(["power-saver", "balanced"], active="power-saver")
        result = power_mode.run(["auto", "ac"], runner)
        self.assertTrue(result["success"])
        self.assertEqual(result["active"], "balanced")
        self.assertIn(["powerprofilesctl", "set", "balanced"], runner.commands)

        runner = PowerProfileRunner(["power-saver", "balanced"])
        result = power_mode.run(["auto", "battery"], runner)
        self.assertTrue(result["success"])
        self.assertEqual(result["active"], "power-saver")
        self.assertIn(["powerprofilesctl", "set", "power-saver"], runner.commands)

    def test_manual_selection_rejects_unsupported_modes_and_reports_failures(self):
        runner = PowerProfileRunner(["balanced", "power-saver"], fail_set=True)
        result = power_mode.run(["set", "performance"], runner)
        self.assertFalse(result["success"])
        self.assertFalse(any(command[1:2] == ["set"] for command in runner.commands))

        result = power_mode.run(["set", "power-saver"], runner)
        self.assertFalse(result["success"])
        self.assertIn("failed", result["error"])


if __name__ == "__main__":
    unittest.main()
