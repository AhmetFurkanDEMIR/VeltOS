"""Mouse pointer style and size (Settings > Accessibility > Mouse pointer),
as in Windows 11's "Mouse pointer and touch" page, with VeltOS' default on
top: the pointer follows the colour mode (product owner, 2026-10-31).

Styles:

- "theme" (default): a dark pointer with a white edge in light mode, a
  white pointer with a dark edge in dark mode;
- "white", "black": always that pointer, whatever the mode;
- "custom": Windows 11's custom colour: the pointer's body in a colour of
  the user's choice, made into a cursor theme of the user's own
  (~/.icons/VeltOS-pointer-RRGGBB-SIZE) from the installed
  Fluent theme's Xcursor files.

The choice is kept in ~/.config/veltos/pointer.json; the size is KDE's own
`kcminputrc [Mouse] cursorSize`. `plasma-apply-cursortheme` applies a theme
to the running session (KWin and programs started later); it ignores
`--size` when the theme stays the same (VM, 2026-10-31), so the size is also
written and announced (KGlobalSettings CursorChanged), which KWin follows.
`/usr/libexec/veltos/pointer-style follow light|dark` runs when the colour
mode changes (Settings' and VeltOS AI's light/dark command, app.APPLY_THEME).
"""

import array
import json
import os
import re
import shutil
import struct
import sys
from pathlib import Path

from .devices import config_home, run
from .prefs import as_int, read_value, write_command

STYLES = ("theme", "white", "black", "custom")
WHITE = "Fluent-dark-cursors"       # white pointer, dark edge (veltos-fluent-icons)
BLACK = "Fluent-cursors"            # dark pointer, white edge
# Nominal sizes the Fluent themes are drawn at (veltos-fluent-icons
# tools/cursors.py); the size slider's steps.
SIZES = (24, 30, 36, 48, 60, 72, 96)
DEFAULT_SIZE = 24
CUSTOM_PREFIX = "VeltOS-pointer-"
# Windows 11's "Recommended colours" for a custom pointer, in VeltOS' set.
RECOMMENDED = ("#B4FF00", "#FFE600", "#FF8C00", "#FF3B7F", "#E040FB", "#7C5CFF", "#00B7FF", "#00D9A0")
ICON_DIRS = (Path("/usr/share/icons"),)
# KGlobalSettings::notifyChange(CursorChanged = 5, 0): KWin loads the
# pointer theme and size from kcminputrc again.
CURSOR_CHANGED = ["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
                  "org.kde.KGlobalSettings.notifyChange", "int32:5", "int32:0"]

IMAGE = 0xFFFD0002
COMMENT = 0xFFFE0001
COLOUR = re.compile(r"#[0-9A-Fa-f]{6}")


# --- the user's choice ----------------------------------------------------------------------

def state_file():
    return config_home() / "veltos" / "pointer.json"


def load():
    """{"style", "colour"}: the saved choice, defaults for anything missing."""
    try:
        data = json.loads(state_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    style = data.get("style") if data.get("style") in STYLES else "theme"
    colour = data.get("colour") if isinstance(data.get("colour"), str) and COLOUR.fullmatch(data["colour"]) else ""
    if style == "custom" and not colour:
        colour = RECOMMENDED[0]
    return {"style": style, "colour": colour.upper()}


def save(choice):
    path = state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"style": choice["style"], "colour": choice.get("colour", "")}) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def nearest_size(value):
    value = as_int(value, DEFAULT_SIZE)
    return min(SIZES, key=lambda size: (abs(size - value), size))


def current_size(dirs=None):
    return nearest_size(read_value("kcminputrc", ["Mouse"], "cursorSize", DEFAULT_SIZE, dirs))


def custom_name(colour, size):
    return f"{CUSTOM_PREFIX}{colour.lstrip('#').upper()}-{size}"


def theme_for(style, dark, colour="", size=DEFAULT_SIZE):
    if style == "white":
        return WHITE
    if style == "black":
        return BLACK
    if style == "custom" and COLOUR.fullmatch(colour or ""):
        return custom_name(colour, size)
    return WHITE if dark else BLACK


def state(dirs=None):
    """What the Accessibility page shows."""
    choice = load()
    size = current_size(dirs)
    return {"pointerStyle": choice["style"], "pointerColour": choice["colour"],
            "pointerSize": SIZES.index(size) + 1, "pointerSizes": len(SIZES),
            "pointerColours": list(RECOMMENDED)}


# --- a custom colour ------------------------------------------------------------------------

def luminance(colour):
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def base_for(colour):
    """(theme, body grey, edge grey) the colour is laid on: the white pointer
    (dark edge) for most colours, the dark one (white edge) for dark
    colours, so the edge always stands out from the body."""
    if luminance(colour) < 90:
        return BLACK, 0x33, 0xFF
    return WHITE, 0xFF, 0x25


def recolour_pixels(pixels, colour, body, edge):
    """Xcursor ARGB pixels (premultiplied; opaque ones are plain) with the
    pointer's grey body in `colour`. Only opaque grey pixels change, by how
    far they lie from the edge's grey towards the body's: the body takes
    the colour, the edge stays, the anti-aliased seam between them blends.
    The soft shadow (never opaque) and coloured parts (the busy ring, the
    help mark, the stop sign) stay as drawn."""
    cr, cg, cb = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    span = body - edge
    for index, value in enumerate(pixels):
        if value < 0xFA000000:          # alpha below 250: shadow, edge of the drawing
            continue
        r, g, b = (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
        if max(r, g, b) - min(r, g, b) > 24:
            continue
        t = ((r + g + b) / 3 - edge) / span
        if t <= 0:
            continue
        t = min(t, 1.0)
        r = min(255, max(0, round(r + t * (cr - body))))
        g = min(255, max(0, round(g + t * (cg - body))))
        b = min(255, max(0, round(b + t * (cb - body))))
        pixels[index] = (value & 0xFF000000) | (r << 16) | (g << 8) | b
    return pixels


def read_chunks(data):
    """[(type, subtype, chunk bytes)] of an Xcursor file."""
    magic, _header, _version, count = struct.unpack_from("<4sIII", data, 0)
    if magic != b"Xcur":
        raise ValueError("not an Xcursor file")
    chunks = []
    for index in range(count):
        kind, subtype, position = struct.unpack_from("<III", data, 16 + 12 * index)
        if kind == IMAGE:
            width, height = struct.unpack_from("<II", data, position + 16)
            length = 36 + 4 * width * height
        elif kind == COMMENT:
            length = 20 + struct.unpack_from("<I", data, position + 16)[0]
        else:
            continue
        chunks.append((kind, subtype, data[position:position + length]))
    return chunks


def write_chunks(chunks):
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(chunks))
    position = 16 + 12 * len(chunks)
    toc, body = [], []
    for kind, subtype, chunk in chunks:
        toc.append(struct.pack("<III", kind, subtype, position))
        body.append(chunk)
        position += len(chunk)
    return header + b"".join(toc) + b"".join(body)


def recolour_xcursor(data, colour, body, edge, sizes=None):
    """An Xcursor file's bytes with its images recoloured; images of other
    nominal sizes than `sizes` (when given) are left out."""
    chunks = []
    for kind, subtype, chunk in read_chunks(data):
        if kind == IMAGE:
            if sizes and subtype not in sizes:
                continue
            pixels = array.array("I")
            pixels.frombytes(chunk[36:])
            if sys.byteorder == "big":     # Xcursor is little-endian
                pixels.byteswap()
            recolour_pixels(pixels, colour, body, edge)
            if sys.byteorder == "big":
                pixels.byteswap()
            chunk = chunk[:36] + pixels.tobytes()
        chunks.append((kind, subtype, chunk))
    if not any(kind == IMAGE for kind, _s, _c in chunks):
        return data                         # no image of these sizes: keep the file as it is
    return write_chunks(chunks)


def find_theme(name, icon_dirs=ICON_DIRS):
    for folder in icon_dirs:
        if (Path(folder) / name / "cursors").is_dir():
            return Path(folder) / name
    return None


def icons_home():
    """~/.icons: plasma-apply-cursortheme finds a user's cursor themes only
    there (libXcursor's path); one in ~/.local/share/icons was "not found"
    and the pointer stayed as it was (VM, 2026-10-31)."""
    return Path.home() / ".icons"


def make_custom_theme(colour, size, icon_dirs=ICON_DIRS, home=None):
    """The user's theme for `colour` at `size` (and up to twice that, for
    scaled screens); older custom themes are removed. Returns its name, or
    "" when the Fluent theme it is made from is missing."""
    colour = colour.upper()
    home = Path(home) if home else icons_home()
    name = custom_name(colour, size)
    base_name, body, edge = base_for(colour)
    base = find_theme(base_name, icon_dirs)
    if base is None:
        return ""
    dest = home / name
    sizes = {s for s in SIZES if size <= s <= 2 * size} or {size}
    if not (dest / "cursors").is_dir():
        tmp = home / (name + ".new")
        shutil.rmtree(tmp, ignore_errors=True)
        (tmp / "cursors").mkdir(parents=True)
        for entry in sorted((base / "cursors").iterdir()):
            target = tmp / "cursors" / entry.name
            if entry.is_symlink():
                os.symlink(os.readlink(entry), target)
            elif entry.is_file():
                target.write_bytes(recolour_xcursor(entry.read_bytes(), colour, body, edge, sizes))
        (tmp / "index.theme").write_text(
            f"[Icon Theme]\nName=VeltOS {colour}\nComment=VeltOS custom pointer colour\n"
            f"Inherits={base_name}\n", encoding="utf-8")
        shutil.rmtree(dest, ignore_errors=True)
        os.replace(tmp, dest)
    for old in home.glob(CUSTOM_PREFIX + "*"):
        if old.name != name and old.is_dir():
            shutil.rmtree(old, ignore_errors=True)
    return name


def remove_custom_themes(home=None):
    home = Path(home) if home else icons_home()
    for old in home.glob(CUSTOM_PREFIX + "*"):
        if old.is_dir():
            shutil.rmtree(old, ignore_errors=True)


# --- applying -------------------------------------------------------------------------------

def apply(choice, size, dark, runner=run, icon_dirs=ICON_DIRS, home=None):
    """Make `choice` ({"style", "colour"}) at `size` the session's pointer."""
    size = nearest_size(size)
    style, colour = choice.get("style", "theme"), choice.get("colour", "")
    if style == "custom" and COLOUR.fullmatch(colour or ""):
        name = make_custom_theme(colour, size, icon_dirs, home)
        if not name:
            style, name = "white", WHITE
    else:
        name = theme_for(style, dark, colour, size)
        remove_custom_themes(home)
    ok = runner(write_command("kcminputrc", ["Mouse"], "cursorSize", size))[0] == 0
    # The tool sets the theme for KWin and for programs started later
    # (XCURSOR_THEME/SIZE); it does nothing when the theme is already set.
    ok = runner(["plasma-apply-cursortheme", name, "--size", str(size)], timeout=30)[0] == 0 and ok
    runner(CURSOR_CHANGED)
    runner(["dbus-update-activation-environment", "--systemd",
            f"XCURSOR_THEME={name}", f"XCURSOR_SIZE={size}"])
    return ok


def set_choice(style, colour, size, dark, runner=run, icon_dirs=ICON_DIRS, home=None):
    if style not in STYLES:
        return False
    choice = {"style": style, "colour": (colour or "").upper() if COLOUR.fullmatch(colour or "") else ""}
    if style == "custom" and not choice["colour"]:
        choice["colour"] = load()["colour"] or RECOMMENDED[0]
    save(choice)
    return apply(choice, size, dark, runner, icon_dirs, home)


def follow(mode, runner=run, dirs=None):
    """The colour mode changed: the pointer follows it with the "theme" style."""
    choice = load()
    if choice["style"] != "theme":
        return True
    return apply(choice, current_size(dirs), mode == "dark", runner)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 2 and argv[0] == "follow" and argv[1] in ("light", "dark"):
        return 0 if follow(argv[1]) else 1
    print("usage: pointer-style follow light|dark", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
