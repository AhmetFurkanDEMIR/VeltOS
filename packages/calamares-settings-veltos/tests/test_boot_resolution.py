"""The installer job that starts the installed system at the screen's resolution."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parent.parent
JOB = PKG / "helpers/boot-resolution"


class BootResolutionJobTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target = self.tmp / "target"
        self.target.mkdir()
        self.log = self.tmp / "helper.log"
        # The job sources common.sh from its installed path; run a copy that
        # sources the one in the repository.
        job = JOB.read_text().replace("/usr/libexec/veltos-installer/common.sh", str(PKG / "helpers/common.sh"))
        self.job = self.tmp / "boot-resolution"
        self.job.write_text(job)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_job(self, detected, set_status=0):
        helper = self.tmp / "helper"
        # Like veltos-boot's helper: --root is refused to callers that came
        # through pkexec (PKEXEC_UID set).
        helper.write_text(f"#!/bin/sh\necho \"$@\" >> '{self.log}'\n"
                          f"[ \"$1\" = detect ] && {{ [ -n '{detected}' ] && echo '{detected}' || exit 1; }}\n"
                          "[ -n \"${PKEXEC_UID:-}\" ] && { echo refused >&2; exit 2; }\n"
                          f"exit {set_status}\n")
        helper.chmod(0o755)
        # Calamares itself runs through pkexec: its jobs inherit PKEXEC_UID.
        env = {"PATH": "/usr/bin:/bin", "VELTOS_TARGET": str(self.target), "VELTOS_BOOT_HELPER": str(helper),
               "PKEXEC_UID": "1000"}
        return subprocess.run(["sh", str(self.job)], capture_output=True, text=True, env=env)

    def test_writes_the_detected_mode_into_the_target(self):
        result = self.run_job("2560x1440")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("refused", result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), ["detect", f"set 2560x1440 --root {self.target}"])

    def test_no_screen_keeps_the_default(self):
        result = self.run_job("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), ["detect"])
        self.assertIn("keeps 1024x768", result.stdout)

    def test_a_failure_never_stops_the_installation(self):
        # The first ISO with this job failed every installation at its end.
        result = self.run_job("1280x800", set_status=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("keeps 1024x768", result.stdout)

    def test_runs_before_the_bootloader_jobs(self):
        settings = yaml.safe_load((PKG / "calamares/settings.conf").read_text(encoding="utf-8"))
        executed = [m for step in settings["sequence"] for m in step.get("exec", [])]
        self.assertLess(executed.index("boot-resolution"), executed.index("grubcfg"))
        self.assertLess(executed.index("boot-resolution"), executed.index("bootloader"))

    def test_initramfs_exists_before_update_grub(self):
        # The live image leaves its own initramfs out (build/live-build/
        # config/rootfs/excludes); update-grub writes an initrd line only
        # for a file that exists, so the initramfs comes first, after the
        # Plymouth theme it contains.
        settings = yaml.safe_load((PKG / "calamares/settings.conf").read_text(encoding="utf-8"))
        executed = [m for step in settings["sequence"] for m in step.get("exec", [])]
        self.assertLess(executed.index("plymouthcfg"), executed.index("initramfs"))
        self.assertLess(executed.index("initramfscfg"), executed.index("initramfs"))
        self.assertLess(executed.index("initramfs"), executed.index("bootloader"))
        self.assertLess(executed.index("crypttab-tries"), executed.index("initramfs"))
        # live-tools (removed by "packages") diverts update-initramfs to a
        # wrapper that does nothing while the installer runs from the live
        # medium: the installed system had no initramfs (QEMU, 2026-10-23).
        removed = yaml.safe_load((PKG / "calamares/modules/packages.conf").read_text(encoding="utf-8"))
        self.assertIn("live-tools", removed["operations"][0]["remove"])
        self.assertLess(executed.index("packages"), executed.index("initramfs"))
        self.assertGreater(executed.index("boot-check"), executed.index("bootloader"))
        excludes = (PKG.parent.parent / "build/live-build/config/rootfs/excludes")
        if excludes.exists():           # the package is also built outside the repository
            self.assertIn("boot/initrd.img*", excludes.read_text().splitlines())


if __name__ == "__main__":
    unittest.main()
