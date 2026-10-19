"""Runs helpers/efi-label against fake efibootmgr/blkid/lsblk output, in the
format efibootmgr 18 prints in a Debian 13 VM (install test 2026-10-19)."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ENTRY = ("Boot0008* debian\tHD(1,GPT,77d13c30-cd28-4440-9d84-8f6e4e584087,0x1000,0x96000)"
         "/File(\\EFI\\debian\\shimx64.efi)")


@unittest.skipUnless(os.name == "posix", "runs a shell script")
class EfiLabelTests(unittest.TestCase):
    def run_helper(self, efibootmgr_output):
        tmp = Path(tempfile.mkdtemp())
        bin_dir, efivars, sysfs = tmp / "bin", tmp / "efivars", tmp / "sys"
        bin_dir.mkdir()
        efivars.mkdir()
        (sysfs / "class/block/vda1").mkdir(parents=True)
        (sysfs / "class/block/vda1/partition").write_text("1\n")
        log = tmp / "calls"
        (tmp / "entries").write_text(efibootmgr_output + "\n")
        fakes = {
            "efibootmgr": f'if [ "$1" = -v ]; then cat {tmp}/entries; else echo "$@" >> {log}; fi',
            "blkid": "echo /dev/vda1",
            "lsblk": "echo vda",
        }
        for name, body in fakes.items():
            path = bin_dir / name
            path.write_text(f"#!/bin/sh\n{body}\n")
            path.chmod(0o755)
        env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}",
                   VELTOS_EFIVARS=str(efivars), VELTOS_SYSFS=str(sysfs))
        result = subprocess.run(["sh", str(PKG / "helpers/efi-label")], env=env,
                                capture_output=True, text=True, check=True)
        calls = log.read_text().splitlines() if log.exists() else []
        return result.stdout, calls

    def test_debian_entry_becomes_veltos(self):
        out, calls = self.run_helper("BootCurrent: 0008\nBootOrder: 0008,0000\n" + ENTRY)
        self.assertEqual(calls, ["-q -c -d /dev/vda -p 1 -L VeltOS -l \\EFI\\debian\\shimx64.efi",
                                 "-q -b 0008 -B"])
        self.assertIn("labelled VeltOS", out)

    def test_nothing_to_do(self):
        out, calls = self.run_helper("BootOrder: 0001\nBoot0001* VeltOS\tHD(1,GPT,...)/File(\\EFI\\debian\\shimx64.efi)")
        self.assertEqual(calls, [])
        self.assertIn("nothing to rename", out)


if __name__ == "__main__":
    unittest.main()
