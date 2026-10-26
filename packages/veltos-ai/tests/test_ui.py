"""Loads the real VeltOS AI pane and window offscreen: the settings view
without a key, the greeting, a conversation with an action that waits for
"Allow", the settings view again, the local model's settings with the
download screen, and the window (Start, search). Any QML warning fails the
test."""

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
    import PySide6.QtQuick  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

import fakeservice as fake  # noqa: E402


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class PaneTests(unittest.TestCase):
    lang = "en"

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def setUp(self):
        self.messages.clear()

    def load(self, provider="", *answers, qml="Main.qml"):
        from veltos_ai import app, config
        folder = Path(tempfile.mkdtemp())
        file = folder / "ai.json"
        self.old_data = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = str(folder / "data")
        data = config.load(file)
        if provider:
            data["provider"] = provider
            data["services"][provider]["key"] = "test-key"
        config.save(data, file)
        self.backend = app.Backend(lang=self.lang, opener=fake.FakeService(*answers), settings_file=file,
                                   threaded=False, starter=lambda command: None)
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / qml)))
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.window.show()
        self.settle()

    def tearDown(self):
        if self.old_data is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = self.old_data
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def settle(self):
        for _ in range(5):
            self.app.processEvents()
        self.window.grabWindow()

    def find(self, name):
        return self.window.findChild(QObject, name)

    def problems(self):
        # Offscreen there is no Wayland: the layer shell says so and does
        # nothing (as on X11).
        return [m for m in self.messages if ("qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower() or "binding loop" in m.lower())
                and "not a wayland window" not in m]

    def test_no_key_shows_settings(self):
        self.load()
        self.assertTrue(self.find("settingsView").property("visible"))
        self.assertFalse(self.find("composer").property("visible"))
        self.assertEqual(self.problems(), [])

    def test_conversation_with_an_action(self):
        self.load("claude", fake.claude_tool_turn(), fake.claude_text("**Done.** Wi-Fi is on."))
        self.assertTrue(self.find("greeting").property("visible"))
        self.assertTrue(self.find("composer").property("visible"))
        from veltos_ai import tools
        from types import SimpleNamespace

        class Network:
            def __init__(self, run):
                pass

            def set_wifi(self, on):
                return True
        old = tools.settings_helpers
        tools.settings_helpers = lambda: SimpleNamespace(Network=Network)
        try:
            self.backend.send("Turn on Wi-Fi")
            self.settle()
            self.assertEqual(self.find("messages").property("count"), 3)
            action = [m for m in self.backend.messages if m["kind"] == "action"][0]
            self.backend.allowAction(action["id"])
            self.settle()
        finally:
            tools.settings_helpers = old
        self.assertEqual(self.find("messages").property("count"), 4)
        self.find("assistant").setProperty("settingsOpen", True)
        self.settle()
        self.assertTrue(self.find("settingsView").property("visible"))
        self.window.setProperty("width", 360)
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_local_model_settings_and_download_screen(self):
        self.load()
        self.assertTrue(self.find("localModels").property("visible"))      # local is the first choice
        self.assertFalse(self.find("keyField").property("visible"))
        self.assertTrue(self.find("defaultModel").property("visible"))
        self.assertFalse(self.find("downloadCard").property("visible"))
        self.backend._download.update(active=True, file="m.gguf", title="Gemma", done=50_000_000,
                                      total=184_517_664, speed=2e6)
        self.backend.downloadChanged.emit()
        self.settle()
        self.assertTrue(self.find("downloadCard").property("visible"))
        self.assertEqual(self.backend.download["percent"], 27)
        self.backend._on_hub("results", [{"repo": "a/b-GGUF", "downloads": 3, "likes": 0}], "")
        self.backend._on_hub("files", [{"file": "b-Q4.gguf", "size": 200_000_000, "sha256": ""}], "")
        self.backend._hub["repo"] = "a/b-GGUF"
        self.backend.hubChanged.emit()
        self.settle()
        self.assertEqual(self.problems(), [])

    def test_window(self):
        self.load("claude", qml="AppWindow.qml")
        self.assertEqual(self.window.objectName(), "appWindow")
        self.assertTrue(self.find("composer").property("visible"))
        self.assertFalse(self.find("assistant").property("docked"))
        self.assertEqual(self.problems(), [])


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class TurkishPaneTests(PaneTests):
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
