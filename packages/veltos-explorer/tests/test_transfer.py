"""Tests for the copy engine behind Windows 11's copy window (transfer.py)
and the window itself offscreen (transferwindow.py, Transfer.qml)."""

import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_explorer import transfer  # noqa: E402


def tree(root, files):
    for name, data in files.items():
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.src = self.root / "Downloads"
        self.dst = self.root / "Desktop"
        self.src.mkdir()
        self.dst.mkdir()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_copy_files_and_folders_with_progress(self):
        tree(self.src, {"big.iso": os.urandom(3 * transfer.CHUNK + 5), "Photos/a.jpg": b"a" * 10,
                        "Photos/sub/b.jpg": b"b" * 20})
        calls = []
        job = transfer.Transfer([str(self.src / "big.iso"), str(self.src / "Photos")], str(self.dst),
                                progress=lambda: calls.append(1))
        self.assertEqual(job.total_bytes, 3 * transfer.CHUNK + 35)
        self.assertEqual(job.total_items, 3)
        job.run()
        self.assertTrue(job.finished)
        self.assertEqual(job.fraction, 1.0)
        self.assertEqual((self.dst / "big.iso").read_bytes(), (self.src / "big.iso").read_bytes())
        self.assertEqual((self.dst / "Photos/sub/b.jpg").read_bytes(), b"b" * 20)
        self.assertGreater(len(calls), 4)
        self.assertEqual(job.errors, [])
        self.assertFalse(list(self.dst.rglob("*.veltos-part")))

    def test_copy_into_the_same_folder_gets_windows_copy_name(self):
        tree(self.src, {"report.txt": b"x"})
        transfer.Transfer([str(self.src / "report.txt")], str(self.src)).run()
        transfer.Transfer([str(self.src / "report.txt")], str(self.src)).run()
        self.assertTrue((self.src / "report - Copy.txt").is_file())
        self.assertTrue((self.src / "report - Copy (2).txt").is_file())

    def test_conflicts_ask_replace_or_skip_and_can_answer_for_all(self):
        tree(self.src, {"a.txt": b"new", "b.txt": b"new", "c.txt": b"new"})
        tree(self.dst, {"a.txt": b"old", "b.txt": b"old", "c.txt": b"old"})
        asked = []

        def ask(item):
            asked.append(os.path.basename(item.target))
            return (transfer.SKIP, False) if len(asked) == 1 else (transfer.REPLACE, True)
        transfer.Transfer([str(self.src / n) for n in ("a.txt", "b.txt", "c.txt")], str(self.dst), ask=ask).run()
        self.assertEqual(asked, ["a.txt", "b.txt"])           # the third took the answer for all
        self.assertEqual((self.dst / "a.txt").read_bytes(), b"old")
        self.assertEqual((self.dst / "b.txt").read_bytes(), b"new")
        self.assertEqual((self.dst / "c.txt").read_bytes(), b"new")

    def test_move_on_one_drive_is_a_rename(self):
        tree(self.src, {"Folder/x.txt": b"x"})
        job = transfer.Transfer([str(self.src / "Folder")], str(self.dst), mode="move")
        self.assertEqual(len(job.renames), 1)
        job.run()
        self.assertFalse((self.src / "Folder").exists())
        self.assertEqual((self.dst / "Folder/x.txt").read_bytes(), b"x")

    def test_move_between_drives_copies_then_removes_but_keeps_skipped(self):
        tree(self.src, {"keep/x.txt": b"x", "go.txt": b"g"})
        tree(self.dst, {"keep/x.txt": b"old"})
        original = transfer.same_device
        transfer.same_device = lambda a, b: False
        try:
            job = transfer.Transfer([str(self.src / "keep"), str(self.src / "go.txt")], str(self.dst), mode="move",
                                    ask=lambda item: (transfer.SKIP, True))
            job.run()
        finally:
            transfer.same_device = original
        self.assertFalse((self.src / "go.txt").exists())
        self.assertEqual((self.dst / "go.txt").read_bytes(), b"g")
        self.assertTrue((self.src / "keep/x.txt").exists())      # something in it was skipped
        self.assertEqual(job.skipped, 1)

    def test_a_folder_cannot_go_into_itself(self):
        tree(self.src, {"a/b/c.txt": b"c"})
        job = transfer.Transfer([str(self.src / "a")], str(self.src / "a/b"))
        self.assertEqual(job.problems, [(str(self.src / "a"), "into_itself")])
        job.run()
        self.assertFalse((self.src / "a/b/a").exists())

    def test_cancel_leaves_no_half_file_and_pause_waits(self):
        tree(self.src, {"big.bin": os.urandom(4 * transfer.CHUNK)})
        job = None
        pieces = []

        def progress():
            pieces.append(job.done_bytes)
            if job.done_bytes >= transfer.CHUNK and not job._cancel.is_set():
                job.cancel()
        job = transfer.Transfer([str(self.src / "big.bin")], str(self.dst), progress=progress)
        job.run()
        self.assertTrue(job.cancelled)
        self.assertFalse((self.dst / "big.bin").exists())
        self.assertFalse(list(self.dst.iterdir()))
        paused = transfer.Transfer([str(self.src / "big.bin")], str(self.dst))
        paused.pause()
        worker = threading.Thread(target=paused.run)
        worker.start()
        worker.join(0.3)
        self.assertTrue(worker.is_alive())
        self.assertEqual(paused.done_bytes, 0)
        paused.resume()
        worker.join(5)
        self.assertTrue(paused.finished)
        self.assertEqual((self.dst / "big.bin").stat().st_size, 4 * transfer.CHUNK)

    def test_errors_are_collected_and_the_rest_goes_on(self):
        tree(self.src, {"ok.txt": b"ok", "bad.txt": b"bad"})
        original = transfer.Transfer._copy_file

        def failing(job, item):
            if item.source.endswith("bad.txt"):
                raise PermissionError(13, "Permission denied")
            return original(job, item)
        transfer.Transfer._copy_file = failing
        try:
            job = transfer.Transfer([str(self.src / "bad.txt"), str(self.src / "ok.txt")], str(self.dst))
            job.run()
        finally:
            transfer.Transfer._copy_file = original
        self.assertEqual(job.errors, [(str(self.src / "bad.txt"), "Permission denied")])
        self.assertTrue((self.dst / "ok.txt").is_file())

    def test_speed_and_time_texts(self):
        clock = iter([0.0, 1.0, 2.0]).__next__
        job = transfer.Transfer([], str(self.dst), clock=clock)
        job.total_bytes = 300
        job._sample()
        job.done_bytes = 100
        job._sample()
        self.assertEqual(job.speed(), 100.0)
        self.assertEqual(job.seconds_left(), 2.0)
        self.assertEqual(transfer.duration_text(None), "Calculating…")
        self.assertEqual(transfer.duration_text(12), "About 15 seconds")
        self.assertEqual(transfer.duration_text(125, "tr"), "Yaklaşık 2 dakika")
        self.assertEqual(transfer.duration_text(3 * 3600 + 600), "About 3 hours 10 minutes")


try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class TransferWindowTests(unittest.TestCase):
    def test_window_shows_progress_and_asks_on_conflict(self):
        from veltos_explorer import app as explorer, transferwindow
        app = QGuiApplication.instance() or QGuiApplication([])
        root = Path(tempfile.mkdtemp())
        (root / "src").mkdir()
        (root / "dst").mkdir()
        (root / "src/a.txt").write_bytes(b"new")
        (root / "dst/a.txt").write_bytes(b"old")
        messages = []
        from PySide6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(lambda _t, _c, m: messages.append(m))
        backend = None
        job = transfer.Transfer([str(root / "src/a.txt")], str(root / "dst"), ask=lambda item: backend.ask(item))
        backend = transferwindow.TransferBackend(job, explorer.EmptyBinBackend(lang="en"), lang="en")
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(explorer.QML_DIR / "Transfer.qml")))
        self.assertTrue(engine.rootObjects(), messages)
        window = engine.rootObjects()[0]
        self.assertIn("Copying 1 item from src to dst", backend.property("heading"))
        backend.start()
        for _ in range(200):
            app.processEvents()
            if backend.property("conflict"):
                break
        self.assertTrue(backend.property("conflict"))
        self.assertIn('"a.txt"', backend.property("conflictText"))
        window.setProperty("visible", True)
        backend.toggleDetails()
        window.grabWindow()
        backend.answer("replace", False)
        for _ in range(200):
            app.processEvents()
            if job.finished:
                break
        app.processEvents()
        self.assertTrue(job.finished)
        self.assertEqual((root / "dst/a.txt").read_bytes(), b"new")
        self.assertEqual(backend.property("percent"), 100)
        problems = [m for m in messages if "qml" in m.lower() or "error" in m.lower() or "undefined" in m.lower()]
        self.assertEqual(problems, [])
        from PySide6.QtCore import QCoreApplication, QEvent
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
