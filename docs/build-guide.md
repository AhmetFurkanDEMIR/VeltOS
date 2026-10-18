# Build Guide

How to build the VeltOS ISO and boot-test it. All steps run inside the
`veltos-builder` container; the host only needs Docker.

## Requirements

| | Minimum | Notes |
|---|---|---|
| Docker | Docker Engine (Linux) or Docker Desktop (Windows/macOS) | Must allow `--privileged` containers (live-build needs chroot, mounts, device nodes) |
| Disk | ~25 GB free | Build volume (chroot + package cache) and output ISOs |
| RAM | 8 GB | 16 GB+ recommended; the boot test VM uses 4 GB |
| Network | Access to deb.debian.org | First build downloads ~2 GB of packages; later builds reuse the cache |
| KVM | Needed for `test` only | Linux: `/dev/kvm`. Windows: see below |
| Shell | bash | On Windows use Git Bash |

### Windows (Docker Desktop + WSL2)

- Start Docker Desktop first (`docker info` must work).
- `build/run.sh test` needs KVM inside Docker's Linux VM. The script loads
  the `kvm_intel`/`kvm_amd` module there automatically if `/dev/kvm` is
  missing. This only affects Docker Desktop's VM, is not persistent (lost
  when Docker or WSL restarts) and does not change Windows settings.
  Nested virtualization must be available (Windows 11 + WSL2 default).
- Git Bash rewrites `/paths`; `build/run.sh` sets `MSYS_NO_PATHCONV=1`.
  When calling `docker` by hand, do the same.

## Commands

```bash
build/run.sh image        # build the builder image (done automatically when missing)
build/run.sh packages     # build VeltOS .deb packages (+ unit tests) into out/packages/
build/run.sh iso          # packages + live ISO into out/iso/veltos-<version>-<timestamp>/
build/run.sh test         # boot the newest ISO with UEFI and verify the desktop
build/run.sh test bios    # same with legacy BIOS (SeaBIOS)
build/run.sh test secureboot   # UEFI with Secure Boot (Microsoft keys enrolled)
build/run.sh shell        # interactive shell in the builder (build volume at /build)
build/run.sh clean        # delete the build volume (next build starts cold)
```

Environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `VELTOS_VERSION` | `0.1.0-dev` | Version in the ISO name and volume label |
| `SOURCE_DATE_EPOCH` | last git commit time | Timestamps inside the image |
| `VELTOS_DEBIAN_MIRROR` | `http://deb.debian.org/debian/` | Mirror used during the build (e.g. a local apt cache or a snapshot.debian.org URL) |
| `VELTOS_SECURITY_MIRROR` | `http://deb.debian.org/debian-security/` | Security mirror used during the build |
| `VELTOS_BUILDER_IMAGE` | `veltos-builder:dev` | Builder image tag |
| `VELTOS_BUILD_VOLUME` | `veltos-build` | Docker volume holding the live-build tree and cache |

The installed system always points APT at `deb.debian.org`, whatever mirror
was used to build.

## Outputs

```
out/
├── packages/                       VeltOS .deb files
├── iso/veltos-<ver>-<stamp>/
│   ├── veltos-<ver>-amd64.hybrid.iso   bootable from DVD or USB (BIOS + UEFI)
│   ├── SHA256SUMS
│   ├── *.packages                  exact package versions in the image
│   ├── build.log                   full live-build log
│   ├── build-info.txt              version, SOURCE_DATE_EPOCH, tool versions
│   └── veltos-*.deb                the VeltOS packages that went in
└── test-results/<stamp>-<firmware>/
    ├── report.md / report.json     checks, measurements
    ├── 01-boot-menu.png, 02-desktop.png
    └── qemu.log, serial.log, plasma-appletsrc.txt
```

`out/` is not committed. Test reports that document a milestone are copied
to `tests/results/` (screenshots + report) and committed.

## What `build/run.sh iso` does

1. `build/scripts/build-packages.sh`: for each directory in `packages/`,
   install its Build-Depends in the container, run `dpkg-buildpackage`
   (which runs the package's unit tests) and lintian (advisory).
2. `build/scripts/build-iso.sh`: copy `build/live-build/` into the build
   volume (keeping `cache/`), add the fresh `.deb` files as a local
   repository (`config/packages.chroot/`), run `lb config` (which executes
   `auto/config`) and `lb build`.
3. live-build stages: bootstrap (debootstrap trixie) → chroot (install
   package lists, firmware, run hooks — `9000-veltos-verify` fails the build
   if branding/identity checks fail) → binary (squashfs, GRUB BIOS/UEFI,
   splash, ISO).
4. Copy the ISO, manifest, log and checksums to `out/iso/...`.

## Writing the ISO to a USB stick

The image is an isohybrid: write it raw, e.g. on Linux
`sudo dd if=veltos-*.iso of=/dev/sdX bs=4M conv=fsync status=progress`
(double-check `/dev/sdX`; it is overwritten), or use a tool such as
Rufus (DD mode) or balenaEtcher on Windows. Live session user: `velt`,
password `live`.

## Troubleshooting

- `lb build` fails in the chroot stage with "Unable to locate package":
  a name in `build/live-build/config/package-lists/` is wrong for trixie.
- Fails in `9000-veltos-verify`: read the `E: veltos-verify:` line in
  `build.log`; it names the broken invariant.
- Disk full: `docker system df`; `build/run.sh clean` drops the build volume.
- Interrupted build: just rerun; the script cleans the previous state.
