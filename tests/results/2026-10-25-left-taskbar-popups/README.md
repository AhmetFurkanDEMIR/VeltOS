# Left-aligned taskbar: Start and search open at the left (2026-10-25, dev VM)

Item 29 of the product owner's 2026-10-23 list. QEMU dev VM (Turkish
session) with this change's shell override (`CompactApplet.qml` through
`update-plasma-overrides`); the alignment was changed the way Settings >
Personalization > Taskbar does it (`veltos_settings.taskbar.Taskbar().set
("alignment", ...)`), without restarting anything. 1280x720 copies.

| Picture | What it shows |
|---|---|
| `1-centred-start.png` | Centred taskbar: Start opens over the middle of the taskbar (unchanged) |
| `2-left-aligned-start.png` | Left-aligned taskbar: Start opens at the left, over its button |
| `3-left-aligned-search.png` | Left-aligned taskbar: the search window also opens at the left |
| `4-centred-again-start.png` | Centred again: Start is back in the middle at the next opening |

The popup's visual parent is decided each time it opens: the centred item
while the Start (or search) button sits more than 12 % of the screen's
width from its left edge (centred buttons), the button itself otherwise.
