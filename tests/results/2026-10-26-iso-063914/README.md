# 2026-10-26 — ISO 20261026-063914: boot tests and a BIOS installation

ISO `veltos-0.1.0-dev-20261026-063914`, 2,368,847,872 bytes, sha256
`ef58a6b5d67b7b620f8817a1293c9ebe87c83fcda9ff6216c1a0ef90c70dcd2c`. Built
from the working tree with the product owner's items 38-45 (language
choice, taskbar audio badge, Maps and location, Bluetooth icons, Explorer
format and shortcuts, power modes, mobile hotspot). The image's verify hook
passed (including the new hotspot checks).

## Boot tests of the live ISO (QEMU/KVM, 4 vCPU, 4 GB, no 3D)

| Firmware | Checks | `systemd-analyze` | plasmashell | Memory in use |
|---|---|---|---|---|
| UEFI | 19 passed | 6.298 s | 20.5 s | 1538 MiB |
| BIOS | 18 passed | 5.648 s | 19.9 s | 1539 MiB |
| Secure Boot (OVMF, Microsoft keys) | 20 passed | 5.706 s | 16.3 s | 1541 MiB |

No FAIL or WARN lines; reports `boot-test-*.md`.

## Installation (dev VM: SeaBIOS, 8 GB, empty 40 GB virtio disk)

Welcome window > Install VeltOS > language, location, keyboard unchanged >
"Erase disk" > account "Jordan Lee" (VM-only test values, not recorded) >
Install Now. The 44 jobs ran from 10:06:15 to 10:08:17 (about two
minutes), `boot-check` passed, "VeltOS is ready" (`03`). Started from the
disk: `systemd-analyze` 4.247 s (kernel 2.273 s + userspace 1.974 s), the
initramfs was there (`/boot/initrd.img-6.12.113+deb13-amd64`, 135 MB), no
failed units, no core dumps, and the lock screen came up (`04`; the date in
Turkish because the location page chose Istanbul). Signing in to the
installed desktop was not done in this run (stopped by the product owner's
new requests); the 2026-10-23 installations signed in.
