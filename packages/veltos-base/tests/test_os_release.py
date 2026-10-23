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

    def test_links_to_the_veltos_website(self):
        # Product owner, 2026-10-22: the operating system's site.
        self.assertEqual(self.fields["HOME_URL"], "https://veltos.ahmetfurkandemir.com/")
        self.assertEqual(self.fields["SUPPORT_URL"], "https://veltos.ahmetfurkandemir.com/")

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


class LoginBannerTests(unittest.TestCase):
    def test_console_banner_says_veltos(self):
        issue = (PKG / "issue").read_text()
        self.assertTrue(issue.startswith("VeltOS "))
        self.assertIn("\\l", issue)   # getty: name of the terminal
        self.assertNotIn("Debian", issue)
        self.assertEqual((PKG / "issue.net").read_text(), "VeltOS 0.1\n")

    def test_banners_follow_the_version(self):
        version = parse_os_release((PKG / "os-release").read_text())["VERSION_ID"]
        self.assertIn(f"VeltOS {version} ", (PKG / "issue").read_text())

    def test_message_after_signing_in(self):
        # Replaces Debian's /etc/motd text (keeping its licence notice) only
        # while it is unchanged; removal brings Debian's back.
        motd = (PKG / "motd").read_text()
        self.assertIn("VeltOS comes with ABSOLUTELY NO WARRANTY", motd)
        self.assertIn("/usr/share/doc/*/copyright", motd)
        self.assertNotIn("Debian", motd)
        postinst = (PKG / "debian/veltos-base.postinst").read_text()
        self.assertIn("cmp -s /etc/motd /usr/share/base-files/motd", postinst)
        postrm = (PKG / "debian/veltos-base.postrm").read_text()
        self.assertIn("install -m 644 /usr/share/base-files/motd /etc/motd", postrm)


if __name__ == "__main__":
    unittest.main()
