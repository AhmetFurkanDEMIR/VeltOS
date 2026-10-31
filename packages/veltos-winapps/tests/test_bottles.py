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
        # Straight into the VeltOS bottle, the file through the document
        # portal (Bottles' window asked "Select Bottle" every time).
        self.assertEqual(bottles.open_command("/x/setup.exe"),
                         ["flatpak", "run", "--file-forwarding", "--command=bottles-cli", bottles.APP_ID,
                          "run", "-b", "VeltOS", "-e", "@@", "/x/setup.exe", "@@"])
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
        self.system.write_text("[Windows programs]\nrunner=bottles\n")
        with mock.patch.object(bottles.shutil, "which", return_value="/usr/bin/flatpak"):
            # Bottles not there, the first start is over and no network: give
            # up for now (the next sign-in tries again).
            done.write_text("done")
            self.assertFalse(bottles.setup(runner=lambda *a, **k: ran.append(a), first_update_done=done,
                                           deadline=0, connected=lambda: False))
            self.assertEqual(ran, [])
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

    def test_chosen_in_settings_without_internet(self):
        # Bottles chosen in Settings while offline: Settings' install failed
        # and nothing installed it later (2026-10-31). The set-up installs
        # this user's copy once the PC is online; not chosen: never.
        done = self.home / "first-update-done"
        done.write_text("done")
        ran, network = [], [False, False, True]

        def runner(command, **kwargs):
            ran.append(command)
            if command[:2] == ["flatpak", "install"]:
                user = self.home / f".local/share/flatpak/exports/share/applications/{bottles.APP_ID}.desktop"
                user.parent.mkdir(parents=True)
                user.write_text("[Desktop Entry]\n")
            if "new" in command:
                bottles.bottle_dir().mkdir(parents=True)
            return subprocess.CompletedProcess(command, 0, "", "")
        with mock.patch.object(bottles.shutil, "which", return_value="/usr/bin/flatpak"):
            self.assertTrue(bottles.setup(runner=runner, first_update_done=done))      # Wine: nothing
            self.assertEqual(ran, [])
            bottles.set_preference("bottles")
            waits = []
            self.assertTrue(bottles.setup(runner=runner, wait=waits.append, first_update_done=done,
                                          connected=lambda: network.pop(0)))
        self.assertEqual(waits, [30, 30])                  # offline twice, then online
        self.assertEqual([c[:3] for c in ran[:2]], [["flatpak", "remote-add", "--user"],
                                                    ["flatpak", "install", "--user"]])
        self.assertEqual(ran[-1], bottles.setup_command())
        # Wine chosen again while it waited: nothing installed.
        bottles.set_preference("wine")
        self.assertTrue(bottles.setup(runner=lambda *a, **k: self.fail("installed")))


if __name__ == "__main__":
    unittest.main()
