#!/usr/bin/env python3
"""Generate the boot artwork of veltos-boot into <out>/root.

    build-assets.py --out build-assets

  * Plymouth theme "veltos": the VeltOS logo with a Windows-style spinner of
    dots underneath, on a near-black background;
  * GRUB theme "veltos" for installed systems: background with the logo and
    name (the menu is drawn by GRUB on top).

Only the Python standard library and rsvg-convert are required.
"""

import argparse
import math
import shutil
import subprocess
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
LOGO = SRC / "branding/veltos-logo.svg"
PLYMOUTH_DIR = Path("usr/share/plymouth/themes/veltos")
GRUB_DIR = Path("usr/share/grub/themes/veltos")

SPINNER_FRAMES = 60
SPINNER_SIZE = 72
SPINNER_DOTS = 6

# Password prompt images are reused from Plymouth's "spinner" theme.
SHARED_FROM_SPINNER = ["bullet.png", "capslock.png", "entry.png", "keyboard.png",
                       "keymap-render.png", "lock.png"]


def render(svg_text, width, height, dest, tmp):
    tmp.write_text(svg_text, encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsvg-convert", "--width", str(width), "--height", str(height),
                    "--output", str(dest), str(tmp)], check=True)


def logo_inner(prefix):
    """The logo's drawing, with ids prefixed so it can be embedded."""
    logo = LOGO.read_text(encoding="utf-8")
    inner = logo[logo.index(">", logo.index("<svg")) + 1:logo.rindex("</svg>")]
    return inner.replace('id="blade-', f'id="{prefix}blade-').replace("url(#blade-", f"url(#{prefix}blade-")


def spinner_frame(index):
    """Dots chasing each other around a circle, fast at the bottom and slow at
    the top, like the Windows boot spinner."""
    c = SPINNER_SIZE / 2
    orbit = SPINNER_SIZE * 0.36
    radius = SPINNER_SIZE * 0.045
    dots = []
    for dot in range(SPINNER_DOTS):
        phase = (index / SPINNER_FRAMES - dot * 0.055) % 1.0
        # Eased angle: one full turn per cycle with varying speed.
        eased = phase - math.sin(2 * math.pi * phase) / (2 * math.pi) * 0.75
        angle = 2 * math.pi * eased - math.pi / 2
        x, y = c + orbit * math.cos(angle), c + orbit * math.sin(angle)
        dots.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="#FFFFFF"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SPINNER_SIZE}" height="{SPINNER_SIZE}" '
            f'viewBox="0 0 {SPINNER_SIZE} {SPINNER_SIZE}">{"".join(dots)}</svg>')


def build_plymouth(root, tmp):
    dest = root / PLYMOUTH_DIR
    dest.mkdir(parents=True)
    shutil.copy(SRC / "plymouth/veltos.plymouth", dest / "veltos.plymouth")
    render(LOGO.read_text(encoding="utf-8"), 168, 168, dest / "watermark.png", tmp / "logo.svg")
    for i in range(SPINNER_FRAMES):
        render(spinner_frame(i), SPINNER_SIZE, SPINNER_SIZE,
               dest / f"throbber-{i + 1:04d}.png", tmp / "frame.svg")
    for name in SHARED_FROM_SPINNER:
        (dest / name).symlink_to(f"../spinner/{name}")


def grub_background():
    w, h = 1920, 1080
    size = 120
    x, y = (w - size) / 2, 150
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        '<defs>'
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#060A1E"/><stop offset="1" stop-color="#0E1A4A"/></linearGradient>'
        f'<radialGradient id="glow" cx="{w / 2}" cy="{y + size / 2}" r="700" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#3D6CFF" stop-opacity="0.35"/>'
        '<stop offset="1" stop-color="#3D6CFF" stop-opacity="0"/></radialGradient>'
        '</defs>'
        f'<rect width="{w}" height="{h}" fill="url(#bg)"/><rect width="{w}" height="{h}" fill="url(#glow)"/>'
        f'<g transform="translate({x} {y}) scale({size / 64:.4f})">{logo_inner("g-")}</g>'
        f'<text x="{w / 2}" y="{y + size + 90}" text-anchor="middle" font-family="Inter" '
        'font-size="64" font-weight="500" fill="#FFFFFF">VeltOS</text>'
        '</svg>'
    )


def build_grub(root, tmp):
    dest = root / GRUB_DIR
    dest.mkdir(parents=True)
    shutil.copy(SRC / "grub/theme.txt", dest / "theme.txt")
    render(grub_background(), 1920, 1080, dest / "background.png", tmp / "grub.svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        shutil.rmtree(args.out)
    root, tmp = args.out / "root", args.out / "tmp"
    root.mkdir(parents=True)
    tmp.mkdir()
    build_plymouth(root, tmp)
    build_grub(root, tmp)
    defaults = root / "etc/default/grub.d"
    defaults.mkdir(parents=True)
    shutil.copy(SRC / "default/veltos.cfg", defaults / "veltos.cfg")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
