"""Keyboard Lighting with a made-up /sys/class/leds: a ThinkPad (brightness
only), ASUS (asus-wmi kbd_rgb_mode), System76 (color) and a multicolour
LED; the helper's checks and writes, the sign-in restore and the window
offscreen in English and Turkish. Nothing touches the real hardware."""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from veltos_lighting import config, helper, leds  # noqa: E402

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def make_leds():
    root = Path(tempfile.mkdtemp())

    def led(name, maximum, brightness, **files):
        folder = root / name
        folder.mkdir()
        (folder / "max_brightness").write_text(f"{maximum}\n")
        (folder / "brightness").write_text(f"{brightness}\n")
        for key, value in files.items():
            (folder / key).write_text(value + "\n")
    led("tpacpi::kbd_backlight", 2, 1)
    led("asus::kbd_backlight", 3, 0, kbd_rgb_mode="", kbd_rgb_mode_index="cmd mode red green blue speed")
    led("system76_acpi::kbd_backlight", 255, 128, color="FF0000")
    led("rgb:kbd_backlight", 100, 50, multi_index="red green blue", multi_intensity="0 128 255")
    led("input3::capslock", 1, 0)
    return root


class LedTests(unittest.TestCase):
    def setUp(self):
        self.root = make_leds()

    def test_keyboards_and_their_colours(self):
        found = {k["id"]: k for k in leds.keyboards(self.root)}
        self.assertEqual(sorted(found), ["asus::kbd_backlight", "rgb:kbd_backlight", "system76_acpi::kbd_backlight",
                                         "tpacpi::kbd_backlight"])
        self.assertEqual((found["tpacpi::kbd_backlight"]["maker"], found["tpacpi::kbd_backlight"]["colorKind"]),
                         ("Lenovo ThinkPad", ""))
        self.assertEqual(found["asus::kbd_backlight"]["effects"], ["static", "breathing", "cycle"])
        self.assertEqual(found["system76_acpi::kbd_backlight"]["color"], "#FF0000")
        self.assertEqual(found["rgb:kbd_backlight"]["color"], "#0080FF")
        self.assertEqual(leds.keyboards(self.root / "missing"), [])

    def test_what_is_written(self):
        asus = self.root / "asus::kbd_backlight"
        self.assertEqual(leds.writes(asus, "asus", 3, "#FF8000", "breathing", 2),
                         [(asus / "kbd_rgb_mode", "1 1 255 128 0 2"), (asus / "brightness", "3")])
        s76 = self.root / "system76_acpi::kbd_backlight"
        self.assertEqual(leds.writes(s76, "system76", 999, "#00ff00"),
                         [(s76 / "color", "00FF00"), (s76 / "brightness", "255")])
        rgb = self.root / "rgb:kbd_backlight"
        self.assertEqual(leds.writes(rgb, "multicolor", None, "#102030"), [(rgb / "multi_intensity", "16 32 48")])

    def test_helper_writes_only_keyboard_lights(self):
        self.assertEqual(helper.main(["asus::kbd_backlight", "--brightness", "2", "--color", "#00FF00"], self.root), 0)
        self.assertEqual((self.root / "asus::kbd_backlight/kbd_rgb_mode").read_text(), "1 0 0 255 0 1\n")
        self.assertEqual((self.root / "asus::kbd_backlight/brightness").read_text(), "2\n")
        for bad in (["input3::capslock", "--brightness", "1"], ["../etc", "--brightness", "1"],
                    ["tpacpi::kbd_backlight", "--color", "red; reboot"]):
            with self.subTest(bad=bad):
                self.assertEqual(helper.main(bad, self.root), 2)
        self.assertEqual((self.root / "input3::capslock/brightness").read_text(), "0\n")

    def test_restore_at_sign_in(self):
        settings = Path(tempfile.mkdtemp()) / "lighting.json"
        settings.write_text(json.dumps({
            "asus::kbd_backlight": {"on": True, "brightness": 100, "color": "#FF0000", "effect": "cycle", "speed": 2,
                                    "matchAccent": True},
            "tpacpi::kbd_backlight": {"on": False, "brightness": 50}}))
        commands = []
        self.assertTrue(config.restore(self.root, lambda c: commands.append(c) or 0, settings, accent_color="#2F5EE6"))
        self.assertEqual(commands, [
            ["pkexec", config.HELPER, "asus::kbd_backlight", "--brightness", "3", "--color", "#2F5EE6",
             "--effect", "cycle", "--speed", "2"],
            ["pkexec", config.HELPER, "tpacpi::kbd_backlight", "--brightness", "0"]])
        # Nothing saved, or no keyboard light: nothing runs.
        self.assertTrue(config.restore(self.root / "none", lambda c: 1, settings))


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

    def open(self, root):
        from veltos_lighting import app
        self.commands = []
        self.settings = Path(tempfile.mkdtemp()) / "lighting.json"
        backend = app.Backend(lang=self.lang, root=root, runner=lambda c: self.commands.append(c) or 0,
                              settings=self.settings, apply_delay=1, accent_color="#2F5EE6")
        # The window reads the backend until it is deleted at the test's end.
        self.addCleanup(lambda kept=backend: kept)
        self.messages.clear()
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "Main.qml")))
        self.assertTrue(engine.rootObjects(), self.messages)
        self.addCleanup(self.dispose, engine)
        window = engine.rootObjects()[0]
        window.grabWindow()
        return backend, window

    def dispose(self, engine):
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower() or "warning" in m.lower()
                or "undefined" in m.lower()]

    def settle(self):
        for _ in range(10):
            self.app.processEvents()
            time.sleep(0.01)

    def test_colour_keyboard(self):
        backend, window = self.open(make_leds())
        backend.select(0)                          # asus::kbd_backlight
        self.assertEqual(backend.keyboard["id"], "asus::kbd_backlight")
        backend.setColor("#ff3b30")
        backend.setEffect("breathing")
        backend.setBrightness(66)
        self.settle()
        self.assertEqual(self.commands[-1], ["pkexec", config.HELPER, "asus::kbd_backlight", "--brightness", "2",
                                             "--color", "#FF3B30", "--effect", "breathing", "--speed", "1"])
        backend.setMatchAccent(True)
        self.settle()
        self.assertIn("#2F5EE6", self.commands[-1])
        backend.setOn(False)
        self.settle()
        self.assertEqual(self.commands[-1][3:5], ["--brightness", "0"])
        saved = json.loads(self.settings.read_text())
        self.assertEqual(saved["asus::kbd_backlight"]["effect"], "breathing")
        window.grabWindow()
        self.assertEqual(self.problems(), [])

    def test_one_colour_keyboard_and_none(self):
        root = Path(tempfile.mkdtemp())
        folder = root / "tpacpi::kbd_backlight"
        folder.mkdir()
        (folder / "max_brightness").write_text("2\n")
        (folder / "brightness").write_text("2\n")
        backend, window = self.open(root)
        self.assertEqual(backend.choice["brightness"], 100)
        backend.setBrightness(40)
        self.settle()
        self.assertEqual(self.commands[-1], ["pkexec", config.HELPER, "tpacpi::kbd_backlight", "--brightness", "1"])
        backend, window = self.open(Path(tempfile.mkdtemp()))
        self.assertEqual(backend.keyboards, [])
        window.grabWindow()
        self.assertEqual(self.problems(), [])


class TurkishWindowTests(WindowTests):
    lang = "tr"


if __name__ == "__main__":
    unittest.main()
