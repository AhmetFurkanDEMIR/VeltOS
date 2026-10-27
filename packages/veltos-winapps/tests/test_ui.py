"""Loads the real runner window offscreen and walks through every page.

Catches errors that only show up when the Python/QML UI actually runs
(an earlier version crashed at import time and showed no window at all).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from test_winapps import minimal_pe  # noqa: E402


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class RunnerWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        # Every Qt/QML warning (including JavaScript TypeErrors) fails the test.
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    def setUp(self):
        self.messages.clear()
        self.keep = []

    def tearDown(self):
        # Destroy windows before their runner objects, as the real app does.
        from PySide6.QtCore import QCoreApplication, QEvent
        for runner, engine in reversed(self.keep):
            engine.deleteLater()
        # Delete the engines now, while their runners still exist: a later
        # test saw this one's bindings read a dead runner.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.keep.clear()

    def load(self, filename, data):
        from veltos_winapps import app as runner_app
        path = Path(tempfile.mkdtemp()) / filename
        path.write_bytes(data)
        runner = runner_app.Runner(path)
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(lambda items: warnings.extend(w.toString() for w in items))
        engine.rootContext().setContextProperty("runner", runner)
        engine.load(QUrl.fromLocalFile(str(runner_app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.keep.append((runner, engine))
        return runner, engine, warnings

    def test_every_page_renders_without_qml_errors(self):
        runner, engine, warnings = self.load("ToolSetup.exe", minimal_pe())
        self.assertTrue(engine.rootObjects(), "Main.qml did not load")
        self.assertEqual(runner.page, "running")       # no question first (Windows)
        for page in ["preparing", "running", "waiting", "done", "failed", "invalid", "nospace"]:
            runner._go(page)
            self.app.processEvents()
            self.assertTrue(runner.title, page)
        self.assertEqual(warnings, [])
        self.assertEqual([m for m in self.messages if "qml" in m.lower() or "Error" in m], [])

    def test_installer_and_program_texts(self):
        installer, _, _ = self.load("ToolSetup.exe", minimal_pe())
        program, _, _ = self.load("Tool.exe", minimal_pe())
        self.assertTrue(installer.isInstaller)
        self.assertFalse(program.isInstaller)
        self.assertNotEqual(installer.title, program.title)
        # Publisher (unknown here) and kind, as in the Windows App Installer.
        self.assertEqual(len(installer.details), 2)
        self.assertTrue(installer.details[1].endswith("64-bit"))

    def test_choose_page_fits(self):
        """Two alternatives: the window grows so that the information bar
        stays above Open/Cancel (they overlapped in a 400 px window)."""
        from unittest import mock
        from veltos_winapps import app as runner_app
        alternatives = [{"id": name, "name": name.title(), "icon": "application-x-executable",
                         "desktop": f"/usr/share/applications/{name}.desktop"} for name in ("bottles", "lutris")]
        with mock.patch.object(runner_app, "alternative_runners", return_value=alternatives), \
                mock.patch.object(runner_app.bottles, "preference", return_value=""):
            runner, engine, warnings = self.load("Notepad++ Installer.exe", minimal_pe())
        self.assertEqual(runner.page, "choose")
        window = engine.rootObjects()[0]
        window.grabWindow()
        self.assertGreater(window.height(), 400)

        def items(item):
            for child in item.childItems():
                yield child
                yield from items(child)
        all_items = list(items(window.contentItem()))
        footer = next(i for i in all_items if i.objectName() == "footer")
        bar = next(i for i in all_items if i.objectName() == "infoBar")
        self.assertTrue(bar.isVisible())
        self.assertLessEqual(bar.mapToScene(bar.boundingRect().bottomLeft()).y(),
                             footer.mapToScene(footer.boundingRect().topLeft()).y())
        self.assertEqual(warnings, [])

    def test_batch_file_pages(self):
        runner, engine, warnings = self.load("start.cmd", b"@echo off\r\necho hi\r\n")
        self.assertTrue(engine.rootObjects(), "Main.qml did not load")
        self.assertIn("start.cmd", runner.title)
        for page in ["running", "failed"]:
            runner._go(page)
            self.app.processEvents()
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
