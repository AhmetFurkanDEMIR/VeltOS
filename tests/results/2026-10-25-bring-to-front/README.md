# Programs come to the front when something opens in them (2026-10-25, dev VM)

Item 28 of the product owner's 2026-10-23 list. QEMU dev VM (Turkish
session), Firefox ESR 153.5.1 running, this change's packages installed
(1280x720 copies of the 1920x1080 screenshots).

| Picture | What it shows |
|---|---|
| `before-xdg-open-firefox-stays-behind.png` | Before: a program window opening a link with an `xdg-open` child (as most VeltOS apps did): the tab opens, Firefox stays behind, its taskbar button only turns orange |
| `qt-portal-firefox-in-front.png` | The same link through Qt (`QDesktopServices.openUrl`: the desktop portal's OpenURI with an activation token): Firefox comes to the front |
| `explorer-html-1-before.png`, `explorer-html-2-firefox-in-front.png` | File Explorer in front, `sayfa.html` double-clicked: Firefox comes forward with the file |
| `notepad-1-behind.png`, `notepad-2-handed-over-in-front.png` | Notepad open behind File Explorer, `not.txt` double-clicked: the running Notepad (one process, checked with pgrep) gets the file and comes to the front |
| `settings-website-firefox-in-front.png` | Settings > VeltOS Update > VeltOS website: Firefox comes forward |
| `start-search-firefox-in-front.png` | Start's "Search with Google" row (plasmashell, unchanged) already brought Firefox forward |

Why: KWin 6.3 on Wayland raises a window only with an xdg-activation token
that the active program asked for (`XdgActivationV1Integration`,
src/xdgactivationv1.cpp on invent.kde.org); a child process such as
`xdg-open` or `kioclient` has no window and so no token. Qt asks for one
for its focused window and passes it through the portal.

Not seen in the VM: Mail's links and attachments (same Qt call as
Settings), VeltOS AI's "open a web page" action (the pane is a layer-shell
surface; KWin may not give it a token), PDF Reader, Store and Task Manager
hand-overs (same code as Notepad's).
