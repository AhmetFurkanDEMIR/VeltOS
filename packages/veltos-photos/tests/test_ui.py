"""Loads the real Photos window offscreen with a small picture library:
gallery, favorites, filter, viewer, rotate, edit, file information,
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
    from PySide6.QtCore import QCoreApplication, QEvent, QSettings, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PIL import Image
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 and Pillow (Build-Depends)")
class PhotosTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
        os.environ["XDG_CACHE_HOME"] = str(home / ".cache")
        cls.home = home
        pictures = home / "Pictures"
        (pictures / "Holiday").mkdir(parents=True)
        for i, color in enumerate([(220, 30, 30), (30, 160, 60), (40, 60, 220)]):
            Image.new("RGB", (60 + i * 10, 40), color).save(pictures / f"Holiday/p{i}.jpg", quality=90)
        Image.new("RGB", (30, 30), (200, 200, 0)).save(pictures / "sun.png")
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_photos import app
        self.messages.clear()
        settings = QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat)
        self.backend = app.Backend(lang=self.lang, settings=settings, scan=False)
        self.backend.scan_now()
        self.engine = QQmlApplicationEngine()
        self.engine.addImageProvider("thumb", app.ThumbnailProvider())
        self.engine.addImageProvider("icon", app.IconProvider())
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.rootContext().setContextProperty("openedFile", False)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.settle()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def tearDown(self):
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def settle(self):
        for _ in range(20):
            self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def paths(self):
        return [item["path"] for row in self.backend.rows.rows for item in row["items"]]

    def test_gallery_lists_pictures_by_month(self):
        self.assertEqual(self.backend.count, 4)
        self.assertEqual(self.backend.rows.rows[0]["type"], "header")
        self.backend.setColumns(2)
        self.assertEqual([len(r["items"]) for r in self.backend.rows.rows if r["type"] == "row"], [2, 2])
        self.backend.setQuery("holiday p1")
        self.assertEqual([Path(p).name for p in self.paths()], ["p1.jpg"])
        self.backend.setQuery("")
        self.backend.setFilter("video")
        self.assertEqual(self.backend.count, 0)
        self.backend.setFilter("all")
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_favorites_page(self):
        first = self.paths()[0]
        self.backend.toggleFavorite(first)
        self.window.setProperty("pane", "favorites")
        self.backend.setPage("favorites")
        self.assertEqual(self.paths(), [first])
        self.backend.toggleFavorite(first)
        self.assertEqual(self.paths(), [])
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_viewer_rotate_edit_and_info(self):
        path = str(self.home / "Pictures/Holiday/p0.jpg")
        self.backend.openInViewer(path)
        self.settle()
        self.assertTrue(self.window.property("viewing"))
        self.assertEqual(self.backend.viewerItem["path"], path)
        step = 1 if self.backend.viewerIndex == 0 else -1
        self.backend.viewerStep(step)
        self.assertNotEqual(self.backend.viewerItem["path"], path)
        self.backend.viewerGo(self.backend.viewerItems.index(next(i for i in self.backend.viewerItems
                                                                 if i["path"] == path)))
        self.assertTrue(self.backend.rotate(path))
        with Image.open(path) as image:
            self.assertEqual(image.size, (40, 60))
        info = self.backend.fileInfo(path)
        self.assertEqual(info["dimensions"], "40 x 60")
        saved = self.backend.saveEdit(path, {"crop": [0, 0, 1, 0.5], "brightness": 20}, True)
        self.assertTrue(saved.endswith(f"p0 - {self.backend.texts['copy_word']}.jpg"))
        self.assertEqual(self.backend.viewerItem["path"], saved)          # the copy is shown
        with Image.open(saved) as image:
            self.assertEqual(image.size, (40, 30))
        self.backend.closeViewer()
        self.settle()
        self.assertFalse(self.window.property("viewing"))
        self.assertEqual(self.problems(), [])

    def test_settings_and_folders(self):
        self.window.setProperty("pane", "settings")
        extra = self.home / "Extra"
        extra.mkdir(exist_ok=True)
        Image.new("RGB", (10, 10)).save(extra / "x.png")
        self.backend.addFolder(str(extra))
        self.assertIn(str(extra), self.backend.folders)
        self.backend.scan_now()
        self.assertEqual(self.backend.total, 5)
        self.backend.removeFolder(str(extra))
        self.assertNotIn(str(extra), self.backend.folders)
        self.backend.setTheme("dark")
        self.assertTrue(self.backend.darkMode)
        self.settle()
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 and Pillow (Build-Depends)")
class TurkishPhotosTests(PhotosTests):
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
