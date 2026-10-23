# 2026-10-23 — Installation (BIOS) and boot tests of ISO 20261023-061442

ISO `veltos-0.1.0-dev-20261023-061442`, 2,445,506,560 bytes, sha256
`9d8afa183a94975fa43db82708bb095b6e23e40a527e5733b7c01cc196d32464`.
QEMU/KVM, 4 vCPU, virtio-vga 1920x1080 without 3D (the dev VM: 8 GB, a
40 GB virtio disk, SeaBIOS like the product owner's VirtualBox VM).

## Installation

The previous ISO (`20261023-045821`) left the live system's initramfs out of
its file system, and the installer's initramfs job made nothing (live-tools'
`update-initramfs` wrapper does nothing from the live medium): the installed
system stopped at "Unable to mount root fs" (`01-old-iso-kernel-panic.png`).
With the fix (live packages removed before the initramfs job, the new
`boot-check` job; development log, 2026-10-23 day):

| Step | Result |
|---|---|
| Installer pages | Welcome, location, keyboard, "Erase disk" (boot 1 GiB + root 39 GiB, ext4, MBR), account "Jordan Lee" (VM-only test values) |
| Installation | About 110 s; the initramfs job 12 s; `boot-check` passed; "VeltOS is ready" (`02`–`04`) |
| Installed system | `/boot/initrd.img-6.12.113+deb13-amd64` (135 MB), five initrd lines in grub.cfg, `GRUB_GFXMODE=1920x1080,…` from the boot-resolution job |
| First start from disk | `systemd-analyze`: 3.976 s (kernel 2.136 s + userspace 1.839 s); sign-in screen about 15 s after the VM started (BIOS, GRUB's 2 s included) |
| Signing in | plasmashell about 2.9 s after Enter; Start (`06`); no failed units, no core dumps |

## Boot tests of the live ISO

| Firmware | Checks | `systemd-analyze` | plasmashell | Memory in use |
|---|---|---|---|---|
| UEFI | 19 passed | 6.980 s | 21.0 s | 1551 MiB |
| BIOS | 18 passed | 5.615 s | 19.9 s | 1506 MiB |
| Secure Boot (OVMF, Microsoft keys) | 20 passed | 5.708 s | 16.0 s | 1522 MiB |

Reports: `boot-test-*.md` (their screenshots stayed in `out/test-results/`).

## Windows program

`build/run.sh test-winapps`: 7-Zip 26.04 installed through `veltos-run`
(Wine's PE libraries stripped of debug information), both Start shortcuts
created, no crashes (`winapps-report.json`); Start's search shows both
with their icons (`07-winapps-start-search.png`).

## Not covered here

A UEFI installation with this ISO, an encrypted one (last tested end to end
on 2026-10-19), VirtualBox (VMs on the developer host stall in NEM mode,
see `docs/status.md`), real hardware.
