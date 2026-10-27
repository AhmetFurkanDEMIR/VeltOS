"""The first start's update (firstupdate.py) with stand-ins for apt-get and
the network, when its window shows, and the window offscreen in English
and Turkish (firststart.py, FirstStart.qml)."""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_store import firstupdate  # noqa: E402

from test_ui import APP, MESSAGES  # noqa: E402,F401


class FakeApt:
    """apt-get: `update` succeeds, `full-upgrade` prints APT::Status-Fd lines."""

    def __init__(self, upgrade_code=0, update_code=0):
        self.calls = []
        self.upgrade_code, self.update_code = upgrade_code, update_code

    def popen(self, command, **kwargs):
        self.calls.append(command)
        lines = ""
        code = self.update_code
        if "full-upgrade" in command:
            lines = ("dlstatus:1:20.0:Retrieving file 1 of 2\ndlstatus:1:100:Retrieved\n"
                     "pmstatus:vlc:40.0:Unpacking vlc\npmstatus:vlc:100:Installed vlc\n")
            code = self.upgrade_code

        class Process:
            stdout = io.StringIO(lines)

            def wait(self):
                return code
        return Process()

    def run(self, command, **kwargs):
        self.calls.append(command)
        out = "Inst vlc [1] (2 Debian:13)\nInst firefox-esr [1] (2 Debian:13)\n" if "-s" in command else ""
        return subprocess.CompletedProcess(command, 0, out, "")


class UpdateTests(unittest.TestCase):
    def setUp(self):
        folder = Path(tempfile.mkdtemp())
        self.status, self.done, self.log = folder / "run/first-update.json", folder / "lib/done", folder / "log"
        self.seen = []
        original = firstupdate.write_status

        def recording(state, percent=0, status=firstupdate.STATUS, **extra):
            self.seen.append((state, int(percent)))
            original(state, percent, status, **extra)
        firstupdate.write_status = recording
        self.addCleanup(setattr, firstupdate, "write_status", original)

    def run_main(self, apt, online=True):
        return firstupdate.main(self.status, self.done, self.log, apt.run, apt.popen, lambda runner: online)

    def test_update_and_upgrade(self):
        apt = FakeApt()
        self.assertEqual(self.run_main(apt), 0)
        self.assertEqual(apt.calls[0][-1], "update")
        self.assertEqual(apt.calls[-1][-2:], ["-y", "full-upgrade"])
        self.assertIn("DPkg::Lock::Timeout=600", apt.calls[-1])
        self.assertEqual([s for s, _p in self.seen][:3], ["network", "lists", "download"])
        self.assertIn(("download", 10), self.seen)
        self.assertIn(("install", 70), self.seen)
        self.assertEqual(self.seen[-1], ("done", 100))
        self.assertEqual(json.loads(self.status.read_text())["state"], "done")
        self.assertIn("done", self.done.read_text())
        self.assertIn("pmstatus:vlc:100", self.log.read_text())

    def test_offline_and_failure_still_finish(self):
        self.assertEqual(self.run_main(FakeApt(), online=False), 0)
        self.assertEqual(json.loads(self.status.read_text())["state"], "offline")
        self.assertTrue(self.done.exists())
        self.done.unlink()
        self.assertEqual(self.run_main(FakeApt(upgrade_code=100)), 1)
        self.assertEqual(json.loads(self.status.read_text())["state"], "failed")
        self.assertTrue(self.done.exists())         # only once, as asked: VeltOS Update tries again

    def test_progress_lines(self):
        self.assertEqual(firstupdate.progress("dlstatus:1:42.5:Retrieving"), ("download", 42.5))
        self.assertEqual(firstupdate.progress("pmstatus:dpkg-exec:0:Running dpkg"), ("install", 0.0))
        self.assertIsNone(firstupdate.progress("Get:1 http://deb.debian.org trixie InRelease"))
        self.assertEqual(firstupdate.overall("install", 50), 75)

    def test_when_the_window_shows(self):
        folder = Path(tempfile.mkdtemp())
        cmdline, shown = folder / "cmdline", folder / "shown"
        cmdline.write_text("BOOT_IMAGE=/vmlinuz root=UUID=x quiet splash\n")
        status, done = folder / "status.json", folder / "done"
        status.write_text('{"state": "download"}')
        self.assertTrue(firstupdate.should_show(done, status, shown, cmdline))
        done.write_text("done")
        self.assertTrue(firstupdate.should_show(done, status, shown, cmdline))
        self.assertFalse(firstupdate.should_show(done, status, shown, cmdline, now=time.time() + 3600))
        shown.write_text("x")
        self.assertFalse(firstupdate.should_show(done, status, shown, cmdline))
        shown.unlink()
        cmdline.write_text("BOOT_IMAGE=/live/vmlinuz boot=live quiet\n")
        self.assertFalse(firstupdate.should_show(done, status, shown, cmdline))


class WindowTests(unittest.TestCase):
    lang = "en"

    def test_window_from_updating_to_ready(self):
        from PySide6.QtCore import QCoreApplication, QEvent, QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        from veltos_store import firststart
        folder = Path(tempfile.mkdtemp())
        status, done, shown = folder / "status.json", folder / "done", folder / "shown"
        firstupdate.write_status("download", 30, status, packages=12)
        backend = firststart.FirstStart(lang=self.lang, status=status, done=done, interval=20, shown=shown)
        MESSAGES.clear()
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(firststart.QML_DIR / "FirstStart.qml")))
        self.assertTrue(engine.rootObjects(), MESSAGES)
        window = engine.rootObjects()[0]
        window.grabWindow()
        texts = backend.texts
        self.assertEqual(backend.detail, texts["fs_download"].replace("{percent}", "30"))
        self.assertFalse(backend.ready)
        finished = []
        backend.finished.connect(lambda: finished.append(True))
        firstupdate.write_status("done", 100, status)
        backend.poll()
        self.assertTrue(backend.ready)
        window.grabWindow()
        firststart.CLOSE_AFTER_READY, old = 0, firststart.CLOSE_AFTER_READY
        try:
            time.sleep(0.05)
            backend.poll()
        finally:
            firststart.CLOSE_AFTER_READY = old
        self.assertEqual(finished, [True])
        self.assertTrue(shown.exists())
        problems = [m for m in MESSAGES if "qml" in m.lower() or "error" in m.lower() or "warning" in m.lower()
                    or "undefined" in m.lower()]
        self.assertEqual(problems, [])
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()


class TurkishWindowTests(WindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
