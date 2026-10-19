"""Checks for veltos-boot (run by dh_auto_test)."""

import configparser
import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
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

    def test_font_is_copied_into_the_initramfs(self):
        theme = configparser.ConfigParser()
        theme.read(PKG / "plymouth/veltos.plymouth")
        hook = (PKG / "initramfs/hook").read_text()
        self.assertIn("/usr/share/fonts/opentype/inter/Inter-$face.otf", hook)
        faces = re.search(r"for face in ([A-Za-z ]+); do", hook).group(1).split()
        for key in ("Font", "TitleFont"):
            family, *style, _size = theme["two-step"][key].split()
            self.assertEqual(family, "Inter")
            self.assertIn(style[0] if style else "Regular", faces)

    def test_password_box_below_the_logo(self):
        theme = configparser.ConfigParser()
        theme.read(PKG / "plymouth/veltos.plymouth")
        two_step = theme["two-step"]
        logo, entry_height = 168, 34      # watermark.png and entry.png heights
        for height in (600, 768, 1080, 2160):
            logo_top = (height - logo) * float(two_step["WatermarkVerticalAlignment"])
            logo_bottom = logo_top + logo * 54 / 64     # the V ends at y=54 of 64
            box_top = (height - entry_height) * float(two_step["DialogVerticalAlignment"])
            self.assertGreater(box_top, logo_bottom + 8, height)

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


@unittest.skipUnless(os.name == "posix", "runs shell scripts")
class UnlockTextsTests(unittest.TestCase):
    """initramfs/unlock-texts on an excerpt of Debian's cryptsetup functions."""

    def patched(self, source=PKG / "tests/data/cryptsetup-functions", runs=1):
        tmp = Path(tempfile.mkdtemp())
        functions = tmp / "functions"
        shutil.copyfile(source, functions)
        for _ in range(runs):
            result = subprocess.run(["sh", str(PKG / "initramfs/unlock-texts"), str(functions)],
                                    capture_output=True, text=True, check=True)
        return functions, result.stderr

    def test_windows_like_prompt(self):
        functions, warnings = self.patched()
        text = functions.read_text()
        self.assertEqual(warnings, "")
        self.assertIn('keyscriptarg="$(veltos_unlock_prompt)"', text)
        self.assertNotIn("Please unlock disk", text)
        subprocess.run(["sh", "-n", str(functions)], check=True)
        # run_keyscript() exports CRYPTTAB_TRIED, the number of failed tries.
        for tried, prompt in (("0", "Enter the password to unlock this PC"),
                              ("2", "The password is incorrect. Try again.")):
            out = subprocess.run(["sh", "-c", f'. "{functions}"; CRYPTTAB_TRIED={tried} veltos_unlock_prompt'],
                                 capture_output=True, text=True, check=True)
            self.assertEqual(out.stdout, prompt + "\n")

    def test_splash_messages_hidden_others_unchanged(self):
        functions, _ = self.patched()
        text = functions.read_text()
        self.assertIn('*": cryptsetup failed, bad password or options?"|*": set up successfully")', text)
        # Outside the boot splash cryptsetup's own function prints as before.
        for message in ("luks-1: set up successfully", "ERROR: luks-1: maximum number of tries exceeded"):
            out = subprocess.run(["sh", "-c", f'. "{functions}"; cryptsetup_message "{message}"'],
                                 capture_output=True, text=True, check=True)
            self.assertEqual(out.stderr, f"cryptsetup: {message}\n")

    def test_runs_once(self):
        once, _ = self.patched()
        twice, _ = self.patched(runs=2)
        self.assertEqual(once.read_text(), twice.read_text())

    def test_unknown_code_is_left_alone(self):
        tmp = Path(tempfile.mkdtemp()) / "other"
        tmp.write_text("say() {\n    echo hi\n}\n")
        functions, warnings = self.patched(source=tmp)
        self.assertEqual(functions.read_text(), tmp.read_text())
        self.assertEqual(warnings.count("keeping cryptsetup's text"), 2)


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
                                "submenu 'Advanced options for VeltOS GNU/Linux' $menuentry_id_option "
                                "'gnulinux-advanced-1234' {\n"
                                "\tmenuentry 'VeltOS GNU/Linux, with Linux 6.12.113+deb13-amd64 (recovery mode)'"
                                " $menuentry_id_option 'gnulinux-6.12.113+deb13-amd64-recovery-1234' {\n"
                                "\t\tlinux /vmlinuz-6.12.113+deb13-amd64 single\n"
                                "\t}\n"
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
            # Titles without the kernel build suffix; IDs and files keep it.
            self.assertIn("menuentry 'VeltOS, with Linux 6.12.113 (recovery mode)' "
                          "$menuentry_id_option 'gnulinux-6.12.113+deb13-amd64-recovery-1234'", out)
            self.assertIn("linux /vmlinuz-6.12.113+deb13-amd64 single", out)
            self.assertNotIn("Loading", out)
            self.assertIn("linux /vmlinuz", out)
            # A missing original (dpkg left it as 10_linux.dpkg-new, install
            # test 2026-10-19) fails update-grub instead of an empty menu.
            missing = subprocess.run(["sh", "-c", wrapper.replace(str(original), str(original) + ".gone")],
                                     env=env, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("missing", missing.stderr)
            # A failing original fails update-grub instead of dropping entries.
            original.write_text("#!/bin/sh\nexit 3\n")
            failed = subprocess.run(["sh", "-c", wrapper], env=env, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)

    def test_grub_common_configured_before_the_diversion(self):
        control = (PKG / "debian/control").read_text()
        self.assertRegex(control, r"Pre-Depends: grub-common")
        postinst = (PKG / "debian/veltos-boot.postinst").read_text()
        self.assertIn("10_linux.dpkg-new", postinst)      # repairs older installs

    def test_keyboard_layout_in_initramfs(self):
        # The disk encryption password is typed with the installed layout.
        text = (PKG / "initramfs/veltos-keymap").read_text()
        self.assertIn("KEYMAP=y", text.splitlines())

    def test_initramfs_hook_runs_after_plymouth_and_cryptroot(self):
        import subprocess
        out = subprocess.run(["sh", str(PKG / "initramfs/hook"), "prereqs"],
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.split(), ["plymouth", "cryptroot"])

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
