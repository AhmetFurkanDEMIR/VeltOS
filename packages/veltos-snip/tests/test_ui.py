"""Loads the real Snipping Tool window and the screen overlay offscreen
and goes through their states; any QML warning fails the test. The
Turkish class runs in the Turkish C locale when it is installed."""

import json
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
    from PySide6.QtCore import Q_ARG, QCoreApplication, QEvent, QMetaObject, QSettings, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QColor, QGuiApplication, QImage
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
        cls.home = home
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        QGuiApplication.clipboard().clear()
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_snip import app
        self.messages.clear()
        settings = app.Settings(QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat))
        self.editor = app.Editor(lang=self.lang, settings=settings, start=lambda command: None)
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.editor)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def tearDown(self):
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def call(self, name, *values):
        QMetaObject.invokeMethod(self.window, name, *[Q_ARG("QVariant", v) for v in values])
        self.app.processEvents()

    def strokes(self):
        value = self.window.property("strokes")      # a list, or a QJSValue holding one
        return value.toVariant() if hasattr(value, "toVariant") else value

    def test_empty_window_then_snip_and_markup(self):
        self.assertFalse(self.editor.hasImage)
        image = QImage(640, 360, QImage.Format.Format_ARGB32)
        image.fill(QColor("#4f7cff"))
        self.editor.set_image(image)
        self.app.processEvents()
        for tool in ("pen", "highlighter", "eraser", "crop", "crop", "pen"):
            self.call("chooseTool", tool)
        self.call("setStrokes", [{"tool": "pen", "color": "#000000", "width": 4, "points": [1, 2, 300, 200]}])
        self.assertEqual(len(self.strokes()), 1)
        self.call("undo")
        self.assertEqual(len(self.strokes()), 0)
        self.call("redo")
        self.assertEqual(len(self.strokes()), 1)
        self.call("chooseTool", "crop")
        self.call("applyCrop")
        self.app.processEvents()
        self.assertEqual(self.editor.imageWidth, 640)
        self.assertEqual(len(self.strokes()), 0)      # new picture, markup baked in
        self.editor.copy("[]")
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_overlay(self):
        from veltos_snip import app, strings
        screen = QGuiApplication.primaryScreen().geometry()
        image = QImage(screen.width(), screen.height(), QImage.Format.Format_ARGB32)
        image.fill(QColor("#203040"))
        snipper = app.Snipper(strings.texts(self.lang), "rect", capture_image=image,
                              windows=[{"x": 0, "y": 0, "width": 100, "height": 80, "caption": "A"}])
        done = []
        snipper.finished.connect(done.append)
        snipper.start()
        self.app.processEvents()
        for mode in ("window", "free", "rect"):
            snipper.setMode(mode)
            self.app.processEvents()
        self.assertEqual(snipper.mode, "rect")
        snipper.setMode("full")                 # "Full screen" snips at once
        self.app.processEvents()
        self.assertEqual(done[0].width(), screen.width())
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)   # the overlay goes first
        self.app.processEvents()
        self.assertEqual(self.problems(), [])


class TurkishWindowTests(WindowTests):
    lang = "tr"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.old_locale = locale.setlocale(locale.LC_ALL)
        for name in ("tr_TR.UTF-8", "tr_TR.utf8"):
            try:
                locale.setlocale(locale.LC_ALL, name)
                break
            except locale.Error:
                continue

    @classmethod
    def tearDownClass(cls):
        locale.setlocale(locale.LC_ALL, cls.old_locale)
        super().tearDownClass()

    def test_turkish_texts(self):
        self.assertEqual(self.editor.texts["new"], "Yeni")
        self.assertEqual(json.loads(self.editor.eraseAt("[]", 0, 0, 1)), [])


if __name__ == "__main__":
    unittest.main()
