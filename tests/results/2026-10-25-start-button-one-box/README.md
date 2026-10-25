# Start button: one see-through box, light and dark (2026-10-25, dev VM)

Item 34 of the product owner's 2026-10-23 list, and their follow-up while it
was being done ("the framing box should be see-through, not grey").

| Picture | What it shows |
|---|---|
| `before-start-open-box-in-box.png` | Before (zoomed 4x): Start open: Plasma's framed box around the applet and Start's own backdrop inside it |
| `step1-one-grey-box.png` | First fix: Plasma's box left out, one box, still grey (the text colour at 9 %) |
| `after-light-and-dark.png` | Now, rows: light mode Start open, Task View under the pointer, quick settings open, clock open; then the same in dark mode. A see-through white highlight with a hairline edge (light), a faint white (dark) |

Changes: the desktop shell override (`CompactApplet.qml`) no longer draws
Plasma's expanded-applet box around Start, quick settings and the clock,
which draw their own (it already skipped the search box); the four
VeltOS taskbar buttons draw white at 62 % (38 % pressed) with a 5 % black
hairline in light mode and white at 9 % (5 %) with a 7 % white hairline in
dark mode. Plasma's own task buttons (the apps) are unchanged.
