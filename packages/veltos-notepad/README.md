# veltos-notepad

VeltOS Notepad: plain text editing in the layout of Windows 11's Notepad
(PySide6 + QML). It replaces KWrite in the image and opens text files by
default (veltos-desktop's `update-app-names` writes the default apps).

- **Window**: tabs in the title bar (a dot on tabs with unsaved changes,
  close on hover, "+" for a new tab, middle click closes), File / Edit /
  View menus with Settings (gear) on the right, the text, the status bar.
  The window draws its own frame and shadow (`frame.py` keeps clicks on
  the shadow going to the windows behind).
- **File**: New tab, New window, Open (the desktop's file dialog: the app
  is a QApplication), Recent, Save, Save as (adds `.txt`), Save all, Print
  (Qt's print dialog), Close tab, Close window, Exit.
- **Edit**: Undo, Cut, Copy, Paste, Delete, Find (panel at the top right:
  previous/next, Match case, Wrap around), Replace / Replace all (one step
  for Undo), Go to line, Select all, Time/Date (F5, the region's short
  formats), Font.
- **View**: Zoom (Ctrl + wheel, Ctrl +/-/0), Status bar, Word wrap.
- **Status bar**: line and column, characters (or the selection), zoom,
  line ending and encoding; clicking the last two changes them.
- **Files** (`textfile.py`): UTF-8, UTF-8 with BOM, UTF-16 LE/BE and ANSI
  (cp1254 in Turkish, cp1252 otherwise) are detected and kept, and so are
  Windows (CRLF), Unix (LF) and Macintosh (CR) line endings; new files are
  UTF-8 with LF. Saving is atomic and keeps the file's permissions. Files
  over 64 MB are refused.
- **Session** (Windows 11 behaviour): every tab, with the text of unsaved
  ones, is kept in `~/.local/share/veltos/notepad/session.json` (mode 600)
  every 15 s and on exit, and comes back at the next start; closing the
  window does not ask. "Start new session" in Settings asks about unsaved
  changes instead. A second start hands its files to the running Notepad
  as tabs (local socket `veltos-notepad-UID`), unless "Open in a new
  window" is chosen.
- **Settings**: app theme (light, dark, system), font family, style and
  size with a preview, word wrap, opening files, start behaviour, about.
  Stored in `~/.config/veltos/notepad.conf`.
- English and Turkish.

Tests: `tests/test_textfile.py` (encodings, line endings, saving,
positions) and `tests/test_ui.py` (the real window offscreen in English and
Turkish: open/edit/save, find/replace, session, close question, menus,
settings).
