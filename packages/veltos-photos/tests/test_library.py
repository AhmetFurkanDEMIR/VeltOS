"""Scanning, dates, grouping and the picture edits of VeltOS Photos (with
real pictures made by Pillow)."""

import datetime
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_photos import edit, library  # noqa: E402

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


def make_jpeg(path, size=(64, 32), color=(200, 40, 40), taken=None, orientation=None):
    image = Image.new("RGB", size, color)
    exif = Image.Exif()
    if taken:
        exif.get_ifd(0x8769)[0x9003] = taken
    if orientation:
        exif[0x0112] = orientation
    image.save(path, "JPEG", exif=exif.tobytes(), quality=95)


@unittest.skipUnless(HAVE_PIL, "needs Pillow (Build-Depends)")
class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "Pictures/Trip").mkdir(parents=True)
        (self.tmp / "Pictures/.thumbnails").mkdir()
        make_jpeg(self.tmp / "Pictures/Trip/beach.jpg", taken="2024:07:14 10:30:00")
        make_jpeg(self.tmp / "Pictures/new.jpg")
        Image.new("RGB", (8, 8)).save(self.tmp / "Pictures/.thumbnails/skip.png")
        (self.tmp / "Pictures/notes.txt").write_text("not a picture")
        (self.tmp / "Pictures/clip.mp4").write_bytes(b"\0" * 10)
        old = datetime.datetime(2023, 1, 5).timestamp()
        os.utime(self.tmp / "Pictures/clip.mp4", (old, old))

    def test_scan_dates_kinds_and_order(self):
        items = library.scan([self.tmp / "Pictures"])
        names = [Path(i["path"]).name for i in items]
        self.assertEqual(names, ["new.jpg", "beach.jpg", "clip.mp4"])      # newest first, hidden skipped
        beach = items[1]
        self.assertEqual(beach["date"], "2024-07-14T10:30:00")             # EXIF, not the file time
        self.assertTrue(beach["taken"])
        self.assertEqual(items[2]["kind"], "video")
        cache = {i["path"]: i for i in items}
        again = library.scan([self.tmp / "Pictures"], cache)
        self.assertEqual(again, items)

    def test_rows_group_by_month(self):
        items = library.scan([self.tmp / "Pictures"])
        rows = library.rows(items, 2, lambda y, m: f"{m}/{y}")
        kinds = [(r["type"], r.get("title", ""), len(r["items"])) for r in rows]
        self.assertEqual(kinds[0][0], "header")
        self.assertEqual([k for k in kinds if k[0] == "header"][1:], [("header", "7/2024", 0), ("header", "1/2023", 0)])
        self.assertEqual(sum(n for t, _, n in kinds if t == "row"), 3)

    def test_siblings_and_cache_file(self):
        sibs = library.siblings(self.tmp / "Pictures/new.jpg")
        self.assertEqual([Path(s["path"]).name for s in sibs], ["clip.mp4", "new.jpg"])
        cache = self.tmp / "cache/index.json"
        items = library.scan([self.tmp / "Pictures"])
        library.save_cache(cache, items)
        self.assertEqual(set(library.load_cache(cache)), {i["path"] for i in items})


@unittest.skipUnless(HAVE_PIL, "needs Pillow (Build-Depends)")
class EditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photo = self.tmp / "photo.jpg"
        make_jpeg(self.photo, size=(80, 40), taken="2025:01:02 03:04:05")

    def test_rotate_crop_flip_and_keep_exif(self):
        edit.save(self.photo, rotation=90)
        with Image.open(self.photo) as image:
            self.assertEqual(image.size, (40, 80))
            self.assertEqual(image.getexif().get_ifd(0x8769).get(0x9003), "2025:01:02 03:04:05")
        copy = edit.save(self.photo, edit.copy_name(self.photo), crop=[0, 0, 0.5, 0.5])
        self.assertEqual(Path(copy).name, "photo - Copy.jpg")
        with Image.open(copy) as image:
            self.assertEqual(image.size, (20, 40))
        self.assertEqual(edit.copy_name(self.photo).name, "photo - Copy (2).jpg")

    def test_orientation_is_applied_and_reset(self):
        turned = self.tmp / "turned.jpg"
        make_jpeg(turned, size=(80, 40), orientation=6)          # camera held upright
        edit.save(turned, brightness=10)
        with Image.open(turned) as image:
            self.assertEqual(image.size, (40, 80))
            self.assertEqual(image.getexif().get(0x0112), 1)

    def test_adjustments(self):
        base = Image.new("RGB", (4, 4), (100, 100, 100))
        brighter = edit.apply(base, brightness=50).getpixel((0, 0))
        self.assertGreater(brighter[0], 100)
        warm = edit.apply(base, warmth=100).getpixel((0, 0))
        self.assertGreater(warm[0], warm[2])
        grey = edit.apply(Image.new("RGB", (2, 2), (200, 50, 50)), saturation=-100).getpixel((0, 0))
        self.assertEqual(grey[0], grey[1])
        png = Image.new("RGBA", (10, 10), (10, 20, 30, 128))
        self.assertEqual(edit.apply(png, contrast=20).mode, "RGBA")

    def test_info(self):
        facts = edit.info(self.photo)
        self.assertEqual((facts["width"], facts["height"]), (80, 40))


if __name__ == "__main__":
    unittest.main()
