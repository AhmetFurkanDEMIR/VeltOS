"""Tests for the live session welcome window and live session settings."""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

loader = importlib.machinery.SourceFileLoader("live_welcome", str(PKG / "welcome/veltos-live-welcome"))
spec = importlib.util.spec_from_loader("live_welcome", loader)
welcome = importlib.util.module_from_spec(spec)
loader.exec_module(welcome)

try:
    from PySide6.QtCore import QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class TextTests(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(welcome.language({"LANG": "tr_TR.UTF-8"}), "tr")
        self.assertEqual(welcome.language({"LANGUAGE": "tr:en", "LANG": "en_US.UTF-8"}), "tr")
        self.assertEqual(welcome.language({"LANG": "en_US.UTF-8"}), "en")
        self.assertEqual(welcome.language({}), "en")

    def test_translations_complete_and_unbranded(self):
        self.assertEqual(set(welcome.TEXTS["en"]), set(welcome.TEXTS["tr"]))
        for texts in welcome.TEXTS.values():
            for value in texts.values():
                self.assertNotIn("debian", value.lower())

    def test_session_language_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            welcome.write_session_language("tr", Path(tmp))
            localerc = Path(tmp, "plasma-localerc").read_text()
            self.assertIn("LANG=tr_TR.UTF-8", localerc)
            self.assertIn("LANGUAGE=tr", localerc)
            self.assertIn("LayoutList=tr", Path(tmp, "kxkbrc").read_text())
            welcome.write_session_language("en", Path(tmp))
            self.assertIn("LayoutList=us", Path(tmp, "kxkbrc").read_text())

    def test_does_nothing_outside_the_live_system(self):
        if welcome.LIVE_MEDIUM.exists():
            self.skipTest("running on a live system")
        self.assertEqual(welcome.main(["veltos-live-welcome"]), 0)


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    def test_window_loads_without_warnings(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        # The logo is installed by veltos-desktop, not present at build time.
        welcome.LOGO = str(PKG / "branding/veltos-logo.svg")
        self.maxDiff = None
        messages = []
        qInstallMessageHandler(lambda _type, _ctx, msg: messages.append(msg))
        keep = []  # backends must outlive their windows, as in the real app
        for lang in ("en", "tr"):
            backend = welcome.welcome_object(welcome.TEXTS[lang])
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("welcome", backend)
            engine.load(QUrl.fromLocalFile(str(welcome.qml_file())))
            app.processEvents()
            self.assertTrue(engine.rootObjects(), messages)
            self.assertEqual(engine.rootObjects()[0].property("title"), "VeltOS")
            keep.append((backend, engine))
        for _backend, engine in keep:
            engine.deleteLater()
        app.processEvents()
        problems = [m for m in messages if "qml" in m.lower() or "error" in m.lower()
                    or "warning" in m.lower() or "undefined" in m.lower()]
        self.assertEqual(problems, [])


class LiveSessionScriptTests(unittest.TestCase):
    SCRIPT = PKG / "data/veltos-live-session.sh"

    def run_script(self, home, medium):
        env = {"HOME": str(home), "PATH": "/usr/bin:/bin", "VELTOS_LIVE_MEDIUM": str(medium)}
        subprocess.run(["sh", "-c", f". {self.SCRIPT}"], env=env, check=True)

    def test_live_session_never_locks_or_sleeps(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, medium = Path(tmp) / "home", Path(tmp) / "medium"
            medium.mkdir()
            self.run_script(home, medium)
            locker = (home / ".config/kscreenlockerrc").read_text()
            self.assertIn("Autolock=false", locker)
            power = (home / ".config/powerdevilrc").read_text()
            for profile in ("AC", "Battery", "LowBattery"):
                self.assertIn(f"[{profile}][SuspendAndShutdown]\nAutoSuspendAction=0", power)
                self.assertIn(f"[{profile}][Display]\nDimDisplayWhenIdle=false", power)

    def test_installed_system_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            self.run_script(home, Path(tmp) / "no-medium")
            self.assertFalse((home / ".config").exists())


if __name__ == "__main__":
    unittest.main()
