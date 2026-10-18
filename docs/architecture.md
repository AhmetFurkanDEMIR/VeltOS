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
  - colour schemes derived from Breeze at package build time (only the accent
    colours change, so Breeze fixes flow in on rebuild);
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
  pages; a VeltOS welcome app is planned).
- The layout only applies to users who start Plasma for the first time; it
  never rewrites existing users' configuration.
- Session: Wayland (Plasma 6 default). X11 session (`kwin-x11`) is installed
  via Recommends as a fallback.
- Revisit: replacing more stock Plasma UI (System Settings, notifications)
  only where it blocks the "familiar for Windows users" goal.

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
  - `os-prober` is enabled so Windows stays bootable in dual-boot setups.
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
