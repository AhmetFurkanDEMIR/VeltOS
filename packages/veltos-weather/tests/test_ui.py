"""Loads the real Weather window offscreen on the saved answers (no network):
every page, the chart kinds, a day, search, favorites, units, offline.
Any QML warning fails the test. The Turkish class runs in the Turkish
locale when it is installed."""

import json
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
os.environ["QML_DISABLE_DISK_CACHE"] = "1"

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401  (root objects as QQuickWindow)
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from fakenet import FakeNet  # noqa: E402


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WeatherWindowTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.home = Path(tempfile.mkdtemp())
        os.environ["XDG_CONFIG_HOME"] = str(cls.home / ".config")
        os.environ["XDG_CACHE_HOME"] = str(cls.home / ".cache")
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        self.messages.clear()

    def load(self, online=True, settings=None):
        from veltos_weather import app, openmeteo
        folder = Path(tempfile.mkdtemp())
        settings_file = folder / "weather.json"
        settings_file.write_text(json.dumps(settings or {"unit": "C"}), encoding="utf-8")
        self.net = FakeNet(online)
        self.backend = app.Backend(lang=self.lang, opener=self.net, cache=openmeteo.Cache(folder / "cache"),
                                   settings_file=settings_file, zone="Europe/Istanbul", threaded=False)
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.backend.start()
        self.settle()

    def tearDown(self):
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def settle(self):
        for _ in range(5):
            self.app.processEvents()
        self.window.grabWindow()          # lays the window out and paints the canvases

    def find(self, name):
        return self.window.findChild(QObject, name)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower() or "binding loop" in m.lower()]

    def test_forecast_page(self):
        self.load()
        self.assertEqual(self.find("placeName").property("text"), "İstanbul")
        self.assertEqual(self.find("temperature").property("text"), "14")
        self.assertEqual(self.find("days").property("count"), 10)
        self.assertGreater(self.find("hero").property("height"), 200)
        self.assertTrue(self.find("details").property("visible"))
        for kind in ("precipitation", "wind", "humidity", "uv_index", "feels_like", "cloud_cover", "pressure",
                     "visibility", "overview"):
            self.backend.setChartKind(kind)
            self.settle()
        for day in (3, 9, 0):
            self.backend.selectDay(day)
            self.settle()
        self.window.setProperty("width", 760)            # narrow: one column of details
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_other_pages_search_and_units(self):
        self.load()
        for page in ("history", "favorites", "settings", "forecast"):
            self.backend.setPage(page)
            self.settle()
        self.assertTrue(self.find("historyPage") is not None)
        self.backend.search("ist")
        self.settle()
        self.backend.choosePlace(0)
        self.backend.toggleFavorite()
        self.backend.setPage("favorites")
        self.settle()
        self.backend.setUnit("F")
        self.settle()
        self.backend.setPage("forecast")
        self.settle()
        self.assertEqual(self.find("temperature").property("text"), "57")
        self.assertEqual(self.problems(), [])

    def test_offline_first_start(self):
        self.load(online=False)
        self.assertTrue(self.find("firstPlace").property("visible"))
        self.assertTrue(self.find("offlineBar").property("visible"))
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class TurkishWeatherWindowTests(WeatherWindowTests):
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
