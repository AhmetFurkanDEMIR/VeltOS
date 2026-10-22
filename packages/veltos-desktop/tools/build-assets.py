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
import wallpapers  # noqa: E402  (tools/wallpapers.py: procedural wallpapers)
import fluent  # noqa: E402  (tools/fluent.py: themes derived from Fluent-kde)
import gtktheme  # noqa: E402  (tools/gtktheme.py: GTK theme with Windows 11 caption buttons)
import firefox  # noqa: E402  (tools/firefox.py: Windows 11 caption buttons in Firefox)
import sounds  # noqa: E402  (tools/sounds.py: original VeltOS system sounds)
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
# The alternative wallpapers come in fewer sizes; Plasma scales the nearest.
ALT_WALLPAPER_SIZES = [(1920, 1080), (2560, 1600), (3840, 2160)]

# Plasma picks contents/images_dark/ when the colour scheme is dark and
# contents/images/ otherwise. Values are tools/wallpapers.py variants.
WALLPAPER_VARIANTS = {"images": "light", "images_dark": "dark"}

STARTMENU_ID = "org.veltos.startmenu"
QUICKSETTINGS_ID = "org.veltos.quicksettings"
SEARCH_ID = "org.veltos.search"
TASKVIEW_ID = "org.veltos.taskview"
CLOCK_ID = "org.veltos.clock"
SHOWDESKTOP_ID = "org.veltos.showdesktop"

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
    "kcm_about-distro",      # shows the kernel's build name; VeltOS Settings > About replaces it
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
        # Start's first pinned app and "open link" in KDE programs: Firefox
        # (Debian's KDE defaults name Falkon, which is not installed).
        "BrowserApplication": "firefox-esr.desktop",
    }
    groups["[WM]"]["activeFont"] = UI_FONT
    groups["[Icons]"] = {"Theme": lnf["icons"]}
    # VeltOS system sounds (tools/sounds.py), Ocean for the rest.
    groups["[Sounds]"] = {"Theme": sounds.THEME}
    groups["[KDE]"] = {
        "LookAndFeelPackage": DEFAULT_LOOK_AND_FEEL,
        # The light/dark pair offered by Settings > Quick Settings.
        "DefaultLightLookAndFeel": "org.veltos.light",
        "DefaultDarkLookAndFeel": "org.veltos.dark",
        "widgetStyle": lnf["widget_style"],
        "contrast": scheme_groups.get("[KDE]", {}).get("contrast", "4"),
        # Buttons without icons (OK, Cancel), as Windows draws them; KDE's
        # remaining dialogs (new folder on the desktop) look plainer.
        "ShowIconsOnPushButtons": "false",
    }
    groups["[KDE Control Module Restrictions]"] = {kcm: "false" for kcm in HIDDEN_SETTINGS_PAGES}
    # The taskbar is locked (session-fixups): its items then offer no
    # "Configure ..." entries opening KDE's widget settings dialogs; Windows'
    # taskbar items have none either. VeltOS Settings covers the options.
    groups["[KDE Action Restrictions]"] = {"plasma/allow_configure_when_locked": "false"}
    header =("# VeltOS system-wide KDE defaults. Users override these in\n"
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


def wallpaper_svg(variant, design="bloom"):
    """Generated wallpaper SVG for a contents/ directory name (see WALLPAPER_VARIANTS)."""
    return wallpapers.svg(design, WALLPAPER_VARIANTS[variant])


def build_wallpaper(root, tmp_dir):
    """The default wallpaper (VeltOS Bloom) and the alternatives offered in
    Settings > Personalisation > Background, each light and dark."""
    if wallpapers.DESIGNS["bloom"][0] != WALLPAPER_ID:
        raise SystemExit("tools/wallpapers.py: the default design must be the VeltOS package")
    for design, (package_id, name) in wallpapers.DESIGNS.items():
        base = root / "usr/share/wallpapers" / package_id
        sizes = WALLPAPER_SIZES if package_id == WALLPAPER_ID else ALT_WALLPAPER_SIZES
        for variant in WALLPAPER_VARIANTS:
            svg = wallpaper_svg(variant, design)
            for w, h in sizes:
                render_svg(svg_with_viewbox(svg, w, h), w, h,
                           base / "contents" / variant / f"{w}x{h}.png", tmp_dir)
        render_svg(svg_with_viewbox(wallpaper_svg("images", design), 400, 250), 400, 250,
                   base / "contents/screenshot.png", tmp_dir)
        # The dark picture's preview, for Settings' theme tiles (VeltOS file,
        # Plasma ignores it).
        render_svg(svg_with_viewbox(wallpaper_svg("images_dark", design), 400, 250), 400, 250,
                   base / "contents/screenshot-dark.png", tmp_dir)
        metadata = {
            "KPlugin": {
                "Authors": [{"Name": "VeltOS Project"}],
                "Id": package_id,
                "License": "CC-BY-SA-4.0",
                "Name": name,
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
        splash = contents / "splash/Splash.qml"
        splash_qml = splash.read_text(encoding="utf-8")
        if "@LOGIN_IMAGE@" not in splash_qml:
            raise SystemExit("Splash.qml: @LOGIN_IMAGE@ placeholder missing")
        splash.write_text(splash_qml.replace("@LOGIN_IMAGE@", f"file:///{WALLPAPER_DIR}/contents/{LOGIN_WALLPAPER}"),
                          encoding="utf-8")
        # Ctrl+Alt+Del security screen and shut-down dialog in Windows 11 style.
        shutil.copytree(SRC / "plasma/logout", contents / "logout", dirs_exist_ok=True)
        logout = contents / "logout/Logout.qml"
        logout_qml = logout.read_text(encoding="utf-8")
        if "@LOGIN_IMAGE@" not in logout_qml:
            raise SystemExit("Logout.qml: @LOGIN_IMAGE@ placeholder missing")
        logout.write_text(logout_qml.replace("@LOGIN_IMAGE@", f"file:///{WALLPAPER_DIR}/contents/{LOGIN_WALLPAPER}"),
                          encoding="utf-8")
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
            "ToolButtonStyle=TextBesideIcon\n"
            # Details view like Windows: small icons, one line per item, no
            # tree expanders.
            "\n[DetailsMode]\n"
            "IconSize=22\n"
            "PreviewSize=22\n"
            "ExpandableFolders=false\n"),
        # Shut down / restart / sign out from Start act at once, like on
        # Windows (no full-screen confirmation dialog), and sign-in starts
        # with a clean desktop instead of reopening the last session's apps.
        # Terminal like Windows Terminal: the VeltOS profiles (One Half
        # Light / Campbell colours, Cascadia Mono, konsole/; system/
        # terminal-theme picks the one of the light/dark theme and styles the
        # tabs), tabs always shown with a "+" button, no toolbars
        # (konsole/*.rc), opening at the profile's 120 x 30 like Windows
        # Terminal instead of the last size.
        "etc/xdg/konsolerc": (
            "[Desktop Entry]\n"
            "DefaultProfile=VeltOS Light.profile\n"
            "\n[KonsoleWindow]\n"
            "RememberWindowSize=false\n"
            "\n[MainWindow]\n"
            "MenuBar=Disabled\n"
            "\n[TabBar]\n"
            "TabBarVisibility=AlwaysShowTabBar\n"
            "NewTabButton=true\n"
            "SearchTabsButton=HideSearchTabsButton\n"
            "CloseTabButton=OnEachTab\n"
            "TabBarUseUserStyleSheet=true\n"
            "TabBarUserStyleSheetFile=file:///usr/share/veltos/konsole/tabs-light.css\n"),
        # The clipboard keeps pictures too (Windows' clipboard does), so a
        # snip stays pasteable after VeltOS Snipping Tool has ended: Plasma's
        # Klipper ignores images by default (klipper.kcfg, Plasma 6.3.6).
        # Windows key + Space switches the keyboard layout, as on Windows
        # (KDE's Meta+Alt+K stays as a second key). kglobalacceld reads this
        # as the current shortcut for users who have not changed it.
        "etc/xdg/kglobalshortcutsrc": (
            "[KDE Keyboard Layout Switcher]\n"
            "Switch to Next Keyboard Layout=Meta+Space\\tMeta+Alt+K,Meta+Alt+K,Switch to Next Keyboard Layout\n"),
        "etc/xdg/klipperrc": (
            "[General]\n"
            "IgnoreImages=false\n"),
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
        # No application icon bouncing next to the pointer while a program
        # starts (KWin's startup feedback; Windows shows none). KWin on
        # Wayland draws the icon in every feedback mode and never switches
        # to a busy pointer, so the feedback is off; the taskbar button
        # shows that the program is starting.
        # The power key (also VirtualBox's "send the shutdown signal") shuts
        # down, Windows' default. Plasma's default opens the logout screen,
        # which cannot appear over the lock screen, so the key seemed to do
        # nothing there. Programs can still stop it when there is unsaved work.
        "etc/xdg/powerdevilrc": "".join(
            f"[{profile}][SuspendAndShutdown]\nPowerButtonAction=8\n\n"
            for profile in ("AC", "Battery", "LowBattery")),
        "etc/xdg/klaunchrc": (
            "[FeedbackStyle]\n"
            "BusyCursor=false\n"),
        # A chime when the desktop appears after signing in, like Windows'
        # start-up sound (Plasma has the event but no sound by default).
        "etc/xdg/plasma_workspace.notifyrc": (
            "[Event/startkde]\n"
            "Action=Sound\n"),
        "etc/xdg/ksplashrc": (
            "[KSplash]\n"
            "Engine=KSplashQML\n"
            f"Theme={DEFAULT_LOOK_AND_FEEL}\n"),
        # No "KDE Wallet" set-up wizard (Windows has none): Wi-Fi keys are
        # kept by the system (NetworkManager, readable by root only), and
        # Firefox has its own password store. Users can turn the wallet on
        # in the Control Panel.
        "etc/xdg/kwalletrc": (
            "[Wallet]\n"
            "Enabled=false\n"
            "First Use=false\n"),
        # Vendor defaults; /etc/sddm.conf.d/ and /etc/sddm.conf override them.
        # SDDM's default input method is its on-screen keyboard, which
        # covered the sign-in screen while typing the password.
        # The sign-in screen runs in KWin on Wayland, like the session: the
        # X11 greeter SDDM starts by default came up at a different
        # resolution than the desktop in VirtualBox and QEMU (small, then a
        # mode switch at sign-in and again at shut-down; product owner,
        # 2026-10-21). KWin picks the same screen mode for the greeter and
        # the session. The command line is the one Plasma's own SDDM settings
        # module writes (plasma-workspace 6.3).
        # Before SDDM starts, pick the sign-in screen's renderer for this
        # machine (VirtualBox: Mesa llvmpipe; the script explains).
        "usr/lib/systemd/system/sddm.service.d/veltos-virtualbox.conf": (
            "# Installed as /usr/lib/systemd/system/sddm.service.d/veltos-virtualbox.conf.\n"
            "# Decides the sign-in screen's renderer for this machine before SDDM\n"
            "# starts (VirtualBox: Mesa llvmpipe; /usr/libexec/veltos/sddm-virtualbox-env).\n"
            "[Service]\n"
            "ExecStartPre=-/usr/libexec/veltos/sddm-virtualbox-env\n"
        ),
        "usr/lib/sddm/sddm.conf.d/10-veltos.conf": (
            "[General]\n"
            "InputMethod=\n"
            "DisplayServer=wayland\n"
            # In VirtualBox, sddm-virtualbox-env (ExecStartPre of sddm.service)
            # writes a later drop-in that repeats this line with Mesa's
            # llvmpipe added, so the greeter renders there too; on every
            # other machine this line is the whole greeter environment.
            "GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell\n"
            "\n[Wayland]\n"
            "CompositorCommand=/usr/libexec/veltos/greeter-compositor\n"
            "\n[Theme]\n"
            "Current=veltos\n"
            f"CursorTheme={CURSOR_THEME}\n"
            # Accounts without a picture: the VeltOS default picture.
            f"FacesDir=/{FACES_DIR}\n"),
        # File indexing (Searching files in Settings) is off until a user
        # turns it on: the indexer reads every file of the home folder and
        # is the kind of background work VeltOS keeps off by default.
        "etc/xdg/baloofilerc": (
            "[Basic Settings]\n"
            "Indexing-Enabled=false\n"),
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

    # Changes to Plasma components, applied on the target system by
    # /usr/libexec/veltos/update-plasma-overrides.
    overrides = root / "usr/share/veltos/plasma-overrides"
    overrides.mkdir(parents=True, exist_ok=True)
    for spec in sorted((SRC / "plasma-overrides").glob("*.json")):
        shutil.copy(spec, overrides / spec.name)
    # Whole files that replace Plasma's (the Windows 11 lock screen).
    shutil.copytree(SRC / "plasma-overrides/files", overrides / "files", dirs_exist_ok=True)

    # Terminal profile and colours (usr/share/konsole) and Konsole's window
    # layout without toolbars (usr/share/kxmlgui5/konsole).
    konsole = root / "usr/share/konsole"
    konsole.mkdir(parents=True, exist_ok=True)
    for name in ("VeltOS Light.profile", "VeltOS Dark.profile", "VeltOS-OneHalfLight.colorscheme",
                 "VeltOS-Campbell.colorscheme"):
        shutil.copy(SRC / "konsole" / name, konsole / name)
    tabs = root / "usr/share/veltos/konsole"
    tabs.mkdir(parents=True, exist_ok=True)
    for name in ("tabs-light.css", "tabs-dark.css", "tab-close-light.svg", "tab-close-dark.svg"):
        shutil.copy(SRC / "konsole" / name, tabs / name)
    kxmlgui = root / "usr/share/kxmlgui5/konsole"
    kxmlgui.mkdir(parents=True, exist_ok=True)
    for name in ("konsoleui.rc", "sessionui.rc"):
        shutil.copy(SRC / "konsole" / name, kxmlgui / name)

    # KWin effects in QML (Windows 11 Task View).
    shutil.copytree(SRC / "kwin/effects", root / "usr/share/kwin/effects", dirs_exist_ok=True)

    # Desktop icons every user gets (see system/veltos-session.sh).
    desktop_icons = root / "usr/share/veltos/desktop"
    desktop_icons.mkdir(parents=True, exist_ok=True)
    for entry in sorted((SRC / "desktop").glob("*.desktop")):
        shutil.copy(entry, desktop_icons / entry.name)

    # Session script (application names, per-user defaults) and its helpers.
    env_dir = root / "etc/xdg/plasma-workspace/env"
    env_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "system/veltos-session.sh", env_dir / "veltos-session.sh")
    autostart = root / "etc/xdg/autostart"
    autostart.mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC / "system/veltos-session-fixups.desktop", autostart / "veltos-session-fixups.desktop")
    libexec = root / "usr/libexec/veltos"
    libexec.mkdir(parents=True, exist_ok=True)
    for helper in ("context-menus", "display-scale", "greeter-compositor", "needs-software-rendering",
                   "sddm-virtualbox-env", "session-defaults", "session-fixups", "start-categories",
                   "terminal-theme", "update-app-names", "update-plasma-overrides"):
        shutil.copy(SRC / "system" / helper, libexec / helper)
        (libexec / helper).chmod(0o755)
    # Plasma's own services start with KDE's platform theme, not the
    # portal's. veltos-session.sh gives every program
    # QT_QPA_PLATFORMTHEME=xdgdesktopportal (Windows 11 file dialogs), and a
    # Qt program starting with it first asks the portal (colour scheme). At
    # session start the portal cannot be up yet: its backends are Wayland
    # clients of KWin and Qt programs themselves. So kcminit, ksplash,
    # plasmashell, kded6, ksmserver, kactivitymanagerd ... each blocked 25 s
    # (the D-Bus timeout; systemd-analyze --user blame, VM 2026-10-22) and
    # xdg-desktop-portal.service itself timed out after 90 s: plasmashell
    # came after ~95 s instead of ~18 s (QEMU boot tests, since 2026-10-21).
    # A drop-in per unit; one for a unit that is not installed is inert.
    # Programs the user starts keep the portal theme.
    units_dir = root / "usr/lib/systemd/user"
    for unit in PLASMA_SERVICES:
        dropin = units_dir / f"{unit}.service.d" / "veltos-portal-theme.conf"
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_bytes(
            b"# Installed by veltos-desktop (tools/build-assets.py): Plasma's own\n"
            b"# services use KDE's platform theme; the portal's would wait for the\n"
            b"# portal, which cannot be up before they are (25 s each, 2026-10-22).\n"
            b"[Service]\nEnvironment=QT_QPA_PLATFORMTHEME=kde\n")


# Plasma's user services (plasma-workspace, kwin, kded6, powerdevil,
# kactivitymanagerd, kglobalacceld, xdg-desktop-portal-kde; Debian trixie,
# checked against the live image's /usr/lib/systemd/user on 2026-10-22).
PLASMA_SERVICES = (
    "plasma-baloorunner", "plasma-gmenudbusmenuproxy", "plasma-kaccess", "plasma-kactivitymanagerd",
    "plasma-kcminit", "plasma-kcminit-phase1", "plasma-kded", "plasma-kded6", "plasma-kglobalaccel",
    "plasma-krunner", "plasma-kscreen", "plasma-kscreen-osd", "plasma-ksmserver", "plasma-ksplash",
    "plasma-ksplash-ready", "plasma-ksystemstats", "plasma-kwallet-pam", "plasma-kwin_wayland",
    "plasma-kwin_x11", "plasma-plasmashell", "plasma-polkit-agent", "plasma-powerdevil",
    "plasma-restoresession", "plasma-xdg-desktop-portal-kde", "plasma-xembedsniproxy",
)


# VeltOS plasmoids: source directory under plasma/ -> plugin id.
PLASMOIDS = {"startmenu": STARTMENU_ID, "quicksettings": QUICKSETTINGS_ID, "search": SEARCH_ID,
             "taskview": TASKVIEW_ID, "clock": CLOCK_ID, "showdesktop": SHOWDESKTOP_ID}


# Default account picture (artwork/user-avatar.svg): the sign-in screen
# shows it through SDDM's FacesDir, session-defaults copies it to a new
# account's ~/.face at the first sign-in (packages may not use /etc/skel),
# and VeltOS apps show it for accounts without a picture.
FACES_DIR = "usr/share/veltos/faces"


def build_user_picture(root, tmp_dir):
    svg = (SRC / "artwork/user-avatar.svg").read_text(encoding="utf-8")
    picture = root / FACES_DIR / "default.png"
    render_svg(svg, 256, 256, picture, tmp_dir)
    shutil.copy(picture, root / FACES_DIR / ".face.icon")


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
    build_user_picture(root, tmp_dir)
    gtktheme.build(root)
    firefox.build(root)
    sounds.build(root)
    shutil.rmtree(tmp_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
