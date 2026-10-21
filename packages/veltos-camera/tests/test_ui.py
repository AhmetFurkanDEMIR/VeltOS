"""Loads the real Camera window offscreen (the build machine has no camera,
so it shows the "no camera" state) and goes through modes, timer and
settings; any QML warning fails the test. The Turkish class runs in the
Turkish C locale when it is installed (PySide6 keyword-argument bug, see
AGENTS.md)."""

import locale
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.home = Path(tempfile.mkdtemp())
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_camera import app
        self.messages.clear()
        self.opened = []
        self.folder = self.home / self.id() / "Camera Roll"
        settings = QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat)
        self.backend = app.Backend(lang=self.lang, settings=settings, folder=self.folder,
                                   opener=self.opened.append)
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def tearDown(self):
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "undefined" in m.lower()
                or "typeerror" in m.lower() or "referenceerror" in m.lower()]

    def find(self, name):
        item = self.window.findChild(QObject, name)
        todo = [self.window.contentItem()]
        while item is None and todo:
            current = todo.pop()
            if current.objectName() == name:
                item = current
            todo.extend(current.childItems())
        self.assertIsNotNone(item, name)
        return item

    def click(self, name):
        self.find(name).clicked.emit()
        self.app.processEvents()

    def test_without_a_camera(self):
        if self.window.property("hasCamera"):
            self.skipTest("this machine has a camera")
        self.assertTrue(self.find("noCamera").property("visible"))
        self.assertFalse(self.find("shutter").property("enabled"))
        self.assertFalse(self.find("lastCapture").property("visible"))
        self.assertEqual(self.problems(), [])

    def test_modes_timer_and_settings(self):
        self.click("mode_video")
        self.assertEqual(self.backend.mode, "video")
        self.assertFalse(self.find("timerButton").property("visible"))
        self.click("mode_photo")
        self.assertTrue(self.find("timerButton").property("visible"))
        for expected in (2, 5, 10, 0):
            self.click("timerButton")
            self.assertEqual(self.backend.timer, expected)
        self.click("settingsButton")
        self.assertTrue(self.window.property("settingsOpen"))
        self.click("grid_thirds")
        self.assertEqual(self.backend.grid, "thirds")
        self.click("recordAudio")
        self.assertFalse(self.backend.recordAudio)
        self.click("openFolder")
        self.assertTrue(self.folder.is_dir())
        self.assertEqual(self.opened[-1].toLocalFile(), str(self.folder))
        self.click("closeSettings")
        self.assertFalse(self.window.property("settingsOpen"))
        self.assertEqual(self.problems(), [])

    def test_last_capture_shows_and_opens(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        photo = Path(self.backend.newPhotoPath(""))
        self.assertTrue(photo.name.startswith("IMG_"))
        photo.write_bytes(b"not really a picture")
        self.backend.captured(QUrl.fromLocalFile(str(photo)).toString())
        self.app.processEvents()
        self.assertTrue(self.find("lastCapture").property("visible"))
        self.click("lastCapture")
        self.assertEqual(self.opened[-1].toLocalFile(), str(photo))
        self.assertTrue(self.backend.newVideoUrl().endswith(".mp4"))


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
