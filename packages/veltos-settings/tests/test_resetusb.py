"""Accounts > Sign-in options: the password reset USB and the password hint
(veltos_settings/resetusb.py) against a stand-in for veltos-auth's
password-recovery, pkexec and busctl."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import resetusb  # noqa: E402

DRIVES = [{"path": "/dev/sdb1", "disk": "/dev/sdb", "label": "KEYS", "size": 7990000000,
           "model": "Kingston DataTraveler", "fstype": "vfat", "mountpoint": ""}]


class Runner:
    def __init__(self, configured=False, create_code=0, create_out='{"error": ""}'):
        self.configured = configured
        self.create_code, self.create_out = create_code, create_out
        self.commands = []
        self.hint = "first cat"

    def __call__(self, command, timeout=20, input=None, merge=False):
        self.commands.append(list(command))
        if command[1:2] == ["status"]:
            return 0, json.dumps({"configured": self.configured}) + "\n"
        if command[1:2] == ["drives"]:
            return 0, json.dumps(DRIVES) + "\n"
        if command[:1] == ["pkexec"] and command[2] == "create":
            return self.create_code, self.create_out
        if command[:1] == ["pkexec"] and command[2] == "remove":
            return 0, '{"error": ""}'
        if command[:3] == ["busctl", "--system", "get-property"]:
            return 0, 's "%s"\n' % self.hint
        if command[:3] == ["busctl", "--system", "call"]:
            self.hint = command[-1]
            return 0, ""
        return 1, ""


class ResetUsbTests(unittest.TestCase):
    def make(self, **kwargs):
        self.runner = Runner(**kwargs)
        command = Path(tempfile.mkdtemp()) / "password-recovery"
        command.write_bytes(b"")
        return resetusb.ResetUsb(self.runner, command=str(command), user="ayse", uid=1000, host="ayse-pc")

    def test_status_drives_and_hint(self):
        usb = self.make()
        self.assertEqual(usb.status(), {"available": True, "configured": False, "hint": "first cat"})
        self.assertEqual([d["path"] for d in usb.drives()], ["/dev/sdb1"])
        self.assertIn(["busctl", "--system", "get-property", "org.freedesktop.Accounts",
                       "/org/freedesktop/Accounts/User1000", "org.freedesktop.Accounts.User", "PasswordHint"],
                      self.runner.commands)

    def test_without_veltos_auth_there_is_no_reset_usb(self):
        usb = resetusb.ResetUsb(Runner(), command="/nonexistent/password-recovery", user="ayse", uid=1000)
        self.assertFalse(usb.status()["available"])
        self.assertEqual(usb.drives(), [])

    def test_create_and_remove_go_through_pkexec(self):
        usb = self.make()
        self.assertEqual(usb.create("/dev/sdb1"), "")
        self.assertEqual(self.runner.commands[-1][0], "pkexec")
        self.assertEqual(self.runner.commands[-1][2:], ["create", "ayse", "/dev/sdb1", "--host", "ayse-pc"])
        self.assertEqual(usb.remove(), "")
        self.assertEqual(self.make(create_code=1, create_out='{"error": "bad-drive"}').create("/dev/sdb1"),
                         "bad-drive")
        self.assertEqual(self.make(create_code=126, create_out="").create("/dev/sdb1"), "not-allowed")

    def test_hint_is_one_short_line(self):
        usb = self.make()
        self.assertTrue(usb.set_hint("  my\nfirst cat " + "x" * 200))
        self.assertEqual(self.runner.commands[-1][:8], ["busctl", "--system", "call", "org.freedesktop.Accounts",
                                                        "/org/freedesktop/Accounts/User1000",
                                                        "org.freedesktop.Accounts.User", "SetPasswordHint", "s"])
        self.assertEqual(len(self.runner.hint), 100)
        self.assertTrue(self.runner.hint.startswith("my first cat"))
        self.runner.hint = "çay \\\\ bardağı"
        self.assertEqual(usb.hint(), "çay \\ bardağı")


if __name__ == "__main__":
    unittest.main()
