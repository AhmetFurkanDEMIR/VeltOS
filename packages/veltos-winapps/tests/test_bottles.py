"""Bottles as the way to open Windows programs (bottles.py): the choice
(user over system), Bottles found by its Flatpak desktop entry, the
commands for Flathub and the sign-in set-up. Stand-ins only."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_winapps import bottles  # noqa: E402


class BottlesTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config"),
                                               "XDG_DATA_HOME": str(self.home / ".local/share")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.system = self.home / "etc-windows-apps.conf"
        p = mock.patch.object(bottles, "SYSTEM_CONF", self.system)
        p.start()
        self.addCleanup(p.stop)
        d = mock.patch.object(bottles, "DESKTOPS", [self.home / "system-apps" / f"{bottles.APP_ID}.desktop"])
        d.start()
        self.addCleanup(d.stop)

    def test_choice_user_over_system(self):
        self.assertEqual(bottles.preference(), "")
        self.system.write_text("[Windows programs]\nrunner=bottles\n")
        self.assertEqual(bottles.preference(), "bottles")
        self.assertTrue(bottles.set_preference("wine"))
        self.assertEqual(bottles.preference(), "wine")
        self.assertFalse(bottles.set_preference("lutris"))
        self.system.write_text("[Windows programs]\nrunner=something\n")
        (self.home / ".config/veltos/windows-apps.conf").unlink()
        self.assertEqual(bottles.preference(), "")

    def test_installed_and_open(self):
        self.assertFalse(bottles.installed())
        self.assertEqual(bottles.open_command("/x/setup.exe"), [])
        user_desktop = self.home / f".local/share/flatpak/exports/share/applications/{bottles.APP_ID}.desktop"
        user_desktop.parent.mkdir(parents=True)
        user_desktop.write_text("[Desktop Entry]\n")
        self.assertTrue(bottles.installed())
        self.assertEqual(bottles.open_command("/x/setup.exe"), ["gio", "launch", str(user_desktop), "/x/setup.exe"])
        # No bottle yet: not ready, VeltOS opens the file itself.
        self.assertFalse(bottles.ready())
        bottles.bottle_dir().mkdir(parents=True)
        self.assertTrue(bottles.ready())
        self.assertEqual(bottles.install_commands("--system")[1],
                         ["flatpak", "install", "--system", "-y", "--noninteractive", "flathub", bottles.APP_ID])
        self.assertIn(bottles.FLATHUB, bottles.install_commands()[0])

    def test_setup_at_sign_in(self):
        ran = []
        done = self.home / "first-update-done"
        # Not chosen: nothing to do.
        self.assertTrue(bottles.setup(runner=lambda *a, **k: ran.append(a)))
        bottles.set_preference("bottles")
        with mock.patch.object(bottles.shutil, "which", return_value="/usr/bin/flatpak"):
            # Bottles not there and the first start is over: give up quietly.
            done.write_text("done")
            self.assertFalse(bottles.setup(runner=lambda *a, **k: ran.append(a), first_update_done=done))
            done.unlink()
            # The first start installs it while the set-up waits.
            desktop = bottles.DESKTOPS[0]
            waits = []

            def wait(seconds):
                waits.append(seconds)
                desktop.parent.mkdir(parents=True, exist_ok=True)
                desktop.write_text("[Desktop Entry]\n")

            def runner(command, **kwargs):
                ran.append(command)
                bottles.bottle_dir().mkdir(parents=True)
                return subprocess.CompletedProcess(command, 0, "created", "")
            self.assertTrue(bottles.setup(runner=runner, wait=wait, first_update_done=done))
            self.assertEqual(waits, [30])
            self.assertEqual(ran[-1], bottles.setup_command())
            self.assertIn("--environment", ran[-1])
            # Once made, it is not made again.
            self.assertTrue(bottles.setup(runner=lambda *a, **k: self.fail("ran again")))


if __name__ == "__main__":
    unittest.main()
