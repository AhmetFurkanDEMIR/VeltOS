# 2026-10-27 — VeltOS 1.0: the release ISO and its tests

ISO `veltos-1.0-amd64.hybrid.iso` (build `veltos-1.0-20261027-071020`),
2,108,434,432 bytes (under GitHub's 2 GiB = 2,147,483,648 bytes per release
file), sha256
`3e5273a13b0f87a11bd6a3fb668674b02c5865264065dfe5e570387f4ac1a2af`.
Built from the working tree with items 78-89 and release steps F1, F2, F7;
1055 package unit tests and the repository checks passed in the build, the
image's verify hook passed.

## Boot tests of the live ISO (QEMU/KVM, 4 vCPU, 4 GB, no 3D)

| Firmware | Checks | plasmashell (live) | Memory in use |
|---|---|---|---|
| UEFI | 19 passed | 30.6 s | 1541 MiB |
| BIOS | 18 passed | 31.4 s | 1565 MiB |
| Secure Boot (OVMF, Microsoft keys) | 20 passed | 30.6 s | 1554 MiB |

Reports: `boot-test-*.md`. The live desktop comes about 10 s later than
with the zstd squashfs of earlier ISOs (16-20 s): files are unpacked from
xz now (the price of the ISO under 2 GiB); installed systems read their
own disk and are not affected.

## Installations (dev VM, 8 GB, 40 GB virtio disk, network switched off)

- UEFI, English, "Erase disk", **offline** (`nmcli networking off`, the
  image has no APT package lists): the first try failed at the installer's
  package removal (Debian's `live-task-*` names, unknown to apt without
  lists); fixed in `packages.conf` and checked by the verify hook; the
  second try installed, the bootloader came from the trimmed pool
  (grub-efi-amd64-signed, shim-signed), the first start reached the
  sign-in screen in 3.9 s (no console-setup rebuild), VeltOS 1.0, zram on.
  VeltOS Store's catalogue showed apps without the lists; with the network
  on it refreshed the lists itself and installed VLC after the password
  prompt (`08`).
- BIOS, Turkish, "Erase disk", offline: installed (GRUB-PC from the pool),
  the desktop in Turkish, 4.0 s to the sign-in screen.
- Installer in English and Turkish shows "VeltOS 1.0" and the Turkish
  slogan on two lines (`05`; the version showed as "1" before: Calamares
  reads branding strings that look like numbers as numbers). Slides
  (`03`, `04`).

## Installed system with the new packages (dev VM)

- `01`, `02`: the start screen's F1/F6 hints; F1 held from the reset opened
  the boot menu; without a key VeltOS started.
- `06`: Settings in dark mode, the frame in the window's colour (no band).
- `07`: VeltOS Graphics Cards' pkcon runner asked for the administrator
  password (before: refused without asking); the package installed.
- Settings maximised: pages switched, 0 % CPU (it hung before).

Not tested here: real NVIDIA/AMD hardware, real Bluetooth devices and
touchpads, two real screens.
