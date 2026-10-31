#!/usr/bin/env python3
"""Build a Fluent cursor theme from upstream's SVG sources.

    cursors.py SRC DEST SVG_DIR INDEX_THEME

SRC is upstream's `cursors/src` (config/*.cursor, cursorList and the SVG
folders), SVG_DIR the folder with the drawings (`svg`: dark pointer with a
white edge, `svg-white`: white pointer with a dark edge), DEST the theme
folder to make and INDEX_THEME upstream's index.theme for it.

Upstream ships the themes prebuilt at 24, 30, 36 and 48 px. VeltOS
Settings offers Windows 11's pointer size slider up to 96 px, and KWin
draws a size the theme lacks at the largest one it has (a 96 px pointer
stayed at 48 px, VM 2026-10-31), so every cursor is drawn again at SIZES
with rsvg-convert (upstream's build.sh uses Inkscape the same way: the
32-unit drawing at 4/3 of the nominal size, the hot spot scaled with it)
and packed with xcursorgen. Aliases come from upstream's cursorList.
"""

import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SIZES = (24, 30, 36, 48, 60, 72, 96)
BASE = 24       # upstream's "x1" lines: nominal size 24, drawn at 32 px


def read_config(path):
    """[(hot_x, hot_y, drawing name, delay or None)] of one cursor, from
    the lines of upstream's config for the nominal size 24."""
    frames = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0] != str(BASE):
            continue
        name = Path(parts[3]).stem
        delay = int(parts[4]) if len(parts) > 4 else None
        frames.append((int(parts[1]), int(parts[2]), name, delay))
    return frames


def read_aliases(path):
    """[(alias, target)] from cursorList ("alias target" per line)."""
    pairs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            pairs.append((parts[0], parts[1]))
    return pairs


def pixels(size):
    return size * 4 // 3


def hot_spot(value, size):
    return round(value * size / BASE)


def config_lines(frames, png_of):
    """xcursorgen's input for every size: "size x y file [delay]"."""
    lines = []
    for size in SIZES:
        for hot_x, hot_y, name, delay in frames:
            line = f"{size} {hot_spot(hot_x, size)} {hot_spot(hot_y, size)} {png_of(name, size)}"
            lines.append(line + (f" {delay}" if delay else ""))
    return "\n".join(lines) + "\n"


def build(src, dest, svg_dir, index_theme):
    src, dest = Path(src), Path(dest)
    cursors = {p.stem: read_config(p) for p in sorted((src / "config").glob("*.cursor"))}
    cursors = {name: frames for name, frames in cursors.items() if frames}
    if not cursors:
        sys.exit(f"no cursors in {src / 'config'}")
    drawings = sorted({frame[2] for frames in cursors.values() for frame in frames})
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        def png_of(name, size):
            return tmp / str(size) / f"{name}.png"

        def draw(job):
            name, size = job
            out = png_of(name, size)
            out.parent.mkdir(parents=True, exist_ok=True)
            px = str(pixels(size))
            subprocess.run(["rsvg-convert", "-w", px, "-h", px, "-o", str(out),
                            str(src / svg_dir / f"{name}.svg")], check=True)

        jobs = [(name, size) for name in drawings for size in SIZES]
        with concurrent.futures.ThreadPoolExecutor(os.cpu_count() or 4) as pool:
            list(pool.map(draw, jobs))

        out = dest / "cursors"
        if dest.exists():
            shutil.rmtree(dest)
        out.mkdir(parents=True)
        for name, frames in cursors.items():
            config = tmp / f"{name}.config"
            config.write_text(config_lines(frames, png_of), encoding="utf-8")
            subprocess.run(["xcursorgen", str(config), str(out / name)], check=True)
    # An alias may name another alias listed later: link in rounds, and
    # never leave a link to nothing.
    pending = read_aliases(src / "cursorList")
    while pending:
        left = []
        for alias, target in pending:
            if os.path.lexists(out / alias):
                continue
            if (out / target).exists():
                os.symlink(target, out / alias)
            else:
                left.append((alias, target))
        if len(left) == len(pending):
            break
        pending = left
    shutil.copyfile(index_theme, dest / "index.theme")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    build(*sys.argv[1:])
