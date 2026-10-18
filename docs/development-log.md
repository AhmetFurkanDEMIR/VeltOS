# Development Log

Newest entries first. Record what was done, what was verified and what
went wrong, so the next person can trust the state of the repository.

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
