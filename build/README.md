# build/

Everything needed to turn this repository into a VeltOS ISO.

| Path | Purpose |
|---|---|
| `run.sh` | Entry point (`image`, `packages`, `iso`, `test`, `shell`, `clean`). Runs all work in the builder container. |
| `builder/Dockerfile` | Debian trixie image (pinned by digest) with live-build, debhelper, librsvg, QEMU/OVMF and Python. |
| `scripts/build-packages.sh` | Builds every package in `packages/` with `dpkg-buildpackage` (unit tests included) and runs lintian. |
| `scripts/build-iso.sh` | Prepares the live-build tree in the `veltos-build` Docker volume, injects the fresh `.deb`s, runs `lb config` + `lb build`, collects outputs in `out/iso/`. |
| `live-build/` | The live-build configuration (see below). |

## live-build configuration

| File | What it controls |
|---|---|
| `live-build/auto/config` | All `lb config` options: trixie/amd64, archive areas, GRUB for BIOS+UEFI, Secure Boot, firmware, zstd squashfs, ISO label, live boot parameters (user `velt`, hostname `veltos`), mirrors. |
| `live-build/auto/clean` | `lb clean` wrapper. |
| `live-build/config/package-lists/*.list.chroot` | Packages in the image: `veltos-desktop` (Plasma + apps), `veltos-hardware` (diagnostics, Mesa, microcode), `veltos-system` (identity, Calamares, locales, guest agent). |
| `live-build/config/archives/veltos-no-debian-branding.pref.chroot` | APT pin keeping Debian's `desktop-base` artwork out. |
| `live-build/config/hooks/normal/8000-veltos-os-release.hook.chroot` | Restores `/etc/os-release` as a symlink to VeltOS' `/usr/lib/os-release` (live-build replaces it with a Debian copy). |
| `live-build/config/hooks/normal/9000-veltos-verify.hook.chroot` | Fails the build if VeltOS identity/branding invariants are broken. |
| `live-build/config/bootloaders/splash.svg` | Boot menu background (rendered to 800x600 by live-build). |
| `live-build/config/bootloaders/grub-pc/grub.cfg` | Boot menu entries (default, Turkish, safe graphics, utilities) with a 10 s timeout. Used for BIOS and UEFI. |
| `live-build/config/bootloaders/grub-pc/live-theme/theme.txt` | GRUB menu theme (positions, colours). |

Only files that differ from live-build's templates are kept here; live-build
copies its defaults first and overlays these.

Full instructions: [docs/build-guide.md](../docs/build-guide.md).
