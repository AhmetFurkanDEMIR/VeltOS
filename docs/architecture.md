# VeltOS Architecture

Status: Milestone 0 decisions, written 2026-10-18. Each decision lists the
alternatives considered and when it should be revisited. Versions were
verified against packages.debian.org / tracker.debian.org on that date.

## 1. Overview

VeltOS is a Debian-based desktop distribution. It is **not** a fork of the
kernel, the graphics stack, KDE Plasma or Wine. VeltOS-specific work lives in
small, independently testable Debian packages (`packages/`) and a
live-build configuration (`build/live-build/`) that assembles them with
stock Debian packages into a bootable, installable ISO.

```
┌──────────────────────────────────────────────────────────────────────┐
│ VeltOS packages        veltos-base · veltos-desktop · (planned:       │
│                        hardware manager, Windows app manager, gaming) │
├──────────────────────────────────────────────────────────────────────┤
│ Desktop                KDE Plasma 6.3 (Wayland) · SDDM · PipeWire     │
├──────────────────────────────────────────────────────────────────────┤
│ Graphics               Mesa 25.0 (radeonsi/RADV, iris/ANV, nouveau/NVK)│
│                        optional NVIDIA 550 from Debian non-free (M2)  │
├──────────────────────────────────────────────────────────────────────┤
│ Base system            Debian 13 "trixie" · Linux 6.12 LTS · systemd  │
│                        APT · firmware from non-free-firmware          │
├──────────────────────────────────────────────────────────────────────┤
│ Boot / delivery        live-build ISO (GRUB BIOS+UEFI, shim Secure Boot)│
│                        live-boot/live-config · Calamares installer    │
└──────────────────────────────────────────────────────────────────────┘
```

## 2. Decisions

### 2.1 Base: Debian 13 "trixie" (stable)

- Facts (2026-10-18): Debian 13 is stable (released 2025-08-09, point
  release 13.7 on 2026-09-12). Debian 12 is oldstable; 14 "forky" is testing.
- Why: longest security support of the candidates, the package set already
  contains everything Milestones 1–4 need (Plasma 6.3, Mesa 25.0, Wine 10.0,
  Calamares 3.3, live-build), and Debian's archive signing gives us verified
  package delivery for free.
- Alternatives: Debian testing (newer Plasma 6.7/Mesa 26 but no stable
  security story); Ubuntu base (Snap-centric, different ecosystem).
- Newer hardware: `trixie-backports` carries Linux 7.2 and Mesa 26.1. It is
  **not enabled** in the image yet. Offering backports kernels/Mesa as an
  opt-in "new hardware" path is a Milestone 2/4 decision that needs
  benchmark and regression data first.
- Revisit: when Debian 14 is released (expected 2027).

### 2.2 Kernel: Debian `linux-image-amd64` (6.12 LTS)

Signed by Debian for Secure Boot, maintained by the Debian kernel team,
receives security updates through `trixie-security`. A custom kernel would
lose Secure Boot signing and add a large maintenance burden.

### 2.3 Desktop: KDE Plasma 6.3 from Debian, customised by packages

- Plasma is the closest open-source desktop to the Windows interaction
  model (taskbar, start menu, system tray, window controls) and its layout
  can be fully defined by a Plasma "global theme" (look-and-feel package).
- Built from `kde-plasma-desktop` (minimal) plus a short application list,
  not `task-kde-desktop`, to keep RAM and disk use down.
- **No fork.** `veltos-desktop` ships:
  - global themes `org.veltos.light` (**default**, soft like Windows 11) and
    `org.veltos.dark`;
  - a Plasma layout script: bottom taskbar, start button and task manager
    centred between two flexible spacers, tray + clock on the right;
  - **VeltOS Start** (`org.veltos.startmenu`), a QML applet with the
    Windows 11 Start layout (search, pinned grid, recommended files,
    account/power). It reuses Plasma's own models (`org.kde.plasma.private
    .kicker`, the same backend as KDE Kickoff) instead of reimplementing
    app indexing, search and session actions. Trade-off: that QML API is
    private and may change between Plasma releases; the applet is small
    and tested in a VM on every change (`build/run.sh preview`);
  - the Windows 11 inspired look (application style, window frames,
    Plasma theme, colour schemes) derived at package build time from the
    pinned Fluent-kde release (see 2.3.1);
  - `/etc/xdg/kdeglobals`, `kcminputrc`, `kscreenlockerrc`, `ksplashrc`
    system defaults (Inter UI font, Fluent icons/cursors);
  - the "Velt Bloom" wallpaper, generated procedurally (`tools/bloom.py`)
    so it is original artwork and reproducible; login splash, SDDM
    background and the VeltOS logo.
- Icons: Fluent icon theme (GPL-3.0, not in Debian) packaged by VeltOS from
  a pinned, checksum-verified release (`veltos-fluent-icons`). Its icons
  that depict Microsoft's Windows logo are replaced/removed (trademark).
- Third-party branding pinned out of the image: Debian's `desktop-base`,
  `calamares-settings-debian`, and KDE's `plasma-welcome` (KDE community
  pages). The live system shows its own small welcome window ("Try VeltOS"
  / "Install VeltOS", `calamares-settings-veltos`); a welcome app for
  installed systems is planned.
- The layout only applies to users who start Plasma for the first time; it
  never rewrites existing users' configuration.
- Session: Wayland (Plasma 6 default). X11 session (`kwin-x11`) is installed
  via Recommends as a fallback.
- Revisit: replacing more stock Plasma UI (System Settings, notifications)
  only where it blocks the "familiar for Windows users" goal.

#### 2.3.1 Windows 11 look: derive from Fluent-kde, do not write a widget style

The product owner asked for an interface "written from scratch, like
Windows 11". What users see of an application is mostly drawn by three
replaceable parts of the desktop: the Qt widget style, the window
decoration and the Plasma theme. Options considered:

| Option | Verdict |
|---|---|
| Write a VeltOS Qt widget style and KWin decoration in C++ | Months of work for every widget type and state; high risk of visual bugs across hundreds of applications. Rejected for now. |
| Tweak Breeze (colours, rounded options) | Light and robust, but still looks like KDE (chevron window buttons, Breeze controls). Rejected as the only change. |
| Klassy / Lightly decorations and styles | Not in Debian; would need packaging and maintenance of C++ code against each Plasma release. Rejected. |
| **Fluent-kde** (Kvantum SVG style + Aurorae decoration + Plasma theme, GPL-3.0) | Chosen. Windows 11 inspired, actively maintained, no compiled code (Kvantum and Aurorae are in Debian), so it is recoloured and fixed at build time by `tools/fluent.py`. |

Changes VeltOS makes to Fluent-kde and why are listed in
`packages/veltos-desktop/README.md` (accent colour, removed third-party
logos, opaque window frames because the translucent ones need blur, no
translucent application windows for lightness, opaque popups unless the
blur effect is available).

Trade-offs: Kvantum renders from SVG and costs a little more CPU than
Breeze; Aurorae decorations are QML and heavier than Breeze's C++ one.
Measured RAM/CPU impact on the live session is still to be recorded in
`docs/status.md`. Kvantum reads its theme only from `~/.config` (no
system-wide file), so a Plasma session script creates it for new users.

#### 2.3.2 Windows-familiar application names without patching packages

Users look for "File Explorer", "Settings", "Task Manager", not Dolphin,
System Settings, System Monitor. Options:

| Option | Verdict |
|---|---|
| Patch/fork the application packages | Violates "reuse, don't fork"; every Debian update would need a rebuild. Rejected. |
| `dpkg-divert` the upstream `.desktop` files and ship VeltOS copies | Copies go stale when Debian updates the originals (new actions, changed `Exec`). Rejected. |
| **Generated overrides in an earlier XDG data directory** | Chosen. `update-app-names` copies the installed originals, changes only `Name`/`GenericName`/`Keywords`/`NoDisplay`, and writes them to `/var/lib/veltos/xdg/applications/`; the Plasma session puts that directory first in `XDG_DATA_DIRS`. A dpkg trigger on `/usr/share/applications` regenerates the copies after every package change. |

The Windows word and the original name stay search keywords.

Inside the programs, Qt appends the program's own display name to every
window title ("Home — Dolphin"). That name is a translatable string, so
VeltOS ships message catalogs for two pseudo-languages, `en@veltos` and
`tr@veltos`, containing only those names, and the session script puts the
matching one first in `LANGUAGE` (`tr@veltos:tr`). KDE's translation
system looks a string up language by language, so every other text falls
through to the real language. Result: "Home — File Explorer", without
patching or diverting any package file. Alternatives rejected: replacing
the programs' complete catalogs (copies of thousands of strings that go
stale), patching `KAboutData` in the programs (fork). Limits: English and
Turkish only; About dialogs and help texts keep other mentions of KDE. Settings pages for unused KDE services are
hidden with KDE's own kiosk mechanism (`[KDE Control Module Restrictions]`
in `/etc/xdg/kdeglobals`).

#### 2.3.3 Settings: a new app in front of KDE's settings modules

KDE System Settings exposes everything, in KDE's own structure and words.
VeltOS Settings (`veltos-settings`, PySide6 + QML) is a new, small app with
the Windows 11 Settings structure (navigation pane, Home, System,
Bluetooth & devices, …, search). Pages people use most are built in
(theme, About/rename PC, Storage, Windows programs); every other setting
opens the corresponding KDE settings module (`kcmshell6 kcm_…`) in its own
window, so VeltOS does not reimplement and maintain display, network,
sound, Bluetooth or user management. KDE System Settings stays available
as "Control Panel" — the same split Windows has. Trade-off: detailed
pages look like KDE pages; built-in pages can replace them one by one.
Python + QML (as `veltos-run`) keeps the app small and testable: its
window is loaded offscreen in the package build.

Built-in system pages (Wi-Fi, Bluetooth, Sound, Display, Background,
Colours, Date & time; `veltos_settings/devices.py`) drive the standard
command-line tools (`nmcli`, `bluetoothctl`, `pactl`, `kscreen-doctor`,
`timedatectl`, `plasma-apply-*`) in a worker thread and parse their
output, so tests replace them with recorded output. Alternatives were the
private Plasma QML plugins (used by Quick Settings; unstable API and not
loadable outside plasmashell) or D-Bus bindings for every service (more
code, no gain for these simple reads). One exception: a new Wi-Fi key is
handed to NetworkManager inside its D-Bus `AddAndActivateConnection` call
(GLib's D-Bus client from python3-gi). `nmcli … password KEY` would put
the key on a command line other users can read, and `nmcli … passwd-file`
makes NetworkManager ask the password agents, which started Plasma's
"KDE Wallet" setup wizard in a VM test. A wrong key is recognised by the
device entering `need-auth` with a reason (it passes `need-auth` once
without a reason while it checks that a key exists); the new connection
is then deleted so no agent prompts.

KDE Wallet is off by default (`/etc/xdg/kwalletrc`): Windows has no wallet
set-up wizard, Wi-Fi keys are kept by NetworkManager (root-only files) and
Firefox has its own password store. Trade-off: KDE programs that want the
wallet (e.g. KDE PIM) store nothing or ask again; it can be turned on in
the Control Panel.

#### 2.3.4 Taskbar: small VeltOS widgets, see-through theme

The Windows 11 taskbar pieces Plasma lacks are three small plasmoids in
`veltos-desktop`: Search (a box that opens VeltOS Start, which searches as
you type — Plasma's D-Bus `activateLauncherMenu`), Task View (KWin's
Overview, via the kglobalaccel D-Bus call), and a clock with time and date
in the same size (Plasma's digital clock draws the date smaller and has no
four-digit-year short format; its calendar component is reused). The
taskbar is 48 px and see-through like Windows 11: the panel is set to
"translucent" and the Plasma theme's panel background is 86 % opaque
without the blur effect (no 3D acceleration, e.g. VirtualBox), 70 % with
blur, with a more saturated blur ("acrylic"). Opacity, not a picture of
the wallpaper, so it costs nothing without blur.

#### 2.3.5 Installer look

Calamares runs as root through pkexec, so the user's Kvantum style does
not apply to it. Its branding instead uses Calamares' QML side bar and
navigation (`calamares-sidebar.qml`: logo and steps with check marks;
`calamares-navigation.qml`: Back / accent Next / Cancel) and a Qt style
sheet (`stylesheet.qss`) for every page's controls (rounded buttons and
fields, accent underline, accent check boxes, thin scroll bars). The style
sheet works with any base Qt style, so it does not depend on root's
configuration. Calamares' own page layouts and icons stay.

#### 2.3.6 Branding and third-party artwork

The VeltOS logo is a "V" of two slanted bars (product owner's sketch,
2026-10-19); one SVG source with copies in the packages that need it
(checked by `tests/repo`). VeltOS does **not** ship Windows wallpapers,
icons, sounds or fonts (Segoe UI): they are Microsoft's copyrighted works
and their licence does not allow redistribution in another operating
system, so an ISO containing them could not be shared. VeltOS draws
original artwork in the same spirit (the generated "Velt Bloom"
wallpaper, without any logo or text, like Windows 11's) and uses Inter
and the Fluent icon theme (GPL). Folder icons are recoloured to the solid
yellow of Windows 11 folders (`veltos-fluent-icons/tools/recolour-folders.py`),
and the coloured place icons are used at small sizes too.

"Not recognisable as Debian" is pursued for everything a user sees
(os-release, console banner, boot menu titles, About pages, app names).
The package system stays Debian's (`/etc/debian_version`, `ID_LIKE=debian`,
`VERSION_CODENAME=trixie`, package licences and the kernel's internal
version string) because third-party installers depend on it and licences
require the notices.

#### 2.3.7 Start-up and sign-in

Like Windows, the boot menu is hidden (GRUB `timeout_style=hidden`, 2 s;
Esc/F4/Shift shows it) and any text GRUB prints is drawn black on black,
so the screen goes from the firmware logo to the VeltOS boot screen
(Plymouth: logo and spinner) to the desktop or the sign-in screen. The
sign-in screen is a VeltOS SDDM theme in Windows 11 layout; it never shows
session/desktop names. The language of the live system is chosen in its
welcome window (re-sign-in) instead of a boot menu entry.

No text appears while starting: the kernel and systemd are quiet
(`loglevel=3`, `systemd.show_status=false`, no text cursor). After
signing in, a Windows-like "Welcome" screen (blurred sign-in wallpaper,
dot spinner) replaces Plasma's progress bar. The power key and
Ctrl+Alt+Del show a VeltOS power card instead of Plasma's full-screen
logout dialog. The sign-in screen has no on-screen keyboard (SDDM's
default input method is turned off).

#### 2.3.8 Changing Plasma components without forking them

Some Plasma parts have no theme or setting for the Windows 11 look (for
example the taskbar's hidden-icons flyout, which shows a titled panel with
labelled icons). VeltOS changes them with **exact text replacements** on a
copy of the installed package (`veltos-desktop`: `plasma-overrides/*.json`,
`update-plasma-overrides`). The copy lives in `/var/lib/veltos/xdg`, which
the session puts first in `XDG_DATA_DIRS`, so Plasma loads it instead of
its own; Plasma's files are never modified. Each replacement must match
exactly as often as expected; after a Plasma update that changes the
text, the copy is removed and Plasma's own version is used (a dpkg trigger
re-runs the tool; the image build fails so developers notice).

Alternatives: forking the Plasma QML (stale after every update, against
the project rules), dpkg-diverting Plasma's files (other packages' files,
conffile-like problems), writing new components from scratch (done where
the public APIs allow it: Start, clock and notification centre, Quick
Settings). Trade-off: the replacements depend on Plasma's private QML and
must be checked when Plasma is updated; the fallback keeps Plasma working.

#### 2.3.9 Non-KDE programs

- **GTK programs** use the `VeltOS` GTK theme: Breeze (KDE's GTK theme,
  colours from the KDE colour scheme) plus the Windows 11 caption buttons
  drawn by the same code as the window frames. KDE's GTK settings module
  can copy window-frame buttons into GTK, but produced empty images for the
  Aurorae frames VeltOS uses.
- **Firefox** draws its own round title bar buttons on Linux and ignores
  the GTK theme; a system-wide autoconfig file registers a style sheet with
  the Windows 11 buttons. It depends on Firefox's internal class names and
  is checked when Firefox is updated (documented in veltos-desktop).
- **Text in VeltOS' own QML programs** is drawn with native (FreeType)
  rendering, as KDE programs do; Qt Quick's distance-field text looked
  uneven at fractional display scales.

#### 2.3.10 Software rendering

Without 3D acceleration (many virtual machines) KWin renders with
llvmpipe. Its window captures are then garbled, so the taskbar shows window
titles instead of previews there (`session-fixups`, decided at each
sign-in from KWin's renderer); with a real GPU the previews stay on.

#### 2.3.11 Taskbar lock, power key, Ctrl+Alt+Del, display scale

- **Locked taskbar.** Windows' taskbar has no widgets to add, move or
  configure. Plasma can lock the whole shell (SystemImmutable through the
  kiosk key `plasma/plasmashell/unlockedDesktop`), but that also refuses
  the D-Bus scripts VeltOS Settings and `plasma-apply-wallpaperimage` use.
  VeltOS locks the taskbar's applets one by one (`session-fixups`; Plasma
  applets follow the shell's lock, not their panel's), hides their
  "Configure …" entries with `plasma/allow_configure_when_locked=false`,
  and sets the right-click menu options of the desktop and the taskbar
  (`context-menus`, the `[ActionPlugins]` groups plasmashell reads at
  start). Trade-off: a user who edits the layout file can unlock it again.
- **Power key**: shut down, Windows' default (`powerdevilrc`). Plasma's
  default, its logout screen, cannot appear over the lock screen, so the
  key seemed dead there (VirtualBox "send the shutdown signal").
- **Ctrl+Alt+Del** opens Plasma's logout greeter, whose QML the VeltOS
  global theme replaces with Windows' security options screen. The
  greeter offers no way to start programs; the screen uses Plasma5Support's
  "executable" data engine (Task Manager, KDE's Users page). Alternative: a
  separate full-screen program bound to Ctrl+Alt+Del — a normal window
  cannot cover the taskbar and the lock screen like the greeter's layer.
- **Display scale** in Windows' 25 % steps: KWin picks 5 % steps from the
  screen size (105 % for a VM screen), which blurs text and 1 px lines.
  `display-scale` rounds each screen the user has not had before once, at
  sign-in; later choices are kept.
- **Title bars like Mica**: the frame colour is the VeltOS apps' window
  background (Windows 11 apps draw no separate title bar), not Fluent's
  white.

#### 2.3.12 Store: a VeltOS app instead of restyling Discover

Discover's pages are compiled into the program (Qt resources), so its
layout cannot be changed without forking it. VeltOS Store is a small
PySide6/QML program on the same data and services Discover uses: Debian's
AppStream catalogue (`gir1.2-appstream-1.0`) and PackageKit (`pkcon`, so
authorisation stays with PackageKit and polkit). Alternatives: forking
Discover (against the project rules), GNOME Software (GTK, other look),
a web store (needs a server). Trade-offs: no ratings, Flatpak or
firmware updates yet; the curated lists are package names in the code.

### 2.4 Graphics drivers

- AMD and Intel: kernel drivers + Mesa from Debian (OpenGL, Vulkan via RADV
  and ANV, VA-API). Nothing proprietary needed.
- NVIDIA: the live image uses nouveau (+ NVK Vulkan in Mesa 25.0). Debian
  trixie ships NVIDIA 550.163.01 in non-free (proprietary and open kernel
  module variants) as DKMS packages. They are **not preinstalled**, because
  DKMS modules must be built against the installed kernel and, with Secure
  Boot on, signed with an enrolled MOK key. Recommending and installing the
  right variant per GPU (and handling MOK enrolment and reboots) is the job
  of the Velt Hardware Manager (Milestone 2).
- Never install drivers from unverified downloads (prompt principle).

### 2.5 Live system and installer

- `live-build` 1:20250505+deb13u1 (Debian's own tool for Debian live images),
  `live-boot` + `live-config` for the live session, SDDM autologin as user
  `velt` (live-config default password: `live`).
- Bootloaders: **GRUB for both BIOS and UEFI** (live-build's default BIOS
  loader is isolinux). One menu/theme for both firmware types; isolinux is
  effectively unmaintained upstream. Secure Boot via Debian's signed shim and
  GRUB (`--uefi-secure-boot enable`).
- Installer: Calamares 3.3.14 with VeltOS settings
  (`calamares-settings-veltos`, derived from Debian's ISC-licensed
  settings). Decisions:
  - UEFI installs get `shim-signed` + `grub-efi-amd64-signed` so installed
    systems boot with Secure Boot on;
  - the EFI directory stays `\EFI\debian\` because Debian's signed GRUB
    looks for its configuration there; only the firmware boot entry label
    is changed to "VeltOS" (a new entry is created before the old one is
    removed; anything unexpected leaves entries untouched);
  - bootloader packages are in the ISO's package pool, so installs work
    offline;
  - `os-prober` is enabled so Windows stays bootable in dual-boot setups;
  - **disk encryption works like BitLocker**: "Encrypt system" encrypts the
    system partition (LUKS) and leaves a 1 GiB ext4 `/boot` unencrypted.
    The VeltOS boot screen (Plymouth + cryptsetup-initramfs) asks for the
    password, with the installer's keyboard layout, Windows-like texts
    ("Enter the password to unlock this PC", "The password is incorrect.
    Try again.") and unlimited tries (`tries=0` in crypttab, written by
    the `crypttab-tries` installer job; cryptsetup's default of three tries
    ends in a recovery shell).
    Alternative rejected: `/boot` inside LUKS (Calamares' default). GRUB
    then asks on a text screen with a US layout, can only open LUKS1, and
    the installed system needs a key file in the initramfs; the product
    owner's install ended in `grub rescue`. Trade-off: kernel and initramfs
    are readable and could be modified by someone with physical access
    (as on most Linux distributions' default encrypted installs); the
    system data is protected. `luksGeneration` stays LUKS1 so that manual
    layouts without a separate `/boot` still boot (GRUB cannot open LUKS2
    with Argon2id); LUKS2 for the automatic layout is a possible later
    improvement.
  - The texts on the password screen are changed only in the initramfs
    copy of cryptsetup's shell functions (veltos-boot initramfs hook); if
    cryptsetup changes that code, its own texts stay (the hook warns). The
    alternatives — a crypttab `keyscript` or a diverted cryptsetup file —
    would change installed configuration or packaged files and are not
    supported by systemd-cryptsetup.
  Debian-installer is not included (keeps the ISO smaller).
- Boot splash: Plymouth `veltos` theme (`veltos-boot`): logo with a dot
  spinner on near-black, like Windows; GRUB theme and `GRUB_DISTRIBUTOR=VeltOS`
  on installed systems.
- SquashFS: zstd level 15 instead of xz — slightly larger ISO but much faster
  decompression, which shortens live boot and application start-up.

### 2.6 Build system

- Everything runs in a Docker container (`build/builder/Dockerfile`, base
  image pinned by digest). The host needs only Docker; nothing is installed
  on or changed in the host OS.
- live-build needs a real Linux filesystem, so the build tree is a Docker
  named volume (`veltos-build`) that also caches downloaded packages.
- `SOURCE_DATE_EPOCH` is set from the last git commit, and every build
  records its exact package list (`*.packages`) and tool versions
  (`build-info.txt`).
- Reproducibility status: inputs are pinned *except the Debian archive
  state*. Bit-for-bit reproducible ISOs additionally need a pinned
  snapshot.debian.org timestamp (`VELTOS_DEBIAN_MIRROR` is the hook for it)
  and a verification run (two builds, compare hashes). Not done yet.

### 2.7 Testing

- `tests/boot/vmtest.py` boots the ISO under QEMU/KVM in the same container
  (BIOS, UEFI, UEFI + Secure Boot with Microsoft keys) and checks the result
  through QMP (screenshots) and the QEMU guest agent (commands in the guest).
- `qemu-guest-agent` is shipped in the image on purpose: it only starts when
  a hypervisor provides its virtio channel, and it is useful for VeltOS users
  running in VMs. The host already fully controls a VM, so it adds no new
  privilege boundary.
- VMs do not replace real NVIDIA/AMD/Intel hardware testing (see
  `docs/testing.md`).

### 2.8 Updates (initial position)

Conventional APT updates from Debian (signed metadata, security archive)
plus VeltOS packages. An image-based/transactional model (OSTree, A/B
partitions) is not adopted until a concrete problem justifies its
complexity; a comparison and the recovery strategy are Milestone 5 work.
Snapshot-based rollback (e.g. Btrfs + snapper) is a candidate to evaluate.

### 2.9 Windows compatibility and gaming (planned, not implemented)

- Wine 10.0 from Debian as the base; per-application prefixes; winetricks;
  DXVK and VKD3D-Proton for Direct3D → Vulkan; Steam (Debian `steam-installer`,
  needs i386 multiarch) with Proton for games. Details and the compatibility
  matrix arrive with Milestones 3 and 4.
- VeltOS will never claim that all Windows software works. Anti-cheat
  kernel drivers, some DRM and some launchers are known to fail under Wine.
- Wine is not a security sandbox; untrusted `.exe` files are never run with
  elevated privileges.

## 3. Licensing and redistribution

- VeltOS code: GPL-3.0-or-later (`LICENSE`). VeltOS artwork:
  CC-BY-SA-4.0. Derived Breeze colour schemes stay LGPL-2.0-or-later.
- The ISO includes Debian `non-free-firmware` (redistributable firmware
  blobs, as Debian's own images do) and CPU microcode. Nothing from
  `non-free` is preinstalled yet; the NVIDIA driver will only be installed
  on the user's machine from Debian's archive.
- "VeltOS" name/logo: trademark policy still to be written.

## 4. Technical risks

| Risk | Impact | Mitigation |
|---|---|---|
| Plasma layout script runs only for new users | Updates to the layout never reach existing users | Treat layout changes as new-user defaults; provide an explicit "reset to VeltOS layout" action later |
| Plasma 6.3 in trixie ages during the Debian cycle | Missing newer Plasma features | Accept for stability; evaluate backports per release |
| NVIDIA proprietary driver + Secure Boot (DKMS, MOK) | Black screens / unsigned modules for NVIDIA users | Nouveau/NVK default; guided install + MOK enrolment in Hardware Manager; test on real RTX hardware |
| Live-build image not bit-for-bit reproducible | Can't independently verify ISOs | snapshot.debian.org pinning + double-build check (planned) |
| Calamares with Debian settings | Debian branding in installer, untested installs | VeltOS calamares settings + VM install test (Milestone 5) |
| Windows compatibility expectations | Users expect every .exe to work | Honest compatibility matrix, per-app profiles, clear error messages |
| 1–1.5 GB idle RAM target with Plasma | May not be met with Recommends on | Measure in VM boot test; trim Recommends with data |
| Single developer host (Docker Desktop, nested KVM) | Builds depend on one machine setup | Container-only builds; CI (planned) |
