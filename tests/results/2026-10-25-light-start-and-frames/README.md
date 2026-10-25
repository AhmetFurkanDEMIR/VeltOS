# Light-mode Start and search, popups without a frame (2026-10-25, dev VM)

Items 35, 36 and 37 of the product owner's 2026-10-23 list. QEMU dev VM
with this change's `veltos-desktop`, light and dark mode switched the way
Settings does it. Corner pictures are zoomed 4x.

| Picture | What it shows |
|---|---|
| `before-light-start.png`, `before-light-search.png` | Before: Start and search in the colour scheme's grey (#F3F3F3) with a white search field, grey cards and a grey band at the bottom |
| `before-dark-white-frame.png` | Before: dark mode, a light line around Start (and every flyout); light mode had a dark one |
| `after-light-start.png` | Now: Start in one white like VeltOS Settings (search field, footer, page: #FFFFFF), category cards with a touch of the accent colour |
| `after-light-search-qs-calendar.png` | Search, quick settings and the calendar flyout, white as well |
| `after-light-corner.png`, `after-dark-corner.png`, `after-dark-qs-corner.png` | No frame around the popups in either mode; the shadow stays |
| `after-dark-start.png` | Dark mode otherwise unchanged |
| `start-opening-slowed.png` | Start's new opening (the content rises and fades in, 220-280 ms), slowed down six times in the VM's copy only to be caught by screenshots |

Causes: Fluent's popup frame (`dialogs/background.svgz`, also tooltips)
draws a line in the text colour (15-45 % opaque) inside its shadow pieces
`shadow-top`/`shadow-topleft`, which the other edges copy with `<use>`;
the light Plasma theme filled popups with the scheme's window colour. Both
are changed in the theme build (`tools/fluent.py`: `drop_popup_outline`,
`white_popup`), which stops if Fluent's files no longer have them.
