# veltos-desktop

The VeltOS desktop experience on top of stock KDE Plasma 6 (Debian trixie).
No Plasma code is forked; everything is configuration, artwork and a layout
script.

## What a new user gets

- A bottom taskbar with the start button and pinned/running apps **centered**
  (Windows 11 style) and system tray, clock/calendar and show-desktop on
  the right. Pinned: Dolphin, Firefox ESR, Konsole, System Settings.
- The VeltOS logo as the start button (Kickoff launcher).
- "VeltOS Dark" global theme by default; "VeltOS Light" selectable in
  System Settings → Colors & Themes → Global Theme.
- The "Velt Bloom" wallpaper: light and dark variants; Plasma picks the one
  matching the colour scheme.
- Branded login splash (ksplash), lock screen and SDDM login background.

Existing users are not modified: Plasma runs the layout script only for
users who have no Plasma configuration yet.

## Source layout

| Path | What |
|---|---|
| `artwork/veltos-logo.svg` | Logo mark: the bloom petals forming a "V" |
| `artwork/wallpaper.svg.in` | Wallpaper template; `@TOKENS@` filled per light/dark variant |
| `plasma/layout.js` | Plasma 6 layout script (panel, widgets, wallpaper) |
| `plasma/splash/Splash.qml` | Login splash shown while Plasma starts |
| `tools/build-assets.py` | Generates the whole installed tree into `build-assets/root/` |
| `tests/test_build_assets.py` | Unit tests + a full asset build check |

## Generated at build time (`tools/build-assets.py`)

| Installed path | Content |
|---|---|
| `/usr/share/plasma/look-and-feel/org.veltos.{dark,light}/` | Global themes: metadata, defaults, layout script, splash, preview |
| `/usr/share/color-schemes/VeltOS{Dark,Light}.colors` | Breeze schemes with VeltOS accent colours (Breeze colours that are not found fail the build) |
| `/etc/xdg/kdeglobals` | System defaults: VeltOS Dark colours, breeze-dark icons, `LookAndFeelPackage=org.veltos.dark` |
| `/etc/xdg/kscreenlockerrc`, `/etc/xdg/ksplashrc` | Lock screen wallpaper, splash theme |
| `/usr/share/wallpapers/VeltOS/` | 7 resolutions × 2 variants (16:9, 16:10, 21:9), cropped not stretched |
| `/usr/lib/sddm/sddm.conf.d/10-veltos.conf` | SDDM uses the Breeze theme |
| `/usr/share/sddm/themes/breeze/theme.conf.user` | SDDM background = dark wallpaper |
| `/usr/share/icons/hicolor/scalable/apps/veltos-logo.svg` | Logo icon (`veltos-logo`) |

Build-Depends: `kde-style-breeze-data` (source colour schemes),
`librsvg2-bin` (SVG → PNG), `python3`.

## Known limitations

- The Global Theme preview image is the wallpaper, not a real desktop
  screenshot yet.
- `theme.conf.user` in the Breeze SDDM theme directory is owned by this
  package; changing the login background in System Settings edits it and
  a package upgrade would replace it.
- Plymouth (graphical boot splash) is not configured yet.

## Licences

Code GPL-3.0-or-later; artwork CC-BY-SA-4.0; derived colour schemes
LGPL-2.0-or-later (from KDE Breeze). See `debian/copyright`.
