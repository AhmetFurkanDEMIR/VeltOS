# Development Log

Newest entries first. Record what was done, what was verified and what
went wrong, so the next person can trust the state of the repository.

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
