#!/usr/bin/env python3
"""Give Fluent's folder icons the yellow of Windows 11 folders.

    recolour-folders.py ICONS_DIR      (usr/share/icons of the package)

Fluent draws folders in its blue (#198ee6) with a 60 % opaque back and an
80 % opaque front. Windows 11 folders are yellow and solid, so the back
becomes a deeper amber and the front a light yellow, both opaque. Applies to
the place icons (folders, home, desktop, ...) and the File Explorer icon.
Symbolic links are skipped (their targets are recoloured once).

Windows 11 also shows these coloured icons in small sizes (File Explorer's
navigation pane), while Fluent has monochrome 16-24 px place icons; those
are removed where a coloured one exists, so the coloured ones are used
(VeltOS's own small drawings of the special folders are kept).
"""

import re
import sys
from pathlib import Path

FLUENT_BLUE = "#198ee6"
BACK = "#E3A21A"     # back of the folder
FRONT = "#FFC83D"    # front of the folder
OTHER = "#F2B425"    # anything else drawn in Fluent's blue

PAIR = re.compile(r'fill="' + FLUENT_BLUE + r'"(\s+)opacity="(0?\.\d+|1)"', re.IGNORECASE)


def recolour(svg):
    def pick(match):
        colour = BACK if float(match.group(2)) < 0.7 else FRONT
        return f'fill="{colour}"'
    svg = PAIR.sub(pick, svg)
    return re.sub(re.escape(FLUENT_BLUE), OTHER, svg, flags=re.IGNORECASE)


def veltos_drawing(path):
    """True for VeltOS's own files (not symbolic links, which may dangle)."""
    if path.is_symlink():
        return False
    return "VeltOS artwork" in path.read_text(encoding="utf-8")


def drop_small_places(icons, names):
    dropped = 0
    for base in icons.glob(".Fluent*-base"):
        for size in ("16", "22", "24"):
            for path in (base / size / "places").glob("*.svg"):
                # VeltOS's own small drawings (branding/small/) stay.
                if path.name in names and not veltos_drawing(path):
                    path.unlink()
                    dropped += 1
    return dropped


def main(argv):
    icons = Path(argv[1])
    scalable = icons / ".Fluent-base" / "scalable"
    targets = sorted(p for p in (scalable / "places").glob("*.svg") if not p.is_symlink())
    targets.append((scalable / "apps" / "system-file-manager.svg").resolve())
    changed = 0
    for path in targets:
        text = path.read_text(encoding="utf-8")
        if FLUENT_BLUE.lower() not in text.lower():
            continue
        path.write_text(recolour(text), encoding="utf-8", newline="\n")
        changed += 1
    if changed < 20:
        raise SystemExit(f"only {changed} folder icons recoloured: did Fluent change?")
    names = {p.name for p in (scalable / "places").glob("*.svg")}
    print(f"recoloured {changed} folder icons, "
          f"dropped {drop_small_places(icons, names)} monochrome small place icons")


if __name__ == "__main__":
    main(sys.argv)
