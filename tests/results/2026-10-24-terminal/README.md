# Terminal (Konsole) fixes (2026-10-24, dev VM)

Item 10 of the product owner's 2026-10-23 list.

| Picture | What it shows |
|---|---|
| `before-right-click-crash-drkonqi.png` | Before: a right-click in the Terminal ended it ("Konsole closed unexpectedly", SIGSEGV in `MainWindow::updateHamburgerMenu`, `coredumpctl`) |
| `right-click-menus.png` | After: the right-click menu with and without selected text (Copy, Paste, Find, Select All, Split View, Clear Scrollback, Menu) |
| `new-tab-and-menus.png` | "+" opens a tab; the menus of the terminal and of a tab |
| `ctrl-c-without-selection-interrupts.png` | Ctrl+C with nothing selected interrupts `sleep 100` (^C) |
| `ctrl-c-with-selection-copies.png` | Ctrl+C with text selected copies it (no ^C) |
| `ctrl-v-pastes.png` | Ctrl+V pastes the copied text at the prompt |
| `before-title-konsole.png` / `after-title-terminal.png` | The window title said "— Konsole" in a Turkish session; after the session fix "— Terminal" |

Causes: VeltOS' Konsole layout files had no toolbars, and Konsole 25.04's
hamburger menu (added to the right-click menu while the menu bar is
hidden) crashed without them; the toolbars are back, hidden. Plasma 6.3's
startplasma applies `plasma-localerc`'s LANGUAGE after the session
scripts, which dropped VeltOS' program-name catalogs (`tr@veltos`).
