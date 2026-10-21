# veltos-archive

VeltOS Archive: an archive manager in WinRAR's layout with Windows 11
controls (the product owner asked for a WinRAR style ZIP/RAR app).

## What the user sees

- **Window**: menu bar (File, Commands, Help); WinRAR's toolbar of large
  pictures — Add, Extract To, Test, View, Delete, Find, Info; the up
  button and the archive path ("photos.zip\2024 - ZIP archive, unpacked
  size … bytes"); the file list with Name, Size, Packed, Type, Modified
  and CRC32 (sortable, folders first, ".." goes up, Ctrl/Shift
  selection); the status bar ("Selected …" / "Total … files, … bytes",
  a lock for password-protected archives).
- **Opening**: double-click an archive in File Explorer (the app is the
  only archive handler, Ark is not installed), File > Open, or drop it on
  the window. Folders inside the archive open with a double click; a file
  opens with its app (extracted to a private temporary folder).
- **Extract To**: destination (default: a folder named like the archive),
  overwrite mode (rename automatically, overwrite, skip); the selection
  or everything. A "Show files" button opens the result.
- **Add**: dropping files on an open ZIP/7Z/TAR archive adds them; with no
  archive open, WinRAR's "Archive name and parameters" dialog creates one
  — ZIP, 7Z, TAR.GZ or TAR.XZ, compression Store … Best, optional password
  (AES-256 for ZIP, "Encrypt file names" for 7Z).
- **Test, Delete, Find, Info** as in WinRAR (delete only for ZIP/7Z/TAR,
  not solid archives).
- **Passwords**: asked when needed; a wrong password asks again.
- **File Explorer**: "Extract All…" (to a folder named like the archive),
  "Extract here", "Compress to ZIP file" and "Add to archive…" run this
  app; it then shows only WinRAR's small progress window (Background,
  Cancel) and closes when done.

English and Turkish.

## How it works

| File | Role |
|---|---|
| `veltos_archive/archive.py` | Commands and parsers: 7-Zip (`7z l -slt`, `x`, `e`, `t`, `a`, `d`) and, for compressed tar archives, bsdtar (`-tv`, `-x`); folder tree, names, progress and error parsing |
| `veltos_archive/app.py` | `Backend` (rows, sorting, find, passwords, operations) and `Job` (one 7-Zip/bsdtar run with WinRAR's progress, QProcess); command-line modes |
| `veltos_archive/qml/` | `Main.qml` (the window), `Task.qml` (File Explorer's progress window), dialogs (`AddDialog`, `PasswordDialog`, `WinDialog`), controls, toolbar pictures (`icons/`, VeltOS drawings) |

- 7-Zip (Debian `7zip`) reads ZIP, 7Z, TAR, GZ, BZ2, XZ, ZST, ISO, CAB,
  ARJ, LZH, WIM and more. RAR needs the `7zip-rar` plugin (Debian
  non-free, RARLAB's unRAR code; the image includes it): with it, all RAR
  versions including RAR5 and password-protected RARs open.
- 7-Zip shows a .tar.gz as a compressed stream holding one .tar file;
  WinRAR shows what is inside, so compressed tars are listed and
  extracted with bsdtar (libarchive-tools). bsdtar prints no percentage:
  progress counts its "x name" lines. bsdtar cannot rename existing
  files: "Rename automatically" keeps them (like "Skip") for tars.
- Creating RAR archives needs RARLAB's proprietary `rar` (shareware); it
  is not shipped, and RAR is shown disabled in the Add dialog with a note.
- 7-Zip is always given `-p` (an empty password when none is known):
  without it, it would wait for a password on its terminal.

## Tests

`tests/test_archive.py` runs the real 7-Zip and bsdtar (Build-Depends):
ZIP/7Z/TAR.GZ/TAR.XZ/TAR.ZST creation, listing and folder tree, extracting
a selection, overwrite modes, passwords (7Z with encrypted names, AES ZIP,
wrong passwords), test/delete/append, non-archives, name helpers.
`tests/test_ui.py` loads the window offscreen (English and Turkish C
locale), opens a real ZIP, browses, sorts, finds, extracts, tests, views,
deletes, and runs File Explorer's "Extract to <name>" and "Add to"
windows. RAR is not covered by the package tests (no RAR maker in Debian
main); it was checked in the builder with Debian's non-free `rar`.
