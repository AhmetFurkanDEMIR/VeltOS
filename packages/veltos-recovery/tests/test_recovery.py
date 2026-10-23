"""Checks for VeltOS Automatic Repair (run by dh_auto_test)."""

import configparser
import os
import subprocess
import sys
import tempfile
import unittest
from collections import namedtuple
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG))

from veltos_recovery import repair, strings  # noqa: E402

Result = namedtuple("Result", "returncode stdout stderr")


class FakeRunner:
    """subprocess.run stand-in: records commands, answers from a table."""

    def __init__(self, answers=None):
        self.commands = []
        self.answers = answers or {}

    def __call__(self, command, **_kwargs):
        self.commands.append(command)
        for prefix, answer in self.answers.items():
            if tuple(command[:len(prefix)]) == prefix:
                return Result(*answer)
        return Result(0, "", "")


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.grubenv = Path(tempfile.mkdtemp()) / "grubenv"
        self.grubenv.write_text("# GRUB Environment Block\n")
        repair.GRUBENV = str(self.grubenv)

    def test_restart_clears_the_counter_first(self):
        runner = FakeRunner()
        repair.restart(runner)
        self.assertEqual(runner.commands, [["grub-editenv", str(self.grubenv), "unset", "veltos_failed"],
                                           ["systemctl", "reboot"]])

    def test_safe_mode_starts_the_safe_entry_once(self):
        runner = FakeRunner()
        repair.safe_mode(runner)
        self.assertEqual(runner.commands[1:], [["grub-reboot", "veltos-safe"], ["systemctl", "reboot"]])
        # No restart when GRUB could not be told.
        runner = FakeRunner({("grub-reboot",): (1, "", "no such entry")})
        ok, output = repair.safe_mode(runner)
        self.assertFalse(ok)
        self.assertNotIn(["systemctl", "reboot"], runner.commands)

    def test_startup_repair_steps(self):
        runner = FakeRunner({("update-grub",): (1, "", "grub-probe: error: failed to get canonical path")})
        Usage = namedtuple("Usage", "total used free")
        results = [repair.run_step(i, runner, usage=lambda _p: Usage(10, 9, 5 << 30))
                   for i in range(len(repair.STEPS))]
        self.assertEqual([r[0] for r in results], [True, True, True, True, False, True])
        self.assertIn("failed to get canonical path", results[4][2])
        self.assertEqual(runner.commands, [
            ["dpkg", "--configure", "-a"],
            ["apt-get", "-y", "--no-download", "--fix-broken", "install"],
            ["update-initramfs", "-u", "-k", "all"],
            ["update-grub"],
            ["systemctl", "reset-failed"],
        ])

    def test_makes_room_only_when_the_disk_is_nearly_full(self):
        Usage = namedtuple("Usage", "total used free")
        runner = FakeRunner()
        self.assertEqual(repair.make_room(runner, lambda _p: Usage(10, 9, 5 << 30))[:2], (True, False))
        self.assertEqual(runner.commands, [])
        ok, freed, _output = repair.make_room(runner, lambda _p: Usage(10, 9, 100 << 20))
        self.assertTrue(ok and freed)
        self.assertEqual(runner.commands, [["apt-get", "clean"], ["journalctl", "--vacuum-size=100M"]])

    def test_previous_problems(self):
        one_boot = FakeRunner({("journalctl", "--list-boots"): (0, " 0 abc Thu 2026-10-22\n", "")})
        self.assertEqual(repair.previous_problems(one_boot), "")
        two_boots = FakeRunner({
            ("journalctl", "--list-boots"): (0, "-1 aaa Thu\n 0 bbb Thu\n", ""),
            ("journalctl", "-b", "-1", "-p"): (0, "Oct 22 sddm[800]: Failed to read display number\n", ""),
            ("journalctl", "-b", "-1", "--no-pager", "-q", "-o", "cat"): (0, "Failed to start sddm.service\n", ""),
        })
        text = repair.previous_problems(two_boots)
        self.assertIn("Failed to read display number", text)
        self.assertIn("Failed to start sddm.service", text)

    def test_commands_that_cannot_run_are_reported(self):
        def broken(command, **_kwargs):
            raise FileNotFoundError(2, "No such file or directory", command[0])
        ok, output = repair.run(["update-grub"], broken)
        self.assertFalse(ok)
        self.assertIn("update-grub", output)

    def test_system_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            locale = Path(tmp) / "locale"
            locale.write_text('LANG="tr_TR.UTF-8"\n')
            self.assertEqual(repair.system_language([str(locale)], environ={}), "tr")
            locale.write_text("LANG=en_US.UTF-8\n")
            self.assertEqual(repair.system_language([str(locale)], environ={"LANG": "tr_TR.UTF-8"}), "en")
            self.assertEqual(repair.system_language([str(Path(tmp) / "none")], environ={}), "en")


class TextTests(unittest.TestCase):
    def test_every_text_in_both_languages(self):
        for key, (english, turkish) in strings.TEXTS.items():
            with self.subTest(key=key):
                self.assertTrue(english and turkish)
        for key, _command in repair.STEPS:
            self.assertIn(key, strings.TEXTS)

    def test_qml_names_only_known_texts(self):
        import re
        qml = (PKG / "veltos_recovery/qml/Main.qml").read_text(encoding="utf-8")
        for key in set(re.findall(r'backend\.text\("([a-z_]+)"\)', qml)) | set(re.findall(r'(?:title|desc): "([a-z_]+)"', qml)):
            self.assertIn(key, strings.TEXTS, key)


class SystemFileTests(unittest.TestCase):
    def unit(self, name):
        parser = configparser.ConfigParser(strict=False, interpolation=None)
        parser.optionxform = str
        parser.read_string((PKG / "system" / name).read_text())
        return parser

    def test_scripts_parse(self):
        for name in ("run-recovery", "boot-ok", "boot-failed", "safe-graphics"):
            subprocess.run(["sh", "-n", str(PKG / "system" / name)], check=True)

    def test_safe_graphics_signs_in_on_x11_only_without_a_driver(self):
        # Debian's kernel has no simpledrm: with nomodeset there is no DRM
        # device, Wayland cannot run and Safe mode stayed black (VM,
        # 2026-10-22); X11 runs on the firmware's frame buffer.
        with tempfile.TemporaryDirectory() as tmp:
            cmdline = Path(tmp) / "cmdline"
            conf = Path(tmp) / "sddm.conf.d" / "zz-veltos-safe-graphics.conf"
            env = dict(os.environ, VELTOS_CMDLINE=str(cmdline), VELTOS_SDDM_CONF=str(conf))
            cmdline.write_text("BOOT_IMAGE=/vmlinuz root=UUID=x ro quiet splash nomodeset\n")
            subprocess.run(["sh", str(PKG / "system/safe-graphics")], env=env, check=True)
            self.assertIn("\nDisplayServer=x11\n", conf.read_text())
            cmdline.write_text("BOOT_IMAGE=/vmlinuz root=UUID=x ro quiet splash\n")
            subprocess.run(["sh", str(PKG / "system/safe-graphics")], env=env, check=True)
            self.assertFalse(conf.exists())
        dropin = self.unit("sddm-veltos-recovery.conf")["Unit"]
        self.assertEqual(dropin["Wants"], "veltos-safe-graphics.service")
        self.assertEqual(dropin["After"], "veltos-safe-graphics.service")
        unit = self.unit("veltos-safe-graphics.service")["Unit"]
        self.assertEqual(unit["Before"], "display-manager.service")
        # Plymouth leaves the console in graphics mode; Linux ignores the
        # switch to SDDM's console then (Xorg waited for ever, VM).
        self.assertIn("plymouth-quit.service", unit["After"])
        self.assertIn("0x4B3A", (PKG / "system/safe-graphics").read_text())

    def test_failed_start_restarts_only_normal_starts(self):
        text = (PKG / "system/veltos-boot-failed.service").read_text()
        for option in ("single", "emergency", "rescue", "systemd.unit=emergency.target",
                       "systemd.unit=rescue.target", "systemd.unit=veltos-recovery.target"):
            self.assertIn(f"ConditionKernelCommandLine=!{option}\n", text)
        self.assertIn("ConditionPathExists=/boot/grub/grubenv", text)

    def test_success_does_not_hold_up_the_start(self):
        self.assertEqual(self.unit("veltos-boot-ok.service")["Service"]["Type"], "simple")
        target = self.unit("veltos-recovery.target")["Unit"]
        self.assertIn("display-manager.service", target["Conflicts"])
        self.assertEqual(target["AllowIsolate"], "yes")
        screen = self.unit("veltos-recovery.service")["Service"]
        self.assertEqual(screen["TTYPath"], "/dev/tty1")
        run = (PKG / "system/run-recovery").read_text()
        self.assertIn("export QT_QPA_PLATFORM=linuxfb", run)

    def test_boot_ok_needs_the_sign_in_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp)
            log = bin_dir / "log"
            (bin_dir / "systemctl").write_text(f"#!/bin/sh\necho systemctl \"$@\" >> '{log}'\nexit $STATE\n")
            (bin_dir / "grub-editenv").write_text(f"#!/bin/sh\necho grub-editenv \"$@\" >> '{log}'\n")
            for tool in ("systemctl", "grub-editenv"):
                (bin_dir / tool).chmod(0o755)
            env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "VELTOS_OK_DELAY": "0"}
            subprocess.run(["sh", str(PKG / "system/boot-ok")], env=dict(env, STATE="3"), check=True)
            self.assertNotIn("grub-editenv", log.read_text())
            subprocess.run(["sh", str(PKG / "system/boot-ok")], env=dict(env, STATE="0"), check=True)
            self.assertIn("grub-editenv /boot/grub/grubenv unset veltos_failed", log.read_text())


@unittest.skipUnless(os.environ.get("DISPLAY") or sys.platform.startswith("linux"), "needs Qt")
class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        os.environ["QT_QUICK_BACKEND"] = "software"
        from PySide6.QtGui import QGuiApplication
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def load_window(self, backend):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        # Imported so that the root object comes back as a QQuickWindow
        # (with contentItem()), not as a plain QWindow.
        from PySide6.QtQuick import QQuickWindow  # noqa: F401
        from veltos_recovery import app as app_module
        # The logo is installed with the package, not present at build time.
        app_module.LOGO = str(PKG / "branding/veltos-logo.svg")
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(app_module.QML)))
        self.assertTrue(engine.rootObjects())
        return engine, engine.rootObjects()[0]

    @staticmethod
    def find_item(item, name):
        """An item by objectName in the visual tree (QML items declared in
        a Window are not QObject children of its content item)."""
        if item.objectName() == name:
            return item
        for child in item.childItems():
            found = WindowTests.find_item(child, name)
            if found is not None:
                return found
        return None

    @staticmethod
    def close_window(engine):
        # Delete the engine while the backend still exists: deleted later,
        # its bindings read a dead backend ("Cannot call method 'text' of
        # null" after the tests).
        from PySide6.QtCore import QCoreApplication, QEvent
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_window_loads_without_warnings(self):
        from PySide6.QtCore import qInstallMessageHandler
        from veltos_recovery import app as app_module

        problems = []

        def handler(_mode, _context, message):
            problems.append(message)
        previous = qInstallMessageHandler(handler)
        backend = app_module.Backend(lang="tr", runner=FakeRunner(), threaded=False)
        try:
            engine, window = self.load_window(backend)
            self.app.processEvents()
            self.assertEqual(window.property("page"), "home")
            window.setProperty("page", "options")
            self.app.processEvents()
            window.setProperty("page", "repair")
            self.app.processEvents()
            self.close_window(engine)
        finally:
            qInstallMessageHandler(previous)
        self.assertEqual([p for p in problems if "qml" in p.lower() or "Unable" in p], [])

    def test_options_fit_small_screens(self):
        # Without a graphics driver the screen is the firmware's frame buffer,
        # often 1024x768 or 800x600: in one column the six tiles ran under
        # the Back button and off the screen (VM, 2026-10-22).
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QWindow
        from veltos_recovery import app as app_module
        backend = app_module.Backend(lang="tr", runner=FakeRunner(), threaded=False)
        engine, window = self.load_window(backend)
        window.setVisibility(QWindow.Visibility.Windowed)
        window.setProperty("page", "options")
        grid = self.find_item(window.contentItem(), "tileGrid")
        back = self.find_item(window.contentItem(), "backButton")
        self.assertIsNotNone(grid)
        self.assertIsNotNone(back)
        for width, height in ((1024, 768), (800, 600)):
            with self.subTest(size=f"{width}x{height}"):
                window.resize(width, height)
                self.app.processEvents()
                window.grabWindow()                # lays the page out
                self.assertEqual(grid.property("columns"), 2)
                bottom_right = grid.mapToScene(QPointF(grid.width(), grid.height()))
                back_top = back.mapToScene(QPointF(0, 0)).y()
                self.assertLessEqual(bottom_right.x(), width)
                self.assertLessEqual(bottom_right.y(), back_top)
                self.assertLessEqual(back_top + back.height(), height)
        self.close_window(engine)

    def test_command_prompt_ends_the_window_for_a_console_sign_in(self):
        # Linux ignores console switches while the window's console is in
        # graphics mode, so the window ends for the sign-in and run-recovery
        # starts it again afterwards (VM, 2026-10-22: a terminal opened next
        # to the window never appeared).
        from veltos_recovery import app as app_module
        codes = []
        with tempfile.TemporaryDirectory() as tmp:
            app_module.TERMINAL_HINT = str(Path(tmp) / "terminal-hint")
            backend = app_module.Backend(lang="tr", runner=FakeRunner(), threaded=False, quit=codes.append)
            backend.openTerminal()
            self.assertEqual(codes, [app_module.TERMINAL_EXIT])
            self.assertTrue(backend.terminalOpen)
            self.assertIn("exit", Path(app_module.TERMINAL_HINT).read_text(encoding="utf-8"))
        script = (PKG / "system/run-recovery").read_text(encoding="utf-8")
        self.assertIn(f'[ "$status" -eq {app_module.TERMINAL_EXIT} ]', script)
        self.assertIn("openvt -s -w --", script)
        self.assertIn("setupcon --current-tty", script)     # "ı" and "İ" on the console
        self.assertIn("/run/veltos-recovery/terminal-hint", script)
        self.assertIn("options=--options", script)
        self.assertNotIn("exec /usr/bin/veltos-recovery", script)

    def test_repair_reports_every_step(self):
        from veltos_recovery import app as app_module
        backend = app_module.Backend(lang="en", runner=FakeRunner(), threaded=False)
        events = []
        backend.stepChanged.connect(lambda i, state, _out: events.append((i, state)))
        finished = []
        backend.repairFinished.connect(finished.append)
        backend.startRepair()
        steps = len(repair.STEPS)
        self.assertEqual([e for e in events if e[1] != "running"], [(i, "ok") for i in range(steps)])
        self.assertEqual(finished, [True])
        self.assertFalse(backend.busy)


if __name__ == "__main__":
    unittest.main()
