"""The installer job that saves the console's keymap and font cache in the
installed system (helpers/console-cache), run with a stand-in chroot."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parent.parent
JOB = PKG / "helpers/console-cache"


class ConsoleCacheJobTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target = self.tmp / "target"
        self.target.mkdir()
        self.log = self.tmp / "chroot.log"
        job = JOB.read_text().replace("/usr/libexec/veltos-installer/common.sh", str(PKG / "helpers/common.sh"))
        self.job = self.tmp / "console-cache"
        self.job.write_text(job)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_job(self, status=0):
        chroot = self.bin / "chroot"
        chroot.write_text(f"#!/bin/sh\necho \"$@\" >> '{self.log}'\nexit {status}\n")
        chroot.chmod(0o755)
        env = {"PATH": f"{self.bin}:/usr/bin:/bin", "VELTOS_TARGET": str(self.target)}
        return subprocess.run(["sh", str(self.job)], capture_output=True, text=True, env=env)

    def test_saves_the_cache_in_the_target(self):
        result = self.run_job()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().split(), [str(self.target), "setupcon", "--force", "--save-only"])
        self.assertIn("saved", result.stdout)

    def test_a_failure_never_stops_the_installation(self):
        result = self.run_job(status=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("at start-up", result.stderr)

    def test_runs_after_the_keyboard_and_before_the_initramfs(self):
        settings = yaml.safe_load((PKG / "calamares/settings.conf").read_text(encoding="utf-8"))
        executed = [m for step in settings["sequence"] for m in step.get("exec", [])]
        self.assertLess(executed.index("keyboardq"), executed.index("console-cache"))
        self.assertLess(executed.index("localecfg"), executed.index("console-cache"))
        self.assertLess(executed.index("console-cache"), executed.index("initramfs"))
        desc = yaml.safe_load((PKG / "modules/console-cache/module.desc").read_text(encoding="utf-8"))
        self.assertEqual(desc["command"], "/usr/libexec/veltos-installer/console-cache")


if __name__ == "__main__":
    unittest.main()
