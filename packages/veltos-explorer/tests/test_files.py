"""Tests for listing, sorting, naming and searching (files.py)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_explorer import files  # noqa: E402


def fake_mime(path, is_dir):
    if is_dir:
        return files.FOLDER_MIME, "File folder", "folder"
    ext = os.path.splitext(path)[1]
    return {".txt": ("text/plain", "Text document", "text-plain"),
            ".png": ("image/png", "PNG image", "image-png")}.get(ext, ("application/octet-stream", "File", "unknown"))


class FolderTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        for name in ("file10.txt", "file2.txt", "B.png", "a.txt", ".hidden"):
            (self.dir / name).write_text("x" * 10, encoding="utf-8")
        (self.dir / "Zeta").mkdir()
        (self.dir / "alpha").mkdir()

    def test_listing_hides_dot_files(self):
        names = {i["name"] for i in files.list_folder(self.dir)}
        self.assertNotIn(".hidden", names)
        self.assertIn(".hidden", {i["name"] for i in files.list_folder(self.dir, show_hidden=True)})

    def test_folders_first_then_natural_order(self):
        items = files.sort_items(files.list_folder(self.dir, mime=fake_mime))
        self.assertEqual([i["name"] for i in items], ["alpha", "Zeta", "a.txt", "B.png", "file2.txt", "file10.txt"])
        descending = files.sort_items(items, "name", True)
        self.assertEqual([i["name"] for i in descending][:2], ["Zeta", "alpha"])
        by_type = files.sort_items(items, "type")
        self.assertEqual([i["name"] for i in by_type][2], "B.png")   # "PNG image" < "Text document"
        with self.assertRaises(ValueError):
            files.sort_items(items, "colour")

    def test_entry(self):
        item = next(i for i in files.list_folder(self.dir, mime=fake_mime) if i["name"] == "a.txt")
        self.assertEqual((item["size"], item["type"], item["icon"], item["isDir"]),
                         (10, "Text document", "text-plain", False))

    def test_desktop_launcher_shows_its_own_name_and_icon(self):
        (self.dir / "my-app.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=My App\nName[tr]=Uygulamam\nIcon=veltos-store\nExec=true\n",
            encoding="utf-8")
        (self.dir / "notes.desktop").write_text("just text, not a launcher\n", encoding="utf-8")
        items = {i["path"].rsplit(os.sep, 1)[-1]: i for i in files.list_folder(self.dir, mime=fake_mime)}
        launcher = items["my-app.desktop"]
        self.assertEqual((launcher["name"], launcher["icon"], launcher["type"]), ("My App", "veltos-store", "Shortcut"))
        self.assertEqual(items["notes.desktop"]["name"], "notes.desktop")     # not a launcher: the file name
        self.assertEqual(files.desktop_entry(self.dir / "my-app.desktop", "tr")["name"], "Uygulamam")

    def test_unreadable_folder_raises(self):
        with self.assertRaises(OSError):
            files.list_folder(self.dir / "missing")

    def test_search_matches_all_words_below_the_folder(self):
        (self.dir / "alpha" / "Holiday photo 2026.png").write_text("", encoding="utf-8")
        found = files.search(self.dir, "photo holiday", mime=fake_mime)
        self.assertEqual([i["name"] for i in found], ["Holiday photo 2026.png"])
        self.assertEqual(found[0]["folder"], str(self.dir / "alpha"))
        self.assertEqual(files.search(self.dir, "   "), [])
        self.assertEqual(files.search(self.dir, "a", cancelled=lambda: True), [])


class NameTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_unique_names(self):
        self.assertEqual(files.unique_name(self.dir, "New folder", True), "New folder")
        (self.dir / "New folder").mkdir()
        (self.dir / "New folder (2)").mkdir()
        self.assertEqual(files.unique_name(self.dir, "New folder", True), "New folder (3)")
        (self.dir / "a.txt").write_text("", encoding="utf-8")
        self.assertEqual(files.unique_name(self.dir, "a.txt"), "a (2).txt")
        (self.dir / "v1.0").mkdir()
        self.assertEqual(files.unique_name(self.dir, "v1.0", True), "v1.0 (2)")

    def test_copy_names_like_windows(self):
        (self.dir / "report.pdf").write_text("", encoding="utf-8")
        self.assertEqual(files.copy_name(self.dir, "report.pdf"), "report - Copy.pdf")
        (self.dir / "report - Copy.pdf").write_text("", encoding="utf-8")
        self.assertEqual(files.copy_name(self.dir, "report.pdf"), "report - Copy (2).pdf")
        self.assertEqual(files.copy_name(self.dir, ".bashrc"), ".bashrc - Copy")

    def test_rename_checks(self):
        (self.dir / "a.txt").write_text("", encoding="utf-8")
        (self.dir / "b.txt").write_text("", encoding="utf-8")
        self.assertEqual(files.check_new_name(self.dir, "a.txt", "  "), "empty")
        self.assertEqual(files.check_new_name(self.dir, "a.txt", "x/y"), "invalid")
        self.assertEqual(files.check_new_name(self.dir, "a.txt", "b.txt"), "exists")
        self.assertIsNone(files.check_new_name(self.dir, "a.txt", "A.txt"))
        self.assertIsNone(files.check_new_name(self.dir, "a.txt", "c.txt"))


class StartupTests(unittest.TestCase):
    def test_no_stale_qml_cache(self):
        # Packaged files all carry the same time stamp; a QML disk cache
        # would keep old compiled QML after an update (crash, 2026-10-19).
        text = (Path(__file__).resolve().parent.parent / "veltos_explorer/bin_main.py").read_text(encoding="utf-8")
        self.assertIn('os.environ["QML_DISABLE_DISK_CACHE"] = "1"', text)


class SizeTests(unittest.TestCase):
    def test_details_view_sizes_in_kb(self):
        self.assertEqual(files.size_kb(0), 0)
        self.assertEqual(files.size_kb(1), 1)
        self.assertEqual(files.size_kb(1024), 1)
        self.assertEqual(files.size_kb(1025), 2)
        self.assertEqual(files.size_kb(1234567), 1206)

    def test_human_sizes(self):
        self.assertEqual(files.human_size(900), "900 bytes")
        self.assertEqual(files.human_size(1234567), "1.18 MB")
        self.assertEqual(files.human_size(25 * 1024 ** 3), "25.0 GB")
        self.assertEqual(files.human_size(512 * 1024 ** 3), "512 GB")


if __name__ == "__main__":
    unittest.main()
