# build/

Everything needed to turn this repository into a VeltOS ISO. All work runs
in the builder container; the host needs only Docker and bash.

| Path | Purpose |
|---|---|
| `run.sh` | The single entry point: `image`, `packages [name...]`, `iso`, `test [uefi\|bios\|secureboot]`, `test-winapps`, `preview`, `vm`, `shell`, `clean`. |
| `builder/Dockerfile` | Debian trixie image (pinned by digest) with live-build, debhelper, lintian, librsvg, QEMU/OVMF, Python with Pillow, and the Turkish locale for the package tests. Each package's build dependencies (PySide6 and so on) are installed when it builds. |
| `scripts/build-packages.sh` | Builds the packages in `packages/` with `dpkg-buildpackage` (unit tests included), runs lintian and the repository checks, and copies the `.deb` files to `out/packages/` only when every named package built. |
| `scripts/build-iso.sh` | Prepares the live-build tree in the `veltos-build` Docker volume, adds the fresh `.deb` files, runs `lb config` and `lb build`, and collects the outputs in `out/iso/`. |
| `scripts/fetch-upstream.py` | Downloads third-party sources pinned in a package's `upstream.json` and checks their SHA-256. |
| `scripts/plain-png.py` | Rewrites PNG pictures unfiltered and uncompressed, the form GRUB always reads. |
| `live-build/` | The live-build configuration (below). |

## live-build configuration

| File | What it controls |
|---|---|
| `live-build/auto/config` | All `lb config` options: trixie/amd64, archive areas, GRUB for BIOS and UEFI, Secure Boot, firmware, SquashFS with zstd level 19, ISO label, live boot options (user `velt`, hostname `veltos`, the live-config components a VeltOS session does not need), mirrors. |
| `live-build/auto/clean` | `lb clean` wrapper. |
| `live-build/config/package-lists/*.list.chroot` | Packages in the image: `veltos-desktop` (Plasma and apps), `veltos-hardware` (diagnostics, Mesa, microcode), `veltos-firmware` (redistributable device firmware), `veltos-system` (identity, boot splash, installer, guest agent), `veltos-windows` (Windows program support: veltos-winapps, Wine 64/32-bit, DXVK, Mono/Gecko). |
| `live-build/config/package-lists/veltos-installer-{uefi,bios}.list.binary` | Bootloader packages in the ISO's package pool for offline installations (two lists because `grub-pc` conflicts with `grub-efi-amd64`). |
| `live-build/config/archives/veltos-no-debian-branding.pref.chroot` | APT pins keeping third-party branding (`desktop-base`, `calamares-settings-debian`, `plasma-welcome`) and firmware downloaders (`firmware-b43*-installer`) out. |
| `live-build/config/archives/veltos-lean.pref.chroot` | APT pins keeping out packages that only recommendations bring in and no VeltOS feature uses (extra Noto weights, Marvell switch firmware, an English speech model, Plasma Vault). |
| `live-build/config/includes.chroot_before_packages/etc/dpkg/dpkg.cfg.d/veltos-lean` | dpkg leaves out package changelogs (the copyright files stay) and KDE's unused "Next" wallpaper. |
| `live-build/config/includes.chroot_after_packages/` | AppArmor's kernel feature set, so the profile cache is compiled at build time. |
| `live-build/config/rootfs/excludes` | Files kept out of the SquashFS: the initramfs copy (the installer makes the installed system's own) and apt's package caches. |
| `live-build/config/hooks/normal/0500-veltos-locales.hook.chroot` | Compiles the English and Turkish locales. |
| `live-build/config/hooks/normal/8000-veltos-os-release.hook.chroot` | Restores `/etc/os-release` as a link to VeltOS' `/usr/lib/os-release` (live-build replaces it with a Debian copy). |
| `live-build/config/hooks/normal/8500-veltos-apparmor-cache.hook.chroot` | Compiles the AppArmor profile cache (11 s less at every start). |
| `live-build/config/hooks/normal/8900-veltos-update-done.hook.chroot` | Marks `/etc` and `/var` as updated, so systemd's update services do not run at every live start. |
| `live-build/config/hooks/normal/9000-veltos-verify.hook.chroot` | Fails the build if a VeltOS invariant is broken: required packages, no third-party branding or firmware downloaders, identity, default theme, Start menu, Plymouth theme, installer branding, file associations, Wine Mono, stripped Wine libraries, the lean package set, no menu launcher mentioning Debian. |
| `live-build/config/hooks/normal/9100-veltos-grub-png.hook.binary` | Rewrites the live boot menu's pictures in the form GRUB always reads. |
| `live-build/config/bootloaders/splash.svg` | Boot menu background (rendered by live-build). |
| `live-build/config/bootloaders/grub-pc/grub.cfg` | Boot menu entries (start, basic graphics, advanced options), hidden with a 2 s timeout like Windows; Esc shows the menu. Used for BIOS and UEFI. |
| `live-build/config/bootloaders/grub-pc/config.cfg` | Boot menu graphics and fonts (live-build's default without its start-up beep). |
| `live-build/config/bootloaders/grub-pc/live-theme/` | GRUB menu theme (positions, colours, fonts). |

Only files that differ from live-build's templates are kept here; live-build
copies its defaults first and overlays these.

Full instructions: [docs/dev/build-guide.md](../docs/dev/build-guide.md).
