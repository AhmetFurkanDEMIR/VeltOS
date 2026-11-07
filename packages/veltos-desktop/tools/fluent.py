"""VeltOS widget style, window frames and panel theme, derived from Fluent-kde.

Fluent-kde (GPL-3.0, https://github.com/vinceliuice/Fluent-kde) is pinned in
upstream.json and unpacked into upstream/ by build/scripts/fetch-upstream.py.
Its "round" variants become the VeltOS themes:

  Kvantum widget style    usr/share/Kvantum/VeltOS/VeltOS{,Dark}.{kvconfig,svg}
  Aurorae window frames   usr/share/aurorae/themes/VeltOS{,-Dark}/
  Plasma desktop theme    usr/share/plasma/desktoptheme/VeltOS{,-Dark}/
  colour schemes          VeltOS{Light,Dark} (returned as KDE config groups)

Changes from upstream: Fluent's Windows blue (#0078d4) becomes the VeltOS
accent; artwork showing other brands (the Windows logo used as "start" icon,
the Manjaro logo, a "KDE Desktop" badge) is dropped; translucent application
windows are off (blurring what is behind every window costs GPU time on
weak hardware; menus and panels keep their blur); window titles are
left-aligned like on Windows 11; window frames are the opaque ("solid")
variants and inactive windows are not faded.
"""

import gzip
import json
import re
import shutil
from pathlib import Path

# VeltOS accent colours (brand blue #4F7CFF; a darker shade on light
# backgrounds so white text on the accent stays readable).
ACCENTS = {
    "light": {"accent": (47, 94, 230), "hover": (79, 124, 255),
              "alt": (92, 132, 240), "link": (36, 86, 214)},
    "dark": {"accent": (79, 124, 255), "hover": (122, 156, 255),
             "alt": (110, 150, 255), "link": (122, 156, 255)},
}
# Fluent's accent in its SVG artwork and Kvantum configuration.
FLUENT_BLUE = "#0078d4"

KVANTUM = {"VeltOS": ("Fluent-round", "light"), "VeltOSDark": ("Fluent-roundDark", "dark")}
KVANTUM_DIR = "VeltOS"
KVANTUM_GENERAL = {
    "author": "Vince Liuice (Fluent), based on KvAdapta by Tsu Jan; VeltOS colours",
    "comment": "VeltOS application style (derived from Fluent-round)",
    "translucent_windows": "false",
    "blurring": "false",
    "popup_blurring": "true",
    # Windows does not fade the contents of inactive windows.
    "no_inactiveness": "true",
}

# The "solid" variants: Fluent's default frames are 75 % opaque and meant to
# be blurred; without blur (software rendering, VMs) they show the desktop
# through every title bar, and made inactive windows look washed out.
AURORAE = {"VeltOS": ("Fluent-round-light-solid", "light"),
           "VeltOS-Dark": ("Fluent-round-dark-solid", "dark")}
AURORAE_GENERAL = {"TitleAlignment": "Left", "LeftButtons": "M", "RightButtons": "IAX",
                   "UseTextShadow": "false"}
# Windows 11 title bar: 32 px high, the minimise / maximise / close buttons
# 46 x 32 and flush with the top right corner, the app icon and the title on
# the left. A 1 px bottom border: with 0, a 1 px seam between the window
# contents and the rounded bottom edge shows the desktop through (VM test).
AURORAE_LAYOUT = {"BorderBottom": "1",
                  "ButtonWidth": "46", "ButtonHeight": "32", "ButtonSpacing": "0",
                  "ButtonMarginTop": "0", "ExplicitButtonSpacer": "0", "ButtonWidthMenu": "28",
                  "TitleHeight": "32", "TitleEdgeTop": "0", "TitleEdgeBottom": "0",
                  "TitleEdgeLeft": "6", "TitleEdgeRight": "0",
                  "TitleEdgeTopMaximized": "0", "TitleEdgeBottomMaximized": "0",
                  "TitleEdgeLeftMaximized": "6", "TitleEdgeRightMaximized": "0",
                  "TitleBorderLeft": "6", "TitleBorderRight": "8"}
AURORAE_TEXT = {"light": {"ActiveTextColor": "27,29,36", "InactiveTextColor": "138,143,156"},
                "dark": {"ActiveTextColor": "242,243,247", "InactiveTextColor": "143,148,166"}}
# Caption button drawing (VeltOS's own, replacing Fluent's round buttons):
# glyph colour, inactive glyph colour, hover and pressed backgrounds.
CAPTION_COLOURS = {
    "light": {"glyph": "#1b1d24", "inactive": "#8a8f9c", "hover": ("#000000", 0.06),
              "pressed": ("#000000", 0.035)},
    "dark": {"glyph": "#f2f3f7", "inactive": "#8f94a6", "hover": ("#ffffff", 0.08),
             "pressed": ("#ffffff", 0.05)},
}
CLOSE_RED = "#c42b1c"
# Title bar colours like Windows 11's Mica: the window background of the
# VeltOS apps (Settings, File Explorer, Task Manager), so the title bar and
# the window read as one surface; inactive windows a shade lighter (light)
# or darker (dark). Fluent's solid frames are white / #202020.
FRAME_COLOURS = {
    "light": {"#ffffff": "#f3f5fa", "#f5f5f5": "#f3f5fa"},
    "dark": {"#202020": "#1c1d26", "#2c2c2c": "#1c1d26"},
}
# Fluent lays a tint over its frames (dark: 5 % white, light: 25 % of a cyan
# white), so the title bar, the side edges and the bottom edge came out a
# shade lighter than the window (#272830 around #1c1d26): a visible band
# under every window in dark mode (product owner, 2026-10-26). The tints are
# switched off; inactive windows keep the same colour too (their caption
# text is dimmed instead), so no edge ever stands apart from the window.
FRAME_TINTS = {
    "light": {"opacity:0.25;fill:#f3fdff": "opacity:0;fill:#f3fdff"},
    "dark": {"opacity:0.05;fill:#ffffff": "opacity:0;fill:#ffffff"},
}
# Fluent's frames have a 1 px line around the window (dark: #686868 at 50 %,
# a light ring; light: black at 15 %, a grey one). The product owner wants
# no line at all, the edge in the window's own colour (2026-11-02): the line
# is painted in the frame colour, so the window simply ends where its
# shadow begins.
FRAME_BORDERS = {
    "light": {"opacity:0.15;fill:#000000": "opacity:1;fill:#f3f5fa"},
    "dark": {"opacity:0.5;fill:#686868": "opacity:1;fill:#1c1d26"},
}
CAPTION_W, CAPTION_H = 46, 32
WINDOW_RADIUS = 8

DESKTOPTHEMES = {"VeltOS": "light", "VeltOS-Dark": "dark"}
# Plasma theme files that show other projects' or companies' logos.
DESKTOPTHEME_DROP = ("icons/start.svgz", "icons/manjaro.svgz", "widgets/branding.svgz")
# Taskbar background opacity without the blur effect (no 3D acceleration):
# see-through like Windows 11 and still readable. With blur, the translucent
# backgrounds get ACRYLIC below.
PANEL_OPACITY = {"widgets/panel-background.svgz": 0.86}
# Windows 11's acrylic, used where KWin can blur (Plasma then takes the
# translucent/ backgrounds; veltos-desktop turns KWin's blur and contrast
# effects on everywhere, also where KWin renders in software, with a blur
# strength of 8): Start, search, Quick Settings, the other flyouts and the
# taskbar in these colours over the blurred desktop or windows behind,
# which KWin's contrast effect first brightens (light) or darkens (dark)
# and makes more colourful, so the text stays readable while what is
# behind shows through. History: 85 % colour (2026-11-02) was nearly
# opaque; 52-60 % with KWin's strongest blur (15) still looked opaque over
# a window, because everything behind was smeared into one colour (product
# owner, 2026-11-07: "see-through also with something behind"). With
# blur 8 and these values the windows and pictures behind show as soft
# colour shapes, as through Windows 11's acrylic (dev VM, over VeltOS
# Photos; out/vm/pblur-compare.png). Light mode brightened the desktop
# behind 1.4 times at first: over the pale corner of a light wallpaper
# that clipped to white and the calendar, Quick Settings and the
# hidden-icons flyout looked opaque; 1.15 keeps the wallpaper's tint and
# shapes (product owner, 2026-11-07).
ACRYLIC = {
    "light": {"popup": ("#f3f3f3", 0.45), "taskbar": ("#eeeeee", 0.55),
              "contrast": ["enabled=true", "contrast=0.7", "intensity=1.15", "saturation=1.8"]},
    "dark": {"popup": ("#202020", 0.45), "taskbar": ("#1c1c1c", 0.55),
             "contrast": ["enabled=true", "contrast=0.75", "intensity=0.5", "saturation=2.2"]},
}
ACRYLIC_FILES = {"translucent/dialogs/background.svgz": "popup",
                 "translucent/widgets/panel-background.svgz": "taskbar"}
FRAME_PIECES = ("center", "top", "bottom", "left", "right", "topleft", "topright", "bottomleft", "bottomright")

COLOR_SCHEMES = {
    "VeltOSLight": {"source": "FluentLight.colors", "name": "VeltOS Light", "variant": "light"},
    "VeltOSDark": {"source": "FluentDark.colors", "name": "VeltOS Dark", "variant": "dark"},
}

ATTRIBUTION = "Derived from Fluent-kde by Vince Liuice (GPL-3.0) for VeltOS"


def hex_colour(rgb):
    return "#%02x%02x%02x" % rgb


def rgb_text(rgb):
    return ",".join(str(c) for c in rgb)


def recolour(text, variant, what):
    """Replace Fluent's accent with the VeltOS accent; fail if it is missing,
    so an upstream palette change is noticed instead of shipping Windows blue."""
    new, count = re.subn(re.escape(FLUENT_BLUE), hex_colour(ACCENTS[variant]["accent"]),
                         text, flags=re.IGNORECASE)
    if count == 0:
        raise SystemExit(f"{what}: Fluent accent {FLUENT_BLUE} not found; update tools/fluent.py")
    return new


def set_ini_keys(text, section, values, what, add=()):
    """Set keys inside one [section] of an INI-style file, keeping everything
    else byte for byte. Every key must already exist in that section,
    except the keys named in `add`, which are added after the header."""
    lines = text.splitlines()
    current = None
    header = None
    seen = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            current = stripped
            if current == section:
                header = i
            continue
        if current == section and "=" in stripped:
            key = stripped.split("=", 1)[0]
            if key in values:
                lines[i] = f"{key}={values[key]}"
                seen.add(key)
    missing = set(values) - seen - set(add)
    if missing or header is None:
        raise SystemExit(f"{what}: keys {sorted(missing)} not found in {section}")
    lines[header + 1:header + 1] = [f"{key}={values[key]}" for key in values
                                    if key in add and key not in seen]
    return "\n".join(lines) + "\n"


# --- Kvantum -------------------------------------------------------------------

# Menus: Fluent draws them 75 % opaque for blur behind them; without blur
# (software rendering, VMs, KWin's blur off) the text of the window behind
# showed through and made menus hard to read (Start's quick link menu, VM
# 2026-10-21). Windows 11's menus are nearly opaque acrylic.
MENU_OPACITY = 0.94


def set_menu_opacity(svg, opacity, name="svg"):
    """Set the opacity of the menu background pieces (menu-normal and its
    eight edges and corners) of a Kvantum SVG."""
    pieces = list(re.finditer(r'<(path|g)\b[^>]*\bid="menu-normal(?:-[a-z]+)?"[^>]*>', svg))
    if len(pieces) != 9:
        raise SystemExit(f"{name}: expected 9 menu background pieces, found {len(pieces)}")
    out, pos = [], 0
    for match in pieces:
        end = match.end() if match.group(1) == "path" else svg.index("</g>", match.end())
        out.append(svg[pos:match.start()])
        out.append(re.sub(r"(?<![-\w])opacity:[0-9.]+", f"opacity:{opacity}", svg[match.start():end]))
        pos = end
    out.append(svg[pos:])
    return "".join(out)


def _style_of(element):
    match = re.search(r'\bstyle="([^"]*)"', element)
    return match.group(1) if match else ""


def _with_opacity(element, opacity):
    """The element with its style's opacity set (replaced or added)."""
    style = _style_of(element)
    if not style and "style=" not in element:
        return re.sub(r"^<(\w+)", rf'<\1 style="opacity:{opacity}"', element)
    if re.search(r"(?<![-\w])opacity:[0-9.]+", style):
        new_style = re.sub(r"(?<![-\w])opacity:[0-9.]+", f"opacity:{opacity}", style)
    else:
        new_style = f"opacity:{opacity};" + style
    return element.replace(f'style="{style}"', f'style="{new_style}"', 1)


def uniform_menu_band(svg, opacity, name="svg"):
    """Give the band in Kvantum's menu shadow the menu's own opacity.

    Fluent draws a menu as a square-cornered body (menu-normal, made
    `opacity` by set_menu_opacity) inside a rounded band of the same colour
    at 75 % that is part of the shadow pieces (menu-shadow-*), meant to be
    seen through blur. Without blur (VMs, KWin's blur off) the two showed
    as two boxes, one inside the other, lighter or darker than each other
    (product owner, 2026-10-22). The band's solid fill (75 %) now has the
    body's opacity, so menu and band read as one rounded box; the soft
    shadow gradients and the thin edge lines stay as they are."""
    pieces = list(re.finditer(r'<(path|g|rect)\b[^>]*\bid="menu-shadow-(?!hint)[a-z]+"[^>]*>', svg))
    if not pieces:
        raise SystemExit(f"{name}: no menu shadow pieces")
    changed = 0

    def even_out(element_match):
        nonlocal changed
        element = element_match.group(0)
        style = _style_of(element)
        fill = re.search(r"(?<![-\w])fill:([^;]+)", style)
        level = re.search(r"(?<![-\w])opacity:([0-9.]+)", style)
        if (fill is None or fill.group(1).startswith("url(") or fill.group(1).lower() in ("#000000", "#000")
                or level is None or float(level.group(1)) < 0.7):
            return element
        changed += 1
        return _with_opacity(element, opacity)

    out, pos = [], 0
    for match in pieces:
        out.append(svg[pos:match.start()])
        if match.group(1) == "g":
            end = svg.index("</g>", match.end())
            out.append(match.group(0) + re.sub(r"<(?:path|rect)\b[^>]*/?>", even_out, svg[match.end():end]))
        else:
            end = match.end()
            out.append(re.sub(r"<(?:path|rect)\b[^>]*/?>", even_out, match.group(0)))
        pos = end
    out.append(svg[pos:])
    if changed == 0:
        raise SystemExit(f"{name}: no band found in the menu shadow pieces; update tools/fluent.py")
    return "".join(out)


def build_kvantum(upstream, root):
    src = upstream / "Kvantum/Fluent-round"
    dest = root / "usr/share/Kvantum" / KVANTUM_DIR
    dest.mkdir(parents=True, exist_ok=True)
    for name, (fluent, variant) in KVANTUM.items():
        svg = (src / f"{fluent}.svg").read_text(encoding="utf-8")
        svg = set_menu_opacity(recolour(svg, variant, f"{fluent}.svg"), MENU_OPACITY, f"{fluent}.svg")
        svg = uniform_menu_band(svg, MENU_OPACITY, f"{fluent}.svg")
        (dest / f"{name}.svg").write_text(svg, encoding="utf-8")
        config = (src / f"{fluent}.kvconfig").read_text(encoding="utf-8")
        config = recolour(config, variant, f"{fluent}.kvconfig")
        config = set_ini_keys(config, "[%General]", KVANTUM_GENERAL, f"{fluent}.kvconfig")
        if variant == "light":
            # Fluent Light's palette highlight is translucent black; Qt and
            # Kirigami cannot use a translucent highlight and fall back to
            # Qt's default blue. Use the accent, as Fluent Dark does.
            accent = hex_colour(ACCENTS[variant]["accent"])
            config = set_ini_keys(config, "[GeneralColors]", {
                "highlight.color": accent,
                "inactive.highlight.color": accent + "74",
                "highlight.text.color": "#ffffff",
            }, f"{fluent}.kvconfig")
        # Plain lists without zebra stripes, as in Windows 11 File Explorer.
        base = re.search(r"^base\.color=(\S+)", config, re.M)
        if base is None:
            raise SystemExit(f"{fluent}.kvconfig: no base colour")
        config = set_ini_keys(config, "[GeneralColors]", {"alt.base.color": base.group(1)},
                              f"{fluent}.kvconfig")
        (dest / f"{name}.kvconfig").write_text(config, encoding="utf-8")


# --- Aurorae window decoration ---------------------------------------------------

def build_aurorae(upstream, root):
    for name, (fluent, variant) in AURORAE.items():
        dest = root / "usr/share/aurorae/themes" / name
        # Licence and authors are recorded in debian/copyright.
        shutil.copytree(upstream / "aurorae" / fluent, dest,
                        ignore=shutil.ignore_patterns("LICENSE", "AUTHORS"))
        (dest / f"{fluent}rc").rename(dest / f"{name}rc")
        rc = dest / f"{name}rc"
        text = set_ini_keys(rc.read_text(encoding="utf-8"), "[General]",
                            dict(AURORAE_GENERAL, **AURORAE_TEXT[variant]), rc.name)
        rc.write_text(set_ini_keys(text, "[Layout]", AURORAE_LAYOUT, rc.name, add=("ButtonWidthMenu",)),
                      encoding="utf-8")
        for kind in ("minimize", "maximize", "restore", "close"):
            (dest / f"{kind}.svg").write_text(caption_svg(kind, variant), encoding="utf-8")
        metadata = (dest / "metadata.desktop").read_text(encoding="utf-8")
        metadata = set_ini_keys(metadata, "[Desktop Entry]", {
            "Name": name.replace("-", " "),
            "X-KDE-PluginInfo-Name": name,
            "X-KDE-PluginInfo-Author": "Vince Liuice (Fluent); VeltOS Developers",
        }, f"{fluent}/metadata.desktop")
        (dest / "metadata.desktop").write_text(metadata, encoding="utf-8")
        decoration = dest / "decoration.svg"
        frame = decoration.read_text(encoding="utf-8")
        for old, new in FRAME_COLOURS[variant].items():
            if f"fill:{old}" not in frame:
                raise SystemExit(f"{fluent}/decoration.svg: frame colour {old} not found")
            frame = frame.replace(f"fill:{old}", f"fill:{new}")
        for old, new in FRAME_TINTS[variant].items():
            if old not in frame:
                raise SystemExit(f"{fluent}/decoration.svg: frame tint {old} not found")
            frame = frame.replace(old, new)
        for old, new in FRAME_BORDERS[variant].items():
            if old not in frame:
                raise SystemExit(f"{fluent}/decoration.svg: frame border {old} not found")
            frame = frame.replace(old, new)
        decoration.write_text(frame, encoding="utf-8")
        # The window buttons are monochrome; only the frame may carry the accent.
        for svg in dest.glob("*.svg"):
            text = svg.read_text(encoding="utf-8")
            if re.search(re.escape(FLUENT_BLUE), text, flags=re.IGNORECASE):
                svg.write_text(recolour(text, variant, svg.name), encoding="utf-8")


def caption_glyph(kind, x, colour, opacity=1.0):
    """The thin line glyph of a caption button whose left edge is at x
    (Windows 11 proportions: 10 px wide, 1 px lines, centred)."""
    cx, cy = x + CAPTION_W / 2, CAPTION_H / 2
    stroke = f'fill="none" stroke="{colour}" stroke-width="1" opacity="{opacity:g}"'
    if kind == "minimize":
        # On whole pixels: a line across two pixel rows looks grey and blurred.
        return f'<rect x="{cx - 5:g}" y="{cy:g}" width="10" height="1" fill="{colour}" opacity="{opacity:g}"/>'
    if kind == "maximize":
        return f'<rect x="{cx - 4.5:g}" y="{cy - 4.5:g}" width="9" height="9" rx="1.5" {stroke}/>'
    if kind == "restore":
        return (f'<rect x="{cx - 4.5:g}" y="{cy - 2.5:g}" width="7" height="7" rx="1" {stroke}/>'
                f'<path d="M {cx - 2.5:g} {cy - 2.5:g} V {cy - 3.5:g} A 1 1 0 0 1 {cx - 1.5:g} {cy - 4.5:g} '
                f'H {cx + 3.5:g} A 1 1 0 0 1 {cx + 4.5:g} {cy - 3.5:g} V {cy + 1.5:g} '
                f'A 1 1 0 0 1 {cx + 3.5:g} {cy + 2.5:g} H {cx + 2.5:g}" {stroke}/>')
    if kind == "close":
        return (f'<path d="M {cx - 5:g} {cy - 5:g} L {cx + 5:g} {cy + 5:g} M {cx + 5:g} {cy - 5:g} '
                f'L {cx - 5:g} {cy + 5:g}" {stroke} stroke-linecap="round"/>')
    raise ValueError(kind)


def caption_background(kind, x, colour, opacity, maximized=False):
    """Hover/pressed background; the close button rounds the window's top
    right corner, as on Windows 11 (square on maximised windows, whose
    corners are square)."""
    if kind == "close" and not maximized:
        r = WINDOW_RADIUS
        return (f'<path d="M {x} 0 H {x + CAPTION_W - r} A {r} {r} 0 0 1 {x + CAPTION_W} {r} '
                f'V {CAPTION_H} H {x} Z" fill="{colour}" opacity="{opacity:g}"/>')
    return f'<rect x="{x}" y="0" width="{CAPTION_W}" height="{CAPTION_H}" fill="{colour}" opacity="{opacity:g}"/>'


def caption_svg(kind, variant):
    """An Aurorae button SVG: the five states Aurorae reads (active,
    inactive, hover, pressed, deactivated), side by side, each the full
    46 x 32 button (an invisible rectangle keeps the size). The close
    button also has square hover/pressed pictures for maximised windows
    (hover-maximized, pressed-maximized: read by VeltOS' change to KWin's
    AuroraeButton.qml, plasma-overrides/aurorae.json), and every state has
    an "-ondark" twin with white glyphs for the Office apps' coloured
    title bars (same change)."""
    red = kind == "close"

    def states_for(c, suffix):
        base = [
            ("active", c["glyph"], 1.0, None),
            ("inactive", c["inactive"], 1.0, None),
            ("hover", "#ffffff" if red else c["glyph"], 1.0, (CLOSE_RED, 1.0) if red else c["hover"]),
            ("pressed", "#ffffff" if red else c["glyph"], 0.7 if red else 0.8,
             (CLOSE_RED, 0.85) if red else c["pressed"]),
            ("deactivated", c["glyph"], 0.3, None),
        ]
        result = [(f"{state}{suffix}", colour, opacity, background) for state, colour, opacity, background in base]
        if red:
            result += [(f"{state}-maximized{suffix}", colour, opacity, background)
                       for state, colour, opacity, background in base if state in ("hover", "pressed")]
        return result

    # The "-ondark" states (white glyphs, light hover) are used on the
    # app-coloured title bars of the Office apps (plasma-overrides/aurorae.json).
    states = states_for(CAPTION_COLOURS[variant], "") + states_for(CAPTION_COLOURS["dark"], "-ondark")
    parts = []
    for i, (state, colour, opacity, background) in enumerate(states):
        x = i * (CAPTION_W + 2)
        group = [f'<g id="{state}-center">',
                 f'<rect x="{x}" y="0" width="{CAPTION_W}" height="{CAPTION_H}" fill="#000000" opacity="0.001"/>']
        if background:
            group.append(caption_background(kind, x, *background, maximized="-maximized" in state))
        group.append(caption_glyph(kind, x, colour, opacity))
        group.append("</g>")
        parts.append("".join(group))
    width = len(states) * (CAPTION_W + 2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{CAPTION_H}" '
            f'viewBox="0 0 {width} {CAPTION_H}">\n<!-- VeltOS caption button "{kind}" ({variant}), '
            f'Windows 11 proportions. SPDX-License-Identifier: GPL-3.0-or-later -->\n'
            + "\n".join(parts) + "\n</svg>\n")


# --- Plasma desktop theme (panel, popups, widgets) -------------------------------

def read_svgz(path):
    return gzip.decompress(path.read_bytes()).decode("utf-8")


def write_svgz(path, text):
    # mtime=0: reproducible output.
    path.write_bytes(gzip.compress(text.encode("utf-8"), mtime=0))


def desktop_entry_groups(path):
    """[group] -> lines of a metadata.desktop, except [Desktop Entry]."""
    groups, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            current = stripped
            groups[current] = []
        elif current and stripped and not stripped.startswith("#"):
            groups[current].append(stripped)
    groups.pop("[Desktop Entry]", None)
    return groups


def set_background_opacity(svg, opacity, name="svg"):
    """Set the opacity of the frame pieces (the elements filled with the
    colour scheme's background) of a Plasma frame SVG."""
    def fix(match):
        tag = match.group(0)
        if re.search(r"(?<![-\w])opacity:", tag):
            return re.sub(r"(?<![-\w])opacity:[0-9.]+", f"opacity:{opacity}", tag)
        if 'style="' in tag:
            return tag.replace('style="', f'style="opacity:{opacity};', 1)
        return re.sub(r"^<(\w+)", rf'<\1 style="opacity:{opacity}"', tag)
    result, count = re.subn(r'<(?:rect|path)\b[^>]*class="ColorScheme-Background"[^>]*>', fix, svg)
    if count == 0:
        raise SystemExit(f"{name}: no frame pieces to make see-through")
    return result


def acrylic(svg, colour, opacity, name="svg"):
    """Paint the frame pieces of a translucent Plasma background (the
    elements in the scheme's background colour or Fluent's white) in one
    colour and opacity (ACRYLIC). Shadows, the dark mode's dark rim
    (#000000) and empty helper rectangles stay."""
    count = 0

    def piece(group):
        def paint(element):
            nonlocal count
            tag = element.group(0)
            style = re.search(r'style="([^"]*)"', tag)
            text = style.group(1) if style else ""
            if "fill:none" in text or "fill:#000000" in text or 'fill="none"' in tag:
                return tag
            if not ('class="ColorScheme-Background"' in tag or "currentColor" in tag
                    or re.search(r"fill:#(?:ffffff|f9fafc)\b", text)):
                return tag
            count += 1
            text = re.sub(r"(?<![-\w])fill:[^;]*;?", "", text)
            text = re.sub(r"(?<![-\w])opacity:[0-9.]+;?", "", text).strip(";")
            text = f"fill:{colour};opacity:{opacity}" + (f";{text}" if text else "")
            tag = tag.replace(' class="ColorScheme-Background"', "")
            tag = re.sub(r'\sfill="currentColor"', "", tag)
            if style:
                return tag.replace(style.group(0), f'style="{text}"')
            return re.sub(r"^<(\w+)", rf'<\1 style="{text}"', tag)
        return re.sub(r"<(?:rect|path)\b[^>]*>", paint, group.group(0))
    result = re.sub(r'<g\b[^>]*id="(?:%s)"[^>]*>.*?</g>' % "|".join(FRAME_PIECES), piece, svg, flags=re.S)
    if count == 0:
        raise SystemExit(f"{name}: no frame pieces to paint (Fluent changed?)")
    return result


def drop_popup_outline(svg, name="svg"):
    """Fluent's popup frames draw a line in the text colour inside their
    shadow pieces (shadow-top and shadow-topleft; the other edges and
    corners are <use> copies of them): white around Start and the flyouts
    in dark mode, black in light mode (product owner, 2026-10-23: no frame).
    Those lines become invisible; the shadow itself stays. Returns the SVG
    and the number of lines found."""
    count = 0

    def clear_group(group):
        nonlocal count

        def clear(element):
            nonlocal count
            count += 1
            tag = element.group(0)
            if re.search(r"(?<![-\w])opacity:", tag):
                return re.sub(r"(?<![-\w])opacity:[0-9.]+", "opacity:0", tag)
            return tag.replace('class="ColorScheme-Text"', 'class="ColorScheme-Text" opacity="0"', 1)
        return re.sub(r'<(?:rect|path)\b[^>]*class="ColorScheme-Text"[^>]*>', clear, group.group(0))
    result = re.sub(r'<g\b[^>]*id="shadow-(?:top|topleft)"[^>]*>.*?</g>', clear_group, svg, flags=re.S)
    return result, count


def drop_scrollbar_separator(svg, name="svg"):
    """Plasma's scroll bars draw a 1 px line beside themselves when the
    theme's scrollbar.svg has the element "private-hint-show-separator"
    (plasma-framework ScrollBar.qml); Fluent has it, so Start showed a
    vertical line left of its scroll bar (product owner, 2026-10-26: no
    line, as Windows 11's scroll bars have none)."""
    result, count = re.subn(r'<(\w+)\b[^>]*\bid="private-hint-show-separator"[^>]*?(?:/>|>.*?</\1>)',
                            "", svg, flags=re.S)
    if count != 1:
        raise SystemExit(f"{name}: scroll bar separator hint not found (Fluent changed?)")
    return result


# The rim takes the popup's own colour: a 35 % black edge (2026-10-28)
# showed as a black frame around Start and the flyouts in dark mode, and a
# transparent one left the shadow's darkest pixel as a thin dark line
# (product owner, 2026-11-02: no frame, no border). The edge is part of the
# popup; the shadow pieces stay outside it.
DARK_RIM = "fill:currentColor"


def dark_popup_rim(svg, name="svg"):
    """Dark mode: Fluent's see-through popup frame (translucent/, used when
    KWin can blur, so on real graphics cards) draws a 12 % white line along
    the outer edge of its frame pieces ("top", "topleft"; the other edges
    and corners are <use> copies). Over the blurred dark desktop it showed
    as a white frame around Start, search, the flyouts and tooltips
    (product owner, 2026-10-28: no white frame in dark mode; seen in the VM
    once blur was loaded). The line becomes part of the popup: the colour
    and opacity of the frame piece beside it (DARK_RIM; `acrylic` paints
    both alike). Returns the SVG and the number of lines changed."""
    count = 0

    def darken_group(group):
        nonlocal count
        piece = re.search(r'<(?:rect|path)\b[^>]*class="ColorScheme-Background"[^>]*>', group.group(0))
        opacity = re.search(r"(?<![-\w])opacity:([0-9.]+)", piece.group(0)) if piece else None
        style = DARK_RIM + (f";opacity:{opacity.group(1)}" if opacity else "")

        def darken(element):
            nonlocal count
            tag = element.group(0)
            if "class=" in tag:
                return tag
            count += 1
            tag = re.sub(r'style="[^"]*"', f'style="{style}"', tag, count=1)
            return re.sub(r"^<(\w+)", r'<\1 class="ColorScheme-Background"', tag)
        return re.sub(r'<(?:rect|path)\b[^>]*style="[^"]*fill:#ffffff;opacity:[0-9.]+[^"]*"[^>]*>', darken,
                      group.group(0))
    result = re.sub(r'<g\b[^>]*id="(?:top|topleft|topright|bottom|bottomleft|bottomright|left|right)"[^>]*>.*?</g>',
                    darken_group, svg, flags=re.S)
    return result, count


LIGHT_POPUP = "#ffffff"
# Light mode's taskbar: an airy near-white instead of the scheme's grey
# window colour (product owner, 2026-11-01: "not grey in light mode").
LIGHT_TASKBAR = "#f9fafc"


def white_popup(svg, name="svg", colour=LIGHT_POPUP):
    """Light mode: popups (Start, search, the flyouts) in the white of VeltOS
    Settings' cards instead of the colour scheme's grey window colour, which
    they took through `ColorScheme-Background` (product owner, 2026-10-23:
    Start and search in one colour that matches the theme, Settings' white).
    Only the popup frame changes; programs keep the scheme's colours."""
    def paint(match):
        tag = match.group(0).replace(' class="ColorScheme-Background"', "")
        tag = re.sub(r"fill:currentColor", f"fill:{colour}", tag)
        if f"fill:{colour}" not in tag:
            tag = tag.replace('style="', f'style="fill:{colour};', 1)
        return tag
    result, count = re.subn(r'<(?:rect|path)\b[^>]*class="ColorScheme-Background"[^>]*>', paint, svg)
    if count == 0:
        raise SystemExit(f"{name}: no popup background to make white")
    return result


def build_desktoptheme(upstream, root, name, variant):
    """The VeltOS Plasma theme (taskbar, Start, flyouts) from Fluent-kde.

    Without a `colors` file of its own (Fluent ships one): Plasma then takes
    its colours from the system colour scheme, the same VeltOS Light/Dark
    scheme the global theme selects, and with it the accent colour the user
    chooses in Settings. With the file, the taskbar, Start and the flyouts
    kept VeltOS blue whatever accent was chosen (VM, 2026-10-22)."""
    base = upstream / "plasma/desktoptheme/Fluent-round"
    dest = root / "usr/share/plasma/desktoptheme" / name
    shutil.copytree(base, dest, ignore=shutil.ignore_patterns("metadata.desktop"))
    # As Fluent's install.sh: light SVGs on top of the shared ones. Then the
    # "solid" (opaque) panel and popup backgrounds as the normal ones: Plasma
    # only uses translucent/ when the blur effect is available, so popups
    # are see-through with blur (OpenGL) and opaque without it (software
    # rendering), instead of see-through and unreadable.
    if variant == "light":
        overlays = ["Fluent-round-light", "Fluent-round-light-solid"]
    else:
        overlays = ["Fluent-round-solid"]
    for overlay in overlays:
        src = upstream / "plasma/desktoptheme" / overlay
        for path in sorted(src.rglob("*.svgz")):
            target = dest / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target)
    for rel in DESKTOPTHEME_DROP:
        (dest / rel).unlink()
    recoloured = 0
    outlines = 0
    rims = 0
    separators = 0
    for path in sorted(dest.rglob("*.svgz")):
        text = read_svgz(path)
        if re.search(re.escape(FLUENT_BLUE), text, flags=re.IGNORECASE):
            text = recolour(text, variant, str(path))
            recoloured += 1
        if path.name in ("background.svgz", "tooltip.svgz"):
            text, found = drop_popup_outline(text, str(path))
            outlines += found
            if variant == "dark":
                text, found = dark_popup_rim(text, str(path))
                rims += found
        if variant == "light" and path.parent.name == "dialogs" and path.name == "background.svgz":
            text = white_popup(text, str(path))
        if path.parent.name == "widgets" and path.name == "scrollbar.svgz" and "private-hint-show-separator" in text:
            text = drop_scrollbar_separator(text, str(path))
            separators += 1
        write_svgz(path, text)
    if variant == "dark" and rims == 0:
        raise SystemExit(f"{name}: no white rim found in the dark popup frames (Fluent changed?)")
    if outlines == 0:
        raise SystemExit(f"{name}: no popup outline found (Fluent changed?)")
    if separators == 0:
        raise SystemExit(f"{name}: no scroll bar separator hint found (Fluent changed?)")
    (dest / "colors").unlink(missing_ok=True)       # follow the system scheme (docstring)
    for rel, opacity in PANEL_OPACITY.items():
        svg = set_background_opacity(read_svgz(dest / rel), opacity, rel)
        if variant == "light":
            svg = white_popup(svg, rel, LIGHT_TASKBAR)
        write_svgz(dest / rel, svg)
    for rel, part in ACRYLIC_FILES.items():
        write_svgz(dest / rel, acrylic(read_svgz(dest / rel), *ACRYLIC[variant][part], name=rel))

    # Plasma 6 reads metadata.json; theme settings live in plasmarc.
    groups = desktop_entry_groups(base / "metadata.desktop")
    groups["[ContrastEffect]"] = ACRYLIC[variant]["contrast"]
    # Fluent asks for adaptive transparency: Plasma then makes the taskbar
    # opaque while a window is maximized. Windows 11's taskbar stays
    # see-through (product owner, 2026-11-07). Off, libplasma reports every
    # panel as translucent (PanelView::opacityMode); the taskbar's own
    # setting cannot be changed by a script in Plasma 6.3.6
    # (Panel::setOpacity calls QWindow::setOpacity).
    groups["[AdaptiveTransparency]"] = ["enabled=false"]
    groups["[Wallpaper]"] = ["defaultWallpaperTheme=VeltOS", "defaultFileSuffix=.png",
                             "defaultWidth=3840", "defaultHeight=2160"]
    plasmarc = [f"# {ATTRIBUTION}"]
    for group, lines in groups.items():
        plasmarc += ["", group, *lines]
    (dest / "plasmarc").write_text("\n".join(plasmarc) + "\n", encoding="utf-8")
    metadata = {
        "KPlugin": {
            "Authors": [{"Name": "Vince Liuice (Fluent)"}, {"Name": "VeltOS Developers"}],
            "Description": f"VeltOS panel and popup theme ({variant}). {ATTRIBUTION}.",
            "EnabledByDefault": True,
            "Id": name,
            "License": "GPL-3.0",
            "Name": name.replace("-", " "),
            "Version": "1.0",
            "Website": "https://github.com/vinceliuice/Fluent-kde",
        },
        "X-Plasma-API": "5.0",
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return recoloured


# --- Colour schemes ---------------------------------------------------------------

def derive_color_scheme(groups, scheme_id, spec):
    """Fluent colour scheme groups -> VeltOS scheme (accent keys replaced)."""
    accent = ACCENTS[spec["variant"]]
    colour_groups = [g for g in groups if g.startswith("[Colors:")]
    if "[Colors:Selection]" not in groups or len(colour_groups) < 6:
        raise SystemExit(f"{spec['source']}: unexpected colour scheme layout")
    for group in colour_groups:
        entries = groups[group]
        selection = group.startswith("[Colors:Selection]")
        if "DecorationFocus" in entries:
            entries["DecorationFocus"] = rgb_text(accent["hover" if selection else "accent"])
        if "DecorationHover" in entries:
            entries["DecorationHover"] = rgb_text(accent["hover"])
        if "DecorationInactive" in entries:
            entries["DecorationInactive"] = rgb_text(accent["accent"])
        if selection:
            entries["BackgroundNormal"] = rgb_text(accent["accent"])
            entries["BackgroundAlternate"] = rgb_text(accent["alt"])
            entries["ForegroundActive"] = "255,255,255"
        else:
            if "ForegroundLink" in entries:
                entries["ForegroundLink"] = rgb_text(accent["link"])
            if "ForegroundActive" in entries:
                entries["ForegroundActive"] = rgb_text(accent["accent"])
    general = groups.setdefault("[General]", {})
    for key in [k for k in general if k.startswith("Name")]:
        del general[key]
    general["ColorScheme"] = scheme_id
    general["Name"] = spec["name"]
    return groups
