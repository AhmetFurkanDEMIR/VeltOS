# VeltOS Status

Last updated: 2026-10-19 (night). Every "Implemented" item names the
evidence that shows it working. "Untested" means nobody has observed it
working yet. All observations so far are from QEMU/KVM virtual machines (no
3D acceleration) and one VirtualBox VM of the product owner; **VeltOS has
not been run on real hardware yet.**

## Implemented

| Item | Evidence |
|---|---|
| Container build environment (Debian trixie, pinned) | `build/run.sh image` |
| `veltos-base`: os-release identity, console login banners say VeltOS (dpkg diversions) | 6 unit tests; booted system reports `ID=veltos` |
| `veltos-desktop`: Windows 11 look from Fluent-kde (Kvantum style, window frames with VeltOS-drawn 46×32 caption buttons, Plasma theme, colour schemes), 48 px see-through taskbar with VeltOS Start, Search box, Task View, Quick Settings, two-line clock with calendar, show-desktop corner; Windows-familiar app names; sign-in screen; wallpaper without logo; KDE Wallet off | 47 unit tests (incl. full asset build); VM screenshots of taskbar (light and dark), Start, Explorer, Settings; light/dark switch changes the taskbar at once (VM) |
| `veltos-explorer` (new): File Explorer in the Windows 11 layout — tabs in the title bar, command bar, address and search boxes, navigation pane, Home (Quick access, Recent), This PC, Recycle Bin, Details/Tiles/icon views with thumbnails, context menus, drag and drop, rename in place; copy/move/delete through KIO | 30 unit tests (incl. the real window offscreen, EN/TR); VM: opened from the taskbar, Home, Documents in Details view, item and background menus |
| `veltos-settings`: Windows 11 Settings with built-in Wi-Fi, Bluetooth, Sound, Display, Background, Colours (mode, accent), Date & time pages, About with OS build, search, EN/TR | 55 unit tests (parsers with recorded tool output, offscreen window); VM: every page; **Wi-Fi tested end to end on simulated hardware** (mac80211_hwsim + hostapd WPA2: wrong key refused without extra prompts, correct key connects and gets an address, disconnect, reconnect, forget) |
| `veltos-fluent-icons`: Fluent icons/cursors (pinned, verified; Microsoft logos removed), yellow Windows 11 folders, coloured place icons at all sizes | Package checks; VM screenshots |
| `veltos-boot`: Plymouth splash, GRUB theme, hidden menu, fixed video mode (VirtualBox/Hyper-V fix), kernel titles without the Debian build suffix, keyboard layout in the initramfs, disk-encryption password screen (Inter font, Windows-like texts, box below the logo) | 22 unit tests; boot screenshots; encrypted install screenshots |
| `calamares-settings-veltos`: installer with Windows 11 style side bar, buttons and controls (QML + style sheet, Kvantum for its dialogs), live welcome window, BitLocker-like encryption (unencrypted /boot, password asked by the boot screen, unlimited tries), firmware entry "VeltOS" | 19 unit tests; **encrypted installation tested end to end in a VM (UEFI)** on ISO 20261019-174700: install, firmware entry, boot menu, password screen (wrong and right password), sign-in, desktop — `tests/results/2026-10-19-encrypted-install-uefi/` |
| `veltos-winapps` + `veltos-wine-addons`: double-click `.exe`/`.msi` → install/run via Wine (Wine "Light" theme) | 20 unit tests; 7-Zip installed in a VM (earlier ISO) |
| live-build configuration, verify hook (also: Explorer default, Dolphin/System Settings hidden, OS build file, taskbar widgets, installer side bar, console banner) | Passes in every ISO build |
| VM test tools: boot test (BIOS/UEFI/Secure Boot), Windows-program test, preview, long-running VM | See `docs/testing.md` |

### Latest ISO

See the newest entry of `docs/development-log.md` for the ISO name and the
checks that passed.

## Not yet tested

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
- The disk-encryption password screen is in English only (the initramfs
  has no language setting yet); its keyboard indicator is Plymouth's image.
- KDE programs' About dialogs still name KDE and the original programs.
- The Store (Discover) shows Debian package sources.
- ISO is not verified bit-for-bit reproducible. No CI.

## Next steps

1. Plain (unencrypted) installation and a BIOS installation in a VM on
   the latest ISO; the product owner reinstalls in VirtualBox.
2. Installer pages still in Calamares' own design (partitions, users):
   Windows 11 style icons and layout; confirmation dialog without
   minimise/maximise buttons.
3. Built-in Settings pages for the rest of the Control Panel (product
   owner's request): Mouse, Keyboard, Notifications, Power & battery,
   Default apps, Startup apps, Accounts, Language & region, Accessibility.
4. File Explorer: FileManager1 D-Bus service, distinct icons for Desktop /
   Downloads / Documents / Pictures / Music / Videos, Ark and udisks tests.
5. Lighter live session (Discover notifier, KDE Connect, xwaylandvideobridge
   ~550 MiB RSS at idle).
6. First run on real hardware.
