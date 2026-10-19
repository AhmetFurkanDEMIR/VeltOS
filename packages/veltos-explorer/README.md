# veltos-explorer

VeltOS File Explorer: a file manager in the layout of Windows 11 File
Explorer, written for VeltOS in Python (PySide6) and QML.

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
