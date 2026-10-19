"""Repository-wide consistency checks (run by build/scripts/build-packages.sh)."""

import re
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

    def test_no_control_characters_in_text_files(self):
        # Shell quoting accidents turn "\b" or "\1" into control characters.
        bad = re.compile(rb"[\x00-\x08\x0b\x0e-\x1f]")
        offenders = []
        for path in REPO.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "out" in path.parts:
                continue
            if path.suffix not in {".py", ".qml", ".js", ".sh", ".svg", ".json", ".md", ".po",
                                   ".conf", ".cfg", ".txt", ".rc", ".desktop"}:
                continue
            if bad.search(path.read_bytes()):
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()


class PySideTests(unittest.TestCase):
    # PySide6 turns keyword arguments of Qt constructors into setter calls
    # with the C library's toupper(); in a Turkish locale "interval" becomes
    # "setİnterval" and the call fails. File Explorer did not start on
    # Turkish systems because of QTimer(self, singleShot=True, interval=250).
    QT_KEYWORD_PROPERTY = re.compile(r"\bQ[A-Z]\w*\((?:[^()]|\([^()]*\))*?\b[a-z]\w*\s*=(?!=)")

    def test_no_qt_properties_as_keyword_arguments(self):
        offenders = []
        for path in sorted(REPO.glob("packages/*/**/*.py")):
            if "tests" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if self.QT_KEYWORD_PROPERTY.search(code):
                    offenders.append(f"{path.relative_to(REPO)}:{number}: {line.strip()}")
        self.assertEqual(offenders, [], "use setters instead of keyword arguments")

    def test_pattern_catches_the_bug(self):
        self.assertTrue(self.QT_KEYWORD_PROPERTY.search("t = QTimer(self, singleShot=True, interval=250)"))
        self.assertFalse(self.QT_KEYWORD_PROPERTY.search("t = QTimer(self)"))
        self.assertFalse(self.QT_KEYWORD_PROPERTY.search('Property(str, notify=changed)'))
