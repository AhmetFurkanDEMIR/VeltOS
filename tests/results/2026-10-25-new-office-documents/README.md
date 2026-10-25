# New > Word, PowerPoint and Excel documents (2026-10-25, dev VM)

Item 19 of the product owner's 2026-10-23 list. Turkish session.

| Picture | What it shows |
|---|---|
| `desktop-new-menu.png` | The desktop's right-click menu, New: Folder, then Word Belgesi, PowerPoint Sunusu, Metin Belgesi, Excel Çalışma Sayfası (Windows 11's order with Office) |
| `desktop-new-sheet-rename.png` | Excel Çalışma Sayfası chosen: "Yeni Excel Çalışma Sayfası.xlsx" on the desktop with the Excel icon, its name (without the extension) selected for typing |
| `desktop-sheet-opened.png` | Double-clicked: Calc with the Excel icon in the title bar and on the taskbar, sheet "Sayfa1", Calibri 11 |
| `explorer-new-menu.png` | File Explorer's command bar, New: the same entries, Ctrl+Shift+N beside Folder |
| `explorer-new-word-rename.png` | Word Belgesi chosen in Documents: "Yeni Word Belgesi.docx" (0 KB, type "Microsoft Word Belgesi") with its name open; the click stayed in the menu |
| `explorer-word-opened.png` | Double-clicked: Writer with the Word icon, "Yeni Word Belgesi.docx — VeltOS Office Writer", Turkish, Carlito 11 |

Checked before choosing empty files (same VM, LibreOffice 25.2.3): an
empty `.docx` and `.pptx` open as new documents with the Word/PowerPoint
icon; after typing, Ctrl+S saved "Yeni Word Belgesi.docx" as a real Word
file (5078 bytes, `file`: "Microsoft Word 2007+") without a question. An
empty `.xlsx` opened in Calc with a plain document icon (twice), hence the
small workbook for Excel.

Before the menu fix, choosing Word Belgesi over the navigation pane also
opened Home ("Giriş") in that window.

Not tested: opening the new files in Microsoft Office.
