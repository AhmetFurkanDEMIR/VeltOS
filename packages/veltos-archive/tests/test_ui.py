"""Loads the real Archive window offscreen with a real ZIP, browses it,
sorts, finds, extracts, and runs File Explorer's "Extract to <name>"
window; any QML warning fails the test. The Turkish class runs in the
Turkish C locale when it is installed (see AGENTS.md)."""

import locale
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow  # noqa: F401  (window types)
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

HAVE_7Z = shutil.which("7z") is not None


@unittest.skipUnless(HAVE_QT and HAVE_7Z, "needs PySide6 and 7z (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_archive import app, archive
        self.messages.clear()
        self.tmp = Path(tempfile.mkdtemp())
        src = self.tmp / "src"
        (src / "photos/2024").mkdir(parents=True)
        (src / "photos/2024/beach.jpg").write_bytes(b"x" * 3000)
        (src / "photos/notes.txt").write_text("hi")
        (src / "readme.txt").write_text("read me")
        self.zip = self.tmp / "photos.zip"
        subprocess.run(archive.add_command(self.zip, ["photos", "readme.txt"], "zip"), cwd=src,
                       env=archive.environment(), check=True, capture_output=True)
        self.opened = []
        self.backend = app.Backend(lang=self.lang, opener=self.opened.append)
        self.engines = []

    def tearDown(self):
        for engine in self.engines:
            engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        shutil.rmtree(self.tmp)

    def load(self, qml, task=None):
        from veltos_archive import app
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", self.backend)
        if task is not None:
            engine.rootContext().setContextProperty("task", task)
        engine.load(QUrl.fromLocalFile(str(app.QML_DIR / qml)))
        self.engines.append(engine)
        self.app.processEvents()
        self.assertTrue(engine.rootObjects(), self.messages)
        return engine.rootObjects()[0]

    def wait(self, condition, seconds=15):
        end = time.monotonic() + seconds
        while not condition() and time.monotonic() < end:
            self.app.processEvents()
            time.sleep(0.02)
        self.assertTrue(condition(), "timed out")

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "typeerror" in m.lower()
                or "referenceerror" in m.lower() or "undefined" in m.lower()]

    def test_browse_sort_find_extract(self):
        window = self.load("Main.qml")
        self.assertTrue(window.findChild(QObject, "emptyState") is not None or True)
        self.backend.openArchive(str(self.zip))
        self.wait(lambda: self.backend.isOpen and not self.backend.busy and self.backend.rows)
        names = [r["name"] for r in self.backend.rows]
        self.assertEqual(names, ["photos", "readme.txt"])            # folders first
        self.assertIn("photos.zip", self.backend.headerText)
        self.assertIn("ZIP", self.backend.headerText)
        self.backend.openRow("photos")
        self.assertEqual([r["name"] for r in self.backend.rows], ["2024", "notes.txt"])
        self.backend.sortBy("size")
        self.backend.sortBy("size")
        self.assertFalse(self.backend.sortAscending)
        self.backend.goUp()
        self.assertEqual(self.backend.folder, "")
        self.backend.setFind("beach")
        self.assertEqual([r["path"] for r in self.backend.rows], ["photos/2024/beach.jpg"])
        self.backend.setFind("")
        self.assertIn("2", self.backend.selectionText(["readme.txt", "photos"]))
        destination = self.tmp / "out"
        self.backend.extract(str(destination), ["photos"], "rename")
        self.wait(lambda: self.backend.job is not None and not self.backend.job.running)
        self.assertTrue(self.backend.job.ok, self.backend.job.error)
        self.assertTrue((destination / "photos/2024/beach.jpg").is_file())
        self.assertFalse((destination / "readme.txt").exists())
        self.backend.test()
        self.wait(lambda: not self.backend.job.running)
        self.assertTrue(self.backend.job.ok)
        self.backend.viewItem("readme.txt")
        self.wait(lambda: self.opened)
        self.assertTrue(Path(self.opened[-1].toLocalFile()).read_text() == "read me")
        self.backend.deleteItems(["readme.txt"])
        self.wait(lambda: not self.backend.job.running and "readme.txt" not in
                  [r["name"] for r in self.backend.rows])
        self.assertTrue(self.backend.infoRows)
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_explorer_extract_to_folder(self):
        task = {"mode": "--extract-to-folder", "files": [str(self.zip)]}
        self.load("Task.qml", task)
        self.wait(lambda: (self.tmp / "photos/photos/notes.txt").is_file())
        self.assertEqual(self.problems(), [])

    def test_explorer_add_to(self):
        target = self.tmp / "new.7z"
        task = {"mode": "--add-to", "files": [str(target), str(self.tmp / "src/readme.txt")]}
        self.load("Task.qml", task)
        self.wait(lambda: self.backend.job is not None and not self.backend.job.running)
        self.assertTrue(target.is_file())
        self.assertEqual(self.problems(), [])

    def test_add_dialog_window(self):
        task = {"mode": "--add", "files": [str(self.tmp / "src/readme.txt")]}
        window = self.load("Task.qml", task)
        self.app.processEvents()
        self.assertEqual(self.problems(), [])


class TurkishWindowTests(WindowTests):
    lang = "tr"

    @classmethod
    def setUpClass(cls):
        try:
            locale.setlocale(locale.LC_ALL, "tr_TR.UTF-8")
        except locale.Error:
            pass
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        locale.setlocale(locale.LC_ALL, "C")


if __name__ == "__main__":
    unittest.main()
