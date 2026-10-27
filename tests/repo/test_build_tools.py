"""The ISO build's own tools: the package pool trimmer and the initrd packer
(build/scripts/trim-pool.py, shrink-initrd.py), which keep the ISO under
2 GiB without leaving anything out."""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), REPO / "build/scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TrimPoolTests(unittest.TestCase):
    def setUp(self):
        self.tool = load("trim-pool")

    def test_installed_packages_from_dpkg_status(self):
        status = ("Package: libc6\nStatus: install ok installed\nArchitecture: amd64\nVersion: 2.41-12\n\n"
                  "Package: grub-pc\nStatus: deinstall ok config-files\nArchitecture: amd64\nVersion: 2.12-9\n\n"
                  "Package: os-prober\nStatus: install ok installed\nArchitecture: amd64\nVersion: 1.83\n")
        self.assertEqual(self.tool.installed(status), {("libc6", "amd64", "2.41-12"), ("os-prober", "amd64", "1.83")})

    def test_the_installers_removals(self):
        conf = (REPO / "packages/calamares-settings-veltos/calamares/modules/packages.conf").read_text()
        names = self.tool.installer_removals(conf)
        self.assertIn("live-boot", names)
        self.assertIn("calamares", names)
        self.assertNotIn("remove", names)

    def test_what_autoremove_takes_is_kept(self):
        simulation = ("NOTE: This is only a simulation!\n"
                      "Purg live-boot [1:20250225]\n"
                      "Purg kpmcore [24.12.3-1]\n"
                      "Remv libkpmcore12:amd64 [24.12.3-1]\n"
                      "Inst something\n")
        self.assertEqual(self.tool.removed_with_autoremove(simulation), {"live-boot", "kpmcore", "libkpmcore12"})

    def test_release_checksums(self):
        suite = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, suite)
        (suite / "main/binary-amd64").mkdir(parents=True)
        (suite / "main/binary-amd64/Packages").write_text("Package: grub-pc\n")
        (suite / "Release").write_text("old\n")
        text = self.tool.checksum_sections(suite)
        self.assertIn("SHA256:\n", text)
        self.assertIn(" main/binary-amd64/Packages\n", text)
        self.assertNotIn(" Release\n", text)


class ShrinkInitrdTests(unittest.TestCase):
    @staticmethod
    def newc(entries):
        """A newc cpio archive of (name, data) entries."""
        out = b""
        for ino, (name, data) in enumerate(entries + [("TRAILER!!!", b"")], 1):
            name_bytes = name.encode() + b"\0"
            header = "070701" + "".join(f"{v:08X}" for v in (ino, 0o100644, 0, 0, 1, 0, len(data), 0, 0, 0, 0,
                                                              len(name_bytes), 0))
            out += header.encode() + name_bytes
            out += b"\0" * (-len(out) % 4) + data
            out += b"\0" * (-len(out) % 4)
        return out

    @unittest.skipUnless(shutil.which("zstd") and shutil.which("xz"), "needs zstd and xz (the builder image)")
    def test_main_part_becomes_xz_and_the_rest_stays(self):
        tool = load("shrink-initrd")
        early = self.newc([("kernel/x86/microcode/GenuineIntel.bin", b"\x01" * 1000)])
        modules = self.newc([("usr/lib/modules/x.ko.xz", b"\x02" * 3000)])
        main = self.newc([("init", b"#!/bin/sh\n" * 500), ("usr/lib/firmware/a.bin", bytes(range(256)) * 400)])
        packed_main = subprocess.run(["zstd", "-q", "-c"], input=main, capture_output=True, check=True).stdout
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        initrd = folder / "initrd.img"
        initrd.write_bytes(early + modules + packed_main)
        self.assertEqual(tool.shrink(str(initrd)), 0)
        data = initrd.read_bytes()
        prefix, rest = tool.split(data)
        self.assertEqual(prefix, early + modules)
        self.assertTrue(rest.startswith(tool.XZ))
        self.assertEqual(subprocess.run(["xz", "-dc"], input=rest, capture_output=True, check=True).stdout, main)
        # The kernel's xz decoder needs CRC32 checks (stream flags byte 1).
        self.assertEqual(rest[7], 0x01)
        self.assertEqual(tool.shrink(str(initrd)), 0)          # already xz: unchanged
        self.assertEqual(initrd.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
