"""Repository-wide consistency checks (run by build/scripts/build-packages.sh)."""

import os
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRUNED = {".git", "out", "__pycache__"}


def repo_files():
    """Every file of the repository, without descending into .git, out or
    __pycache__ (out holds builds and extracted upstream packages, whose
    symlinks a Windows host cannot even stat)."""
    for directory, names, files in os.walk(REPO):
        names[:] = sorted(name for name in names if name not in PRUNED)
        for name in sorted(files):
            yield Path(directory) / name


class ArtworkTests(unittest.TestCase):
    def test_logo_copies_match_source(self):
        """Packages build in isolation, so some keep a copy of the logo."""
        source = (REPO / "packages/veltos-desktop/artwork/veltos-logo.svg").read_bytes()
        copies = sorted(REPO.glob("packages/*/branding/veltos-logo.svg"))
        self.assertGreaterEqual(len(copies), 3)
        for copy in copies:
            self.assertEqual(copy.read_bytes(), source, f"{copy} differs from the source logo")

    def test_pkcon_runner_copies_match(self):
        """VeltOS Store and VeltOS Graphics Cards build on their own and each
        carry the runner that keeps pkcon's transactions interactive."""
        source = (REPO / "packages/veltos-store/veltos_store/ptyrun.py").read_bytes()
        copy = REPO / "packages/veltos-graphics/veltos_graphics/ptyrun.py"
        self.assertEqual(copy.read_bytes(), source, f"{copy} differs from veltos-store's ptyrun.py")

    def test_grub_png_tool_copies_match(self):
        """veltos-boot builds in isolation and keeps a copy of the tool that
        rewrites GRUB's pictures (build/scripts/plain-png.py)."""
        source = (REPO / "build/scripts/plain-png.py").read_bytes()
        copy = REPO / "packages/veltos-boot/tools/plain_png.py"
        self.assertEqual(copy.read_bytes(), source, f"{copy} differs from build/scripts/plain-png.py")

    def test_boot_menu_splash_embeds_current_logo(self):
        logo = (REPO / "packages/veltos-desktop/artwork/veltos-logo.svg").read_text()
        inner = logo[logo.index(">", logo.index("<svg")) + 1:logo.rindex("</svg>")]
        splash = (REPO / "build/live-build/config/bootloaders/splash.svg").read_text()
        self.assertIn(inner, splash)

    def test_website_texts_have_turkish(self):
        """Every text key of the website (data-i18n and data-i18n-attr in
        docs/index.html) has a Turkish entry in docs/assets/js/main.js, and
        every picture the page uses exists."""
        page = REPO / "docs/index.html"
        if not page.exists():
            self.skipTest("no website in this tree")
        html = page.read_text(encoding="utf-8")
        script = (REPO / "docs/assets/js/main.js").read_text(encoding="utf-8")
        keys = set(re.findall(r'data-i18n="([^"]+)"', html))
        for attrs in re.findall(r'data-i18n-attr="([^"]+)"', html):
            keys.update(pair.split(":", 1)[1] for pair in attrs.split(";"))
        turkish = set(re.findall(r'^\s*"([^"]+)":', script, re.M))
        self.assertEqual(sorted(keys - turkish), [], "website keys without Turkish text")
        for src in set(re.findall(r'(?:src|href)="(assets/[^"]+)"', html)):
            self.assertTrue((REPO / "docs" / src).exists(), src)

    def test_download_checksum_and_link_agree(self):
        """The ISO's SHA-256 and download link are the same on the website
        (download panel, structured data) and in the README, so a visitor
        checks the file against the release's own .sha256."""
        page = REPO / "docs/index.html"
        if not page.exists():
            self.skipTest("no website in this tree")
        html = page.read_text(encoding="utf-8")
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        site_hashes = set(re.findall(r"\b[0-9a-f]{64}\b", html))
        readme_hashes = set(re.findall(r"\b[0-9a-f]{64}\b", readme))
        self.assertEqual(len(site_hashes), 1, site_hashes)
        self.assertEqual(site_hashes, readme_hashes)
        meta = re.search(r'name="veltos-iso-url" content="([^"]+)"', html).group(1)
        self.assertIn(f'"downloadUrl": "{meta}"', html)
        self.assertIn(meta, readme)
        self.assertIn(meta + ".sha256", html)

    def test_website_icons_are_the_systems(self):
        """The website (docs/) shows VeltOS' own icons: each must still be
        identical to a file of the same name in a package's artwork, data or
        branding folder."""
        icons = sorted((REPO / "docs/assets/icons").glob("*.svg"))
        if not icons:
            self.skipTest("no website in this tree")
        sources = {}
        for pattern in ("packages/*/artwork/*.svg", "packages/*/data/*.svg",
                        "packages/*/branding/*.svg", "packages/*/branding/*/*.svg"):
            for path in REPO.glob(pattern):
                sources.setdefault(path.name, []).append(path.read_bytes())
        for icon in icons:
            with self.subTest(icon=icon.name):
                self.assertIn(icon.read_bytes(), sources.get(icon.name, []),
                              f"docs/assets/icons/{icon.name} differs from the system's icon")


BINARY = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".iso", ".deb", ".gz", ".mo",
          ".woff", ".woff2", ".ttf", ".otf", ".pdf", ".mp3", ".mp4", ".ogg", ".wav", ".webm"}


class LineEndingTests(unittest.TestCase):
    def test_no_crlf_in_text_files(self):
        offenders = []
        for path in repo_files():
            if path.suffix in BINARY:
                continue
            if b"\r\n" in path.read_bytes():
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(offenders, [])

    def test_no_control_characters_in_text_files(self):
        # Shell quoting accidents turn "\b" or "\1" into control characters.
        bad = re.compile(rb"[\x00-\x08\x0b\x0e-\x1f]")
        offenders = []
        for path in repo_files():
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
