# veltos-photos

VeltOS Photos: the gallery and viewer of Windows 11's Photos (PySide6 +
QML). It replaces Gwenview in the image and opens pictures by default
(veltos-desktop's `update-app-names` writes the default apps).

- **Window**: title bar with the app name and the search box in the
  middle, navigation pane (Gallery, Favorites, the folders with "Add a
  folder", Settings). Own frame and shadow (`frame.py`).
- **Gallery** (`library.py`): the pictures and videos of Pictures and
  Videos (XDG user folders) and added folders, with their subfolders
  (hidden folders and Wine prefixes skipped), grouped by month by the date
  taken (EXIF DateTimeOriginal through Pillow, else the file time), newest
  first; Filter (photos and videos / photos / videos), Sort (newest or
  oldest first), View (small, medium, large tiles), Slideshow, search by
  name and folder. The index is cached in `~/.cache/veltos/photos-index.json`
  so EXIF is read once per file. Rows are made in Python for the number
  of columns that fit, so the list stays light for large libraries.
- **Thumbnails** (`thumbs.py`): the shared freedesktop.org cache
  (`~/.cache/thumbnails`); pictures with Qt's image reader, videos with
  ffmpegthumbnailer; served to QML as `image://thumb/...` and made in Qt's
  image loading threads.
- **Viewer**: toolbar (zoom out/in, rotate, edit, delete, favorite, file
  information, more: copy, set as desktop background or lock screen,
  show in folder, slideshow), the picture fitted to the window (wheel
  zooms at the pointer, drag pans, double click zooms), previous/next at
  the sides, filmstrip, zoom level with fit/actual size, file information
  panel (name, date taken, modified, dimensions, size, camera, lens,
  exposure, folder). Keys: arrows, +/-/0, Delete, F5, Ctrl+R, Ctrl+E,
  Ctrl+C, Esc. Videos show their frame and open in VeltOS Media Player.
- **Edit image** (`edit.py`, Pillow): crop with handles and aspect ratios
  (free, original, square, 16:9, 4:3, 3:2), rotate left/right, flip,
  brightness, contrast, saturation and warmth with a live preview
  (QtQuick.Effects MultiEffect); "Save as copy" ("photo - Copy.jpg",
  "- Kopya" in Turkish) or "Save". The picture is turned upright first
  and keeps its EXIF data (orientation reset); JPEG at quality 95.
- Delete moves to the Recycle Bin (`kioclient move ... trash:/`).
- **Settings**: app theme, folders (add, remove), about.
- English and Turkish.

Tests: `tests/test_library.py` (scan, EXIF dates, grouping, edits with real
Pillow pictures) and `tests/test_ui.py` (the window offscreen in English
and Turkish: gallery, favorites, viewer, rotate, edit, settings).
