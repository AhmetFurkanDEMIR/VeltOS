"""Repository-wide consistency checks (run by build/scripts/build-packages.sh)."""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class ArtworkTests(unittest.TestCase):
    def test_logo_copies_match_source(self):
        """Packages build in isolation, so some keep a copy of the logo."""
        source = (REPO / "packages/veltos-desktop/artwork/veltos-logo.svg").read_bytes()
        copies = sorted(REPO.glob("packages/*/branding/veltos-logo.svg"))
        self.assertGreaterEqual(len(copies), 3)
        for copy in copies:
            self.assertEqual(copy.read_bytes(), source, f"{copy} differs from the source logo")

    def test_boot_menu_splash_embeds_current_logo(self):
        logo = (REPO / "packages/veltos-desktop/artwork/veltos-logo.svg").read_text()
        inner = logo[logo.index(">", logo.index("<svg")) + 1:logo.rindex("</svg>")]
        splash = (REPO / "build/live-build/config/bootloaders/splash.svg").read_text()
        self.assertIn(inner, splash)


class LineEndingTests(unittest.TestCase):
    def test_no_crlf_in_text_files(self):
        offenders = []
        for path in REPO.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "out" in path.parts:
                continue
            if path.suffix in {".png", ".jpg", ".iso", ".deb", ".gz", ".mo"}:
                continue
            if b"\r\n" in path.read_bytes():
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
