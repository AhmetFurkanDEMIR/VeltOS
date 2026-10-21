"""Save folder, file names and the last capture (standard library only)."""

import datetime
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_camera import files, strings  # noqa: E402


class FileTests(unittest.TestCase):
    def test_camera_roll_in_the_xdg_pictures_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".config").mkdir()
            self.assertEqual(files.camera_roll("en", home, home / ".config"), home / "Pictures/Camera Roll")
            (home / ".config/user-dirs.dirs").write_text('XDG_PICTURES_DIR="$HOME/Resimler"\n', encoding="utf-8")
            self.assertEqual(files.camera_roll("tr", home, home / ".config"), home / "Resimler/Film Rulosu")
            # A pictures folder equal to home is ignored (xdg-user-dirs does that when disabled).
            (home / ".config/user-dirs.dirs").write_text('XDG_PICTURES_DIR="$HOME/"\n', encoding="utf-8")
            self.assertEqual(files.pictures_dir(home, home / ".config"), home / "Pictures")

    def test_names_like_a_phone_camera_and_never_overwrite(self):
        now = datetime.datetime(2026, 10, 21, 9, 30, 15)
        with tempfile.TemporaryDirectory() as tmp:
            first = files.new_path(tmp, "photo", now)
            self.assertEqual(first.name, "IMG_20261021_093015.jpg")
            first.write_bytes(b"x")
            self.assertEqual(files.new_path(tmp, "photo", now).name, "IMG_20261021_093015_2.jpg")
            self.assertEqual(files.new_path(tmp, "video", now).name, "VID_20261021_093015.mp4")

    def test_latest_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertIsNone(files.latest_capture(folder / "missing"))
            self.assertIsNone(files.latest_capture(folder))
            old, new = folder / "IMG_1.jpg", folder / "VID_2.mp4"
            old.write_bytes(b"x")
            new.write_bytes(b"x")
            (folder / "notes.txt").write_text("not a capture")
            past = time.time() - 60
            os.utime(old, (past, past))
            self.assertEqual(files.latest_capture(folder), new)
            self.assertTrue(files.is_video(new))
            self.assertFalse(files.is_video(old))


class StringTests(unittest.TestCase):
    def test_every_text_has_both_languages(self):
        for key, pair in strings.TEXTS.items():
            self.assertEqual(len(pair), 2, key)
            self.assertTrue(all(pair), key)
            self.assertEqual("{n}" in pair[0], "{n}" in pair[1], key)
            self.assertEqual("{folder}" in pair[0], "{folder}" in pair[1], key)


if __name__ == "__main__":
    unittest.main()
