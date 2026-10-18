"""Unit tests for tools/build-assets.py (run by dh_auto_test)."""

import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
BREEZE_DIR = Path("/usr/share/color-schemes")

spec = importlib.util.spec_from_file_location(
    "build_assets", PKG / "tools/build-assets.py")
build_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_assets)

SAMPLE_SCHEME = """\
# comment
[Colors:View]
DecorationFocus=61,174,233
ForegroundLink=29,153,243

[Colors:Header][Inactive]
DecorationFocus=61,174,233

[Colors:Selection]
BackgroundAlternate=30,87,116

[General]
ColorScheme=BreezeDark
Name=Breeze Dark
Name[tr]=Esinti Koyu

[KDE]
contrast=4
"""


class KConfigTests(unittest.TestCase):
    def test_nested_groups_round_trip(self):
        groups = build_assets.parse_kconfig(SAMPLE_SCHEME)
        self.assertIn("[Colors:Header][Inactive]", groups)
        again = build_assets.parse_kconfig(build_assets.format_kconfig(groups))
        self.assertEqual(groups, again)

    def test_line_outside_group_is_rejected(self):
        with self.assertRaises(ValueError):
            build_assets.parse_kconfig("Key=value\n")


class ColorSchemeTests(unittest.TestCase):
    def test_accent_replaced_and_names_rewritten(self):
        spec = build_assets.COLOR_SCHEMES["VeltOSDark"]
        groups = build_assets.derive_color_scheme(SAMPLE_SCHEME, "VeltOSDark", spec)
        self.assertEqual(groups["[Colors:View]"]["DecorationFocus"], "79,124,255")
        self.assertEqual(groups["[Colors:Header][Inactive]"]["DecorationFocus"], "79,124,255")
        self.assertEqual(groups["[General]"]["ColorScheme"], "VeltOSDark")
        self.assertEqual(groups["[General]"]["Name"], "VeltOS Dark")
        self.assertNotIn("Name[tr]", groups["[General]"])

    def test_missing_breeze_colour_fails_loudly(self):
        spec = dict(build_assets.COLOR_SCHEMES["VeltOSDark"])
        spec["map"] = {"1,2,3": "4,5,6"}
        with self.assertRaises(SystemExit):
            build_assets.derive_color_scheme(SAMPLE_SCHEME, "VeltOSDark", spec)


class WallpaperTests(unittest.TestCase):
    def test_crop_keeps_target_aspect(self):
        for w, h in build_assets.WALLPAPER_SIZES:
            x, y, vw, vh = build_assets.crop_viewbox(w, h)
            self.assertAlmostEqual(vw / vh, w / h, places=3)
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)

    def test_generated_wallpaper_is_deterministic(self):
        for variant in build_assets.WALLPAPER_VARIANTS:
            first = build_assets.wallpaper_svg(variant)
            self.assertEqual(first, build_assets.wallpaper_svg(variant))
            self.assertIn(">VeltOS</text>", first)

    def test_viewbox_rewrite_keeps_namespaces(self):
        svg = build_assets.wallpaper_svg("images_dark")
        out = build_assets.svg_with_viewbox(svg, 2560, 1600)
        root = out[out.index("<svg"):out.index(">", out.index("<svg")) + 1]
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', root)
        self.assertIn('width="2560"', root)
        self.assertIn('height="1600"', root)


class LayoutScriptTests(unittest.TestCase):
    def test_centered_taskbar_widgets(self):
        js = (PKG / "plasma/layout.js").read_text(encoding="utf-8")
        order = [js.index(w) for w in (
            '"org.kde.plasma.panelspacer"', '"org.veltos.startmenu"',
            '"org.kde.plasma.icontasks"', '"org.kde.plasma.systemtray"')]
        self.assertEqual(order, sorted(order))
        self.assertEqual(js.count('"org.kde.plasma.panelspacer"'), 2)


class StartMenuTests(unittest.TestCase):
    STARTMENU = PKG / "plasma/startmenu"

    def test_metadata(self):
        meta = json.loads((self.STARTMENU / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], build_assets.STARTMENU_ID)
        # Lets the Meta key open this menu.
        self.assertIn("org.kde.plasma.launchermenu", meta["X-Plasma-Provides"])

    def test_config_schema_is_xml(self):
        import xml.etree.ElementTree as ET
        ET.parse(self.STARTMENU / "contents/config/main.xml")

    def test_every_ui_string_is_translated(self):
        strings = set()
        for qml in (self.STARTMENU / "contents/ui").glob("*.qml"):
            strings |= set(re.findall(r'i18n\("((?:[^"\\]|\\.)*)"', qml.read_text(encoding="utf-8")))
        self.assertTrue(strings)
        for po in (self.STARTMENU / "translations").glob("*.po"):
            msgids = set(re.findall(r'^msgid "(.+)"$', po.read_text(encoding="utf-8"), re.M))
            self.assertEqual(sorted(strings - msgids), [], f"untranslated in {po.name}")
            self.assertEqual(sorted(msgids - strings), [], f"stale strings in {po.name}")


@unittest.skipUnless(shutil.which("rsvg-convert") and
                     (BREEZE_DIR / "BreezeDark.colors").exists(),
                     "needs rsvg-convert and kde-style-breeze-data")
class FullBuildTest(unittest.TestCase):
    def test_build_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "assets"
            build_assets.main(["--breeze-colors", str(BREEZE_DIR), "--out", str(out)])
            root = out / "root"
            for lnf in build_assets.LOOK_AND_FEEL:
                meta = json.loads((root / "usr/share/plasma/look-and-feel" / lnf /
                                   "metadata.json").read_text())
                self.assertEqual(meta["KPlugin"]["Id"], lnf)
            kdeglobals = build_assets.parse_kconfig(
                (root / "etc/xdg/kdeglobals").read_text())
            self.assertEqual(kdeglobals["[KDE]"]["LookAndFeelPackage"],
                             build_assets.DEFAULT_LOOK_AND_FEEL)
            self.assertIn("[Colors:Window]", kdeglobals)
            login = (root / "usr/share/sddm/themes/breeze/theme.conf.user").read_text()
            image = login.split("background=", 1)[1].strip()
            self.assertTrue((root / image.lstrip("/")).is_file(), image)


if __name__ == "__main__":
    unittest.main()
