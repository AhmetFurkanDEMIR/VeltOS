# VeltOS Status

Last updated: 2026-10-19. Every "Implemented" item names the evidence that
shows it working. "Untested" means nobody has observed it working yet. All
observations so far are from QEMU/KVM virtual machines (no 3D acceleration);
**VeltOS has not been run on real hardware yet.**

## Implemented

| Item | Evidence |
|---|---|
| Container build environment (Debian trixie, pinned) | `build/run.sh image` |
| `veltos-base`: os-release identity (dpkg diversion) | 4 unit tests; booted system reports `ID=veltos` |
| `veltos-desktop`: global themes, centred taskbar, VeltOS Start, wallpaper, Windows 11 look derived from Fluent-kde (Kvantum style, Aurorae frames, Plasma theme, colour schemes), Windows-familiar app names in menus and window titles, File Explorer defaults, Windows-style clock/tray, sign-in screen (SDDM theme), no logout confirmation | 29 unit tests (incl. full asset build, offscreen load of the sign-in screen); VM screenshots of desktop, Start, File Explorer ("Home — File Explorer"), Text Editor, sign-in screen in `sddm-greeter --test-mode` |
| `veltos-settings`: Windows 11 style Settings app (Home, About, Storage, Windows programs, light/dark theme, search, EN/TR); KDE System Settings as "Control Panel" | 23 unit tests (catalogue, system facts, offscreen window in EN and TR visiting every page); VM screenshots of Home, System, About |
| `veltos-fluent-icons`: Fluent icons/cursors (pinned, checksum-verified; Microsoft logos removed) | Package checks; visible in VM |
| `veltos-boot`: Plymouth splash (logo + spinner), GRUB theme with Inter fonts, Plymouth defaults diversion, SDDM-after-Plymouth ordering | 10 unit tests + install-tree checks; boot screenshot shows the VeltOS splash (UEFI VM) |
| `calamares-settings-veltos`: installer branding/config, live welcome window (Try / Install, English / Türkçe switch), no lock/sleep in the live session | 15 unit tests (incl. offscreen welcome window); welcome window seen in every live boot test |
| `veltos-winapps` + `veltos-wine-addons`: double-click `.exe`/`.msi` → install/run via Wine | 20 unit tests; 7-Zip installed and started in a live VM on 2026-10-19 (earlier ISO) |
| live-build configuration: hidden boot menu (Esc/F4 shows it), no Turkish entry (language is chosen in the welcome window), Turkish locale compiled, BIOS+UEFI, Secure Boot chain | ISO builds; verify hook passes |
| Build-time verification hook (packages, branding, Plymouth theme *inside the initramfs* as real files, Kvantum/Aurorae/Plasma themes, app names, Settings, Turkish locale, no "Debian" launchers) | Passes in every ISO build |
| VM test tools: boot test (BIOS/UEFI/Secure Boot), Windows-program test, preview, long-running VM (`build/run.sh vm`) | See `docs/testing.md` |

### Latest ISO

See the "Latest test runs" section of `docs/development-log.md` (2026-10-19
entry) for the ISO name, the checks that passed and the screenshots.

### Milestone 1 baseline measurements (UEFI, QEMU/KVM, 4 vCPU, 4 GiB, no 3D)

| Metric | Value |
|---|---|
| systemd-analyze (live) | 2.5 s kernel + 4.5 s userspace = 7.1 s |
| Guest agent reachable (from VM start, incl. 8 s boot-menu wait) | 16.5 s |
| Plasma shell running (from VM start) | 25.1 s |
| Idle RAM, live session, 60 s after login (`MemTotal-MemAvailable`) | 1696 MiB (incl. KDE Welcome Center window) |

Newer boot tests record the same measurements in their `report.md`; they
have not yet been compared systematically (Kvantum/Aurorae cost is still
to be measured, see architecture 2.3.1).

## Not yet tested

- Installing VeltOS to a disk with Calamares (VM) on the latest ISO, and
  therefore the installed system's sign-in screen, GRUB theme, boot splash
  and first login. The sign-in screen has only run in SDDM's test mode.
- Secure Boot boot test on the latest ISO (UEFI and BIOS pass on
  `veltos-0.1.0-dev-20261019-064631`; Secure Boot last passed on a
  2026-10-18 ISO).
- `build/run.sh test-winapps` on the latest ISO.
- The live welcome window's language switch end to end (sign out → signed
  in again in Turkish).
- Anything on real hardware: GPUs (NVIDIA/AMD/Intel), Wi-Fi, Bluetooth,
  audio, laptops, HiDPI screens, blur/translucency with a real GPU.

## Known gaps

- The screen locker after sign-in is still Plasma's own design (Plasma 6
  loads it from the shell package, which VeltOS does not replace yet).
- KDE programs' About dialogs and help menus still name KDE and the
  original program names; Settings opens KDE's own pages for detailed
  settings.
- `/etc/issue` (text console) still says Debian.
- The live system's root drive shows as "/" in File Explorer.
- ISO is not verified bit-for-bit reproducible. No CI.

## Planned

| Milestone | Items |
|---|---|
| UI (continuing) | Windows 11 style screen locker, Quick Settings flyout (Wi-Fi, sound, brightness in one panel), installed-system welcome app, notification/OSD polish, more built-in Settings pages |
| 2 — Hardware | Velt Hardware Manager, NVIDIA driver recommendation + install with Secure Boot MOK handling, printers, hardware test matrix |
| 3 — Windows apps | Runtimes (winetricks), uninstall inside Settings, compatibility matrix |
| 4 — Gaming | Steam + Proton, DXVK/VKD3D-Proton verification, per-game profiles, benchmarks on real GPUs |
| 5 — Releases | Update/recovery strategy, release process, reproducibility verification |

## Next steps

1. Calamares install test in a VM on the latest ISO with screenshots of
   every installer page, then the installed system: sign-in screen, first
   login, Settings, File Explorer.
2. Secure Boot boot test and `test-winapps` on the latest ISO.
3. Lighter live session: Discover notifier, KDE Connect daemon and
   xwaylandvideobridge use ~550 MiB RSS at idle (boot test report).
4. Windows 11 style screen locker and Quick Settings flyout.
5. First run on real hardware (product owner's PC, from USB), recording
   what works.
