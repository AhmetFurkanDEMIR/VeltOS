"""Loads the real VeltOS AI pane offscreen: the settings view without a key,
the greeting, a conversation with an action that waits for "Allow", and
the settings view again. Any QML warning fails the test."""

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

    def load(self, provider="", *answers):
        from veltos_ai import app, config
        file = Path(tempfile.mkdtemp()) / "ai.json"
        data = config.load(file)
        if provider:
            data["provider"] = provider
            data["services"][provider]["key"] = "test-key"
        config.save(data, file)
        self.backend = app.Backend(lang=self.lang, opener=fake.FakeService(*answers), settings_file=file,
                                   threaded=False, starter=lambda command: None)
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.window.show()
        self.settle()

    def tearDown(self):
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
        self.window.setProperty("settingsOpen", True)
        self.settle()
        self.assertTrue(self.find("settingsView").property("visible"))
        self.window.setProperty("width", 360)
        self.settle()
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
