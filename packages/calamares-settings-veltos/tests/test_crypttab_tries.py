"""Runs helpers/crypttab-tries on a fake target root, with the crypttab the
installer wrote in the encrypted install test (2026-10-19)."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
HEADER = "# <name>               <device>                         <password> <options>\n"


@unittest.skipUnless(os.name == "posix", "runs a shell script")
class CrypttabTriesTests(unittest.TestCase):
    def run_helper(self, crypttab):
        target = Path(tempfile.mkdtemp())
        (target / "etc").mkdir()
        path = target / "etc/crypttab"
        path.write_text(crypttab)
        path.chmod(0o600)
        # The helper sources common.sh from its installed location.
        helper = (PKG / "helpers/crypttab-tries").read_text().replace(
            "/usr/libexec/veltos-installer/common.sh", str(PKG / "helpers/common.sh"))
        subprocess.run(["sh", "-c", helper], check=True, capture_output=True,
                       env=dict(os.environ, VELTOS_TARGET=str(target)))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        return path.read_text()

    def test_typed_password_entries_get_unlimited_tries(self):
        out = self.run_helper(
            HEADER + "luks-6872 UUID=6872     none \n"
            "data UUID=1234 none luks,discard\n")
        self.assertEqual(out, HEADER + "luks-6872 UUID=6872 none tries=0\n"
                                       "data UUID=1234 none luks,discard,tries=0\n")

    def test_key_files_and_own_tries_left_alone(self):
        text = (HEADER + "luks-1 UUID=1 /crypto_keyfile.bin luks,keyscript=/bin/cat\n"
                "luks-2 UUID=2 none luks,tries=5\n")
        self.assertEqual(self.run_helper(text), text)


if __name__ == "__main__":
    unittest.main()
