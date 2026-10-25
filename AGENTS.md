# AGENTS.md — Working on VeltOS

This file is for AI coding agents and new human contributors. It contains
the project rules, where things are, and how to continue the work. Read it
fully before changing anything, then read `docs/dev/status.md` (what is done)
and `docs/dev/architecture.md` (why it is built this way).

## Project in one paragraph

VeltOS ("Your PC. No Limits.") is a Debian 13 "trixie" based desktop
distribution with a Windows 11-inspired KDE Plasma desktop, hardware-aware
driver management and (planned) strong Windows application and game
compatibility through Wine/Proton. It is built incrementally as a real,
installable OS with reproducible builds and automated tests. The product
owner sets priorities; agents act as the engineering team.

## Rules (non-negotiable)

1. **Language.** Everything in the repository is English: code, comments,
   docs, commit messages, package descriptions. Answer people in the
   language they write in; the repository stays English. (VeltOS itself
   speaks English and Turkish: its translations are part of the product.)
2. **Working software first.** A bootable, installable system beats
   ambitious unimplemented features. Work in small, verifiable increments.
3. **Never fabricate results.** Do not claim a build passed, a test ran,
   hardware works or a feature is complete unless you observed it. Report
   failures with their output. Mark anything untested as untested.
4. **No silent mocks.** Never replace a real implementation with a mock or
   stub without labelling it clearly in code and in `docs/dev/status.md`.
5. **Reuse, don't rewrite.** Use Debian, KDE, Mesa, Wine/Proton and other
   mature upstream components. VeltOS code goes into small, testable
   packages under `packages/`. Do not fork Plasma, the kernel or Wine.
6. **Verify upstream facts.** Check package names/versions against
   packages.debian.org or `apt-cache policy` in the builder container and
   read upstream docs; do not rely on memory. Record what you verified.
7. **Lightweight by default.** Every new service, daemon or autostart
   entry needs a reason; measure RAM/CPU/boot impact (see `docs/dev/testing.md`).
8. **Security and safety.** Packages come only from signed Debian archives
   or are built from this repo. Never install drivers from unverified
   downloads. Never run untrusted `.exe` files with elevated privileges.
   Wine is not a sandbox — say so.
9. **Host safety.** Never repartition disks, change boot configuration,
   overwrite user data or run destructive commands on a developer's machine
   without explicit approval. Builds and tests run in the builder container.
10. **Honest claims.** Never promise universal Windows compatibility or
    "native performance" without comparative measurements.
11. **Explain decisions.** Architectural choices go into
    `docs/dev/architecture.md` with alternatives and trade-offs.
12. **Keep the handoff current.** After any meaningful change update
    `docs/dev/status.md`, add an entry to `docs/dev/development-log.md`, and keep
    README files accurate. The next agent must be able to continue from the
    repository alone.

## Repository map

| Path | What |
|---|---|
| `build/run.sh` | Single entry point: `image`, `packages [name...]`, `iso`, `test`, `test-winapps`, `preview`, `vm`, `shell`, `clean` |
| `build/builder/Dockerfile` | Build/test container (Debian trixie, pinned by digest) |
| `build/scripts/` | In-container scripts: package build, ISO build |
| `build/live-build/` | live-build config: `auto/config` (options), package lists, APT pins, hooks, GRUB menu/theme, boot splash |
| `packages/veltos-base/` | VeltOS `os-release` identity (dpkg diversion) |
| `packages/veltos-desktop/` | Global themes (Light default), Windows 11 style taskbar + VeltOS Start menu, Windows 11 look derived from Fluent-kde (Kvantum style, Aurorae frames, Plasma theme, colour schemes), Windows-familiar app names (menus and window titles), File Explorer defaults, sign-in screen (SDDM theme), generated wallpapers (Bloom default, Flow, Glow, Lake), splash, Ctrl+Alt+Del screen, locked taskbar and its menus, Plasma overrides (toasts, tray flyouts, taskbar menus, the desktop's Windows 11 menus / New / protected icons), volume OSD at the bottom, master logo, software rendering where the display driver has no OpenGL (VirtualBox without 3D: `needs-software-rendering`, session and sign-in screen), Plasma's own services without the portal platform theme (session start); KWin script `kwin/scripts/veltostaskbarpreview` (taskbar window previews, Peek) and effect `kwin/effects/veltostoast` (toasts slide in); the desktop guard (`system/veltos-desktop-guard`, D-Bus system service keeping This PC, Recycle Bin and Store on the desktop) |
| `packages/veltos-settings/` | VeltOS Settings: Windows 11 style settings app (PySide6/QML), every page built in (network, devices, display, sound, power, notifications, personalization, apps, accounts, time & language, accessibility, privacy); diverts `systemsettings`/`kcmshell6`/`kinfocenter`/`keditfiletype` to itself so KDE's settings window never opens (the `*.kde` originals root-only); Personalization > Taskbar (`taskbar.py`); privileged AccountsService calls in one process (`admin_calls.py`) |
| `packages/veltos-explorer/` | VeltOS File Explorer: Windows 11 File Explorer layout (tabs in the title bar, command bar, Home, This PC, Recycle Bin), file operations through KIO (`kioclient`); default for folders. Also the Windows 11 file dialog of every program (`--pick`; `--portal` = the xdg-desktop-portal FileChooser backend) and the "Select an app to open this file" window (`--open-with`), and the Windows 11 Properties window (`--properties`, also from the desktop) |
| `packages/veltos-auth/` | VeltOS authentication prompt: polkit agent (GLib) + a window in the layout of Windows 11's User Account Control (PySide6/QML); the password goes through polkit's own helper; KDE's agent service masked |
| `packages/veltos-clock/` | VeltOS Clock: Windows 11 Clock (Focus sessions, Timer, Alarm, Stopwatch, World clock); `veltos-clock-agent` rings alarms and timers while the app is closed, and VeltOS Calendar's reminders |
| `packages/veltos-calendar/` | VeltOS Calendar: Windows 11 Calendar (day, work week, week, month, year views; quick event card and full editor; repeats and reminders) on one iCalendar file (`~/.local/share/veltos-calendar/calendar.ics`) |
| `packages/veltos-taskmanager/` | VeltOS Task Manager: Windows 11 Task Manager layout (Processes, Performance, Startup apps), psutil, GPUs from DRM fdinfo / amdgpu sysfs / nvidia-smi (`gpu.py`); Ctrl+Shift+Esc; also KWin's "is not responding" window (diverts `kwin_killer_helper`, `notresponding.py`) and the notice after a crash instead of DrKonqi (`crash.py`, drop-in for DrKonqi's per-crash launcher service) |
| `packages/veltos-calculator/` | VeltOS Calculator: Windows 11 Calculator (Standard and Scientific modes, memory, history, keep on top, app theme); decimal engine in `engine.py` |
| `packages/veltos-notepad/` | VeltOS Notepad: Windows 11 Notepad layout (tabs in the title bar, File/Edit/View, find and replace, status bar with encoding and line ending), keeps encodings/line endings, restores unsaved tabs; default for text files |
| `packages/veltos-photos/` | VeltOS Photos: Windows 11 Photos (gallery by month, favorites, folders, viewer with filmstrip and file information, Edit image with crop/rotate/adjust via Pillow, slideshow); default for pictures |
| `packages/veltos-media/` | VeltOS Media Player: Windows 11 Media Player (music library with tags/covers via mutagen, video library, play queue with shuffle/repeat, playlists, player bar, now playing) on Qt Multimedia; default for audio and video |
| `packages/veltos-pdf/` | VeltOS PDF Reader: modern PDF reader layout (Home with recent files, tabs, search, thumbnails, bookmarks, zoom/fit, read mode, properties, passwords, printing) on QtQuick Pdf; replaces Okular, default for PDF |
| `packages/veltos-mail/` | VeltOS Mail: e-mail in the layout of Windows 11's new Outlook (PySide6/QML: blue header with search, app bar, Home/View/Help ribbon, folder pane with Favorites, Focused/Other list, reading pane in Qt WebEngine with JavaScript off, compose in the reading pane, "Add your account"); IMAP/SMTP with Python's imaplib/smtplib, local copy in SQLite; OAuth 2.0 only with a configured client id (`/etc/veltos/mail-oauth.json`); replaces Thunderbird (2026-10-23) |
| `packages/veltos-office/` | VeltOS Office: Microsoft 365's start screen (Home / New / Open / Account / Options, the app's colour, Windows 11 animations; PySide6/QML, `veltos-office word|sheet|slides`) in front of LibreOffice Writer/Calc/Impress (Debian), VeltOS' own templates (built from flat ODF by LibreOffice at package build time) and a configuration layer for Windows users (Tabbed interface, Colibre icons, MS formats by default, Carlito font, "VeltOS Office" in titles, no bars); app names, icons and defaults live in veltos-desktop/veltos-fluent-icons, the coloured title bars in veltos-desktop's Aurorae change |
| `packages/veltos-archive/` | VeltOS Archive: WinRAR's layout (toolbar, archive list, Extract To, Add, Test, passwords) on 7-Zip (+ 7zip-rar) and bsdtar; File Explorer's extract/compress |
| `packages/veltos-camera/` | VeltOS Camera: Windows 11 Camera layout (photo, video, timer, framing grid, Camera Roll) on Qt Multimedia (FFmpeg backend, V4L2) |
| `packages/veltos-snip/` | VeltOS Snipping Tool: Print Screen / Win+Shift+S overlay (rectangle, window, full screen, freeform), clipboard + Pictures/Screenshots + notification, markup window; captures through Spectacle in the background |
| `packages/veltos-store/` | VeltOS Store: Microsoft Store layout (Home, Apps, Gaming, Library, app pages) on AppStream (gir1.2-appstream-1.0) and PackageKit (pkcon); replaces Discover |
| `packages/veltos-fluent-icons/` | Fluent icons/cursors from a pinned upstream release (Microsoft logos removed), VeltOS "This PC" and Recycle Bin icons |
| `packages/veltos-boot/` | Plymouth splash (+ Plymouth defaults diversion), GRUB theme and fonts, boot defaults, SDDM-after-Plymouth ordering, disk-encryption password screen (initramfs hook), start-up screen at the screen's resolution (`resolution/`: set at installation, kept in step at sign-in), GRUB start counting with the Recovery and safe-graphics entries (`grub.d/10_linux`) |
| `packages/veltos-recovery/` | VeltOS Automatic Repair: after two starts that did not finish, GRUB starts `veltos-recovery.target`, a full-screen Windows 11 style recovery window on Qt's linuxfb (Restart, Startup Repair, Safe mode, Command Prompt as a console sign-in, last start's problems, Turn off); the services that clear the count or restart after a failed start; `veltos-safe-graphics` (starts without a graphics driver sign in to Plasma on X11); persistent journal |
| `packages/calamares-settings-veltos/` | VeltOS installer (Calamares) configuration and branding: VeltOS QML pages for Calamares' QML modules (`branding/veltos/*q.qml`, Windows 11 setup look), slideshow, partition layout (BitLocker-like encryption), installer jobs (incl. `boot-resolution`, and `boot-check`, which stops an installation whose system could not start), live welcome window (Try/Install), live session settings; the installer's Qt style `veltos-installer` (`style/`, C++ plugin over Kvantum: Calamares' disk bars, legend and resize bar in VeltOS' look, Disk Management's sizes, drop-down lists under their box) |
| `packages/veltos-disks/` | VeltOS Disk Management: Windows 11's Disk Management layout (volume list over the disk map, partitions to scale) on UDisks2 (busctl): format, delete, new simple volume, label, mount/unmount/eject, initialize; the running system's volumes protected; replaces KDE Partition Manager |
| `packages/veltos-graphics/` | VeltOS Graphics Cards: the PC's graphics cards (lspci, sysfs, eglinfo, vulkaninfo) with driver and properties; one button installs or updates NVIDIA's driver (Debian non-free, `nvidia-detect`, DKMS, Secure Boot key through mokutil) or the AMD/Intel firmware and Mesa drivers through `pkcon`; also Settings > Display > Graphics cards |
| `packages/veltos-winapps/` | `veltos-run`: double-click `.exe`/`.msi`/`.bat`/`.cmd` → install/open via Wine, in a Windows 11 App Installer style window; `programs.py` reads installed Windows programs from Wine's registry files (Settings' Windows programs page) and removes what Wine leaves after an uninstall (`forget_removed`) |
| `packages/veltos-wine-addons/` | Wine Mono/Gecko (pinned, verified) |
| `tests/boot/vmlib.py` | Shared QEMU/QMP/guest-agent helpers |
| `tests/boot/vmtest.py` | QEMU/KVM boot test with screenshots, checks and measurements (`build/run.sh test`) |
| `tests/boot/vmpreview.py` | Dev aid: install fresh `.deb`s into a live VM and screenshot a scripted interaction (`build/run.sh preview`) |
| `tests/boot/winapps_vmtest.py` | Installs a real Windows program through `veltos-run` in a VM (`build/run.sh test-winapps`) |
| `tests/boot/vmctl.py` | Long-running VM driven step by step: installations, demos, website pictures (`build/run.sh vm ...`) |
| `tests/repo/` | Repository-wide checks (line endings, control characters, logo copies, the website's icons, Qt keyword arguments) |
| `tests/results/` | Committed test evidence for milestones |
| `docs/` | The website, https://veltos.ahmetfurkandemir.com/ (GitHub Pages, static; see "The website" below) |
| `docs/dev/` | Developer documentation: status, architecture, build guide, testing, development log |
| `out/` | Build outputs (ISO, logs, test runs) — git-ignored |

## How to continue

1. Read `docs/dev/status.md`; pick the first item under "Next steps" unless the
   product owner says otherwise.
2. Make sure the environment works: `build/run.sh packages` (fast) and, for
   image changes, `build/run.sh iso` followed by `build/run.sh test`.
3. Change the smallest thing that delivers the step. Add or update tests.
4. Build and test for real. Read the report (`out/test-results/.../report.md`)
   and look at the screenshots.
5. Update `docs/dev/status.md`, `docs/dev/development-log.md`, README files and,
   for design decisions, `docs/dev/architecture.md`.
6. Commit with a clear English message describing what changed and what was
   verified.

## Conventions

- Debian packaging: debhelper compat 13, `3.0 (native)`, one package per
  directory in `packages/`, version `X.Y.Z~devN` during development. Put
  generated files in `build-assets/` (git-ignored) via `debian/rules`.
- Package unit tests: Python `unittest` under `packages/<pkg>/tests/`, run
  by `override_dh_auto_test`. Standard library only.
- Shell: `bash` with `set -euo pipefail` for scripts; POSIX `sh` for
  live-build hooks and maintainer scripts.
- Line endings: LF everywhere (`.gitattributes`). Files from a Windows bind
  mount appear executable in containers; build scripts normalise modes.
- Artwork: SVG sources in the package; PNGs are rendered at build time.
  Brand palette: blue `#4F7CFF`, indigo `#5B3FE0`, cyan `#2FA8F0`,
  navy background `#050818`–`#0E1846`.
- Naming: packages `veltos-*`; Plasma IDs `org.veltos.*`; live user `velt`.

## The website (`docs/`)

https://veltos.ahmetfurkandemir.com/ is published by GitHub Pages from the
`docs/` folder of `main` (`CNAME`, `.nojekyll`). It is static HTML, CSS
and JavaScript with no build step, no external requests and no cookies:
`docs/index.html` opens complete with a double-click (`file://`).

- Texts: English in `index.html` (`data-i18n` keys), Turkish in the `TR`
  dictionary of `assets/js/main.js`; every key needs both. English and
  dark are the defaults; the visitor's choice is kept in `localStorage`.
- Pictures: `assets/img/*.webp` (1600x900) are screenshots of an installed
  system in the QEMU dev VM (English, 1920x1080, downscaled); `og.jpg`
  (1200x630) is the link preview. Retake them when the desktop changes
  visibly, and never show something the ISO does not do.
- Icons: copies of the OS's own SVGs (`tests/repo` checks they still
  match a file of the same name in `packages/`). Fonts: Inter subsets
  (OFL, `assets/fonts/LICENSE-Inter.txt`).
- Download: the ISO's direct https link goes into
  `<meta name="veltos-iso-url">` in `docs/index.html`; the head script marks
  the page `iso-ready` and every `[data-iso-link]` button follows it (empty:
  "Download ISO · Soon" and a note). Update the size and the SHA-256 in the
  download panel with the link. A GitHub release file must be under 2 GiB
  (docs.github.com, "About releases"); the ISO is larger, so it is hosted
  elsewhere.
- Claims on the site follow the project rules: no untested support, no
  "native performance", measured numbers with how they were measured.
- Turkish is written as Turkish, not word for word, and uses the names the
  OS shows (VeltOS Mail, VeltOS Mağaza, Bu bilgisayar, Görev Görünümü,
  Başlangıç Onarımı, Komut İstemi; firmware is "üretici yazılımı").
  Numbers follow the language (`data-suffix-tr`, decimal comma). Check a
  new text for both languages at 1081-1140 px: Turkish menu names are
  longer (the menu folds at 1120 px).
- The logo links to `#top`, which HTML treats as the top of the document
  only while no element has that id; an id on the sticky header made the
  link do nothing (the header is always in view).
- Keep scrolling cheap: no `filter: blur()` or `backdrop-filter` on large or
  moving elements (they were drawn again for every frame), endless
  animations only on `transform`/`opacity` (the hero's pause while it is
  scrolled away), no layout reads in scroll handlers (IntersectionObserver
  instead).
- The developer documentation lives in `docs/dev/` (also published by
  Pages as plain files).

## Gotchas learned so far

- `/dev/kvm` is missing in Docker Desktop containers until the KVM module
  is loaded in Docker's VM; `build/run.sh test` handles it.
- live-build's GRUB template has no timeout; ours sets 10 s.
- live-build substitutes placeholders in `config/bootloaders/grub-pc/grub.cfg`
  with unanchored `sed` (e.g. any `KERNEL_LIVE`, `APPEND_LIVE`, `MEMTEST`
  text is replaced) — avoid those words in comments there.
- debhelper treats executable `debian/*.install` files as dh-exec scripts.
- live-build turns `/etc/os-release` into a *copy* of Debian's file
  (`bootstrap_debootstrap`), so diverting `/usr/lib/os-release` alone is not
  enough; hook `8000-veltos-os-release` restores the symlink. Always check
  identity in the booted system, not only in the build chroot.
- live-build's `--firmware-chroot true` also installs contrib
  `firmware-b43*-installer` packages that download non-redistributable
  firmware during the build. VeltOS uses an explicit firmware list
  (`veltos-firmware.list.chroot`); the verify hook rejects the installers.
- `*.list.binary` package lists need `apt-utils` (apt-ftparchive) in the
  builder image.
- Foreign-architecture packages (`wine32:i386`) in a `.list.chroot` make
  live-build enable that architecture automatically.
- On Windows, Python's `Path.write_text()` writes CRLF; make writes break.
  Write bytes or use `newline="\n"`. `build-packages.sh` refuses CRLF
  files and `tests/repo` checks the whole tree.
- debhelper runs `dh_auto_test` *before* `dh_auto_install`; checks on the
  installed tree belong in `execute_after_dh_auto_install`. `python3 -m
  unittest` with zero tests exits non-zero (good: catches missing tests).
- Debian version ordering: `10.0~repack-6` is *lower* than `10.0`. Use
  `(>= 10.0~)` in dependencies.
- Plasma 6.3 `Kicker.SystemModel` dereferences its favorites model
  without a null check: create it only after `RootModel.refresh()` (see
  `StartMenu.qml`). Found by `coredumpctl` in the VM; boot tests now fail
  on any core dump.
- Fluent icons draw `start-here*` and Wine icons as Microsoft's Windows
  logo; `veltos-fluent-icons` replaces/removes them. Re-check after
  updating upstream.
- Debian's Wine does not download Wine Mono/Gecko; `veltos-wine-addons`
  ships the exact versions Wine expects (see `dlls/appwiz.cpl/addons.c`).
- Plasma applies the global theme's layout script only to users without
  existing Plasma configuration.
- Plymouth's theme comes from `/usr/share/plymouth/plymouthd.defaults`
  (diverted by `veltos-boot`), not from the `default.plymouth`
  alternative. Debian's file named a theme that is not installed, so every
  initramfs silently fell back to the text splash. Check with
  `lsinitramfs`; the verify hook does.
- Files listed in `debian/*.install` are copied by `dh_install`, which runs
  after `dh_auto_install`: checks on them belong in
  `execute_after_dh_install`.
- Kvantum has no system-wide configuration; the theme is set per user by
  the Plasma session script (`veltos-session.sh`).
- `kwriteconfig6 --delete` on a user file writes a deletion marker that
  also hides the `/etc/xdg` value; to test system defaults, remove the
  user's line instead.
- Fluent-kde: its Plasma theme draws the "start" icon as the Windows logo
  (removed by `tools/fluent.py`), its default window frames are 75 %
  opaque and need blur (VeltOS uses the solid variant), and Fluent Light's
  Kvantum highlight is translucent (Kirigami falls back to Qt's blue).
- `grub-mkfont` names fonts "<family> <Regular|Bold> <size>"; Inter
  SemiBold would also be "Inter Regular", so it gets its own family name.
- live-build's default GRUB `config.cfg` beeps at start-up; VeltOS ships
  its own in `config/bootloaders/grub-pc/`.
- System Settings pages are hidden with `kcm_<id>=false` in
  `[KDE Control Module Restrictions]` of `/etc/xdg/kdeglobals`.
- Plymouth's two-step plugin refuses to start without `lock.png` in the
  theme; the initramfs contains only the selected theme, so its images
  must be real files, not symlinks to another theme (it silently showed
  the text splash for that reason).
- GRUB: load proportional theme fonts only *after* `terminal_output
  gfxterm` (gfxterm takes the last loaded font and fails with "glyphs too
  large", falling back to the firmware console without the theme); a
  `progress_bar` with any `text` property is a full text line tall;
  `selected_item_pixmap_style` borders are drawn *outside* the item, so
  `item_spacing` must be at least twice the border slice size.
- Programs started with `build/run.sh vm exec-user` do not get the Plasma
  session environment (`LANGUAGE`, `XDG_DATA_DIRS`); start them from Start
  or the taskbar when checking names or titles.
- `pkill -f PATTERN` inside `vm exec "..."` also matches the `sh -c` that
  runs it and kills it first; use `pkill -x NAME`.
- VirtualBox on a Windows host with Hyper-V active (Docker Desktop/WSL2)
  runs in "NEM" mode: GRUB on BIOS with `GRUB_GFXMODE=auto` made it stop
  with a triple fault when starting Linux; a fixed mode (1024x768/800x600)
  works. VirtualBox can be driven from Git Bash with `VBoxManage`
  (headless start, `screenshotpng`); keep test VMs separate from the
  product owner's VMs and work on disk copies.
- Do not ship a conffile at the path of another package's diverted
  conffile (dpkg asks a question and stops); copy such files in the
  postinst instead.
- PySide6/QML apps: packaged files all get the same time stamp
  (SOURCE_DATE_EPOCH), so Qt's QML disk cache keeps old compiled QML
  after an update and mixing it with new types crashed File Explorer.
  Every VeltOS QML app's launcher sets `QML_DISABLE_DISK_CACHE=1`, and
  `veltos_controls.use()` turns the cache on again in a folder named after
  a hash of the app's QML files (`QML_DISK_CACHE_PATH`, Qt 6.8).
- PySide6 6.8: a QMimeData made in Python and given to the clipboard is
  deleted by Qt after Python has shut down -> segfault at exit (and a core
  dump the boot test would count). File Explorer leaves with `os._exit`;
  its tests clear the clipboard in `tearDownClass`.
- A QGuiApplication (not QApplication) in a Plasma session gets the
  `org.kde.breeze` Qt Quick Controls style even when `org.kde.desktop` is
  asked for. Test QML apps started from the taskbar, not only with
  `vm exec-user` (which lacks `XDG_CURRENT_DESKTOP=KDE`).
- `plasma-apply-lookandfeel` writes the Plasma theme to
  `~/.config/kdedefaults/plasmarc`; the running taskbar only watches the
  user's own `~/.config/plasmarc` file (KDirWatch, not KConfig change
  signals), and `kwriteconfig6` does not write a value equal to the
  kdedefaults one. Settings therefore edits `~/.config/plasmarc` directly
  (the first light/dark switch left the taskbar light before).
- Calamares without a `partition.conf` put `/boot` inside the encrypted
  partition (LUKS1, GRUB asks on a text console, one try, US keyboard),
  and the image lacked `cryptsetup-initramfs`: encrypted installs could not
  start. VeltOS now keeps `/boot` unencrypted (`partitionLayout` with
  `noEncrypt`) and lets the boot screen ask for the password.
- KDE's command-line file tool is `kioclient` (Qt 6 build) in Debian 13;
  there is no `kioclient6`.
- `tools/fluent.py` `set_ini_keys` refuses keys that upstream does not have
  (catches upstream changes); new keys must be listed in `add=`.
- Calamares' fstab module writes crypttab entries *without options* when
  `/boot` is unencrypted (`crypttabOptions` is ignored then); VeltOS adds
  `tries=0` in its own `crypttab-tries` job.
- Debian's plymouth initramfs hook copies only fontconfig's default and
  monospace fonts; a theme font that is missing makes the boot splash
  text monospace. veltos-boot's initramfs hook copies Inter. Check with
  `lsinitramfs`.
- Plymouth `display-message` text stays on screen until `hide-message`;
  the unlock screen shows "wrong password" through the prompt instead.
- `dh_installinitramfs` adds the `update-initramfs` trigger for files in
  `usr/share/initramfs-tools/hooks`; a hand-written `.triggers` line for it
  is a lintian error (`repeated-trigger-name`).
- PySide6 turns keyword arguments of Qt constructors into setter calls
  with the C library's `toupper()`: in a Turkish locale `interval` becomes
  `setİnterval` and the call fails (File Explorer did not start on
  Turkish systems). Use setters; `tests/repo` rejects the pattern, and the
  builder image has `tr_TR.UTF-8` so Turkish test classes run in it.
- Firefox on Linux draws its own (libadwaita-like) title bar buttons and
  ignores the GTK theme; VeltOS styles them through Firefox autoconfig
  (`veltos-desktop/tools/firefox.py`). Firefox does not let `data:` images
  use `context-stroke`, so glyph images carry explicit colours.
- KDE's GTK settings module produced empty button images for Aurorae
  window frames; the VeltOS GTK theme carries its own buttons.
- KWin's startup feedback (Wayland) draws the starting app's icon next to
  the pointer in every mode and never shows a busy pointer; VeltOS turns
  it off (`klaunchrc` `BusyCursor=false`).
- SDDM's default `InputMethod` is `qtvirtualkeyboard`: the on-screen
  keyboard covered the sign-in screen. VeltOS sets it empty.
- A Plasma package copied to `/var/lib/veltos/xdg/plasma/plasmoids/<id>`
  replaces Plasma's own (`XDG_DATA_DIRS` order); `update-plasma-overrides`
  uses this. While developing, delete `~/.cache/plasmashell/qmlcache` and
  restart `plasma-plasmashell` after installing rebuilt packages (same file
  times, stale compiled QML).
- Panel popups float with all corners rounded only when the containment
  has `ContainmentPrefersFloatingApplets`; Plasma sets it only for floating
  panels, so VeltOS' plasmoids keep it set (`floatPopups()`).
- With llvmpipe (VMs without 3D) KWin's window captures for taskbar
  previews are garbled; `session-fixups` switches previews off there.
- `notify-send` (libnotify-bin) is not in the image; send test
  notifications with `gdbus call ... org.freedesktop.Notifications.Notify`.
- In Git Bash, `\n` inside a quoted heredoc can reach Python as a real
  newline; write code containing escapes with the editor tools instead.
- KDE's platform theme forces `org.kde.breeze` as the Qt Quick style of
  every QGuiApplication (`QT_QUICK_CONTROLS_STYLE` is ignored);
  `QQuickStyle.setStyle` after creating the application wins. VeltOS'
  apps do that with `veltos_controls.use()` (style `org.veltos.controls`,
  veltos-desktop). Kirigami picks its platform plugin by the style's name
  (`kf6/kirigami/platform/<name>*.so` in the library paths): a style
  without one gets Kirigami's plain colours. A style module's qmldir
  falls back with `import org.kde.breeze` (no version: `auto` took the
  module's own 1.0 and failed).
- Konsole 25.04 builds its hamburger menu (shown in the right-click menu
  while the menu bar is hidden) from the toolbars; layout files without
  them crashed it on every right-click. Hide toolbars with
  `hidden="true"`, never remove them. Plasma 6.3's startplasma applies
  `plasma-localerc`'s `[Translations] LANGUAGE` *after* the
  `plasma-workspace/env` scripts, so a LANGUAGE exported there is lost
  when that file has one; write such values into the file
  (`veltos-session.sh`).
- Running KDE tools for a session from `vm exec` needs the session's
  `XDG_MENU_PREFIX=plasma-` (and the other variables of plasmashell's
  environment): `kbuildsycoca6` without it built an empty application
  database and the taskbar showed "?" icons.
- Linux cuts process names (`comm`) to 15 characters; match programs by
  their command line (VeltOS Task Manager `program_of`).
- Every ISO build leaves a 3.5 GB directory in `out/iso`; the product
  owner's C: drive filled up after eight builds, the last ISO could not be
  written and Docker Desktop hung. Delete superseded builds regularly.
- Plasma applets take their lock (immutability) from the whole shell, not
  from their panel: `panel.locked = true` alone leaves the taskbar's items
  configurable. Lock each applet (`session-fixups`). Locking the shell
  itself (SystemImmutable) makes `evaluateScript` refuse D-Bus scripts.
- Plasma's notification pop-up model lists the oldest first whatever its
  `sortOrder`; position toasts by iterating backwards. For equal widths in
  a `RowLayout` use `uniformCellSizes` (stretch factors did not work).
- KWin chose 105 % display scale for QEMU's screen; fractional scales blur
  1 px lines and text. `display-scale` rounds to 25 % steps once per screen.
- Restart the welcome window or other programs in `vm exec` with a
  pattern the command line itself does not contain
  (`pkill -f '[v]eltos-live-welcome'`), and start them in a second call.
- Running package unit tests on the host leaves `__pycache__` directories;
  the repository test then fails the package build. Delete them first.
- GRUB's PNG reader failed on one compressed boot menu picture (black
  menu, GRUB waiting); a one-character change in the picture triggered it.
  GRUB pictures are rewritten unfiltered and uncompressed
  (`build/scripts/plain-png.py`, binary hook, veltos-boot).
- The lock screen comes from Plasma's desktop *shell* package
  (`/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen`),
  not from the look-and-feel package; VeltOS replaces `LockScreenUi.qml`
  through `update-plasma-overrides` (type "shells").
- KWin's Aurorae engine loads its QML from `kwin/aurorae/` in the XDG data
  dirs (`/usr/share/kwin/aurorae`, package kwin-data), so it can be
  changed like Plasma's packages (type "kwin"). KWin reads it at start:
  sign out and in after installing a changed copy. Aurorae button SVGs
  have no state for maximised windows; VeltOS adds `*-maximized` pictures.
- In a live system made from an older ISO, Dolphin may still be
  installed; its `org.kde.dolphin.FileManager1.service` and VeltOS File
  Explorer's service claim the same D-Bus name and dbus picked Dolphin's.
  The image leaves Dolphin out; when testing in an old live system, move
  Dolphin's service file away and reload the bus configuration.
- `vsess` (VM helper) takes the whole command as one argument.
- KXMLGUI (`KXMLGUIClient::findVersionNumber`) takes the first word
  "version" after the first "gui" in an `.rc` file as its number: a
  comment mentioning "version" before the `<gui>` element made Konsole
  ignore VeltOS' file. Put comments inside the `<gui>` element.
- Konsole 25.04 uses `TabBarStyleSheet` only when
  `TabBarUseUserStyleSheet=true` and the file in `TabBarUserStyleSheetFile`
  cannot be read; VeltOS ships the tab styles as files.
- Konsole sets a see-through window background (for transparent
  profiles); with Kvantum the tab bar and toolbar areas then showed the
  windows behind. VeltOS starts it with `--notransparency`.
- On Wayland only programs KWin trusts may take screenshots
  (`org.kde.KWin.ScreenShot2`); VeltOS Snipping Tool runs `spectacle
  --background --nonotify --fullscreen --output FILE`. kglobalacceld takes
  shortcuts from `X-KDE-Shortcuts` in application desktop files and skips
  files in `kglobalaccel/` with `NoDisplay=true` (first file of a name in
  `XDG_DATA_DIRS` wins); it reads them when the session starts.
- gdbus prints a notification number as "(uint32 5,)": do not collect all
  digits. PySide6 cannot send D-Bus `uint` arguments; VeltOS sends
  notifications with `gdbus call` and receives the signals with a
  `QDBusMessage` slot.
- KDE's `systemsettings` and `kcmshell6` are diverted by veltos-settings
  (`/usr/bin/*.kde`) to `veltos-settings-redirect`: never send users to
  KDE's settings window; add a VeltOS Settings page instead.
- `xdg-mime query default text/plain` failed in the Plasma session
  ("Illegal number", xdg-utils 1.2): read mimeapps.list directly.
- Fluent's 12 px `window-pin` icon draws as a cut "x"; File Explorer uses
  its own `qml/pin.svg`. Its navigation pane's pins were also cut in half
  because the scroll view's content was as wide as the pane, not as its
  `availableWidth`: size ScrollView content to `availableWidth`.
- Plasma's clipboard (Klipper) ignores images by default; VeltOS turns
  that off so screenshots stay on the clipboard after the program ends.
- KWin keeps the QML of a scene effect (Task View) after
  unloadEffect/loadEffect; sign out and in to test a changed effect.
- Qt's `Text.StyledText` ignores `<sup>`/`<sub>` (x² showed as "x2");
  use `Text.RichText` for such labels.
- `findChild` does not find Repeater delegates (they are not QObject
  children); tests walk `contentItem().childItems()` instead.
- A QML property named `checked` on a button type clashes with the FINAL
  property of Qt's buttons ("Cannot override FINAL property"); the whole
  file then fails to load.
- `apt-get install ./x.deb` does not reinstall a package of the same
  version (all VeltOS packages are `0.1.0~dev1`): the old files stayed in
  the VM. Use `dpkg -i` to replace an installed package of the same
  version.
- PySide6 ties the Python wrapper of `QQuickTextDocument.textDocument()`
  to the wrapper of the QQuickTextDocument passed in from QML: keep both,
  or the QTextDocument is "already deleted" for Python once QML's wrapper
  is collected (VeltOS Notepad `attach`).
- A QML property bound to `repeater.itemAt(index)` is not re-evaluated when
  the Repeater creates its delegates later; depend on `repeater.count` too.
- `plasma-apply-colorscheme --accent-color` writes the colours but not
  `AccentColor`; VeltOS Settings records it with kwriteconfig6 so it can be
  read back.
- Plasma shows an applet's right-click menu only through the panel's
  context menu plugin; with VeltOS' locked taskbar it has no actions and
  no applet menu appears (libplasma `ContainmentItem::mousePressEvent`).
  Applets open their own `PlasmaExtras.Menu` (Start's Windows + X menu).
- `plasma-workspace-data` (not `plasma-workspace`) ships the QML of
  Plasma's applets; extract it with `apt-get download` in the builder to
  read the exact upstream text for overrides (`out/upstream/`).
- Qt 6.8's `PdfMultiPageView` calls `forceLayout()` on a scale change
  before its column width (`pageHolderWidth`) has followed the new scale:
  zooming out left the pages off-centre. VeltOS PDF Reader lays the page
  table out again afterwards. Its QML is inside `libQt6PdfQuick.so.6`
  (Qt resources): load the library with `ctypes.CDLL` in a PySide6 script
  and read `:/qt-project.org/imports/QtQuick/Pdf/*.qml` with `QFile`.
- A modal Popup's `Overlay.modal` covers the whole QQuickWindow, including
  the transparent shadow margin of VeltOS' self-drawn windows; use
  `Scrim.qml` (dims the window only).
- Qt Quick `TapHandler`s take only a passive grab by default
  (`gesturePolicy: DragThreshold`): a handler on a row *and* one on the
  button inside it both fire for one tap (Settings' "Change" password
  button toggled its panel open and shut). Give buttons
  `ReleaseWithinBounds` or make the row ignore taps on its control.
- A QML singleton (`Theme.qml`) can read root context properties
  (`backend.textScale`); every object given to an engine that loads such
  QML must have the properties the singleton reads, or "Unable to assign
  [undefined] to double" follows (the Snipping Tool's second backend).
- polkit flows cannot be tested with `vm exec-user` (runuser from the
  guest agent is in no login session, so no agent is found): run the
  command inside the user's systemd manager, `systemd-run
  --machine=velt@.host --user --collect sh -c '...'`. The live system's
  `sudo_on_live.rules` grants everything without a prompt; move it out of
  `/usr/share/polkit-1/rules.d/` (polkitd reloads at once) to see the
  prompt.
- `polkit-agent-helper-1` (setuid): argv[1] = user, first stdin line =
  cookie, then `PAM_PROMPT_ECHO_OFF <text>` lines answered with a plain
  line, `SUCCESS`/`FAILURE` at the end; on success the helper itself tells
  polkitd. One agent per session: KDE's `plasma-polkit-agent.service`
  (static, pulled by plasma-core.target) must be masked
  (`/etc/systemd/user/... -> /dev/null`).
- Qt's portal platform theme (`QT_QPA_PLATFORMTHEME=xdgdesktopportal`,
  package qt6-xdgdesktopportal-platformtheme) wraps the platform's own
  theme (KDE's) and only takes file dialogs (and the colour scheme) from
  the portal. xdg-desktop-portal reads `kde-portals.conf` from
  `/etc/xdg/xdg-desktop-portal/` first and must be restarted after the file
  changes (`systemctl --user restart xdg-desktop-portal`).
- LibreOffice's Qt file picker sends two portal OpenFile requests per
  Ctrl+O; `portal.py` merges identical requests of one window
  (`DUPLICATE_SECONDS`). A portal backend that fails to start makes
  xdg-desktop-portal drop the interface ("No such interface
  org.freedesktop.portal.FileChooser") and Qt silently falls back to
  KDE's dialog: check `busctl --user list | grep portal` and the user
  journal (`journalctl -b _UID=1000`, not `journalctl --user -M`, which
  showed nothing in the VM).
- `/usr/share/applications/mimeinfo.cache` exists only with
  `desktop-file-utils`; GTK programs and Settings' Default apps read it.
  Baloo's tools (`balooctl6`) are in `baloo6`.
- Calamares' slideshow `Slide` has no "current" property: `Presentation`
  toggles each slide's `visible`; start a slide's animations from
  `onVisibleChanged`. Test the QML in the VM with PySide6 and
  `engine.addImportPath('/usr/share/calamares/qml')`.
- deb.debian.org (a CDN) was down to 20 KB/s from the developer host on
  2026-10-21 while ftp.de.debian.org gave 7 MB/s; every package build
  installs its build dependencies with apt, so a slow mirror stalls the
  whole run. `VELTOS_DEBIAN_MIRROR=http://ftp.de.debian.org/debian
  VELTOS_SECURITY_MIRROR=http://ftp.de.debian.org/debian-security
  build/run.sh packages` switches the builder's apt sources (and the ISO
  build's mirrors) for that run. Check with
  `curl -o /dev/null -w '%{speed_download}' URL` before a long build.
- `build-packages.sh` deletes the named packages' old `.deb` files first
  and copies the new ones only when every named package built: one failing
  test leaves `out/packages` without those packages. A full build builds
  every directory under `packages/`; one without `debian/rules` (a draft)
  is skipped since 2026-10-21 (before that it stopped the whole build).
- LibreOffice's recent documents are the `PickList` history in the user
  profile's `registrymodifications.xcu` (ItemList with Title/Filter per
  URL, OrderList with 0 = most recent); its `item`/`node`/`prop`
  elements carry no namespace prefix, only the attributes do
  (`oor:path`, `oor:name`). Templates: `libreoffice -n FILE` makes a
  new document from a template; LibreOffice writes
  `Thumbnails/thumbnail.png` into templates it saves, also from
  `soffice --headless --convert-to ott:writer8_template` (flat .fodt
  written by hand converts fine; `-env:UserInstallation=file:///tmp/x`
  for a throw-away profile). The window title is "<doc> — <ooName>
  <ooSetupFactoryUIName>" (framework TitleHelper); `ooName` is a plain
  string in `Setup/Product`, but the module names are localized
  properties: an unlocalized empty `<value/>` in an .xcd layer does not
  replace them (the title kept "Writer", VM 2026-10-21).
- Testing a program that starts others from `systemd-run --user`
  (`--machine=velt@.host`): the unit's cgroup is killed when the main
  process exits (`KillMode=control-group`), so LibreOffice started by
  the Office start screen died with it. Use `-p KillMode=process` for
  such checks, or start the program from Start (Plasma gives it a scope
  of its own). And `pkill -f '[v]eltos-office'` in a `vm exec` whose
  text also contains `veltos-office ...` elsewhere (a `systemd-run ...
  sh -c 'veltos-office word'` in the same call) kills that shell first:
  keep the pkill in a call of its own, and match the launcher, not the
  product (`[/]usr/bin/veltos-office`; LibreOffice's command line
  contains `/usr/share/veltos-office/templates/...`).
- KDecoration3 exposes no window class to Aurorae's QML
  (`windowClass()` is C++ only; `decoration.client` has caption, icon,
  active, maximized, modal, palette...). VeltOS' Aurorae copy tells the
  Office windows by their caption ("… — VeltOS Office Writer"). KWin
  reads Aurorae's QML at start (sign out and in). In the live VM
  `loginctl terminate-user velt` left SDDM's relogin crashed and the
  console autologin on tty3; `systemctl restart sddm` started a new
  Plasma session (about two minutes).
- LibreOffice's GTK plug-in (`SAL_USE_VCLPLUGIN=gtk3`, package
  libreoffice-gtk3) renders the Tabbed ribbon as a GtkNotebook that GTK
  CSS reaches with type selectors only (`notebook > header tab`;
  GtkBuilder ids are not CSS names, so `#ContextContainer` matches
  nothing); the quick toolbar and menu button beside the tabs are
  VCL-painted, and `window { background }` also paints the document
  canvas and status bar. A per-process theme goes through `GTK_THEME`.
  Tried and dropped for the Office look (2026-10-22).
- LibreOffice's sidebar default visibility is NOT a window-state
  docking window (docking window 10243 does nothing; the toggle records
  no `private:resource` Visible=false), so an .xcd layer cannot hide it
  by default. The Start Center's thumbnail pane colours are
  `Common/Help/StartCenter/StartCenterThumbnails{Background,Text}Color`
  (integers). An .xcd layer overrides writer/calc/impress.xcd only when
  it names them as dependencies (later files win; the default-filter
  override was silently lost before).
- VirtualBox's VMSVGA display (the vmwgfx driver) offers no working
  OpenGL when 3D acceleration is off (Mesa: "VMware: No 3D enabled") and
  Plasma 6 Wayland then stays black (`Applying output config failed`,
  plasmashell's `libEGL: failed to create dri2 screen`). Not a VRAM/mode
  problem (kscreen-doctor showed the output at 1280x800 the whole time).
  The fix is `LIBGL_ALWAYS_SOFTWARE=1` ONLY (Mesa llvmpipe: OpenGL in
  software): KWin's own OpenGL scene then runs on llvmpipe and paints,
  with Task View's window previews and the desktop labels' shadows. The
  two "safer" extras were harmful: `KWIN_COMPOSE=Q` (QPainter) leaves Task
  View's previews black, `QT_QUICK_BACKEND=software` draws grey boxes
  under desktop labels and paints slowly. With 3D acceleration ON the same
  display gives real OpenGL (Mesa svga, renderer "SVGA3D"), so the rule
  (`needs-software-rendering`) is "VirtualBox AND Mesa's GBM renderer is
  llvmpipe" (`eglinfo -B`, no display needed; sysfs and DMI cannot tell 3D
  on from off). 16 MB VRAM works; 128 MB is smoother. (2026-10-22)
- VirtualBox on the developer host can be driven from Git Bash without
  touching the product owner's VMs (`out/vbox/boot-probe*.sh`,
  `diag-probe.sh`, 2026-10-22): `VBoxManage createvm/modifyvm` with the
  owner's settings (`showvminfo <vm> --machinereadable` reads them),
  `startvm --type headless`, `controlvm <vm> screenshotpng FILE` every
  few seconds, `keyboardputscancode 1d 38 3c bc b8 9d` for Ctrl+Alt+F2
  (the live system logs the live user in on tty2, so commands can be typed
  with `keyboardputstring` + `keyboardputscancode 1c 9c` for Enter), and a
  serial port written to a host file (`modifyvm --uart1 0x3F8 4
  --uartmode1 file PATH`; in the guest `sudo chmod 666 /dev/ttyS0` and
  `cmd > /dev/ttyS0`) brings journal text out. Three VMs booting at once
  slow every boot down (a desktop at 4 min instead of 1.5).
- Qt 6.8 `Rectangle` has `topLeftRadius` & co. (per-corner radii); the
  Office start screen's page area uses it against the coloured rail.
- Plasma's folder view (the desktop) cannot write files from QML; commands
  run through `org.kde.plasma.plasma5support`'s `DataSource { engine:
  "executable" }` (`connectSource(command)`, stdout in `onNewData`), as
  VeltOS' plasmoids already do. The override adds a whole QML file to
  Plasma's package (`"add"` in `update-plasma-overrides`).
  `Plasmoid.configuration.sortMode` is KDirModel's column (0 name, 1 size,
  2 modified, 6 type; -1 unsorted), not the config XML's stale comment.
  Learned in the VM (2026-10-22): the desktop's `url` and `resolvedUrl`
  stay `desktop:/` (resolve it from user-dirs.dirs yourself);
  `FolderModel.urlForIndex` is in the qmltypes but "not a function" from
  QML (read the roles through the delegate: `model.fileName`/`model.url`);
  the folder view's `acceptedButtons` leaves the right button to the
  containment on empty desktop space (its menu opened, not ours) until
  the override adds `Qt.RightButton` there; a new item becomes the
  current delegate only after the GridView has made it, so select it and
  wait until `gridView.currentItem` is that delegate before `rename()`
  (an immediate rename() edited the previously current item); a
  `PlasmaExtras.MenuItem` has no default property, a submenu is declared
  as `readonly property PlasmaExtras.Menu submenu: PlasmaExtras.Menu {
  visualParent: item.action ... }` (Plasma's task manager does the same).
- plasmashell 6.3 loads the on-screen display (volume, brightness) from
  the desktop *shell* package (`plasma/shells/org.kde.plasma.desktop/
  contents/osd/`), not from the global theme's `contents/osd` (a copy
  there is never read). KWin places OSD windows with their centre at two
  thirds of the screen (`Placement::placeOnScreenDisplay`); a bottom
  flyout is a window tall enough for its bottom edge to end above the
  taskbar (measure with a KWin script: `workspace.windowAdded` +
  `w.onScreenDisplay`, `w.frameGeometry`). `Screen.height` is 0 while
  the dialog's item is first sized; read `dialog.screen`.
- `kioclient --interactive remove trash:/` returns 0 and leaves the trash
  as it was; `ktrash6 --empty` empties it.
- A Plasma theme with its own `colors` file pins plasmashell's colours
  (Kirigami.Theme, and even `SystemPalette` there) to that file: the
  user's accent never reached the taskbar or Start. The VeltOS themes
  have none since 2026-10-22. After `plasma-apply-colorscheme
  --accent-color` plasmashell keeps the old colours until it hears
  `dbus-send --session --type=signal /KGlobalSettings
  org.kde.KGlobalSettings.notifyChange int32:0 int32:0` (PaletteChanged).
- The box around a taskbar applet while its popup is open is Plasma's
  `expandedItem` (`widgets/tabbar` active tab) in the shell's
  `applet/CompactApplet.qml`; the box around the focused applet is the
  "Panel Focus Indicator" in `views/Panel.qml` (shown whenever the panel
  window is active, also after a mouse click). Both are in the shell
  package override.
- Qt window flags (`Qt.Dialog`, `WindowCloseButtonHint`) do not reach
  KWin on Wayland: a parentless dialog still gets minimize and maximize.
  A fixed size (minimum = maximum) disables maximize; minimize stays.
- A Qt Quick `ScrollView` with `contentWidth: availableWidth` and a child
  bound to its width loops ("Binding loop detected for rightPadding"
  through the scroll bar); use a `Flickable` with an explicit
  `contentHeight`.
- A user's `PATH` has no `/usr/sbin`: `shutil.which("mkfs.ntfs")` finds
  nothing in a session (Disk Management offered no file system); pass
  `path="/usr/sbin:/sbin:..."`. UDisks2 runs the mkfs programs as root
  anyway.
- The desktop's Recycle Bin launcher keeps a fixed old date (@2) for the
  date order; `touch` without a date moved it to the end of the desktop.
  `trash-icon` alternates @2 / @2.5 (still before This PC's @3).
- Qt Quick `ListView` rows overlapped in the search window when the
  model's rows changed (results arriving); a `Column` + `Repeater` cannot
  overlap. `Kirigami.Icon`'s `color` takes no `undefined` ("Unable to
  assign [undefined] to QColor"); "transparent" is its "no colour".
- QMP key names (`vm do key:`): `esc`, `ret`, `meta_l`; `escape` is
  refused.
- A QML engine deleted with `deleteLater()` after a test function
  returned re-reads its bindings from a dead backend ("Cannot call method
  'text' of null"): flush the deferred delete inside the test
  (`QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)`).
- The desktop `.desktop` launchers (`/usr/share/veltos/desktop`) all come
  back at sign-in now (Store included, product owner 2026-10-22); the
  session fixup writes the desktop's date order once (`veltosDateOrder`)
  so "Sort by" in the desktop's menu sticks.
- LibreOffice configuration: VeltOS adds `share/registry/veltos-office.xcd`
  (all `.xcd` files there are read; users' changes win). A toolbar mode is
  selected by its `CommandArg` (`notebookbar.ui` = Tabbed), not by its
  node name; properties of extensible groups (VCL `DefaultFonts`) need
  `oor:type` or LibreOffice ends at start. Test a layer quickly with
  `soffice -env:UserInstallation=file:///tmp/p --headless
  --terminate_after_init`. LibreOffice is single-instance: kill
  `soffice.bin` (`pkill -9 -x soffice.bin`) and delete the profile before
  checking first-start defaults.
- Plasma sources `/etc/xdg/plasma-workspace/env/*.sh` in name order, and
  `99-*.sh` sorts *before* `veltos-session.sh` (digits before letters): a
  later file cannot `unset` what the session script exports, so two
  renderer experiments in a VM silently ran with the unchanged variables
  (2026-10-22). To test a changed session environment, edit
  `veltos-session.sh` itself in the VM (`sudo sed -i`), then `systemctl
  restart sddm`; adding variables in an earlier file is fine. After the
  restart send no VT keystrokes (SDDM activates its VT itself) and force
  real repaints (Start, Win+Tab) before trusting a screenshot: VirtualBox's
  framebuffer keeps the last text console when a compositor never paints.
- `QT_QPA_PLATFORMTHEME=xdgdesktopportal` in the session environment
  reaches Plasma's own services, and a Qt program starting with that
  theme asks the portal (colour scheme) and blocks up to 25 s when it
  does not answer; at session start it cannot (its backends are Wayland
  clients of the KWin that is asking). kwin, kcminit, ksplash, kded6,
  ksmserver and plasmashell each waited 25 s: plasmashell after ~95 s
  instead of ~18 s from the 2026-10-21 evening ISO until 2026-10-22.
  Plasma's user services get `Environment=QT_QPA_PLATFORMTHEME=kde`
  drop-ins (`PLASMA_SERVICES`, veltos-desktop) — all but plasmashell:
  programs started from Start inherit plasmashell's environment (KIO's
  launcher hands it to their transient unit), so a drop-in there takes
  the portal theme, and the Windows 11 file dialogs, away from every
  program (LibreOffice got KDE's dialog, 2026-10-22). What found it: the
  boot-test reports' "plasmashell running ... after N s" across ISOs, and
  in a VM `systemd-analyze --user blame` / `critical-chain
  plasma-workspace.target` and `journalctl -b | grep -iE
  'WaitForName|timed out|Failed to start'`. Compare a timing against the
  previous ISOs' reports before blaming the renderer.
- `build/run.sh vm stop` is forwarded to `vmctl.py` inside the `veltos-vm`
  container and leaves the container itself running (it still showed "Up
  15 hours" afterwards, with the QEMU guest's 8 GB reserved; 2026-10-22).
  When done with the dev VM, remove it: `docker rm -f veltos-vm && docker
  volume rm veltos-vm`. Check `docker ps` before long VirtualBox or QEMU
  test runs; a forgotten dev VM slows every other VM on the host.
- `build/run.sh iso` rebuilds every package inside the build volume from
  the current source and copies them into the image; `out/packages` is
  written only by `build/run.sh packages`. So `out/packages` can be older
  than the ISO (18 drop-ins there, 25 in the ISO, 2026-10-22). To know
  what an ISO contains, list its live filesystem in the builder:
  `xorriso -osirrox on -indev ISO -extract /live/filesystem.squashfs
  /tmp/fs.squashfs && unsquashfs -l /tmp/fs.squashfs | grep ...`
  (`unsquashfs -q -f -d /tmp/x /tmp/fs.squashfs PATH...` extracts single
  files). Docker Desktop's bind mount showed the container the edited
  source at once; it was not stale.
- VirtualBox: `startvm` of a VM created under a name that was just
  unregistered (or that is selected in the owner's VirtualBox window)
  can fail with "already locked by a session"; the script went on,
  every `screenshotpng` failed, and the old files of the same name's
  output directory passed for results (2026-10-22). Use a fresh name per
  run (`veltos-chk-off-HHMM`), check `showvminfo --machinereadable` for
  `VMState="running"` right after `startvm`, and treat a screenshot's
  file time, not only its size, as evidence.
- Never edit a bash script while it is running: bash reads the file as
  it goes, so the running `out/vbox/verify-chain.sh` and `verify-iso.sh`
  died with "syntax error near unexpected token" and "unexpected EOF"
  the moment they were edited (2026-10-22), the QEMU step never ran and
  the jobs gated on their "done" line waited forever. Copy a script to a
  new name before changing it, or wait for the run to end.
- Calamares 3.3.14 QML steps (`welcomeq`, `localeq`, `keyboardq`,
  `usersq`, `finishedq`; `qmlSearch: both` loads
  `<branding>/<module>.qml`): every step has its own QML engine and only
  the slideshow is retranslated when the language changes (read texts
  when the page is shown, `VeltPage.t()`); `KeyboardQmlViewStep` never
  calls the page's `onActivate` (the layout list stayed empty: VeltPage
  emits `activated()` when its window becomes visible); the installer
  runs with `-style kvantum`, so `import QtQuick.Controls` looked for a
  QML style "kvantum" and the page did not load: use
  `QtQuick.Controls.Basic` and versionless imports (`uniformCellSizes`
  is not in `QtQuick.Layouts 1.15`). After a failed job the queue
  emits "failed" and then "finished": the finished page gets
  `config.failed`. The users module ignores "nonempty"; libpwquality
  wants 6 characters and no dictionary word (VeltOS: `minLength: 1`
  without libpwquality, as Windows allows any password).
- Calamares' error dialog has no parent, so the branding style sheet
  (set on the main window) does not reach it; `install-veltos` passes
  Qt's own `-stylesheet FILE`. In that QSS a namespaced class is written
  with `--` (`Calamares--Widgets--ClickableLabel`), message box buttons
  go right with `QDialogButtonBox { qproperty-centerButtons: false; }`,
  and a `font-size` on `qt_msgbox_label` broke QMessageBox's size
  calculation (the text was cut off).
- xdg-desktop-portal 1.20 uses the GTK backend "as a last resort" for an
  interface no configured backend has (Lockdown: KDE's has none); the
  GTK backend waits for `graphical-session.target`, which made sign-in
  take 25 s more. `kde-portals.conf` says `Lockdown=none` and
  `Settings=kde`. plasmashell started with the portal platform theme
  waited for the KDE portal, which waits for plasmashell: its unit
  starts it with `-platformtheme kde` (the argument wins over
  `QT_QPA_PLATFORMTHEME`, which programs started from Start still
  inherit).
- AppArmor's boot-time cache directory is named after a hash of the
  kernel's feature set; without a cache every boot compiled all profiles
  (11 s). `aa-features-abi -x -w FILE` records the features in a VM;
  `apparmor_parser --features-file FILE --skip-kernel-load --write-cache
  --cache-loc /var/cache/apparmor /etc/apparmor.d/` builds the same
  directory in the image (hook 8500). Cache files get the newest source's
  mtime and squashfs keeps mtimes, so the cache stays valid.
- Thunderbird (VeltOS Mail until 2026-10-23; now its own app): a user style sheet with a default
  `@namespace` (XUL) does not match HTML elements such as
  `#unifiedToolbarContainer` (mail-header.css did nothing); generated
  `file://` URLs must use "/" (`Path.as_posix()`: a file generated on
  Windows had backslashes and no Mail style sheet loaded). Its settings
  store (xulstore) can be preset from autoconfig at "final-ui-startup":
  the toolbar (`messenger.xhtml` / `unifiedToolbar` / `state`), the
  message header (`messageHeader` / `layout`) and any persisted XUL
  attribute (the compose menu bar's `autohide`). Sender names in the
  message list are cached in each folder's `.msf`: a changed
  `mail.addressDisplayFormat` shows only after the index is rebuilt
  (delete the `.msf` while Thunderbird is closed) or in a new profile. The
  compose window's hidden menu bar keeps its padding and its labels
  peeked out (mail.css sets it to 0). Read Thunderbird's own markup and
  CSS in the VM with Python's `zipfile` on `/usr/lib/thunderbird/omni.ja`.
  `pkill -x thunderbird` stops it.
- QML: a property named `state` clashes with Item's; a property name
  must start with a lower-case letter (the devices flyout did not load);
  `visible: a && b` with an undefined `a` assigns undefined to a bool
  ("Unable to assign [undefined] to bool"): write `!!a && b`.
- Fluent names its icons the other way round: `view-more-symbolic` is the
  horizontal "…" (Windows 11's "More options").
- A package's offscreen window test must not need files from other
  packages (`/usr/share/icons/...` is empty in the build container): the
  recovery window's logo is the package's own copy (`branding/`, checked
  by `tests/repo`) given to QML by the backend, which the test points at
  the source tree. SVG pictures need `qt6-svg-plugins` in
  Build-Depends too ("Unsupported image format").
- `vm do type:` sends US key codes through QMP: "@" is refused ("does
  not accept value '@'") and the guest's Turkish layout turns some keys
  into other letters (type "i" as `key:apostrophe` on a Turkish Q
  console). The installed dev VM locks its session when idle; typed text
  then goes into the lock screen's password field. `vm do` clicks are in
  1920x1080 coordinates, scaled to whatever mode the guest shows (the
  recovery start's frame buffer is 1024x768).
- Debian 13's kernel has no simpledrm (`CONFIG_DRM_SIMPLEDRM` unset): with
  `nomodeset` there is only efifb/vesafb (`/dev/fb0`) and no `/dev/dri`,
  so KWin, the Wayland sign-in screen and Plasma cannot start (black
  screen). Xorg with the fbdev driver works (veltos-recovery's
  `safe-graphics` switches SDDM to X11 for such starts).
- Qt's `linuxfb` puts its console in graphics mode (KD_GRAPHICS), and Linux
  ignores every console switch then (`openvt -s -w` waited for ever,
  `fgconsole` stayed 1): end the Qt program before showing a text console.
  A console's font comes from console-setup; one opened later by `openvt`
  had the kernel's font without "ı"/"İ" until `setupcon --current-tty`.
  Debian's `login` gives up after 60 s without input.
- `chmod` follows symlinks: Plasma's `/usr/bin/kinfocenter` is a symlink
  to `systemsettings`, so after VeltOS diverted both, `chmod 0700
  kinfocenter.kde` locked VeltOS' own redirect and `systemsettings` said
  "Permission denied" (VM, 2026-10-23). Test `[ -L ]` before changing
  modes in maintainer scripts.
- polkit keeps an `auth_admin_keep` answer only for the process that got
  it: every `gdbus call` is a new process, so two AccountsService calls
  asked for the password twice. Make related privileged calls from one
  process (`veltos_settings/admin_calls.py`, Gio with
  `ALLOW_INTERACTIVE_AUTHORIZATION`).
- Qt Quick layouts: a `ColumnLayout`/`RowLayout` whose children have
  `Layout.fillWidth: true` expands itself, whatever its
  `Layout.preferredWidth`; give a fixed side pane `Layout.fillWidth:
  false` and a `Layout.maximumWidth` (Calendar's pane took the whole
  window). Offscreen tests: `grabWindow()` lays the window out, then
  check item widths.
- Do not edit files under `packages/` while `build/run.sh packages` or
  `iso` runs: each package is copied with `tar` when its turn comes, and a
  README saved at that moment stopped the ISO build ("tar: .: file
  changed as we read it", 2026-10-23). Edits to packages built later are
  picked up, edits to packages already built are not.
- PySide6 returns `engine.rootObjects()[0]` as a plain `QWindow` (no
  `contentItem()`) unless `PySide6.QtQuick` was imported first. Repeater
  delegates and items declared in a `Window` are found by walking
  `contentItem().childItems()`, not with `findChild`.
- Qt's `QLocale` has no two-letter weekday format (Long "Pazartesi",
  Short "Pzt", Narrow "P"): cutting the short Turkish names to two letters
  labelled Monday "Pz", which Turkish readers take for Pazar (Sunday).
  Use the CLDR two-letter forms the taskbar clock uses ("Pt Sa Ça Pe Cu
  Ct Pa"; Calendar `TWO_LETTER_DAYS`).
- Calamares runs through pkexec: its jobs inherit `PKEXEC_UID`, and a
  helper that refuses pkexec callers refuses the installer too (the
  boot-resolution job failed every installation at its end, VirtualBox
  2026-10-23; unit tests had passed). Run every installer job in a real
  installation before shipping it.
- pkexec clears the environment (`QT_QUICK_BACKEND` too); `pkexec env
  VAR=… calamares` lost the display, because only an action with
  `org.freedesktop.policykit.exec.allow_gui` keeps DISPLAY. Calamares is
  started by `start-calamares` with its own policy (calamares-settings-
  veltos). Calamares ignores arguments that are not options; QML reads
  them with `Qt.application.arguments` (VeltTheme.js).
- Calamares applies the branding's `stylesheet.qss` to its main window
  itself, besides Qt's `-stylesheet` for the other windows: a different
  sheet passed with `-stylesheet` left the main window (and its C++
  partition page) in the branding sheet's colours.
- Calamares loads the slideshow QML when it starts and its first slide is
  `visible` from then on: an endless animation there redrew the whole
  installer 60 times a second behind every page (140 % CPU in VirtualBox
  without 3D). In Calamares QML, run endless animations only where they
  are shown (`activatedInCalamares`, the page's window being visible).
  In a QML welcome page `config.isNextEnabled` stays false; the Next
  button's state is `ViewManager.nextEnabled`.
- Root's QML cache (`/root/.cache/calamares/qmlcache`) kept an old page
  after `dpkg -i` of a rebuilt package (same file times); delete it before
  checking installer QML in a VM.
- live-config runs every component in `/usr/lib/live/config/` with the
  boot option `components` (~90 ms each warm, 11 s of a VirtualBox live
  start); `nocomponents=a,b` leaves some out (auto/config). The live image
  had no `/etc/.updated`, so ldconfig.service rebuilt the linker cache at
  every live start (10.6 s in VirtualBox): hook 8900 stamps it.
- live-build: `config/rootfs/excludes` (mksquashfs wildcards, relative
  paths) leaves files out of the squashfs only; `MKSQUASHFS_OPTIONS` in
  the environment of `lb build` reaches mksquashfs (block size);
  `config/includes.chroot_before_packages/` is copied before the package
  installation (dpkg `path-exclude` files there take effect for every
  package but debootstrap's).
- Debian 13's Wine is not a WoW64 build (its amd64 package has no
  i386-windows DLLs): 32-bit Windows programs need wine32:i386 and the
  i386 libraries. Its PE DLLs carry DWARF debug information (more than
  half their size); `strip --strip-debug` keeps the "Wine builtin DLL"
  mark (veltos-winapps strips them).
- In VirtualBox the product owner opens throw-away VMs in their window
  (a `VBoxUI.log` appears within seconds) and may click through them
  themselves; ask before driving such a VM (`VBOX_OWNER_WATCHING=NAME`
  lets `out/vbox` scripts send input after they said so), and expect
  their clicks between yours.
- live-tools diverts `update-initramfs` to a wrapper that does nothing
  while the system runs from a live medium (`boot=live` in
  `/proc/cmdline`, read-only medium: "I: update-initramfs is disabled"),
  and inside Calamares' target chroot `/proc/cmdline` is the live one. So
  an installer job that makes an initramfs before live-tools is removed
  makes nothing. Since the ISO leaves the live initramfs out of its file
  system, installed systems then stopped at "Unable to mount root fs"
  (QEMU, 2026-10-23); the live packages are removed first now and the
  `boot-check` job stops such an installation. Boot an installed system
  after any change to the image's contents or the installer's jobs.
- VirtualBox 7.2 on a host with Hyper-V active (Docker Desktop/WSL2) runs
  VMs in NEM mode, and there VMs stopped for 60-232 s at a time until a
  key was pressed (VBox.log: "TM: Giving up catch-up attempt", "Guest
  seems to be unresponsive"), even in GRUB's menu before Linux ran
  (2026-10-23; upstream: github.com/VirtualBox/virtualbox/issues/722).
  Grep VBox.log for those lines before trusting a VirtualBox timing,
  "stutter" or a screenshot (a stalled VM's screenshots repeat byte for
  byte); measure in QEMU.
- Kvantum's combo box lists (with `combo_menu`, as in VeltOS' theme) are
  translucent menus: it reserves its shadow in `SC_ComboBoxListBoxPopup`
  (the list opened 15 px up and left, over its own box) and gives the list
  a transparent style sheet when it finds Qt's `QComboMenuDelegate`; the
  style sheet's `combobox-popup: 0` alone did not help. The installer's
  style keeps Kvantum off `QComboBoxPrivateContainer`/`QComboBoxListView`,
  sets a styled delegate first and returns the box's rect for the list.
- Calamares' partition pictures (PartitionBarsView, PartitionLabelsView,
  PartitionSplitterWidget) are painted in C++ with fixed colours; a style
  can take over their paint events by class name, but the splitter must
  paint first (it sets its resize handle position while painting). Its
  `partitionResized(QString,qint64,qint64)` signal can be connected by
  name without Calamares' headers. Calamares' Turkish translation writes
  its MiB values as "MB". PySide6 classes carry their Python class name
  as meta-object name, so stand-ins named like Calamares' classes test
  such a plugin offscreen. Start a dark installer in the VM with
  `systemd-run --machine=velt@.host --user --collect -p KillMode=process
  sh -c 'pkexec /usr/libexec/veltos-installer/start-calamares --dark
  --accent "#E81123"'` (pkexec refuses when its parent has exited).
- Testing Wi-Fi and Bluetooth UI without hardware (dev VM): `modprobe
  mac80211_hwsim radios=3`, `nmcli device set wlan1 managed no`, hostapd
  on wlan1/wlan2 and dnsmasq for DHCP (`out/vm/wifisim.sh`; without DHCP
  NetworkManager stays "activating"; turning Wi-Fi off also stops the
  simulated access points). `btvirt -l2` (bluez-test-tools, hci_vhci)
  gives two controllers; make the second discoverable with bluetoothctl
  (`out/vm/btsim.sh`). Both are local, so they also see each other as
  paired/connected devices and a disconnect is undone at once.
- plasma-nm's `NetworkModel.DelayModelUpdatesRole` freezes a row's data
  (state included) until it is cleared: set it only while a key is typed.
  A Quick Settings page is destroyed when the flyout closes (clicking a
  notification closes it): keep long-running calls (Bluetooth pairing) in
  the applet's root, not in the page.
- KWin runs `/usr/lib/x86_64-linux-gnu/libexec/kwin_killer_helper` when a
  window that does not answer KWin's ping is closed (Alt+F4 or the
  taskbar; a self-drawn window's own close button cannot ask a frozen
  program). Reproduce with `kill -STOP <pid>` and Alt+F4. A Qt Window whose
  height and minimum/maximum height are bound to each other loops; bind all
  of them to one computed property.
- Crashes reach the user through DrKonqi's chain: systemd-coredump ->
  `drkonqi-coredump-processor@` (system) -> JSON on
  `/run/user/UID/drkonqi-coredump-launcher` (SOCK_SEQPACKET, Accept=yes)
  -> `drkonqi-coredump-launcher@.service`, whose program VeltOS replaces
  (`crash-notice`). A program started from such a service is killed with
  the unit when the service exits: wait for it (kioclient). Test with
  `kill -SEGV` on a program started through `kioclient exec <desktop
  file>` (it then runs in an `app-<id>-<pid>.scope`).
- LibreOffice opens an empty (0-byte) `.docx`/`.pptx`/`.xlsx` as a new
  document of that type and saves it in that format without asking, but
  Calc's window for an empty `.xlsx` had no app icon (title bar,
  taskbar); VeltOS' new Excel worksheets are small workbooks
  (veltos-office `blank.py`). Qt types empty files by their extension,
  GIO as `application/x-zerosize`.
- The `org.kde.desktop` style's TextArea/TextField open KDE's own text
  menu (Spell checking, Undo, Cut ...) on the right button (a TapHandler
  with a 1 ms long-press threshold) and on the Menu key; an app showing
  its own menu there gets two menus (Notepad did). Use
  `QtQuick.Templates`' TextArea for such text (set `implicitWidth` /
  `implicitHeight` as the styles do).
- A Popup menu whose entries use a plain `TapHandler` (passive grab) lets
  the tap through to the item under the menu as well (File Explorer's
  New > Word Document also opened Home in the navigation pane). Menu
  entries take `gesturePolicy: TapHandler.ReleaseWithinBounds`.
- Wine's menu builder only adds Linux menu entries: after a Windows
  uninstaller ran, `~/.local/share/applications/wine/...`, the
  `applications-merged/wine-*.menu` files, `.directory` files and icons
  stay, and Start keeps the program. VeltOS removes entries whose `.lnk`
  or ProgID is gone (`shortcuts.remove_stale`). Their Exec lines quote the
  Windows path twice (desktop-file escaping on top of shell quoting: four
  backslashes per separator in the file).
- Wine's Start shortcuts have spaces in their file names ("7-Zip File
  Manager.desktop"): pipe file lists with `-print0`/`-0` or use `find
  -exec`, never plain `xargs` (the Windows program test reported a
  missing shortcut that existed).
- VeltOS Mail (2026-10-24): Qt WebEngine must be initialised
  (`QtWebEngineQuick.initialize()`) before the first QCoreApplication of a
  process, also in tests: one test module that made a QCoreApplication
  first left the next module's WebEngine window aborting ("core dumped");
  the tests share `tests/qtapp.py`. As root (package builds) Chromium needs
  `QTWEBENGINE_DISABLE_SANDBOX=1`; offscreen WebEngine then works.
- Python 3.13's `email.utils.getaddresses` is strict: one empty field in
  the list (`["a@b.c", "", ""]`) returns no address at all (Mail sent to
  nobody); pass only non-empty fields. With `policy.compat32`, a header with
  raw 8-bit bytes (UTF-8 without RFC 2047 words, common) comes back as an
  `email.header.Header` with charset `unknown-8bit`, and `str()` of it has
  replacement characters: decode its chunks yourself (`mime.decode`).
- A QML ListView whose model is reset deletes the model's per-row QObject
  wrappers while delegate bindings still read them ("Cannot read property
  'label' of null", dozens per reset). Rows that need many roles read a
  plain object instead: `readonly property var row: { model.revision;
  return model.get(index); }` (VeltOS Mail's MessageModel).
- The developer host's clock was 3 hours behind (Windows time service not
  synchronised, source "Local CMOS Clock", 2026-10-23): apt in the builder
  refused freshly signed Debian Release files ("Not live until ..."). Until
  the clock is right, build with a snapshot that is older than the host's
  clock: `VELTOS_DEBIAN_MIRROR=http://snapshot.debian.org/archive/debian/
  20261023T120000Z VELTOS_SECURITY_MIRROR=http://snapshot.debian.org/
  archive/debian-security/20261023T120000Z build/run.sh packages ...`.
- Testing VeltOS Mail against real servers in the dev VM:
  `out/vm/mailseed.py` (Dovecot IMAP on localhost:993 with its self-signed
  certificate added to the VM's trust store, sample mail, the account) and
  `out/vm/mailsmtp.sh` (Postfix with STARTTLS on 587 and Dovecot's SASL,
  `ayse@`/`ali@example.com` aliased to velt). Dev VM only.
