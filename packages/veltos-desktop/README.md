# veltos-desktop

The VeltOS desktop experience on top of stock KDE Plasma 6 (Debian trixie).
No Plasma code is forked: it is configuration, artwork, a layout script and
one small QML applet (VeltOS Start).

## What a new user gets

- **Taskbar** at the bottom: Start button and pinned/running apps
  **centred** (Windows 11 style), tray, clock/calendar and show-desktop on
  the right. Pinned: Dolphin, Firefox ESR, Konsole, System Settings.
- **VeltOS Start** menu (opens with the Windows/Meta key or Alt+F1):
  search field, "Pinned" grid with "All apps >", "Recommended" recent files,
  account button (settings, lock, sign out) and power button (sleep,
  restart, shut down). Right-click: Pin/Unpin to Start, Add to Desktop, etc.
  English and Turkish.
- **VeltOS Light** global theme by default (soft, like Windows 11);
  **VeltOS Dark** selectable in System Settings → Colors & Themes.
- Fluent icons and cursors (`veltos-fluent-icons`), Inter UI font.
- **"Velt Bloom" wallpaper**: sky, sunrise glow, misty hills over a lake and
  a bloom of blue folded petals, with the VeltOS logo and name; light and
  dark variants (Plasma picks the one matching the colour scheme).
- Branded login splash, lock screen and SDDM login background.

Existing users are not modified: Plasma runs the layout script only for
users without Plasma configuration.

## Source layout

| Path | What |
|---|---|
| `artwork/veltos-logo.svg` | **Master logo**: a "V" of two blue blades. Other packages keep checked copies. |
| `tools/bloom.py` | Procedural generator of the wallpaper (fixed seed → reproducible, original artwork) |
| `tools/build-assets.py` | Generates the whole installed tree into `build-assets/root/` |
| `plasma/layout.js` | Plasma 6 layout script (panel, widgets, wallpaper) |
| `plasma/startmenu/` | VeltOS Start applet (`org.veltos.startmenu`): QML, config schema, Turkish translation |
| `plasma/splash/Splash.qml` | Login splash shown while Plasma starts |
| `tests/test_build_assets.py` | Unit tests incl. a full asset build and "every UI string translated" |

## Generated at build time

| Installed path | Content |
|---|---|
| `/usr/share/plasma/look-and-feel/org.veltos.{light,dark}/` | Global themes: metadata, defaults, layout script, splash, preview |
| `/usr/share/plasma/plasmoids/org.veltos.startmenu/` | VeltOS Start |
| `/usr/share/locale/*/LC_MESSAGES/plasma_applet_org.veltos.startmenu.mo` | Start menu translations |
| `/usr/share/color-schemes/VeltOS{Light,Dark}.colors` | Breeze schemes with VeltOS accent colours |
| `/etc/xdg/kdeglobals` | Defaults: VeltOS Light colours, Fluent icons, Inter font, global theme |
| `/etc/xdg/kcminputrc`, `kscreenlockerrc`, `ksplashrc` | Cursor theme, lock screen wallpaper, splash |
| `/usr/share/wallpapers/VeltOS/` | 7 resolutions × light/dark (16:9, 16:10, 21:9; cropped, never stretched) |
| `/usr/lib/sddm/sddm.conf.d/10-veltos.conf`, `/usr/share/sddm/themes/breeze/theme.conf.user` | Login screen theme, cursor and background |
| `/usr/share/icons/hicolor/scalable/apps/veltos-logo.svg` | Logo icon (`veltos-logo`) |

Build-Depends: `kde-style-breeze-data`, `librsvg2-bin`, `fonts-inter`
(wallpaper wordmark), `gettext`, `python3`.

## Development

Try changes in a live VM without rebuilding the ISO:
`build/run.sh packages && build/run.sh preview` (screenshots of the desktop,
Start menu, context menu, All apps, search and power menu in
`out/preview/`).

## Known limitations

- Global Theme preview images show the wallpaper, not a desktop screenshot.
- `theme.conf.user` in the Breeze SDDM theme directory is owned by this
  package; changing the login background in System Settings edits it.
- VeltOS Start uses Plasma's private `org.kde.plasma.private.kicker` models
  (as KDE's own launchers do); a Plasma upgrade may require adjustments.
  Plasma 6.3's `SystemModel` crashes plasmashell if it is created before
  the root model is populated — see the comment in `StartMenu.qml`.

## Licences

Code GPL-3.0-or-later; artwork CC-BY-SA-4.0; derived colour schemes
LGPL-2.0-or-later (from KDE Breeze); `ActionMenu.qml` adapted from KDE
Kickoff (GPL-2.0-or-later). See `debian/copyright`.
