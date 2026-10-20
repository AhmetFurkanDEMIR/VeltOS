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
    "light": {"#ffffff": "#f3f5fa", "#f5f5f5": "#f8f9fc"},
    "dark": {"#202020": "#1c1d26", "#2c2c2c": "#24252f"},
}
CAPTION_W, CAPTION_H = 46, 32
WINDOW_RADIUS = 8

DESKTOPTHEMES = {"VeltOS": "light", "VeltOS-Dark": "dark"}
# Plasma theme files that show other projects' or companies' logos.
DESKTOPTHEME_DROP = ("icons/start.svgz", "icons/manjaro.svgz", "widgets/branding.svgz")
# Taskbar background opacity, see-through like Windows 11: the normal
# background is used without the blur effect (no 3D acceleration) and stays
# readable; the translucent one is used with blur ("acrylic").
PANEL_OPACITY = {"widgets/panel-background.svgz": 0.86,
                 "translucent/widgets/panel-background.svgz": 0.7}
# Blur with more colour, closer to Windows 11 acrylic than Fluent's default.
CONTRAST_EFFECT = ["enabled=true", "contrast=0.18", "intensity=1.1", "saturation=1.7"]

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

def build_kvantum(upstream, root):
    src = upstream / "Kvantum/Fluent-round"
    dest = root / "usr/share/Kvantum" / KVANTUM_DIR
    dest.mkdir(parents=True, exist_ok=True)
    for name, (fluent, variant) in KVANTUM.items():
        svg = (src / f"{fluent}.svg").read_text(encoding="utf-8")
        (dest / f"{name}.svg").write_text(recolour(svg, variant, f"{fluent}.svg"), encoding="utf-8")
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
    AuroraeButton.qml, plasma-overrides/aurorae.json)."""
    c = CAPTION_COLOURS[variant]
    red = kind == "close"
    states = [
        ("active", c["glyph"], 1.0, None),
        ("inactive", c["inactive"], 1.0, None),
        ("hover", "#ffffff" if red else c["glyph"], 1.0, (CLOSE_RED, 1.0) if red else c["hover"]),
        ("pressed", "#ffffff" if red else c["glyph"], 0.7 if red else 0.8,
         (CLOSE_RED, 0.85) if red else c["pressed"]),
        ("deactivated", c["glyph"], 0.3, None),
    ]
    if red:
        states += [(f"{state}-maximized", colour, opacity, background)
                   for state, colour, opacity, background in states if state in ("hover", "pressed")]
    parts = []
    for i, (state, colour, opacity, background) in enumerate(states):
        x = i * (CAPTION_W + 2)
        group = [f'<g id="{state}-center">',
                 f'<rect x="{x}" y="0" width="{CAPTION_W}" height="{CAPTION_H}" fill="#000000" opacity="0.001"/>']
        if background:
            group.append(caption_background(kind, x, *background, maximized=state.endswith("-maximized")))
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


def build_desktoptheme(upstream, root, name, variant, colors_text):
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
    for path in sorted(dest.rglob("*.svgz")):
        text = read_svgz(path)
        if re.search(re.escape(FLUENT_BLUE), text, flags=re.IGNORECASE):
            text = recolour(text, variant, str(path))
            recoloured += 1
        write_svgz(path, text)
    (dest / "colors").write_text(colors_text, encoding="utf-8")
    for rel, opacity in PANEL_OPACITY.items():
        write_svgz(dest / rel, set_background_opacity(read_svgz(dest / rel), opacity, rel))

    # Plasma 6 reads metadata.json; theme settings live in plasmarc.
    groups = desktop_entry_groups(base / "metadata.desktop")
    groups["[ContrastEffect]"] = CONTRAST_EFFECT
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
