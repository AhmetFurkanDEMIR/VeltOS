# VeltOS

**Your PC. No Limits.**

VeltOS is a lightweight, Debian-based desktop operating system with a
Windows 11-inspired KDE Plasma desktop. Its goals are automatic, safe
hardware and driver management, and the broadest *practical* compatibility
with Windows applications and games through Wine and Proton.

> **Project status: pre-alpha.** VeltOS builds as a bootable live ISO with
> the VeltOS desktop and has only been tested in virtual machines. It is
> not ready for daily use. The hardware manager, gaming support and a
> tested installation are not done yet. See [docs/status.md](docs/status.md)
> for exactly what works and what has been tested.

## What exists today

- A reproducible-by-design live ISO build (Debian 13 "trixie", Linux 6.12,
  KDE Plasma 6.3 on Wayland) that runs entirely in a Docker container.
- A Windows 11 style desktop: centred taskbar, VeltOS Start menu,
  Windows 11 inspired windows, buttons and menus (derived from Fluent-kde),
  Windows-familiar program names (File Explorer, Settings, Task Manager,
  …), a Windows 11 style Settings app, sign-in screen, boot screen (logo
  and spinner, no visible boot menu) and a live-system welcome window
  ("Try VeltOS" / "Install VeltOS", English / Türkçe).
- Double-clicking a Windows `.exe`/`.msi` (or a `.bat`/`.cmd` batch file) installs or runs it through Wine
  (VeltOS runner); Wine is not a security sandbox, and not every Windows
  program works.
- A VeltOS installer (Calamares) with VeltOS branding.
- System identity (`os-release` says VeltOS while staying Debian-compatible).
- Hardware diagnostic tools on the ISO (lspci, lsusb, lshw, inxi, hwinfo,
  vulkaninfo, glxinfo, vainfo, smartctl, nvme, sensors, mokutil) and
  Debian's redistributable firmware.
- An automated VM boot test (BIOS, UEFI, Secure Boot) with screenshots,
  checks and measurements.

## Quick start (developers)

Requirements: Docker (Docker Desktop on Windows/macOS), bash (Git Bash on
Windows), ~25 GB disk, network access to deb.debian.org.

```bash
build/run.sh iso     # build packages and the ISO into out/iso/
build/run.sh test    # boot it in QEMU/KVM and verify the desktop (UEFI)
```

Details, options and troubleshooting: [docs/build-guide.md](docs/build-guide.md).
Live session login: user `velt`, password `live`.

## Project rules

VeltOS is developed by humans and AI agents together under a short set of
rules — the full text is in [AGENTS.md](AGENTS.md):

1. Working, bootable software before ambitious unimplemented features.
2. Never fabricate build results, test results, hardware support or
   completed features; untested means untested.
3. Reuse mature upstream components (Debian, KDE, Mesa, Wine/Proton);
   VeltOS code lives in small, testable Debian packages.
4. Security, reliability, maintainability and low resource use are
   requirements, not extras.
5. No universal-compatibility or "native performance" claims without
   measurements.
6. Builds and tests stay isolated from the developer's host system.
7. Everything in the repository is written in English, and docs are kept
   current so anyone (or any agent) can continue the work.

## Repository layout

| Path | Contents |
|---|---|
| [AGENTS.md](AGENTS.md) | Rules and handoff guide for contributors and AI agents |
| [build/](build/) | Build entry point, builder container, live-build configuration |
| [packages/](packages/) | VeltOS Debian packages (`veltos-base`, `veltos-desktop`, `veltos-settings`, `veltos-boot`, `veltos-fluent-icons`, `calamares-settings-veltos`, `veltos-winapps`, `veltos-wine-addons`) |
| [tests/](tests/) | VM boot test and committed test evidence |
| [docs/architecture.md](docs/architecture.md) | Technical decisions, trade-offs, risks |
| [docs/build-guide.md](docs/build-guide.md) | How to build and test |
| [docs/testing.md](docs/testing.md) | Test strategy and measurement caveats |
| [docs/status.md](docs/status.md) | Implemented / in progress / planned, with evidence |
| [docs/development-log.md](docs/development-log.md) | Chronological engineering log |

## Roadmap

| Milestone | Scope | State |
|---|---|---|
| 0 — Feasibility & architecture | Base, desktop, driver and compatibility strategy, risks | Done ([architecture](docs/architecture.md)) |
| 1 — First bootable ISO | live-build config, branding, diagnostic tools, VM boot | Done in VMs; Windows 11 UI work continuing — see [status](docs/status.md) |
| 2 — Hardware detection | Velt Hardware Manager, driver recommendations | Planned |
| 3 — Windows application manager | .exe handling, shared Wine environment, logs | Started (runner works in VM tests) |
| 4 — Gaming | Steam/Proton, DXVK/VKD3D-Proton, profiles, benchmarks | Planned |
| 5 — Installer & releases | Branded Calamares, install tests, updates, recovery | Branded installer done; install test pending |

## License

VeltOS code is licensed under the GNU GPL v3 or later ([LICENSE](LICENSE)).
VeltOS artwork is CC-BY-SA-4.0. Debian and upstream components keep their
own licenses.
