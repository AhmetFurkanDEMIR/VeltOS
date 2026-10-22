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
- **VeltOS Start** menu (opens with the Windows/Meta key or Alt+F1), in
  the layout of Windows 11's Start of 2025: the search field at the top,
  then one scrolling page with "Pinned" (8 columns, two rows until "Show
  all"), "Recommended" (recent files, 3 columns, "Show all") and "All"
  with "View: Category / Grid / List". The category view groups the apps
  like Windows (Productivity, Utilities & tools, Creativity, Entertainment,
  Games, Social, Developer tools, Education, Other) from their desktop
  files (`/usr/libexec/veltos/start-categories`); a category needs three
  apps, the rest is "Other"; a card's first three icons start their apps,
  the card opens the category. Account button (settings, lock, sign out)
  and power button (sleep, restart, shut down) at the bottom.
  Right-click on an app: Pin/Unpin to Start, Add to Desktop, etc.
  Right-click on the Start button: Windows 11's quick link menu (Windows +
  X: Installed apps, Power Options, System, Network Connections, Disk
  Management, Terminal, Task Manager, Settings, File Explorer, Search,
  sign out/sleep/shut down/restart, Desktop) instead of KDE's "Edit
  Applications". English and Turkish.
- **Windows 11 inspired look** everywhere, all in VeltOS colours:
  - application style (buttons, menus, lists, scroll bars): Kvantum theme
    `VeltOS` / `VeltOSDark`;
  - window frames: Aurorae theme `VeltOS` / `VeltOS-Dark` with Windows
    style minimise / maximise / close buttons on the right, the app icon
    and a left-aligned title on the left; the title bar has the VeltOS
    apps' window colour, like Windows 11's Mica (no separate white bar);
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
- **Wallpapers**: "VeltOS Bloom" (default, soft translucent petals), "VeltOS Flow", "VeltOS Glow", "VeltOS Lake" (the first design) and the colour variants used by Settings' themes, "VeltOS Nebula" (purple glow), "VeltOS Ember" (crimson bloom), "VeltOS Tide" (teal flow) and "VeltOS Dawn" (silver flow), each light and dark with a preview of each (`tools/wallpapers.py`); branded login
  splash, lock screen and SDDM login background.

Existing users are not modified: Plasma runs the layout script only for
users without Plasma configuration, and the session helper only creates
files that do not exist yet.

## How it works

| Mechanism | Where | Notes |
|---|---|---|
| System-wide KDE defaults | `/etc/xdg/kdeglobals`, `kwinrc`, `plasmarc`, `dolphinrc`, `kcminputrc`, `kscreenlockerrc`, `ksplashrc` | Users override them in `~/.config`. `kdeglobals` also lists the hidden Settings pages (`[KDE Control Module Restrictions]`) and the light/dark global theme pair. |
| Global themes | `/usr/share/plasma/look-and-feel/org.veltos.{light,dark}/` | Switching between them switches colours, icons, Plasma theme, window frames and (via the `kvantum` / `kvantum-dark` style key) the application style. |
| Session script | `/etc/xdg/plasma-workspace/env/veltos-session.sh` | Sourced by Plasma before anything starts: puts `/var/lib/veltos/xdg` first in `XDG_DATA_DIRS`, puts the pseudo-language `en@veltos` / `tr@veltos` first in `LANGUAGE` and, if needed, runs `/usr/libexec/veltos/session-defaults`. Where `needs-software-rendering` says so (VirtualBox without 3D acceleration) it exports `LIBGL_ALWAYS_SOFTWARE=1` (Mesa llvmpipe) so the session renders at all — only that: KWin's QPainter compositor left Task View's previews black and Qt Quick's software scene graph drew boxes under the desktop labels. |
| Program-name catalogs | `/usr/share/locale/{en,tr}@veltos/LC_MESSAGES/*.mo` (from `tools/app_titles.py`) | Translate only the programs' own names ("Dolphin" → "File Explorer"). KDE falls through to the real language for every other text, so no other package's files change. |
| Sign-in screen | `/usr/share/sddm/themes/veltos/` (`sddm/veltos/Main.qml`), selected in `/usr/lib/sddm/sddm.conf.d/10-veltos.conf` | Tested offscreen at build time with stand-ins for SDDM's objects (`tests/test_sddm.py`). |
| Session manager | `/etc/xdg/ksmserverrc` | `confirmLogout=false`, `loginMode=emptySession`. |
| `session-defaults` | `/usr/libexec/veltos/` | Creates `~/.config/Kvantum/kvantum.kvconfig` (Kvantum has no system-wide setting) and `~/.local/share/user-places.xbel` (File Explorer side bar, with the user's localised folder names). Never overwrites. |
| `update-app-names` | `/usr/libexec/veltos/` | Writes renamed/hidden copies of other packages' `.desktop` files to `/var/lib/veltos/xdg/applications/` (and adds program options where needed: Terminal's `--notransparency`; removes Spectacle's global shortcuts, also through `/var/lib/veltos/xdg/kglobalaccel/`, because Print Screen belongs to VeltOS Snipping Tool). Also writes VeltOS' default apps for file types (`kde-mimeapps.list` there, from `DEFAULT_APPS`: the first installed VeltOS app per type, e.g. text files → Notepad), which Plasma reads before KDE's own list. Run from `postinst` and from a dpkg trigger on `/usr/share/applications`, so the copies follow package updates. Other packages' files are never modified. |
| `update-plasma-overrides` | `/usr/libexec/veltos/`, specs in `/usr/share/veltos/plasma-overrides/*.json` (source: `plasma-overrides/`) | Windows 11 changes to Plasma and KWin components without forking them: copies the installed package (e.g. the system tray) to `/var/lib/veltos/xdg/plasma/plasmoids/` (shells: `plasma/shells/`, KWin QML: `kwin/`), applies exact text replacements or whole-file replacements (only while the original has the recorded sha256) and checks each matched; if one no longer fits after an update, the copy is removed and the original is used. Run from `postinst` and dpkg triggers on `/usr/share/plasma/plasmoids`, `/usr/share/plasma/shells` and `/usr/share/kwin/aurorae`; the image build fails if a change does not fit. Currently: the taskbar's hidden-icons flyout (icons only, small, no header) and item flyouts without settings/pin buttons; notification toasts like Windows 11 (bottom-right, picture left, equal buttons, newest at the bottom, no tray bell); "Safely Remove Hardware" (drives) flyout; taskbar button menus ("Pin to taskbar", no KDE settings), tooltips, no spinner on starting apps and a stacked button (no "+") for several windows of one app; the Windows 11 lock screen (desktop shell); square close-button hover on maximised windows (KWin's Aurorae); the desktop's Windows 11 menus, New, Refresh and protected icons (`org.kde.desktopcontainment`, a file added with `"add"`). |
| GTK theme `VeltOS` | `/usr/share/themes/VeltOS/` (`tools/gtktheme.py`) | Breeze (colours follow the KDE colour scheme) with Windows 11 caption buttons drawn by the same code as the window frames. The session script switches users from Breeze to it. |
| Firefox caption buttons | `/usr/lib/firefox-esr/defaults/pref/veltos.js`, `/usr/lib/firefox-esr/veltos.cfg`, `/usr/share/veltos/firefox/caption-buttons.css` (`tools/firefox.py`) | Firefox draws its own round (libadwaita-like) title bar buttons on Linux and ignores the GTK theme; its autoconfig registers a style sheet with the 46 x 32 Windows 11 buttons and red close. |
| Ctrl+Alt+Del screen | `contents/logout/Logout.qml` of both global themes (`plasma/logout/`) | Windows' security options: blurred sign-in wallpaper, Lock, Switch user, Sign out, Change a password, Task Manager, Cancel, power menu bottom right. A program asking to shut down gets a small Windows-style card instead. |
| Power key | `/etc/xdg/powerdevilrc` | Shuts down, Windows' default (also VirtualBox's "send the shutdown signal"). |
| Locked taskbar | `/etc/xdg/kdeglobals` `[KDE Action Restrictions]`, `session-fixups`, `context-menus` | No widgets added/moved/removed and no KDE "Configure …" dialogs; desktop menu with the file entries only, no menu on the empty taskbar. |
| Desktop icons | `/usr/share/veltos/desktop/*.desktop`, copied by the session script | "This PC", "Recycle Bin" and "VeltOS Store" on every user's desktop, like Windows' system icons: a deleted one comes back at the next sign-in, and the desktop's menu offers no Delete, Rename or Cut for them (see the desktop override below). The Recycle Bin's icon follows the trash (`veltos-trash-icon.path`, a systemd user path unit on `~/.local/share/Trash`, runs `trash-icon`, which touches the launcher). |
| Desktop (Windows 11 behaviour) | `plasma-overrides/org.kde.desktopcontainment.json`, `plasma-overrides/files/desktop/VeltOSDesktop.qml` (added to Plasma's folder view by `update-plasma-overrides`), `/usr/libexec/veltos/desktop-new`, catalog `/usr/share/locale/tr/LC_MESSAGES/veltos-desktop.mo` (`translations/tr.po`, `i18nd`) | Right-click on the desktop opens Windows 11's menu (View: icon sizes, auto arrange; Sort by; Refresh; Paste; New: Folder, Text Document; Display settings; Personalize; Open in Terminal), never Plasma's containment menu (no Edit Mode, no Add Widgets). New > Folder / Text Document make the item with Windows' name ("New folder", "New folder (2)", …; `desktop-new`) and open its name for editing at once, as Windows does (Plasma asked in a dialog); Refresh and F5 blink the icons; the Recycle Bin, This PC and the Store have a small menu of their own (Open, Empty Recycle Bin → File Explorer's Windows 11 question, Properties) and the Delete key, F2 and Ctrl+X skip them; the name box has square corners. Texts come from VeltOS' own catalog, so KDE's translations are untouched. |
| `session-fixups` | `/usr/libexec/veltos/`, started by `/etc/xdg/autostart/veltos-session-fixups.desktop` | One-shot at sign-in: locks the taskbar's items; display scale in 25 % steps for new screens (`display-scale`); with software rendering (llvmpipe, VMs without 3D) KWin's window captures are garbled, so the taskbar shows titles instead of window previews there. |
| `context-menus` | `/usr/libexec/veltos/`, run by `veltos-session.sh` before plasmashell starts | Right-click menu options of the desktop and the taskbar (`[ActionPlugins]` in the Plasma layout file). |
| `needs-software-rendering` | `/usr/libexec/veltos/` | The one rule for when VeltOS renders in software instead of with the display driver's OpenGL (exit status 0 = yes): VirtualBox (DMI) **without working 3D acceleration**. With 3D off, Mesa has already fallen back to llvmpipe on the GBM platform (`eglinfo -B`, no display needed); with 3D on the same VMSVGA display gives real OpenGL (renderer "SVGA3D") and nothing is forced. Nothing in sysfs tells the two apart. Only VirtualBox is probed. Used by `veltos-session.sh` and `sddm-virtualbox-env`. |
| `greeter-compositor` | `/usr/libexec/veltos/`, SDDM's `CompositorCommand` | Starts KWin for the sign-in screen with Plasma's own arguments; when `/run/veltos/software-rendering` exists (left by `sddm-virtualbox-env`), with KWin's software compositor and Mesa's llvmpipe (the session does the same in `veltos-session.sh`). |
| `sddm-virtualbox-env` | `/usr/libexec/veltos/`, `ExecStartPre` of `sddm.service` (`/usr/lib/systemd/system/sddm.service.d/veltos-virtualbox.conf`) | Before SDDM starts, asks `needs-software-rendering` (as root, so the render node can be probed). Yes: writes `/etc/sddm.conf.d/zz-veltos-virtualbox.conf` (the vendor `GreeterEnvironment` plus `LIBGL_ALWAYS_SOFTWARE=1`, so the sign-in screen's QML renders with llvmpipe) and the marker `/run/veltos/software-rendering` for `greeter-compositor`; no: removes both. Decided at every start, so a disk moved between a VM and real hardware, or a VM whose 3D setting changed, does the right thing. |
| Plasma services without the portal theme | `/usr/lib/systemd/user/plasma-*.service.d/veltos-portal-theme.conf` (generated by `tools/build-assets.py`, list `PLASMA_SERVICES`) | `Environment=QT_QPA_PLATFORMTHEME=kde` for Plasma's own services (kwin, ksplash, kded6, kcminit, ksmserver, kactivitymanagerd, powerdevil, KDE's portal backend, ...) — not plasmashell, whose environment programs started from Start inherit: it keeps the portal theme for their file dialogs. The session gives every program the portal platform theme for the Windows 11 file dialogs; a Qt program starting with it asks the portal first, and at session start the portal cannot be up yet (its backends are Wayland clients of KWin and Qt programs themselves): each of those services blocked 25 s and the portal timed out after 90 s, plasmashell came after ~95 s instead of ~18 s (2026-10-22). Programs the user starts keep the portal theme. |
| Task View | `/usr/share/kwin/effects/veltostaskview/` (`kwin/effects/veltostaskview/`) | Windows 11 Task View as a KWin QML scene effect (public `org.kde.kwin` API): window thumbnails with icon, title and close button; desktops strip with "New desktop" and remove, pointing at a desktop shows its windows; Meta+Tab and the taskbar's Task View button. |
| Terminal | `/usr/share/konsole/VeltOS Light.profile`, `VeltOS Dark.profile`, `VeltOS-OneHalfLight.colorscheme`, `VeltOS-Campbell.colorscheme`, `/usr/share/veltos/konsole/tabs-*.css`, `/usr/share/kxmlgui5/konsole/*.rc`, `/etc/xdg/konsolerc`, `/usr/libexec/veltos/terminal-theme` (source: `konsole/`, `system/`) | Konsole like Windows Terminal, following the light/dark theme (`terminal-theme`, run at sign-in and by Settings' theme switch; open terminals switch colours over D-Bus): One Half Light or Campbell colours, rounded tabs with the selected one in the terminal colour (Konsole reads tab styles only from a file: `TabBarUseUserStyleSheet`), Cascadia Mono 12 (fonts-cascadia-code), bar cursor, 120 x 30, tabs always shown with a "+" button, no toolbars (Konsole's own window layout files without the toolbars, same number so KXMLGUI prefers them), opaque window (`--notransparency` added by `update-app-names`: Konsole's see-through window let other windows show through its tab bar). |
| Sounds | `/usr/share/sounds/veltos/` (`tools/sounds.py`), `[Sounds] Theme=veltos` in kdeglobals, `/etc/xdg/plasma_workspace.notifyrc` | Original system sounds synthesised at build time (Windows' sounds are not shipped); a chime when the desktop appears after signing in. |
| Animations | `KWIN_EFFECTS_FORCE_ANIMATIONS=1` in the session script | KWin switches its animations off with software rendering (most VMs); VeltOS keeps them on (open/close, minimise, maximise, sliding popups, desktop switching). |
| Clipboard | `/etc/xdg/klipperrc` | Plasma's clipboard keeps pictures (Klipper ignores them by default), so a snip stays pasteable after Snipping Tool ends. |
| Other defaults | `/etc/xdg/klaunchrc`, `usr/lib/sddm/sddm.conf.d/10-veltos.conf` | No app icon bouncing next to the pointer while a program starts; no on-screen keyboard on the sign-in screen (SDDM's default input method). |

## Source layout

| Path | What |
|---|---|
| `artwork/veltos-logo.svg` | **Master logo**: a "V" of two blue blades. Other packages keep checked copies. |
| `upstream.json` | Pinned Fluent-kde release (commit 44794f29c89d, SHA-256 checked) |
| `tools/fluent.py` | Derives the Kvantum, Aurorae and Plasma themes and colour schemes from Fluent-kde |
| `tools/wallpapers.py` | Procedural generator of the wallpapers (Bloom, Flow, Glow and their colour variants; reproducible, original artwork) |
| `tools/bloom.py` | The first wallpaper design, kept as "VeltOS Lake" |
| `tools/build-assets.py` | Generates the whole installed tree into `build-assets/root/` |
| `plasma/layout.js` | Plasma 6 layout script (panel, widgets, wallpaper) |
| `plasma/startmenu/` | VeltOS Start applet (`org.veltos.startmenu`): QML, config schema, Turkish translation |
| `plasma/splash/Splash.qml` | Splash after signing in: blurred sign-in wallpaper, Windows dot spinner, "Welcome" (no progress bar) |
| `plasma/logout/Logout.qml` | Ctrl+Alt+Del security options screen, shut-down card |
| `plasma/clock/` | Taskbar clock; its flyout is the Windows 11 notification centre (`NotificationCenter.qml`) above a calendar (`Calendar.qml`) |
| `plasma-overrides/` | Changes to Plasma and KWin components (see `update-plasma-overrides`); `files/` holds whole replacement files |
| `desktop/` | Desktop icons: This PC, Recycle Bin, VeltOS Store |
| `konsole/` | Terminal profile, Campbell colour scheme, Konsole window layout without toolbars |
| `tools/gtktheme.py`, `tools/firefox.py` | GTK theme and Firefox style sheet with Windows 11 caption buttons |
| `tools/app_titles.py` | Program-name catalogs for the en@veltos / tr@veltos pseudo-languages |
| `sddm/veltos/` | VeltOS sign-in screen (SDDM theme) |
| `system/` | `veltos-session.sh`, `context-menus`, `desktop-new`, `display-scale`, `greeter-compositor`, `needs-software-rendering`, `sddm-virtualbox-env`, `session-defaults`, `session-fixups`, `terminal-theme`, `trash-icon`, `update-app-names`, `update-plasma-overrides` |
| `translations/` | The `veltos-desktop` message catalog (Turkish): texts VeltOS adds to Plasma's own components |
| `tests/` | Unit tests: asset build (incl. a full build), Fluent derivation, app names, session helpers; `tests/data/` holds the Plasma QML the overrides apply to |

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

## Added 2026-10-21 (evening)

- **Search window** (`plasma/search`): the taskbar's search box opens
  Windows 11's search window (centred like Start, through the
  `org.kde.plasma.desktop` override): a search field, "Top apps" (Start's
  pinned apps) while empty, results on the left with the best match and
  "Open" on the right while typing (Plasma's runners).
- **Progress on the taskbar** as a thin accent bar under the icon
  (`plasma-overrides/files/taskmanager/TaskProgressOverlay.qml` replaces
  Plasma's fill behind the icon).
- **Sign-in screen in KWin on Wayland** (`10-veltos.conf`:
  `DisplayServer=wayland`, Plasma's `CompositorCommand`), so the greeter
  and the session pick the same screen mode (the X11 greeter came up
  small in VirtualBox/QEMU).
- **Session environment** for the portal file dialogs
  (`veltos-session.sh`: `QT_QPA_PLATFORMTHEME=xdgdesktopportal`,
  `GTK_USE_PORTAL=1`; see veltos-explorer), Firefox/Mail preference
  `widget.use-xdg-desktop-portal.file-picker=1`, Firefox's downloads
  panel in the Windows 11 look (`firefox/downloads.css`).
- **Sounds** (`tools/sounds.py`) synthesised softer (slow attack, fewer
  partials, detuned second voice, low-pass, small reverb, -6 dBFS) and a
  new `alarm-clock-elapsed` for VeltOS Clock.
- File indexing off until a user turns it on (`/etc/xdg/baloofilerc`);
  KDE buttons without icons (`ShowIconsOnPushButtons=false`).

## Added 2026-10-22

- **Desktop** (`plasma-overrides/org.kde.desktopcontainment.json`,
  `files/desktop/VeltOSDesktop.qml`): Windows 11's right-click menu, New
  with the name box open at once, Refresh that blinks the icons, the
  Recycle Bin / This PC / Store without Delete (and the Store comes back
  like the other two). `update-plasma-overrides` can now add a file to a
  Plasma package (`"add"`).
- **Volume / brightness OSD** at the bottom of the screen like Windows 11
  (`plasma-overrides/files/osd/`, a shell-package override: plasmashell
  6.3 loads the OSD from the desktop shell package, not from the global
  theme; KWin centres OSD windows at two thirds of the screen, so the
  window is made tall enough for its bottom edge to end above the
  taskbar).
- **Task View** (`kwin/effects/veltostaskview`): desktop cards show their
  windows; right-click or double-click switches to the desktop; the
  selection frame wraps the card.
- **Search window** (`plasma/search`): a plain field with the accent line
  under it (no frame), results in a column (rows overlapped in the list
  view), the best-match card filled again, only Windows' kinds of results
  (no KDE settings modules: `runners`). No box around the taskbar's search
  box while its window is open (Plasma's expanded-applet highlight in the
  shell's `CompactApplet.qml` is off for it), and the panel's focus box
  (`Panel.qml`) shows only for Tab navigation.
- **Taskbar in the accent colour** (`plasma-overrides/files/shell/TaskbarTint.qml`,
  added to Plasma's panel view): a soft accent glow behind the centred
  icons over the light/dark background, cross-fading and sending one band
  of colour across the bar when the accent or the mode changes; nothing
  moves at rest. The VeltOS Plasma themes no longer carry their own
  `colors` file (`tools/fluent.py`), so the taskbar, Start and the
  flyouts follow the accent chosen in Settings.
- **Desktop icons** without Plasma's hover buttons (selection markers,
  folder preview pop-ups: `layout.js`, `session-fixups`); the desktop
  menu's Display settings / Personalize entries use line icons.
- **Start** categories: Office (Word, Excel, PowerPoint, PDF Reader);
  Media Player under Entertainment (every non-empty category is shown).
- **LibreOffice's start-up window** stays off the taskbar
  (`/etc/xdg/kwinrulesrc`, window class `soffice`); moving files to the
  Recycle Bin asks nothing (`/etc/xdg/kiorc`).
- Fluent's `preferences-color` / `preferences-desktop-theme` and a
  `veltos-colour-mode` symbolic icon (veltos-fluent-icons) for Settings'
  Personalization rows.

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
