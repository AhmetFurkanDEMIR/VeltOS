"""Loads the real Task Manager window offscreen with recorded data and
shows every page; any QML warning fails the test. The Turkish class runs
in the Turkish C locale when it is installed."""

import locale
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

try:
    from PySide6.QtCore import Q_ARG, QCoreApplication, QEvent, QMetaObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from fakepsutil import FakePsutil  # noqa: E402
from test_system import app_index, sample_processes  # noqa: E402


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        from veltos_taskmanager import app, system
        self.ps = sample_processes()
        self.ended = []
        startup_dir = Path(tempfile.mkdtemp())
        (startup_dir / "x.desktop").write_text("[Desktop Entry]\nType=Application\nName=Updates\nExec=x\n")
        self.backend = app.Backend(
            lang=self.lang,
            processes=system.Processes(self.ps, apps=system.AppIndex(dirs=[app_index()], lang=self.lang), uid=1000),
            performance=system.Performance(FakePsutil()),
            startup=system.StartupApps(startup_dir, Path(tempfile.mkdtemp()), self.lang),
            end_task=self.ended.append, start=lambda command: None)
        self.backend.refresh()
        self.messages.clear()
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

    def test_every_page_loads(self):
        for page in ("processes", "performance", "startup", "processes"):
            QMetaObject.invokeMethod(self.window, "showPage", Q_ARG("QVariant", page))
            self.backend.refresh()
            self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_rows_model_has_groups_and_apps(self):
        rows = self.backend.rows.rows()
        headers = [r["title"] for r in rows if r["kind"] == "header"]
        self.assertEqual(len(headers), 3)
        names = [r["name"] for r in rows if r["kind"] == "row"]
        self.assertIn("Firefox", names)

    def test_search_and_end_task(self):
        self.backend.setSearch("fire")
        rows = [r for r in self.backend.rows.rows() if r["kind"] == "row"]
        self.assertEqual([r["name"] for r in rows], ["Firefox"])
        self.backend.endTask(rows[0]["key"])
        self.assertEqual([sorted(p) for p in self.ended], [[1100, 1101]])

    def test_update_in_place(self):
        before = self.backend.rows.rowCount()
        self.ps.procs[1100].cpu = 40.0
        self.backend.refresh()
        self.assertEqual(self.backend.rows.rowCount(), before)
        self.ps.add(1400, 1000, "newproc")
        self.backend.refresh()
        self.assertEqual(self.backend.rows.rowCount(), before + 1)


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
        self.assertEqual(self.backend.texts["app_title"], "Görev Yöneticisi")
        titles = [r["title"] for r in self.backend.rows.rows() if r["kind"] == "header"]
        self.assertTrue(titles[0].startswith("Uygulamalar"))


class RowsModelTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_QT, "needs PySide6")
    def test_sync_inserts_removes_and_updates(self):
        from veltos_taskmanager.model import RowsModel
        model = RowsModel()
        model.sync([{"key": "a"}, {"key": "b"}, {"key": "c"}])
        model.sync([{"key": "a"}, {"key": "c", "x": 1}, {"key": "d"}])
        self.assertEqual([r["key"] for r in model.rows()], ["a", "c", "d"])
        self.assertEqual(model.rows()[1]["x"], 1)
        model.sync([])
        self.assertEqual(model.rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
