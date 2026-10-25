# Hidden taskbar search no longer overlaps Task View (2026-10-25, dev VM)

Item 31 of the product owner's 2026-10-23 list. QEMU dev VM (Turkish
session); the search mode was changed the way Settings > Personalization >
Taskbar does it (`veltos_settings.taskbar.Taskbar().set("search", n)`).

| Picture | What it shows |
|---|---|
| `before-hidden-overlap.png` | Before: "Hide" left the magnifier and "Ara" drawn over Task View's button (zoomed 2x) |
| `after-hidden.png` | Now: Start, Task View and the apps, nothing in between (zoomed 2x) |
| `search-modes.png` | Rows: before (hidden), now hidden, search icon only, icon and label, search box |

Cause: the search applet hid its taskbar part with `visible: false` and
no width, but Plasma sets the compact representation visible again
whenever it places it, so the zero-wide box drew its icon and label over
the next button. The box is now clipped, transparent and disabled while
hidden.
