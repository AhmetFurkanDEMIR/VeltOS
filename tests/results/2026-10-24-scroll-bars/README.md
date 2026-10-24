# Windows 11 scroll bars (2026-10-24, dev VM)

Items 11 ("Open with": an extra line pointing down) and 16 (Settings
Home: a straight line left of the scroll bar) of the product owner's
2026-10-23 list. Both lines were KDE Breeze's separator beside every
scroll bar: KDE's platform theme gives every QGuiApplication (all VeltOS
apps) the org.kde.breeze Qt Quick style, and its ScrollBar draws a
`Kirigami.Separator` along the bar.

| Picture | What it shows |
|---|---|
| `open-with-before-line.png` / `open-with-after.png` | "Select an app" with More apps open: the line beside the bar, then only a thin Windows 11 bar (it widens with a faint track under the pointer) |
| `settings-home-before-line.png` / `settings-home-after.png` | Settings Home: the full-height line at the right, then only the thin bar |
| `file-explorer-after.png` | File Explorer's list with the new bar |
| `open-with-submenu-before-icon.png` / `open-with-submenu-after.png` | "Choose another app" had Fluent's executable icon (a window with "!"); now no icon, as in Windows 11 |

The fix is a small Qt Quick Controls style of VeltOS' own
(`org.veltos.controls`, veltos-desktop: ScrollBar and ScrollView, the
rest from Breeze) that every VeltOS app selects after creating its
QGuiApplication (`veltos_controls.use()`).
