"""The Windows 11 "is not responding" window that replaces KWin's helper
(veltos_taskmanager/notresponding.py, qml/NotResponding.qml)."""

import os
import signal
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

try:
    from PySide6.QtCore import QCoreApplication, QEvent, QPointF, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import PySide6.QtQuick  # noqa: F401  (root objects as QQuickWindow)
    from veltos_taskmanager import notresponding
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

KWIN_ARGS = ["--pid", "4242", "--hostname", "localhost", "--windowname", "Untitled — Notepad",
             "--applicationname", "veltos-notepad", "--wid", "kde-handle-123", "--timestamp", "0"]


def desktop_dir():
    directory = Path(tempfile.mkdtemp())
    (directory / "veltos-notepad.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Notepad\nName[tr]=Not Defteri\n"
        "Icon=veltos-notepad\nExec=veltos-notepad\n", encoding="utf-8")
    return directory


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class HelperTests(unittest.TestCase):
    def test_kwin_options(self):
        args = notresponding.parse(KWIN_ARGS + ["--unknown", "x"])
        self.assertEqual((args.pid, args.hostname, args.applicationname, args.wid),
                         ("4242", "localhost", "veltos-notepad", "kde-handle-123"))

    def test_name_and_icon_from_the_desktop_file(self):
        dirs = [desktop_dir()]
        self.assertEqual(notresponding.app_info("veltos-notepad", "en", dirs), ("Notepad", "veltos-notepad"))
        self.assertEqual(notresponding.app_info("veltos-notepad", "tr", dirs), ("Not Defteri", "veltos-notepad"))
        self.assertEqual(notresponding.app_info("unknown", "en", dirs), ("unknown", "application-x-executable"))

    def test_caption_without_the_program_name(self):
        self.assertEqual(notresponding.short_caption("Untitled — Notepad", "Notepad"), "Untitled")
        self.assertEqual(notresponding.short_caption("Page - Firefox", "Firefox"), "Page")

    def test_alive_reads_the_process_state(self):
        proc = Path(tempfile.mkdtemp())
        (proc / "10").mkdir()
        (proc / "10" / "stat").write_text("10 (my (prog)) S 1 2 3")
        (proc / "11").mkdir()
        (proc / "11" / "stat").write_text("11 (zombie) Z 1 2 3")
        self.assertTrue(notresponding.alive(10, proc))
        self.assertFalse(notresponding.alive(11, proc))
        self.assertFalse(notresponding.alive(12, proc))

    def test_drkonqi_note(self):
        proc = Path(tempfile.mkdtemp())
        (proc / "sys/kernel/random").mkdir(parents=True)
        (proc / "sys/kernel/random/boot_id").write_text("aa-bb\n")
        (proc / "55").mkdir()
        (proc / "55" / "exe").symlink_to("/usr/bin/python3.13")
        cache = Path(tempfile.mkdtemp())
        path = notresponding.note_for_drkonqi(55, cache=cache, proc=proc, now=lambda: 12.5)
        self.assertEqual(path, cache / "drkonqi/application-not-responding/python3.13.aabb.55.12500.json")
        self.assertTrue(path.exists())
        self.assertIsNone(notresponding.note_for_drkonqi(56, cache=cache, proc=proc))

    def test_end_program_aborts_first_then_kills(self):
        sent = []
        # Ends on SIGABRT (its crash handler records the hang): no SIGKILL.
        self.assertTrue(notresponding.end_program(7, kill=lambda p, s: sent.append(s),
                                                  is_alive=lambda p: False, sleep=lambda s: None,
                                                  note=lambda p: None))
        self.assertEqual(sent, [signal.SIGABRT])
        sent.clear()
        self.assertTrue(notresponding.end_program(7, kill=lambda p, s: sent.append(s),
                                                  is_alive=lambda p: True, sleep=lambda s: None,
                                                  note=lambda p: None))
        self.assertEqual(sent, [signal.SIGABRT, signal.SIGKILL])

        def denied(pid, sig):
            raise PermissionError
        self.assertFalse(notresponding.end_program(7, kill=denied, is_alive=lambda p: True,
                                                   sleep=lambda s: None, note=lambda p: None))

    def test_other_hosts_go_to_kdes_helper(self):
        called = []
        args = list(KWIN_ARGS)
        args[3] = "otherhost"
        notresponding.main(args, run_kde_helper=called.append)
        self.assertEqual(called, [args])
        notresponding.main(["--pid", "0"], run_kde_helper=called.append)
        self.assertEqual(len(called), 2)


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class WindowTests(unittest.TestCase):
    lang = "en"
    heading = "“Untitled” in Notepad is not responding"
    close_label = "Close the program"

    @classmethod
    def setUpClass(cls):
        os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.messages = []
        qInstallMessageHandler(lambda _t, _c, msg: cls.messages.append(msg))

    @classmethod
    def tearDownClass(cls):
        qInstallMessageHandler(None)

    def load(self, ended):
        self.messages.clear()
        backend = notresponding.Backend(4242, "Untitled — Notepad", "veltos-notepad", lang=self.lang,
                                        dirs=[desktop_dir()], end=lambda pid: ended.append(pid) or True)
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(QUrl.fromLocalFile(str(notresponding.QML)))

        def unload():
            # Delete the window while its backend still exists (AGENTS.md).
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.addCleanup(unload)
        self.assertTrue(engine.rootObjects(), self.messages)
        return backend, engine, engine.rootObjects()[0]

    @staticmethod
    def items(window):
        found, todo = {}, [window.contentItem()]
        while todo:
            item = todo.pop()
            if item.objectName():
                found[item.objectName()] = item
            todo.extend(item.childItems())
        return found

    def test_window(self):
        ended = []
        backend, engine, window = self.load(ended)
        window.grabWindow()
        self.assertEqual(window.title(), backend.appName)
        found = self.items(window)
        self.assertEqual(found["heading"].property("text"), self.heading)
        self.assertEqual(found["closeButton"].property("label"), self.close_label)
        self.assertTrue(found["closeButton"].property("primary"))
        self.assertFalse(found["waitButton"].property("primary"))
        # The buttons and the heading fit the fixed window.
        for name in ("closeButton", "waitButton"):
            button = found[name]
            self.assertLessEqual(button.mapToScene(QPointF(button.width(), 0)).x(), window.width())
            self.assertGreaterEqual(button.mapToScene(QPointF(0, 0)).x(), 0)
        self.assertEqual([m for m in self.messages if "qml" in m.lower() or "warning" in m.lower()], [])
        backend.closeProgram()
        self.assertEqual(ended, [4242])
        self.assertEqual(backend.result, "closed")
        backend.wait()                    # closing the window afterwards
        self.assertEqual(backend.result, "closed")

    def test_wait_leaves_the_program(self):
        ended = []
        backend, engine, window = self.load(ended)
        backend.wait()
        self.assertEqual((ended, backend.result), ([], "wait"))


class TurkishWindowTests(WindowTests):
    lang = "tr"
    heading = "Not Defteri içindeki “Untitled” yanıt vermiyor"
    close_label = "Programı kapat"


if __name__ == "__main__":
    unittest.main()
