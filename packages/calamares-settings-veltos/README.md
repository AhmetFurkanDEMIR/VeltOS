# calamares-settings-veltos

The VeltOS installer: configuration and branding for
[Calamares](https://calamares.io) as shipped in the live ISO. Replaces
Debian's `calamares-settings-debian` (from which the configuration and
helper scripts are derived, ISC licence).

## What the user sees

- When the live system starts, a **welcome window**: "Try VeltOS"
  (closes the window) or "Install VeltOS" (starts the installer and hides
  the window until the installer is closed, so the language can be changed
  again), and an English / Türkçe switch in the corner. Switching writes
  the language and keyboard layout for the session (`plasma-localerc`,
  `kxkbrc`) and signs out (waiting for the session manager's answer before
  the window closes); SDDM signs the live user in again at once
  (`Relogin=true` from `/etc/sddm.conf.d/veltos-live.conf`), now in that
  language, and the welcome window opens again — the switch works as often
  as wanted. The boot menu therefore has no separate Turkish entry. Shown
  only on the install medium.
- In the live session the screen never locks, dims or turns off and the
  computer does not go to sleep (nobody knows the live user's password).
- An "Install VeltOS" icon on the live desktop and in the Start menu
  ("VeltOS'u Kur" in Turkish).
- Calamares with VeltOS name, logo and colours, its pages in the layout
  of Windows 11's setup (English and Turkish, written in QML in
  `calamares/branding/veltos/`): a picture on the left, the question and
  its answers on the right, with Windows 11 lists, search boxes, text
  boxes, toggle switches and InfoBars, and animations each time a page
  comes into view:
  - **Welcome** (`welcomeq`): the VeltOS logo and the language list;
    requirements the PC misses appear as a red (cannot install) or yellow
    (recommendation) InfoBar.
  - **Time zone** (`localeq`): one searchable list of cities with their
    region, and what the choice sets (time zone, language, formats).
  - **Keyboard** (`keyboardq`): searchable layouts, the layout's variants
    (its default first; no Kurdish variants, product owner 2026-10-22) and
    a box to try the keys.
  - **Partitioning**: Calamares' own C++ page, styled by the style sheet
    (no technical boot-mode/partition-table labels, no old-style disk
    pictures, a drive picture in the free space).
  - **Account** (`usersq`): name, account name and PC name (suggested from
    the name), password twice, automatic sign-in as a toggle switch. Any
    non-empty password is accepted, as on Windows.
  - **Installing**: a slideshow over the VeltOS wallpapers (cross-fading,
    slowly zooming) with current pictures of the system, a Windows 11
    progress ring and "Don't turn off your PC", and a thin progress bar.
    No buttons and no command output.
  - **Finish** (`finishedq`): "VeltOS is ready" with Restart now / Restart
    later; when a step failed, "VeltOS couldn't be installed" with the
    failed step's output in a terminal-style box and the path of the full
    log. Calamares' own error window shows the same output in the same
    style (`start-calamares` passes the style sheet with Qt's
    `-stylesheet`, because Calamares styles only its main window).
- A confirmation prompt before anything is written to disk (a Windows 11
  style message box: buttons on the right; VeltOS' window frames give
  modal dialogs only a Close button). No Debian branding anywhere.

## The session's look, and a light load (2026-10-23)

Product owner, after the first installation in VirtualBox: the installer
takes the system's theme and colours, the side bar's steps follow the
language, the website link works, the first page's loading animation is
centred and Windows-like, and nothing stutters.

- **Theme**: `install-veltos` (as the live user) asks `installer-theme`
  for the session's light or dark mode, the accent colour chosen in
  Settings (kdeglobals `AccentColor`, else the colour scheme's selection
  colour) and whether Mesa draws in software (`eglinfo`: llvmpipe), and
  starts `start-calamares` through pkexec (polkit action
  `org.veltos.installer.start`, which keeps the display like Calamares'
  own). `start-calamares` (root) validates the options, writes
  `/run/veltos-installer/stylesheet.qss` from `stylesheet-light.qss` or
  `stylesheet-dark.qss` (made from the light one by
  `tools/dark-stylesheet.py` at build time) with the accent put in, gives
  root the matching Kvantum style (VeltOS / VeltOSDark) and starts
  Calamares with `-stylesheet` and one argument for the QML,
  `veltos-theme=dark=…;accent=…;software=…`, which Calamares ignores and
  `VeltTheme.js` reads (every QML file takes its colours from it). The
  branding's `stylesheet.qss` is a link to the written sheet, because
  Calamares applies that file to its main window itself.
- **Drawn in software** (VMs without 3D): Calamares runs with
  `QT_QUICK_BACKEND=software`, which redraws only what changes. Measured
  in VirtualBox (no 3D) on the first page: Calamares 140 % CPU and KWin
  110 % before, Calamares 24 % with the software renderer. The cause of
  the load was the slideshow: Calamares loads it at start, and its first
  slide's float animation ran behind the other pages and redrew the whole
  window 60 times a second; the slides animate only while the slideshow is
  shown now (`Presentation.activatedInCalamares`), the pages' breathing
  glow and floating picture only on the page that is shown, and drawn in
  software those slow motions (and the slideshow's slow zoom) advance 20
  (10) times a second, which looks the same.
- **Side bar**: VeltOS names the steps itself in English and Turkish
  (Calamares' names were never retranslated in a QML side bar) and the
  website is a link: Calamares runs as root, so a click asks
  `open-website`, started by `install-veltos` as the live user (127.0.0.1
  only, VeltOS' page only, once in two seconds), to open it in the user's
  browser.
- **First page**: `welcomeq.qml` is a small file that shows Windows 11's
  progress ring (`VeltSpinner.qml`) in the middle while the page itself
  (`WelcomePage.qml`) loads in the background; Calamares' old line spinner
  at the left is hidden by the style sheet. While Calamares checks the PC,
  "Checking this PC…" stands under the list.
- **Qt's own buttons** ("Close" on the error window, "OK"/"Cancel" in the
  partition dialogs) were English in a Turkish installer: Calamares loads
  a translation file from the branding's `lang/` folder, which is a link to
  Qt's Turkish translation (`calamares-veltos_tr.qm` → `qtbase_tr.qm`).
- **Fixes**: the `boot-resolution` job failed every installation at its
  end (VirtualBox, 2026-10-23: Calamares runs through pkexec, and
  veltos-boot's helper refused `--root` to a caller with `PKEXEC_UID`); it
  calls the helper without that variable and can no longer stop an
  installation. The live image carries no initramfs of its own any more
  (127 MB of the ISO), so the `initramfs` job runs before the bootloader
  jobs, whose `update-grub` adds an initrd line only for a file that
  exists, and after `packages`: the live packages it removes include
  live-tools, whose `update-initramfs` wrapper does nothing while the
  installer runs from the live medium (it sees `boot=live` and a read-only
  medium). The first ISO without the live initramfs installed systems that
  stopped at "Unable to mount root fs" (QEMU, BIOS, 2026-10-23). The
  `boot-check` job (after the bootloader jobs) now stops an installation
  whose kernel has no initramfs, or whose boot menu does not load it.

## What it does differently from Debian's settings

| Area | VeltOS behaviour | Why |
|---|---|---|
| UEFI bootloader | Installs `grub-efi-amd64-signed` + `shim-signed` | Installed systems boot with Secure Boot on (Debian's helper installs unsigned GRUB only) |
| EFI directory | Stays `\EFI\debian\` (`efiBootloaderId`) | Debian's signed GRUB looks for its config there; another name breaks Secure Boot |
| Firmware boot entry | Renamed to "VeltOS" by the `efi-label` job | Users see VeltOS in the firmware boot menu (F12 etc.) |
| Disk encryption password tries | `crypttab-tries` job adds `tries=0` to the installed system's crypttab entries unlocked with a typed password | The start-up screen asks until the password is right, like Windows, instead of dropping to a recovery shell after three wrong tries (cryptsetup's default). Calamares' fstab module writes those entries without options when /boot is unencrypted, so `crypttabOptions` cannot do it. |
| Dual boot | `os-prober` installed, `GRUB_DISABLE_OS_PROBER=false` | Windows appears in the boot menu |
| Offline install | Bootloader packages come from the ISO's package pool (`veltos-installer.list.binary`) | Installs work without network |
| APT sources | `main contrib non-free non-free-firmware` for trixie, -updates, -security | Needed for NVIDIA drivers and Steam later |
| Requirements | 20 GB disk, 2 GB RAM | Realistic for a Plasma desktop plus apps |
| Passwords | Any non-empty password (`minLength: 1`, no libpwquality) | libpwquality refused anything under 6 characters and dictionary words even with `minlen=0` |
| Installer pages | Calamares' QML modules (`*q`) with VeltOS' own QML; `hide-back-and-next-during-exec`, `disable-cancel-during-exec` | Windows 11 setup look; no buttons while the disk is being written |
| Removed after install | live packages, Calamares and this package | Installed system has no installer leftovers |

## Layout

| Path | Installed to |
|---|---|
| `calamares/settings.conf`, `calamares/modules/*.conf` | `/etc/calamares/` |
| `calamares/branding/veltos/` (+ rendered `logo.png`, `welcome.png` link to the wallpaper) | `/etc/calamares/branding/veltos/` |
| `modules/*/module.desc` (custom jobs) | `/usr/lib/calamares/modules/` |
| `helpers/*` (job scripts; `installer-theme`, `start-calamares`, `open-website`) | `/usr/libexec/veltos-installer/` |
| `data/org.veltos.installer.policy` (pkexec for `start-calamares`) | `/usr/share/polkit-1/actions/` |
| `tools/dark-stylesheet.py` (build time) | `stylesheet-dark.qss` in the branding folder |
| `bin/install-veltos`, `bin/veltos-install-desktop-icon` | `/usr/bin/` |
| `data/install-veltos.desktop` / `veltos-install-icon.desktop` | `/usr/share/applications/` / `/etc/xdg/autostart/` |
| `welcome/veltos-live-welcome`, `welcome/Main.qml` | `/usr/libexec/veltos-installer/`, `/usr/share/veltos-live-welcome/` (PySide6 + QML) |
| `data/veltos-live-welcome.desktop` | `/etc/xdg/autostart/` and `/usr/share/applications/` (hidden; gives the window its icon) |
| `data/veltos-live-session.sh` | `/etc/xdg/plasma-workspace/env/` (live-only: no lock, no sleep, no screen off) |
| `data/veltos-live.conf` | `/etc/sddm.conf.d/` (live-only: sign in again after signing out) |

## Tests

`tests/test_config.py` (package build): YAML validity, every sequence step
is a known Calamares module or a shipped job, job scripts exist and pass
`sh -n`, no user-visible installer string mentions Debian, every page but
partitioning is a VeltOS QML page with `qmlSearch: both`, every picture the
QML names is shipped, the password rule, no buttons while installing, no
Kurdish keyboard variants, and the error window's style sheet.
The QML pages themselves were checked in the dev VM (language, time zone,
keyboard, account, a failing first step and a full installation,
2026-10-22); Calamares' QML cannot be loaded outside Calamares.

Notes for changing the pages (learned in the VM, 2026-10-22):
- Calamares starts with `-style kvantum`; `import QtQuick.Controls` then
  looks for a QML style called "kvantum" and the page fails to load. The
  pages import `QtQuick.Controls.Basic` and use versionless imports
  (`QtQuick.Layouts 1.15` lacks `uniformCellSizes`).
- Calamares does not retranslate its QML pages when the language changes,
  and keyboardq never calls the page's `onActivate()`: `VeltPage.qml`
  re-reads texts when the step changes and emits `activated()` when its
  window is shown.
- The locale and keyboard steps settle their choice only after the page is
  shown; the pages follow `currentLocationChanged` / `currentIndexChanged`.
`tests/test_welcome.py`: language detection, complete translations, the
welcome window loads offscreen without QML warnings and comes back when
the installer closes, and the live session
script writes the no-lock/no-sleep settings only on the install medium.

`tests/test_efi_label.py`, `tests/test_crypttab_tries.py` and
`tests/test_boot_check.py` run the job scripts against fake firmware
output and fake target roots (`boot-check`: a kernel without initramfs, an
empty one, a boot menu without the initrd line, two kernels, none);
`tests/test_boot_resolution.py` runs the screen-mode job with
`PKEXEC_UID` set and a failing helper, and checks that the initramfs is
made after the live packages are removed and before the bootloader jobs. `tests/test_theme.py`: the dark style
sheet (every light colour mapped, the accent and the text on it kept),
`installer-theme` with stand-ins for kreadconfig6 and eglinfo,
`start-calamares` with a stand-in for Calamares (sheet, Kvantum style,
arguments, software renderer, refused options), `open-website` (only
VeltOS' page, once in two seconds), `VeltTheme.js`'s argument parsing and
the progress ring offscreen. The themed pages were checked in the dev VM
(light, dark with a red accent, Turkish side bar; 2026-10-23).

Status: an installation with "Encrypt system" (UEFI, VM) was tested end to
end on 2026-10-19 (`tests/results/2026-10-19-encrypted-install-uefi/`);
plain and BIOS installations are not yet tested — see `docs/dev/status.md`.
