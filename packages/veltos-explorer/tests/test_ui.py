"""Loads the real File Explorer window offscreen and uses it: tabs,
navigation, views, selection, new folder, rename, menus. Any QML warning
or error fails the test."""

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
    from PySide6.QtCore import Q_ARG, QMetaObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def turkish_locale():
    """Name of an installed Turkish UTF-8 locale, or None."""
    current = locale.setlocale(locale.LC_ALL)
    for name in ("tr_TR.UTF-8", "tr_TR.utf8"):
        try:
            locale.setlocale(locale.LC_ALL, name)
        except locale.Error:
            continue
        locale.setlocale(locale.LC_ALL, current)
        return name
    return None


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class ExplorerWindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(cls.home)
        os.environ["XDG_CONFIG_HOME"] = str(cls.home / ".config")
        os.environ["XDG_DATA_HOME"] = str(cls.home / ".local/share")
        os.environ["XDG_CACHE_HOME"] = str(cls.home / ".cache")
        for name in ("Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"):
            (cls.home / name).mkdir()
        (cls.home / "Documents" / "report.txt").write_text("hello", encoding="utf-8")
        (cls.home / "Documents" / "Old").mkdir()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        # Files copied to the clipboard are a QMimeData made in Python; if Qt
        # deletes it after Python has shut down, the process crashes.
        QGuiApplication.clipboard().clear()
        cls.app.processEvents()
        # Messages Qt prints while shutting down must not call into Python.
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_explorer import app as explorer, places
        places.HOME = self.home
        self.started = []
        self.messages.clear()
        self.backend = explorer.Backend(lang=self.lang, threaded=False,
                                        start=lambda command, cwd=None: self.started.append(command),
                                        runner=lambda command, timeout=20: (1, ""))
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(explorer.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    def tearDown(self):
        # Delete the window before the backend it uses.
        self.engine.deleteLater()
        self.app.processEvents()
        self.backend.deleteLater()
        self.app.processEvents()

    def call(self, name, *args):
        QMetaObject.invokeMethod(self.window, name, *[Q_ARG("QVariant", a) for a in args])
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_home_this_pc_and_folders(self):
        tab = self.backend.current
        self.assertEqual(tab.kind, "home")
        tab.navigate("thispc:")
        tab.navigate(str(self.home / "Documents"))
        self.app.processEvents()
        self.assertEqual(tab.kind, "folder")
        self.assertEqual([tab.items.get(r)["name"] for r in range(tab.items.count)], ["Old", "report.txt"])
        # Like Windows: the address starts at the known folder.
        self.assertEqual([c["name"] for c in tab.crumbs], ["Documents"])
        tab.navigate(str(self.home / "Documents" / "Old"))
        self.assertEqual([c["name"] for c in tab.crumbs], ["Documents", "Old"])
        tab.back()
        for mode in ("tiles", "small", "medium", "large", "xlarge", "details"):
            tab.setViewMode(mode)
            self.app.processEvents()
        tab.back()
        self.assertEqual(tab.kind, "thispc")
        tab.forward()
        tab.up()
        self.assertEqual(tab.location, str(self.home))
        tab.navigate("trash:")
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_long_folders_scroll_with_the_wheel(self):
        from PySide6.QtCore import QObject, QPoint, QPointF, Qt
        from PySide6.QtGui import QWheelEvent
        many = self.home / "Many"
        many.mkdir(exist_ok=True)
        for i in range(150):
            (many / f"file-{i:03}.txt").write_text("x", encoding="utf-8")
        self.window.setProperty("width", 1000)
        self.window.setProperty("height", 600)
        tab = self.backend.current
        tab.navigate(str(many))
        tab.setViewMode("details")
        self.app.processEvents()
        view = self.window.findChild(QObject, "folderView")
        details = view.property("view")
        self.assertEqual(details.property("contentY"), details.property("originY"))
        # A wheel turn over the items, as a virtual machine's absolute
        # pointer sends it (the old WheelHandler ignored it).
        centre = QPointF(self.window.property("width") / 2, self.window.property("height") / 2)
        for _ in range(3):
            event = QWheelEvent(centre, centre, QPoint(0, 0), QPoint(0, -120), Qt.NoButton, Qt.NoModifier,
                                Qt.NoScrollPhase, False)
            self.app.sendEvent(self.window, event)
            self.app.processEvents()
        self.assertGreater(details.property("contentY"), details.property("originY") + 100)
        self.assertEqual(self.problems(), [])

    def test_tabs(self):
        self.backend.newTab(str(self.home / "Pictures"))
        self.app.processEvents()
        self.assertEqual(len(self.backend.tabs), 2)
        self.assertEqual(self.backend.current.title, "Pictures")
        self.assertEqual(self.backend.current.viewMode, "large")      # pictures: large icons
        self.assertTrue(self.backend.closeTab(1))
        self.assertFalse(self.backend.closeTab(0))                     # last tab closes the window
        self.assertEqual(self.problems(), [])

    def test_select_copy_new_rename_delete(self):
        tab = self.backend.current
        tab.navigate(str(self.home / "Documents"))
        self.app.processEvents()
        tab.items.select(1, "single")
        self.assertEqual(tab.items.selectedCount, 1)
        self.backend.copy()
        self.assertTrue(self.backend.canPaste)
        self.backend.paste()
        self.assertEqual(self.started[-1][:3], ["kioclient", "--interactive", "copy"])
        self.assertTrue(self.started[-1][-1].endswith("report - Copy.txt"))
        self.backend.createNew("folder")
        self.app.processEvents()
        new_folder = self.home / "Documents" / self.backend.text("new_folder_name")
        self.assertTrue(new_folder.is_dir())
        self.assertEqual(self.backend.rename(str(new_folder), "Old"), self.backend.text("rename_exists"))
        self.assertEqual(self.backend.rename(str(new_folder), "Trip " + self.lang), "")
        tab.items.selectPath(str(self.home / "Documents" / "report.txt"))
        self.call("runAction", "delete", None)
        self.assertEqual(self.started[-1][-1], "trash:/")
        self.call("itemMenu", None, 10, 10)        # null: at the window
        self.call("backgroundMenu", None, 10, 10)
        tab.search("rep")
        self.app.processEvents()
        self.assertEqual(tab.kind, "search")
        self.assertEqual(self.problems(), [])


class TurkishExplorerTests(ExplorerWindowTests):
    """Turkish texts and, where the locale is installed, the Turkish C locale:
    PySide6 maps keyword arguments to setters with the C library's
    toupper(), and File Explorer did not start on Turkish systems
    (QTimer(interval=...) -> "setİnterval")."""
    lang = "tr"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.old_locale = locale.setlocale(locale.LC_ALL)
        cls.turkish = turkish_locale()
        if cls.turkish:
            locale.setlocale(locale.LC_ALL, cls.turkish)

    @classmethod
    def tearDownClass(cls):
        locale.setlocale(locale.LC_ALL, cls.old_locale)
        super().tearDownClass()

    def test_turkish_c_locale_is_used_when_installed(self):
        if self.turkish:
            self.assertEqual("i".upper(), "I")          # Python is locale-independent
            self.assertTrue(locale.setlocale(locale.LC_CTYPE).startswith("tr_TR"))
        else:
            self.skipTest("tr_TR.UTF-8 locale not installed")


if __name__ == "__main__":
    unittest.main()
