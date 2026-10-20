# Development Log

Newest entries first. Record what was done, what was verified and what
went wrong, so the next person can trust the state of the repository.

## 2026-10-20 (night) — ISO with all of today's work; Konqueror out

- ISO `veltos-0.1.0-dev-20261019-222530` (everything up to the Task
  Manager): verify hook passed; boot tests UEFI PASS (16 checks) and BIOS
  PASS (15), no crashed processes. Its live session showed Konqueror as
  the first pinned app in Start: `preferred://browser` fell back to it
  because Debian's KDE defaults name Falkon (not installed), and
  Konqueror (recommended by kde-baseapps) also preloads itself at every
  sign-in (it showed in Task Manager's Startup apps).
- Fix: Konqueror pinned out of the image (verify hook checks it) and
  `BrowserApplication=firefox-esr.desktop` in kdeglobals.
- The ISO with this fix (20261020-021732) passed the verify hook (no
  Konqueror), but copying it to `out/` failed: the host's C: drive was
  full (325 MB free; eight 3.5 GB ISOs in `out/iso`). Superseded ISO
  outputs were deleted (kept: 20261019-174700, used for the encrypted
  install test, and 20261019-222530, the latest tested one); 22 GB free
  again. Docker Desktop stopped answering after the disk had been full
  and needs a restart; the fix is therefore **not yet in a built ISO**.
  Keep `out/iso` small (`build/run.sh clean` or delete old builds).


## 2026-10-20 (evening) — VeltOS Task Manager

New package `veltos-taskmanager` (PySide6/QML, psutil 7.0.0 from Debian):
Processes, Performance and Startup apps in the Windows 11 layout,
Ctrl+Shift+Esc (`X-KDE-Shortcuts`), one instance per user (local socket).
KDE's System Monitor is renamed "Resource Monitor"; Start pins Task
Manager. Verified in the VM: Ctrl+Shift+Esc opens it; Firefox shows as one
app with its 11 processes; Performance shows the CPU graph and figures;
Startup apps lists the autostart entries; a second Ctrl+Shift+Esc does not
start a second copy.

Problems: the kernel cuts process names to 15 characters
("veltos-taskman"), so apps are matched by their command line; a process
list replaced every second would lose scroll position and hover, so rows
are updated in place (`model.py`); `data` is a reserved QML property name.
While testing, `kbuildsycoca6` run without `XDG_MENU_PREFIX=plasma-` emptied
the application database (taskbar showed "?" icons) until it was rebuilt
with the session's variables; and one `vm upload` did not replace the
package in the VM - check the installed files after `dpkg -i`.

## 2026-10-20 (later) — Task View, sounds, animations, toasts

- **Task View** like Windows 11 as a KWin QML scene effect
  (`veltostaskview`, public `org.kde.kwin` API only): window thumbnails
  with icon/title/close, desktops strip with "New desktop" and remove,
  Meta+Tab and the taskbar button. Verified in the VM: opens with
  Meta+Tab, hover/close, switching to a second desktop ("No open
  windows"), creating and removing a desktop; helper windows that skip
  the window switcher are left out (the Wayland recording bridge showed).
  KWin keeps a loaded effect's QML: re-login after changing it.
- **No animations in VMs**: KWin had loaded none of its animation effects
  (scale, squash, slidingpopups, slide, maximize...) because it renders
  with llvmpipe. `KWIN_EFFECTS_FORCE_ANIMATIONS=1` in the session script
  (KWin reads it; verified that all of them load after re-login). CPU is
  used only while an animation runs; not measured on real hardware yet.
- **Sounds**: original VeltOS sound theme synthesised at build time
  (`tools/sounds.py`; Windows' sounds are Microsoft's and not shipped),
  login chime enabled. Not listened to (the VM has no audio output).
- **Toasts**: no timeout bar, monochrome close glyph (second
  `update-plasma-overrides` spec). Verified with two test notifications.
- ISO `veltos-0.1.0-dev-20261019-215605` (first part of the day): verify
  hook passed incl. the override check; boot tests not run yet.

## 2026-10-20 — Windows 11 polish: start-up, flyouts, Firefox, File Explorer fix

### Product-owner feedback that drove this work

Dark mode left the taskbar light; an app icon bounced under the pointer
while programs started; "use Windows 11 pointers"; Firefox and other
programs still had "Debian" minimise/close buttons; the status and
notification area and Start should be exactly Windows 11; File Explorer
"does not open any more, shows an error"; broken Turkish text in Settings
(Apps > Windows programs); garbled taskbar window previews; a flat-line
loading screen; text scrolling at start-up; the shutdown menu of the power
key looked like Debian; the on-screen keyboard covered the sign-in screen;
This PC and Recycle Bin on the desktop; File Explorer and Settings icons;
plus larger requests (Task View, Task Manager, Control Panel, animations
and sounds, Wine dialogs, Store) that are not done yet (see status).

### Causes found and fixes

- **File Explorer did not start on Turkish systems**:
  `QTimer(self, singleShot=True, interval=250)` - PySide6 maps keyword
  arguments to setters with the C `toupper()`, which turns `interval` into
  `setİnterval` in a Turkish locale (reproduced in the VM with
  `setlocale(tr_TR.UTF-8)`). Setters now; a repository test rejects the
  pattern; the builder image has `tr_TR.UTF-8` and the Turkish test classes
  of File Explorer and Settings run in it.
- **Broken Turkish text** ("kal dır", "program lar"): Qt Quick's
  distance-field text at the VM's 105 % scale; offscreen renders were fine
  in every locale. All VeltOS QML programs now use native text rendering.
- **Dark taskbar**: the global theme writes `kdedefaults/plasmarc`, the
  taskbar watches the user's `plasmarc` file only, and `kwriteconfig6` did
  not write a value equal to the kdedefaults one; a KConfig change signal
  sent by hand did not help either. Settings now edits the file directly
  (verified: taskbar dark at once on a first switch).
- **Firefox buttons**: Firefox draws its own round libadwaita-style buttons
  and ignores GTK themes (hover showed pink/white circles). An autoconfig
  style sheet gives them the VeltOS 46 x 32 buttons and red close
  (verified on hover). KDE's GTK module produced empty button images for
  our Aurorae frames, so a VeltOS GTK theme (Breeze + our buttons) covers
  other GTK programs.
- **Launch icon at the pointer**: KWin's startup feedback; it never shows a
  busy pointer on Wayland, so it is off. **Pointers**: Debian's default
  `x-cursor-theme` was Adwaita; Fluent cursors are now the default.
- **Sign-in keyboard**: SDDM's default `InputMethod=qtvirtualkeyboard`.
- **Previews**: KWin renders with llvmpipe in the VM and its captures are
  garbled; with software rendering the taskbar shows titles only
  (`session-fixups`, autostart one-shot).
- New: Windows-like "Welcome" splash (blurred sign-in wallpaper, dot
  spinner) instead of the progress line; VeltOS power screen
  (`Logout.qml`); flyouts float with rounded corners
  (`ContainmentPrefersFloatingApplets` kept set by our plasmoids); Start
  (pill search box, Windows buttons, one-line labels, neutral avatar,
  "More" page, File Explorer pinned); clock flyout = notification centre +
  Windows calendar; hidden-icons flyout with icons only through the new
  `update-plasma-overrides` mechanism (architecture 2.3.8); This PC and
  Recycle Bin desktop icons that come back; new File Explorer and Settings
  icons; quiet kernel/systemd options; `xwaylandvideobridge` kept out of
  the image.

### Verified (installed encrypted VM, packages installed with dpkg)

Sign-in without on-screen keyboard -> Welcome splash -> desktop with the
two icons; Start, Quick Settings, clock and hidden-icons flyouts floating;
power screen; notification centre with two test notifications; Firefox
buttons and hover states; File Explorer running in a Turkish locale;
Settings Windows-programs page in Turkish; dark taskbar on a first switch;
`x-cursor-theme`, SDDM, klaunchrc, grub.cfg options in place. Package
tests: veltos-desktop 53, veltos-explorer 31, veltos-settings 57,
veltos-boot 22, calamares-settings-veltos 19, veltos-winapps 20, repo 6.

Not yet: a new ISO with all of this; on-screen check of the quiet start-up
and shutdown; the pointer theme in X11 programs.

### Problems hit

- A new Settings test shifted test order and exposed a teardown bug: a QML
  engine deleted later printed "backend is null" into the next test. The
  engine is now destroyed in `tearDown`.
- Git Bash heredocs turned `\n` in Python sources into real newlines
  several times; such edits are done with the editor tools now.

## 2026-10-19 (night) — Encrypted installation verified, unlock screen like Windows

### Installation test on the fixed ISO

ISO `veltos-0.1.0-dev-20261019-170820`, VM (UEFI), "Erase disk" +
"Encrypt system": Calamares finished; firmware entry `Boot0009* VeltOS`;
`grub.cfg` has the "VeltOS" entries again; booting the disk shows the
password box on the VeltOS boot screen, the correct password leads to
the sign-in screen and the desktop. The three bugs of the previous test
are fixed. Evidence: `tests/results/2026-10-19-encrypted-install-uefi/`.

### Problems seen on the password screen (fixed)

- The prompt read "Please unlock disk luks-<uuid>:" (cryptsetup's text,
  with Calamares' mapping name) in a **monospace** font, and the box, the
  text and the keyboard indicator were drawn over the logo.
  - Font: Debian's plymouth initramfs hook copies only fontconfig's default
    and monospace fonts; the theme asked for Cantarell, which was not in
    the initramfs, and fontconfig chose DejaVu Sans Mono. veltos-boot now
    has an initramfs hook that copies Inter; the theme uses Inter.
  - Texts: the hook changes the initramfs copy of cryptsetup's shell
    functions (`/usr/lib/veltos-boot/unlock-texts`): "Enter the password
    to unlock this PC", after a wrong password "The password is incorrect.
    Try again.", no technical splash messages for a wrong password or a
    successful unlock. A first version showed the warning as a Plymouth
    message; it stayed on screen while the next (correct) password was
    being checked, so the warning now replaces the prompt.
  - Layout: `DialogVerticalAlignment=.6` (below the logo; unit test checks
    600-2160 px screen heights).
- After three wrong passwords cryptsetup gives up and the system falls to
  a recovery shell. Calamares' fstab module drops `crypttabOptions` when
  `/boot` is unencrypted, so a new installer job `crypttab-tries` adds
  `tries=0` (unlimited, crypttab(5)) to entries with a typed password.
- Lintian: `repeated-trigger-name update-initramfs` — `dh_installinitramfs`
  adds the trigger for the new hook; veltos-boot's own `.triggers` file
  was removed.

Verified in the installed VM with the new packages (`dpkg -i`, installer
job run by hand): Inter and the new texts in the initramfs (`lsinitramfs`,
`unmkinitramfs`); prompt below the logo; four wrong passwords in a row
without a recovery shell; correct password -> spinner without messages ->
sign-in screen.

### ISO `veltos-0.1.0-dev-20261019-174700`

- Verify hook passed (new checks: Inter in the live initramfs, installer
  runs `crypttab-tries`, initramfs hook installed).
- Boot tests: UEFI PASS, BIOS PASS (all checks, no crashed processes).
- **Encrypted installation repeated on this ISO**: Calamares ran
  `crypttab-tries` (crypttab `... none tries=0`), "All done"; boot: prompt
  -> wrong password -> "The password is incorrect. Try again." -> correct
  password -> sign-in screen; no failed systemd units.
- Package tests: veltos-boot 22 (was 14), calamares-settings-veltos 19
  (was 17), repo 4.
- Not tested on this ISO: a plain (unencrypted) installation, Secure Boot,
  `test-winapps`, BIOS installation.

### Seen during the installation, not changed yet

- The installer's partition and user pages still use Calamares' own
  icons and layout (only colours and controls are styled).
- Calamares' confirmation dialog has minimise/maximise buttons.
- The keyboard indicator on the password screen ("us") is Plymouth's
  pre-rendered image (bold, not Inter).

## 2026-10-19 (evening) — File Explorer, Settings pages, taskbar, installer, encryption fix

### Product-owner feedback that drove this work

- VirtualBox stopped the installed system at start-up (fixed: GRUB video
  mode, commit 8d06195). Later: an install with "Encrypt system" ended in
  `grub rescue` after the GRUB password prompt.
- "Settings, files, app windows — everything Windows 11", "the taskbar more
  like Windows, translucent", "the installer looks like old Qt", "logo like
  my sketch (V of two bars)", "no Debian anywhere", "File Explorer exactly
  like Windows 11" (with screenshots), "dark mode leaves the taskbar
  white", "show desktop at the bottom right", "Control Panel inside
  Settings", "every window's close/minimise buttons like Windows 11",
  dialogs and confirmations Windows 11 style.
- Asked to ship Windows 11's own wallpapers: declined (Microsoft's
  copyright; an ISO with them could not be shared); original artwork kept.

### Implemented

- **VeltOS File Explorer** (new package `veltos-explorer`): see its README.
  Replaces Dolphin as the default for folders and on the taskbar.
- **Settings**: built-in Wi-Fi, Bluetooth, Sound, Display, Background,
  Colours, Date & time pages (`devices.py` + QML pages, Windows 11 toggles,
  sliders, drop-downs); About shows "OS build" (from
  `/usr/lib/veltos/build-info`, written by the ISO build) instead of the
  kernel; separate Control Panel entry removed; light/dark switch now
  updates the taskbar at once.
- **Taskbar**: 48 px, see-through (opacity in the Plasma theme, translucent
  panel mode, acrylic-like blur where available); Search box, Task View,
  new clock (time over date, same size, four-digit year, calendar),
  show-desktop corner.
- **Window frames**: VeltOS-drawn caption buttons in Windows 11 metrics
  (46×32, thin glyphs, grey hover, red close with the rounded corner),
  32 px title bar, left title with app icon.
- **Logo**: new "V" of two slanted bars (product owner's sketch) in every
  package; wallpaper without logo or text.
- **Installer**: QML side bar with steps and check marks, Back / accent
  Next / Cancel, style sheet for all controls, Kvantum style for its
  dialogs (root).
- **Yellow folders** like Windows 11; coloured place icons at small sizes.
- **No Debian in sight**: console banner, GRUB kernel titles, About page,
  KDE "About this System" page hidden; `systemd-timesyncd` added for
  automatic time.
- **Encryption fix**: `partition.conf` with an unencrypted `/boot`
  (`noEncrypt`), `cryptsetup-initramfs` and `console-setup` in the image,
  `KEYMAP=y` in the initramfs. Before, `/boot` was inside LUKS (GRUB text
  prompt, one try, US keyboard) and the initramfs could not unlock the
  system at all.

### Problems hit (and fixed)

- File Explorer crashed when started from the taskbar but not from the
  test tools: Qt's QML disk cache kept compiled QML of the previous package
  (all packaged files share one time stamp). QML disk cache is now off in
  every VeltOS QML app.
- File Explorer and its tests crashed at exit (QMimeData on the
  clipboard deleted after Python shut down).
- Kirigami found no icons with the "Basic" Qt Quick style outside Plasma.
- Plasma ignored the theme change written to `kdedefaults` until the next
  sign-in.
- Settings' first Wi-Fi code (`nmcli … passwd-file`) made NetworkManager
  ask password agents, which opened the "KDE Wallet" wizard; replaced by
  D-Bus `AddAndActivateConnection` with the key. NetworkManager passes
  `need-auth` once even with a key; a wrong key is detected by the state
  reason.
- Shell heredocs turned `\b` and `\1` into control characters in Python
  sources twice; `tests/repo` now rejects control characters.

### Test runs

- ISO `veltos-0.1.0-dev-20261019-125115`: boot tests UEFI and BIOS PASS
  (16 checks each, no crashed processes), with File Explorer as launcher
  and Dolphin/System Settings hidden.
- Package tests: veltos-desktop 47, veltos-explorer 30, veltos-settings 55,
  veltos-boot 14, calamares-settings-veltos 15, veltos-base 6,
  veltos-winapps 20, tests/repo 4.
- The encryption fix and the new caption buttons are in the next ISO; see
  below.

### Installation test (VM, UEFI, "Erase disk" + "Encrypt system")

First installation test in a VM since the VirtualBox fix. Calamares
finished ("All done"): EFI 300 MiB, `/boot` 1 GiB ext4 unencrypted,
system 38.7 GiB LUKS1; crypttab asks at start-up (`none`), the initramfs
has cryptsetup, the keymap and the boot screen's password box; Calamares
skipped the keyfile because `/boot` is unencrypted. **The installed system
did not start**: the firmware went to its setup page. Causes found:

1. `/boot/grub/grub.cfg` had **no VeltOS entry**. In the image build
   grub-common was unpacked before veltos-boot's preinst diverted
   `/etc/grub.d/10_linux`, so dpkg left Debian's script as
   `10_linux.dpkg-new` and the VeltOS wrapper found nothing to run (it
   exited 0 silently). Every installation since commit 8d06195 was
   affected. Fixed: veltos-boot `Pre-Depends: grub-common`, the postinst
   repairs the stale file, the wrapper now fails update-grub (and the
   installer) when Debian's script is missing, the verify hook checks it.
2. The firmware entry was still called "debian": a shell quoting accident
   had collapsed the doubled backslashes of the `efi-label` helper's grep
   pattern for the `\EFI\debian\` path into single ones, so its grep failed. Fixed with `grep -F`; the helper now has a test
   with fake efibootmgr output.
3. `hwclock` is in `util-linux-extra` in Debian 13; added to the image.

The fixed ISO is tested in the next entry.

## 2026-10-19 (later) — Windows 11 look, Settings app, start-up like Windows

### Product-owner feedback that drove this work

- "The Windows program runner does not work" (fixed earlier the same day,
  commit 65b676c) and "the interface is very bad": files, settings, menus,
  search must be redone, simple, light, like Windows 11; the ISO start-up
  looks bad; it must not be recognisable as Debian.
- After a first round: "still not good"; the clock/date is far too big;
  remove the "Türkçe" boot menu entry; it must not look like Linux at all.

### Implemented

- **Windows 11 look from Fluent-kde** (pinned commit 44794f29c89d,
  SHA-256 checked, `veltos-desktop/tools/fluent.py`): Kvantum application
  style, Aurorae window frames (minimise/maximise/close on the right, app
  icon and left-aligned title), Plasma theme, colour schemes; Windows blue
  replaced by the VeltOS accent; Windows/Manjaro/KDE logos removed.
  Problems found in VM screenshots and fixed: 75 % opaque frames (need
  blur) made title bars and inactive windows see-through → solid variant;
  1 px seam under every window → `BorderBottom=1`; Fluent Light's
  translucent highlight made Kirigami apps use Qt's default blue → accent;
  translucent popups unreadable without blur → opaque unless blur exists.
- **Windows-familiar names** in Start/search (`update-app-names`, dpkg
  trigger, overrides in `/var/lib/veltos/xdg`) and **inside the programs**
  (pseudo-language catalogs `en@veltos`/`tr@veltos`): "Home — File
  Explorer". KDE System Settings is "Control Panel". Developer/KDE extras
  hidden from Start; KDE-only Settings pages hidden (kiosk).
- **VeltOS Settings** (new package `veltos-settings`): Windows 11 layout,
  Home, theme, About/rename PC, Storage, Windows programs, search, EN/TR;
  other settings open KDE's modules.
- **File Explorer**: Windows-like side bar, icon-only toolbar, zip as
  folders, no Templates/Public folders.
- **Taskbar**: Windows-sized two-line clock, tray reduced to network,
  sound, battery, notifications (rest behind "^"), pins File Explorer,
  Firefox, Settings; no show-desktop button; shut down/restart without a
  confirmation screen.
- **Start-up**: hidden boot menu (Esc/F4), boot text invisible, beep
  removed, Inter fonts and rounded highlight when the menu is shown, no
  Turkish entry. **Plymouth splash now actually shows** (see problems).
  SDDM waits for Plymouth.
- **Sign-in screen**: new SDDM theme in Windows 11 layout (time/date →
  picture, name, password; power menu), Inter font, tested offscreen.
- **Live system**: welcome window (Try / Install, English / Türkçe switch
  with automatic re-sign-in), no screen lock/sleep, Turkish locale and
  Firefox Turkish language pack in the image.

### Problems hit (and fixed)

- The VeltOS boot splash had never been shown: Debian's
  `plymouthd.defaults` names a theme that is not installed, so every
  initramfs had only the text splash; after diverting it, the two-step
  plugin still failed because `lock.png` was a symlink into a theme not in
  the initramfs. Found with `plymouth.debug`; images are now copies and
  the verify hook checks the initramfs.
- GRUB fell back to the firmware text console ("glyphs too large to fit on
  screen") because the Inter fonts were loaded before gfxterm started.
- GRUB highlight boxes overlapped the next entry (border slices are drawn
  outside the item) and the countdown bar was a text line tall (any
  `text` property).
- `qt-style-kvantum` has no system-wide theme setting; Lintian rejects
  files in `/etc/skel` → Plasma session script.
- Heredocs in the agent's shell collapse `\\`; several edits had to be
  redone with the file editor (environment quirk, recorded in memory).

### Latest test runs

ISO `veltos-0.1.0-dev-20261019-064631` (verify hook passed):

- UEFI boot test `20261019-065930-uefi`: all 16 checks pass (incl. VeltOS
  Plymouth theme in the initramfs, welcome window, application names,
  per-user defaults, no crashed processes). Screenshots: hidden boot menu
  revealed with F4 (themed, three entries), VeltOS boot splash, desktop
  with welcome window, Start menu.
- BIOS boot test `20261019-070134-bios`: all checks pass.
- Measurements (UEFI, 4 vCPU, 4 GiB, no 3D): systemd-analyze 7.9 s;
  plasmashell running 19.1 s after VM start (the boot menu no longer
  waits); idle used RAM 1691 MiB (baseline 1696 MiB). Largest optional
  processes: Discover notifier 254 MiB RSS, xwaylandvideobridge 151 MiB,
  kdeconnectd 148 MiB, kaccess 133 MiB — candidates for the next
  lightweight pass.
- In the live VM (packages installed on the previous ISO): Settings app
  pages, "Home — File Explorer" / "Welcome — Text Editor" titles, the
  sign-in screen in `sddm-greeter-qt6 --test-mode` (lock view and sign-in
  view).
- Not run: Secure Boot test, Calamares installation, `test-winapps` on
  this ISO; nothing on real hardware.

## 2026-10-19 — "VeltOS everywhere", Windows 11 UI, Windows programs

### Product-owner feedback that drove this work

- After installing the first ISO: "it is just Debian". Nothing may mention
  Debian; installer, boot, menus, settings must all be VeltOS.
- Interface quality like Windows 11: simple icons, a real Start menu,
  soft visuals (a reference image: sky, misty lake, blue ribbon bloom,
  two-blade "V" logo).
- Double-click `.exe` support; automatic hardware support; the audience is
  Windows users and gamers who should not have to learn anything.

### Implemented

- **VeltOS Start** (`org.veltos.startmenu`): Windows 11 style launcher on
  Plasma's kicker models; English/Turkish. Verified in VM: open with Meta,
  pinned grid, All apps, search, context menu.
- **Crash found and fixed**: plasmashell segfaulted at login with the new
  menu. `coredumpctl` + Debian debug symbols located it in Plasma 6.3's
  `SystemModel::refresh()` (null `favoritesModel`); the menu now creates
  that model only after the root model is populated. Boot tests now fail
  on any core dump.
- **Fluent icons/cursors** (`veltos-fluent-icons`) from a pinned,
  checksum-verified release; found that upstream draws `start-here*` and
  Wine icons as Microsoft's Windows logo → replaced with the VeltOS logo /
  removed. Inter as UI font.
- **New visual identity**: two-blade "V" logo; procedurally generated
  "Velt Bloom" wallpaper (sky, sunrise glow, misty hills, lake, layered
  blue petals with radial shading and soft shadows, logo + name); light
  and dark variants. VeltOS Light is now the default theme.
- **VeltOS installer** (`calamares-settings-veltos`), **boot splash and
  GRUB theme** (`veltos-boot`); KDE Welcome Center removed from the image.
- **Windows programs**: `veltos-winapps` (`veltos-run`, default handler
  for `.exe`/`.msi`), `veltos-wine-addons` (Wine Mono 9.4.0 / Gecko 2.47.4,
  SHA-256 pinned to the values in Wine's source), Wine 10 with 32-bit
  support and DXVK in the image.
- Firmware: explicit redistributable list instead of live-build's
  automatic one, which had built non-redistributable Broadcom firmware
  downloads (`firmware-b43*-installer`) into the earlier ISOs. Those ISOs
  were only used for local testing.
- Tooling: `build/run.sh preview` (install fresh packages into a live VM
  and screenshot a scripted interaction), `build/run.sh test-winapps`,
  `fetch-upstream.py` (pinned + verified third-party downloads),
  repository consistency tests (logo copies, CRLF).

### Problems hit (and fixed)

- CRLF files written by Python on Windows broke `debian/rules`.
- `dh_auto_test` runs before `dh_auto_install` (checks moved).
- Debian version ordering with `~` (`10.0~repack-6` < `10.0`).
- `.list.binary` needs `apt-utils` on the build host, and BIOS/UEFI GRUB
  packages must be in separate lists (they conflict).

## 2026-10-18 — Milestones 0 and 1 started

### Environment inspection (developer host)

- Host: Windows 11 Pro, Intel Core i7-13620H (10C/16T), 32 GB RAM,
  NVIDIA RTX 4070 Laptop + Intel UHD Graphics. No native Linux, QEMU or
  WSL distribution; Docker Desktop 28.3.3 (WSL2 backend) installed.
- Privileged Debian trixie containers work → live-build can run in Docker.
- `/dev/kvm` was absent in containers. The WSL2 kernel
  (6.6.87.2-microsoft-standard-WSL2) has `CONFIG_KVM_INTEL=m` and the module
  file exists; `modprobe kvm_intel` in Docker's VM (via `nsenter -t 1`)
  made `/dev/kvm` available with `nested=Y`. Automated in `build/run.sh test`.

### Upstream facts verified (packages.debian.org / tracker.debian.org)

- Debian 13 trixie is stable; latest point release 13.7 (2026-09-12).
- trixie versions: live-build 1:20250505+deb13u1, linux-image-amd64
  6.12.113-1 (backports 7.2.6), plasma-desktop 4:6.3.6-1, Mesa 25.0.7
  (backports 26.1.6), Wine 10.0~repack-6, Calamares 3.3.14-1,
  nvidia-graphics-drivers 550.163.01-2, QEMU 10.0.13, OVMF 2025.02.
- live-build in trixie: default BIOS loader is isolinux unless dracut is
  used; GRUB templates in `/usr/share/live/build/bootloaders/grub-pc` serve
  both BIOS and UEFI and can be overridden file by file; no menu timeout in
  the template; splash.svg is rendered at 800x600 for GRUB.
- live-config 11.0.5 has an SDDM component that writes autologin for the
  live user and picks the `plasma.desktop` (Wayland) session.
- Debian's `desktop-base` (Debian artwork, owns `/etc/xdg/kcm-about-distrorc`)
  is pulled only through sddm's Recommends on `sddm-theme-debian-breeze`.
  `/etc/xdg/kdeglobals` and `/etc/xdg/kscreenlockerrc` are not owned by any
  trixie package (apt-file), so `veltos-desktop` can ship them.
- Breeze colour schemes live in `kde-style-breeze-data`.

### Decisions

Recorded with trade-offs in `docs/architecture.md`: Debian 13 stable base,
Debian kernel, Plasma 6.3 customised via packages (no fork), GRUB for BIOS
and UEFI, Secure Boot via Debian shim, zstd squashfs, NVIDIA proprietary
driver not preinstalled (Hardware Manager will handle it), Calamares with
Debian settings as a stopgap, container-only builds.

### Implemented

- Repository skeleton, `.gitattributes` (LF), GPL-3 `LICENSE`.
- `build/builder/Dockerfile` (trixie pinned by digest), `build/run.sh`,
  `build/scripts/build-packages.sh`, `build/scripts/build-iso.sh`.
- `packages/veltos-base`: os-release via dpkg diversion; 4 unit tests.
- `packages/veltos-desktop`: global themes, centered taskbar layout
  script, Breeze-derived colour schemes, Velt Bloom wallpaper (light/dark,
  7 sizes), splash, SDDM/lock screen branding, logo; 9 unit tests.
- live-build configuration, branded GRUB menu + splash, verification hook.
- `tests/boot/vmtest.py` VM boot test.

### Product-owner feedback applied

- Wallpaper redesigned to follow the Windows 11 "Bloom" style (translucent
  folded petals, soft shadows, light and dark variants) while forming the
  VeltOS "V"; the logo now uses the same petals.
- All repository content in English; READMEs and `AGENTS.md` describe rules
  and status so other people and AI agents can continue the work.

### Problems hit and fixed

- `dpkg-checkbuilddeps` prints "unmet" in lower case; the build-deps parser
  expected "Unmet". Fixed, and `build-essential` added to the builder image.
- Files from the Windows bind mount appear executable; debhelper then
  executed `debian/veltos-base.install` as a dh-exec script. Build scripts
  now normalise file modes.
- `docker build` received a Git Bash `/c/...` path; `run.sh` now passes the
  Windows-style path from `pwd -W`.
- Rewriting the wallpaper's root `<svg>` tag dropped the `xlink` namespace;
  the script now edits only width/height/viewBox (covered by a unit test).

### Verified so far

- `build/run.sh packages`: both packages build; 13 unit tests pass.

### First ISO build and UEFI boot test

- First `build/run.sh iso` succeeded in ~10 min (cold cache):
  `veltos-0.1.0-dev-amd64.hybrid.iso`, 2,607,017,984 bytes. The verify hook
  passed.
- UEFI boot test: system up in 16 s (guest agent), Plasma Wayland session
  in 25 s, no failed units, centered taskbar + VeltOS start button +
  wallpaper confirmed in the screenshot and in the Plasma config.
- **Failure found:** the booted system's `/etc/os-release` said Debian
  (`IMAGE_ID=live`). Cause: live-build's `bootstrap_debootstrap` replaces the
  `/etc/os-release` symlink with a copy of Debian's file. The build hook only
  checked `/usr/lib/os-release`, so it passed. Visible effects: boot menu
  footer "VeltOS 13", KDE Welcome Center "Welcome to Debian". Would also
  have affected installed systems.
- Fix: hook `8000-veltos-os-release.hook.chroot` restores the symlink; the
  verify hook now checks both paths. Rebuilt and retested (next entry).
- Other observations from the first run (not fixed yet): "Install Debian"
  desktop icon from calamares-settings-debian; KDE Welcome Center opens on
  live login; live-session idle RAM 1709 MiB with Welcome Center (333 MiB),
  Discover notifier (241 MiB), KDE Connect (145 MiB) as the largest optional
  consumers.
