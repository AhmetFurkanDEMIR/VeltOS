"""Checks for the VeltOS os-release file (run by dh_auto_test)."""

import re
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent


def parse_os_release(text):
    fields = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        if value[:1] in "\"'":
            value = value[1:-1]
        fields[key] = value
    return fields


class OsReleaseTests(unittest.TestCase):
    def setUp(self):
        self.fields = parse_os_release((PKG / "os-release").read_text())

    def test_identity(self):
        self.assertEqual(self.fields["ID"], "veltos")
        self.assertEqual(self.fields["ID_LIKE"], "debian")
        self.assertEqual(self.fields["NAME"], "VeltOS")

    def test_keeps_debian_codename_for_third_party_repos(self):
        self.assertEqual(self.fields["VERSION_CODENAME"], "trixie")

    def test_keys_follow_spec_syntax(self):
        for key in self.fields:
            self.assertRegex(key, r"^[A-Z0-9_]+$")

    def test_version_matches_changelog(self):
        changelog = (PKG / "debian/changelog").read_text()
        version = re.match(r"\S+ \(([^)~]+)", changelog).group(1)
        self.assertTrue(version.startswith(self.fields["VERSION_ID"] + "."),
                        f"changelog {version} vs VERSION_ID {self.fields['VERSION_ID']}")


if __name__ == "__main__":
    unittest.main()
