"""Loads the real Disk Management window offscreen with recorded disks:
the volume list and the disk map, the right-click menu, every dialog, and
Windows 11's Format window (from Disk Management and on its own, as File
Explorer opens it). Any QML warning or error fails the test."""

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
    from PySide6.QtCore import Q_ARG, QCoreApplication, QEvent, QMetaObject, QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from test_disks import BLOCKS, fake_statvfs, sample_objects  # noqa: E402


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
        from veltos_disks import app
        self.calls = []
        self.backend = app.Backend(lang=self.lang, reader=sample_objects,
                                   runner=lambda command: (self.calls.append(command), (0, "", ""))[1],
                                   start=lambda command: None, formats=["ntfs", "ext4"], threaded=False,
                                   statvfs=fake_statvfs)
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

    def call(self, name, *args):
        QMetaObject.invokeMethod(self.window, name, *[Q_ARG("QVariant", a) for a in args])
        self.app.processEvents()

    def problems(self):
        return [m for m in self.messages if "qml" in m.lower() or "error" in m.lower()
                or "undefined" in m.lower() or "warning" in m.lower()]

    def test_window_lists_volumes_and_disks(self):
        self.window.setProperty("width", 1100)
        self.window.setProperty("height", 760)
        self.app.processEvents()
        self.assertEqual(len(self.backend.volumes), 3)
        self.assertEqual(len(self.backend.disks), 4)
        self.backend.refresh()
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_menu_and_dialogs(self):
        dialog = self.window.findChild(QObject, "formDialog")
        self.assertTrue(self.call("selectVolume", BLOCKS + "sdb1") is None)
        self.assertEqual(self.window.property("selectedKey"), BLOCKS + "sdb1")
        self.call("menuForSelected")
        for action in ("label", "delete", "properties"):
            self.call("run", action)
            self.assertTrue(dialog.property("visible"), action)
            QMetaObject.invokeMethod(dialog, "close")
            self.app.processEvents()
        self.call("selectUnallocated", BLOCKS + "sda")
        self.call("menuForSelected")
        self.call("run", "new")
        self.assertTrue(dialog.property("visible"))
        # OK on the New Simple Volume dialog makes the partition.
        QMetaObject.invokeMethod(dialog.findChild(QObject, "acceptButton"), "clicked")
        self.app.processEvents()
        self.assertEqual(self.calls[-1][7], "CreatePartitionAndFormat")
        self.call("selectDisk", BLOCKS + "sr0")
        self.call("menuForSelected")
        self.call("run", "properties")
        self.assertTrue(dialog.property("visible"))
        QMetaObject.invokeMethod(dialog, "close")
        self.app.processEvents()
        # A blank disk offers Initialize Disk (GPT by default); OK writes the table.
        from PySide6.QtCore import Q_RETURN_ARG
        self.call("selectDisk", BLOCKS + "vda")
        texts = QMetaObject.invokeMethod(self.window, "menuTexts", Q_RETURN_ARG("QVariant"))
        self.assertEqual(texts, self.backend.texts["initialize"] + "|" + self.backend.texts["properties"])
        self.call("selectVolume", BLOCKS + "sdb1")
        texts = QMetaObject.invokeMethod(self.window, "menuTexts", Q_RETURN_ARG("QVariant"))
        self.assertIn(self.backend.texts["format"] + "|" + self.backend.texts["delete_volume"], texts)
        self.assertIn("|" + self.backend.texts["mount"] + "|", texts)          # not mounted: Mount, enabled
        self.assertNotIn(self.backend.texts["unmount"], texts)
        self.assertNotIn("(off)", texts.split("|")[3])
        self.call("selectVolume", BLOCKS + "sda2")                            # the system volume
        texts = QMetaObject.invokeMethod(self.window, "menuTexts", Q_RETURN_ARG("QVariant"))
        self.assertIn(self.backend.texts["format"] + " (off)|" + self.backend.texts["delete_volume"] + " (off)", texts)
        self.call("selectDisk", BLOCKS + "vda")
        self.call("run", "initialize")
        self.assertTrue(dialog.property("visible"))
        QMetaObject.invokeMethod(dialog.findChild(QObject, "acceptButton"), "clicked")
        self.app.processEvents()
        self.assertEqual(self.calls[-1][7:10], ["Format", "sa{sv}", "gpt"])
        # The selection survives a refresh (the disks are read again).
        self.backend.refresh()
        self.app.processEvents()
        self.assertEqual(self.window.property("selectedKey"), "disk:" + BLOCKS + "vda")
        self.assertEqual(self.problems(), [])

    def format_window(self, window):
        """Start, confirm and wait for the (synchronous) format."""
        self.assertEqual(window.objectName(), "formatWindow")
        self.assertTrue(window.property("visible"))
        self.assertEqual(window.property("phase"), "ready")
        self.assertEqual(window.property("fs"), "ntfs")
        QMetaObject.invokeMethod(window, "start")
        self.app.processEvents()
        self.assertEqual(window.property("phase"), "confirm")
        window.setProperty("label", "Backup")
        QMetaObject.invokeMethod(window, "confirm")
        self.app.processEvents()
        self.assertEqual(window.property("phase"), "done")
        command = self.calls[-1]
        self.assertIn("Format", command)
        self.assertIn("ntfs", command)
        return command

    def test_format_window_from_disk_management(self):
        from PySide6.QtCore import Q_RETURN_ARG
        self.call("selectVolume", BLOCKS + "sdb1")
        window = QMetaObject.invokeMethod(self.window, "openFormat", Q_RETURN_ARG("QVariant"))
        self.app.processEvents()
        self.assertEqual(window.property("title"), self.backend.texts["format_title"].replace("{name}", "USB"))
        self.format_window(window)
        QMetaObject.invokeMethod(window, "close")
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_format_window_on_its_own(self):
        from veltos_disks import app
        volume = next(v for v in self.backend.volumes if v["device"] == "/dev/sdb1")
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("backend", self.backend)
        engine.setInitialProperties({"volume": volume})
        engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "FormatWindow.qml")))
        self.assertTrue(engine.rootObjects(), self.messages)
        window = engine.rootObjects()[0]
        window.show()
        self.app.processEvents()
        self.format_window(window)
        # Not formatable: the window says so and Start does nothing.
        engine.setInitialProperties({"volume": None})
        engine.load(QUrl.fromLocalFile(str(app.QML_DIR / "FormatWindow.qml")))
        blocked = engine.rootObjects()[-1]
        self.assertEqual(blocked.property("phase"), "unavailable")
        calls = len(self.calls)
        QMetaObject.invokeMethod(blocked, "start")
        self.app.processEvents()
        self.assertEqual(len(self.calls), calls)
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertEqual(self.problems(), [])

    def test_format_command_selects_only_a_formatable_volume(self):
        from veltos_disks import app
        from PySide6.QtCore import Q_RETURN_ARG
        args = app.parse_args(["veltos-disks", "--format", "/dev/sdb1"])
        self.assertEqual(args.format_device, "/dev/sdb1")

        dialog = self.window.findChild(QObject, "formDialog")
        opened = QMetaObject.invokeMethod(self.window, "openFormatForDevice", Q_RETURN_ARG("QVariant"),
                                          Q_ARG("QVariant", "/dev/sdb1"))
        self.assertTrue(opened)
        self.assertFalse(dialog.property("visible"))            # a window of its own
        self.assertEqual(self.window.property("selectedKey"), BLOCKS + "sdb1")

        blocked = QMetaObject.invokeMethod(self.window, "openFormatForDevice", Q_RETURN_ARG("QVariant"),
                                           Q_ARG("QVariant", "/dev/sda2"))
        self.assertFalse(blocked)
        self.assertTrue(dialog.property("visible"))
        self.assertEqual(dialog.property("message"), self.backend.texts["format_unavailable"])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.problems(), [])


class TurkishWindowTests(WindowTests):
    lang = "tr"

    def test_turkish_title(self):
        self.assertEqual(self.window.property("title"), "Disk Yönetimi")
        self.assertEqual(self.problems(), [])


if __name__ == "__main__":
    unittest.main()
