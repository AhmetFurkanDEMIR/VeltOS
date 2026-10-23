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

The same mechanism changes KWin's window frame engine (Aurorae), whose QML
KWin also finds through `XDG_DATA_DIRS` (`kwin/aurorae/aurorae.qml`):
Aurorae button SVGs cannot differ between normal and maximised windows,
so the rounded corner of the close button's red hover showed in the screen
corner of maximised windows. VeltOS lets a button SVG carry
`hover-maximized`/`pressed-maximized` pictures (three replacements in
`AuroraeButton.qml`; themes without them look as before). Alternatives:
a square hover everywhere (sticks out of the rounded window corner), a QML
window decoration of our own (much more code to maintain), Breeze-style
C++ decoration (a fork).

The mechanism can also **add a file** to a Plasma package (`"add"`,
2026-10-22): the desktop's Windows 11 behaviour lives in one VeltOS QML
file placed next to Plasma's folder view (`VeltOSDesktop.qml`), and the
replacements in `FolderView.qml` are a dozen one-line hooks into it
(right-click, Menu key, Delete/F2/Ctrl+X/F5). The file is dropped like
any other change when Plasma gains a file of that name.

#### 2.3.8b The taskbar in the accent colour; Plasma themes without colours of their own (2026-10-22)

- The VeltOS Plasma themes (derived from Fluent-kde) shipped Fluent's
  practice of a `colors` file in the theme. Plasma then draws the panel,
  Start and the flyouts in those fixed colours and ignores the colour
  scheme the user has, accent included: with a red accent, Start's search
  field stayed VeltOS blue (VM). Since the file held exactly the VeltOS
  Light/Dark scheme that the global theme selects anyway, the themes now
  have no `colors` file and Plasma follows the system scheme — so the
  taskbar, Start and the flyouts take the user's accent, as Windows 11's
  do. Trade-off: a user who picks a non-VeltOS colour scheme in some
  other way also recolours the taskbar (VeltOS Settings offers only the
  VeltOS pair).
- The owner asked for the taskbar to change colour "by theme and accent,
  with a nice transition, like Windows 11". Read as: Windows 11's taskbar
  takes on the accent (acrylic tinted by it); VeltOS draws a soft accent
  glow behind the centred icons (`TaskbarTint.qml`, added to Plasma's
  panel view through the override mechanism), which cross-fades and
  sends one band of colour across the bar when the accent or light/dark
  mode changes. Nothing animates at rest: in VMs with software rendering
  every animated frame of the panel costs CPU. Alternatives: an accent
  layer in the theme's SVGs (no transition, and SVG gradients cannot take
  the accent colour), a switch between the panel's translucent and opaque
  backgrounds (Plasma cross-fades those, but "opaque" also changes when
  windows touch the bar), Windows' "Show accent colour on Start and
  taskbar" switch (not asked for as such; possible later).
- `plasma-apply-colorscheme --accent-color` rewrites kdeglobals but does
  not make plasmashell reload its colours; KDE's own colours module sends
  `org.kde.KGlobalSettings.notifyChange(0, 0)` (PaletteChanged) and VeltOS
  Settings now does the same after an accent change.

#### 2.3.8a The desktop: Windows 11's menus inside Plasma's folder view (2026-10-22)

The product owner wants the desktop to behave like Windows 11's: its own
right-click menu (View, Sort by, Refresh, New, Display settings,
Personalize, Open in Terminal), "New > Folder" that makes the folder and
opens its name at once (Plasma's `KNewFileMenu` asks in a dialog), a
blink on Refresh, and system icons (Recycle Bin, This PC, Store) that
cannot be deleted. The desktop is Plasma's folder-view containment
(`org.kde.desktopcontainment`, C++ model + QML view).

- Decision: keep Plasma's containment and change its QML through the
  override mechanism (2.3.8). The added `VeltOSDesktop.qml` holds two
  `PlasmaExtras.Menu`s (Plasma's own QMenu-backed menus, styled by the
  application style like every other VeltOS menu), runs commands through
  `plasma5support`'s executable engine (the folder view cannot write
  files; a small helper, `desktop-new`, picks Windows' names "New
  folder (2)"), waits for KDirLister to list the new item and then
  selects it and calls the view's own `rename()`; protected icons are
  recognised by file name (`recycle-bin.desktop`, ...) through the
  model's `urlForIndex`. Texts use `i18nd` with a VeltOS catalog
  (`veltos-desktop.mo`), so KDE's catalog for the containment stays as
  it is.
- Alternatives: a VeltOS desktop containment of our own (a second file
  manager's worth of code: positioning, drag and drop, selection,
  previews — rule 5); patching plasma-desktop (a fork); Plasma's
  containment menu with fewer entries (`context-menus` already does
  that, but "New" still went through KDE's dialog, and Plasma's
  "Enter Edit Mode"/"Add Widgets" could not be removed from it).
- Trade-off: as with every override, the hooks are checked against
  Plasma's text and fall back to Plasma's own desktop after a Plasma
  update that changes them.

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

**VirtualBox** (2026-10-22). Its VMSVGA display (the vmwgfx driver) does
not even fall back by itself: with 3D acceleration off, KWin cannot
configure its output and plasmashell and the QML apps cannot create a GL
context, and the desktop stays black. VeltOS then forces Mesa's llvmpipe
for the whole session (`LIBGL_ALWAYS_SOFTWARE=1`) — and only that: KWin's
own OpenGL scene runs on llvmpipe, so window animations, Task View's
previews and the desktop labels' shadows all work. Rejected: KWin's
QPainter compositor (`KWIN_COMPOSE=Q`), which cannot render QML scene
effects' thumbnails (Task View's previews stayed black), and Qt Quick's
software scene graph (`QT_QUICK_BACKEND=software`), which paints slowly
and cannot draw shader effects (grey boxes behind the desktop labels);
both were shipped for a few hours and withdrawn. The rule lives in one
script, `needs-software-rendering`: VirtualBox by DMI *and* Mesa's
GBM-platform renderer being llvmpipe (`eglinfo -B`, no display needed).
With 3D acceleration on, the same display gives real OpenGL (Mesa's svga
driver, "SVGA3D") and nothing is forced; nothing in sysfs or DMI tells
the two apart. Only VirtualBox is probed, so real GPUs and QEMU never run
it. The sign-in screen gets the same answer through an `ExecStartPre` of
`sddm.service` (`sddm-virtualbox-env`: a later `sddm.conf.d` drop-in for
the greeter's environment, and a marker in `/run/veltos` for the
greeter's compositor wrapper), because SDDM's `GreeterEnvironment` is
static and the sddm user may not open the render node. Alternative
considered: asking the owner to enable 3D acceleration — the better
experience (native OpenGL), and the rule leaves it alone, but the system
must also come up when it is off. Trade-off: llvmpipe is CPU rendering;
the desktop appears later than on a GPU (about two minutes on 4 vCPUs),
and Mesa's svga driver still reports "No 3D enabled" in the journal.

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
- SquashFS: zstd instead of xz — a larger ISO but much faster
  decompression, which shortens live boot, application start-up and the
  installation's unpacking. Since 2026-10-23 level 19 with 1 MiB blocks
  (`MKSQUASHFS_OPTIONS="-b 1M"`, build-iso.sh): 11 % smaller than level 15
  with 128 KiB blocks and unpacking as fast (measured on 3.9 GB of the
  image: 1372 → 1220 MB, 3 s to unpack either way); xz would save 20 % but
  unpack twice as slowly, and the product owner chose "lossless only" for
  the ISO size (see 2.23).

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

### 2.10 File dialogs: one Windows 11 dialog for every program (2026-10-21)

- The product owner wants every open/save/folder window to be Windows
  11's. VeltOS writes one dialog (File Explorer's `--pick` mode, reusing
  Explorer's address bar, navigation pane and views) and makes every
  program use it through the desktop portal: `veltos-explorer --portal`
  is the `org.freedesktop.impl.portal.FileChooser` backend, named in
  `/etc/xdg/xdg-desktop-portal/kde-portals.conf` (everything else stays
  with KDE's backend).
- Reaching it: GTK programs with `GTK_USE_PORTAL=1`; Firefox and Mail with
  `widget.use-xdg-desktop-portal.file-picker=1`; Qt, KDE and LibreOffice
  (kf6 plugin uses QFileDialog) with `QT_QPA_PLATFORMTHEME=xdgdesktopportal`,
  Qt's portal platform theme, which wraps the KDE theme (`themeNames()`)
  and takes only file dialogs and the colour scheme from the portal
  (checked in Qt 6.8's `qxdgdesktopportaltheme.cpp`). VeltOS' own apps call
  the dialog directly (JSON over a pipe; Settings) or use QML
  `FileDialog`, which goes through the same theme.
- Alternatives: replacing KDE's `KFileWidget` (impossible without
  patching plasma-integration/KIO); a Qt platform theme plugin of our own
  (C++, must follow Qt releases); per-app dialogs (every Qt/GTK program
  would keep its own). The portal is the one hook every toolkit honours.
- Trade-offs: the dialog is a separate window (the portal gives a
  `parent_window` handle VeltOS cannot attach to from PySide6); dialogs
  opened in the first milliseconds of a Qt program, before the portal's
  version is known, fall back to KDE's; file dialogs inside Flatpak apps
  would go through the same backend (good).
- Start-up (2026-10-22): the theme must not reach Plasma's own services
  or the portal's backends. A Qt program starting with it asks the portal
  (colour scheme) and blocks up to the D-Bus timeout (25 s); at session
  start the portal cannot answer, because its backends are Wayland
  clients of the very KWin that is asking — so kwin, kcminit, ksplash,
  kded6, ksmserver, kactivitymanagerd and plasmashell each waited 25 s,
  the portal failed after 90 s and plasmashell came after ~95 s instead
  of ~18 s (QEMU boot tests since the 2026-10-21 evening ISO;
  `systemd-analyze --user blame` in a VM). VeltOS gives every Plasma user
  service but plasmashell a drop-in `Environment=QT_QPA_PLATFORMTHEME=kde`
  (`PLASMA_SERVICES`, veltos-desktop), the same to its polkit agent, and
  the portal's own dialogs KDE's theme. plasmashell keeps the portal
  theme: programs started from Start inherit its environment (KIO's
  launcher hands it to their transient unit), and with KDE's theme there
  every program lost the Windows 11 dialogs (2026-10-22); once the other
  services no longer wait, the portal is up within seconds for it. Alternatives: setting the theme
  only for programs the user starts (Plasma has no such layer: launched
  programs inherit the session environment); a `service.d` drop-in for
  all user services (would also strip launched programs, which Plasma
  runs as transient services); dropping the portal theme altogether (no
  Windows 11 dialogs in Qt programs). Trade-off: the list of Plasma's
  units must follow Plasma (a drop-in for a unit that is not installed is
  inert).

### 2.11 Administrator password: VeltOS' own polkit agent (2026-10-21)

- polkit asks the *session's* authentication agent, so the only way to
  show a Windows 11 "User Account Control" window for every program
  (Store, Settings, pkexec, KDE tools) is to be that agent: `veltos-auth`
  registers `org.freedesktop.PolicyKit1.AuthenticationAgent` for the login
  session (GLib/GDBus, no Qt in the resident process) and opens the
  prompt (PySide6/QML) per request. The password is checked by polkit's
  own setuid helper, exactly as KDE's and GNOME's agents do, so VeltOS
  handles no PAM and no privileges itself.
- KDE's agent (`plasma-polkit-agent.service`) is masked; the package does
  not remove polkit-kde-agent-1 (plasma-desktop depends on it).
- Alternatives: restyling KDE's agent (its window is C++/QML inside the
  binary; no override hook); patching polkit-kde-agent-1 (a fork to keep
  up with Plasma). Rejected per rule 5.
- Known limit: KWin on Wayland does not keep the prompt above everything
  (no secure desktop); the window is activated and centred.

### 2.12 Small resident helpers: alarms and the portal backend (2026-10-21)

- Rule 7 asks for a reason for every daemon. VeltOS Clock's alarms must
  ring with the app closed (Windows does the same with a background
  task), so `veltos-clock-agent` runs with the session: GLib only, a check
  every 15 s plus a file monitor, about 15 MB. The portal backend
  (`veltos-explorer --portal`) is D-Bus activated and ends after five
  idle minutes; the authentication agent is required by polkit's design.
- Text size: VeltOS apps draw text at fixed pixel sizes (Windows 11
  proportions). Accessibility's text size is kept where KDE keeps it (the
  kdeglobals fonts) and every VeltOS app derives a `textScale` from it,
  so KDE programs, Plasma and VeltOS apps follow one setting.

### 2.13 VeltOS Office: Microsoft 365's start screen in front of LibreOffice (2026-10-22)

- The product owner wants Word, Excel and PowerPoint "exactly like
  Microsoft's: content, theme, animations". Rule 5 (no rewrite, no fork)
  and the licence rule out copying Office or patching LibreOffice, so
  VeltOS puts what Office users see first in front of LibreOffice: a
  VeltOS start screen (PySide6/QML, `veltos-office`) in the layout of
  Microsoft 365's Home / New / Open / Account / Options pages, in the
  app's colour, with Windows 11's entrance animations, templates with
  thumbnails and the recent list; LibreOffice opens the chosen document
  with the Tabbed interface and Colibre icons (the nearest thing to the
  ribbon), named "VeltOS Office" in its titles. The document window
  itself stays LibreOffice's: its tab strip is not in the app's colour
  and it has no animations (that would need LibreOffice changes), and
  closing the last document shows LibreOffice's Start Center.
  Alternatives: OnlyOffice Desktop Editors (closest to Office's look) is
  not in Debian 13 (rule 8: signed archives only); LibreOffice's gtk3
  plugin with per-app GTK CSS could colour the tab strip but would make
  the Office apps the only GTK-styled programs on VeltOS and lose the
  Qt/portal integration.
- The title bar of LibreOffice's windows does get the app's colour, as
  Office's has: the Aurorae frame (VeltOS' changed copy of KWin's QML,
  `plasma-overrides/aurorae.json`) tints the title bar by the window's
  caption ("… — VeltOS Office Writer"; KDecoration3 gives the QML no
  window class) and switches to white caption text
  and white-glyph buttons ("-ondark" states in the button SVGs). On the
  dark frame nothing is tinted, like Office's Black theme. This is a
  frame-side rule, not a KWin window rule, so users' own rules are
  untouched.
- Recent files are read from LibreOffice's own list (PickList in the
  user profile), not kept twice; the start screen adds only what it
  opened itself until LibreOffice records it. Templates are real
  LibreOffice templates (VeltOS' own built at package build time from
  flat ODF by LibreOffice itself, with thumbnails), so "New from
  template" is LibreOffice's `-n`, and users' templates in LibreOffice's
  folder appear too.

### 2.14 Disk Management: a VeltOS app on UDisks2 (2026-10-22)

- The product owner wants Disk Management "nicer, like Windows 11". KDE
  Partition Manager (what VeltOS named "Disk Management" until now) is a
  Qt Widgets program with its own layout and dialogs; restyling it would
  stay KDE's layout. VeltOS Disk Management (`veltos-disks`,
  PySide6/QML like the other VeltOS apps) draws Windows' layout: the
  volume list over the disk map with partitions to scale and Disk
  Management's partition colours, and the same menu entries and dialogs
  (Format, Delete Volume, New Simple Volume, label, Initialize Disk,
  Properties).
- It does nothing itself: every change is a UDisks2 method call
  (`busctl --system`), the system service every desktop uses, which
  enforces polkit (the VeltOS administrator prompt appears where
  UDisks2's rules ask) and refuses what it must not do. VeltOS adds its
  own guard rails like Windows': the running system's volumes (`/`,
  `/boot`, the EFI system partition, the live medium) cannot be
  formatted or deleted, optical and read-only devices neither, and a
  disk with a partition table is never initialized again. Formats
  offered are those whose `mkfs` is installed (NTFS, exFAT, FAT32,
  ext4). Alternatives: KDE Partition Manager's KPMcore (a C++ library,
  root helper of its own, no Windows look); GNOME Disks (a GTK program,
  again its own layout); writing partition tables with `sfdisk`/`parted`
  from the app (would need VeltOS' own privileged helper and policy —
  UDisks2 already is that helper).
- No daemon: the window re-reads UDisks2 every 5 s only while it is
  open, and after each action.

### 2.15 Installer pages: Calamares' QML modules with VeltOS QML (2026-10-22)

- The product owner wants every installer step in the Windows 11 setup
  look, with animations, and the log only when a step fails. Debian's
  Calamares 3.3.14 ships QML variants of the welcome, location, keyboard,
  users and finished steps (`welcomeq`, `localeq`, `keyboardq`, `usersq`,
  `finishedq`); with `qmlSearch: both` Calamares loads
  `<branding>/<module>.qml`, so VeltOS writes those pages itself
  (illustration on the left, question and answers on the right, sliding
  page changes; shared parts `VeltPage`/`VeltList`/`VeltField`/
  `VeltButton`/`VeltToggle`/`VeltInfoBar`) and binds them to the modules'
  own `config` objects. The modules' logic (locale lists, keyboard
  preview, password rules, writing the configuration) stays Calamares'.
  The partition step has no QML variant and stays Calamares' C++ page,
  restyled by the branding style sheet (Windows-like texts, no
  partition-table jargon, VeltOS disk picture).
- While installing, Back/Next/Cancel are hidden
  (`hide-back-and-next-during-exec`, `disable-cancel-during-exec`) and
  the slideshow (`show.qml`, screenshots of VeltOS apps) runs; the
  finished page shows the failing step's message and details in a
  terminal-style box only when the job queue failed (`config.failed`),
  otherwise a "ready" page. Calamares' error dialog has no parent and
  so no branding style sheet: `install-veltos` passes the style sheet to
  Qt itself (`-stylesheet`), which styles every window of the process.
- Each QML step has its own engine and only the slideshow is
  retranslated when the language changes, so the pages pick their text
  each time they are shown (`VeltPage.t()`), not at load time. The
  installer runs with `-style kvantum`; the pages use
  `QtQuick.Controls.Basic` so Qt does not look for a QML style of that
  name.
- Alternatives: a VeltOS installer of its own (partitioning, bootloader
  and user setup are exactly what Calamares already does safely);
  patching Calamares' C++ pages (a fork to carry). Trade-off: the
  partition page keeps Calamares' structure.

### 2.16 Start-up screen resolution (2026-10-22)

- GRUB drew the boot menu and passed Linux a small mode, so the start-up
  screen was small. `boot-resolution` (veltos-boot) writes
  `GRUB_GFXMODE=<mode>,1024x768,800x600,auto` to
  `/etc/default/grub.d/veltos_resolution.cfg`; with
  `GRUB_GFXPAYLOAD_LINUX=keep` the splash is drawn at that mode too.
- At installation a Calamares job (`boot-resolution` module, before the
  bootloader step) takes the screen's preferred mode from the kernel's DRM
  connectors (built-in panel first) and writes it into the target. At
  each sign-in a user service (`veltos-boot-resolution.service`) reads the
  mode the primary screen is set to (`kscreen-doctor -j`) and, when it
  differs, has the root helper rewrite the file and run `update-grub`
  (`pkexec`; polkit action `org.veltos.boot.resolution`, allowed for the
  active local user without a password; `--root` is refused under
  pkexec). Live media are left alone.
- Risk: VirtualBox with Hyper-V stopped with a triple fault when GRUB
  chose `auto` on BIOS (AGENTS.md). The list puts the detected mode
  first and safe modes before `auto`; it must be checked in VirtualBox
  BIOS before relying on it there.

### 2.17 Start-up and sign-in time (2026-10-22)

- Boot: Debian compiles every AppArmor profile at boot when no cache for
  the running kernel's feature set exists (11 s in the VM). The image
  ships the cache: hook `8500-veltos-apparmor-cache` compiles it at build
  time against the kernel features recorded from a VeltOS VM
  (`/usr/share/veltos/apparmor/kernel-features.abi`, made with
  `aa-features-abi -x -w`), into the same hash directory the boot would
  use; the verify hook and the boot test (AppArmor < 3 s) check it.
  Alternative: disabling AppArmor (less security; rejected).
- Sign-in: xdg-desktop-portal 1.20 looks for a Lockdown backend and, as
  KDE's has none, starts the GTK backend "as a last resort", which waits
  for `graphical-session.target` — 25 s; and plasmashell started with the
  portal platform theme waited for the KDE portal, which waits for
  plasmashell. `kde-portals.conf` (veltos-explorer) sets `Lockdown=none`
  and `Settings=kde`, and plasmashell's unit starts it with
  `-platformtheme kde` (a Qt argument wins over the environment), so the
  programs it launches keep the portal theme and VeltOS' file dialogs.
  Desktop about 2 s after signing in in the VM (was about 30 s).

### 2.18 Automatic Repair (2026-10-22)

- Windows starts Automatic Repair after two starts that did not finish.
  VeltOS does the same without new boot software: veltos-boot's
  `/etc/grub.d/10_linux` counts each VeltOS start in GRUB's environment
  block (`veltos_failed`, `save_env`); `veltos-boot-ok.service`
  (veltos-recovery) clears the count once the sign-in screen is up; a
  start that ends in emergency or rescue mode, or a sign-in screen that
  keeps failing (`OnFailure=` on sddm), restarts the PC. At a count of
  two GRUB's default becomes the "VeltOS Recovery" entry
  (`systemd.unit=veltos-recovery.target nomodeset`), which runs the
  repair window: PySide6/QML on Qt's `linuxfb` platform on the first
  console, so it needs neither the compositor nor a graphics driver.
- The window offers Restart, Startup Repair (dpkg/apt repair from the
  disk only, free space, initramfs, GRUB, failed units — no network),
  Safe mode (a one-time `grub-reboot` into the entry with `nomodeset`),
  Command Prompt (the window closes and a sign-in opens on the next
  console: while Qt draws on the frame buffer its console is in graphics
  mode, and Linux ignores console switches then), the last start's
  problems (the journal is kept on disk, at most 200 MB) and Turn off,
  in English and Turkish.
- Safe mode needs X11: Debian's kernel has no simpledrm, so a start with
  `nomodeset` has only the firmware's frame buffer (efifb/vesafb) and no
  DRM device, and KWin (Wayland) cannot start. `veltos-safe-graphics`
  switches SDDM to X11 for such starts only and the VeltOS sign-in screen
  then starts Plasma on X11 (Xorg's fbdev driver); every start with a
  graphics driver gets Wayland again.
- GRUB can write its environment block only on plain file systems:
  `10_linux` adds the counting only when `/boot/grub` is on one
  (`grub-probe` file system and abstraction checks); on Btrfs, LVM, RAID
  or encrypted `/boot` VeltOS starts without it (no false repair loops).
  Alternatives: systemd-boot's boot counting (`boot-complete.target`,
  needs systemd-boot and UEFI; VeltOS uses GRUB for BIOS too); a repair
  mode inside the Plasma session (cannot help when the session is what
  fails).

### 2.19 Taskbar window previews from KWin (2026-10-22)

- Plasma's window tooltips capture windows through the screen-cast
  service, which gives garbled pictures with software rendering (most
  VMs), and they do not look like Windows 11's cards. A KWin script
  (`kwin/scripts/veltostaskbarpreview`, QML, KWin's public API only)
  draws the cards itself with `WindowThumbnail`, which works with every
  renderer: icon, title, close button, live picture, a click switches,
  pointing at a card for a moment shows that window alone (Peek: the
  other windows fade; KWin's Highlight effect is not reachable from a
  script). The script finds the pointed-at button through the windows'
  `iconGeometry`, which Plasma's task manager already reports to KWin for
  the minimize animation; the task manager's own tooltips are off for
  running apps.
- Notification pop-ups slide in from the right like Windows 11 toasts:
  a KWin effect (`kwin/effects/veltostoast`) animates the pop-up windows
  (QML inside the pop-up cannot move its window); it takes the animation
  over from KWin's Fading Popups.

### 2.20 Desktop system icons that cannot be deleted (2026-10-22)

- This PC, the Recycle Bin and the Store must stay on the desktop, also
  against a terminal. Files in a folder the user owns can always be
  deleted by the user, and `chattr +i` would stop root too (deleting the
  account would fail). `veltos-desktop-guard`, a D-Bus system service
  (`org.veltos.DesktopGuard`, activated on demand, gone after a minute),
  makes the three launchers root's files and the user's desktop folder
  root's with the user's group, group-writable and sticky (1775, like
  `/tmp`): the user keeps creating and deleting their own files, but not
  root's. It acts only on the caller's own desktop (the caller's uid from
  the bus, folders opened one name at a time without following links).
  File Explorer and the desktop refuse to delete, cut or rename them
  with Windows' message.
- Trade-off: a group-writable desktop is only private while the group is
  the user's alone. The guard therefore acts only for a user private group
  (Debian's default: named after the user, no other members, nobody
  else's primary group) and leaves a shared group's desktop alone, where
  the icons stay deletable copies (2026-10-23, with unit tests on a fake
  account's home).

### 2.21 Installed Windows programs from Wine's registry files (2026-10-22)

- Settings' list of Windows programs used Wine's own uninstaller window
  and took many seconds. Wine keeps its registry as text
  (`system.reg`, `user.reg`), so `veltos_winapps/programs.py` reads the
  Uninstall keys (also `Wow6432Node`) directly: name, publisher,
  version, size, date, in milliseconds. Removing still runs the
  program's own uninstaller through Wine (`uninstaller --remove`), as
  Windows does.

### 2.22 VeltOS Mail: Thunderbird in Outlook's look (2026-10-22)

- The product owner wants the mail app "exactly like Outlook", named
  VeltOS Mail. Writing a mail client is out of scope (IMAP, SMTP,
  OAuth and encryption are security-critical), and Evolution is a GTK
  program with its own layout; VeltOS keeps Debian's Thunderbird 140 ESR
  and changes its look and defaults from outside the program:
  - autoconfig (`/usr/lib/thunderbird/veltos.cfg`, `tools/firefox.py`)
    registers user style sheets for every profile (`mail.css` and the
    generated `mail-header.css`), renames window titles ("VeltOS Mail")
    and writes Outlook's defaults into Thunderbird's own settings store
    (xulstore) only where the user has none: the simplified ribbon
    (New mail, Delete, Archive, Report, Move, Reply, Reply all, Forward,
    Read/Unread, Tag), the reading pane header (big sender picture,
    icon-only actions) and no menu bar in the new message window (Alt
    shows it);
  - `mail.css` draws Outlook's blue title band (name, centred search,
    window buttons) over the toolbar wrapped into two rows, the ribbon,
    the reading pane (subject first), the new message window, the
    add-account card and an account page without Thunderbird's story,
    donation request and links;
  - default preferences: one tab without a tab bar, names only in the
    message list.
- Alternatives: `userChrome.css` (needs a per-profile file and a legacy
  preference in every profile); a WebExtension theme (colours only).
  Trade-off: the selectors are matched against Thunderbird 140.17's
  markup and must be checked again with each ESR (they are listed with
  the files they were checked against); menus and dialogs Thunderbird
  builds from its brand strings ("About Thunderbird") keep the name.

### 2.23 A lighter installer, a faster start, a smaller ISO (2026-10-23)

The product owner's first VirtualBox installation of the 38-item ISO
(VMSVGA, no 3D) failed at its end, stuttered, and the live start was
slow; they also asked for an ISO under 2 GB "without giving up quality,
graphics or animation", and chose "lossless only" when the trade-offs
were measured (below).

- **Installer load.** Measured in that VM: Calamares 140 % CPU and KWin
  110 % on the welcome page, 99 % idle without it. Cause: Calamares loads
  the slideshow at start, and its first slide's endless float animation
  redrew the whole window 60 times a second behind the other pages (with
  Mesa's software rasterizer). Fixes, keeping every animation: slides
  animate only while the slideshow is shown, the pages' ambient motion
  only on the shown page; where Mesa draws in software the installer runs
  on Qt Quick's software renderer (`QT_QUICK_BACKEND=software`, which
  repaints only what changed; our QML uses no shaders or layers) and the
  slow motions advance 20 (zoom: 10) times a second. After: Calamares
  24 % with the animations running (VirtualBox), 6 % (QEMU).
  Alternative: turning the ambient animations off in VMs (rejected: the
  owner's "no compromise on animation").
- **Installer theme.** The installer follows the session's light/dark
  mode and accent like the rest of VeltOS. Calamares runs as root and
  sees nothing of the user's settings, and pkexec clears the environment,
  so `install-veltos` reads the theme as the user (`installer-theme`)
  and hands it to a root wrapper (`start-calamares`, its own polkit action
  with `allow_gui`), which writes the style sheet (light or a dark twin
  generated at build time, accent put in) and passes one argument the QML
  reads (`veltos-theme=…`; Calamares parses only options). Alternatives:
  reading the user's kdeglobals from root's QML (needs XMLHttpRequest file
  access, root reading user files), a generated QML file in /etc
  (conffile edits at run time).
- **Live start.** `ldconfig.service` took 10.6 s of the live start in
  VirtualBox (3.2 s in QEMU) because the image had no `/etc/.updated`
  (systemd's ConditionNeedsUpdate): a late chroot hook runs
  `systemd-update-done`, which also spares installed systems that work at
  their first start. live-config ran 35 components (~90 ms each warm, 11 s
  cold in VirtualBox); the boot line lists the 21 a VeltOS live session
  never needs (`nocomponents=`, other display managers, GNOME/Xfce bits,
  apport, ssh keys, X11 config, time zone).
- **ISO size: lossless only** (3.62 GB before; each saving measured on
  the 2026-10-23 image as its zstd-compressed share):
  Wine's PE DLLs without DWARF debug information (235 MB; veltos-winapps
  strips them on install and Wine updates — Debian builds them with
  `-g`, the code is unchanged), no initramfs copy inside the squashfs
  (127 MB; the installer makes the target's after removing the live
  packages — live-tools' update-initramfs wrapper does nothing from a
  live medium, which first gave installed systems without one — and
  before update-grub; a `boot-check` job stops an installation whose
  kernel has no initramfs in the boot menu),
  Noto's extra weights (113 MB; regular and bold of every script stay,
  CJK included), package changelogs (64 MB; the copyright files stay),
  apt's package caches and source indices (63 MB; regenerated by apt),
  firmware for Marvell network-switch chips (58 MB), KDE's unused "Next"
  wallpaper (41 MB), an English speech model (27 MB), and zstd level 19
  with 1 MiB blocks instead of level 15 with 128 KiB (11 %, unpacking as
  fast). Result: 2.45 GB (2,445,506,560 bytes, ISO 20261023-045821).
- **Rejected for size** (offered to the owner with their measured share,
  not chosen): xz compression (−20 % more, unpacking twice as slow),
  downloading Wine Mono/Gecko on first use (184 MB; .NET programs would
  need the internet once), dropping translations other than English and
  Turkish (88 MB), and anything under 2 GB, which would need removing a
  feature (32-bit Windows programs need Wine's i386 stack: Debian 13's
  Wine is not a WoW64 build; or Office/Mail). The initrd's 137 MB is
  mostly AMD and NVIDIA firmware the kernel needs before the root
  filesystem is mounted; leaving it out risks a black screen on those
  GPUs.

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
