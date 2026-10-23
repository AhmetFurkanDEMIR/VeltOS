"""pad-app-icon: a program's own icon, unchanged, drawn with a margin."""

import base64
import importlib.machinery
import importlib.util
import re
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("pad_app_icon", str(PKG / "tools/pad-app-icon"))
spec = importlib.util.spec_from_loader(loader.name, loader)
pad = importlib.util.module_from_spec(spec)
loader.exec_module(pad)


def tiny_png(size):
    """A valid opaque PNG of the given size (standard library only)."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\xff\x80\x00" * size for _ in range(size))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class PadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.hicolor = self.tmp / "hicolor"
        self.dest = self.tmp / "apps"
        self.dest.mkdir()
        for size in (32, 128, 64):
            folder = self.hicolor / f"{size}x{size}/apps"
            folder.mkdir(parents=True)
            (folder / "firefox-esr.png").write_bytes(tiny_png(size))

    def run_tool(self, *extra):
        return pad.main(["firefox-esr", "--dest", str(self.dest), "--hicolor", str(self.hicolor), *extra])

    def test_largest_png_with_a_margin(self):
        self.assertEqual(self.run_tool(), 0)
        svg = (self.dest / "firefox-esr.svg").read_text()
        self.assertIn('viewBox="0 0 128 128"', svg)
        self.assertIn('x="10.24" y="10.24" width="107.52" height="107.52"', svg)
        data = re.search(r"base64,([A-Za-z0-9+/=]+)", svg).group(1)
        self.assertEqual(base64.b64decode(data), (self.hicolor / "128x128/apps/firefox-esr.png").read_bytes())
        self.assertIn(pad.MARKER, svg)

    def test_removed_with_the_program_and_others_left_alone(self):
        self.run_tool()
        for folder in self.hicolor.glob("*/apps"):
            (folder / "firefox-esr.png").unlink()
        self.run_tool()
        self.assertFalse((self.dest / "firefox-esr.svg").exists())
        (self.dest / "firefox-esr.svg").write_text("<svg>someone else's</svg>")
        for size in (32,):
            (self.hicolor / f"{size}x{size}/apps/firefox-esr.png").write_bytes(tiny_png(size))
        self.run_tool()
        self.assertEqual((self.dest / "firefox-esr.svg").read_text(), "<svg>someone else's</svg>")


if __name__ == "__main__":
    unittest.main()
