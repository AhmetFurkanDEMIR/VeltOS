"""VeltOS Snipping Tool without a screen: file names, folders, the KWin
window list, cropping, freeform, markup, eraser, notification command and
the capture flow with a given picture (no Spectacle, no KWin)."""

import datetime
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from veltos_snip import capture, strings  # noqa: E402

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QSettings
    from PySide6.QtGui import QColor, QGuiApplication, QImage
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

NOW = datetime.datetime(2026, 10, 20, 10, 30, 15)


class FileTests(unittest.TestCase):
    def test_capture_command_asks_spectacle_without_window(self):
        command = capture.capture_command("/tmp/x.png")
        self.assertEqual(command[0], "spectacle")
        for option in ("--background", "--nonotify", "--fullscreen"):
            self.assertIn(option, command)
        self.assertEqual(command[-2:], ["--output", "/tmp/x.png"])

    def test_pictures_folder_from_user_dirs(self):
        home = Path(tempfile.mkdtemp())
        config = home / ".config"
        config.mkdir()
        self.assertEqual(capture.pictures_dir(home, config), home / "Pictures")
        (config / "user-dirs.dirs").write_text('XDG_PICTURES_DIR="$HOME/Resimler"\n', encoding="utf-8")
        self.assertEqual(capture.screenshots_dir(home, config), home / "Resimler" / "Screenshots")
        # "$HOME/" alone means the folder is switched off: use Pictures.
        (config / "user-dirs.dirs").write_text('XDG_PICTURES_DIR="$HOME/"\n', encoding="utf-8")
        self.assertEqual(capture.pictures_dir(home, config), home / "Pictures")

    def test_windows_style_names(self):
        folder = Path(tempfile.mkdtemp())
        first = capture.unique_path(folder, NOW)
        self.assertEqual(first.name, "Screenshot 2026-10-20 103015.png")
        first.write_bytes(b"x")
        self.assertEqual(capture.unique_path(folder, NOW).name, "Screenshot 2026-10-20 103015 (2).png")


class WindowListTests(unittest.TestCase):
    def test_script_reports_to_our_service(self):
        script = capture.window_script("org.veltos.SnippingTool.p42", "/SnippingTool", "org.veltos.SnippingTool")
        self.assertIn('callDBus("org.veltos.SnippingTool.p42", "/SnippingTool", "org.veltos.SnippingTool", '
                      '"setWindows"', script)
        self.assertIn("workspace.stackingOrder", script)
        self.assertIn("frameGeometry", script)

    def test_parse_and_topmost(self):
        data = json.dumps([{"x": 0, "y": 0, "width": 800, "height": 600, "caption": "Below"},
                           {"x": 100.4, "y": 50, "width": 300, "height": 200, "caption": "Above"},
                           {"x": 1, "y": 1, "width": 0, "height": 5},
                           {"caption": "broken"}])
        windows = capture.parse_windows(data)
        self.assertEqual([w["caption"] for w in windows], ["Below", "Above"])
        self.assertEqual(windows[1]["x"], 100)
        self.assertEqual(capture.window_at(windows, 150, 100), 1)
        self.assertEqual(capture.window_at(windows, 10, 10), 0)
        self.assertEqual(capture.window_at(windows, 900, 10), -1)
        self.assertEqual(capture.parse_windows("not json"), [])

    def test_clamp(self):
        self.assertEqual(capture.clamp_rect(-5, -5, 20, 20, 100, 100), (0, 0, 15, 15))
        self.assertIsNone(capture.clamp_rect(120, 0, 10, 10, 100, 100))


class StrokeTests(unittest.TestCase):
    def test_eraser_touches_whole_strokes(self):
        stroke = {"tool": "pen", "width": 4, "points": [0, 0, 100, 0]}
        self.assertTrue(capture.stroke_hit(stroke, 50, 5, 4))
        self.assertFalse(capture.stroke_hit(stroke, 50, 20, 4))
        dot = {"tool": "pen", "width": 2, "points": [10, 10]}
        self.assertTrue(capture.stroke_hit(dot, 12, 10, 2))


class TextTests(unittest.TestCase):
    def test_both_languages(self):
        en, tr = strings.texts("en"), strings.texts("tr")
        self.assertEqual(set(en), set(tr))
        self.assertEqual(tr["app_title"], "Ekran Alıntısı Aracı")


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class PictureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def picture(self, colour="#ff0000", width=100, height=80):
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(colour))
        return image

    def test_crop(self):
        part = capture.crop(self.picture(), 10, 10, 20, 30)
        self.assertEqual((part.width(), part.height()), (20, 30))
        self.assertIsNone(capture.crop(self.picture(), 10, 10, 0, 30))

    def test_freeform_is_transparent_outside_the_shape(self):
        shape = capture.freeform(self.picture(), [10, 10, 90, 10, 50, 70])
        self.assertEqual((shape.width(), shape.height()), (80, 60))
        self.assertEqual(shape.pixelColor(2, 55).alpha(), 0)          # outside the triangle
        self.assertEqual(shape.pixelColor(40, 10).red(), 255)          # inside
        self.assertIsNone(capture.freeform(self.picture(), [1, 1, 5, 5]))

    def test_pen_and_highlighter_strokes(self):
        strokes = [{"tool": "pen", "color": "#000000", "width": 4, "points": [10, 20, 90, 20]},
                   {"tool": "highlighter", "color": "#ffff00", "width": 10, "points": [10, 60, 90, 60]}]
        result = capture.compose(self.picture("#ffffff"), strokes)
        self.assertLess(result.pixelColor(50, 20).red(), 60)            # black pen
        marked = result.pixelColor(50, 60)
        self.assertEqual(marked.red(), 255)
        self.assertTrue(100 < marked.blue() < 255)                    # see-through yellow
        self.assertEqual(result.pixelColor(50, 40), QColor("#ffffff"))  # untouched

    def test_toast_command(self):
        from veltos_snip import app
        texts = dict(strings.texts("tr"))
        texts["toast_body"] = "it's a snip"
        command = app.toast_command(texts, Path("/home/u/Resimler/Screenshots/Screenshot 1.png"))
        self.assertEqual(command[:3], ["gdbus", "call", "--session"])
        self.assertIn("'it\\'s a snip'", command)
        self.assertIn("'image-path': <'file:///home/u/Resimler/Screenshots/Screenshot 1.png'>", command[-2])
        self.assertEqual(command[-1], str(app.TOAST_MS))
        # The "32" of "uint32" is not part of the number (it was, VM 2026-10-20).
        self.assertEqual(app.toast_id("(uint32 5,)\n"), 5)
        self.assertIsNone(app.toast_id(""))


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class FlowTests(unittest.TestCase):
    """Snipper and Editor with a given picture; the overlay windows load
    offscreen."""

    @classmethod
    def setUpClass(cls):
        cls.home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(cls.home)
        os.environ["XDG_CONFIG_HOME"] = str(cls.home / ".config")
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    @classmethod
    def tearDownClass(cls):
        QGuiApplication.clipboard().clear()

    def setUp(self):
        self.keep = []

    def tearDown(self):
        # The overlay is deleted before its backend, as in the program.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.keep.clear()

    def snipper(self, windows=()):
        from veltos_snip import app
        screen = QGuiApplication.primaryScreen().geometry()
        image = QImage(screen.width(), screen.height(), QImage.Format.Format_ARGB32)
        image.fill(QColor("#336699"))
        snipper = app.Snipper(strings.texts("en"), "rect", capture_image=image, windows=list(windows))
        results = []
        snipper.finished.connect(results.append)
        snipper.cancelled.connect(lambda: results.append(None))
        snipper.start()
        self.app.processEvents()
        self.keep.append(snipper)
        return snipper, results

    def test_rectangle_window_free_and_cancel(self):
        snipper, results = self.snipper([{"x": 5, "y": 6, "width": 40, "height": 30, "caption": "A"}])
        snipper.captureRect(10, 10, 50, 40)
        self.assertEqual((results[-1].width(), results[-1].height()), (50, 40))
        snipper, results = self.snipper([{"x": 5, "y": 6, "width": 40, "height": 30, "caption": "A"}])
        self.assertEqual(snipper.windowAt(20, 20), 0)
        snipper.captureWindow(0)
        self.assertEqual((results[-1].width(), results[-1].height()), (40, 30))
        snipper, results = self.snipper()
        snipper.captureFree([0, 0, 60, 0, 30, 40])
        self.assertEqual((results[-1].width(), results[-1].height()), (60, 40))
        snipper, results = self.snipper()
        snipper.cancel()
        self.assertEqual(results, [None])

    def test_editor_markup_crop_save_copy(self):
        from veltos_snip import app
        settings = app.Settings(QSettings(str(self.home / "snip.conf"), QSettings.Format.IniFormat))
        editor = app.Editor(lang="en", settings=settings, start=lambda command: None)
        image = QImage(200, 100, QImage.Format.Format_ARGB32)
        image.fill(QColor("#ffffff"))
        editor.set_image(image)
        strokes = json.dumps([{"tool": "pen", "color": "#000000", "width": 4, "points": [0, 50, 200, 50]},
                              {"tool": "pen", "color": "#ff0000", "width": 4, "points": [10, 10]}])
        left = json.loads(editor.eraseAt(strokes, 100, 52, 3))
        self.assertEqual([s["color"] for s in left], ["#ff0000"])
        editor.applyCrop(0, 0, 100, 60, strokes)
        self.assertEqual((editor.imageWidth, editor.imageHeight), (100, 60))
        folder = self.home / "Pictures" / "Screenshots"
        before = set(folder.glob("Screenshot *.png"))
        editor.save("[]")
        saved = set(folder.glob("Screenshot *.png")) - before
        self.assertEqual(len(saved), 1)
        self.assertEqual(QImage(str(saved.pop())).width(), 100)
        self.assertEqual(editor.message, strings.texts("en")["saved"])
        self.assertTrue(editor.canShowSaved)
        editor.copy("[]")
        self.assertEqual(QGuiApplication.clipboard().image().width(), 100)
        editor.setMode("free")
        editor.setDelay(5)
        editor.setDelay(7)                      # not offered: ignored
        self.assertEqual((editor.mode, editor.delay), ("free", 5))

    def test_delivery_copies_and_saves(self):
        from veltos_snip import app
        image = QImage(30, 20, QImage.Format.Format_ARGB32)
        image.fill(QColor("#00ff00"))
        delivery = app.Delivery(strings.texts("en"), auto_save=True, notify=False)
        path = delivery.deliver(image, now=NOW)
        self.assertEqual(path.name, "Screenshot 2026-10-20 103015.png")
        self.assertTrue(path.is_file())
        self.assertEqual(QGuiApplication.clipboard().image().width(), 30)


if __name__ == "__main__":
    unittest.main()
