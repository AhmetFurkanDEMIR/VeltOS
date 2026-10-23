"""The Properties window (properties.py): what it shows for files, folders,
several items, drives and Recycle Bin items, and the changes it applies
(temporary folders; no KDE needed)."""

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QGuiApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6 (Build-Depends)")
class PropertiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        from veltos_explorer import properties
        self.properties = properties
        self.folder = Path(tempfile.mkdtemp())
        self.data = Path(tempfile.mkdtemp())
        patcher = mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def window(self, *paths, lang="en"):
        started = []
        props = self.properties.Properties([str(p) for p in paths], lang=lang, start=started.append,
                                           threaded=False)
        return props, started

    def test_sizes_and_dates_as_windows_writes_them(self):
        size_text = self.properties.size_text
        self.assertEqual(size_text(1264, "en"), "1.23 KB (1,264 bytes)")
        self.assertEqual(size_text(1264, "tr"), "1,23 KB (1.264 bayt)")
        self.assertEqual(size_text(512, "tr"), "512 bayt")
        self.assertEqual(size_text(3 * 1024 ** 3, "en"), "3.00 GB (3,221,225,472 bytes)")
        moment = 1792672752   # 2026-10-22
        self.assertIn("2026", self.properties.date_text(moment, "en"))
        self.assertIn("Ekim 2026", self.properties.date_text(moment, "tr"))
        self.assertEqual(self.properties.date_text(0, "en"), "")

    def test_paths_urls_and_the_desktop(self):
        resolve = self.properties.resolve
        self.assertEqual(resolve("file:///home/velt/a%20b.txt"), "/home/velt/a b.txt")
        with mock.patch.object(self.properties.places, "user_dirs",
                               return_value=[("DESKTOP", "/home/velt/Masaüstü", "user-desktop")]):
            self.assertEqual(resolve("desktop:/Not.txt"), "/home/velt/Masaüstü/Not.txt")

    def test_a_file(self):
        path = self.folder / "report.txt"
        path.write_bytes(b"x" * 1264)
        props, started = self.window(path)
        info = props.info
        self.assertEqual(info["kind"], "file")
        self.assertEqual(info["name"], "report.txt")
        self.assertEqual(info["location"], str(self.folder))
        self.assertEqual(props.sizeText, "1.23 KB (1,264 bytes)")
        self.assertTrue(props.sizeOnDiskText)
        self.assertEqual(props.title, "report.txt Properties")
        self.assertTrue(info["canChangeMode"])
        self.assertFalse(info["readOnly"])
        props.changeApp()
        self.assertEqual(started[0][-2:], ["--open-with", str(path)])

    def test_rename_read_only_hidden_and_permissions(self):
        path = self.folder / "a.txt"
        path.write_text("a", encoding="utf-8")
        (self.folder / "taken.txt").write_text("b", encoding="utf-8")
        props, _ = self.window(path)
        messages = []
        props.message.connect(messages.append)
        self.assertFalse(props.apply("taken.txt", False, False, props.info["mode"]))
        self.assertEqual(len(messages), 1)
        self.assertFalse(props.apply("x/y", False, False, props.info["mode"]))
        self.assertTrue(props.apply("b.txt", True, False, props.info["mode"]))
        self.assertTrue((self.folder / "b.txt").exists())
        self.assertFalse(os.stat(self.folder / "b.txt").st_mode & stat.S_IWUSR)
        self.assertTrue(props.apply("b.txt", True, True, props.info["mode"]))
        self.assertTrue((self.folder / ".b.txt").exists())
        self.assertEqual(props.info["name"], ".b.txt")
        self.assertTrue(props.apply(".b.txt", False, True, 0o640))
        self.assertEqual(stat.S_IMODE(os.stat(self.folder / ".b.txt").st_mode), 0o640)

    def test_a_folder_counts_what_it_contains(self):
        (self.folder / "sub").mkdir()
        (self.folder / "sub" / "one.txt").write_bytes(b"1" * 10)
        (self.folder / "two.txt").write_bytes(b"2" * 20)
        props, _ = self.window(self.folder, lang="tr")
        self.assertEqual(props.info["kind"], "folder")
        self.assertEqual(props.containsText, "2 Dosya, 1 Klasör")
        self.assertEqual(props.sizeText, "30 bayt")
        self.assertFalse(props.counting)

    def test_several_items(self):
        for name in ("a.txt", "b.txt"):
            (self.folder / name).write_text("x", encoding="utf-8")
        props, _ = self.window(self.folder / "a.txt", self.folder / "b.txt")
        self.assertEqual(props.info["kind"], "multiple")
        self.assertEqual(props.info["location"], f"All in {self.folder}")
        self.assertEqual(props.containsText, "2 Files, 0 Folders")
        self.assertTrue(props.apply("", False, True, props.info["mode"]))
        self.assertTrue((self.folder / ".a.txt").exists() and (self.folder / ".b.txt").exists())

    def test_a_recycle_bin_item_and_the_bin(self):
        trash = self.data / "Trash"
        (trash / "files").mkdir(parents=True)
        (trash / "info").mkdir()
        (trash / "files" / "old.txt").write_text("x", encoding="utf-8")
        (trash / "info" / "old.txt.trashinfo").write_text(
            "[Trash Info]\nPath=/home/velt/Belgeler/old.txt\nDeletionDate=2026-10-22T16:39:12\n", encoding="utf-8")
        props, _ = self.window(trash / "files" / "old.txt")
        self.assertEqual(props.info["kind"], "trash")
        self.assertEqual(props.info["original"], "/home/velt/Belgeler/old.txt")
        self.assertIn("2026", props.info["deleted"])
        self.assertTrue(props.apply("other.txt", True, True, 0))     # nothing changes in the bin
        self.assertTrue((trash / "files" / "old.txt").exists())
        props, _ = self.window(trash / "files")
        self.assertEqual((props.info["name"], props.info["icon"]), ("Recycle Bin", "user-trash-full"))

    def test_the_root_drive(self):
        props, _ = self.window("/")
        self.assertEqual(props.info["kind"], "drive")
        drive = props.drive
        self.assertGreater(props.info["capacity"], 0)
        self.assertTrue(0 <= drive["usedFraction"] <= 1)
        self.assertEqual(props.sizeText, "")


if __name__ == "__main__":
    unittest.main()
