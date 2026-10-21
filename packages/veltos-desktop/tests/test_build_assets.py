"""Unit tests for tools/build-assets.py (run by dh_auto_test)."""

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
# Fluent-kde, unpacked by build/scripts/fetch-upstream.py (upstream.json).
FLUENT_DIR = PKG / "upstream"

spec = importlib.util.spec_from_file_location(
    "build_assets", PKG / "tools/build-assets.py")
build_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_assets)
fluent = build_assets.fluent
wallpapers = build_assets.wallpapers

SAMPLE_SCHEME = """\
# comment
[Colors:Button]
DecorationFocus=0,120,212
DecorationHover=0,145,255

[Colors:Complementary]
DecorationFocus=0,120,212

[Colors:Header]
DecorationFocus=0,120,212

[Colors:Tooltip]
DecorationFocus=0,120,212

[Colors:View]
DecorationFocus=0,120,212
ForegroundLink=66,133,244
ForegroundActive=255,128,224

[Colors:Header][Inactive]
DecorationFocus=52,118,207

[Colors:Window]
DecorationFocus=0,120,212

[Colors:Selection]
BackgroundNormal=0,120,212
BackgroundAlternate=82,148,226
DecorationFocus=127,195,255

[General]
Name=FluentDark
Name[tr]=Akici Koyu

[KDE]
contrast=0
"""

SAMPLE_KVCONFIG = """\
[%General]
author=Vince Liuice
comment=An uncomplicated theme
translucent_windows=true
blurring=true
popup_blurring=true
no_inactiveness=false

[GeneralColors]
highlight.color=#0078D4
translucent_windows=keep-me
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
    def derive(self, text=SAMPLE_SCHEME):
        groups = build_assets.parse_kconfig(text)
        return fluent.derive_color_scheme(groups, "VeltOSDark", fluent.COLOR_SCHEMES["VeltOSDark"])

    def test_accent_replaced_and_names_rewritten(self):
        groups = self.derive()
        self.assertEqual(groups["[Colors:View]"]["DecorationFocus"], "79,124,255")
        self.assertEqual(groups["[Colors:Header][Inactive]"]["DecorationFocus"], "79,124,255")
        self.assertEqual(groups["[Colors:Selection]"]["BackgroundNormal"], "79,124,255")
        self.assertEqual(groups["[Colors:View]"]["ForegroundActive"], "79,124,255")
        self.assertEqual(groups["[General]"]["ColorScheme"], "VeltOSDark")
        self.assertEqual(groups["[General]"]["Name"], "VeltOS Dark")
        self.assertNotIn("Name[tr]", groups["[General]"])

    def test_no_windows_blue_left(self):
        text = build_assets.format_kconfig(self.derive())
        self.assertNotIn("0,120,212", text)

    def test_unexpected_layout_fails_loudly(self):
        with self.assertRaises(SystemExit):
            self.derive("[General]\nName=x\n")


class FluentTests(unittest.TestCase):
    def test_recolour_is_case_insensitive(self):
        out = fluent.recolour('fill="#0078D4" stroke="#0078d4"', "light", "t")
        self.assertEqual(out, 'fill="#2f5ee6" stroke="#2f5ee6"')

    def test_recolour_fails_without_fluent_blue(self):
        with self.assertRaises(SystemExit):
            fluent.recolour('fill="#123456"', "light", "t")

    def test_kvantum_general_keys_only_in_general(self):
        out = fluent.set_ini_keys(SAMPLE_KVCONFIG, "[%General]", fluent.KVANTUM_GENERAL, "t")
        self.assertIn("translucent_windows=false", out)
        self.assertIn("translucent_windows=keep-me", out)
        self.assertIn("comment=VeltOS application style", out)

    def test_missing_key_fails_loudly(self):
        with self.assertRaises(SystemExit):
            fluent.set_ini_keys(SAMPLE_KVCONFIG, "[%General]", {"nonexistent": "1"}, "t")

    def test_menus_nearly_opaque(self):
        edges = "".join(f'<g id="menu-normal-{e}"><path style="opacity:0.75;fill:#fff"/></g>'
                        for e in ("left", "right", "top", "bottom", "topleft", "topright",
                                  "bottomleft", "bottomright"))
        svg = ('<path id="menu-normal" style="opacity:0.75;fill:#fff"/>' + edges
               + '<path id="menuitem-normal" style="opacity:0.1"/>')
        out = fluent.set_menu_opacity(svg, 0.94, "t")
        self.assertEqual(out.count("opacity:0.94"), 9)
        self.assertIn('id="menuitem-normal" style="opacity:0.1"', out)   # hover stays
        with self.assertRaises(SystemExit):
            fluent.set_menu_opacity('<path id="menu-normal"/>', 0.94, "t")


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
            # Like Windows 11: no logo or name on the wallpaper.
            self.assertNotIn("<text", first)

    def test_every_design_in_both_variants(self):
        # Settings' themes use these package ids (veltos-settings devices.THEMES).
        ids = {package for package, _name in wallpapers.DESIGNS.values()}
        self.assertTrue({"VeltOS", "VeltOS-Nebula", "VeltOS-Ember", "VeltOS-Tide", "VeltOS-Dawn"} <= ids)
        for design in wallpapers.DESIGNS:
            light, dark = wallpapers.svg(design, "light"), wallpapers.svg(design, "dark")
            self.assertNotEqual(light, dark, design)
            self.assertNotIn("<text", light + dark)

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
            strings |= set(re.findall(r'i18np?\("((?:[^"\\]|\\.)*)"', qml.read_text(encoding="utf-8")))
        self.assertTrue(strings)
        for po in (self.STARTMENU / "translations").glob("*.po"):
            msgids = set(re.findall(r'^msgid "(.+)"$', po.read_text(encoding="utf-8"), re.M))
            self.assertEqual(sorted(strings - msgids), [], f"untranslated in {po.name}")
            self.assertEqual(sorted(msgids - strings), [], f"stale strings in {po.name}")


class QuickSettingsTests(StartMenuTests):
    STARTMENU = PKG / "plasma/quicksettings"

    def test_metadata(self):
        meta = json.loads((self.STARTMENU / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], build_assets.QUICKSETTINGS_ID)

    def test_config_schema_is_xml(self):
        self.skipTest("no configuration")

    def test_layout_adds_it_and_drops_the_tray_icons_it_replaces(self):
        js = (PKG / "plasma/layout.js").read_text(encoding="utf-8")
        self.assertIn('panel.addWidget("org.veltos.quicksettings")', js)
        enabled = js.split('writeConfig("extraItems"', 1)[1].split("]", 1)[0]
        for replaced in ("networkmanagement", "volume", "battery", "bluetooth", "brightness"):
            self.assertNotIn(replaced, enabled)


class SearchTests(StartMenuTests):
    STARTMENU = PKG / "plasma/search"
    PLUGIN_ID = build_assets.SEARCH_ID

    def test_metadata(self):
        meta = json.loads((self.STARTMENU / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], self.PLUGIN_ID)
        self.assertIn(self.STARTMENU.name, build_assets.PLASMOIDS)

    def test_config_schema_is_xml(self):
        self.skipTest("no configuration")

    def test_layout_adds_it_next_to_start(self):
        js = (PKG / "plasma/layout.js").read_text(encoding="utf-8")
        start = js.index('addWidget("org.veltos.startmenu")')
        here = js.index(f'addWidget("{self.PLUGIN_ID}")')
        tasks = js.index('addWidget("org.kde.plasma.icontasks")')
        self.assertLess(start, here)
        self.assertLess(here, tasks)


class TaskViewTests(SearchTests):
    STARTMENU = PKG / "plasma/taskview"
    PLUGIN_ID = build_assets.TASKVIEW_ID


class ClockTests(StartMenuTests):
    STARTMENU = PKG / "plasma/clock"

    def test_metadata(self):
        meta = json.loads((self.STARTMENU / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], build_assets.CLOCK_ID)

    def test_two_cards_like_windows(self):
        main = (self.STARTMENU / "contents/ui/main.qml").read_text(encoding="utf-8")
        # The notification centre is its own card above the calendar and
        # must not take the focus (the calendar popup closes without it).
        self.assertIn("type: PlasmaCore.Dialog.Notification", main)
        self.assertIn("flags: Qt.WindowDoesNotAcceptFocus", main)
        self.assertIn("NotificationCenter {", main)
        self.assertIn("startFocus()", main)


class CaptionButtonTests(unittest.TestCase):
    def test_windows_11_buttons(self):
        import xml.etree.ElementTree as ET
        for variant in ("light", "dark"):
            for kind in ("minimize", "maximize", "restore", "close"):
                svg = fluent.caption_svg(kind, variant)
                root = ET.fromstring(svg)
                ids = {el.get("id") for el in root.iter() if el.get("id")}
                states = {"active-center", "inactive-center", "hover-center",
                          "pressed-center", "deactivated-center"}
                if kind == "close":
                    states |= {"hover-maximized-center", "pressed-maximized-center"}
                self.assertEqual(ids, states, kind)
                hover = svg.split('id="hover-center"', 1)[1].split("</g>", 1)[0]
                self.assertEqual(fluent.CLOSE_RED in hover, kind == "close", kind)
                if kind == "close":
                    # Rounded top right corner; square when maximised.
                    self.assertIn(" A ", hover)
                    square = svg.split('id="hover-maximized-center"', 1)[1].split("</g>", 1)[0]
                    self.assertIn(fluent.CLOSE_RED, square)
                    self.assertNotIn(" A ", square)
        with self.assertRaises(ValueError):
            fluent.caption_svg("shade", "light")

    def test_title_bar_metrics(self):
        layout = fluent.AURORAE_LAYOUT
        self.assertEqual((layout["ButtonWidth"], layout["ButtonHeight"], layout["TitleHeight"]),
                         ("46", "32", "32"))
        self.assertEqual(layout["TitleEdgeRight"], "0")      # buttons flush with the corner


class TaskbarTests(unittest.TestCase):
    def test_clock(self):
        meta = json.loads((PKG / "plasma/clock/metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], build_assets.CLOCK_ID)
        js = (PKG / "plasma/layout.js").read_text(encoding="utf-8")
        self.assertIn('panel.addWidget("org.veltos.clock")', js)
        self.assertIn('clock.globalShortcut = "Meta+N"', js)     # Windows: Win+N
        self.assertNotIn("digitalclock", js)

    def test_show_desktop_at_the_right_end(self):
        meta = json.loads((PKG / "plasma/showdesktop/metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], build_assets.SHOWDESKTOP_ID)
        js = (PKG / "plasma/layout.js").read_text(encoding="utf-8")
        self.assertGreater(js.index('addWidget("org.veltos.showdesktop")'),
                           js.index('addWidget("org.veltos.clock")'))

    def test_see_through_like_windows(self):
        js = (PKG / "plasma/layout.js").read_text(encoding="utf-8")
        self.assertIn('panel.opacity = "translucent"', js)
        svg = ('<svg><rect id="a" style="opacity:1" class="ColorScheme-Background"/>'
               '<path class="ColorScheme-Background" d="M0 0"/>'
               '<rect id="hint" style="fill-opacity:1" fill="#f00"/></svg>')
        out = fluent.set_background_opacity(svg, 0.86)
        self.assertIn('id="a" style="opacity:0.86"', out)
        self.assertIn('<path style="opacity:0.86" class=', out)
        self.assertIn('id="hint" style="fill-opacity:1"', out)
        with self.assertRaises(SystemExit):
            fluent.set_background_opacity("<svg/>", 0.5)


@unittest.skipUnless(shutil.which("rsvg-convert") and (FLUENT_DIR / "Kvantum").is_dir(),
                     "needs rsvg-convert and upstream/ (Fluent-kde)")
class FullBuildTest(unittest.TestCase):
    def test_build_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "assets"
            build_assets.main(["--fluent", str(FLUENT_DIR), "--out", str(out)])
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
            self.check_fluent_themes(root, kdeglobals)
            self.check_terminal(root)

    def check_terminal(self, root):
        import re
        import xml.etree.ElementTree as ET
        konsolerc = build_assets.parse_kconfig((root / "etc/xdg/konsolerc").read_text())
        profile_name = konsolerc["[Desktop Entry]"]["DefaultProfile"]
        profile = build_assets.parse_kconfig(
            "\n".join(line for line in (root / "usr/share/konsole" / profile_name).read_text().splitlines()
                      if not line.startswith("#")))
        self.assertEqual(profile_name, "VeltOS Light.profile")          # the default theme is light
        tab_style = konsolerc["[TabBar]"]["TabBarUserStyleSheetFile"].removeprefix("file:///")
        self.assertIn("QTabBar::tab:selected", (root / tab_style).read_text())
        self.assertTrue((root / "usr/share/veltos/konsole/tabs-dark.css").is_file())
        backgrounds = {"VeltOS Light.profile": "250,250,250", "VeltOS Dark.profile": "12,12,12"}
        for name, background in backgrounds.items():
            profile = build_assets.parse_kconfig(
                "\n".join(line for line in (root / "usr/share/konsole" / name).read_text().splitlines()
                          if not line.startswith("#")))
            scheme = profile["[Appearance]"]["ColorScheme"]
            colours = (root / f"usr/share/konsole/{scheme}.colorscheme").read_text()
            self.assertIn(f"[Background]\nColor={background}\n", colours)   # One Half Light, Campbell
            self.assertTrue(profile["[Appearance]"]["Font"].startswith("Cascadia Mono,12,"))
            self.assertEqual(profile["[General]"]["Name"], name.removesuffix(".profile"))
        expected = {"konsoleui.rc": ("konsole", "20"), "sessionui.rc": ("session", "36")}  # Konsole 25.04.2
        for name, (gui_name, number) in expected.items():
            text = (root / "usr/share/kxmlgui5/konsole" / name).read_text()
            gui = ET.fromstring(text.split("\n", 2)[2])
            self.assertEqual((gui.get("name"), gui.get("version")), (gui_name, number))
            self.assertIsNone(gui.find("ToolBar"))
            # KXMLGUI (KXMLGUIClient::findVersionNumber) takes the first
            # "version" after the first "gui" after the first "<" as the
            # file's number: a comment mentioning it hid the file (VM).
            start = text.lower().index("gui", text.index("<") + 1)
            found = re.match(r'version\s*=\s*"(\d+)"', text[text.lower().index("version", start):])
            self.assertEqual(found and found.group(1), number, name)

    def check_explorer_layout(self, root):
        import xml.etree.ElementTree as ET
        rc = root / "usr/share/veltos/dolphin/dolphinui.rc"
        gui = ET.parse(rc).getroot()
        self.assertGreater(int(gui.get("version")), 43)  # Dolphin 25.04's own is 43
        bars = {bar.get("name"): [a.get("name") for a in bar.findall("Action")]
                for bar in gui.findall("ToolBar")}
        self.assertIn("url_navigators", bars["mainToolBar"])
        self.assertEqual(bars["commandBar"][:2], ["new_menu", "edit_cut"])

    def check_title_catalogs(self, root):
        mo = root / "usr/share/locale/tr@veltos/LC_MESSAGES/dolphin.mo"
        self.assertIn("Dosya Gezgini".encode(), mo.read_bytes())
        self.assertIn(b"File Explorer", (root / "usr/share/locale/en@veltos/LC_MESSAGES/dolphin.mo").read_bytes())

    def check_session_files(self, root, kdeglobals):
        self.assertTrue((root / "etc/xdg/plasma-workspace/env/veltos-session.sh").is_file())
        for helper in ("session-defaults", "update-app-names", "start-categories"):
            path = root / "usr/libexec/veltos" / helper
            self.assertTrue(path.stat().st_mode & 0o111, f"{helper} is not executable")
        # Default account picture: new accounts (skel), sign-in screen (FacesDir).
        picture = (root / "usr/share/veltos/faces/default.png").read_bytes()
        self.assertTrue(picture.startswith(b"\x89PNG"))
        self.assertEqual((root / "usr/share/veltos/faces/.face.icon").read_bytes(), picture)
        self.assertFalse((root / "etc/skel").exists())     # Debian policy: no package files in skel
        self.assertIn("FacesDir=/usr/share/veltos/faces\n",
                      (root / "usr/lib/sddm/sddm.conf.d/10-veltos.conf").read_text())
        # Firefox and Mail (Thunderbird): autoconfig loads the caption buttons.
        css = "file:///usr/share/veltos/firefox/caption-buttons.css"
        self.assertTrue((root / "usr/share/veltos/firefox/caption-buttons.css").is_file())
        for prefs, cfg in (("usr/lib/firefox-esr/defaults/pref/veltos.js", "usr/lib/firefox-esr/veltos.cfg"),
                           ("usr/share/thunderbird/defaults/pref/veltos.js", "usr/lib/thunderbird/veltos.cfg")):
            self.assertIn('pref("general.config.filename", "veltos.cfg");', (root / prefs).read_text())
            # File dialogs through the portal (VeltOS File Explorer's dialog).
            self.assertIn('pref("widget.use-xdg-desktop-portal.file-picker", 1);', (root / prefs).read_text())
            text = (root / cfg).read_text()
            self.assertTrue(text.startswith("//"), cfg)       # autoconfig skips the first line
            self.assertIn(css, text)
        mail = (root / "usr/share/thunderbird/defaults/pref/veltos.js").read_text()
        self.assertIn('pref("mail.shell.checkDefaultClient", false);', mail)
        self.assertIn("file:///usr/share/veltos/mail/mail.css", (root / "usr/lib/thunderbird/veltos.cfg").read_text())
        self.assertNotIn("mail.css", (root / "usr/lib/firefox-esr/veltos.cfg").read_text())
        # Firefox's downloads panel in the Windows 11 look.
        self.assertIn("file:///usr/share/veltos/firefox/downloads.css", (root / "usr/lib/firefox-esr/veltos.cfg").read_text())
        self.assertIn("#downloadsPanel", (root / "usr/share/veltos/firefox/downloads.css").read_text())
        css = (root / "usr/share/veltos/mail/mail.css").read_text()
        self.assertIn('@-moz-document url-prefix("chrome://messenger/content/")', css)   # never inside mails
        # The add-account page is about:accountsetup (Thunderbird 140), not a
        # chrome:// URL: without it the page kept Thunderbird's look (VM).
        self.assertIn('url("about:accountsetup")', css)
        self.assertIn('content: "Add your account";', css)
        self.assertIn('content: "Hesabınızı ekleyin";', css)
        restrictions = kdeglobals["[KDE Control Module Restrictions]"]
        self.assertEqual(restrictions["kcm_kdeconnect"], "false")
        self.assertIn("ToolButtonStyle=IconOnly", (root / "etc/xdg/dolphinrc").read_text())

    def check_fluent_themes(self, root, kdeglobals):
        kvantum = root / "usr/share/Kvantum" / fluent.KVANTUM_DIR
        for name in fluent.KVANTUM:
            self.assertTrue((kvantum / f"{name}.svg").is_file())
            config = (kvantum / f"{name}.kvconfig").read_text()
            self.assertIn("translucent_windows=false", config)
            self.assertIn("no_inactiveness=true", config)
        self.assertEqual(kdeglobals["[KDE]"]["widgetStyle"], "kvantum")
        self.assertEqual(kdeglobals["[KDE]"]["ShowIconsOnPushButtons"], "false")
        self.assertEqual(kdeglobals["[KDE]"]["DefaultDarkLookAndFeel"], "org.veltos.dark")
        self.check_session_files(root, kdeglobals)
        self.check_title_catalogs(root)
        self.check_explorer_layout(root)
        for name in fluent.AURORAE:
            theme = root / "usr/share/aurorae/themes" / name
            self.assertTrue((theme / f"{name}rc").is_file())
            self.assertIn(f"X-KDE-PluginInfo-Name={name}", (theme / "metadata.desktop").read_text())
        kwinrc = (root / "etc/xdg/kwinrc").read_text()
        self.assertIn("theme=__aurorae__svg__VeltOS\n", kwinrc)
        for name in fluent.DESKTOPTHEMES:
            theme = root / "usr/share/plasma/desktoptheme" / name
            meta = json.loads((theme / "metadata.json").read_text())
            self.assertEqual(meta["KPlugin"]["Id"], name)
            self.assertTrue((theme / "widgets/panel-background.svgz").is_file())
            self.assertIn("[Colors:Window]", (theme / "colors").read_text())
            # Other brands' logos are not shipped.
            for rel in fluent.DESKTOPTHEME_DROP:
                self.assertFalse((theme / rel).exists(), rel)
        # Everything the global themes point to exists.
        for lnf, spec in build_assets.LOOK_AND_FEEL.items():
            self.assertTrue((root / "usr/share/plasma/desktoptheme" / spec["plasma_theme"]).is_dir())
            self.assertTrue((root / "usr/share/aurorae/themes" / spec["decoration"]).is_dir())
            self.assertTrue((root / "usr/share/color-schemes" / f"{spec['color_scheme']}.colors").is_file())


if __name__ == "__main__":
    unittest.main()
