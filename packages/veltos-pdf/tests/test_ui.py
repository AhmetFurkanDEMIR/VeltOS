"""Makes real PDF files (QPdfWriter) and loads them in the PDF Reader window
offscreen: tabs, recent files, pages, search, thumbnails, bookmarks panel,
properties; a damaged file is refused. Any QML warning fails the test. The
Turkish class runs in the Turkish C locale when it is installed."""

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
    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QSettings, QUrl, Q_ARG, qInstallMessageHandler
    from PySide6.QtGui import QPageSize, QPainter, QPdfWriter
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtWidgets import QApplication
    from PySide6.QtPdf import QPdfDocument  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def make_pdf(path, pages=3, words="VeltOS"):
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setTitle("Sample document")
    painter = QPainter(writer)
    for n in range(pages):
        if n:
            writer.newPage()
        painter.drawText(200, 400, f"Page {n + 1}: {words} reader test")
    painter.end()


@unittest.skipUnless(HAVE_QT, "needs PySide6 with QtPdf (Build-Depends)")
class PdfTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        home = Path(tempfile.mkdtemp())
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
        cls.home = home
        cls.app = QApplication.instance() or QApplication([])
        make_pdf(home / "report.pdf", 3)
        make_pdf(home / "notes.pdf", 1, "notes")
        (home / "broken.pdf").write_bytes(b"%PDF-1.4 this is not a real document")
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_pdf import app
        self.messages.clear()
        settings = QSettings(str(self.home / f"{self.id()}.conf"), QSettings.Format.IniFormat)
        self.backend = app.Backend(lang=self.lang, settings=settings)
        self.engine = QQmlApplicationEngine()
        self.engine.addImageProvider("icon", app.IconProvider())
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.settle()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.notices = []
        self.backend.message.connect(self.notices.append)

    def tearDown(self):
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def settle(self, rounds=30):
        for _ in range(rounds):
            self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_open_tabs_and_recent(self):
        self.backend.openPaths([str(self.home / "report.pdf"), str(self.home / "notes.pdf")])
        self.settle()
        self.assertEqual([t["title"] for t in self.backend.tabs], ["report.pdf", "notes.pdf"])
        self.assertEqual(self.backend.currentIndex, 2)
        self.backend.openPaths([str(self.home / "report.pdf")])        # already open: shown
        self.assertEqual(self.backend.currentIndex, 1)
        view = self.window.property("currentView")
        self.assertIsNotNone(view)
        self.assertEqual(view.property("pageCount"), 3)
        self.assertEqual([r["name"] for r in self.backend.recent], ["notes.pdf", "report.pdf"])
        self.backend.closeTab(1)
        self.assertEqual([t["title"] for t in self.backend.tabs], ["notes.pdf"])
        self.backend.forget(str(self.home / "notes.pdf"))
        self.assertEqual([r["name"] for r in self.backend.recent], ["report.pdf"])
        self.assertEqual(self.problems(), [])

    def test_panels_search_and_properties(self):
        self.backend.openPaths([str(self.home / "report.pdf")])
        self.settle()
        view = self.window.property("currentView")
        for panel in ("thumbnails", "bookmarks", "search", ""):
            view.setProperty("panel", panel)
            self.settle()
        QMetaObject.invokeMethod(view, "zoomBy", Q_ARG("QVariant", 1.2))
        QMetaObject.invokeMethod(view, "fitPage")
        QMetaObject.invokeMethod(self.window, "run", Q_ARG("QVariant", "properties"))
        QMetaObject.invokeMethod(self.window, "run", Q_ARG("QVariant", "read-mode"))
        self.settle()
        self.assertTrue(self.window.property("readMode"))
        self.assertEqual(self.backend.pageSizeText(595.28, 841.89), "210 x 297 mm (A4)")
        self.assertEqual(self.problems(), [])

    def test_damaged_file_is_refused(self):
        self.backend.openPaths([str(self.home / "broken.pdf")])
        self.settle()
        self.assertEqual(self.backend.tabs, [])
        self.assertEqual(len(self.notices), 1)
        self.assertIn("broken.pdf", self.notices[0])


@unittest.skipUnless(HAVE_QT, "needs PySide6 with QtPdf (Build-Depends)")
class TurkishPdfTests(PdfTests):
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


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class HandOverTests(unittest.TestCase):
    def test_token_travels_with_the_files(self):
        # A second start hands its files and its activation token to the
        # running window, which needs the token to come to the front.
        from veltos_pdf import app as program
        self.assertEqual(program.handed_over({"paths": ["/a.txt"], "token": "kwin-3"}), (["/a.txt"], "kwin-3"))
        self.assertEqual(program.handed_over(["/a.txt"]), (["/a.txt"], ""))      # older starts


if __name__ == "__main__":
    unittest.main()
