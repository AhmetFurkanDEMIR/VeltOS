"""tools/cursors.py: upstream's cursor configs read and scaled to every size."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cursors", PKG / "tools/cursors.py")
cursors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cursors)


class ConfigTest(unittest.TestCase):
    def write(self, text):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "x.cursor"
        path.write_text(text, encoding="utf-8")
        return path

    def test_reads_the_base_size_only(self):
        path = self.write("24 4 4 x1/default.png\n30 5 5 x1_25/default.png\n48 8 8 x2/default.png\n")
        self.assertEqual(cursors.read_config(path), [(4, 4, "default", None)])

    def test_animation_frames_keep_their_delay(self):
        path = self.write("24 4 4 x1/progress-01.png 30\n24 4 4 x1/progress-02.png 30\n"
                          "48 8 8 x2/progress-01.png 30\n")
        self.assertEqual(cursors.read_config(path),
                         [(4, 4, "progress-01", 30), (4, 4, "progress-02", 30)])

    def test_every_size_scales_picture_and_hot_spot(self):
        lines = cursors.config_lines([(4, 4, "default", None)],
                                     lambda name, size: f"/t/{size}/{name}.png").splitlines()
        self.assertEqual(len(lines), len(cursors.SIZES))
        self.assertIn("24 4 4 /t/24/default.png", lines)
        self.assertIn("48 8 8 /t/48/default.png", lines)
        self.assertIn("96 16 16 /t/96/default.png", lines)
        self.assertEqual(cursors.pixels(96), 128)
        self.assertEqual(cursors.pixels(24), 32)

    def test_sizes_reach_96_pixels(self):
        # Windows 11's size slider in VeltOS Settings needs them.
        self.assertEqual(cursors.SIZES[0], 24)
        self.assertEqual(cursors.SIZES[-1], 96)
        # Every size gives whole pixels and a whole hot spot for upstream's 4 px.
        for size in cursors.SIZES:
            self.assertEqual(size * 4 % 3, 0)
            self.assertEqual(4 * size % cursors.BASE, 0)

    def test_aliases(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "cursorList"
        path.write_text("arrow default\nhand2 pointer\n\n", encoding="utf-8")
        self.assertEqual(cursors.read_aliases(path), [("arrow", "default"), ("hand2", "pointer")])


if __name__ == "__main__":
    sys.exit(unittest.main())
