"""The driver log: the report's parts, the job log's limit and the kernel
messages' filter."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_graphics import diagnostics  # noqa: E402


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp()
        patcher = mock.patch.dict(os.environ, {"XDG_STATE_HOME": self.state})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_job_log_keeps_its_end(self):
        diagnostics.append("first\n")
        diagnostics.append("second\n")
        self.assertEqual(diagnostics.log_file().read_text(), "first\nsecond\n")
        with mock.patch.object(diagnostics, "MAX_LOG", 10):
            diagnostics.append("0123456789ABC")
        self.assertEqual(diagnostics.log_file().read_text(), "3456789ABC")

    def test_report(self):
        diagnostics.append("[2026-10-27 10:00:00] pkcon -p install nvidia-driver:amd64\nFatal error: x\n")
        runs = []

        def runner(command, timeout=20):
            runs.append(command[0])
            return {"mokutil": "SecureBoot enabled", "dkms": "nvidia-current/550.163.01: added"}.get(command[0], "")

        text = diagnostics.report(runner=runner)
        self.assertIn("SecureBoot enabled", text)
        self.assertIn("nvidia-current/550.163.01: added", text)
        self.assertIn("pkcon -p install nvidia-driver:amd64", text)
        self.assertIn("== DKMS", text)
        self.assertEqual(sorted(set(runs)), ["dkms", "lspci", "mokutil"])

    def test_module_parameters(self):
        sysfs = Path(tempfile.mkdtemp())
        (sysfs / "nvidia_drm/parameters").mkdir(parents=True)
        (sysfs / "nvidia_drm/parameters/modeset").write_text("Y\n")
        (sysfs / "nvidia").mkdir()
        (sysfs / "nvidia/version").write_text("550.163.01\n")
        self.assertEqual(diagnostics.module_parameters(sysfs),
                         ["nvidia_drm: loaded, modeset=Y", "nvidia: loaded, version 550.163.01"])

    def test_dkms_logs_and_dpkg_history(self):
        dkms = Path(tempfile.mkdtemp())
        log = dkms / "nvidia-current/550.163.01/build/make.log"
        log.parent.mkdir(parents=True)
        log.write_text("error: x")
        self.assertEqual(diagnostics.dkms_logs(dkms), [log])
        dpkg = Path(tempfile.mkdtemp()) / "dpkg.log"
        dpkg.write_text("2026-10-27 10:00:01 status installed nvidia-driver:amd64 550.163.01-2\n"
                        "2026-10-27 10:00:02 status installed bash:amd64 5.2\n"
                        "2026-10-27 10:00:03 status unpacked nvidia-driver:amd64 550.163.01-2\n"
                        "2026-10-27 10:00:04 remove libnvidia-glcore:i386 550.163.01-2 <none>\n")
        self.assertEqual(len(diagnostics.dpkg_history(dpkg)), 2)

    def test_kernel_messages(self):
        text = ("[    1.0] Linux version 6.12\n[    4.2] nvidia: module verification failed\n"
                "[    4.3] usb 1-1: new device\n[    5.0] nvidia-drm: [drm] modeset\n")
        out = diagnostics.kernel_messages(text)
        self.assertIn("module verification failed", out)
        self.assertIn("nvidia-drm", out)
        self.assertNotIn("usb 1-1", out)


if __name__ == "__main__":
    unittest.main()
