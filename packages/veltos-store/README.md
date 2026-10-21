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
- English and Turkish; light and dark; one window per user.

## How it works

| Part | File | Notes |
|---|---|---|
| Catalogue | `veltos_store/catalog.py` | Debian's AppStream data (DEP-11, downloaded by apt into `/var/lib/swcatalog`) through `gir1.2-appstream-1.0`; icons from the AppStream icon cache. VeltOS's program names and hidden programs (`/var/lib/veltos/xdg/applications`, veltos-desktop's `update-app-names`) are applied. Data older than two days is refreshed at start (`pkcon refresh`): screenshot addresses change with package updates. |
| Install / uninstall / update | `veltos_store/packages.py` | `pkcon -p -y install|remove|update` one job after another, progress read from its output in the C locale. PackageKit asks for the administrator password through the session's agent (the live session needs none). An uninstall that would remove a part of VeltOS (checked with `apt-get -s remove`) is refused with a message. |
| Open | `veltos_store/app.py` | `gtk-launch <desktop id>` |
| Window | `veltos_store/qml/` | `Main.qml` (navigation rail, search), `HomePage`, `GridPage` (apps, games, results), `AppPage`, `LibraryPage`, `AppCard`, `InstallButton` |

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
