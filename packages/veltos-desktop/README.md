# veltos-desktop

The VeltOS desktop experience on top of stock KDE Plasma 6 (Debian trixie).
No Plasma code is forked: it is configuration, artwork, a layout script,
one small QML applet (VeltOS Start), two small session helpers and themes
derived from [Fluent-kde](https://github.com/vinceliuice/Fluent-kde).

## What a new user gets

- **Taskbar** at the bottom: Start button and pinned/running apps
  **centred** (Windows 11 style); on the right the tray (network, sound,
  battery, notifications; everything else behind the "^" arrow) and a
  Windows-sized clock with the date below the time. Pinned: File
  Explorer, Firefox, Settings.
- **VeltOS Start** menu (opens with the Windows/Meta key or Alt+F1):
  search field, "Pinned" grid with "All apps >", "Recommended" recent files,
  account button (settings, lock, sign out) and power button (sleep,
  restart, shut down). Right-click: Pin/Unpin to Start, Add to Desktop, etc.
  English and Turkish.
- **Windows 11 inspired look** everywhere, all in VeltOS colours:
  - application style (buttons, menus, lists, scroll bars): Kvantum theme
    `VeltOS` / `VeltOSDark`;
  - window frames: Aurorae theme `VeltOS` / `VeltOS-Dark` with Windows
    style minimise / maximise / close buttons on the right, the app icon
    and a left-aligned title on the left;
  - taskbar, Start and popups: Plasma theme `VeltOS` / `VeltOS-Dark`
    (acrylic-like see-through popups when the GPU can blur, opaque
    otherwise);
  - colour schemes `VeltOS Light` (default) / `VeltOS Dark`.
- **Windows-familiar names**: File Explorer, Terminal, Text Editor,
  Photos, Document Viewer, Archive Manager, Screenshot, Task Manager,
  System Information, Store, Disk Management, Firefox, and Control Panel
  for KDE's complete System Settings ("Settings" is VeltOS Settings,
  package `veltos-settings`). The names also appear inside the programs:
  window titles read "Home — File Explorer", not "Home — Dolphin".
  Searching for the Windows word ("notepad", "explorer", "cmd"...) or the
  old name finds the app. Developer and KDE-branded extras (Kate,
  Konqueror, KDE Connect, Vim, Winetricks, ...) are hidden from Start.
- **Sign-in screen** (SDDM theme `veltos`) like Windows 11: lock view with
  time and date; any key or click shows the picture, name and password
  field on the blurred wallpaper; power menu bottom right, other users
  bottom left. No session or desktop names are shown.
- Shut down, restart and sign out act at once (no confirmation screen),
  and signing in starts with a clean desktop.
- **Settings** without pages for KDE services VeltOS does not use
  (KDE Connect, Thunderbolt authorisation, telemetry, background services,
  activities, ...).
- **File Explorer** (Dolphin) laid out like Windows 11 File Explorer:
  address row (back, forward, up, address bar, search) and command row
  (New, cut, copy, paste, rename, delete, Sort, View, more;
  `dolphin/dolphinui.rc`), Details view with Name / Date modified / Type /
  Size, side bar sections "Quick access", "This PC", "Removable drives"
  with Home, Desktop, Downloads, Documents, Pictures, Music, Videos, Trash;
  no Network/Recent/Search sections; zip files open like folders; every
  window starts at Home.
- **Quick Settings** (`org.veltos.quicksettings`): one taskbar button with
  the network, sound and battery icons opens a Windows 11 style panel —
  Wi-Fi, Bluetooth, Airplane mode and Night light tiles, brightness and
  volume sliders, battery level and a Settings button. It uses the same
  Plasma components as KDE's tray applets, which are switched off in the
  tray for new users. The home folder has no
  "Templates" and "Public" folders (switched off in xdg-user-dirs).
- Fluent icons and cursors (`veltos-fluent-icons`), Inter UI font.
- **"Velt Bloom" wallpaper** (light and dark variants), branded login
  splash, lock screen and SDDM login background.

Existing users are not modified: Plasma runs the layout script only for
users without Plasma configuration, and the session helper only creates
files that do not exist yet.

## How it works

| Mechanism | Where | Notes |
|---|---|---|
| System-wide KDE defaults | `/etc/xdg/kdeglobals`, `kwinrc`, `plasmarc`, `dolphinrc`, `kcminputrc`, `kscreenlockerrc`, `ksplashrc` | Users override them in `~/.config`. `kdeglobals` also lists the hidden Settings pages (`[KDE Control Module Restrictions]`) and the light/dark global theme pair. |
| Global themes | `/usr/share/plasma/look-and-feel/org.veltos.{light,dark}/` | Switching between them switches colours, icons, Plasma theme, window frames and (via the `kvantum` / `kvantum-dark` style key) the application style. |
| Session script | `/etc/xdg/plasma-workspace/env/veltos-session.sh` | Sourced by Plasma before anything starts: puts `/var/lib/veltos/xdg` first in `XDG_DATA_DIRS`, puts the pseudo-language `en@veltos` / `tr@veltos` first in `LANGUAGE` and, if needed, runs `/usr/libexec/veltos/session-defaults`. |
| Program-name catalogs | `/usr/share/locale/{en,tr}@veltos/LC_MESSAGES/*.mo` (from `tools/app_titles.py`) | Translate only the programs' own names ("Dolphin" → "File Explorer"). KDE falls through to the real language for every other text, so no other package's files change. |
| Sign-in screen | `/usr/share/sddm/themes/veltos/` (`sddm/veltos/Main.qml`), selected in `/usr/lib/sddm/sddm.conf.d/10-veltos.conf` | Tested offscreen at build time with stand-ins for SDDM's objects (`tests/test_sddm.py`). |
| Session manager | `/etc/xdg/ksmserverrc` | `confirmLogout=false`, `loginMode=emptySession`. |
| `session-defaults` | `/usr/libexec/veltos/` | Creates `~/.config/Kvantum/kvantum.kvconfig` (Kvantum has no system-wide setting) and `~/.local/share/user-places.xbel` (File Explorer side bar, with the user's localised folder names). Never overwrites. |
| `update-app-names` | `/usr/libexec/veltos/` | Writes renamed/hidden copies of other packages' `.desktop` files to `/var/lib/veltos/xdg/applications/`. Run from `postinst` and from a dpkg trigger on `/usr/share/applications`, so the copies follow package updates. Other packages' files are never modified. |
| `update-plasma-overrides` | `/usr/libexec/veltos/`, specs in `/usr/share/veltos/plasma-overrides/*.json` (source: `plasma-overrides/`) | Windows 11 changes to Plasma components without forking them: copies the installed package (e.g. the system tray) to `/var/lib/veltos/xdg/plasma/plasmoids/`, applies exact text replacements and checks each matched; if one no longer matches after a Plasma update, the copy is removed and Plasma's own version is used. Run from `postinst` and a dpkg trigger on `/usr/share/plasma/plasmoids`; the image build fails if a change does not fit. Currently: the taskbar's hidden-icons flyout (icons only, small, no header). |
| GTK theme `VeltOS` | `/usr/share/themes/VeltOS/` (`tools/gtktheme.py`) | Breeze (colours follow the KDE colour scheme) with Windows 11 caption buttons drawn by the same code as the window frames. The session script switches users from Breeze to it. |
| Firefox caption buttons | `/usr/lib/firefox-esr/defaults/pref/veltos.js`, `/usr/lib/firefox-esr/veltos.cfg`, `/usr/share/veltos/firefox/caption-buttons.css` (`tools/firefox.py`) | Firefox draws its own round (libadwaita-like) title bar buttons on Linux and ignores the GTK theme; its autoconfig registers a style sheet with the 46 x 32 Windows 11 buttons and red close. |
| Power screen | `contents/logout/Logout.qml` of both global themes (`plasma/logout/`) | Power key / Ctrl+Alt+Del: dimmed desktop and a Windows-style card (Lock, Sign out, Sleep, Shut down, Restart, Cancel) instead of Breeze's full-screen buttons and countdown. |
| Desktop icons | `/usr/share/veltos/desktop/*.desktop`, copied by the session script | "This PC" and "Recycle Bin" on every user's desktop; a deleted one comes back at the next sign-in. |
| `session-fixups` | `/usr/libexec/veltos/`, started by `/etc/xdg/autostart/veltos-session-fixups.desktop` | One-shot at sign-in: with software rendering (llvmpipe, VMs without 3D) KWin's window captures are garbled, so the taskbar shows titles instead of window previews there. |
| Other defaults | `/etc/xdg/klaunchrc`, `usr/lib/sddm/sddm.conf.d/10-veltos.conf` | No app icon bouncing next to the pointer while a program starts; no on-screen keyboard on the sign-in screen (SDDM's default input method). |

## Source layout

| Path | What |
|---|---|
| `artwork/veltos-logo.svg` | **Master logo**: a "V" of two blue blades. Other packages keep checked copies. |
| `upstream.json` | Pinned Fluent-kde release (commit 44794f29c89d, SHA-256 checked) |
| `tools/fluent.py` | Derives the Kvantum, Aurorae and Plasma themes and colour schemes from Fluent-kde |
| `tools/bloom.py` | Procedural generator of the wallpaper (fixed seed → reproducible, original artwork) |
| `tools/build-assets.py` | Generates the whole installed tree into `build-assets/root/` |
| `plasma/layout.js` | Plasma 6 layout script (panel, widgets, wallpaper) |
| `plasma/startmenu/` | VeltOS Start applet (`org.veltos.startmenu`): QML, config schema, Turkish translation |
| `plasma/splash/Splash.qml` | Splash after signing in: blurred sign-in wallpaper, Windows dot spinner, "Welcome" (no progress bar) |
| `plasma/logout/Logout.qml` | Power screen (power key, Ctrl+Alt+Del) |
| `plasma/clock/` | Taskbar clock; its flyout is the Windows 11 notification centre (`NotificationCenter.qml`) above a calendar (`Calendar.qml`) |
| `plasma-overrides/` | Text replacements for Plasma components (see `update-plasma-overrides`) |
| `desktop/` | Desktop icons: This PC, Recycle Bin |
| `tools/gtktheme.py`, `tools/firefox.py` | GTK theme and Firefox style sheet with Windows 11 caption buttons |
| `tools/app_titles.py` | Program-name catalogs for the en@veltos / tr@veltos pseudo-languages |
| `sddm/veltos/` | VeltOS sign-in screen (SDDM theme) |
| `system/` | `veltos-session.sh`, `session-defaults`, `session-fixups`, `update-app-names`, `update-plasma-overrides` |
| `tests/` | Unit tests: asset build (incl. a full build), Fluent derivation, app names, session helpers |

## What is changed from Fluent-kde (`tools/fluent.py`)

- Fluent's Windows blue `#0078d4` → VeltOS accent (`#2F5EE6` light,
  `#4F7CFF` dark). The build fails if the colour disappears upstream.
- Removed artwork showing other brands: the Windows logo used as Plasma
  "start" icon, the Manjaro logo, a "KDE Desktop" badge.
- Window frames use Fluent's opaque ("solid") variant and a 1 px bottom
  border: the default variant is 75 % opaque and needs blur; without blur
  (VMs, software rendering) it showed the desktop through title bars and a
  1 px seam at the bottom of every window (seen in VM screenshots).
- Kvantum: translucent application windows off (lighter, no blur behind
  every window), inactive windows not faded, the light variant's
  translucent selection colour replaced by the accent (Kirigami apps fell
  back to Qt's default blue).
- Plasma theme: opaque panel/popup backgrounds by default; Fluent's
  translucent ones are kept in `translucent/`, which Plasma uses only when
  the blur effect is available.

## Development

Try changes in a live VM without rebuilding the ISO:
`build/run.sh packages veltos-desktop`, then either `build/run.sh preview`
(fresh VM, scripted screenshots in `out/preview/`) or a long-running VM
(`build/run.sh vm start`, `vm upload /tmp/debs /out/packages/...deb`,
`vm exec "apt-get install -y /tmp/debs/*.deb"`, reset the live user's
configuration and restart SDDM as `tests/boot/vmpreview.py` does,
`vm do "shot:name"`).

Plasma keeps compiled QML in `~/.cache/plasmashell/qmlcache`; packages built
from the same changelog entry carry the same file times, so after installing a
rebuilt `veltos-desktop` in a running VM delete that directory and restart
`plasma-plasmashell` (`systemctl --user restart plasma-plasmashell`).

## Known limitations

- Notification pop-ups (toasts) and the taskbar's window tooltip are still
  Plasma's design; the notification centre in the clock flyout is VeltOS'.
- Firefox's caption buttons come from a style sheet that depends on
  Firefox's internal class names (`.titlebar-button`); a Firefox update may
  need `tools/firefox.py` to follow. Firefox from other sources (Flatpak,
  Mozilla's .deb) is not covered.
- Program names inside the programs are replaced only for English and
  Turkish, and only for the strings listed in `tools/app_titles.py`
  (window titles, welcome pages); About dialogs and help menus still
  mention KDE and the original names in other places.
- The screen locker (after sign-in) is still Plasma's own; Plasma 6 loads
  it from the desktop shell package, which VeltOS does not replace yet.
- Global Theme preview images show the wallpaper, not a desktop screenshot.
- `theme.conf.user` in the Breeze SDDM theme directory is owned by this
  package; changing the login background in System Settings edits it.
- VeltOS Start uses Plasma's private `org.kde.plasma.private.kicker` models
  (as KDE's own launchers do); a Plasma upgrade may require adjustments.
  Plasma 6.3's `SystemModel` crashes plasmashell if it is created before
  the root model is populated — see the comment in `StartMenu.qml`.
- Visual checks so far were done in QEMU without 3D acceleration (no
  blur); real-GPU screenshots are still to be taken.

## Licences

Code GPL-3.0-or-later; artwork CC-BY-SA-4.0; themes and colour schemes
derived from Fluent-kde GPL-3.0 (Vince Liuice; Kvantum theme based on
KvAdapta by Tsu Jan); `ActionMenu.qml` adapted from KDE Kickoff
(GPL-2.0-or-later). See `debian/copyright`.
