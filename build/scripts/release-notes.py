#!/usr/bin/env python3
"""The text of a VeltOS release on GitHub (GitHub Actions):

    release-notes.py VERSION ISO_NAME SHA256 > notes.md

docs/release-notes/VERSION.md (English, the line `<!-- tr -->`, Turkish)
with the ISO's name and SHA-256 under each language. VeltOS Update shows
the part of the PC's language (veltos_update.release.notes), so the
marker stays.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MARKER = "<!-- tr -->"


def compose(text, iso, sha):
    english, marker, turkish = text.replace("\r\n", "\n").partition(MARKER)
    if not marker:
        raise SystemExit("release notes need English, the line <!-- tr --> and Turkish")
    en = f"{english.rstrip()}\n\n**Download:** `{iso}` · SHA-256 `{sha}`\n"
    tr = f"{turkish.strip()}\n\n**İndirme:** `{iso}` · SHA-256 `{sha}`\n"
    return f"{en}\n{MARKER}\n\n{tr}"


def main():
    version, iso, sha = sys.argv[1:4]
    text = (REPO / f"docs/release-notes/{version}.md").read_text(encoding="utf-8")
    sys.stdout.write(compose(text, iso, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
