# One menu on a right-click in Notepad (2026-10-25, dev VM)

Item 20 of the product owner's 2026-10-23 list ("a right-click in a text
document opens two menus; keep the Windows one"). Turkish session,
`not.txt` from the desktop.

| Picture | What it shows |
|---|---|
| `before-two-menus.png` | Before: KDE's text menu (Yazım Denetimi, Geri Al, Yinele, Kes, Kopyala, Yapıştır, Sil, Tümünü Seç; the KDE style's TextArea) over Notepad's own menu (its whole Edit menu) |
| `after-one-menu.png` | After, with "hello" selected: one menu, Windows' text menu (Geri al, Kes, Kopyala, Yapıştır, Sil, Tümünü seç) |

Then "Kopyala" from that menu, Ctrl+End, Enter, Ctrl+V pasted "hello" on a
new line with the text cursor after it; Ctrl+Z undid it and the file stayed
unchanged.

The desktop's and File Explorer's right-click menus for the text file
were already single (checked the same day).
