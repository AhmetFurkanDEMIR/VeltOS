#!/usr/bin/env python3
"""Generate the boot artwork of veltos-boot into <out>/root.

    build-assets.py --out build-assets

  * Plymouth theme "veltos": the VeltOS logo with a Windows-style spinner of
    dots underneath, on a near-black background;
  * GRUB theme "veltos" for installed systems: background with the logo and
    name (the menu is drawn by GRUB on top), Inter fonts converted for GRUB
    and a rounded highlight for the selected entry. The live ISO's boot menu
    reuses the fonts and highlight (build/scripts/build-iso.sh).

Requires the Python standard library, rsvg-convert, grub-mkfont and Inter.
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

# GRUB can only use bitmap fonts in its own format (.pf2) at fixed sizes.
INTER_DIR = Path("/usr/share/fonts/opentype/inter")
GRUB_FONTS = [(face, size) for face in ("Regular", "SemiBold") for size in (16, 20, 24)]
# Basic Latin, Latin-1 and Latin Extended-A (Turkish), dashes, arrows.
GRUB_FONT_RANGES = "0x20-0x7E,0xA0-0x17F,0x2010-0x2026,0x2190-0x2193"
# Rounded highlight behind the selected menu entry, as GRUB's 9-slice
# "select_*.png" pixmaps (corners fixed, edges and centre stretched). GRUB
# draws the border slices outside the entry, so themes need an item_spacing
# of at least 2 * SELECT_CORNER or highlights overlap the next entry.
SELECT_SIZE, SELECT_CORNER = 32, 8
SELECT_SLICES = {
    "nw": (0, 0), "n": (1, 0), "ne": (2, 0),
    "w": (0, 1), "c": (1, 1), "e": (2, 1),
    "sw": (0, 2), "s": (1, 2), "se": (2, 2),
}

SPINNER_FRAMES = 60
SPINNER_SIZE = 72
SPINNER_DOTS = 6

# Password prompt images are copied from Plymouth's "spinner" theme
# (plymouth-themes, GPL-2+). Copies, not symlinks: the initramfs contains
# only the selected theme, and the two-step plugin refuses to start when
# lock.png is missing - Plymouth then silently shows its text splash.
SPINNER_DIR = Path("/usr/share/plymouth/themes/spinner")
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
        shutil.copyfile(SPINNER_DIR / name, dest / name)


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


def grub_font_file(face, size):
    return f"inter-{face.lower()}-{size}.pf2"


def grub_font_name(face, size):
    """Name themes use for a font. grub-mkfont builds it from the family
    name, its own Regular/Bold style and the size; Inter's SemiBold file
    reports family "Inter" and style Regular, so it gets its own family name
    or it would clash with Inter Regular."""
    family = "Inter" if face == "Regular" else f"Inter {face}"
    return f"{family} Regular {size}"


def pf2_name(path):
    """Font name stored in a GRUB .pf2 file (the name themes refer to)."""
    data = path.read_bytes()
    at = data.index(b"NAME")
    length = int.from_bytes(data[at + 4:at + 8], "big")
    return data[at + 8:at + 8 + length].rstrip(b"\0").decode()


def build_grub_fonts(dest):
    for face, size in GRUB_FONTS:
        out = dest / grub_font_file(face, size)
        result = subprocess.run(
            ["grub-mkfont", "--name", grub_font_name(face, size).rsplit(" Regular", 1)[0],
             "--size", str(size), "--range", GRUB_FONT_RANGES,
             "--output", str(out), str(INTER_DIR / f"Inter-{face}.otf")],
            capture_output=True, text=True)
        # grub-mkfont warns about every OpenType feature it ignores.
        noise = "WARNING: unsupported font feature parameters"
        for line in result.stderr.splitlines():
            if not line.startswith(noise):
                print(line)
        if result.returncode != 0:
            raise SystemExit(f"grub-mkfont failed for Inter {face} {size}")
        if pf2_name(out) != grub_font_name(face, size):
            raise SystemExit(f"{out.name}: unexpected font name {pf2_name(out)!r}")


def selection_slice(column, row):
    corner, size = SELECT_CORNER, SELECT_SIZE
    middle = size - 2 * corner
    x = (0, corner, corner + middle)[column]
    y = (0, corner, corner + middle)[row]
    w = middle if column == 1 else corner
    h = middle if row == 1 else corner
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="{x} {y} {w} {h}">'
           f'<rect x="0.75" y="0.75" width="{size - 1.5}" height="{size - 1.5}" rx="{corner - 2}" '
           'fill="#4F7CFF" fill-opacity="0.30" stroke="#8FAAFF" stroke-opacity="0.55" '
           'stroke-width="1.5"/></svg>')
    return svg, w, h


def build_grub(root, tmp):
    dest = root / GRUB_DIR
    dest.mkdir(parents=True)
    shutil.copy(SRC / "grub/theme.txt", dest / "theme.txt")
    render(grub_background(), 1920, 1080, dest / "background.png", tmp / "grub.svg")
    build_grub_fonts(dest)
    for name, (column, row) in SELECT_SLICES.items():
        svg, w, h = selection_slice(column, row)
        render(svg, w, h, dest / f"select_{name}.png", tmp / "select.svg")


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
    grub_d = root / "etc/grub.d"
    grub_d.mkdir(parents=True)
    shutil.copy(SRC / "grub.d/35_veltos", grub_d / "35_veltos")
    (grub_d / "35_veltos").chmod(0o755)
    # Copied to /etc/grub.d/10_linux by the postinst (see there).
    wrapper_dir = root / "usr/lib/veltos-boot/grub.d"
    wrapper_dir.mkdir(parents=True)
    shutil.copy(SRC / "grub.d/10_linux", wrapper_dir / "10_linux")
    (wrapper_dir / "10_linux").chmod(0o755)
    shutil.copy(SRC / "plymouth/plymouthd.defaults", root / "usr/share/plymouth/plymouthd.defaults")
    dropin = root / "usr/lib/systemd/system/sddm.service.d"
    dropin.mkdir(parents=True)
    shutil.copy(SRC / "systemd/veltos-plymouth.conf", dropin / "veltos-plymouth.conf")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
