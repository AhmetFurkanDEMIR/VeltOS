"""Accessibility > Mouse pointer (pointer.py): styles, the colour mode, custom
colours made from the Fluent theme's Xcursor files, the size."""

import array
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_settings import pointer  # noqa: E402

WHITE, EDGE, SHADOW = 0xFFFFFFFF, 0xFF21232B, 0x40000000
RING = 0xFF0078D4          # the busy ring's blue


def xcursor(images):
    """An Xcursor file from [(nominal size, [pixels])] (square images)."""
    chunks = []
    for size, pixels in images:
        side = int(len(pixels) ** 0.5)
        header = struct.pack("<9I", 36, pointer.IMAGE, size, 1, side, side, 1, 1, 0)
        chunks.append((pointer.IMAGE, size, header + struct.pack(f"<{len(pixels)}I", *pixels)))
    return pointer.write_chunks(chunks)


def pixels_of(data):
    out = {}
    for kind, size, chunk in pointer.read_chunks(data):
        if kind == pointer.IMAGE:
            values = array.array("I")
            values.frombytes(chunk[36:])
            out[size] = list(values)
    return out


class Recorder:
    def __init__(self):
        self.commands = []

    def __call__(self, command, timeout=20, input=None):
        self.commands.append(command)
        return 0, ""


class PointerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.home = root / "home"
        patcher = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(root / "config"),
                                               "XDG_CONFIG_DIRS": str(root / "etc")})
        patcher.start()
        self.addCleanup(patcher.stop)
        # Custom themes go to ~/.icons (icons_home).
        home = mock.patch.object(pointer, "icons_home", return_value=root / "data" / "icons")
        home.start()
        self.addCleanup(home.stop)

    def test_default_is_the_colour_mode(self):
        self.assertEqual(pointer.load(), {"style": "theme", "colour": ""})
        self.assertEqual(pointer.theme_for("theme", dark=False), pointer.BLACK)
        self.assertEqual(pointer.theme_for("theme", dark=True), pointer.WHITE)

    def test_fixed_styles_ignore_the_mode(self):
        for dark in (False, True):
            self.assertEqual(pointer.theme_for("white", dark), pointer.WHITE)
            self.assertEqual(pointer.theme_for("black", dark), pointer.BLACK)
        self.assertEqual(pointer.theme_for("custom", True, "#ff8c00", 48), "VeltOS-pointer-FF8C00-48")

    def test_choice_is_saved(self):
        pointer.save({"style": "custom", "colour": "#00B7FF"})
        self.assertEqual(pointer.load(), {"style": "custom", "colour": "#00B7FF"})
        pointer.state_file().write_text('{"style": "rainbow"}', encoding="utf-8")
        self.assertEqual(pointer.load()["style"], "theme")
        pointer.state_file().write_text("not json", encoding="utf-8")
        self.assertEqual(pointer.load()["style"], "theme")

    def test_sizes(self):
        self.assertEqual(pointer.nearest_size(24), 24)
        self.assertEqual(pointer.nearest_size(32), 30)
        self.assertEqual(pointer.nearest_size(200), 96)
        self.assertEqual(pointer.nearest_size("x"), 24)
        self.assertEqual(pointer.state()["pointerSize"], 1)
        etc = Path(os.environ["XDG_CONFIG_DIRS"])
        etc.mkdir(parents=True)
        (etc / "kcminputrc").write_text("[Mouse]\ncursorSize=48\n", encoding="utf-8")
        self.assertEqual(pointer.state()["pointerSize"], pointer.SIZES.index(48) + 1)

    def test_recolour_changes_the_body_only(self):
        values = array.array("I", [WHITE, EDGE, SHADOW, RING, 0])
        pointer.recolour_pixels(values, "#FF8C00", 0xFF, 0x25)
        self.assertEqual(values[0], 0xFFFF8C00)          # body: the colour
        self.assertEqual(values[1], EDGE)                # edge stays
        self.assertEqual(values[2], SHADOW)              # soft shadow stays
        self.assertEqual(values[3], RING)                # coloured parts stay
        self.assertEqual(values[4], 0)

    def test_recolour_blends_the_seam(self):
        grey = 0xFF909090                                # between edge and body
        values = array.array("I", [grey])
        pointer.recolour_pixels(values, "#00FF00", 0xFF, 0x25)
        r, g, b = (values[0] >> 16) & 0xFF, (values[0] >> 8) & 0xFF, values[0] & 0xFF
        self.assertLess(r, 0x90)
        self.assertGreater(g, r)
        self.assertEqual(values[0] >> 24, 0xFF)

    def test_dark_colours_use_the_pointer_with_a_white_edge(self):
        self.assertEqual(pointer.base_for("#102040")[0], pointer.BLACK)
        self.assertEqual(pointer.base_for("#FFE600")[0], pointer.WHITE)
        values = array.array("I", [0xFF333333, 0xFFFFFFFF])
        pointer.recolour_pixels(values, "#102040", 0x33, 0xFF)
        self.assertEqual(values[0], 0xFF102040)
        self.assertEqual(values[1], 0xFFFFFFFF)

    def test_xcursor_keeps_wanted_sizes(self):
        data = xcursor([(24, [WHITE] * 4), (48, [WHITE] * 16), (96, [WHITE] * 64)])
        out = pixels_of(pointer.recolour_xcursor(data, "#00B7FF", 0xFF, 0x25, {48, 96}))
        self.assertEqual(sorted(out), [48, 96])
        self.assertEqual(set(out[48]), {0xFF00B7FF})

    def make_base(self):
        icons = Path(self.tmp.name) / "icons"
        cursors = icons / pointer.WHITE / "cursors"
        cursors.mkdir(parents=True)
        (cursors / "default").write_bytes(xcursor([(24, [WHITE, EDGE, SHADOW, 0]), (48, [WHITE] * 4)]))
        try:
            os.symlink("default", cursors / "arrow")
        except OSError:
            self.skipTest("no symbolic links here")
        return icons

    def test_custom_theme(self):
        icons = self.make_base()
        home = Path(self.tmp.name) / "data" / "icons"
        (home / "VeltOS-pointer-123456-24" / "cursors").mkdir(parents=True)
        name = pointer.make_custom_theme("#ff8c00", 24, [icons], home)
        self.assertEqual(name, "VeltOS-pointer-FF8C00-24")
        theme = home / name
        self.assertEqual(os.readlink(theme / "cursors" / "arrow"), "default")
        out = pixels_of((theme / "cursors" / "default").read_bytes())
        self.assertEqual(sorted(out), [24, 48])          # its size and up to twice it
        self.assertEqual(out[24][0], 0xFFFF8C00)
        self.assertEqual(out[24][1], EDGE)
        self.assertIn("Inherits=" + pointer.WHITE, (theme / "index.theme").read_text(encoding="utf-8"))
        self.assertFalse((home / "VeltOS-pointer-123456-24").exists())   # the old one went

    def test_apply_sets_theme_and_size(self):
        runner = Recorder()
        self.assertTrue(pointer.apply({"style": "theme"}, 48, dark=True, runner=runner))
        flat = [" ".join(c) for c in runner.commands]
        self.assertTrue(any("kcminputrc" in c and "cursorSize 48" in c for c in flat))
        self.assertIn(f"plasma-apply-cursortheme {pointer.WHITE} --size 48", flat)
        self.assertIn(pointer.CURSOR_CHANGED, runner.commands)

    def test_custom_choice_applies_its_own_theme(self):
        icons = self.make_base()
        runner = Recorder()
        home = Path(self.tmp.name) / "data" / "icons"
        self.assertTrue(pointer.set_choice("custom", "#00b7ff", 24, False, runner, [icons], home))
        self.assertEqual(pointer.load(), {"style": "custom", "colour": "#00B7FF"})
        self.assertIn(["plasma-apply-cursortheme", "VeltOS-pointer-00B7FF-24", "--size", "24"],
                      runner.commands)
        # Back to a theme pointer: the custom theme is removed.
        pointer.set_choice("white", "", 24, False, runner, [icons], home)
        self.assertEqual(list(home.glob("VeltOS-pointer-*")), [])
        self.assertFalse(pointer.set_choice("rainbow", "", 24, False, runner, [icons], home))

    def test_follow_only_with_the_colour_mode_style(self):
        runner = Recorder()
        self.assertTrue(pointer.follow("dark", runner))
        self.assertIn(["plasma-apply-cursortheme", pointer.WHITE, "--size", "24"], runner.commands)
        pointer.save({"style": "black", "colour": ""})
        runner = Recorder()
        self.assertTrue(pointer.follow("dark", runner))
        self.assertEqual(runner.commands, [])

    def test_command_line(self):
        with mock.patch.object(pointer, "follow", return_value=True) as follow:
            self.assertEqual(pointer.main(["follow", "dark"]), 0)
            follow.assert_called_once_with("dark")
        with mock.patch("sys.stderr"):
            self.assertEqual(pointer.main(["follow", "blue"]), 2)


if __name__ == "__main__":
    unittest.main()
