#!/usr/bin/env python3
"""Generate the boot artwork of veltos-boot into <out>/root.

    build-assets.py --out build-assets

  * Plymouth theme "veltos": the VeltOS logo with a Windows-style spinner of
    dots underneath, on a near-black background;
  * GRUB theme "veltos" for installed systems: background with the logo and
    name (the menu is drawn by GRUB on top), Inter fonts converted for GRUB
    and a rounded highlight for the selected entry. The live ISO's boot menu
    reuses the fonts and highlight (build/scripts/build-iso.sh);
  * the start screen's pieces (startscreen/start-screen puts them together
    at the screen's resolution on the installed system): the logo at the
    boot splash's size and the "F1  Boot menu" / "F6  Recovery" hints, as
    raw RGBA pixels.

Requires the Python standard library, rsvg-convert, grub-mkfont and Inter.
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plain_png  # noqa: E402  (copy of build/scripts/plain-png.py)

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
    return inner.replace('id="', f'id="{prefix}').replace("url(#", f"url(#{prefix}")


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


# --- Start screen (GRUB's wait before VeltOS starts) --------------------------------
START_SCREEN_DIR = Path("usr/share/veltos-boot/start-screen")
# The boot splash draws its logo at 168 px (watermark.png); 4K screens get
# everything twice as large.
START_LOGO = 168
# Two key caps in the bottom right corner while GRUB waits: F1 shows the
# boot menu (35_veltos), F6 starts VeltOS Recovery.
HINT_TEXTS = {"en": ("Boot menu", "Recovery"), "tr": ("Önyükleme menüsü", "Kurtarma")}
HINT_ROW, HINT_GAP, HINT_WIDTH = 28, 6, 260
HINT_HEIGHT = 2 * HINT_ROW + HINT_GAP


def hint_svg(labels):
    """The hints as Windows shows such keys: a small key cap with "F1" or
    "F6" and a word next to it, one row each, quiet colours on the boot
    splash's background."""
    rows = []
    for row, (key, label) in enumerate(zip(("F1", "F6"), labels)):
        y = row * (HINT_ROW + HINT_GAP)
        rows.append(
            f'<rect x="0.75" y="{y + 2.75}" width="30.5" height="22.5" rx="5" fill="#FFFFFF" fill-opacity="0.06" '
            'stroke="#6E7BA8" stroke-width="1.5"/>'
            f'<text x="16" y="{y + 18.5}" text-anchor="middle" font-family="Inter" font-weight="600" '
            f'font-size="12" fill="#E6EBFA">{key}</text>'
            f'<text x="40" y="{y + 18.5}" font-family="Inter" font-size="13" fill="#A9B4D6">{label}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{HINT_WIDTH}" height="{HINT_HEIGHT}" '
            f'viewBox="0 0 {HINT_WIDTH} {HINT_HEIGHT}">' + "".join(rows) + '</svg>')


def rgba(png):
    """Width, height and RGBA bytes of an 8-bit RGBA PNG from rsvg-convert."""
    header, idat = None, b""
    for kind, body in plain_png.chunks(png):
        if kind == b"IHDR":
            header = body
        elif kind == b"IDAT":
            idat += body
    width, height = int.from_bytes(header[0:4], "big"), int.from_bytes(header[4:8], "big")
    if header[8:10] != b"\x08\x06":
        raise SystemExit("start screen: rsvg-convert did not write 8-bit RGBA")
    rows = plain_png.unfilter(zlib.decompress(idat), width, height, 4)
    return width, height, b"".join(rows)


def trim_right(width, height, data):
    """Cut transparent columns off the right (the hint's text width varies)."""
    last = 0
    for x in range(width):
        if any(data[(y * width + x) * 4 + 3] for y in range(height)):
            last = x
    keep = last + 1
    return keep, height, b"".join(data[y * width * 4:(y * width + keep) * 4] for y in range(height))


def build_start_screen(root, tmp):
    dest = root / START_SCREEN_DIR
    dest.mkdir(parents=True)
    assets = {"logo": {}, "hint": {lang: {} for lang in HINT_TEXTS}}
    for scale in (1, 2):
        size = START_LOGO * scale
        render(LOGO.read_text(encoding="utf-8"), size, size, tmp / "logo.png", tmp / "logo.svg")
        width, height, data = rgba((tmp / "logo.png").read_bytes())
        name = f"logo-{scale}x.rgba"
        (dest / name).write_bytes(data)
        assets["logo"][str(scale)] = [width, height, name]
        for lang, labels in HINT_TEXTS.items():
            render(hint_svg(labels), HINT_WIDTH * scale, HINT_HEIGHT * scale, tmp / "hint.png", tmp / "hint.svg")
            width, height, data = trim_right(*rgba((tmp / "hint.png").read_bytes()))
            name = f"hint-{lang}-{scale}x.rgba"
            (dest / name).write_bytes(data)
            assets["hint"][lang][str(scale)] = [width, height, name]
    (dest / "assets.json").write_text(json.dumps(assets, indent=1) + "\n", encoding="utf-8")
    libexec = root / "usr/libexec/veltos-boot"
    libexec.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "startscreen/start-screen", libexec / "start-screen")
    (libexec / "start-screen").chmod(0o755)


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
    # GRUB's PNG reader failed on one compressed picture (black boot menu,
    # ISO 20261020-083729): GRUB gets unfiltered, uncompressed PNG files.
    for png in sorted(dest.glob("*.png")):
        png.write_bytes(plain_png.plain(png.read_bytes()))


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
    build_start_screen(root, tmp)
    defaults = root / "etc/default/grub.d"
    defaults.mkdir(parents=True)
    shutil.copy(SRC / "default/veltos.cfg", defaults / "veltos.cfg")
    # Keyboard layout in the initramfs, for the disk encryption password.
    conf_d = root / "etc/initramfs-tools/conf.d"
    conf_d.mkdir(parents=True)
    shutil.copy(SRC / "initramfs/veltos-keymap", conf_d / "veltos-keymap")
    # Font and texts of the disk encryption password screen.
    hooks = root / "usr/share/initramfs-tools/hooks"
    hooks.mkdir(parents=True)
    shutil.copy(SRC / "initramfs/hook", hooks / "veltos-boot")
    (hooks / "veltos-boot").chmod(0o755)
    lib = root / "usr/lib/veltos-boot"
    lib.mkdir(parents=True)
    shutil.copy(SRC / "initramfs/unlock-texts", lib / "unlock-texts")
    (lib / "unlock-texts").chmod(0o755)
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
    build_resolution(root)
    shutil.rmtree(tmp)


def build_resolution(root):
    """The start-up screen at the screen's resolution (resolution/)."""
    libexec = root / "usr/libexec/veltos-boot"
    libexec.mkdir(parents=True, exist_ok=True)
    for name in ("boot-resolution", "boot-resolution-sync"):
        shutil.copy(SRC / "resolution" / name, libexec / name)
        (libexec / name).chmod(0o755)
    user_units = root / "usr/lib/systemd/user"
    user_units.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "resolution/veltos-boot-resolution.service", user_units / "veltos-boot-resolution.service")
    wants = user_units / "plasma-workspace.target.wants"
    wants.mkdir(exist_ok=True)
    (wants / "veltos-boot-resolution.service").symlink_to("../veltos-boot-resolution.service")
    actions = root / "usr/share/polkit-1/actions"
    actions.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "resolution/org.veltos.boot.policy", actions / "org.veltos.boot.policy")


if __name__ == "__main__":
    main()
