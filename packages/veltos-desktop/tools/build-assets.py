#!/usr/bin/env python3
"""Generate the installable file tree of the veltos-desktop package.

    build-assets.py --fluent upstream --out build-assets

Everything the package installs is produced here from the sources next to
this script, so debian/rules only copies one staging tree (<out>/root).
Only the Python standard library and rsvg-convert are required. Widget
style, window frames, panel theme and colour schemes are derived from the
pinned Fluent-kde release in upstream/ (see tools/fluent.py).
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bloom  # noqa: E402  (tools/bloom.py: procedural wallpaper)
import fluent  # noqa: E402  (tools/fluent.py: themes derived from Fluent-kde)
import app_titles  # noqa: E402  (tools/app_titles.py: program names in titles)

WALLPAPER_ID = "VeltOS"
WALLPAPER_DIR = Path("usr/share/wallpapers") / WALLPAPER_ID
WALLPAPER_CANVAS = (3840, 2160)
WALLPAPER_SIZES = [
    (1366, 768), (1920, 1080), (2560, 1440), (3840, 2160),  # 16:9
    (1920, 1200), (2560, 1600),                             # 16:10
    (3440, 1440),                                           # 21:9
]
LOGIN_WALLPAPER = "images/3840x2160.png"

# Plasma picks contents/images_dark/ when the colour scheme is dark and
# contents/images/ otherwise. Values are tools/bloom.py palette names.
WALLPAPER_VARIANTS = {"images": "light", "images_dark": "dark"}

STARTMENU_ID = "org.veltos.startmenu"
QUICKSETTINGS_ID = "org.veltos.quicksettings"

# UI font for the whole desktop (Debian package fonts-inter). Qt font strings:
# family, point size, pixel size, style hint, weight, italic, underline, ...
UI_FONT = "Inter,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
UI_FONT_SMALL = "Inter,8,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
ICON_THEMES = {"dark": "Fluent-dark", "light": "Fluent"}
CURSOR_THEME = "Fluent-cursors"  # white Windows-style pointer, both themes

# Kvantum's "kvantum-dark" style key selects the Dark variant of the
# configured Kvantum theme (VeltOS -> VeltOSDark), so switching the global
# theme switches the application style without touching Kvantum's config.
LOOK_AND_FEEL = {
    "org.veltos.dark": {
        "name": "VeltOS Dark",
        "description": "VeltOS desktop: centered taskbar, dark theme",
        "color_scheme": "VeltOSDark",
        "icons": ICON_THEMES["dark"],
        "wallpaper_variant": "images_dark",
        "widget_style": "kvantum-dark",
        "plasma_theme": "VeltOS-Dark",
        "decoration": "VeltOS-Dark",
    },
    "org.veltos.light": {
        "name": "VeltOS Light",
        "description": "VeltOS default desktop: centered taskbar, light theme",
        "color_scheme": "VeltOSLight",
        "icons": ICON_THEMES["light"],
        "wallpaper_variant": "images",
        "widget_style": "kvantum",
        "plasma_theme": "VeltOS",
        "decoration": "VeltOS",
    },
}
DEFAULT_LOOK_AND_FEEL = "org.veltos.light"

# Settings pages hidden from System Settings ("KDE Control Module
# Restrictions" in kdeglobals; the mechanism was checked in a VM with
# kcm_bolt and kcm_kdeconnect). They are for KDE services VeltOS does not
# use, for developers, or for rare hardware.
HIDDEN_SETTINGS_PAGES = [
    "kcm_activities",        # Plasma activities
    "kcm_bolt",              # Thunderbolt device authorisation
    "kcm_breezedecoration",  # Breeze window frames (VeltOS uses its own)
    "kcm_feedback",          # KDE telemetry ("User Feedback")
    "kcm_kamera",            # gPhoto2 cameras
    "kcm_kdeconnect",        # KDE Connect
    "kcm_kded",              # KDE background services
    "kcm_kgamma",            # monitor gamma
    "kcm_kup",               # Kup backups
    "kcm_kwin_scripts",      # KWin scripts
    "kcm_kwinxwayland",      # legacy X11 key forwarding
    "kcm_qtquicksettings",   # Qt Quick renderer (developers)
    "kcm_solid_actions",     # device action editor
    "kcm_webshortcuts",      # web search keywords
]



def run(cmd):
    subprocess.run(cmd, check=True)


# --- INI helpers (KDE config files) -----------------------------------------

def parse_kconfig(text):
    """Parse a KDE config file into {group: {key: value}} keeping order.

    Group headers may be nested ("[Colors:Header][Inactive]"); they are kept
    verbatim as the group name. Comment lines are dropped.
    """
    groups = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("["):
            current = stripped
            groups.setdefault(current, {})
            continue
        if current is None or "=" not in stripped:
            raise ValueError(f"unexpected line outside a group: {line!r}")
        key, value = stripped.split("=", 1)
        groups[current][key] = value
    return groups


def format_kconfig(groups, header=""):
    out = [header.rstrip("\n")] if header else []
    for group, entries in groups.items():
        if out:
            out.append("")
        out.append(group)
        out.extend(f"{k}={v}" for k, v in entries.items())
    return "\n".join(out) + "\n"


# --- Colour schemes -----------------------------------------------------------

def build_color_schemes(fluent_dir, root):
    """VeltOS colour schemes, derived from Fluent's (they match the Kvantum
    style's palette, which KDE applications mix with the colour scheme)."""
    out_dir = root / "usr/share/color-schemes"
    out_dir.mkdir(parents=True, exist_ok=True)
    schemes = {}
    for scheme_id, spec in fluent.COLOR_SCHEMES.items():
        text = (fluent_dir / "color-schemes" / spec["source"]).read_text(encoding="utf-8")
        groups = fluent.derive_color_scheme(parse_kconfig(text), scheme_id, spec)
        header = (
            "# SPDX-License-Identifier: GPL-3.0-only\n"
            f"# {spec['name']}: derived from Fluent-kde {spec['source']} (Vince Liuice)\n"
            "# by veltos-desktop/tools/build-assets.py (accent colours replaced).\n")
        (out_dir / f"{scheme_id}.colors").write_text(
            format_kconfig(groups, header), encoding="utf-8")
        schemes[scheme_id] = groups
    return schemes


def build_kdeglobals(scheme_groups, root):
    """System-wide KDE defaults (/etc/xdg/kdeglobals).

    KDE applications read colours from the [Colors:*] groups in kdeglobals,
    not from the ColorScheme name, so the full default scheme is embedded.
    """
    lnf = LOOK_AND_FEEL[DEFAULT_LOOK_AND_FEEL]
    groups = {g: dict(e) for g, e in scheme_groups.items()
              if g.startswith(("[Colors:", "[ColorEffects:", "[WM]"))}
    groups["[General]"] = {
        "ColorScheme": lnf["color_scheme"],
        "font": UI_FONT,
        "menuFont": UI_FONT,
        "toolBarFont": UI_FONT,
        "smallestReadableFont": UI_FONT_SMALL,
    }
    groups["[WM]"]["activeFont"] = UI_FONT
    groups["[Icons]"] = {"Theme": lnf["icons"]}
    groups["[KDE]"] = {
        "LookAndFeelPackage": DEFAULT_LOOK_AND_FEEL,
        # The light/dark pair offered by Settings > Quick Settings.
        "DefaultLightLookAndFeel": "org.veltos.light",
        "DefaultDarkLookAndFeel": "org.veltos.dark",
        "widgetStyle": lnf["widget_style"],
        "contrast": scheme_groups.get("[KDE]", {}).get("contrast", "4"),
    }
    groups["[KDE Control Module Restrictions]"] = {kcm: "false" for kcm in HIDDEN_SETTINGS_PAGES}
    header = ("# VeltOS system-wide KDE defaults. Users override these in\n"
              "# ~/.config/kdeglobals. Generated by veltos-desktop.\n")
    path = root / "etc/xdg/kdeglobals"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_kconfig(groups, header), encoding="utf-8")


# --- Wallpaper ------------------------------------------------------------------

def crop_viewbox(width, height):
    """viewBox that crops the 16:9 canvas to the target aspect ratio."""
    cw, ch = WALLPAPER_CANVAS
    aspect = width / height
    if aspect < cw / ch:   # narrower (16:10, 4:3): trim the sides
        vw, vh = ch * aspect, ch
    else:                  # wider (21:9): trim top and bottom
        vw, vh = cw, cw / aspect
    return (cw - vw) / 2, (ch - vh) / 2, vw, vh


def render_svg(svg_text, width, height, dest, tmp_dir):
    tmp = tmp_dir / f"render-{width}x{height}.svg"
    tmp.write_text(svg_text, encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["rsvg-convert", "--width", str(width), "--height", str(height),
         "--output", str(dest), str(tmp)])


def svg_with_viewbox(svg_text, width, height):
    x, y, w, h = crop_viewbox(width, height)
    root_tag = re.search(r"<svg\b[^>]*>", svg_text)
    if not root_tag:
        raise SystemExit("wallpaper template: <svg> root element not found")
    tag = root_tag.group(0)
    for attr, value in (("width", width), ("height", height),
                        ("viewBox", f"{x:.2f} {y:.2f} {w:.2f} {h:.2f}")):
        tag, count = re.subn(rf'\b{attr}="[^"]*"', f'{attr}="{value}"', tag)
        if count != 1:
            raise SystemExit(f"wallpaper template: root needs one {attr}=")
    return svg_text[:root_tag.start()] + tag + svg_text[root_tag.end():]


def wallpaper_svg(variant):
    """Generated wallpaper SVG for a contents/ directory name (see WALLPAPER_VARIANTS)."""
    return bloom.wallpaper_svg(WALLPAPER_VARIANTS[variant], SRC / "artwork/veltos-logo.svg")


def build_wallpaper(root, tmp_dir):
    base = root / WALLPAPER_DIR
    for variant in WALLPAPER_VARIANTS:
        svg = wallpaper_svg(variant)
        for w, h in WALLPAPER_SIZES:
            render_svg(svg_with_viewbox(svg, w, h), w, h,
                       base / "contents" / variant / f"{w}x{h}.png", tmp_dir)
    render_svg(svg_with_viewbox(wallpaper_svg("images"), 400, 250), 400, 250,
               base / "contents/screenshot.png", tmp_dir)
    metadata = {
        "KPlugin": {
            "Authors": [{"Name": "VeltOS Project"}],
            "Id": WALLPAPER_ID,
            "License": "CC-BY-SA-4.0",
            "Name": "VeltOS Bloom",
        }
    }
    (base / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


# --- Plasma look-and-feel packages ----------------------------------------------

def lnf_defaults(spec):
    return (
        "[kdeglobals][KDE]\n"
        f"widgetStyle={spec['widget_style']}\n"
        "\n[kdeglobals][General]\n"
        f"ColorScheme={spec['color_scheme']}\n"
        "\n[kdeglobals][Icons]\n"
        f"Theme={spec['icons']}\n"
        "\n[plasmarc][Theme]\n"
        f"name={spec['plasma_theme']}\n"
        "\n[kcminputrc][Mouse]\n"
        f"cursorTheme={CURSOR_THEME}\n"
        "\n[kwinrc][WindowSwitcher]\n"
        "LayoutName=org.kde.breeze.desktop\n"
        "\n[kwinrc][org.kde.kdecoration2]\n"
        "library=org.kde.kwin.aurorae\n"
        f"theme=__aurorae__svg__{spec['decoration']}\n"
        "\n[ksplashrc][KSplash]\n"
        "Engine=KSplashQML\n"
        f"Theme={DEFAULT_LOOK_AND_FEEL}\n"
        "\n[Wallpaper]\n"
        f"Image={WALLPAPER_ID}\n"
    )


def build_look_and_feel(root, tmp_dir):
    layout = SRC / "plasma/layout.js"
    splash_dir = SRC / "plasma/splash"
    for package_id, spec in LOOK_AND_FEEL.items():
        svg = wallpaper_svg(spec["wallpaper_variant"])
        base = root / "usr/share/plasma/look-and-feel" / package_id
        contents = base / "contents"
        (contents / "layouts").mkdir(parents=True, exist_ok=True)
        shutil.copy(layout, contents / "layouts/org.kde.plasma.desktop-layout.js")
        shutil.copytree(splash_dir, contents / "splash", dirs_exist_ok=True)
        (contents / "splash/images").mkdir(exist_ok=True)
        shutil.copy(SRC / "artwork/veltos-logo.svg",
                    contents / "splash/images/veltos-logo.svg")
        (contents / "defaults").write_text(lnf_defaults(spec), encoding="utf-8")
        # Preview shown in System Settings > Global Theme. A rendered desktop
        # screenshot from the VM boot test should replace this later.
        render_svg(svg_with_viewbox(svg, 600, 338), 600, 338,
                   contents / "previews/preview.png", tmp_dir)
        metadata = {
            "KPackageStructure": "Plasma/LookAndFeel",
            "KPlugin": {
                "Authors": [{"Name": "VeltOS Project"}],
                "Description": spec["description"],
                "Id": package_id,
                "License": "GPL-3.0-or-later",
                "Name": spec["name"],
                "Version": "0.1",
            },
            "X-Plasma-APIVersion": "2",
        }
        (base / "metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


# --- Login screen, lock screen, icons -----------------------------------------

def build_static_config(root):
    wallpaper_url = f"/usr/share/wallpapers/{WALLPAPER_ID}/"
    login_image = f"/{WALLPAPER_DIR}/contents/{LOGIN_WALLPAPER}"
    lnf = LOOK_AND_FEEL[DEFAULT_LOOK_AND_FEEL]

    files = {
        # Window frames: Windows 11 style buttons on the right, app icon left.
        "etc/xdg/kwinrc": (
            "[org.kde.kdecoration2]\n"
            "library=org.kde.kwin.aurorae\n"
            f"theme=__aurorae__svg__{lnf['decoration']}\n"
            "ButtonsOnLeft=M\n"
            "ButtonsOnRight=IAX\n"),
        "etc/xdg/plasmarc": (
            "[Theme]\n"
            f"name={lnf['plasma_theme']}\n"),
        # File Explorer (Dolphin) like Windows: a fresh window at Home, zip
        # files open like folders, icon-only toolbar, tooltips.
        "etc/xdg/dolphinrc": (
            "[General]\n"
            "RememberOpenedTabs=false\n"
            "BrowseThroughArchives=true\n"
            "ShowToolTips=true\n"
            "\n[MainWindow]\n"
            "MenuBar=Disabled\n"
            "\n[MainWindow][Toolbar mainToolBar]\n"
            "ToolButtonStyle=IconOnly\n"
            # Second row (dolphin/dolphinui.rc): "New", "Sort", "View" with
            # text, cut/copy/paste/rename/delete as icons, like Windows 11.
            "\n[MainWindow][Toolbar commandBar]\n"
            "ToolButtonStyle=TextBesideIcon\n"),
        # Shut down / restart / sign out from Start act at once, like on
        # Windows (no full-screen confirmation dialog), and sign-in starts
        # with a clean desktop instead of reopening the last session's apps.
        "etc/xdg/ksmserverrc": (
            "[General]\n"
            "confirmLogout=false\n"
            "loginMode=emptySession\n"),
        "etc/xdg/kscreenlockerrc": (
            "[Greeter][Wallpaper][org.kde.image][General]\n"
            f"Image={wallpaper_url}\n"
            f"PreviewImage={wallpaper_url}\n"),
        "etc/xdg/kcminputrc": (
            "[Mouse]\n"
            f"cursorTheme={CURSOR_THEME}\n"),
        "etc/xdg/ksplashrc": (
            "[KSplash]\n"
            "Engine=KSplashQML\n"
            f"Theme={DEFAULT_LOOK_AND_FEEL}\n"),
        # Vendor defaults; /etc/sddm.conf.d/ and /etc/sddm.conf override them.
        "usr/lib/sddm/sddm.conf.d/10-veltos.conf": (
            "[Theme]\n"
            "Current=veltos\n"
            f"CursorTheme={CURSOR_THEME}\n"),
        # VeltOS sign-in screen (sddm/veltos, Windows 11 layout).
        "usr/share/sddm/themes/veltos/theme.conf": (
            "[General]\n"
            f"background={login_image}\n"),
        # Read by the Breeze SDDM theme on top of its theme.conf.
        "usr/share/sddm/themes/breeze/theme.conf.user": (
            "[General]\n"
            "type=image\n"
            f"background={login_image}\n"),
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    icon_dir = root / "usr/share/icons/hicolor/scalable/apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "artwork/veltos-logo.svg", icon_dir / "veltos-logo.svg")

    explorer = root / "usr/share/veltos/dolphin"
    explorer.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "dolphin/dolphinui.rc", explorer / "dolphinui.rc")

    for name in ("Main.qml", "metadata.desktop"):
        shutil.copy(SRC / "sddm/veltos" / name, root / "usr/share/sddm/themes/veltos" / name)

    # Session script (application names, per-user defaults) and its helpers.
    env_dir = root / "etc/xdg/plasma-workspace/env"
    env_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "system/veltos-session.sh", env_dir / "veltos-session.sh")
    libexec = root / "usr/libexec/veltos"
    libexec.mkdir(parents=True, exist_ok=True)
    for helper in ("session-defaults", "update-app-names"):
        shutil.copy(SRC / "system" / helper, libexec / helper)
        (libexec / helper).chmod(0o755)


# VeltOS plasmoids: source directory under plasma/ -> plugin id.
PLASMOIDS = {"startmenu": STARTMENU_ID, "quicksettings": QUICKSETTINGS_ID}


def build_plasmoids(root):
    """Install the VeltOS plasmoids and compile their translations."""
    for directory, plugin_id in PLASMOIDS.items():
        src = SRC / "plasma" / directory
        dest = root / "usr/share/plasma/plasmoids" / plugin_id
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("translations"))
        for po in sorted((src / "translations").glob("*.po")):
            mo = (root / "usr/share/locale" / po.stem / "LC_MESSAGES" /
                  f"plasma_applet_{plugin_id}.mo")
            mo.parent.mkdir(parents=True, exist_ok=True)
            run(["msgfmt", "--check", "--output-file", str(mo), str(po)])


def build_fluent_themes(fluent_dir, root, schemes):
    fluent.build_kvantum(fluent_dir, root)
    fluent.build_aurorae(fluent_dir, root)
    for name, variant in fluent.DESKTOPTHEMES.items():
        scheme_id = "VeltOSLight" if variant == "light" else "VeltOSDark"
        colors = format_kconfig(schemes[scheme_id], f"# {fluent.ATTRIBUTION}\n")
        fluent.build_desktoptheme(fluent_dir, root, name, variant, colors)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fluent", type=Path, default=SRC / "upstream",
                        help="unpacked Fluent-kde release (upstream.json)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.out.exists():
        shutil.rmtree(args.out)
    root = args.out / "root"
    tmp_dir = args.out / "tmp"
    root.mkdir(parents=True)
    tmp_dir.mkdir()

    if not (args.fluent / "Kvantum").is_dir():
        raise SystemExit(f"{args.fluent}: Fluent-kde not found; run build/scripts/fetch-upstream.py")
    schemes = build_color_schemes(args.fluent, root)
    build_kdeglobals(schemes[LOOK_AND_FEEL[DEFAULT_LOOK_AND_FEEL]["color_scheme"]], root)
    build_fluent_themes(args.fluent, root, schemes)
    app_titles.build(root, tmp_dir)
    build_wallpaper(root, tmp_dir)
    build_look_and_feel(root, tmp_dir)
    build_plasmoids(root)
    build_static_config(root)
    shutil.rmtree(tmp_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
