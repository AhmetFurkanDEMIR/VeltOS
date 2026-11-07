#!/usr/bin/env python3
"""Checks before a VeltOS release (GitHub Actions, .github/workflows/release.yml):

    release-check.py --version 1.2 [--previous v1.1]

- VERSION, veltos-base's os-release (VERSION_ID) and the release notes
  (docs/release-notes/VERSION.md, English and Turkish) agree;
- every package whose source changed since the previous release has a
  higher version than it had there. Installed PCs get a package only when
  its version is higher (VeltOS Update is APT), so a changed package with
  the old version would never reach them.

Exits 1 and names what is wrong.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def changelog_version(text):
    match = re.match(r"^\S+ \(([^)]+)\)", text or "")
    return match.group(1) if match else ""


def git(*args, root=REPO):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return result.returncode, result.stdout


def version_gt(a, b):
    return subprocess.run(["dpkg", "--compare-versions", a, "gt", b]).returncode == 0


def problems(version, previous, root=REPO):
    found = []
    if (root / "VERSION").read_text(encoding="utf-8").strip() != version:
        found.append(f"VERSION does not say {version}")
    os_release = (root / "packages/veltos-base/os-release").read_text(encoding="utf-8")
    if f'VERSION_ID="{version}"' not in os_release:
        found.append(f'packages/veltos-base/os-release: VERSION_ID is not "{version}"')
    branding = root / "packages/calamares-settings-veltos/calamares/branding/veltos/branding.desc"
    text = branding.read_text(encoding="utf-8")
    if not (re.search(rf"^\s*versionedName:\s*VeltOS {re.escape(version)}\s*$", text, re.M)
            and re.search(rf'^\s*version:\s*"{re.escape(version)}"\s*$', text, re.M)):
        found.append(f"{branding.relative_to(root)}: the installer does not name VeltOS {version}")
    base = changelog_version((root / "packages/veltos-base/debian/changelog").read_text(encoding="utf-8"))
    if not base.startswith(version + "."):
        found.append(f"veltos-base {base}: its version must start with {version}. (VERSION_ID follows it)")
    notes = root / f"docs/release-notes/{version}.md"
    if not notes.exists():
        found.append(f"{notes.relative_to(root)} is missing (the release's text)")
    elif "<!-- tr -->" not in notes.read_text(encoding="utf-8"):
        found.append(f"{notes.relative_to(root)}: English, the line <!-- tr --> and Turkish")
    for changelog in sorted((root / "packages").glob("*/debian/changelog")):
        current = changelog_version(changelog.read_text(encoding="utf-8"))
        if "~dev" in current:
            found.append(f"{changelog.parent.parent.name} {current}: a release carries no development "
                         f"versions (build/scripts/release-bump.py {version})")
    if previous:
        for changelog in sorted((root / "packages").glob("*/debian/changelog")):
            package = changelog.parent.parent
            rel = package.relative_to(root).as_posix()
            code, _ = git("diff", "--quiet", previous, "HEAD", "--", rel, root=root)
            if code == 0:
                continue                         # unchanged since the previous release
            code, old_text = git("show", f"{previous}:{rel}/debian/changelog", root=root)
            if code != 0:
                continue                         # a new package
            new, old = changelog_version(changelog.read_text(encoding="utf-8")), changelog_version(old_text)
            if not version_gt(new, old):
                found.append(f"{package.name}: changed since {previous} but its version {new} is not higher "
                             f"than {old} (add a debian/changelog entry)")
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True)
    parser.add_argument("--previous", default="")
    args = parser.parse_args()
    found = problems(args.version, args.previous)
    for problem in found:
        print(f"::error::{problem}")
    print(f"release {args.version}: {'ready' if not found else f'{len(found)} problem(s)'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
