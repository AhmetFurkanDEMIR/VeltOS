"""Checks for veltos-boot (run by dh_auto_test)."""

import configparser
import importlib.util
import re
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_assets", PKG / "tools/build-assets.py")
build_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_assets)


class PlymouthTests(unittest.TestCase):
    def test_theme_file(self):
        theme = configparser.ConfigParser()
        theme.read(PKG / "plymouth/veltos.plymouth")
        self.assertEqual(theme["Plymouth Theme"]["ModuleName"], "two-step")
        self.assertEqual(theme["two-step"]["ImageDir"], "/usr/share/plymouth/themes/veltos")

    def test_spinner_frames_differ_and_loop(self):
        frames = [build_assets.spinner_frame(i) for i in range(build_assets.SPINNER_FRAMES)]
        self.assertEqual(len(set(frames)), len(frames))
        self.assertEqual(build_assets.spinner_frame(0),
                         build_assets.spinner_frame(build_assets.SPINNER_FRAMES))


class PlymouthDefaultsTests(unittest.TestCase):
    def test_defaults_select_the_veltos_theme(self):
        defaults = configparser.ConfigParser()
        defaults.read(PKG / "plymouth/plymouthd.defaults")
        self.assertEqual(defaults["Daemon"]["Theme"], "veltos")

    def test_sddm_waits_for_the_splash(self):
        dropin = configparser.ConfigParser()
        dropin.read(PKG / "systemd/veltos-plymouth.conf")
        self.assertIn("plymouth-quit.service", dropin["Unit"]["After"])

    def test_diversion_scripts_agree(self):
        preinst = (PKG / "debian/veltos-boot.preinst").read_text()
        postrm = (PKG / "debian/veltos-boot.postrm").read_text()
        for script in (preinst, postrm):
            self.assertIn("--divert /usr/share/plymouth/plymouthd.defaults.debian", script)


class GrubThemeTests(unittest.TestCase):
    def test_theme_uses_only_generated_fonts(self):
        fonts = {build_assets.grub_font_name(face, size) for face, size in build_assets.GRUB_FONTS}
        self.assertEqual(len(fonts), len(build_assets.GRUB_FONTS))
        theme = (PKG / "grub/theme.txt").read_text()
        used = set(re.findall(r'font(?:-|_font)?\s*[:=]\s*"([^"]+)"', theme))
        used |= set(re.findall(r'_font\s*=\s*"([^"]+)"', theme))
        self.assertTrue(used)
        self.assertEqual(sorted(used - fonts), [])

    def test_highlights_do_not_overlap_the_next_entry(self):
        for theme in (PKG / "grub/theme.txt",
                      PKG.parent.parent / "build/live-build/config/bootloaders/grub-pc/live-theme/theme.txt"):
            if not theme.exists():  # the live theme is outside the package build tree
                continue
            spacing = int(re.search(r"item_spacing = (\d+)", theme.read_text()).group(1))
            self.assertGreaterEqual(spacing, 2 * build_assets.SELECT_CORNER, theme)

    def test_progress_bar_has_no_text(self):
        # Any "text" (even empty) makes GRUB's countdown bar a full line tall.
        self.assertNotIn("text =", (PKG / "grub/theme.txt").read_text().split("+ progress_bar")[1])

    def test_selection_slices_tile_the_highlight(self):
        widths = [build_assets.selection_slice(c, 0)[1] for c in range(3)]
        heights = [build_assets.selection_slice(0, r)[2] for r in range(3)]
        self.assertEqual(sum(widths), build_assets.SELECT_SIZE)
        self.assertEqual(sum(heights), build_assets.SELECT_SIZE)
        self.assertEqual(len(build_assets.SELECT_SLICES), 9)


class GrubTests(unittest.TestCase):
    def test_defaults_name_veltos_and_enable_splash(self):
        text = (PKG / "default/veltos.cfg").read_text()
        self.assertIn('GRUB_DISTRIBUTOR="VeltOS"', text)
        self.assertIn('GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"', text)
        self.assertIn("GRUB_DISABLE_OS_PROBER=false", text)
        self.assertNotIn("debian", text.lower())


if __name__ == "__main__":
    unittest.main()
