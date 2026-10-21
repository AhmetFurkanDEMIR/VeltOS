# VeltOS Status

Last updated: 2026-10-21. Every "Implemented" item names the
evidence that shows it working. "Untested" means nobody has observed it
working yet. All observations so far are from QEMU/KVM virtual machines (no
3D acceleration) and one VirtualBox VM of the product owner; **VeltOS has
not been run on real hardware yet.**

## Implemented

| Item | Evidence |
|---|---|
| Container build environment (Debian trixie, pinned) | `build/run.sh image` |
| `veltos-base`: os-release identity, console login banners say VeltOS (dpkg diversions) | 6 unit tests; booted system reports `ID=veltos` |
| `veltos-desktop`: Windows 11 look from Fluent-kde (Kvantum style, window frames with VeltOS-drawn 46×32 caption buttons, Plasma theme, colour schemes), 48 px see-through taskbar with VeltOS Start (layout of Windows 11's 2025 Start: Pinned, Recommended and "All" with Category/Grid/List views on one scrolling page), Search box, Task View, Quick Settings, two-line clock, show-desktop corner; flyouts float with rounded corners; clock flyout = Windows 11's two cards (notification centre grouped by app with do-not-disturb, Clear all, "+N notifications" and per-card chevrons, above the calendar card with folding month and a focus session timer that turns on do-not-disturb), also on Win+N, unread count on the clock; hidden-icons flyout with icons only, "Safely Remove Hardware" flyout (Plasma override mechanism); Windows 11 toasts (bottom-right, picture left, equal buttons); Ctrl+Alt+Del security options screen with Task Manager; power key shuts down; locked taskbar without KDE widget editing, Windows wording in taskbar menus, plain desktop menu, no spinner on starting apps, Store pinned; Terminal like Windows Terminal following light/dark (One Half Light / Campbell, rounded tabs, Cascadia Mono, no toolbars); Task View shows a desktop's windows on hover; Mica-like title bars, square close-button hover on maximised windows (KWin Aurorae override); Windows 11 lock screen; VeltOS default account picture (sign-in screen, Start, Settings, set at first sign-in); 25 % display scale steps; four wallpapers (Bloom default, Flow, Glow, Lake), light and dark; "Welcome" splash; This PC / Recycle Bin / Store on the desktop in Windows' order; Windows 11 search window from the taskbar's search box (top apps, best match; untested on screen); download/copy progress as a thin bar under the taskbar icon (untested on screen); Firefox's downloads panel restyled (untested on screen); sign-in screen in KWin on Wayland like the session (VM, 2026-10-21 evening: full-screen greeter, sign-in works); softer sounds (unheard); session environment for the portal file dialogs; file indexing off by default; VeltOS GTK theme and Firefox caption buttons; no launch icon at the pointer; no on-screen keyboard at sign-in; window previews off with software rendering; Windows-familiar app names; sign-in screen; wallpaper without logo; KDE Wallet off | 76 unit tests (incl. full asset build, Start categories, Start centring override, terminal files, overrides against Plasma 6.3.6 and KWin 6.3.6 QML, menus, scale steps, wallpapers, session scripts); VM (installed system, 2026-10-20): screenshots of each item, dark taskbar on first switch, Firefox hover states; VM (live, 2026-10-20 late): Ctrl+Alt+Del screen and its Task Manager, menus, toasts, flyouts, 100 % scale, wallpaper, lock screen; VM (2026-10-20 night): maximised close hover, desktop order, Store pin, no start-up spinner, Terminal, Task View desktops; VM (2026-10-20, 23:45): new Start with categories, Grid and List views; VM (2026-10-21): Start centred on the screen like Windows 11; VM (live, 2026-10-21): clock flyout cards light and dark, grouping, unfolding, do-not-disturb, folding the month, focus session start/stop and its end notification, Win+N |
| `veltos-explorer` (new): File Explorer in the Windows 11 layout — tabs in the title bar, command bar, address and search boxes, navigation pane, Home (Quick access, Recent), This PC, Recycle Bin, Details/Tiles/icon views with thumbnails, context menus, drag and drop, rename in place; copy/move/delete through KIO; answers "show in folder" (`org.freedesktop.FileManager1`); the only file manager (Dolphin left out of the image); Windows (NTFS) drives with their own icon, opened without a password for administrators, through ntfs-3g with Windows file names, read only with an explanation when Windows did not shut down; **the Windows 11 file dialog of every program** (`--pick`: Open / Save As / Select Folder from Explorer's parts; `--portal`: the xdg-desktop-portal FileChooser backend, chosen for Plasma sessions; Qt/KDE/LibreOffice through Qt's portal theme, GTK/Firefox/Mail through the portal); "Select an app to open this file" window (`--open-with`, Always / Just once; used by Explorer's "Choose another app" and for files no app claims); `cmd`/`terminal` in the address box opens the Terminal | 53 unit tests (incl. the dialog and the open-with window offscreen EN/TR, the portal's request/answer mapping); VM (live, 2026-10-21 evening): the dialog alone (Open, filters, Esc), Firefox's Ctrl+O arriving in it through the portal, Konsole's Save As and LibreOffice Writer's Open through Qt's portal theme (LibreOffice's duplicate request merged; the chosen file opened); `tests/results/2026-10-21-windows-dialogs/`; 31 unit tests (incl. the real window offscreen, EN/TR, Turkish C locale); VM: opened from the taskbar, Home, Documents in Details view, item and background menus; **starts in a Turkish locale** (did not before 2026-10-20); VM (2026-10-20 night): wheel scrolling, `ShowItems` opens the folder with the file selected |
| `veltos-settings`: Windows 11 Settings, every page built in (no KDE settings window: `systemsettings`/`kcmshell6` redirect to it) — Wi-Fi, Bluetooth, Sound, Display, Night light, Notifications, Power, Multitasking, Mouse, Touchpad, Typing, Background, Colours, Lock screen, Default apps, Startup, Your info, Sign-in options, Other users, Date & time, Language & region, Accessibility, Searching files, About (OS build, developer), search, EN/TR, monochrome Windows 11 icons; Home in Windows 11 24H2's layout; Themes (eight wallpaper + mode + accent themes); own Add a device dialog | 78 unit tests (parsers with recorded tool output, KDE config files, accounts with a fake `passwd`, input devices, default/startup apps, redirect, offscreen window with every page, Turkish C locale); VM (2026-10-21): Start "Change account settings" and `systemsettings kcm_users` open Your info; VM: every page; dark mode switches the taskbar on the first switch; fixes of 2026-10-21 evening: the "Change" password button (double tap; VM: the panel opens) and the change itself (passwd conversation; VM: password changed), "Never" for the lock timeout, Default apps filled (mimeinfo.cache + VeltOS' kde-mimeapps.list), Searching files read from its setting (baloo6 in the image), text size scaling VeltOS apps, pictures chosen in the VeltOS dialog; adding a user verified in the live VM session (created with its password); **Wi-Fi tested end to end on simulated hardware** (mac80211_hwsim + hostapd WPA2: wrong key refused without extra prompts, correct key connects and gets an address, disconnect, reconnect, forget) |
| `veltos-taskmanager` (new): Task Manager in the Windows 11 layout — Processes (Apps / Background / System, summed per app, busy cells tinted, search, End task), Performance (60-second CPU/memory/disk/network graphs and figures), Startup apps (enable/disable); Ctrl+Shift+Esc, one instance; KDE System Monitor kept as "Resource Monitor" | 19 unit tests (fake psutil; window offscreen EN/TR, Turkish locale); VM: opened with Ctrl+Shift+Esc, Firefox grouped with its 11 processes, second Ctrl+Shift+Esc does not open a second window, all three pages |
| `veltos-media` (new): Media Player in the Windows 11 layout — Home with recent media, music library (songs, albums with covers, artists, shuffle and play), video library with frames, play queue (shuffle, repeat, play next), playlists, search, player bar, now playing (video or album picture), full screen; Qt Multimedia (FFmpeg); default for audio and video | 11 unit tests (queue logic, tags of real WAV files, window offscreen EN/TR); VM (live, 2026-10-21): albums with embedded covers, an album played (position advancing), video library thumbnails, an MJPEG AVI played to its end. No MPRIS yet; sound output itself not heard (VM) |
| `veltos-pdf` (new): PDF Reader in a modern reader layout (own name and artwork, no Adobe marks) — Home with recent files, one tab per document, continuous pages with selectable text, search with results and highlights, page thumbnails, bookmarks (outline), zoom, fit width/page that stays fitted, rotate, read mode, full screen, document properties, passwords, printing; Qt PDF (PDFium); replaces Okular, default for PDF files | 6 unit tests (real PDFs written with QPdfWriter, window offscreen EN/TR, damaged file refused); VM (live, 2026-10-21): a 19-page PDF opened as the default app (`xdg-open`), thumbnails, bookmarks, search (160 results), zoom out/in, properties, app menu, Home with the recent file. Printing untested |
| `veltos-office` (new): LibreOffice 25.2 (Debian) Writer/Calc/Impress set up for Windows users — ribbon-like Tabbed interface, Colibre icons, .docx/.xlsx/.pptx by default without the format question, Carlito (Calibri metrics) as default font, no tip/donation/what's-new bars, crash reports off, Debian's presentation template diverted; Start names "Word Processor"/"Spreadsheet"/"Presentation" (Kelime İşlemci/Hesap Tablosu/Sunu) with Word/Excel/PowerPoint as search words, original page/sheet/slide icons for apps and file types, no splash, default for Office documents, pinned in Start | 5 tests check every setting against the schema/data of the LibreOffice it is built with; VM (live, 2026-10-21): search "word" finds Word Processor; Writer, Calc and Impress open with the Tabbed interface, Colibre icons and Carlito; Impress templates without DebianTalk. Not checked: dark mode, Turkish interface on screen, real Office documents |
| `veltos-photos` (new): Photos in the Windows 11 layout — search in the title bar, Gallery/Favorites/folders, gallery by month (EXIF date) with filter, sort, tile size and slideshow, viewer (zoom, rotate, delete, heart, file information, copy, set as background/lock screen, filmstrip), Edit image (crop, aspect ratios, rotate, flip, brightness, contrast, saturation, warmth; save or save as copy); video thumbnails (ffmpegthumbnailer); default for pictures; replaces Gwenview | 15 unit tests (scan, EXIF, edits with Pillow; window offscreen EN/TR); VM (live, 2026-10-21): gallery of sample pictures, viewer, edit with live preview, save as copy. Not yet checked: lock-screen picture, very large libraries |
| `veltos-notepad` (new): Notepad in the Windows 11 layout — tabs in the title bar, File/Edit/View menus, find and replace panel, go to line, time/date, zoom, word wrap, status bar (line/column, characters, zoom, line ending, encoding), Settings page (theme, font, word wrap, opening, session); keeps UTF-8/UTF-8 BOM/UTF-16/ANSI and CRLF/LF/CR; unsaved tabs come back (Windows 11 session); default for text files; replaces KWrite | 19 unit tests (encodings, line endings, the real window offscreen EN/TR); VM (live, 2026-10-21): opened a CRLF file from xdg-open, File menu, typing, find panel, Ctrl+S kept CRLF, Settings page. Printing untested |
| `veltos-archive` (new): archive manager in WinRAR's layout with Windows 11 controls — open ZIP/RAR (all versions, 7zip-rar)/7Z/TAR/GZ/ISO/CAB…, folders inside, Extract To, Add (ZIP/7Z/TAR.*; RAR creation not possible without RARLAB's program), Test, View, Delete, Find, Info, passwords; File Explorer's Extract All/Extract here/Compress/Add to archive; replaces Ark | 21 unit tests (real 7-Zip and bsdtar; window offscreen EN/TR); VM (installed, 2026-10-21): RAR5 and password RAR, extract, add, Explorer commands. File dialog is Qt's own |
| `veltos-camera` (new): Camera in the Windows 11 layout — picture over the whole window, Photo/Video switch, shutter, last capture, change camera, photo timer, framing grid, sound with videos, Pictures > Camera Roll; "We can't find your camera" without one | 10 unit tests (files, texts; window offscreen EN/TR without a camera); VM (installed, 2026-10-21) with a virtual webcam (v4l2loopback + ffmpeg test picture): preview, photo (JPEG), video (H.264 MP4). Not yet tested with a real camera or microphone |
| Mail: Debian's Thunderbird 140 ESR named "Mail"/"Posta" (veltos-desktop `update-app-names`), restyled like Windows 11's Outlook (`mail/mail.css`: Mica background, white list and reading pane cards, accent selections, accent "New message"), VeltOS caption buttons and quiet defaults through Thunderbird autoconfig (veltos-desktop `tools/firefox.py`) | veltos-desktop unit test for the autoconfig files; verify hook; VM (installed, 2026-10-21): found in Start as "Mail", opens on account setup without privacy tab; later the same day the add-account page as one centred "Add your account" card (VeltOS texts EN/TR, no Thunderbird illustrations or Mozilla links), the cancel question naming Mail, the main window in the system accent. Sending and receiving mail with a real account untested |
| `veltos-calculator` (new): Calculator in the Windows 11 layout — Standard (order of entry, running result above, %, 1/x, x², √x, memory row) and Scientific (precedence, parentheses, 2nd, π, e, exp, mod, n!, DEG/RAD/GRAD, F-E, Trigonometry and Function flyouts), History and Memory beside the keypad (wide) or over it (narrow), navigation pane, Settings (app theme), Keep on top (KWin keep-above), keyboard keys and the calculator key; decimal arithmetic (0.1 + 0.2 = 0.3, 1 ÷ 3 × 3 = 1); pinned in Start | 42 unit tests (engine against Windows behaviour; window offscreen EN/TR); VM (live, 2026-10-20): opened from Start, 12 + 7 × 3 = 57 (Standard), 2 + 3 × 4 = 14 (Scientific), Trigonometry flyout, Keep on top stays above an active window. Not yet: Graphing, Programmer, Date calculation, converters |
| `veltos-snip` (new): Snipping Tool in the Windows 11 layout — Print Screen / Windows + Shift + S dim the screen with the snipping bar (Rectangle, Window, Full screen, Freeform), snip to clipboard + Pictures/Screenshots + notification with the picture; Windows + Print Screen saves the whole screen; window with New, mode, delay, pen, highlighter, eraser, crop, undo/redo, Save, Copy; Spectacle's shortcuts off and hidden | 20 unit tests (window and overlay offscreen EN/TR, crop, freeform, strokes, eraser, notification); VM (live, 2026-10-20): Print, rectangle snip, saved file, notification, markup window, pen and highlighter |
| `veltos-store` (new): VeltOS Store in the Microsoft Store layout — Home (featured banner, rows), Apps with categories, Gaming, search, app pages (screenshots, description, details), Library (updates, installed apps); AppStream catalogue, PackageKit installs, refuses uninstalls that would remove part of VeltOS; replaces Discover in Start and Settings; a failed install says why (permission, not in the catalogue, download, busy, PackageKit's text) and old/missing package lists are refreshed first | 22 unit tests (window offscreen EN/TR without QML warnings, jobs with a stand-in pkcon); VM (live, 2026-10-20): Home, VLC installed and opened from its page, Library, Firefox uninstall refused |
| `veltos-auth` (new): administrator password prompt in the layout of Windows 11's User Account Control (blue band with the VeltOS shield-and-padlock icon, the question, program and details, the administrator's picture, password, Yes/No; EN/TR) as the session's polkit agent; the password checked by polkit's own helper; KDE's agent service masked | 8 unit tests (helper protocol, request mapping, the window offscreen with a stand-in helper: wrong then right password, cancel); VM (live, 2026-10-21 evening): `pkexec` from the session showed the prompt, wrong password refused with the message, right password accepted (polkit journal), agent registered for the session |
| `veltos-clock` (new): Clock in the Windows 11 layout (Focus sessions, Timer with progress rings, Alarm cards with repeat days and snooze, Stopwatch with laps, World clock) and `veltos-clock-agent`, which rings alarms and finished timers while the app is closed (notification with Snooze/Dismiss, VeltOS alarm sound) | Unit tests (when alarms ring, timers, file format, the window offscreen EN/TR); **not yet seen on screen** |
| `veltos-fluent-icons`: Fluent icons/cursors (pinned, verified; Microsoft logos removed), yellow Windows 11 folders, coloured place icons at all sizes, VeltOS "This PC" (cyan screen), Recycle Bin (glass bin with blue recycling arrows, empty/full), folder, Local Disk and Terminal icons drawn in the look of Windows 11 (`tools/draw-icons.py`, separate 16 px drawings for small sizes), thin monochrome "Close" cross, Fluent cursors as the system default pointer | Package checks; VM screenshots; `x-cursor-theme` points to Fluent-cursors (VM) |
| `veltos-boot`: Plymouth splash, GRUB theme, hidden menu, fixed video mode (VirtualBox/Hyper-V fix), kernel titles without the Debian build suffix, keyboard layout in the initramfs, disk-encryption password screen (Inter font, Windows-like texts, box below the logo) | 22 unit tests; boot screenshots; encrypted install screenshots; quiet kernel/systemd options in the installed grub.cfg (VM) |
| `calamares-settings-veltos`: installer with Windows 11 style side bar, buttons and controls (QML + style sheet, Kvantum for its dialogs), live welcome window (English/Türkçe switch signs the live session in again in that language, any number of times; the window comes back when the installer is closed), animated slideshow with screenshots of Start, Settings, File Explorer and the Store and feature texts in the installer's language (QML loads with Calamares' module in the VM; not yet watched during an installation), BitLocker-like encryption (unencrypted /boot, password asked by the boot screen, unlimited tries), firmware entry "VeltOS" | 21 unit tests; VM (2026-10-20, 23:05): English → Türkçe → English with the installer opened and cancelled in between; **encrypted installation tested end to end in a VM (UEFI)** on ISO 20261019-174700: install, firmware entry, boot menu, password screen (wrong and right password), sign-in, desktop — `tests/results/2026-10-19-encrypted-install-uefi/` |
| `veltos-winapps` + `veltos-wine-addons`: double-click `.exe`/`.msi`/`.bat`/`.cmd` → install/run via Wine (Wine "Light" theme), runner window in the Windows 11 App Installer layout; the file starts at once (no question, like Windows); when Bottles/Lutris/PlayOnLinux are installed it asks which to use (none is in Debian 13); the Done page scrolls its program list; App Installer icon; Windows programs told the light/dark mode at every start | 21 unit tests (incl. the window offscreen); VM (2026-10-20, 23:00): 7-Zip installer started from File Explorer without a question and installed, Start entries found; the batch console window itself not yet observed |
| live-build configuration, verify hook (also: Explorer default, Dolphin/System Settings hidden, OS build file, taskbar widgets, installer side bar, console banner) | Passes in every ISO build |
| VM test tools: boot test (BIOS/UEFI/Secure Boot), Windows-program test, preview, long-running VM | See `docs/testing.md` |

### Latest ISO

See the newest entry of `docs/development-log.md` for the ISO name and the
checks that passed.

## Not yet tested

- From the 2026-10-21 evening work: the installer slideshow during a
  real installation, the Windows-program runner's choice page (needs
  Bottles or Lutris installed), the softer sounds by ear, the Turkish
  texts of the new windows on screen, dark mode of the new windows.
  Seen in the live VM (`tests/results/2026-10-21-windows-dialogs/`):
  the file dialogs (alone, Firefox, Konsole, LibreOffice), the password
  prompt, the Wayland greeter, the taskbar search window, the progress
  bar under taskbar icons and Firefox's downloads panel during a
  download, the Clock app and an alarm ringing with the app closed,
  text size at 150 % in Settings and File Explorer, the Windows-program
  runner installing 7-Zip.
- The 2026-10-20 changes (see the development log) were tested by
  installing the rebuilt packages into VMs, not yet on a newly built ISO;
  the quiet boot options, the Fluent cursor default for X11 programs and
  the GTK theme in GTK 4 / libadwaita programs are untested on screen.
- The power key shutting down (needs a VM that may be switched off), the
  locked taskbar for a brand-new user (layout script), dark wallpapers
  and dark title bars on screen, "Switch user" and "Change a password" on
  the Ctrl+Alt+Del screen.

- A plain (unencrypted) installation and any BIOS installation on the
  latest ISO; an installation in VirtualBox (the product owner's setup).
- Secure Boot boot test and `test-winapps` on the latest ISO.
- Bluetooth pages with a real adapter; Display page changes on real
  monitors; accent colour in all apps (Kvantum apps keep the theme's
  blue); blur/translucency with a real GPU.
- File Explorer: mounting drives (udisks), Extract/Compress with Ark, drag
  and drop between windows, large folders, network shares.
- Anything on real hardware.

## Known gaps

- Product owner's requests still open (2026-10-20 list): taskbar transparency/colour/animations closer
  to Windows 11; taskbar hover previews with name and description (needs
  working captures); Windows 11 style for the grey KDE/Qt window
  backgrounds and for inputs, spin boxes and radio buttons in KDE
  programs; "Your info" / "Other users" pages; a busy pointer while apps
  start; a Windows 11 style "Run/Install Windows program" for
  Bottles — **Bottles is not in Debian 13** (Flathub only), decision
  pending.
- Settings left out until they have a VeltOS page: VPN and wired network
  details, proxy, firewall, fonts, pointer style, per-app volume, display
  arrangement and refresh rate, game controllers, tablets, on-screen
  keyboard, spelling.
- Product owner's requests not done yet: Control Panel pages in the
  Settings design; Windows 11 modern Wine dialogs; installer pages; a full check that no old KDE/Qt window is left (KDE's
  own dialogs still open from some places, e.g. "Change a password" opens
  KDE's Users page). Sounds untested by ear.
- Right-clicking the empty taskbar shows nothing (Windows: "Taskbar
  settings"); the desktop menu has no "Display settings"/"Personalize".
- The desktop's "Create New > Folder" still asks for the name in KDE's
  dialog (KNewFileMenu is C++ inside Plasma's folder view; File Explorer
  itself creates "New folder" and renames in place). KDE's "open with"
  dialog remains for programs that open files through KIO without a
  default app (not through File Explorer).
- Bottles, Lutris and PlayOnLinux are not in Debian 13 (checked
  2026-10-21); the runner offers them only when the user installs them.
  Preinstalling them would need Flatpak/Flathub in the image: the
  product owner's decision.
- The authentication prompt is not kept above other windows (KWin on
  Wayland has no secure desktop); the prompt's details are polkit's.
- Taskbar previews: with software rendering the tooltip shows the window
  title only.
- A busy pointer while a program starts is not possible with KWin on
  Wayland (it only draws the app icon, which VeltOS turned off).
- In VMs without 3D acceleration the taskbar shows window titles instead
  of previews (KWin's captures are garbled with llvmpipe).
- Start: for users who signed in before 2026-10-20, File Explorer replaces
  the pinned KDE file manager at the end of the list, not in its place.

- The disk-encryption password screen is in English only (the initramfs
  has no language setting yet); its keyboard indicator is Plymouth's image.
- KDE programs' About dialogs still name KDE and the original programs.
- VeltOS Store: no ratings/reviews, no Flatpak. Discover is not in the
  image (verify hook); a system installed from an older ISO may still
  have it and its notifier.
- ISO is not verified bit-for-bit reproducible. No CI.

## Next steps

1. Current ISO: `veltos-0.1.0-dev-20261021-163819`: boot tests PASS on
   UEFI and BIOS (`out/test-results/20261021-165735-uefi`,
   `20261021-165951-bios`). It contains everything up to commit ef172e2
   (Notepad, Photos, Media Player, PDF Reader, Office); the Mail account
   page (d4c99b9) and the 2026-10-21 evening work are not in it. Its
   packages were checked in VMs one by one (development log of
   2026-10-21); the image as a whole has only had the automatic boot
   test. Still to check: the power key and shutdown on screen, Camera with
   a real webcam, Mail with a real account and in dark mode, the acrylic
   Start on a PC with a GPU.
2. Build an ISO with the 2026-10-21 evening work (veltos-auth,
   veltos-clock, the file dialogs, the search window, the Wayland
   greeter, the icons) and run the boot tests on it (the new check
   expects veltos-auth, veltos-clock and the portal files in the
   image). Then check what is still marked untested: the sign-in
   screen's size in VirtualBox, the installer slideshow during an
   installation, the sounds by ear, the new windows in Turkish and in
   dark mode.
3. Disk Management in the Windows layout (`packages/veltos-disks`, a
   UDisks2 reader exists, no window yet).
4. Listen to the VeltOS sounds on real hardware; measure animation CPU
   cost with software rendering.
5. Plain and BIOS installations; the product owner reinstalls in
   VirtualBox.
6. Installer pages (partitions, users) in Windows 11 style.
7. The open requests listed under "Known gaps", in the product owner's
   order.
8. First run on real hardware.
