"""tools/wallpapers.py: the VeltOS wallpapers are valid, reproducible SVG
artwork without text, in a light and a dark variant each."""

import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("wallpapers", TOOLS / "wallpapers.py")
wallpapers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wallpapers)

SVG = "{http://www.w3.org/2000/svg}"


class WallpaperTests(unittest.TestCase):
    def test_every_design_in_both_variants(self):
        self.assertEqual(wallpapers.DESIGNS["bloom"][0], "VeltOS")  # the default package
        ids = [package_id for package_id, _name in wallpapers.DESIGNS.values()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 3)
        for design in wallpapers.DESIGNS:
            for variant in ("light", "dark"):
                text = wallpapers.svg(design, variant)
                root = ET.fromstring(text.split("\n", 1)[1])
                self.assertEqual(root.get("viewBox"), "0 0 3840 2160", design)
                self.assertIsNone(root.find(f".//{SVG}text"), f"{design}: no text in wallpapers")
                self.assertIsNone(root.find(f".//{SVG}image"), f"{design}: no embedded pictures")

    def test_reproducible_and_different(self):
        for design in wallpapers.DESIGNS:
            self.assertEqual(wallpapers.svg(design, "light"), wallpapers.svg(design, "light"))
            self.assertNotEqual(wallpapers.svg(design, "light"), wallpapers.svg(design, "dark"))


if __name__ == "__main__":
    unittest.main()
