#!/usr/bin/env python3
"""Prepare the repository for a VeltOS release (before the commit that
GitHub Actions turns into the release, .github/workflows/release.yml):

    release-bump.py 1.1 [--date "Mon, 02 Nov 2026 12:00:00 +0000"]

- VERSION says 1.1;
- veltos-base's os-release says VeltOS 1.1 (PRETTY_NAME, VERSION_ID,
  VERSION) and its changelog gets 1.1.0;
- every package whose changelog's newest version is a development one
  (1.1.0~dev7) gets the release version (1.1.0) with a changelog entry.
  Installed PCs then upgrade from any 1.1.0~devN, and the next
  development versions (1.2.0~dev1) sort after the release.

docs/release-notes/1.1.md (English, `<!-- tr -->`, Turkish) is written
by hand; the script stops when it is missing. Run release-check.py
afterwards. Files are written with LF line endings.
"""

import argparse
import datetime
import email.utils
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HEADER = re.compile(r"^(?P<name>\S+) \((?P<version>[^)]+)\) (?P<rest>[^\n]*)\n")
TRAILER = re.compile(r"^ -- (?P<who>.+?)  (?P<date>.+)$", re.M)


def release_version(current):
    """1.1.0 for 1.1.0~dev7; None when `current` is no development version."""
    if "~dev" not in current:
        return None
    return current.split("~dev", 1)[0]


def entry(name, version, rest, who, date, text):
    return f"{name} ({version}) {rest}\n\n  * {text}\n\n -- {who}  {date}\n\n"


# Packages whose files this script changes for every release carry the
# release's number: veltos-base (os-release; VERSION_ID follows it) and
# calamares-settings-veltos (the installer's branding). Without a new
# version the installer package changed under the old one, and
# release-check's "changed since the previous release" refused it.
ALWAYS_BUMPED = ("veltos-base", "calamares-settings-veltos")


def bump_changelog(path, release, date, base=False):
    """Adds the release entry; returns the new version or None. With
    `base` (ALWAYS_BUMPED) the package gets the release's number even when
    it carries no development version."""
    text = path.read_text(encoding="utf-8")
    head = HEADER.match(text)
    trailer = TRAILER.search(text)
    if not head or not trailer:
        raise SystemExit(f"{path}: no changelog entry to follow")
    current = head.group("version")
    if base and not current.startswith(release + "."):
        new = f"{release}.0"
    else:
        new = release_version(current)
    if not new:
        return None
    path.write_text(entry(head.group("name"), new, head.group("rest"), trailer.group("who"), date,
                          f"VeltOS {release}.") + text, encoding="utf-8", newline="\n")
    return new


def bump_os_release(path, release):
    text = path.read_text(encoding="utf-8")
    for key in ("PRETTY_NAME", "VERSION_ID", "VERSION"):
        value = f"VeltOS {release}" if key == "PRETTY_NAME" else release
        text, count = re.subn(rf'^{key}=.*$', f'{key}="{value}"', text, flags=re.M)
        if count != 1:
            raise SystemExit(f"{path}: no {key} line")
    path.write_text(text, encoding="utf-8", newline="\n")
    # The console's sign-in banners (/etc/issue, /etc/issue.net) name it too.
    for name in ("issue", "issue.net"):
        banner = path.parent / name
        if banner.exists():
            text, count = re.subn(r"\AVeltOS \d+\.\d+", f"VeltOS {release}", banner.read_text(encoding="utf-8"))
            if count != 1:
                raise SystemExit(f"{banner}: does not start with \"VeltOS X.Y\"")
            banner.write_text(text, encoding="utf-8", newline="\n")


BRANDING = "packages/calamares-settings-veltos/calamares/branding/veltos/branding.desc"


def bump_installer_branding(path, release):
    """The installer names the version it installs (its side bar): VeltOS
    1.1's installer still said 1.0 because nothing changed this file."""
    text = path.read_text(encoding="utf-8")
    for key, value in (("version", f'"{release}"'), ("shortVersion", f'"{release}"'),
                       ("versionedName", f"VeltOS {release}"), ("shortVersionedName", f"VeltOS {release}")):
        text, count = re.subn(rf"^(\s*{key}:\s*).*$", lambda m: m.group(1) + value, text, flags=re.M)
        if count != 1:
            raise SystemExit(f"{path}: no {key} line")
    path.write_text(text, encoding="utf-8", newline="\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="the release, e.g. 1.1")
    parser.add_argument("--date", default=email.utils.format_datetime(
        datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)).replace("-0000", "+0000"))
    parser.add_argument("--root", type=Path, default=REPO, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d+\.\d+", args.version):
        raise SystemExit("the release version is MAJOR.MINOR (1.1)")
    root = args.root
    notes = root / f"docs/release-notes/{args.version}.md"
    if not notes.exists():
        raise SystemExit(f"write {notes.relative_to(root)} first (English, <!-- tr -->, Turkish)")
    (root / "VERSION").write_text(args.version + "\n", encoding="utf-8", newline="\n")
    bump_os_release(root / "packages/veltos-base/os-release", args.version)
    bump_installer_branding(root / BRANDING, args.version)
    for changelog in sorted(root.glob("packages/*/debian/changelog")):
        name = changelog.parent.parent.name
        new = bump_changelog(changelog, args.version, args.date, base=name in ALWAYS_BUMPED)
        if new:
            print(f"{name}: {new}")
    print(f"VERSION: {args.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
