# packages/

VeltOS' own software: one Debian source package per directory (debhelper
compat 13, `3.0 (native)`, version `0.1.0~dev1` during development). Each
is built by `build/run.sh packages` (or as part of `build/run.sh iso`), runs
its unit tests while it builds, and goes into the image from a local
repository. Every package has a README with what it does, how it works,
its tests and what has not been tested yet.

| Package | What it is | Unit tests |
|---|---|---|
| [veltos-base](veltos-base/) | System identity (`os-release` says VeltOS, `ID_LIKE=debian`) and the login message | 8 |
| [veltos-desktop](veltos-desktop/) | The desktop: themes, taskbar, Start, Task View, Quick Settings, notifications, the desktop's menus, sign-in and lock screens, wallpapers, Windows-familiar app names, Plasma and KWin overrides, the looks of Firefox, VeltOS Mail (Thunderbird) and Terminal | 113 |
| [veltos-fluent-icons](veltos-fluent-icons/) | Fluent icons and cursors from a pinned upstream release (Microsoft logos removed) and VeltOS' app icons | 2 |
| [veltos-boot](veltos-boot/) | Plymouth splash, GRUB theme and defaults, start-up resolution, the disk-encryption password screen | 30 |
| [veltos-recovery](veltos-recovery/) | Automatic Repair: counting unfinished starts, the repair screen, safe mode | 18 |
| [calamares-settings-veltos](calamares-settings-veltos/) | The installer (Calamares settings, VeltOS pages and jobs) and the live welcome window | 53 |
| [veltos-settings](veltos-settings/) | Settings | 100 |
| [veltos-explorer](veltos-explorer/) | File Explorer, the file dialogs of every program, "Open with" | 74 |
| [veltos-auth](veltos-auth/) | The administrator prompt (polkit agent in the layout of User Account Control) | 9 |
| [veltos-store](veltos-store/) | Store (AppStream and PackageKit) | 22 |
| [veltos-office](veltos-office/) | Microsoft 365's start screen in front of LibreOffice (Word, Excel, PowerPoint), templates and settings for Windows users | 18 |
| [veltos-calendar](veltos-calendar/) | Calendar | 19 |
| [veltos-clock](veltos-clock/) | Clock: alarms, timers, stopwatch, world clock, focus sessions | 10 |
| [veltos-calculator](veltos-calculator/) | Calculator: standard and scientific | 42 |
| [veltos-notepad](veltos-notepad/) | Notepad | 19 |
| [veltos-photos](veltos-photos/) | Photos: gallery, viewer, simple editing | 17 |
| [veltos-media](veltos-media/) | Media Player: music and video libraries, playlists | 11 |
| [veltos-camera](veltos-camera/) | Camera | 10 |
| [veltos-snip](veltos-snip/) | Snipping Tool (Print Screen, Win+Shift+S) | 20 |
| [veltos-pdf](veltos-pdf/) | PDF Reader | 6 |
| [veltos-archive](veltos-archive/) | Archive manager in WinRAR's layout (7-Zip, bsdtar) | 21 |
| [veltos-taskmanager](veltos-taskmanager/) | Task Manager | 19 |
| [veltos-disks](veltos-disks/) | Disk Management (UDisks2) | 19 |
| [veltos-winapps](veltos-winapps/) | Windows programs through Wine: the runner, one Windows environment, programs in Start and Settings | 27 |
| [veltos-wine-addons](veltos-wine-addons/) | Wine Mono and Wine Gecko, the versions Wine expects | SHA-256 checked at build |

Test counts are from the 2026-10-23 builds; `tests/repo` adds 8
repository-wide checks (line endings, control characters, logo copies, the
website's icons, Qt keyword arguments).

The VeltOS apps are Python 3 and Qt Quick (PySide6). Their tests use the
standard library's `unittest` only, and QML is loaded offscreen where a
test needs a window.

## Adding a package

1. `packages/<name>/debian/` with `control`, `changelog`, `rules`,
   `copyright`, `source/format` (`3.0 (native)`), debhelper compat 13.
   Generated files go to `build-assets/` (git-ignored) from `debian/rules`.
2. Tests in `packages/<name>/tests/` (Python `unittest`), run from
   `override_dh_auto_test`. Checks on the *installed* tree go in
   `execute_after_dh_auto_install` or `execute_after_dh_install`
   (dh_auto_test runs before installation, dh_install after
   dh_auto_install).
3. Third-party sources: pin them in `upstream.json` (URL + SHA-256);
   `build/scripts/fetch-upstream.py` verifies and unpacks them.
4. If the package needs the logo, keep a copy in `branding/`; the repo test
   `tests/repo/test_consistency.py` checks it matches the master.
5. Add the package to a list in `build/live-build/config/package-lists/`
   and, if essential, to `9000-veltos-verify.hook.chroot`.
6. Add a `README.md` explaining what it installs and why, and a row to the
   table above and to the repository map in `AGENTS.md`.
