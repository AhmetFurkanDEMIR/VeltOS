# veltos-snip — VeltOS Snipping Tool

Windows 11's Snipping Tool on VeltOS (PySide6 + QML).

## User experience

- **Print Screen** or **Windows + Shift + S**: the screen freezes and dims;
  the snipping bar at the top offers **Rectangle**, **Window**, **Full
  screen** and **Freeform** and a close button. Drag a rectangle, click a
  window (it is shown undimmed under the pointer) or draw a shape; Esc or a
  right click cancels.
- The snip is **copied to the clipboard**, **saved** as
  `Pictures/Screenshots/Screenshot YYYY-MM-DD HHMMSS.png` (Windows' name)
  and a notification "Snip copied to clipboard" with the picture appears;
  selecting it opens the snip for markup.
- **Windows + Print Screen** saves the whole screen at once (same
  clipboard, file and notification).
- **Snipping Tool** in Start: "+ New" (Ctrl+N) with the snipping mode and a
  delay (none, 3, 5, 10 s); for a snip: ballpoint pen and highlighter (a
  second click picks colour and size), eraser (removes whole strokes, as on
  Windows), image crop with corner handles, undo/redo, Save (Ctrl+S, into
  Pictures/Screenshots, "Show in folder") and Copy (Ctrl+C). "..." turns
  automatic saving off.
- English and Turkish ("Ekran Alıntısı Aracı"), light and dark.

## How it works

| Module | Role |
|---|---|
| `capture.py` | Spectacle command (`--background --nonotify --fullscreen --output`), KWin script for the window list, Pictures folder (xdg-user-dirs), file names, crop, freeform mask, drawing the strokes, eraser hit test |
| `app.py` | `Snipper` (frozen screen, one overlay window per screen, coordinates to picture pixels), `Delivery` (clipboard, file, notification through `gdbus`), `Editor` (backend of the window), entry points |
| `qml/Overlay.qml` | Dimmed screen and snipping bar |
| `qml/Main.qml` | Snipping Tool window, strokes, crop |
| `qml/Glyph.qml`, `BarButton.qml`, `VButton.qml`, `Theme.qml` | Windows 11 controls and line glyphs (VeltOS drawings) |

Capturing: on Wayland KWin gives screenshots only to programs whose desktop
entry asks for its restricted `org.kde.KWin.ScreenShot2` interface.
Spectacle is such a program; VeltOS Snipping Tool runs it in the
background for one picture of the whole desktop (about 0.4 s in the VM) and
does the rest itself, so no KDE window appears. Window frames for Window
mode come from a short KWin script (loaded over D-Bus) that calls back the
tool's D-Bus object; without an answer Window mode snips the full screen.

Shortcuts: `X-KDE-Shortcuts` in the desktop file's actions (kglobalaccel).
veltos-desktop switches Spectacle's own shortcuts off and hides it from
Start (`update-app-names`), and lets Plasma's clipboard keep pictures
(`/etc/xdg/klipperrc`), so a snip can still be pasted after the tool ends.

## Limits

- No video recording (Windows' Snipping Tool records the screen too);
  Spectacle, hidden from Start, can still record.
- Save always writes into Pictures/Screenshots (no "Save as" dialog yet).
- Several screens with different scale factors: the picture is mapped with
  one scale factor (untested with real monitors).

## Tests

`tests/test_snip.py`: file names and folders, window list parsing, crop,
freeform, strokes, eraser, notification command, the capture flow with a
given picture, the window backend. `tests/test_ui.py`: the window and the
overlay offscreen (English and Turkish), any QML warning fails.
