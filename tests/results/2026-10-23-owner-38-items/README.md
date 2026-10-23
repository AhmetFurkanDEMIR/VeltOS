# 2026-10-23 — The product owner's 38 items (QEMU/KVM dev VM, UEFI, no 3D)

Screenshots from the QEMU dev VM: a VeltOS system installed on its disk,
with the packages of this change installed by `dpkg -i` (the VM-only
`out/vm/install-debs.sh`), in Turkish; the Automatic Repair and Safe mode
pictures come from real starts of that installed system (GRUB's start
counter at 2, and the "Safe mode" boot entry). Details per item are in
`docs/dev/development-log.md` (2026-10-23 entry).

| File | What it shows |
|---|---|
| `automatic-repair-start.png` | After two unfinished starts GRUB started "VeltOS Recovery": "VeltOS düzgün başlatılamadı" with Advanced options and Restart, on the frame buffer at 1024x768 |
| `automatic-repair-options-before-fix.png` | The first version of "Bir seçenek belirleyin" at 1024x768: one column, the Back button over the fifth tile, the last tile off the screen |
| `automatic-repair-options-1024x768.png` | After the fix: two columns (Startup Repair, Safe mode, Command Prompt, Problem details, Continue, Turn off), Back below them |
| `automatic-repair-startup-repair.png` | Startup Repair running its six steps (three done, the fourth in progress) |
| `automatic-repair-command-prompt.png` | Command Prompt: the console sign-in with the VeltOS hint line (Turkish letters in the console font), signed in; `exit` brought the options back. The Debian login message is a known gap |
| `safe-mode-sign-in-x11.png` | Safe mode (`nomodeset`, no DRM device): the VeltOS sign-in screen on X11 at 1920x1080 |
| `safe-mode-desktop-x11.png` | Safe mode: the desktop as a Plasma X11 session |
| `taskbar-previews.png` | Pointing at File Explorer's taskbar button with two windows open: one card per window with its title and a live picture (KWin script; in English, a live session) |
| `taskbar-stacked-button.png` | Two File Explorer windows: the button shows a second plate's edge |
| `taskbar-sound-badge.png` | Media Player playing a tone: the round speaker badge on its button |
| `toast-menu.png` | A notification toast ("Kablolu bağlantı kuruldu") with its "…" menu open ("Bildirim ayarlarına git") |
| `save-as-type-list.png` | Notepad's Save As in Turkish: "Dosya adı", "Kayıt türü", "Kaydet", "İptal"; the type list opened right above its box, as wide as it |
| `uac-turkish.png` | The User Account Control prompt in Turkish with "Tamam" and "İptal" (polkit's message translated; it still has a Minimise button, see known gaps) |
| `add-user-tab-order.png` | Settings > Other users > Add account: Tab moved Full name → User name → Password |
| `dark-desktop-menu.png` | Dark mode: the desktop's right-click menu as one rounded box (no inner square body) over Settings > Personalization > Colours |
| `mail-reading-pane.png` | VeltOS Mail (Thunderbird): the blue title band with the name and search box, the ribbon with New mail filled, the reading pane with the subject first. Taken before the list was switched to names only (it still shows "Name <address>") |
| `mail-account-page.png` | VeltOS Mail's account page without Thunderbird's story, donation request and links; the import text names VeltOS Mail |
| `mail-compose.png` | The new message window: no menu bar, the accent Send button (pale until a recipient is entered), "Yaz: (konu yok) - VeltOS Mail" as its title |
| `calendar-month-event.png` | VeltOS Calendar after the layout fix: month view with an event saved on the 26th, the left pane at its fixed width. Its small month calendar still shows "Pz" for Monday (Qt's "Pzt" cut to two letters); fixed afterwards to the taskbar clock's "Pt Sa Ça Pe Cu Ct Pa" |
