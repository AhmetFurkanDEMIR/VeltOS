"""Runs helpers/boot-check on fake target roots: the installation stops when
the installed system could not start (no initramfs, or a boot menu that
does not load it)."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
VERSION = "6.12.113+deb13-amd64"
# The installed system's grub.cfg entry (QEMU, BIOS, separate /boot).
ENTRY = ("menuentry 'VeltOS' --class veltos {\n"
         f"\tlinux\t/vmlinuz-{VERSION} root=/dev/vda2 ro quiet splash\n"
         "\techo\t'Loading initial ramdisk ...'\n"
         f"\tinitrd\t/initrd.img-{VERSION}\n"
         "}\n")


@unittest.skipUnless(os.name == "posix", "runs a shell script")
class BootCheckTests(unittest.TestCase):
    def run_helper(self, kernels=(VERSION,), initrds=(VERSION,), grub_cfg=ENTRY, initrd=b"initramfs"):
        target = Path(tempfile.mkdtemp())
        boot = target / "boot"
        (boot / "grub").mkdir(parents=True)
        for version in kernels:
            (boot / f"vmlinuz-{version}").write_bytes(b"kernel")
        for version in initrds:
            (boot / f"initrd.img-{version}").write_bytes(initrd)
        (boot / "grub/grub.cfg").write_text(grub_cfg)
        # The helper sources common.sh from its installed location.
        helper = (PKG / "helpers/boot-check").read_text().replace(
            "/usr/libexec/veltos-installer/common.sh", str(PKG / "helpers/common.sh"))
        return subprocess.run(["sh", "-c", helper], capture_output=True, text=True,
                              env=dict(os.environ, VELTOS_TARGET=str(target)))

    def test_kernel_with_initramfs_in_the_boot_menu(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("every kernel has its initramfs", result.stdout)

    def test_missing_initramfs_stops_the_installation(self):
        # The installed system of 2026-10-23: no initrd.img, no initrd line.
        result = self.run_helper(initrds=(), grub_cfg=ENTRY.replace(f"\tinitrd\t/initrd.img-{VERSION}\n", ""))
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"there is no initramfs for Linux {VERSION}", result.stderr)

    def test_boot_menu_without_the_initramfs_stops_the_installation(self):
        result = self.run_helper(grub_cfg=ENTRY.replace(f"\tinitrd\t/initrd.img-{VERSION}\n", ""))
        self.assertEqual(result.returncode, 1)
        self.assertIn("boot menu does not load the initramfs", result.stderr)

    def test_empty_initramfs_counts_as_missing(self):
        result = self.run_helper(initrd=b"")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no initramfs", result.stderr)

    def test_every_kernel_is_checked(self):
        older = "6.12.100+deb13-amd64"
        result = self.run_helper(kernels=(VERSION, older))
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"no initramfs for Linux {older}", result.stderr)

    def test_no_kernel_stops_the_installation(self):
        result = self.run_helper(kernels=(), initrds=(), grub_cfg="")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no Linux kernel", result.stderr)


if __name__ == "__main__":
    unittest.main()
