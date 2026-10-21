# veltos-pdf

VeltOS PDF Reader: reads PDF documents in a modern reader layout (PySide6 +
QML, pages drawn by Qt PDF, which uses PDFium). It replaces KDE's Okular
in the image and opens PDF files by default (veltos-desktop's
`update-app-names` writes the default apps). The layout follows today's
PDF readers on Windows; the name, icon and artwork are VeltOS' own (no
Adobe names or logos).

- **Window**: own frame and shadow (`frame.py`), the app menu (Open, Open
  recent, Print, Document properties, Show in folder, Read mode, Full
  screen, Close tab, Exit), a Home tab and one tab per document; opening a
  file that is already open shows its tab. One window per user: files
  opened later go to it as tabs (`QLocalServer` "veltos-pdf-UID").
- **Home**: welcome card with "Open file", the recent files (name, folder,
  opened, size; missing files are dropped, "Remove from list").
- **Document** (`DocumentView.qml`): continuous pages with selectable text
  (Ctrl+C, Ctrl+A), the floating page and zoom bar (previous/next page,
  page number, zoom out/in, fit page), the quick tool rail (search, page
  thumbnails, bookmarks, rotate, fit width, print, properties) and the
  side panel for search results (with their context), thumbnails and the
  document outline. Fit width/page keeps fitting when the window or the
  side panel changes; zooming by hand ends it.
- **Passwords**: protected documents ask for their password (wrong
  passwords ask again). Damaged files are refused with a message.
- **Print**: the system print dialog; pages are rendered at the printer's
  resolution (`printDocument`).
- Keys: Ctrl+O open, Ctrl+P print, Ctrl+D properties, Ctrl+W close tab,
  Ctrl+H read mode, F11 full screen, Ctrl+F search, Ctrl+= / Ctrl+- zoom,
  Ctrl+0 fit page, Ctrl+2 fit width, Ctrl+Tab next tab, Ctrl+Q exit.
- App theme follows the system (light/dark, accent). English and Turkish.

Not yet: annotations, highlights, forms filling, signing, editing pages
(Qt PDF only reads), printing tested on a real printer.

Tests: `tests/test_ui.py` writes real PDF files with QPdfWriter and loads
the window offscreen in English and Turkish: tabs and recent files, panels,
search, zoom and properties, a damaged file. Any QML warning fails a test.
