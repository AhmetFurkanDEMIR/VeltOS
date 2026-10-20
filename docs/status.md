# VeltOS Status

Last updated: 2026-10-20. Every "Implemented" item names the
evidence that shows it working. "Untested" means nobody has observed it
working yet. All observations so far are from QEMU/KVM virtual machines (no
3D acceleration) and one VirtualBox VM of the product owner; **VeltOS has
not been run on real hardware yet.**

## Implemented

| Item | Evidence |
|---|---|
| Container build environment (Debian trixie, pinned) | `build/run.sh image` |
| `veltos-base`: os-release identity, console login banners say VeltOS (dpkg diversions) | 6 unit tests; booted system reports `ID=veltos` |
| `veltos-desktop`: Windows 11 look from Fluent-kde (Kvantum style, window frames with VeltOS-drawn 46×32 caption buttons, Plasma theme, colour schemes), 48 px see-through taskbar with VeltOS Start, Search box, Task View, Quick Settings, two-line clock, show-desktop corner; flyouts float with rounded corners; clock flyout = notification centre + Windows calendar, unread count on the clock; hidden-icons flyout with icons only, "Safely Remove Hardware" flyout (Plasma override mechanism); Windows 11 toasts (bottom-right, picture left, equal buttons); Ctrl+Alt+Del security options screen with Task Manager; power key shuts down; locked taskbar without KDE widget editing, Windows wording in taskbar menus, plain desktop menu; Mica-like title bars; 25 % display scale steps; four wallpapers (Bloom default, Flow, Glow, Lake), light and dark; "Welcome" splash; This PC / Recycle Bin on the desktop; VeltOS GTK theme and Firefox caption buttons; no launch icon at the pointer; no on-screen keyboard at sign-in; window previews off with software rendering; Windows-familiar app names; sign-in screen; wallpaper without logo; KDE Wallet off | 64 unit tests (incl. full asset build, overrides against Plasma 6.3.6 QML, menus, scale steps, wallpapers); VM (installed system, 2026-10-20): screenshots of each item, dark taskbar on first switch, Firefox hover states; VM (live, 2026-10-20 late): Ctrl+Alt+Del screen and its Task Manager, menus, toasts, flyouts, 100 % scale, wallpaper |
| `veltos-explorer` (new): File Explorer in the Windows 11 layout — tabs in the title bar, command bar, address and search boxes, navigation pane, Home (Quick access, Recent), This PC, Recycle Bin, Details/Tiles/icon views with thumbnails, context menus, drag and drop, rename in place; copy/move/delete through KIO | 31 unit tests (incl. the real window offscreen, EN/TR, Turkish C locale); VM: opened from the taskbar, Home, Documents in Details view, item and background menus; **starts in a Turkish locale** (did not before 2026-10-20) |
| `veltos-settings`: Windows 11 Settings with built-in Wi-Fi, Bluetooth, Sound, Display, Background, Colours (mode, accent), Date & time pages, About with OS build, search, EN/TR | 57 unit tests (parsers with recorded tool output, offscreen window, Turkish C locale, theme command); VM: every page; dark mode switches the taskbar on the first switch; **Wi-Fi tested end to end on simulated hardware** (mac80211_hwsim + hostapd WPA2: wrong key refused without extra prompts, correct key connects and gets an address, disconnect, reconnect, forget) |
| `veltos-taskmanager` (new): Task Manager in the Windows 11 layout — Processes (Apps / Background / System, summed per app, busy cells tinted, search, End task), Performance (60-second CPU/memory/disk/network graphs and figures), Startup apps (enable/disable); Ctrl+Shift+Esc, one instance; KDE System Monitor kept as "Resource Monitor" | 19 unit tests (fake psutil; window offscreen EN/TR, Turkish locale); VM: opened with Ctrl+Shift+Esc, Firefox grouped with its 11 processes, second Ctrl+Shift+Esc does not open a second window, all three pages |
| `veltos-fluent-icons`: Fluent icons/cursors (pinned, verified; Microsoft logos removed), yellow Windows 11 folders, coloured place icons at all sizes, VeltOS "This PC" and Recycle Bin icons in the Windows 11 style, Fluent cursors as the system default pointer | Package checks; VM screenshots; `x-cursor-theme` points to Fluent-cursors (VM) |
| `veltos-boot`: Plymouth splash, GRUB theme, hidden menu, fixed video mode (VirtualBox/Hyper-V fix), kernel titles without the Debian build suffix, keyboard layout in the initramfs, disk-encryption password screen (Inter font, Windows-like texts, box below the logo) | 22 unit tests; boot screenshots; encrypted install screenshots; quiet kernel/systemd options in the installed grub.cfg (VM) |
| `calamares-settings-veltos`: installer with Windows 11 style side bar, buttons and controls (QML + style sheet, Kvantum for its dialogs), live welcome window (language switch fixed 2026-10-20), BitLocker-like encryption (unencrypted /boot, password asked by the boot screen, unlimited tries), firmware entry "VeltOS" | 19 unit tests; **encrypted installation tested end to end in a VM (UEFI)** on ISO 20261019-174700: install, firmware entry, boot menu, password screen (wrong and right password), sign-in, desktop — `tests/results/2026-10-19-encrypted-install-uefi/` |
| `veltos-winapps` + `veltos-wine-addons`: double-click `.exe`/`.msi` → install/run via Wine (Wine "Light" theme) | 20 unit tests; 7-Zip installed in a VM (earlier ISO) |
| live-build configuration, verify hook (also: Explorer default, Dolphin/System Settings hidden, OS build file, taskbar widgets, installer side bar, console banner) | Passes in every ISO build |
| VM test tools: boot test (BIOS/UEFI/Secure Boot), Windows-program test, preview, long-running VM | See `docs/testing.md` |

### Latest ISO

See the newest entry of `docs/development-log.md` for the ISO name and the
checks that passed.

## Not yet tested

- The 2026-10-20 changes (see the development log) were tested by
  installing the rebuilt packages into VMs, not yet on a newly built ISO;
  the quiet boot options, the Fluent cursor default for X11 programs and
  the GTK theme in GTK 4 / libadwaita programs are untested on screen.
- The power key shutting down (needs a VM that may be switched off), the
  locked taskbar for a brand-new user (layout script), dark wallpapers
  and dark title bars on screen, "Switch user" and "Change a password" on
  the Ctrl+Alt+Del screen.

- A plain (unencrypted) installation and any BIOS installation on the
  latest ISO; an installation in VirtualBox (the product owner's setup).
- Secure Boot boot test and `test-winapps` on the latest ISO.
- Bluetooth pages with a real adapter; Display page changes on real
  monitors; accent colour in all apps (Kvantum apps keep the theme's
  blue); blur/translucency with a real GPU.
- File Explorer: mounting drives (udisks), Extract/Compress with Ark, drag
  and drop between windows, large folders, network shares.
- Anything on real hardware.

## Known gaps

- File Explorer does not answer "show in folder" requests of other
  programs (D-Bus `org.freedesktop.FileManager1`); Dolphin (hidden) opens.
- Settings pages that are not built in still open KDE's own pages in a
  separate window (mouse, keyboard, notifications, power, default apps,
  startup apps, users, region, accessibility, …).
- The screen locker after sign-in is Plasma's design.
- Product owner's requests not done yet: Control Panel pages in the
  Settings design; Windows 11 modern Wine dialogs; the Store (Discover is
  KDE's design: a VeltOS Store in the Microsoft Store layout is next);
  installer pages; a full check that no old KDE/Qt window is left (KDE's
  own dialogs still open from some places, e.g. "Change a password" opens
  KDE's Users page). Sounds untested by ear.
- Right-clicking the empty taskbar shows nothing (Windows: "Taskbar
  settings"); the desktop menu has no "Display settings"/"Personalize".
- Taskbar previews: with software rendering the tooltip shows the window
  title only.
- A busy pointer while a program starts is not possible with KWin on
  Wayland (it only draws the app icon, which VeltOS turned off).
- In VMs without 3D acceleration the taskbar shows window titles instead
  of previews (KWin's captures are garbled with llvmpipe).
- Start: for users who signed in before 2026-10-20, File Explorer replaces
  the pinned KDE file manager at the end of the list, not in its place.

- The disk-encryption password screen is in English only (the initramfs
  has no language setting yet); its keyboard indicator is Plymouth's image.
- KDE programs' About dialogs still name KDE and the original programs.
- The Store (Discover) shows Debian package sources.
- ISO is not verified bit-for-bit reproducible. No CI.

## Next steps

1. VeltOS Store: Microsoft Store layout on PackageKit and AppStream,
   replacing Discover in Start and the taskbar.
2. Build an ISO with all 2026-10-20 changes and run the boot tests; check
   the power key, the quiet start-up and shutdown on screen.
3. Control Panel pages inside Settings ("Change a password", taskbar
   settings, default apps, ...), "Taskbar settings" and "Personalize"
   menu entries.
4. Listen to the VeltOS sounds on real hardware; measure animation CPU
   cost with software rendering.
5. Plain and BIOS installations; the product owner reinstalls in
   VirtualBox.
6. Installer pages (partitions, users) in Windows 11 style.
7. File Explorer: FileManager1 D-Bus service, distinct folder icons.
8. First run on real hardware.
