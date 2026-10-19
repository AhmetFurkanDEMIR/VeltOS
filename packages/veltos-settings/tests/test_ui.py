"""Loads the real Settings window offscreen and visits every page.

Any QML warning or JavaScript error fails the test, so broken bindings are
caught at package build time, not by users.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Q_ARG, QMetaObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class SettingsWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()
        os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: cls.messages.append(msg))

    def setUp(self):
        from veltos_settings import app as settings_app
        self.started = []
        self.messages.clear()
        self.backend = settings_app.Backend(
            lang=self.lang, start=lambda command, env=None: self.started.append(command))
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QUrl.fromLocalFile(str(settings_app.QML_DIR / "Main.qml")))
        self.app.processEvents()
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]

    lang = "en"

    def tearDown(self):
        self.engine.deleteLater()
        self.app.processEvents()

    def call(self, name, *args):
        """Call a JavaScript function of the window."""
        QMetaObject.invokeMethod(self.window, name, *[Q_ARG("QVariant", a) for a in args])
        self.app.processEvents()

    def show(self, page, sub=""):
        self.call("showPage", page, sub)

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_every_page_loads(self):
        for page in self.backend.pages:
            self.show(page["id"])
            self.assertEqual(self.window.property("pageId"), page["id"])
        for page, sub in (("system", "about"), ("system", "storage"), ("apps", "windows-apps")):
            self.show(page, sub)
        self.window.setProperty("query", "sound")
        self.app.processEvents()
        self.window.setProperty("query", "nothing matches this")
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_items_open_modules_and_actions(self):
        self.call("activate", {"kcm": "kcm_pulseaudio", "action": "", "page": ""})
        self.call("activate", {"kcm": "", "action": "updates", "page": ""})
        self.call("activate", {"kcm": "", "action": "", "page": "about", "pageId": "system"})
        self.assertEqual(self.started, [["kcmshell6", "kcm_pulseaudio"],
                                        ["plasma-discover", "--mode", "update"]])
        self.assertEqual(self.window.property("subPage"), "about")

    def test_theme_switch_applies_global_theme(self):
        self.backend.setDarkMode(True)
        self.app.processEvents()
        self.assertEqual(self.started[-1], ["plasma-apply-lookandfeel", "--apply", "org.veltos.dark"])
        self.assertTrue(self.backend.darkMode)
        self.assertEqual(self.problems(), [])

    def test_rename_rejects_bad_names(self):
        self.assertFalse(self.backend.renamePc("  "))
        self.assertTrue(self.backend.renamePc("Ofis PC"))
        self.assertEqual(self.started[-1], ["hostnamectl", "set-hostname", "Ofis PC"])


class TurkishWindowTests(SettingsWindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
