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

    def test_linux_entries_renamed_and_quiet(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "10_linux.dpkg-veltos"
            original.write_text("#!/bin/sh\n"
                                "cat <<'X'\n"
                                "menuentry 'VeltOS GNU/Linux' {\n"
                                "\techo 'Loading Linux 6.12 ...'\n"
                                "\tlinux /vmlinuz\n"
                                "}\n"
                                "X\n")
            original.chmod(0o755)
            wrapper = (PKG / "grub.d/10_linux").read_text().replace(
                "/etc/grub.d/10_linux.dpkg-veltos", str(original))
            env = {"PATH": "/usr/bin:/bin", "GRUB_DISTRIBUTOR": "VeltOS"}
            out = subprocess.run(["sh", "-c", wrapper], capture_output=True, text=True,
                                 check=True, env=env).stdout
            self.assertIn("menuentry 'VeltOS' {", out)
            self.assertNotIn("GNU/Linux", out)
            self.assertNotIn("Loading", out)
            self.assertIn("linux /vmlinuz", out)
            # A failing original fails update-grub instead of dropping entries.
            original.write_text("#!/bin/sh\nexit 3\n")
            failed = subprocess.run(["sh", "-c", wrapper], env=env, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)

    def test_fixed_video_mode_and_hidden_menu(self):
        values = dict(line.split("=", 1) for line in (PKG / "default/veltos.cfg").read_text().splitlines()
                      if "=" in line and not line.startswith("#"))
        # "auto" alone crashed VirtualBox on Hyper-V at kernel start.
        self.assertTrue(values["GRUB_GFXMODE"].startswith("1024x768,800x600"))
        self.assertEqual(values["GRUB_TIMEOUT_STYLE"], "hidden")

    def test_menu_script_shows_menu_only_with_other_systems(self):
        import subprocess
        import tempfile
        script = PKG / "grub.d/35_veltos"
        subprocess.run(["sh", "-n", str(script)], check=True)
        with tempfile.TemporaryDirectory() as bin_dir:
            fake = Path(bin_dir) / "os-prober"
            for found, expect in (("/dev/sda1:Windows Boot Manager:Windows:efi", True), ("", False)):
                fake.write_text(f"#!/bin/sh\necho '{found}'\n" if found else "#!/bin/sh\n")
                fake.chmod(0o755)
                out = subprocess.run(["sh", str(script)], capture_output=True, text=True, check=True,
                                     env={"PATH": f"{bin_dir}:/usr/bin:/bin"}).stdout
                self.assertEqual("set timeout_style=menu" in out, expect, out)
                self.assertIn("set color_normal=black/black", out)


if __name__ == "__main__":
    unittest.main()
