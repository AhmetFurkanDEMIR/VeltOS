# veltos-desktop

The VeltOS desktop experience on top of stock KDE Plasma 6 (Debian trixie).
No Plasma code is forked: it is configuration, artwork, a layout script,
one small QML applet (VeltOS Start), two small session helpers and themes
derived from [Fluent-kde](https://github.com/vinceliuice/Fluent-kde).

## What a new user gets

- **Taskbar** at the bottom: Start button and pinned/running apps
  **centred** (Windows 11 style); on the right the tray (network, sound,
  battery, notifications; everything else behind the "^" arrow) and a
  Windows-sized clock with the date below the time, then Show desktop at
  the screen's right edge. Pinned, left to right, like a fresh Windows 11
  PC (product owner, 2026-10-22): File Explorer, Firefox, Settings, Store,
  Camera, Photos, Media Player. Pointing at a running app shows its
  window previews (KWin, `veltostaskbarpreview`); right-clicking the
  empty taskbar offers Task Manager and Taskbar settings.
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
  App results in taskbar Search retain their runner-provided actions,
  including Add to Desktop. Recent local files in Start and Search also
  offer **Create shortcut on desktop**.
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
    otherwise; light popups in Settings' white, no line around popups,
    which Fluent drew in its shadow pieces);
  - colour schemes `VeltOS Light` (default) / `VeltOS Dark`.
- **Windows-familiar names**: File Explorer, Terminal, Text Editor,
  Photos, Document Viewer, Archive Manager, Screenshot, Task Manager,
  System Information, Store, Disk Management and Firefox ("Settings" is
  VeltOS Settings, package `veltos-settings`; KDE's System Settings is
  hidden, its programs open VeltOS Settings and, since 2026-10-22, only
  root may run KDE's own). The names also appear inside the programs:
  window titles read "Home — File Explorer", not "Home — Dolphin".
  Searching for the Windows word ("notepad", "explorer", "cmd"...) or the
  old name finds the app. Thunderbird is "VeltOS Mail" in every language
  (product owner, 2026-10-22; "Mail", "Posta" and "Outlook" stay search
  words). Developer and KDE-branded extras (Kate, Konqueror, KDE Connect,
  Vim, Winetricks, ...) are hidden from Start, and so is LibreOffice Draw,
  which stays installed because PowerPoint (`libreoffice-impress`) depends
  on it but is offered for no file type either (product owner,
  2026-10-22).
- **Sign-in screen** (SDDM theme `veltos`) like Windows 11: lock view with
  time and date; any key or click shows the picture, name and password
  field on the blurred wallpaper; power menu bottom right, other users
  bottom left with their account pictures. No session or desktop names are shown: it starts Plasma on
  Wayland, or Plasma on X11 when the screen itself runs on X11 — at a
  start without a graphics driver (veltos-recovery's Safe mode), where
  Wayland cannot run; SDDM remembering the X11 session afterwards does not
  carry over to normal starts.
- Shut down, restart and sign out act at once (no confirmation screen),
  and signing in starts with a clean desktop.
- **Settings** without pages for KDE services VeltOS does not use
  (KDE Connect, Thunderbolt authorisation, telemetry, background services,
  activities, ...).
- **File Explorer** is VeltOS File Explorer (package `veltos-explorer`);
  Dolphin is not in the image. The Dolphin defaults this package still
  ships (`dolphin/dolphinui.rc`, `/etc/xdg/dolphinrc`: Windows 11 style
  address and command rows, Details view, "Quick access" / "This PC" side
  bar, every window at Home) only matter on a system where a user
  installs Dolphin themselves.
- **Web search** (taskbar search and Start, 2026-10-24): the last row
  searches the web with Google ("Search with Google", a four-colour
  magnifier drawn by VeltOS), the best match when nothing else is found;
  KDE's web shortcuts runner (DuckDuckGo) is not used.
- **VeltOS AI button** (`org.veltos.aibutton`, 2026-10-26): Windows 11's
  Copilot button after the clock; a click opens or closes the VeltOS AI
  pane, its menu hides it or opens Settings > Apps > VeltOS AI
  (`shown`, also Settings > Personalization > Taskbar). session-fixups
  adds it once to taskbars made before it.
- **No KRunner** (2026-10-26): `/etc/xdg/krunnerrc`
  ActivateWhenTypingOnDesktop=false and its global shortcuts off
  (update-app-names); the taskbar's search is the only search box.
- **Desktop files through File Explorer** (2026-10-26): paste (Ctrl+V and
  the menu) runs File Explorer's copy window, Shift+Delete its "Delete
  File" question; plasmashell's own desktop entry is named "File Explorer"
  (update-app-names `ICONS`), so what plasmashell still shows carries that
  name.
- **Quick Settings** (`org.veltos.quicksettings`): one taskbar button with
  the network, sound and battery icons opens a Windows 11 style panel —
  Wi-Fi, Bluetooth, Airplane mode, Mobile hotspot, Night light and Power
  mode tiles (the hotspot's arrow shows its name, password, band and
  devices through VeltOS Settings' `/usr/libexec/veltos/hotspot`; the
  power mode page has three cards with Plugged in / On battery tabs and
  `system/power-mode` keeps a mode per power source; the battery is
  always on the button and at the bottom left, opening Power & battery),
  brightness and volume sliders, battery level and a Settings button. Power
  mode offers the profiles supported by power-profiles-daemon and
  automatically selects performance on AC or power-saver on battery when
  available, with balanced or another supported profile as a fallback. The
  arrow on the
  Wi-Fi and Bluetooth tiles slides in their lists, as in Windows 11
  (2026-10-24): Wi-Fi networks with signal and security, the connected
  one with Properties and Disconnect, others with "Connect automatically"
  and Connect, the network security key asked in place; paired Bluetooth
  devices with their state and battery, Connect / Disconnect, and new
  devices found nearby with Pair (codes are confirmed in Plasma's
  Bluetooth notification; a paired device is trusted and connected).
  Bluetooth device rows use a plain, monochrome Bluetooth glyph instead of
  BlueZ's blue device artwork; the active tile keeps its accent-colour state.
  While something plays, Windows 11's media card sits 12 px above the
  panel (`MediaCard.qml`, 2026-10-25): the app's icon and name, title,
  artist, cover, Previous / Play-Pause / Next and arrows between players,
  on Plasma's MPRIS model; Plasma's own media item is not in the tray
  (`session-fixups` removes it from older trays). It uses the same Plasma
  components as KDE's tray applets (NetworkModel and Handler, BluezQt and
  bluedevil's models, Mpris2Model), which are switched off in the tray for
  new users. The home folder has no
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
| Session script | `/etc/xdg/plasma-workspace/env/veltos-session.sh` | Sourced by Plasma before anything starts: puts `/var/lib/veltos/xdg` first in `XDG_DATA_DIRS`, puts the pseudo-language `en@veltos` / `tr@veltos` first in `LANGUAGE` and, if needed, runs `/usr/libexec/veltos/session-defaults`. Where `needs-software-rendering` says so (VirtualBox without 3D acceleration) it exports `LIBGL_ALWAYS_SOFTWARE=1` (Mesa llvmpipe) so the session renders at all — only that: KWin's QPainter compositor left Task View's previews black and Qt Quick's software scene graph drew boxes under the desktop labels. It also asks the desktop guard (below) to protect the desktop's system icons, in the background so sign-in does not wait. |
| Program-name catalogs | `/usr/share/locale/{en,tr}@veltos/LC_MESSAGES/*.mo` (from `tools/app_titles.py`) | Translate only the programs' own names ("Dolphin" → "File Explorer"). KDE falls through to the real language for every other text, so no other package's files change. |
| Sign-in screen | `/usr/share/sddm/themes/veltos/` (`sddm/veltos/Main.qml`), selected in `/usr/lib/sddm/sddm.conf.d/10-veltos.conf` | Tested offscreen at build time with stand-ins for SDDM's objects (`tests/test_sddm.py`). |
| Session manager | `/etc/xdg/ksmserverrc` | `confirmLogout=false`, `loginMode=emptySession`. |
| `session-defaults` | `/usr/libexec/veltos/` | Creates `~/.config/Kvantum/kvantum.kvconfig` (Kvantum has no system-wide setting) and `~/.local/share/user-places.xbel` (File Explorer side bar, with the user's localised folder names). Never overwrites. |
| `update-app-names` | `/usr/libexec/veltos/` | Writes renamed/hidden copies of other packages' `.desktop` files to `/var/lib/veltos/xdg/applications/` (and adds program options where needed: Terminal's `--notransparency`; removes Spectacle's global shortcuts, also through `/var/lib/veltos/xdg/kglobalaccel/`, because Print Screen belongs to VeltOS Snipping Tool; hides KScreen's display switcher there too, because Windows + P belongs to VeltOS Settings' Project flyout). Also writes VeltOS' default apps for file types (`kde-mimeapps.list` there, from `DEFAULT_APPS`: the first installed VeltOS app per type, e.g. text files → Notepad), which Plasma reads before KDE's own list. Run from `postinst` and from dpkg triggers on `/usr/share/applications` and `/usr/share/kglobalaccel`, so the copies follow package updates. Other packages' files are never modified. |
| `update-plasma-overrides` | `/usr/libexec/veltos/`, specs in `/usr/share/veltos/plasma-overrides/*.json` (source: `plasma-overrides/`) | Windows 11 changes to Plasma and KWin components without forking them: copies the installed package (e.g. the system tray) to `/var/lib/veltos/xdg/plasma/plasmoids/` (shells: `plasma/shells/`, KWin QML: `kwin/`), applies exact text replacements or whole-file replacements (only while the original has the recorded sha256) and checks each matched; if one no longer fits after an update, the copy is removed and the original is used. Run from `postinst` and dpkg triggers on `/usr/share/plasma/plasmoids`, `/usr/share/plasma/shells` and `/usr/share/kwin/aurorae`; the image build fails if a change does not fit. Currently: the taskbar's hidden-icons flyout (icons only, small, no header; the arrow's tooltip goes away when it is clicked and does not cover the open flyout) and item flyouts without settings/pin buttons; the clipboard flyout as Windows 11's clipboard history (`org.kde.plasma.clipboard`, `files/clipboard/main.qml`); notification toasts like Windows 11 (bottom-right, picture left, equal buttons, newest at the bottom, no tray bell, Windows 11's "..." menu, jobs with Windows 11's progress: `files/notifications/JobItem.qml`); "Safely Remove Hardware" (drives) flyout as Windows 11's menu: "Eject <drive>" entries without the tray heading, a notification when the drive can be unplugged or is in use (`files/devicenotifier/DeviceItem.qml`); taskbar button menus ("Pin to taskbar", no KDE settings), no spinner on starting apps, a stacked button (no "+") for several windows of one app, window previews left to KWin (Plasma's tooltip only names pinned apps that are not running), a round speaker badge on apps playing sound (`files/taskmanager/AudioStream.qml` keeps speaker and mute badges off app icons); Windows 11's taskbar menu and Show desktop at the screen's edge (`org.kde.panel`, `files/panel/VeltOSTaskbarMenu.qml` added with `"add"`); the Windows 11 lock screen (desktop shell); square close-button hover on maximised windows, the Office apps' coloured title bars and modal dialogs with only a Close button (KWin's Aurorae); the desktop's Windows 11 menus, New, Refresh, protected icons and the full/empty Recycle Bin (`org.kde.desktopcontainment`, a file added with `"add"`). |
| GTK theme `VeltOS` | `/usr/share/themes/VeltOS/` (`tools/gtktheme.py`) | Breeze (colours follow the KDE colour scheme) with Windows 11 caption buttons drawn by the same code as the window frames. The session script switches users from Breeze to it. |
| Firefox caption buttons | `/usr/lib/firefox-esr/defaults/pref/veltos.js`, `/usr/lib/firefox-esr/veltos.cfg`, `/usr/share/veltos/firefox/caption-buttons.css` (`tools/firefox.py`) | Firefox draws its own round (libadwaita-like) title bar buttons on Linux and ignores the GTK theme; its autoconfig registers a style sheet with the 46 x 32 Windows 11 buttons and red close. |
| VeltOS Mail (Thunderbird) | `/usr/lib/thunderbird/veltos.cfg` (autoconfig), `/usr/share/thunderbird/defaults/pref/veltos.js`, `/usr/share/veltos/mail/mail.css` (`mail/mail.css`), `/usr/share/veltos/mail/mail-header.css` (`tools/firefox.py`) | Thunderbird as "VeltOS Mail" in the look of Outlook (product owner, 2026-10-22). The autoconfig registers the style sheets, puts "VeltOS Mail" in the window titles (the main window's `titlemodifier`, other windows' titles), and sets Outlook's defaults where the user has none (Thunderbird's xulstore): the simplified ribbon as the mail toolbar (New mail, Delete, Archive, Report, Move to, Reply, Reply all, Forward, Read/Unread, Tag), the reading pane header (big sender picture, actions as icons) and a new message window without a menu bar (Alt shows it). `mail.css`: Outlook's blue title band with "VeltOS Mail", the search box in it and white window glyphs (`mail-header.css`), the ribbon on white below; the reading pane with the subject first and large and a round initial in the accent; the new message window with Send filled in the accent and Windows 11 fields; the account page without Thunderbird's story, donation request, links, version and watermark ("Welcome to VeltOS Mail"); the add-account card with Outlook's Continue button and "VeltOS Mail" texts; tabs in Windows 11's look. Preferences: no tab bar while one tab is open (`mail.tabs.autoHide`), people by their names only in the message list (`mail.addressDisplayFormat=2`). |
| Ctrl+Alt+Del screen | `contents/logout/Logout.qml` of both global themes (`plasma/logout/`) | Windows' security options: blurred sign-in wallpaper, Lock, Switch user, Sign out, Change a password, Task Manager, Cancel, power menu bottom right. A program asking to shut down gets a small Windows-style card instead. |
| Power key | `/etc/xdg/powerdevilrc` | Shuts down, Windows' default (also VirtualBox's "send the shutdown signal"). |
| Locked taskbar | `/etc/xdg/kdeglobals` `[KDE Action Restrictions]`, `session-fixups`, `context-menus` | No widgets added/moved/removed and no KDE "Configure …" dialogs; desktop menu with the file entries only. The empty taskbar's menu is Windows 11's (Task Manager, Taskbar settings: the `org.kde.panel` override), never Plasma's Edit Mode / Add Widgets. VeltOS Settings > Personalization > Taskbar changes the taskbar through plasmashell's scripting interface; for it the VeltOS applets have configuration keys of their own (`contents/config/main.xml`): `org.veltos.search` `mode` (0 hidden, 1 search icon only, 2 icon and label, 3 search box), `org.veltos.taskview` `shown`, `org.veltos.showdesktop` `enabled` (off: a narrow empty end remains). |
| Desktop icons | `/usr/share/veltos/desktop/*.desktop`, copied by the session script and guarded by the desktop guard | "This PC", "Recycle Bin" and "VeltOS Store" on every user's desktop, like Windows' system icons: a deleted one comes back at the next sign-in, the desktop's menu offers no Delete, Rename or Cut for them (see the desktop override below), File Explorer refuses them too (veltos-explorer), and the desktop guard makes them root's so not even a terminal removes them (product owner, 2026-10-22). The Recycle Bin's icon shows whether the bin is full: the desktop override watches `trash:/` and picks `user-trash-full` or `user-trash` (KIO's own `EmptyIcon` in the launcher was not re-read by the desktop). `veltos-trash-icon.path`, a systemd user path unit on `~/.local/share/Trash`, still runs `trash-icon`, which asks the guard to move the root-owned launcher's date (`TouchRecycleBin`) so the desktop re-reads it. |
| Desktop guard | `/usr/libexec/veltos/veltos-desktop-guard`, `/usr/lib/systemd/system/veltos-desktop-guard.service`, D-Bus `org.veltos.DesktopGuard` (`/usr/share/dbus-1/system-services/`, policy in `/usr/share/dbus-1/system.d/`) | A root service started on demand by D-Bus (GLib, `python3-gi`), ending after a minute without calls. `Protect` makes the three launchers root's own files (written anew from `/usr/share/veltos/desktop`, never written through a link) and the caller's desktop folder root's with the user's group, mode 1775 (sticky, like `/tmp`): the user still creates, renames and deletes their own files there, but nobody else's. Only for a user private group (named after the user, nobody else in it or using it as theirs: Debian's default); with a shared group such as `users` the desktop would become writable for others, so nothing is changed and the answer is "refused" (the launchers are then the user's own copies, deletable). `TouchRecycleBin` moves the Recycle Bin launcher's date between 2 and 2.5 s after 1970. It acts only on the calling user's own desktop: the user is the bus' `GetConnectionUnixUser` of the connection, never an argument, and folders are opened one name at a time without following symbolic links, inside the caller's home. Root is not hindered (no immutable flag, so removing an account still works). The unit may write below `/home` only, has no network and keeps four capabilities (`CAP_CHOWN`, `CAP_FOWNER`, `CAP_DAC_OVERRIDE`, `CAP_DAC_READ_SEARCH`); the package does not start it (`dh_installsystemd --no-start`). |
| Desktop (Windows 11 behaviour) | `plasma-overrides/org.kde.desktopcontainment.json`, `plasma-overrides/files/desktop/VeltOSDesktop.qml` (added to Plasma's folder view by `update-plasma-overrides`), `/usr/libexec/veltos/desktop-new`, catalog `/usr/share/locale/tr/LC_MESSAGES/veltos-desktop.mo` (`translations/tr.po`, `i18nd`) | Right-click on the desktop opens Windows 11's menu (View: icon sizes, auto arrange; Sort by; Refresh; Paste; New: Folder, Word Document, PowerPoint Presentation, Text Document, Excel Worksheet (the Office documents while veltos-office is installed, filled by its `blank-document`); Display settings; Personalize; Open in Terminal), never Plasma's containment menu (no Edit Mode, no Add Widgets). New > Folder / Text Document / Office documents make the item with Windows' name ("New folder", "New folder (2)", "Yeni Word Belgesi.docx", …; `desktop-new`) and open its name for editing at once, as Windows does (Plasma asked in a dialog); Refresh and F5 blink the icons; the Recycle Bin, This PC and the Store have a small menu of their own (Open, Empty Recycle Bin → File Explorer's Windows 11 question, Properties) and the Delete key, F2 and Ctrl+X skip them; every other file and folder gets Windows 11's menu (Open, Open with, Cut, Copy, Rename, Delete, Compress to ZIP file, Properties), whose Open with, Compress to ZIP file and Properties go through VeltOS File Explorer (`veltos-explorer --open-with`: the "Select an app" window; `--compress`: the same `.zip` File Explorer makes, with VeltOS Archive's progress; `--properties`: VeltOS' Properties window, KDE's dialog never opens; the Recycle Bin's Properties shows the bin); the Recycle Bin's icon shows whether it is full; the name box has square corners. Texts come from VeltOS' own catalog, so KDE's translations are untouched. |
| `session-fixups` | `/usr/libexec/veltos/`, started by `/etc/xdg/autostart/veltos-session-fixups.desktop` | One-shot at sign-in: locks the taskbar's items; display scale in 25 % steps for new screens (`display-scale`); loads KScreen's kded module when kded did not (it autoloads but was not running: monitors plugged in or out, the laptop lid); pins the Store once for older taskbars. Window previews now come from KWin (`veltostaskbarpreview`), which draws them also with software rendering, so Plasma's tooltip setting, switched off in VMs by older VeltOS versions, is put back on (it now only shapes the pinned apps' tooltips). |
| Taskbar window previews | `/usr/share/kwin/scripts/veltostaskbarpreview/` (`kwin/scripts/`, `EnabledByDefault`) | Windows 11's previews above a taskbar button as a KWin QML script (public `org.kde.kwin` API only; product owner, 2026-10-22): pointing at a running app's button shows one card per window on the current desktop (icon, title, a close button while pointed at, a live picture drawn by KWin's `WindowThumbnail`); a click switches to the window, the close button or a middle click closes it; pointing at a card for a while shows that window alone, the others fade out (Peek); cards that do not fit become a list. KWin finds an app's windows by the button Plasma's task manager gives each window as its minimise target (`iconGeometry`). Plasma's own window tooltips captured windows through the screen-cast service, which gave garbled pictures with software rendering; these work with every renderer. A click on an app with several windows leaves its previews open instead of cycling windows (Meta+number still switches). |
| Toast animation | `/usr/share/kwin/effects/veltostoast/` (`kwin/effects/veltostoast/`, a JavaScript effect, `EnabledByDefault`) | Notification pop-ups slide in from the right edge of the screen while they fade in and slide back out to the right when they close, like Windows 11 toasts; KWin's "Fading Popups" would only fade them (this effect takes the animation over with a forced grab). |
| `context-menus` | `/usr/libexec/veltos/`, run by `veltos-session.sh` before plasmashell starts | Right-click menu options of the desktop and the taskbar (`[ActionPlugins]` in the Plasma layout file). |
| `needs-software-rendering` | `/usr/libexec/veltos/` | The one rule for when VeltOS renders in software instead of with the display driver's OpenGL (exit status 0 = yes): VirtualBox (DMI) **without working 3D acceleration**. With 3D off, Mesa has already fallen back to llvmpipe on the GBM platform (`eglinfo -B`, no display needed); with 3D on the same VMSVGA display gives real OpenGL (renderer "SVGA3D") and nothing is forced. Nothing in sysfs tells the two apart. Only VirtualBox is probed. Used by `veltos-session.sh` and `sddm-virtualbox-env`. |
| `greeter-compositor` | `/usr/libexec/veltos/`, SDDM's `CompositorCommand` | Starts KWin for the sign-in screen with Plasma's own arguments; when `/run/veltos/software-rendering` exists (left by `sddm-virtualbox-env`), with KWin's software compositor and Mesa's llvmpipe (the session does the same in `veltos-session.sh`). |
| `sddm-virtualbox-env` | `/usr/libexec/veltos/`, `ExecStartPre` of `sddm.service` (`/usr/lib/systemd/system/sddm.service.d/veltos-virtualbox.conf`) | Before SDDM starts, asks `needs-software-rendering` (as root, so the render node can be probed). Yes: writes `/etc/sddm.conf.d/zz-veltos-virtualbox.conf` (the vendor `GreeterEnvironment` plus `LIBGL_ALWAYS_SOFTWARE=1`, so the sign-in screen's QML renders with llvmpipe) and the marker `/run/veltos/software-rendering` for `greeter-compositor`; no: removes both. Decided at every start, so a disk moved between a VM and real hardware, or a VM whose 3D setting changed, does the right thing. |
| Plasma services without the portal theme | `/usr/lib/systemd/user/plasma-*.service.d/veltos-portal-theme.conf` (generated by `tools/build-assets.py`, list `PLASMA_SERVICES`) | `Environment=QT_QPA_PLATFORMTHEME=kde` for Plasma's own services (kwin, ksplash, kded6, kcminit, ksmserver, kactivitymanagerd, powerdevil, KDE's portal backend, ...) — not plasmashell, whose environment programs started from Start inherit: it keeps the portal theme for their file dialogs. The session gives every program the portal platform theme for the Windows 11 file dialogs; a Qt program starting with it asks the portal first, and at session start the portal cannot be up yet (its backends are Wayland clients of KWin and Qt programs themselves): each of those services blocked 25 s and the portal timed out after 90 s, plasmashell came after ~95 s instead of ~18 s (2026-10-22). Programs the user starts keep the portal theme. plasmashell itself gets KDE's theme through Qt's `-platformtheme kde` argument instead (`plasma-plasmashell.service.d/veltos-platform-theme.conf`: Debian's `ExecStart` plus the argument), which wins over the variable, so its environment keeps the portal theme for the programs it starts: with the portal theme plasmashell asked the portal for the colour scheme while starting, KDE's portal backend is ordered after `plasma-core.target`, which waits for plasmashell, and every sign-in waited 25 s for that call to time out (faster sign-in, product owner, 2026-10-22). |
| Task View | `/usr/share/kwin/effects/veltostaskview/` (`kwin/effects/veltostaskview/`) | Windows 11 Task View as a KWin QML scene effect (public `org.kde.kwin` API): window thumbnails with icon, title and close button; desktops strip with "New desktop" and remove, pointing at a desktop shows its windows; Meta+Tab and the taskbar's Task View button. |
| Terminal | `/usr/share/konsole/VeltOS Light.profile`, `VeltOS Dark.profile`, `VeltOS-OneHalfLight.colorscheme`, `VeltOS-Campbell.colorscheme`, `/usr/share/veltos/konsole/tabs-*.css`, `/usr/share/kxmlgui5/konsole/*.rc`, `/etc/xdg/konsolerc`, `/usr/libexec/veltos/terminal-theme` (source: `konsole/`, `system/`) | Konsole like Windows Terminal, following the light/dark theme (`terminal-theme`, run at sign-in and by Settings' theme switch; open terminals switch colours over D-Bus): One Half Light or Campbell colours, rounded tabs with the selected one in the terminal colour (Konsole reads tab styles only from a file: `TabBarUseUserStyleSheet`), Cascadia Mono 12 (fonts-cascadia-code), bar cursor, 120 x 30, tabs always shown with a "+" button, no toolbars (Konsole's own window layout files with the toolbars hidden, same number so KXMLGUI prefers them; removing them crashed the right-click menu), Windows Terminal's keys (Ctrl+C copies selected text and otherwise interrupts, Ctrl+V pastes) and its short right-click menu, opaque window (`--notransparency` added by `update-app-names`: Konsole's see-through window let other windows show through its tab bar). |
| Sounds | `/usr/share/sounds/veltos/` (`tools/sounds.py`), `[Sounds] Theme=veltos` in kdeglobals, `/etc/xdg/plasma_workspace.notifyrc` | Original system sounds synthesised at build time (Windows' sounds are not shipped); a chime when the desktop appears after signing in. |
| Animations | `KWIN_EFFECTS_FORCE_ANIMATIONS=1` in the session script | KWin switches its animations off with software rendering (most VMs); VeltOS keeps them on (open/close, minimise, maximise, sliding popups, desktop switching). |
| Clipboard | `/etc/xdg/klipperrc` | Plasma's clipboard keeps pictures (Klipper ignores them by default), so a snip stays pasteable after Snipping Tool ends. |
| Other defaults | `/etc/xdg/klaunchrc`, `usr/lib/sddm/sddm.conf.d/10-veltos.conf`, `/etc/xdg/networkmanagement.notifyrc` | No app icon bouncing next to the pointer while a program starts; no on-screen keyboard on the sign-in screen (SDDM's default input method); no toast when a network connects or disconnects, as on Windows 11 (the network icon tells; failures still pop up). |

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
| `samples/`, `tools/sample-media.py` | Sample media in `/usr/share/veltos/samples` (a song, a video, every wallpaper as a picture), part of Photos' and Media Player's libraries; made by the tool (synthesized music, animated wallpapers), committed so builds need no ffmpeg |
| `system/numlock-state` | Num Lock on when a session starts (`/etc/xdg/kcminputrc`), the state the user left saved at the end of the session (`veltos-numlock.service`) for the next one |
| `qml/org/veltos/controls/`, `system/veltos_controls.py` | VeltOS' Qt Quick Controls style for VeltOS' apps: Windows 11 scroll bars (no Breeze separator line), the rest from Breeze; apps call `veltos_controls.use()` after creating their QGuiApplication, which also keeps their compiled QML in `~/.cache/veltos-qml/<app>-<hash of the QML files>` (faster starts) |
| `konsole/` | Terminal profile, Campbell colour scheme, Konsole window layout with hidden toolbars, Windows Terminal's Ctrl+C/Ctrl+V and right-click menu |
| `kwin/` | KWin effects (`effects/veltostaskview`: Task View; `effects/veltostoast`: the toast animation) and scripts (`scripts/veltostaskbarpreview`: the taskbar's window previews) |
| `mail/mail.css` | VeltOS Mail's Outlook look (Thunderbird user style sheet) |
| `tools/gtktheme.py`, `tools/firefox.py` | GTK theme and Firefox style sheet with Windows 11 caption buttons |
| `tools/app_titles.py` | Program-name catalogs for the en@veltos / tr@veltos pseudo-languages |
| `sddm/veltos/` | VeltOS sign-in screen (SDDM theme) |
| `system/` | `veltos-session.sh`, `context-menus`, `desktop-new`, `display-scale`, `greeter-compositor`, `needs-software-rendering`, `sddm-virtualbox-env`, `session-defaults`, `session-fixups`, `terminal-theme`, `trash-icon`, `update-app-names`, `update-plasma-overrides`, `veltos-desktop-guard` (with `veltos-desktop-guard.service`, `org.veltos.DesktopGuard.service` and `.conf`) |
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
- Kvantum menus are one rounded box (`uniform_menu_band`): Fluent draws a
  square-cornered menu body inside a rounded band of the same colour at
  75 % that belongs to the shadow pieces and is meant to be seen through
  blur; without blur the two showed as two boxes, one inside the other
  (product owner, 2026-10-22). The band now has the body's opacity; the
  shadow gradients and edge lines stay. The build fails if the band is
  not found.

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
  taskbar). It shows the quick settings' icons: the sun for brightness
  (plasmashell asks for `video-display-brightness`, a monitor picture)
  and outline speakers for volume.
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

## Added 2026-10-22 (evening)

The product owner's requests of 2026-10-22, in the mechanisms above:

- **Taskbar**: window previews with Peek from KWin
  (`veltostaskbarpreview`); the stacked button of an app with several
  windows redrawn (only the edge of a second plate beside the button, in
  its colours; the first version looked like two different boxes); a
  click on such a button leaves the previews open; a pinned app's tooltip
  is its name; no speaker or mute badge is drawn over a playing app's
  taskbar icon; right-click on the
  empty taskbar: Task Manager, Taskbar settings; Show desktop a little
  wider and at the screen's very edge; the default pins (Camera, Photos,
  Media Player added); the Task View button's glyph drawn as outlines
  only (it was filled with the theme's background, a black block in dark
  mode); the settings keys Settings > Personalization > Taskbar uses.
- **Search window**: "No results for …" in the middle of the window with
  Windows 11's hint ("Check the spelling or try a different search."); the
  taskbar's search box shows the text (I-beam) pointer and follows the
  Search setting (hidden, icon, icon and label, box).
- **Tray**: the hidden-icons arrow's tooltip goes away when it is
  clicked; the clipboard flyout as Windows 11's clipboard history
  ("Clipboard history", "Clear all", cards newest first with a "..."
  menu, a message while nothing was copied; Klipper's history stays); the
  drives flyout ("Safely Remove Hardware") with Windows 11 rows: icon,
  name, "X free of Y" over a usage bar, an eject button; the brightness
  bar at the bottom of the screen also shows while Quick Settings'
  brightness slider moves, like the volume bar.
- **Notifications**: Windows 11's "..." menu on toasts (turn off all
  notifications of the app in `plasmanotifyrc`, or open Settings'
  notification page); downloads and copies in a toast with a thin
  progress bar, bytes, speed and percentage, and equal buttons (Pause /
  Resume and Cancel, then Open file and Open folder); the slide-in
  animation (`veltostoast`); no toast for network connections.
- **Desktop**: Windows 11's menu for files and folders with VeltOS
  File Explorer's Open with, Compress and Properties windows; the Recycle
  Bin icon full or empty; This PC, the Recycle Bin and the Store guarded
  by the desktop guard.
- **Menus and frames**: Kvantum menus as one rounded box
  (`tools/fluent.py`); modal dialogs (message boxes) with only a Close
  button (Aurorae).
- **VeltOS Mail**: Thunderbird renamed and styled like Outlook (see the
  table).
- **LibreOffice Draw** hidden and offered for no file type.
- **Faster sign-in**: plasmashell with `-platformtheme kde`; the sign-in
  splash and the Ctrl+Alt+Del screen blur the wallpaper once
  (`cached: true`) instead of on every animation frame: with software
  rendering the splash's spinner kept the CPU busy that way while the
  session started. (The portal settings for sign-in are veltos-explorer's
  `kde-portals.conf`.)
- Tests: `tests/test_plasma_overrides.py` (the Recycle Bin icon, window
  previews left to KWin, the stack edge, the click that leaves previews
  open, the pinned app's tooltip, the speaker badge, the taskbar menu and
  the Show desktop edge, job toasts, the tray heading, modal dialogs'
  buttons; `tests/data/` holds the upstream files these apply to),
  `tests/test_build_assets.py` (the menu band, the plasmashell drop-in,
  VeltOS Mail's style sheets, autoconfig and preferences),
  `tests/test_system.py` (VeltOS Mail's name, Draw hidden and without
  file types), `tests/test_desktop_guard.py` (the desktop guard on a fake
  account's home: owners and modes, links replaced rather than written
  through, folders behind links or of somebody else refused, shared groups
  refused; the owner changes need root, which the package build has).

## Added 2026-10-26 / 2026-10-27

- **Start and search** are never taller than the screen above the
  taskbar (`fitHeight`): on small screens (1280x768) Start reached over
  the taskbar and was drawn there as a grey band.
- **Accent colour** in the flyouts: Wi-Fi's Cancel and Disconnect,
  Bluetooth's Disconnect (`OutlineButton.qml`, an accent outline), the
  expanded network or device row (accent tint and border), the clock
  flyout's Focus button.
- **Quick Settings' Bluetooth list** shows only named devices in range
  (BlueZ's cached devices without a signal are left out), by their own
  name.
- **Touchpad scrolling** like Windows 11 (content follows the fingers):
  `touchpad-defaults`, run by `session-fixups`, turns natural scrolling
  on for touchpads the user has not set (KWin ignores
  `[Libinput][Defaults]`). Untested on real touchpads.
- Tests: `tests/test_system.py` (`TouchpadDefaultsTests`).

## Known limitations

- Notification toasts and the tray's flyouts are Plasma's components
  changed by `update-plasma-overrides`: when a Plasma update changes a
  matched file, that component falls back to Plasma's own design until
  the override is updated (building a new image fails until then). The
  notification centre in the clock flyout and the taskbar's window
  previews (KWin script) are VeltOS' own.
- Firefox's caption buttons come from a style sheet that depends on
  Firefox's internal class names (`.titlebar-button`); a Firefox update may
  need `tools/firefox.py` to follow. Firefox from other sources (Flatpak,
  Mozilla's .deb) is not covered.
- Program names inside the programs are replaced only for English and
  Turkish, and only for the strings listed in `tools/app_titles.py`
  (window titles, welcome pages); About dialogs and help menus still
  mention KDE and the original names in other places.
- The screen locker (after sign-in) is Plasma's kscreenlocker; VeltOS
  replaces only its `LockScreenUi.qml` (the Windows 11 lock screen,
  through the desktop shell override), and only while Plasma's file is
  the recorded 6.3.6 one. Its sequence follows Windows 11: the picture
  with the time lifts like a curtain over the blurred sign-in view,
  "Welcome" with the five turning dots after the password, and back to
  the time, fading in from black, after the PC wakes (a jump of the clock
  between two ticks). Esc also turns the screen off: kscreenlocker does
  that itself and keeps the key from the QML.
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
(GPL-2.0-or-later). The QML files in `plasma-overrides/files/` carry
their own SPDX headers; those adapted from Plasma keep Plasma's licences
(GPL-2.0-or-later; LGPL-2.0-or-later for `devicenotifier/DeviceItem.qml`;
GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL for
`notifications/JobItem.qml`). See `debian/copyright`.
