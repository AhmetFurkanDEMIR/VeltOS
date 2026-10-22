# veltos-explorer

VeltOS File Explorer: a file manager in the layout of Windows 11 File
Explorer, written for VeltOS in Python (PySide6) and QML. It is also the
**file dialog of every program** and the **"open with" window**:

- `veltos-explorer --pick` (`picker.py`, `qml/Picker.qml`): Windows 11's
  Open / Save As / Select Folder dialog built from Explorer's own address
  bar, navigation pane and views, with the file name box, the file type
  drop-down, New folder, "already exists, replace?", and the last folder
  remembered. The request is JSON on standard input, the answer JSON on
  standard output (see the module's docstring). VeltOS Settings calls it
  directly (pictures, wallpapers).
- `veltos-explorer --portal` (`portal.py`, GLib/GDBus, no Qt): the
  `org.freedesktop.impl.portal.FileChooser` backend of xdg-desktop-portal
  (D-Bus activated), chosen for Plasma sessions by
  `/etc/xdg/xdg-desktop-portal/kde-portals.conf`. Firefox, Mail and GTK
  programs (`GTK_USE_PORTAL=1`), Qt and KDE programs and LibreOffice
  (through Qt's portal platform theme, `QT_QPA_PLATFORMTHEME=xdgdesktopportal`
  in veltos-desktop's session script) therefore show the VeltOS dialog.
  The dialogs the backend starts (`--pick`) run with KDE's platform theme
  (`app.portal_platform_theme`): they are the portal's own dialog and must
  not ask the portal from inside its request (2026-10-22).
- `veltos-explorer --open-with FILE` (`openwith.py`, `qml/OpenWith.qml`):
  "Select an app to open this .txt file" as Windows 11 asks it, with the
  apps that claim the type, "More apps", Always (records the default in
  `~/.config/mimeapps.list`) and Just once. Explorer's "Open with" menu
  ends with "Choose another app", and a file no app claims opens this
  window instead of KDE's dialog.
- `veltos-explorer --empty-recycle-bin` (`app.empty_recycle_bin`,
  `qml/EmptyBin.qml`): Windows 11's "permanently delete all items?"
  question in a small window of its own, then the bin is emptied; the
  desktop's Recycle Bin menu (veltos-desktop) runs it.
- Typing `cmd`, `terminal`, `powershell` or `wt` into the address box
  opens the Terminal at the folder, as Windows 11 does.
- New > Folder / Text Document make the item and open its name for
  editing once the listing shows it (`models.Tab.request_rename`; asked
  before the listing was done, a slow folder found no row and the item
  kept "New folder", 2026-10-22). Refresh (F5) blinks the view like
  Windows 11's File Explorer (`Tab.refreshed`).

## What it shows

- **Title bar with tabs** (icon, name, close; "+" for a new tab; Ctrl+T,
  Ctrl+W, Ctrl+Tab) and minimise / maximise / close drawn like Windows.
  The window draws its own frame and shadow; the shadow is outside the
  input region (`app.follow_frame`), resizing is handed to the window
  manager (`startSystemResize`).
- **Command bar**: New (folder, text document), cut, copy, paste, rename,
  delete, Sort, View, "…" (select all/none/invert, Open in Terminal,
  Properties). In the Recycle Bin: Empty Recycle Bin, Restore.
- **Address row**: back, forward, recent places, up; the address box shows
  the path as clickable parts starting at the known folder (Documents,
  Pictures, …) and becomes a text box on click / Ctrl+L; refresh; the
  search box ("Search Documents") searches below the folder.
- **Navigation pane**: Home, pinned folders (Quick access), This PC with its
  drives, Recycle Bin.
- **Home**: Quick access tiles and Recent files (freedesktop.org
  `recently-used.xbel` and KDE's RecentDocuments). **This PC**: drives with
  capacity bars; unmounted partitions mount on double-click (udisks).
  Windows (NTFS) drives have their own icon (a window mark, not Microsoft's
  logo) and open without a password for administrators
  (`/usr/share/polkit-1/rules.d/50-veltos-drives.rules`); they are mounted
  through ntfs-3g with Windows file names (`/etc/udisks2/mount_options.conf`)
  and read only, with an explanation, when Windows did not shut down
  completely. Windows' recovery partitions are hidden; the address bar
  starts at the drive ("This PC > Windows").
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

## How it works

- `files.py`: listing, sorting, names ("New folder (2)", "a - Copy.txt"),
  rename checks, search; pure Python.
- `places.py`: user folders (XDG), pinned folders and preferences
  (`~/.config/veltos-explorer.json`), drives (`lsblk`, `udisksctl`),
  Recycle Bin (freedesktop.org trash), recent files, "Open with"
  applications from `.desktop` files.
- `ops.py`: **copying, moving, deleting, the Recycle Bin, opening and
  Properties go through KDE's file engine (`kioclient`)**: progress in the
  notification area, "file already exists" questions, the standard trash.
  Renaming and new items are local calls that never replace an existing
  item. Compress / extract use Ark.
- `models.py`: the Qt model of a folder (with selection) and the tab
  (location, history, view, sort, search) — slow work in a thread.
- `app.py`: the backend object for QML (tabs, clipboard, actions).
- `qml/`: the window. Own controls throughout (no style-dependent ones
  except scroll bars and pop-ups).

Folders open in File Explorer by default (`/etc/xdg/kde-mimeapps.list`).
KDE's Dolphin stays installed for programs that ask the file manager to
"show a file in its folder" (D-Bus `org.freedesktop.FileManager1`, not yet
implemented here); it is hidden from Start.

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

## App icon and text

`data/veltos-explorer.svg` is the File Explorer icon (VeltOS artwork in the style of
Windows 11 app icons, CC-BY-SA-4.0), installed as
`/usr/share/icons/hicolor/scalable/apps/veltos-explorer.svg`. The window draws its
text like KDE programs (`NativeTextRendering`): Qt Quick's default
distance-field text looked uneven at fractional display scales. Qt objects
are configured with setters, never keyword arguments (PySide6 resolves those
with the C library's `toupper()`, which broke in a Turkish locale).
