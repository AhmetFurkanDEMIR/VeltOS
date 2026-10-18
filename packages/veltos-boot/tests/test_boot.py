"""Checks for veltos-boot (run by dh_auto_test)."""

import configparser
import importlib.util
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


class GrubTests(unittest.TestCase):
    def test_defaults_name_veltos_and_enable_splash(self):
        text = (PKG / "default/veltos.cfg").read_text()
        self.assertIn('GRUB_DISTRIBUTOR="VeltOS"', text)
        self.assertIn('GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"', text)
        self.assertIn("GRUB_DISABLE_OS_PROBER=false", text)
        self.assertNotIn("debian", text.lower())


if __name__ == "__main__":
    unittest.main()
