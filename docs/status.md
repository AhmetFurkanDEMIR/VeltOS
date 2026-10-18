# VeltOS Status

Last updated: 2026-10-19. Every "Implemented" item names the evidence that
shows it working. "Untested" means nobody has observed it working yet.

## Implemented

| Item | Evidence |
|---|---|
| Container build environment (Debian trixie, pinned) | `build/run.sh image` |
| `veltos-base` package (os-release identity, dpkg diversion) | Builds; 4 unit tests pass; booted system reports `ID=veltos` |
| `veltos-desktop` package (themes, centered taskbar layout, colour schemes, wallpaper light/dark, splash, SDDM/lock screen, logo) | Builds; 9 unit tests pass; taskbar/wallpaper verified in VM |
| live-build configuration (trixie, Plasma, diagnostics, firmware, GRUB BIOS+UEFI, Secure Boot, branding) | ISO builds in ~10 min (cold cache): 2.6 GB hybrid ISO |
| Build-time verification hook | Passes in ISO build |
| VM boot test harness (BIOS/UEFI/Secure Boot, QMP + guest agent) | UEFI run: all checks pass — `tests/results/2026-10-18-m1-baseline-uefi/` |

### Milestone 1 baseline measurements (UEFI, QEMU/KVM, 4 vCPU, 4 GiB, no 3D)

| Metric | Value |
|---|---|
| systemd-analyze (live) | 2.5 s kernel + 4.5 s userspace = 7.1 s |
| Guest agent reachable (from VM start, incl. 8 s boot-menu wait) | 16.5 s |
| Plasma shell running (from VM start) | 25.1 s |
| Idle RAM, live session, 60 s after login (`MemTotal-MemAvailable`) | 1696 MiB (incl. KDE Welcome Center window) |

## In progress — "VeltOS everywhere" and Windows 11 UI (product-owner priority)

The product owner installed the first ISO and found Debian/KDE identity
still visible. Work now in progress:

| Item | State |
|---|---|
| VeltOS installer (Calamares settings + branding + slideshow, "Install VeltOS" launcher; replaces calamares-settings-debian) | Being written |
| Offline install support (bootloader packages in the ISO pool) | Being written |
| Plymouth boot animation (VeltOS logo + spinner) | Being written |
| Installed-system GRUB theme, "VeltOS" boot entries, UEFI entry label | Being written |
| Windows 11 style Start menu (search, pinned grid, recommended, user + power) | Being written |
| Fluent icon theme (packaged from pinned, checksum-verified upstream release) and Inter UI font | Being written |
| Remove KDE Welcome Center (Konqi/KDE community pages) from the image | Planned in this batch |
| Automated "visible Debian text" audit of the image | Planned in this batch |
| Boot tests BIOS / Secure Boot; VM install test | Not yet run |

## Known gaps

- "Install Debian" desktop icon and Debian-branded installer on current ISO.
- KDE Welcome Center shows KDE community pages on first login.
- `/etc/issue` (text console) still says Debian.
- ISO is not verified bit-for-bit reproducible.
- No CI.

## Planned

| Milestone | Items |
|---|---|
| 2 — Hardware | Velt Hardware Manager, NVIDIA driver recommendation + install with Secure Boot MOK handling, hardware test matrix |
| 3 — Windows apps | Double-click `.exe` → install/run in per-app Wine prefixes with Start-menu shortcuts, no terminal; runtimes (winetricks); logs; compatibility matrix |
| 4 — Gaming | i386 multiarch, Steam + Proton, DXVK/VKD3D-Proton verification, per-game profiles, benchmarks on real GPUs |
| 5 — Releases | Update/recovery strategy, release process, reproducibility verification |

## Next steps

1. Finish the "VeltOS everywhere" + Windows 11 UI batch above, rebuild,
   boot-test (UEFI, BIOS, Secure Boot) and run a VM install test with
   screenshots of every installer page.
2. Windows application support (Milestone 3), then gaming (Milestone 4).
