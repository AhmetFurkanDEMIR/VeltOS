"""VeltOS' symbolic icons follow the light and dark colour schemes: each
has KDE's colour-scheme style sheet and every painted element its class, so
Plasma recolours it (a bare currentColor stayed black on the dark taskbar,
product owner 2026-10-26)."""

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

BRANDING = Path(__file__).resolve().parent.parent / "branding"
SVG = "{http://www.w3.org/2000/svg}"
PAINTED = {f"{SVG}{name}" for name in ("path", "rect", "circle", "ellipse", "line", "polyline", "polygon")}


class SymbolicIconTests(unittest.TestCase):
    def test_every_symbolic_icon_follows_the_colour_scheme(self):
        icons = sorted(BRANDING.glob("*-symbolic.svg"))
        self.assertGreaterEqual(len(icons), 7)
        for icon in icons:
            with self.subTest(icon=icon.name):
                root = ET.parse(icon).getroot()
                styles = [s.text or "" for s in root.iter(f"{SVG}style") if s.get("id") == "current-color-scheme"]
                self.assertEqual(len(styles), 1)
                self.assertRegex(styles[0], r"\.ColorScheme-Text \{ color:#363636; \}")
                for element in root.iter():
                    if element.tag in PAINTED:
                        self.assertEqual(element.get("class"), "ColorScheme-Text", element.attrib)
                # No fixed colours: everything comes from the scheme.
                text = icon.read_text(encoding="utf-8")
                self.assertEqual(re.findall(r'(?:fill|stroke)="#', text), [])

    def test_build_recolours_the_dark_trees(self):
        rules = (BRANDING.parent / "debian/rules").read_text(encoding="utf-8")
        self.assertIn("s/color:#363636;/color:#dedede;/", rules)


if __name__ == "__main__":
    unittest.main()
