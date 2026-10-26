"""The chooser shown when a screen is plugged in (kscreen_osd.py): KScreen's
interface, the Project flyout started once and closed on hideOsd, and the
systemd drop-in that gives VeltOS KScreen's bus name."""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG))

from veltos_settings import kscreen_osd  # noqa: E402


class FakeProcess:
    def __init__(self):
        self.running = True

    def poll(self):
        return None if self.running else 0

    def terminate(self):
        self.running = False


class OsdTests(unittest.TestCase):
    def setUp(self):
        self.started = []

        def start(command):
            self.started.append(command)
            return FakeProcess()
        self.service = kscreen_osd.OsdService(start)

    def test_interface_is_kscreens(self):
        interface = ET.fromstring(kscreen_osd.INTERFACE).find("interface")
        self.assertEqual(interface.get("name"), kscreen_osd.BUS_NAME)
        self.assertEqual(sorted(m.get("name") for m in interface.findall("method")),
                         ["hideOsd", "showActionSelector"])
        self.assertEqual(kscreen_osd.OBJECT_PATH, "/org/kde/kscreen/osdService")

    def test_show_starts_the_project_flyout_once_and_hide_closes_it(self):
        self.service.call("showActionSelector")
        self.service.call("showActionSelector")
        self.assertEqual(self.started, [["veltos-settings", "--project"]])
        flyout = self.service.flyout
        self.service.call("hideOsd")
        self.assertFalse(flyout.running)
        self.assertFalse(self.service.showing())
        self.service.call("showActionSelector")              # a new screen later: a new flyout
        self.assertEqual(len(self.started), 2)
        with self.assertRaises(ValueError):
            self.service.call("reboot")

    def test_drop_in_replaces_plasmas_program(self):
        text = (PKG / "data/systemd/plasma-kscreen-osd-veltos.conf").read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line and not line.startswith("#")]
        self.assertEqual(lines, ["[Service]", "ExecStart=", "ExecStart=/usr/libexec/veltos/kscreen-osd"])
        rules = (PKG / "debian/rules").read_text(encoding="utf-8")
        self.assertIn("usr/lib/systemd/user/plasma-kscreen-osd.service.d/veltos.conf", rules)
        self.assertIn("usr/libexec/veltos/kscreen-osd", rules)


if __name__ == "__main__":
    unittest.main()
