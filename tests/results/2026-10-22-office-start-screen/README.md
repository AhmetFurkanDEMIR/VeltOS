# 2026-10-22 — VeltOS Office start screen (live VM, QEMU/KVM, UEFI, no 3D)

Screenshots taken in the live session of ISO `veltos-0.1.0-dev-20261021-163819`
with the rebuilt `veltos-office` and `veltos-desktop` packages of
2026-10-22 installed (`dpkg -i`).

| File | What it shows |
|---|---|
| `word-processor-home.png` | `veltos-office word`: Home in Word's blue — greeting, New with the blank tile, VeltOS' templates (meeting notes, report, to-do list) and LibreOffice's business letter, "More templates", Recent / Pinned with search |
| `word-processor-new.png` | New: every template with its thumbnail, "Search templates" |
| `word-processor-open.png` | Open: Recent, This PC, Browse |
| `word-processor-account.png` | Account: the user's picture and name, the Office theme (follows VeltOS), product information (LibreOffice 25.2) |
| `word-processor-options.png` | Options: the start screen switch (Windows 11 toggle), clearing the recent list |
| `spreadsheet-home.png` | `veltos-office sheet` in Excel's green with the budget, invoice and expense templates |
| `presentation-home.png` | `veltos-office slides` in PowerPoint's orange with LibreOffice's presentation designs |
| `presentation-new.png` | The 23 presentation designs as a grid |
| `word-processor-home-turkish.png` | The same Home page with `LANGUAGE=tr` |
| `word-processor-from-start.png` | The start screen opened from Start's pinned "Word Processor" (the rewritten desktop entry, `veltos-office word %U`) |
| `writer-meeting-notes-template.png` | "Meeting notes" chosen on Home: LibreOffice Writer with the template, the Tabbed interface, the title "Untitled 1 — VeltOS Office Writer" |
| `writer-blue-title-bar.png` | After a new session (KWin reads the frame QML at start): Writer's title bar in Word's blue with white caption and buttons (VeltOS' Aurorae change, told by the caption) |
| `writer-save-dialog-docx.png` | Ctrl+S in a blank document: the VeltOS Save dialog offers "Word 2007 (.docx)" (the layer now depends on writer/calc/impress.xcd; before it offered .odt) |
| `start-menu-office-icons.png` | Start with the redrawn Office icons (W / S / P tiles in front of a page, sheet and slide, Microsoft 365's composition in VeltOS' drawing; the S became an X and the names Word / Excel / PowerPoint later that day) |

Not in pictures: the entrance animations (sections glide in; tiles lift
on hover), the pin and the right-click menu of the recent list, the Open
dialog from Browse (the VeltOS dialog, as in the 2026-10-21 pictures).
