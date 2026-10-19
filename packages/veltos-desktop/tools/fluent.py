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
AURORAE_GENERAL = {"TitleAlignment": "Left", "LeftButtons": "M", "RightButtons": "IAX"}
# A 1 px bottom border: with 0, a 1 px seam between the window contents and
# the rounded bottom edge shows the desktop through (seen in a VM).
AURORAE_LAYOUT = {"BorderBottom": "1"}

DESKTOPTHEMES = {"VeltOS": "light", "VeltOS-Dark": "dark"}
# Plasma theme files that show other projects' or companies' logos.
DESKTOPTHEME_DROP = ("icons/start.svgz", "icons/manjaro.svgz", "widgets/branding.svgz")

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


def set_ini_keys(text, section, values, what):
    """Set keys inside one [section] of an INI-style file, keeping everything
    else byte for byte. Every key must already exist in that section."""
    lines = text.splitlines()
    current = None
    seen = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            current = stripped
            continue
        if current == section and "=" in stripped:
            key = stripped.split("=", 1)[0]
            if key in values:
                lines[i] = f"{key}={values[key]}"
                seen.add(key)
    missing = set(values) - seen
    if missing:
        raise SystemExit(f"{what}: keys {sorted(missing)} not found in {section}")
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
        text = set_ini_keys(rc.read_text(encoding="utf-8"), "[General]", AURORAE_GENERAL, rc.name)
        rc.write_text(set_ini_keys(text, "[Layout]", AURORAE_LAYOUT, rc.name), encoding="utf-8")
        metadata = (dest / "metadata.desktop").read_text(encoding="utf-8")
        metadata = set_ini_keys(metadata, "[Desktop Entry]", {
            "Name": name.replace("-", " "),
            "X-KDE-PluginInfo-Name": name,
            "X-KDE-PluginInfo-Author": "Vince Liuice (Fluent); VeltOS Developers",
        }, f"{fluent}/metadata.desktop")
        (dest / "metadata.desktop").write_text(metadata, encoding="utf-8")
        # The window buttons are monochrome; only the frame may carry the accent.
        for svg in dest.glob("*.svg"):
            text = svg.read_text(encoding="utf-8")
            if re.search(re.escape(FLUENT_BLUE), text, flags=re.IGNORECASE):
                svg.write_text(recolour(text, variant, svg.name), encoding="utf-8")


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

    # Plasma 6 reads metadata.json; theme settings live in plasmarc.
    groups = desktop_entry_groups(base / "metadata.desktop")
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
