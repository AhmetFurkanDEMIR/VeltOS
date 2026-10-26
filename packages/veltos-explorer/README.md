# veltos-explorer

VeltOS File Explorer: a file manager in the layout of Windows 11 File
Explorer, written for VeltOS in Python (PySide6) and QML. It is also the
**file dialog of every program**, the **"open with" window** and the
**Properties window**:

- `veltos-explorer --pick` (`picker.py`, `qml/Picker.qml`): Windows 11's
  Open / Save As / Select Folder dialog built from Explorer's own address
  bar, navigation pane and views, with the file name box, the file type
  drop-down, New folder, "already exists, replace?", and the last folder
  remembered. The request is JSON on standard input, the answer JSON on
  standard output (see the module's docstring). VeltOS Settings calls it
  directly (pictures, wallpapers). The "Save as type" box is as wide as
  the file name box, as on Windows (product owner, 2026-10-22: long
  LibreOffice type names overflowed the 300 px box), and Explorer's
  drop-down menus are never wider than the window and open in the right
  place the first time too (`WinMenu.qml` follows its own size).
- `veltos-explorer --portal` (`portal.py`, GLib/GDBus, no Qt): the
  `org.freedesktop.impl.portal.FileChooser` backend of xdg-desktop-portal
  (D-Bus activated), chosen for Plasma sessions by
  `/etc/xdg/xdg-desktop-portal/kde-portals.conf`. Firefox, Mail and GTK
  programs (`GTK_USE_PORTAL=1`), Qt and KDE programs and LibreOffice
  (through Qt's portal platform theme, `QT_QPA_PLATFORMTHEME=xdgdesktopportal`
  in veltos-desktop's session script) therefore show the VeltOS dialog.
  The dialogs the backend starts (`--pick`) run with KDE's platform theme
  (`app.portal_platform_theme`): they are the portal's own dialog and must
  not ask the portal from inside its request (2026-10-22). They also get
  the session's language from systemd's user manager
  (`portal.session_environment`: `LANGUAGE`, `LANG`, `LC_ALL`,
  `LC_MESSAGES` from `systemctl --user show-environment`): D-Bus may
  start the backend before Plasma has passed the language on, and the
  dialog then said "File name" and "Save as type" in a Turkish session
  (product owner, 2026-10-22).
  `kde-portals.conf` also sets `org.freedesktop.impl.portal.Settings=kde`
  and `org.freedesktop.impl.portal.Lockdown=none`: KDE's backend has no
  Lockdown interface, so xdg-desktop-portal 1.20 started the GTK backend
  as a fallback (Debian's file lists `kde;gtk;`), which waits for
  `graphical-session.target`, and every early portal request at sign-in
  waited 25 s (faster sign-in, product owner, 2026-10-22).
- `veltos-explorer --open-with FILE` (`openwith.py`, `qml/OpenWith.qml`):
  "Select an app to open this .txt file" as Windows 11 asks it, with the
  apps that claim the type, "More apps", Always (records the default in
  `~/.config/mimeapps.list`) and Just once. Explorer's "Open with" menu
  ends with "Choose another app", and a file no app claims opens this
  window instead of KDE's dialog. As in Start, the first `.desktop` file
  of a name wins even when it is hidden, so apps VeltOS hides with
  `NoDisplay` copies (veltos-desktop `update-app-names`) are not offered.
- `veltos-explorer --properties PATH...` (`properties.py`,
  `qml/Properties.qml`; paths, `file://` URLs and `desktop:/NAME`):
  Windows 11's Properties window instead of KDE's dialog, for files,
  folders, several items, drives and Recycle Bin items, titled "NAME
  Properties". General: icon and name (renaming), type, "Opens with" and
  Change... (the "Select an app" window), location, size and size on
  disk (counted in the background for folders, as Windows counts up),
  what a folder contains, created / modified / accessed, Read-only and
  Hidden; a drive's type, file system and used / free pie; a Recycle Bin
  item's original location and deletion date. Security: owner, group and
  read / write / run permissions (changed by the owner only). Details:
  the facts as a list (picture size for pictures). OK, Cancel and Apply;
  nothing needs the administrator password. Properties in File Explorer
  (command bar, menus, Alt+Enter), Properties in the desktop's menus
  (veltos-desktop) and `org.freedesktop.FileManager1.ShowItemProperties`
  all open it (product owner, 2026-10-22).
- `veltos-explorer --compress PATH...`: the desktop's "Compress to ZIP
  file", the same `.zip` Explorer makes (a free name next to the items,
  VeltOS Archive's progress window).
- `veltos-explorer --empty-recycle-bin` (`app.empty_recycle_bin`,
  `qml/EmptyBin.qml`): Windows 11's "permanently delete all items?"
  question in a small window of its own, then the bin is emptied; the
  desktop's Recycle Bin menu (veltos-desktop) runs it.
- Typing `cmd`, `terminal`, `powershell` or `wt` into the address box
  opens the Terminal at the folder, as Windows 11 does.
- New > Folder / Word Document / PowerPoint Presentation / Text Document /
  Excel Worksheet (Windows 11's order with Office; the Office documents
  while veltos-office is installed, filled by its `blank` module) make
  the item and open its name for editing once the listing shows it (`models.Tab.request_rename`; asked
  before the listing was done, a slow folder found no row and the item
  kept "New folder", 2026-10-22). Refresh (F5) blinks the view like
  Windows 11's File Explorer (`Tab.refreshed`).
- Right-click one file or folder and choose **Create shortcut on desktop**.
  Files and folders become symbolic links; `.desktop` launchers are copied
  and made executable so Plasma can launch them. Existing desktop items are
  never overwritten, and VeltOS' protected desktop icons cannot be copied.
  Start and taskbar Search use `veltos-explorer --create-shortcut
  FILE_OR_FOLDER` for the same action on local recent files.

## What it shows

- **Title bar with tabs** (icon, name, close; "+" for a new tab; Ctrl+T,
  Ctrl+W, Ctrl+Tab) and minimise / maximise / close drawn like Windows.
  The window draws its own frame and shadow; the shadow is outside the
  input region (`app.follow_frame`), resizing is handed to the window
  manager (`startSystemResize`).
- **Command bar**: New (folder, Word, PowerPoint, text, Excel), cut, copy, paste, rename,
  delete, Sort, View, "…" (select all/none/invert, Open in Terminal,
  Properties). In the Recycle Bin: Empty Recycle Bin, Restore all items
  (when nothing is selected), Restore.
- **Recycle Bin** menus as on Windows 11 (product owner, 2026-10-22): an
  item's menu has Restore, Cut, Delete and Properties; the empty space's
  View, Sort, Refresh, Empty Recycle Bin and Restore all items. Items cut
  in the Recycle Bin leave it through KIO's trash (`trash:/0-NAME`,
  `ops.trash_url`), which also drops their `.trashinfo` (a plain move
  left it behind).
- **The desktop's system icons**: This PC, the Recycle Bin and the VeltOS
  Store on the desktop (`places.DESKTOP_SYSTEM_ICONS`) cannot be deleted,
  cut or renamed from File Explorer (a message says so) and their menu
  offers only Open and Properties; veltos-desktop's desktop guard makes
  the files root's, so not even a terminal removes them (product owner,
  2026-10-22).
- **Address row**: back, forward, recent places, up; the address box shows
  the path as clickable parts starting at the known folder (Documents,
  Pictures, …) and becomes a text box on click / Ctrl+L; refresh; the
  search box ("Search Documents") searches below the folder.
- **Navigation pane**: Home, pinned folders (Quick access), This PC with its
  drives, Recycle Bin.
- **Home**: Quick access tiles and Recent files (freedesktop.org
  `recently-used.xbel` and KDE's RecentDocuments). **This PC**: drives with
  capacity bars; unmounted partitions mount on double-click (udisks).
  USB flash drives, other removable disks and fixed Windows (NTFS) drives
  use distinct Windows 11-style icons. Windows drives open without a
  password for administrators
  (`/usr/share/polkit-1/rules.d/50-veltos-drives.rules`); they are mounted
  through ntfs-3g with Windows file names (`/etc/udisks2/mount_options.conf`)
  and read only, with an explanation, when Windows did not shut down
  completely. Windows' recovery partitions are hidden; the address bar
  starts at the drive ("This PC > Windows").
- A drive's right-click menu offers **Format...** only when it is not on
  the physical disk containing the running system's root, boot, EFI, `/usr`
  or `/var` volumes, and is not read-only. The command opens VeltOS Disk
  Management at that volume (`veltos-disks --format DEVICE`), re-reads its
  UDisks2 state and uses the existing Format form and separate data-loss
  confirmation; no format command runs until the user confirms.
- **Views**: Details (Name, Date modified, Type, Size; click a header to
  sort), Tiles, small / medium / large / extra large icons with picture
  thumbnails (shared freedesktop.org cache). Folders first, natural order.
- **Selection**: click, Ctrl/Shift+click, selection rectangle, keyboard
  (arrows, Home/End, Page Up/Down, type-ahead), F2 renames in place,
  Enter opens, Delete moves to the Recycle Bin (Shift+Delete asks and
  deletes for good), drag and drop (moves within a drive, copies between
  drives; Ctrl copies, Shift moves).
- **Context menus** in the Windows 11 style (icon row with cut / copy /
  rename / delete; Open, Open with, Pin to Quick access, Compress to ZIP
  file, Extract All, Copy as path, Properties, Open in Terminal).
- **Status bar**: number of items, selection and its size, Details / Large
  icons switches. Light and dark mode follow the system, live.
- **Accent colour**: focus borders, the selection rectangle, selected text
  and the accent-coloured buttons and marks use the accent chosen in
  Settings (`AccentColor` in kdeglobals; lighter in dark mode, as Windows
  draws it; VeltOS blue without one), in File Explorer and in its
  dialogs (`Theme.qml`). The Home icon is drawn in the accent
  (`qml/LocationIcon.qml`: the house of veltos-fluent-icons'
  `veltos-home`) in the tab, the navigation pane and the address bar
  (product owner, 2026-10-22).
- Text boxes (address, search, file name, rename) are in the Tab order
  and show the text (I-beam) pointer, like Windows'.

- **Copy window** (`--transfer copy|move FOLDER PATH...`, `transfer.py`,
  `transferwindow.py`, `qml/Transfer.qml`; 2026-10-26): Windows 11's
  "37% complete" window for File Explorer's paste and drop and the
  desktop's paste: More details with the speed graph, name, time and items
  remaining, Pause and Cancel (no half-written file stays), "Replace or
  Skip Files" (for all), "name - Copy" in the same folder, renames for
  moves on one drive, errors listed at the end. Shown after 500 ms, closed
  on success. Local files only; network places and the Recycle Bin use KIO.
- **Delete File** (`--delete-permanently PATH...`): Windows 11's question
  for the desktop's Shift+Delete (the empty-bin window's QML).

## How it works

- `files.py`: listing, sorting, names ("New folder (2)", "a - Copy.txt"),
  rename checks, search; pure Python.
- `places.py`: user folders (XDG), pinned folders and preferences
  (`~/.config/veltos-explorer.json`), drives (`lsblk`, `udisksctl`),
  Recycle Bin (freedesktop.org trash), recent files, "Open with"
  applications from `.desktop` files.
- `ops.py`: **copying, moving, deleting, the Recycle Bin and starting
  programs go through KDE's file engine (`kioclient`)**: progress in the
  notification area, "file already exists" questions, the standard trash.
  Documents open through Qt (the desktop portal, with an activation token),
  so an app that is already open (Firefox, Notepad) comes to the front
  with the file; `.desktop` files, Windows programs and runnable scripts
  stay with `kioclient exec` (the portal runs no programs). Renaming and
  new items are local calls that never replace an existing item.
  Properties opens VeltOS' own window (`properties.py`), no longer KDE's
  (`kioclient openProperties`). Compress / extract use VeltOS Archive
  (`veltos-archive`).
- `properties.py`: the Properties window's backend (sizes and dates in
  Windows' wording, the folder count in a thread, drives from
  `/proc/self/mounts`, the default app as Settings > Default apps decides
  it, renaming, Read-only, Hidden and permissions).
- `models.py`: the Qt model of a folder (with selection) and the tab
  (location, history, view, sort, search) — slow work in a thread.
- `app.py`: the backend object for QML (tabs, clipboard, actions).
- `qml/`: the window. Own controls throughout (no style-dependent ones
  except scroll bars and pop-ups).

Folders open in File Explorer by default (`/etc/xdg/kde-mimeapps.list`).
Programs that ask the file manager to show a folder, a file in its folder
or a file's properties (D-Bus `org.freedesktop.FileManager1`,
`filemanager1.py`, started on demand by D-Bus as `veltos-explorer
--filemanager1`) get File Explorer and its Properties window. KDE's
Dolphin is not in the VeltOS image (its service claims the same D-Bus
name).

## Notes

- QML disk cache is off (`bin_main.py`): packaged files share one time
  stamp, so a cache would keep old compiled QML after an update.
- Leaving the program skips Python's clean-up (`os._exit`): a QMimeData
  on the clipboard made in Python crashed PySide6 6.8 at exit.

## Tests

`tests/` (run during the package build): listing, sorting, names, sizes,
search, drives (recorded `lsblk` output), pins, Recycle Bin restore, "Open
with" commands, KIO commands, rename safety, and the real window loaded
offscreen in English and Turkish (navigation, tabs, every view, copy and
paste, new folder, rename, delete, menus, search).
`tests/test_properties.py`: sizes and dates as Windows writes them,
paths, URLs and `desktop:/`, a file, renaming with Read-only, Hidden and
permissions, a folder's contents counted, several items, a Recycle Bin
item and the bin, the root drive. `tests/test_portal_config.py`: file
dialogs from File Explorer, Settings from KDE's backend, Lockdown off, no
GTK backend. `tests/test_portal_theme.py` also checks that the dialogs
take the session's language from systemd, `tests/test_filemanager1.py`
that `ShowItemProperties` opens the Properties window.

## App icon and text

`data/veltos-explorer.svg` is the File Explorer icon (VeltOS artwork in the style of
Windows 11 app icons, CC-BY-SA-4.0), installed as
`/usr/share/icons/hicolor/scalable/apps/veltos-explorer.svg`. The window draws its
text like KDE programs (`NativeTextRendering`): Qt Quick's default
distance-field text looked uneven at fractional display scales. Qt objects
are configured with setters, never keyword arguments (PySide6 resolves those
with the C library's `toupper()`, which broke in a Turkish locale).
