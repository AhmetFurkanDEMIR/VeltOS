# 2026-10-22 — Windows 11 polish batch (live VM, QEMU/KVM, UEFI, no 3D)

Screenshots taken in the live session of ISO `veltos-0.1.0-dev-20261022-093321`
with the rebuilt `veltos-desktop`, `veltos-explorer`, `veltos-settings`,
`veltos-fluent-icons` and the new `veltos-disks` packages of 2026-10-22
installed (`dpkg -i`; later fixes copied in by hand and the session
restarted with `systemctl restart sddm` before the Task View and taskbar
pictures, since KWin and the panel read their QML at start).

| File | What it shows |
|---|---|
| `desktop-menu.png` | Right-click on the desktop: Windows 11's menu (View, Sort by, Refresh, Paste, New, Display settings, Personalize, Open in Terminal) instead of Plasma's containment menu |
| `desktop-menu-view.png` | View submenu: Large / Medium / Small icons, Auto arrange icons |
| `desktop-menu-new.png` | New submenu: Folder, Text Document |
| `desktop-new-folder-name-box.png` | New > Folder: "New folder (2)" made at once, selected, its name open for editing (typing "Photos" + Enter renamed it) |
| `desktop-new-text-document-name-box.png` | New > Text Document with a long name ("New Text Document (2).txt"): the box grows over three lines, no scroll bar (the first version showed one) |
| `recycle-bin-menu.png` | The Recycle Bin's own menu: Open, Empty Recycle Bin, Properties — no Delete, Rename or Cut |
| `empty-recycle-bin-question.png` | "Empty Recycle Bin" from that menu: File Explorer's Windows 11 question in a fixed-size window of its own (`veltos-explorer --empty-recycle-bin`; maximize disabled) |
| `recycle-bin-emptied.png` | After Yes: the trash empty (`ktrash6 --empty`), the bin's icon back to "empty" and still second on the desktop |
| `volume-flyout.png` | Volume key: the Windows 11 flyout (icon, slider, 70 %) above the taskbar (shell-package override; KWin measured the OSD window at 342 × 640 px, bottom edge 24 px above the taskbar) |
| `settings-colour-mode-dark.png` | Settings > Home > Colour mode set to Dark: the page stays on Home (before, the press that closed the list opened "Browse themes") |
| `settings-colour-mode-light.png` | Back to Light the same way |
| `keyboard-add-list.png` | Settings > Typing > Add a keyboard: opens on Turkish Q, the common layouts below it |
| `start-office-category.png` | Start: All apps by category with Office (Word, Excel, PowerPoint, PDF Reader) and Entertainment (Media Player alone) |
| `search-results.png` | The taskbar's search window while typing "not": a plain field with the accent line, the result list, and the best-match card on the right filled in (it stayed empty before) |
| `search-box-while-open.png` | The taskbar's search box while the search window is open: no box around it any more (Plasma's "expanded" highlight is off for it) |
| `task-view.png` | Task View: the "Desktop 1" card shows the File Explorer window on it; the selection frame lies on the card's edge |
| `task-view-two-desktops.png` | After "New desktop": two cards; a right-click on "Desktop 2" switched to it and a double-click on "Desktop 1" switched back |
| `word-save-dialog.png` | Word (LibreOffice Writer started from Word's start screen): Ctrl+S opens the VeltOS Windows 11 Save dialog with "Word 2007 (.docx)" (the portal theme is back for programs started from Start) |
| `photos-add-folder-dialog.png` | Photos > Add a folder: the VeltOS Select Folder dialog |
| `explorer-desktop-shortcuts.png` | File Explorer in the Desktop folder: the launchers show their own names and icons as "Shortcut" |
| `explorer-new-folder-name-box.png` | File Explorer New > Folder: "New folder (2)" with its name box open at once |
| `taskbar-accent-red.png` | The taskbar with a red accent: the accent glows softly behind the centred icons, fading towards the ends |
| `taskbar-accent-wave.png` | Five frames (top to bottom) while the accent changed from green to blue: the glow cross-fades and a band of colour crosses the bar once |
| `settings-accent-orange-taskbar.png` | Settings > Personalization > Colours, orange chosen with a click: the taskbar's glow turned orange at once (Settings sends KDE's PaletteChanged signal; before, plasmashell kept the old accent until restarted) |
| `disk-management-blank-disk.png` | Disk Management: the volume list, the disk map with the blank 40 GB disk ("Not Initialized", black hatching) and the DVD; the disk's menu (Initialize Disk…, Properties) |
| `disk-management-initialize.png` | Initialize Disk dialog (GPT / MBR) |
| `disk-management-new-volume.png` | New Simple Volume dialog on the unallocated space (size in MB, NTFS / exFAT / FAT32 / ext4, label, quick format) |
| `disk-management-volume-menu.png` | The new "Data" NTFS volume (40 GB, made by UDisks2's CreatePartitionAndFormat) and its menu |
| `disk-management-format.png` | Format dialog (label, file system, quick format) |
| `disk-management-format-warning.png` | The "all data will be erased" question before formatting |
| `disk-management-after-delete.png` | After Format (ext4) and Delete Volume: the disk unallocated again (`lsblk` showed no partition) |

Not in pictures: the blink of the icons on Refresh (an animation), the
Delete key / F2 / Ctrl+X skipping the protected icons (the override's
unit test), the LibreOffice start-up window rule (a KWin rule; in QEMU a
KWin script logged no window other than Writer's own while Word opened,
so there was nothing to hide here), Tab order in Settings (unit test).
