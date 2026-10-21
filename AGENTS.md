# AGENTS.md — Working on VeltOS

This file is for AI coding agents and new human contributors. It contains
the project rules, where things are, and how to continue the work. Read it
fully before changing anything, then read `docs/status.md` (what is done)
and `docs/architecture.md` (why it is built this way).

## Project in one paragraph

VeltOS ("Your PC. No Limits.") is a Debian 13 "trixie" based desktop
distribution with a Windows 11-inspired KDE Plasma desktop, hardware-aware
driver management and (planned) strong Windows application and game
compatibility through Wine/Proton. It is built incrementally as a real,
installable OS with reproducible builds and automated tests. The product
owner sets priorities; agents act as the engineering team.

## Rules (non-negotiable)

1. **Language.** Everything in the repository is English: code, comments,
   docs, commit messages, package descriptions. (The product owner may talk
   to agents in Turkish; answer in the language you are addressed in, but
   write the repo in English.)
2. **Working software first.** A bootable, installable system beats
   ambitious unimplemented features. Work in small, verifiable increments.
3. **Never fabricate results.** Do not claim a build passed, a test ran,
   hardware works or a feature is complete unless you observed it. Report
   failures with their output. Mark anything untested as untested.
4. **No silent mocks.** Never replace a real implementation with a mock or
   stub without labelling it clearly in code and in `docs/status.md`.
5. **Reuse, don't rewrite.** Use Debian, KDE, Mesa, Wine/Proton and other
   mature upstream components. VeltOS code goes into small, testable
   packages under `packages/`. Do not fork Plasma, the kernel or Wine.
6. **Verify upstream facts.** Check package names/versions against
   packages.debian.org or `apt-cache policy` in the builder container and
   read upstream docs; do not rely on memory. Record what you verified.
7. **Lightweight by default.** Every new service, daemon or autostart
   entry needs a reason; measure RAM/CPU/boot impact (see `docs/testing.md`).
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
    `docs/architecture.md` with alternatives and trade-offs.
12. **Keep the handoff current.** After any meaningful change update
    `docs/status.md`, add an entry to `docs/development-log.md`, and keep
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
| `packages/veltos-desktop/` | Global themes (Light default), Windows 11 style taskbar + VeltOS Start menu, Windows 11 look derived from Fluent-kde (Kvantum style, Aurorae frames, Plasma theme, colour schemes), Windows-familiar app names (menus and window titles), File Explorer defaults, sign-in screen (SDDM theme), generated wallpapers (Bloom default, Flow, Glow, Lake), splash, Ctrl+Alt+Del screen, locked taskbar and its menus, Plasma overrides (toasts, tray flyouts, taskbar menus), master logo |
| `packages/veltos-settings/` | VeltOS Settings: Windows 11 style settings app (PySide6/QML), every page built in (network, devices, display, sound, power, notifications, personalization, apps, accounts, time & language, accessibility, privacy); diverts `systemsettings`/`kcmshell6`/`kinfocenter` to itself so KDE's settings window never opens |
| `packages/veltos-explorer/` | VeltOS File Explorer: Windows 11 File Explorer layout (tabs in the title bar, command bar, Home, This PC, Recycle Bin), file operations through KIO (`kioclient`); default for folders. Also the Windows 11 file dialog of every program (`--pick`; `--portal` = the xdg-desktop-portal FileChooser backend) and the "Select an app to open this file" window (`--open-with`) |
| `packages/veltos-auth/` | VeltOS authentication prompt: polkit agent (GLib) + a window in the layout of Windows 11's User Account Control (PySide6/QML); the password goes through polkit's own helper; KDE's agent service masked |
| `packages/veltos-clock/` | VeltOS Clock: Windows 11 Clock (Focus sessions, Timer, Alarm, Stopwatch, World clock); `veltos-clock-agent` rings alarms and timers while the app is closed |
| `packages/veltos-taskmanager/` | VeltOS Task Manager: Windows 11 Task Manager layout (Processes, Performance, Startup apps), psutil; Ctrl+Shift+Esc |
| `packages/veltos-calculator/` | VeltOS Calculator: Windows 11 Calculator (Standard and Scientific modes, memory, history, keep on top, app theme); decimal engine in `engine.py` |
| `packages/veltos-notepad/` | VeltOS Notepad: Windows 11 Notepad layout (tabs in the title bar, File/Edit/View, find and replace, status bar with encoding and line ending), keeps encodings/line endings, restores unsaved tabs; default for text files |
| `packages/veltos-photos/` | VeltOS Photos: Windows 11 Photos (gallery by month, favorites, folders, viewer with filmstrip and file information, Edit image with crop/rotate/adjust via Pillow, slideshow); default for pictures |
| `packages/veltos-media/` | VeltOS Media Player: Windows 11 Media Player (music library with tags/covers via mutagen, video library, play queue with shuffle/repeat, playlists, player bar, now playing) on Qt Multimedia; default for audio and video |
| `packages/veltos-pdf/` | VeltOS PDF Reader: modern PDF reader layout (Home with recent files, tabs, search, thumbnails, bookmarks, zoom/fit, read mode, properties, passwords, printing) on QtQuick Pdf; replaces Okular, default for PDF |
| `packages/veltos-office/` | VeltOS Office: Microsoft 365's start screen (Home / New / Open / Account / Options, the app's colour, Windows 11 animations; PySide6/QML, `veltos-office word|sheet|slides`) in front of LibreOffice Writer/Calc/Impress (Debian), VeltOS' own templates (built from flat ODF by LibreOffice at package build time) and a configuration layer for Windows users (Tabbed interface, Colibre icons, MS formats by default, Carlito font, "VeltOS Office" in titles, no bars); app names, icons and defaults live in veltos-desktop/veltos-fluent-icons, the coloured title bars in veltos-desktop's Aurorae change |
| `packages/veltos-archive/` | VeltOS Archive: WinRAR's layout (toolbar, archive list, Extract To, Add, Test, passwords) on 7-Zip (+ 7zip-rar) and bsdtar; File Explorer's extract/compress |
| `packages/veltos-camera/` | VeltOS Camera: Windows 11 Camera layout (photo, video, timer, framing grid, Camera Roll) on Qt Multimedia (FFmpeg backend, V4L2) |
| `packages/veltos-snip/` | VeltOS Snipping Tool: Print Screen / Win+Shift+S overlay (rectangle, window, full screen, freeform), clipboard + Pictures/Screenshots + notification, markup window; captures through Spectacle in the background |
| `packages/veltos-store/` | VeltOS Store: Microsoft Store layout (Home, Apps, Gaming, Library, app pages) on AppStream (gir1.2-appstream-1.0) and PackageKit (pkcon); replaces Discover |
| `packages/veltos-fluent-icons/` | Fluent icons/cursors from a pinned upstream release (Microsoft logos removed), VeltOS "This PC" and Recycle Bin icons |
| `packages/veltos-boot/` | Plymouth splash (+ Plymouth defaults diversion), GRUB theme and fonts, boot defaults, SDDM-after-Plymouth ordering, disk-encryption password screen (initramfs hook) |
| `packages/calamares-settings-veltos/` | VeltOS installer (Calamares) configuration and branding, partition layout (BitLocker-like encryption), installer jobs, live welcome window (Try/Install), live session settings |
| `packages/veltos-winapps/` | `veltos-run`: double-click `.exe`/`.msi`/`.bat`/`.cmd` → install/open via Wine, in a Windows 11 App Installer style window |
| `packages/veltos-wine-addons/` | Wine Mono/Gecko (pinned, verified) |
| `tests/boot/vmlib.py` | Shared QEMU/QMP/guest-agent helpers |
| `tests/boot/vmtest.py` | QEMU/KVM boot test with screenshots, checks and measurements (`build/run.sh test`) |
| `tests/boot/vmpreview.py` | Dev aid: install fresh `.deb`s into a live VM and screenshot a scripted interaction (`build/run.sh preview`) |
| `tests/boot/winapps_vmtest.py` | Installs a real Windows program through `veltos-run` in a VM (`build/run.sh test-winapps`) |
| `tests/repo/` | Repository-wide checks (logo copies, line endings) |
| `tests/results/` | Committed test evidence for milestones |
| `docs/` | Architecture, build guide, testing, status, development log |
| `out/` | Build outputs (ISO, logs, test runs) — git-ignored |

## How to continue

1. Read `docs/status.md`; pick the first item under "Next steps" unless the
   product owner says otherwise.
2. Make sure the environment works: `build/run.sh packages` (fast) and, for
   image changes, `build/run.sh iso` followed by `build/run.sh test`.
3. Change the smallest thing that delivers the step. Add or update tests.
4. Build and test for real. Read the report (`out/test-results/.../report.md`)
   and look at the screenshots.
5. Update `docs/status.md`, `docs/development-log.md`, README files and,
   for design decisions, `docs/architecture.md`.
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
  Every VeltOS QML app sets `QML_DISABLE_DISK_CACHE=1`.
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
- Qt 6.8 `Rectangle` has `topLeftRadius` & co. (per-corner radii); the
  Office start screen's page area uses it against the coloured rail.
- LibreOffice configuration: VeltOS adds `share/registry/veltos-office.xcd`
  (all `.xcd` files there are read; users' changes win). A toolbar mode is
  selected by its `CommandArg` (`notebookbar.ui` = Tabbed), not by its
  node name; properties of extensible groups (VCL `DefaultFonts`) need
  `oor:type` or LibreOffice ends at start. Test a layer quickly with
  `soffice -env:UserInstallation=file:///tmp/p --headless
  --terminate_after_init`. LibreOffice is single-instance: kill
  `soffice.bin` (`pkill -9 -x soffice.bin`) and delete the profile before
  checking first-start defaults.
