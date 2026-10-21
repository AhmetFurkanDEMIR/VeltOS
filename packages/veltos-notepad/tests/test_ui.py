"""Loads the real Notepad window offscreen: opens, edits, finds, replaces,
saves, restores the session and opens the menus and Settings; any QML
warning fails the test. The Turkish class runs in the Turkish C locale
when it is installed (PySide6 keyword-argument bug, see AGENTS.md)."""

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
    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QSettings, QUrl, Q_ARG, qInstallMessageHandler
    from PySide6.QtGui import QTextCursor
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtWidgets import QApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class NotepadTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
        os.environ["XDG_DATA_HOME"] = str(home / ".local/share")
        cls.home = home
        cls.app = QApplication.instance() or QApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        self.messages.clear()
        self.session = self.home / f"{self.id()}.json"
        self.settings = QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat)
        self.load()

    def load(self, restore=True):
        from veltos_notepad import app
        self.backend = app.Backend(lang=self.lang, settings=self.settings, session_file=self.session,
                                   restore=restore)
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

    def run_action(self, action):
        QMetaObject.invokeMethod(self.window, "run", Q_ARG("QVariant", action))
        self.app.processEvents()

    def current_doc(self):
        tab = self.backend.current
        return self.backend._docs[tab["tabId"]]

    def type_text(self, text):
        cursor = QTextCursor(self.current_doc())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.app.processEvents()

    def test_window_and_new_tab(self):
        self.assertEqual(self.backend.tabCount, 1)
        self.assertEqual(self.backend.current["title"], self.backend.texts["untitled"])
        self.run_action("new-tab")
        self.assertEqual(self.backend.tabCount, 2)
        self.assertEqual(self.backend.currentIndex, 1)
        self.assertIsNotNone(self.window.property("area"))
        self.assertEqual(self.problems(), [])

    def test_open_edit_save_keeps_encoding_and_line_endings(self):
        path = self.home / "old windows file.txt"
        path.write_bytes(b"\xff\xfe" + "Merhaba\r\nDünya\r\n".encode("utf-16-le"))
        self.backend.openPaths([str(path)])
        self.app.processEvents()
        self.assertEqual(self.backend.tabCount, 1)          # the blank Untitled tab was replaced
        tab = self.backend.current
        self.assertEqual((tab["title"], tab["encoding"], tab["eol"]), (path.name, "UTF-16 LE", "CRLF"))
        self.assertEqual(self.window.property("area").property("text"), "Merhaba\nDünya\n")
        self.assertFalse(tab["modified"])
        self.type_text("Son satır")
        self.assertTrue(self.backend.current["modified"])
        self.assertTrue(self.window.property("title").startswith("*"))
        self.assertTrue(self.backend.save(self.backend.currentIndex))
        self.assertEqual(path.read_bytes(), b"\xff\xfe" + "Merhaba\r\nDünya\r\nSon satır".encode("utf-16-le"))
        self.assertFalse(self.backend.current["modified"])
        self.assertIn(str(path.resolve()), self.backend.recentFiles)
        self.assertEqual(self.problems(), [])

    def test_find_replace_and_positions(self):
        self.type_text("one two one\nthree One")
        tab_id = self.backend.current["tabId"]
        self.assertEqual(self.backend.find(tab_id, "one", 0, True, True, True), [0, 3])
        self.assertEqual(self.backend.find(tab_id, "one", 3, True, True, True), [8, 11])
        self.assertEqual(self.backend.find(tab_id, "one", 11, True, True, False), [])
        self.assertEqual(self.backend.find(tab_id, "one", 11, True, False, False), [18, 21])
        self.assertEqual(self.backend.find(tab_id, "one", 11, True, True, True), [0, 3])     # wraps
        self.assertEqual(self.backend.lineColumn(tab_id, 14), [2, 3])
        self.assertEqual(self.backend.positionOfLine(tab_id, 2), 12)
        self.assertEqual(self.backend.replaceAll(tab_id, "one", "1", False), 3)
        self.assertEqual(self.current_doc().toPlainText(), "1 two 1\nthree 1")
        self.current_doc().undo()                            # one step, like Windows
        self.assertEqual(self.current_doc().toPlainText(), "one two one\nthree One")
        self.run_action("find")
        from PySide6.QtCore import QObject
        self.assertTrue(self.window.findChild(QObject, "findBar").property("visible"))
        self.assertEqual(self.problems(), [])

    def test_session_comes_back(self):
        self.type_text("unsaved idea")
        saved = self.home / "saved.txt"
        saved.write_text("on disk\n", encoding="utf-8")
        self.backend.openPaths([str(saved)])
        self.backend.saveSession()
        data = json.loads(self.session.read_text(encoding="utf-8"))
        self.assertEqual([t.get("text") for t in data["tabs"]], ["unsaved idea", None])
        self.tearDown()
        self.load()
        self.assertEqual(self.backend.tabCount, 2)
        self.assertEqual(self.backend.model.tabs[0]["title"], self.backend.texts["untitled"])
        self.assertTrue(self.backend.model.tabs[0]["modified"])
        self.backend.setCurrentIndex(0)
        self.app.processEvents()
        self.assertEqual(self.current_doc().toPlainText(), "unsaved idea")
        self.assertEqual(self.backend.model.tabs[1]["path"], str(saved.resolve()))
        self.assertEqual(self.problems(), [])

    def test_closing_a_changed_tab_asks(self):
        self.type_text("something")
        QMetaObject.invokeMethod(self.window, "requestCloseTab", Q_ARG("QVariant", 0))
        self.app.processEvents()
        self.assertEqual(self.backend.tabCount, 1)           # still open, the question is shown
        self.backend.closeTab(0)
        self.assertEqual(self.backend.tabCount, 1)           # a fresh Untitled tab
        self.assertFalse(self.backend.current["modified"])
        self.assertEqual(self.problems(), [])

    def test_menus_settings_and_zoom(self):
        for action in ("zoom-in", "zoom-in", "zoom-out", "word-wrap", "status-bar", "time-date"):
            self.run_action(action)
        self.assertEqual(self.backend.zoom, 110)
        self.assertFalse(self.backend.wordWrap)
        self.assertFalse(self.backend.statusBar)
        self.assertTrue(self.backend.current["modified"])    # time and date inserted
        self.window.setProperty("settingsOpen", True)
        self.app.processEvents()
        self.backend.setFont("DejaVu Sans Mono", 14, "bold")
        self.backend.setTheme("dark")
        self.assertTrue(self.backend.darkMode)
        self.backend.setEol(0, "CRLF")
        self.backend.setEncoding(0, "UTF-8 with BOM")
        self.assertEqual((self.backend.current["eol"], self.backend.current["encoding"]), ("CRLF", "UTF-8 with BOM"))
        self.app.processEvents()
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class TurkishNotepadTests(NotepadTests):
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
