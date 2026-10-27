# veltos-store

Added 2026-10-21: a failed install says why (permission not given, not in
the catalogue, download failed, another installation running, or
PackageKit's own message; `packages.failure_key`), and old or missing
package lists are refreshed (`pkcon refresh`) before an install.

VeltOS Store: apps and games for VeltOS in the layout of the Windows 11
Microsoft Store (PySide6 + QML). It replaces KDE's Discover in Start, the
taskbar and Settings; Discover stays installed but hidden.

## What it does

- **Home**: a featured banner (changes every few seconds), "Essential
  apps", "Productivity", "Create and edit", "Top free games".
- **Apps** (with category chips: Productivity, Photo & design, Music &
  video, Internet & social, Developer tools, Education, Utilities & tools)
  and **Gaming**: tiles with icon, name, category and "Free" / "Installed".
- **Search** box at the top (names first, then descriptions and keywords).
- **App page**: icon, name, publisher, Install / Open / Uninstall with
  progress, screenshots, description, publisher, category, package,
  licence, website.
- **Library**: "Get updates" / "Update all" and the installed apps with
  Open and Uninstall. `veltos-store --updates` opens it and checks for
  updates (Settings > VeltOS Update).
- English and Turkish; light and dark.
- One Store process per user, but not one window: starting the Store
  again (from another virtual desktop, for example) opens another window,
  which KWin places on the current desktop; the windows share the
  installs in progress (one backend). Before, a second start only raised
  the window on the first desktop (product owner, 2026-10-22).

## App Installer for .deb files (2026-10-27)

Double-clicking a `.deb` (File Explorer, Firefox's "Open") opens
`veltos-store --install-file FILE` in the layout of Windows 11's App
Installer: "Install VLC?" with publisher, version, size and package from
the control file, the description, the app's icon taken from the package
(`debfile.py`, read with `dpkg-deb` as a stream; nothing of the package
runs), "Launch when ready", a trust note, then the progress and Open
buttons for the apps it added. An installed package of the same name
turns the question into Update, Reinstall or "a newer version is
installed"; a package for another processor cannot be installed.
Installing is `pkcon -p --allow-untrusted install-local FILE` (plus
`--allow-reinstall` / `--allow-downgrade`), which also brings what the
package needs from Debian's archive; polkit asks for the administrator's
password. Details shows pkcon's output after a failure. Dev VM
(2026-10-27): xterm's .deb installed and launched.

## The first start of a new installation (2026-10-27)

`veltos-first-update.service` (enabled, never started while the package is
installed; `Type=exec` and not ordered after network-online.target, so the
sign-in screen does not wait) runs `/usr/libexec/veltos/first-update`
once on a new installation and never in the live system: it waits for the
network (`nm-online`), runs `apt-get update` and `apt-get -y full-upgrade`
(`--force-confold`, a 10 min dpkg lock wait), writes its progress to
`/run/veltos/first-update.json` (APT::Status-Fd: download 0-50 %,
installation 50-100 %) and `/var/lib/veltos/first-update-done` at the end
(also offline or after a failure: VeltOS Update brings the updates later).
Systems that update veltos-store from 1.0 are marked done (postinst).
When the installer's choice for Windows programs was Bottles, the same
service then installs Bottles from Flathub (`flatpak install --system`,
state "bottles"); without internet or after a failure the done file waits
and the next start tries again, five starts at most.

At sign-in `veltos-store --first-start` (autostart; decides without Qt)
shows the Windows 11 style full-screen "Hi. We're getting everything ready
for you" with drifting brand colours, the moving dots, the step and a
progress line; "Continue in the background" after 20 s; "You're ready to
go" (Başlayabiliriz) when done, then it closes; once per user.

## How it works

| Part | File | Notes |
|---|---|---|
| Catalogue | `veltos_store/catalog.py` | Debian's AppStream data (DEP-11, downloaded by apt into `/var/lib/swcatalog`) through `gir1.2-appstream-1.0`; icons from the AppStream icon cache. VeltOS's program names and hidden programs (`/var/lib/veltos/xdg/applications`, veltos-desktop's `update-app-names`) are applied. Data older than two days is refreshed at start (`pkcon refresh`): screenshot addresses change with package updates. |
| Install / uninstall / update | `veltos_store/packages.py`, `veltos_store/ptyrun.py` | `pkcon -p install|remove|update` one job after another in a pseudo terminal that answers pkcon's "Proceed with changes?" (`-y` would make the transaction non-interactive and polkit would refuse without asking), progress read from its output in the C locale. PackageKit asks for the administrator password through the session's agent (VeltOS' prompt, which names the Store), also for a standard user; the live session's user needs none. A refused uninstall leaves the app installed with the reason. An uninstall that would remove a part of VeltOS (checked with `apt-get -s remove`) is refused with a message. |
| Open | `veltos_store/app.py` | `gtk-launch <desktop id>` |
| Window | `veltos_store/qml/` | `Main.qml` (navigation rail, search), `HomePage`, `GridPage` (apps, games, results), `AppPage`, `LibraryPage`, `AppCard`, `InstallButton`. The rail's selection bar is a short pill at the left edge, level with the icon, and the rail is wide enough that it no longer covers the first letter of "Uygulamalar" (product owner, 2026-10-22). The search box is in the Tab order and shows the text (I-beam) pointer. |
| Single instance | `veltos_store/app.py` | A local socket per user (`raise_running`, `listen_for_raise`): a second start sends `window` to the running Store, which loads another `Main.qml` window. |

Curated lists (featured, essentials, creative apps, games) are package
names in `catalog.py`; only those in the catalogue are shown.

## Tests

`tests/test_catalog.py` (categories, search, curated lists, description
markup, VeltOS names, protected removals, pkcon output) and
`tests/test_ui.py` (the window offscreen in English and Turkish without QML
warnings, states and actions, update check, jobs with a stand-in pkcon).

## Verified

VM (live system, 2026-10-20): Home, app page, installing VLC (progress,
then Open and Uninstall), opening it, Library with VeltOS names, refusing
to uninstall Firefox.

## Not yet done

- Ratings and reviews, paid apps, Flatpak.
- The screenshots of the live image's catalogue were outdated (404) and
  are left out; on an installed system the data is refreshed.
- Discover's "updates available" notification still opens Discover.
