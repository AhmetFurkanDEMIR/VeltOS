"""Loads the real Calculator window offscreen, clicks through its modes,
lists, flyouts, navigation, settings and keep-on-top; any QML warning
fails the test. The Turkish class runs in the Turkish C locale when it is
installed (PySide6 keyword-argument bug, see AGENTS.md)."""

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
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, QUrl, Qt, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication, QKeyEvent
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
        from veltos_calculator import app
        self.messages.clear()
        self.scripts = []
        settings = QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat)
        self.backend = app.Backend(lang=self.lang, settings=settings, kwin=self.scripts.append)
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
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def find(self, name):
        # Repeater delegates are not QObject children: walk the item tree.
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
        item = self.find(name)
        item.clicked.emit()
        self.app.processEvents()

    def text(self, name):
        return self.find(name).property("text")

    def type_keys(self, text):
        for char in text:
            key = {"+": Qt.Key.Key_Plus, "=": Qt.Key.Key_Equal, "*": Qt.Key.Key_Asterisk}.get(
                char, Qt.Key(ord(char.upper())) if char.isalnum() else Qt.Key.Key_unknown)
            for kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
                QGuiApplication.sendEvent(self.window, QKeyEvent(kind, key, Qt.KeyboardModifier.NoModifier, char))
        self.app.processEvents()

    def test_standard_keys(self):
        for key in ("key_7", "key_+", "key_8", "key_=",):
            self.click(key)
        self.assertEqual(self.text("display"), "15")
        self.assertEqual(self.text("expression"), "7 + 8 =")
        self.click("key_sqr")
        self.assertEqual(self.text("expression"), "sqr(15)")
        self.assertEqual(self.text("display"), "225")
        self.click("key_/")
        self.click("key_0")
        self.click("key_=")
        self.assertEqual(self.text("display"), self.backend.texts["divide_by_zero"])
        self.assertFalse(self.find("key_+").property("enabled"))
        self.click("key_C")
        self.assertEqual(self.text("display"), "0")
        self.assertEqual(self.problems(), [])

    def test_keyboard(self):
        self.type_keys("12*3=")
        self.assertEqual(self.text("display"), "36")
        self.assertEqual(self.problems(), [])

    def test_history_and_memory_sheets(self):
        self.window.setProperty("width", 340)
        for key in ("key_2", "key_*", "key_4", "key_=", "key_="):      # 8, then 32 (repeat)
            self.click(key)
        self.backend.press("MS")
        self.app.processEvents()
        self.click("historyButton")
        self.assertTrue(self.find("sheet").property("visible"))
        self.assertEqual(self.find("historyList").property("count"), 2)
        self.click("historyButton")
        self.click("memoryButton")
        self.assertEqual(self.find("memoryList").property("count"), 1)
        self.click("memoryClear")
        self.assertEqual(self.backend.memory, [])
        self.assertEqual(self.problems(), [])

    def test_wide_window_side_panel(self):
        self.window.setProperty("width", 760)
        self.app.processEvents()
        self.assertTrue(self.find("sidePanel").property("visible"))
        self.assertFalse(self.find("historyButton").property("visible"))
        self.backend.press("5")
        self.backend.press("=")
        self.click("tab_memory")
        self.click("tab_history")
        self.assertEqual(self.problems(), [])

    def test_scientific_mode(self):
        self.click("navButton")
        self.assertTrue(self.window.property("navOpen"))
        self.click("nav_scientific")
        self.assertEqual(self.backend.mode, "scientific")
        self.assertEqual(self.text("modeTitle"), self.backend.texts["scientific"])
        self.assertEqual(self.find("keypad").property("columns"), 5)
        for key in ("key_2", "key_+", "key_3", "key_*", "key_4", "key_="):
            self.click(key)
        self.assertEqual(self.text("display"), "14")
        self.click("key_paren")
        self.assertEqual(self.backend.openParens, 1)
        self.click("key_2nd")
        self.assertEqual(self.find("key_sqr").property("label"), "<i>x</i><sup>3</sup>")
        self.click("key_2nd")
        self.click("angleButton")
        self.assertEqual(self.backend.angle, "RAD")
        self.click("feButton")
        self.click("trigButton")
        self.assertTrue(self.find("flyout").property("visible"))
        self.click("flyout_hyp")
        self.assertEqual(self.find("flyout_sin").property("label"), "sinh")
        self.click("flyout_sin")
        self.assertFalse(self.find("flyout").property("visible"))
        self.assertIn("sinh(", self.text("expression"))     # after "(": "(sinh(14)"
        self.click("funcButton")
        self.click("flyout_abs")
        self.assertFalse(self.find("flyout").property("visible"))
        self.assertEqual(self.problems(), [])

    def test_settings_and_theme(self):
        self.click("nav_settings")
        self.assertTrue(self.find("settingsPage").property("visible"))
        self.assertFalse(self.find("keypad").property("visible"))
        self.click("theme_dark")
        self.assertTrue(self.backend.darkMode)
        self.click("theme_light")
        self.assertFalse(self.backend.darkMode)
        self.click("nav_standard")
        self.assertTrue(self.find("keypad").property("visible"))
        self.assertEqual(self.problems(), [])

    def test_keep_on_top(self):
        self.click("keepOnTopButton")
        self.assertTrue(self.backend.keepOnTop)
        self.assertIn("keepAbove = true", self.scripts[-1])
        self.assertFalse(self.find("navButton").property("visible"))
        self.assertEqual(self.find("keypad").property("columns"), 4)
        self.find("key_/")                                  # ÷ stays in the compact keypad
        self.click("fullViewButton")
        self.assertFalse(self.backend.keepOnTop)
        self.assertIn("keepAbove = false", self.scripts[-1])
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

    def test_turkish_decimal_key(self):
        self.assertEqual(self.find("key_.").property("label"), ",")
        for key in ("key_1", "key_.", "key_5", "key_+", "key_1", "key_="):
            self.click(key)
        self.assertEqual(self.text("display"), "2,5")


if __name__ == "__main__":
    unittest.main()
