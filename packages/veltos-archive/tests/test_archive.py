"""archive.py against the real 7-Zip and bsdtar (Build-Depends), and its
pure helpers."""

import datetime
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_archive import archive, strings  # noqa: E402

HAVE_7Z = shutil.which("7z") is not None
HAVE_BSDTAR = shutil.which("bsdtar") is not None


def run(command, cwd=None):
    return subprocess.run(command, cwd=cwd, env=archive.environment(), capture_output=True, text=True)


def make_tree(root):
    (root / "photos/2024").mkdir(parents=True)
    (root / "photos/2024/beach.jpg").write_bytes(b"\xff\xd8" + b"x" * 5000)
    (root / "photos/notes.txt").write_text("hello\n")
    (root / "Türkçe adı.txt").write_text("ç ğ ı ö ş ü\n", encoding="utf-8")


@unittest.skipUnless(HAVE_7Z, "needs 7z (Build-Depends)")
class SevenZipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "src"
        self.src.mkdir()
        make_tree(self.src)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def create(self, name, fmt, password="", encrypt_names=False):
        target = self.tmp / name
        command = archive.add_command(target, ["photos", "Türkçe adı.txt"], fmt, "normal", password, encrypt_names)
        result = run(command, cwd=self.src)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return target

    def listing(self, path, password=""):
        result = run(archive.list_command(path, password))
        return archive.parse_listing(result.stdout + result.stderr)

    def test_zip_listing_and_tree(self):
        target = self.create("photos.zip", "zip")
        info, entries, error = self.listing(target)
        self.assertEqual(error, "")
        self.assertEqual(info["type"].lower(), "zip")
        tree = archive.Tree(entries)
        top = {e["name"]: e for e in tree.children("")}
        self.assertEqual(set(top), {"photos", "Türkçe adı.txt"})
        self.assertTrue(top["photos"]["isDir"])
        self.assertEqual(top["photos"]["size"], 5002 + 6)
        inside = {e["name"] for e in tree.children("photos")}
        self.assertEqual(inside, {"2024", "notes.txt"})
        beach = tree.entries["photos/2024/beach.jpg"]
        self.assertEqual(beach["size"], 5002)
        self.assertTrue(beach["crc"])
        self.assertIsInstance(beach["modified"], datetime.datetime)
        self.assertEqual(tree.totals()["files"], 3)

    def test_extract_selection_with_folders(self):
        target = self.create("photos.7z", "7z")
        _info, entries, _error = self.listing(target)
        tree = archive.Tree(entries)
        out = self.tmp / "out"
        members = tree.expand(["photos/2024"])
        result = run(archive.extract_command(target, out, members))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((out / "photos/2024/beach.jpg").is_file())
        self.assertFalse((out / "photos/notes.txt").exists())
        self.assertEqual(archive.errors(result.stdout), ("", ""))

    def test_overwrite_modes(self):
        target = self.create("p.zip", "zip")
        out = self.tmp / "out"
        run(archive.extract_command(target, out))
        (out / "Türkçe adı.txt").write_text("changed")
        run(archive.extract_command(target, out, overwrite="skip"))
        self.assertEqual((out / "Türkçe adı.txt").read_text(), "changed")
        run(archive.extract_command(target, out, overwrite="rename"))
        self.assertTrue(any("Türkçe adı" in p.name and p.name != "Türkçe adı.txt" for p in out.iterdir()))
        run(archive.extract_command(target, out, overwrite="overwrite"))
        self.assertEqual((out / "Türkçe adı.txt").read_text(encoding="utf-8"), "ç ğ ı ö ş ü\n")

    def test_password_protected(self):
        target = self.create("secret.7z", "7z", password="sırrı", encrypt_names=True)
        _info, entries, error = self.listing(target)
        self.assertEqual(error, "password")
        self.assertEqual(entries, [])
        _info, _entries, error = self.listing(target, "wrong")
        self.assertEqual(error, "password")
        info, entries, error = self.listing(target, "sırrı")
        self.assertEqual(error, "")
        self.assertTrue(any(e["encrypted"] for e in entries))
        result = run(archive.extract_command(target, self.tmp / "o", password="wrong"))
        self.assertEqual(archive.errors(result.stdout + result.stderr)[0], "password")
        zipped = self.create("secret.zip", "zip", password="pw")
        result = run(archive.extract_command(zipped, self.tmp / "z", password="bad"))
        self.assertEqual(archive.errors(result.stdout + result.stderr)[0], "password")
        result = run(archive.extract_command(zipped, self.tmp / "z", password="pw"))
        self.assertEqual(result.returncode, 0)
        self.assertTrue((self.tmp / "z/photos/notes.txt").is_file())

    def test_test_delete_and_append(self):
        target = self.create("edit.zip", "zip")
        self.assertEqual(run(archive.test_command(target)).returncode, 0)
        info, entries, _ = self.listing(target)
        self.assertTrue(archive.can_delete(info))
        tree = archive.Tree(entries)
        self.assertEqual(run(archive.delete_command(target, tree.expand(["photos"]))).returncode, 0)
        _info, entries, _ = self.listing(target)
        self.assertEqual([e["path"] for e in entries], ["Türkçe adı.txt"])
        (self.tmp / "extra.txt").write_text("more")
        self.assertEqual(run(archive.append_command(target, ["extra.txt"], info), cwd=self.tmp).returncode, 0)
        _info, entries, _ = self.listing(target)
        self.assertIn("extra.txt", [e["path"] for e in entries])

    def test_not_an_archive(self):
        bogus = self.tmp / "bogus.zip"
        bogus.write_text("not a zip")
        _info, entries, error = self.listing(bogus)
        self.assertEqual(entries, [])
        self.assertEqual(error, "unsupported")

    @unittest.skipUnless(HAVE_BSDTAR, "needs bsdtar")
    def test_tar_formats(self):
        for fmt in ("tar.gz", "tar.xz", "tar.zst"):
            target = self.create("photos" + archive.CREATE_FORMATS[fmt][1], fmt)
            self.assertTrue(archive.is_compressed_tar(target))
            result = run(archive.tar_list_command(target))
            info, entries, error = archive.parse_tar_listing(result.stdout + result.stderr, target)
            self.assertEqual(error, "", fmt)
            self.assertEqual(info["type"], fmt.upper())
            tree = archive.Tree(entries)
            self.assertEqual({e["name"] for e in tree.children("")}, {"photos", "Türkçe adı.txt"}, fmt)
            self.assertEqual(tree.entries["photos/2024/beach.jpg"]["size"], 5002)
            out = self.tmp / ("x-" + fmt)
            out.mkdir()
            result = run(archive.tar_extract_command(target, out, ["photos/2024"]))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out / "photos/2024/beach.jpg").is_file())
            self.assertFalse((out / "photos/notes.txt").exists())
            self.assertEqual(sum(1 for line in result.stderr.splitlines() if line.startswith("x ")), 2)
            self.assertEqual(run(archive.tar_test_command(target)).returncode, 0)

    def test_tar_listing_dates_and_links(self):
        text = ("drwxr-xr-x  0 root   root        0 Oct 21 05:37 p/\n"
                "lrwxrwxrwx  0 root   root        0 Oct 21 05:37 p/link -> a\n"
                "-rw-r--r--  0 root   root     1234 Mar  3  2024 p/T\u00fcrk\u00e7e dir/b c.txt\n")
        now = datetime.datetime(2026, 10, 21, 12, 0)
        info, entries, error = archive.parse_tar_listing(text, "x.tar.gz", now)
        self.assertEqual(error, "")
        paths = {e["path"]: e for e in entries}
        self.assertEqual(set(paths), {"p", "p/link", "p/T\u00fcrk\u00e7e dir/b c.txt"})
        self.assertEqual(paths["p"]["modified"], datetime.datetime(2026, 10, 21, 5, 37))
        self.assertEqual(paths["p/T\u00fcrk\u00e7e dir/b c.txt"]["modified"], datetime.datetime(2024, 3, 3))
        self.assertEqual(paths["p/T\u00fcrk\u00e7e dir/b c.txt"]["size"], 1234)
        _info, _entries, error = archive.parse_tar_listing("bsdtar: Error opening archive: Unrecognized archive format\n")
        self.assertEqual(error, "unsupported")


class HelperTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(archive.archive_stem("photos.tar.gz"), "photos")
        self.assertEqual(archive.archive_stem("big.part1.rar"), "big")
        self.assertEqual(archive.archive_stem("x.7z.001"), "x")
        self.assertEqual(archive.create_format("A.TAR.XZ"), "tar.xz")
        self.assertEqual(archive.create_format("a.rar"), "")
        self.assertTrue(archive.is_archive_name("a.RAR"))
        self.assertFalse(archive.is_archive_name("a.txt"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "one.txt").write_text("x")
            self.assertEqual(archive.default_archive_name([tmp / "one.txt"]), "one.zip")
            self.assertEqual(archive.default_archive_name([tmp / "one.txt"], "7z"), "one.7z")
            (tmp / "x.zip").write_text("x")
            self.assertEqual(archive.unique_path(tmp / "x.zip").name, "x (2).zip")
            self.assertEqual(archive.unique_path(tmp / "y.zip").name, "y.zip")
            (tmp / "dir").mkdir()
            self.assertEqual(archive.unique_path(tmp / "dir", is_dir=True).name, "dir (2)")
            (tmp / "a/b").mkdir(parents=True)
            self.assertEqual(archive.common_parent([tmp / "a/b", tmp / "one.txt"]), tmp.resolve())

    def test_progress_and_errors(self):
        self.assertEqual(archive.progress("  5% 3 - a\b\b\b 12% 4 - b"), 12)
        self.assertIsNone(archive.progress("Scanning"))
        self.assertEqual(archive.errors("ERROR: Data Error in encrypted file. Wrong password? : a"),
                         ("password", ""))
        self.assertEqual(archive.errors("Everything is Ok"), ("", ""))
        self.assertEqual(archive.errors("ERROR: No more files\n")[0], "error")

    def test_password_is_always_given(self):
        # Without -p, 7-Zip would wait for a password on the terminal.
        for command in (archive.list_command("a.zip"), archive.extract_command("a.zip", "/tmp"),
                        archive.test_command("a.zip")):
            self.assertIn("-p", command)

    def test_listing_parser_handles_missing_folders(self):
        text = ("--\nPath = a.zip\nType = zip\nPhysical Size = 10\n\n----------\n"
                "Path = deep/inside/file.txt\nFolder = -\nSize = 4\nPacked Size = 3\n"
                "Modified = 2026-10-21 09:00:00\nCRC = 1234ABCD\nEncrypted = -\nMethod = Deflate\n\n")
        info, entries, error = archive.parse_listing(text)
        tree = archive.Tree(entries)
        self.assertEqual([e["name"] for e in tree.children("")], ["deep"])
        self.assertEqual([e["name"] for e in tree.children("deep")], ["inside"])
        self.assertEqual(tree.expand(["deep"]), ["deep", "deep/inside", "deep/inside/file.txt"])

    def test_texts(self):
        for key, pair in strings.TEXTS.items():
            self.assertEqual(len(pair), 2, key)
            for placeholder in ("{name}", "{size}", "{count}", "{folder}", "{files}", "{folders}", "{type}",
                                "{query}", "{time}", "{ext}"):
                self.assertEqual(placeholder in pair[0], placeholder in pair[1], (key, placeholder))


if __name__ == "__main__":
    unittest.main()
