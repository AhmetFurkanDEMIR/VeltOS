# Development Log

Newest entries first. Record what was done, what was verified and what
went wrong, so the next person can trust the state of the repository.

## 2026-10-25 — One see-through box around Start

Item 34 of the product owner's list, and their follow-up while it was
being done. While Start was open, Plasma's `expandedItem` box
(`CompactApplet.qml`, the widgets/tabbar frame) surrounded Start's own
backdrop: a box in a box; the same for quick settings and the clock. The
shell override now leaves Plasma's box out for those (it already did for
search). The product owner then asked for the box to be see-through rather
than grey: the four VeltOS taskbar buttons (Start, Task View, quick
settings, clock) draw `Qt.rgba(1, 1, 1, 0.62)` (0.38 pressed) with a
`rgba(0, 0, 0, 0.05)` hairline in light mode and white at 9 % with a white
7 % hairline in dark mode (`Kirigami.ColorUtils.brightnessForColor` of the
background). The dev VM container had stopped between sessions and was
recreated. Verified: veltos-desktop 129 package tests; dev VM, light and
dark, each button open or under the pointer
(`tests/results/2026-10-25-start-button-one-box/`).

## 2026-10-25 — Store installs for standard users; the prompt names the app

Item 33 of the product owner's list, and their follow-up while it was
being done (the prompt's icon should be VeltOS Store's).

- Reproduced in the dev VM with a standard user signed in through SDDM:
  Install failed at once ("Permission was not given"), no prompt;
  PackageKit logged "uid 1001 failed to obtain auth" right after "trying
  to obtain org.freedesktop.packagekit.package-install". pk-console.c
  (PackageKit 1.3.1-1+deb13u1, sources.debian.org) sets the task's
  `"interactive", !noninteractive`, so `-y` forbids polkit interaction;
  the live user's `sudo_on_live.rules` had hidden it. Without -y, pkcon's
  "Proceed with changes?" is read from the controlling terminal
  (`pk_readline_unbuffered` opens `ctermid()`); without one it declined.
- `veltos_store/ptyrun.py`: pkcon in a pty (`pty.fork`), output passed
  through, "Proceed with changes?" answered y, any other [N/y] question n;
  `Jobs` starts `python3 -m veltos_store.ptyrun pkcon -p install X`
  (PYTHONPATH set for the tests' source tree; exit 127 = pkcon missing).
- A refused or failed uninstall kept the app in `_failed` and `state()`
  returned "failed", drawn as Install: failures now remember their action,
  "failed" only while the app is not installed, the reason under the
  buttons (`hasFailure`), "... to uninstall" for a refused removal.
- veltos-auth: `users.requesting_app` walks from `polkit.subject-pid` up
  to eight parents and takes the first argument that names a desktop file
  (VeltOS' renamed copies first) for the prompt's program name and icon;
  falls back to the action's icon.
- Verified: veltos-store 24, veltos-auth 10 package tests; dev VM as the
  standard user: VeltOS prompt with Velt as administrator, install,
  cancelled uninstall (stays installed), uninstall, install again, the
  Store's icon and name in the prompt (`tests/results/2026-10-25-store-standard-user/`).

## 2026-10-25 — Account pictures on the sign-in screen

Item 32 of the product owner's list. The SDDM theme's user list (bottom
left) drew each user's initial; it now shows the user model's `icon` (the
AccountsService picture) masked to a circle, with the initial under it
while no picture loads. `test_sddm.py` builds the theme offscreen with a
user whose picture is a generated PNG and checks that exactly that list
picture loads (its `implicitWidth`: PySide cannot read QML's Image.status
enum reliably). Verified: veltos-desktop 128 package tests; dev VM: SDDM
with Velt and a second user with a picture (`tests/results/2026-10-25-sign-in-pictures/`).

## 2026-10-25 — Hidden taskbar search

Item 31 of the product owner's list. Reproduced in the dev VM with
Settings' search mode 0: the magnifier and "Ara" were drawn over Task
View's button. The search applet's compact box had `visible: !hidden` and
zero width; Plasma sets the compact representation visible again when it
places it, so the zero-wide box painted its contents outside itself. It is
now `clip: true`, `opacity: hidden ? 0 : 1`, `enabled: !hidden` and no
hover while hidden. Verified: veltos-desktop 127 package tests; dev VM:
hidden, icon only, icon and label, box (`tests/results/2026-10-25-hidden-search/`).

## 2026-10-25 — Safely Remove Hardware as Windows 11's menu

Item 30 of the product owner's list. The flyout (Plasma's device
notifier inside the tray's popup) kept a tray heading (back arrow, title,
"..."), drive icons, usage bars and buttons, and after an eject only
wrote a line in the row.

- `DeviceItem.qml` (whole-file override) is a menu entry: "Eject %1" with
  "- <size>" or the state under it, a hover highlight; a click closes the
  flyout and runs the drive's default action (unmount) or, for a volume
  that is not mounted, reports it safe at once. The result comes as a
  notification with Windows' wording, sent with `gdbus` through Plasma's
  executable data source (each argument shell-quoted). Texts in VeltOS'
  own catalog (`translations/tr.po`, `i18nd("veltos-desktop", ...)`).
- `FullRepresentation.qml`: `implicitHeight` from the list's content and
  menu spacing; the tray's `ExpandedRepresentation.qml` treats the device
  notifier like the clipboard (no tray heading) and sizes it from the
  applet's `fullRepresentationItem.implicitHeight`.
- Test drive in the VM: `modprobe scsi_debug removable=1 dev_size_mb=64`,
  `sfdisk` + `mkfs.vfat -n "USB BELLEK"`; a `cd` into the mount from a
  user unit kept it busy for the in-use case.
- Verified: veltos-desktop 125 package tests; dev VM: menu, eject with
  notification and unmount, in-use notification, hover
  (`tests/results/2026-10-25-safely-remove-hardware/`).

## 2026-10-25 — Start and search follow a left-aligned taskbar

Item 29 of the product owner's list. The desktop shell override
(`CompactApplet.qml`) gave Start and search the centred item as popup
parent unconditionally. `startPopupParent()` now returns the centred item
only while the applet's button lies more than 12 % of the panel window's
width from its left edge (centred buttons start around a quarter or more
in; a left-aligned Start sits at the edge), else the button itself; the
binding `visualParent: dialog.visible, root.startPopupParent()` reads it
again whenever the popup opens, so a change in Settings needs no restart.
The JSON spec round-trips byte for byte through `json.dumps(indent=2,
ensure_ascii=False)`, so it was edited with a script. Verified:
veltos-desktop 125 package tests; dev VM: centred, left-aligned (Start
and search), centred again (`tests/results/2026-10-25-left-taskbar-popups/`).

## 2026-10-25 — Programs come to the front

Item 28 of the product owner's list. Reproduced in the dev VM with a
probe window: a link opened by an `xdg-open` child opened a tab in the
running Firefox, which stayed behind with an orange taskbar button; the
same link through `QDesktopServices.openUrl` brought Firefox forward (in
VeltOS sessions Qt uses the portal theme and calls OpenURI with an
activation token), also for a local file. KWin 6.3's
`XdgActivationV1Integration::activateSurface` (read on invent.kde.org)
activates only with the current token of the active window's program;
focus-stealing settings do not apply on Wayland.

- Settings (`launch()` as the default starter: "xdg-open X" through Qt),
  Mail (links, attachments), File Explorer (`ops.open`: documents through
  the portal, `.desktop` files, Windows programs and runnable scripts/ELF
  files through `kioclient exec`), VeltOS AI (actions run in a worker
  thread: a signal hands the link to the main thread).
- Hand-overs to a running instance carry the second start's
  `XDG_ACTIVATION_TOKEN` (Notepad, PDF Reader, Mail as JSON with
  `token`, older list messages still read; Store and Task Manager as a
  word after the request); the running window sets it in its environment
  before `requestActivate()`, which Qt Wayland uses.
- Found on the way (left for item 38): File Explorer's navigation pane
  shows the English folder names (Desktop, Documents...) and "Plain text
  document" in a Turkish session.
- Verified: package tests (Settings 111, Mail 25, Explorer 78, AI 21,
  Notepad 22, PDF 7, Store 22, Task Manager 48); dev VM: Firefox and a
  running Notepad came forward from File Explorer, Firefox from Settings'
  website item (`tests/results/2026-10-25-bring-to-front/`).

## 2026-10-25 — Media card above Quick Settings, MPRIS in Media Player

Item 27 of the product owner's list.

- Quick Settings (`plasma/quicksettings`): `MediaCard.qml` shown in a
  second `PlasmaCore.Dialog` 12 px above the flyout (the clock's technique
  for its notification card) while a player has something: app icon and
  name, title, artist, cover, Previous / Play-Pause / Next, and arrows that
  step `Mpris2Model.currentIndex` through the real players (row 0 is
  Plasma's "multiplexer"). Plasma's API read from its own media controller
  and `kmpris.qmltypes` (PlaybackStatus: Unknown, Stopped, Playing, Paused).
  New Turkish strings ("Sonraki parça", "Duraklat"...); "Next" was taken
  ("İleri", the Wi-Fi page). Plasma's media item left the tray: layout.js
  for new users, `session-fixups` for older trays, Settings' tray list.
- VeltOS Media Player had no MPRIS. `mpris.py` registers
  `org.mpris.MediaPlayer2` and `.Player` with Gio (Qt's event loop is
  GLib's, so the callbacks run in the main thread), reads the QML player
  (objectName "player"), calls the window's `togglePlay()`/`previous()`
  (Windows' Previous rule) and announces changes with PropertiesChanged.
  Found in the VM: PySide had no converter for
  `QMediaPlayer::PlaybackState` through `property()` (also with
  PySide6.QtMultimedia imported), so `Main.qml` gives the state as an int
  (`stateNumber`); the first card once showed Play while playing (most
  likely a state announced before Plasma watched the new name), so the
  service announces everything again 1.5 s and 5 s after start, which also
  brings a video thumbnail made in the meantime.
- Verified: veltos-desktop 125, veltos-settings 111, veltos-media 19
  package tests (MPRIS metadata, variants, introspection); dev VM: MPRIS
  properties with gdbus, Plasma's model with a QML probe, the card playing,
  paused from the card, two players switched with the arrows, the tray
  overflow without Plasma's item (`tests/results/2026-10-25-media-card/`).

## 2026-10-25 — Taskbar date follows the language

Item 26 of the product owner's list. Reproduced in the dev VM: Settings'
Display language wrote only `[Translations] LANGUAGE` to
`plasma-localerc`; after signing in again everything was Turkish but the
taskbar clock (which formats with plasmashell's locale, i.e. `LC_TIME` /
`LANG`) still showed "12:51 PM 10/25/2026". Plasma 6.3's startplasma
(`runStartupConfig`, read on invent.kde.org) exports `LANG` and the `LC_*`
keys of `[Formats]` only when the file has them, so `LC_*` lines from
`/etc/default/locale` (Calamares writes them from the location) would also
win over a `LANG`-only choice.

- `prefs.set_language`: when the current formats are the old language's
  (`LANGUAGE_FORMATS`: en → en_US, tr → tr_TR), they follow the new one;
  `set_formats` writes `LANG` and every `LC_*` key in `FORMAT_KEYS`;
  `formats()` reports the effective time format (`LC_TIME` before `LANG`).
  The page shows the followed format at once.
- Verified: veltos-settings 111 package tests; dev VM: English → Türkçe
  in Settings, the regional format followed, signed in again: "25.10.2026"
  and a Turkish calendar flyout (`tests/results/2026-10-25-taskbar-date-language/`).

## 2026-10-25 — Brightness flyout icon

Item 25 of the product owner's list. plasmashell's OSD asks for
`video-display-brightness` and `input-keyboard-brightness` (UTF-16 strings
in `/usr/bin/plasmashell`, found with `strings -el`); VeltOS' flyout
(`OsdItem.qml`) maps them to the icons quick settings uses
(`brightness-high-symbolic`, `keyboard-brightness-high-symbolic`, both in
Fluent) and adds `-symbolic` to volume icons. A test runs the mapping
function itself in a QJSEngine (it needs a QGuiApplication first: the
build aborted with "Must construct a QCoreApplication before a
QJSEngine"). Verified: veltos-desktop 124 package tests; dev VM: the
brightness flyout through plasmashell's OSD service, the volume flyout,
quick settings for comparison (`tests/results/2026-10-25-brightness-osd-icon/`).

## 2026-10-25 — Lock screen: Windows 11's sign-in sequence

Item 24 of the product owner's list.

- `LockScreenUi.qml` (veltos-desktop's shell override): the sharp picture
  with the time is now a curtain (`ShaderEffectSource` of kscreenlocker's
  `wallpaper` item) over the blurred sign-in background; it goes up in
  420 ms (InOutCubic) and the sign-in box rises in under it; Esc or a
  minute idle bring it down. A correct password (or "Sign in" for accounts
  without one) shows "Welcome" with Windows' five-dot ring (the classic
  5.5 s keyframes, dots 240 ms apart) for 1.3 s before `Qt.quit()`. Waking
  from sleep: the one-second clock tick sees the wall clock jump more than
  20 s (QML timers are monotonic and stand still in sleep) and returns to
  the time without animation, fading in from black. Space and Enter only
  lift the curtain; a letter goes into the password box.
- Found in the VM: the hidden password box kept the keyboard focus after
  returning to the time (keys no longer lifted the curtain; `showClock()`
  gives the focus back), and the sign-in box was drawn above the moving
  curtain (z order fixed). kscreenlocker turns the screen off on every Esc
  release and keeps the key from QML (`UnlockApp::eventFilter`, Plasma
  6.3, read on invent.kde.org): left as it is.
- QEMU cannot show a real wake-up: after `systemctl suspend` and QMP
  `system_wakeup` (new `vm do "wakeup"` action) the virtio GPU stayed black
  and the session was lost; the wake path was tested by moving the clock
  two minutes on with timesyncd stopped (timesyncd's first sync had undone
  the first try). The live session switches lock-on-resume off on purpose
  (`veltos-live-session.sh`); installed systems lock.
- Verified: veltos-desktop 123 package tests (the override test checks the
  curtain, the dots, "Welcome" and the wake path are in the file); dev VM
  screenshots of every step, the curtain also slowed down six times in the
  VM's copy (`tests/results/2026-10-25-lock-screen-animation/`).

## 2026-10-25 — Several monitors, Windows + P, Settings > Display

Item 23 of the product owner's list: a plugged-in monitor shows a picture,
Windows 11's Project chooser, monitors in Settings.

- Reproduced in the dev VM: QEMU's `virtio-vga` with `max_outputs=2`
  (`VELTOS_VM_OUTPUTS=2 build/run.sh vm start`); hot-plugging a second
  `virtio-gpu-pci` did not work, so the second output is "plugged in" from
  the guest (DRM `status` forced on, plus a synthetic `HOTPLUG=1` uevent:
  writing `status` alone sends none and KWin never saw the screen). With
  the event KWin extends the desktop onto the new screen.
- KScreen's kded module (autoload, applies saved layouts) was not loaded in
  the VeltOS session; `session-fixups` loads it when missing.
- `veltos-settings`: `devices.py` reads `kscreen-doctor --json` and plans
  Windows' four choices as kscreen-doctor arguments (Duplicate: the largest
  mode all screens share within each one's preferred size, else the
  largest shared; leaving Duplicate restores preferred modes; numbers fixed:
  a laptop's screen first, then KScreen's ids; the main display kept between
  Extend and Duplicate, display 1 main again after one-screen-only);
  `project.py` + `Project.qml` (the flyout, a layer-shell surface at the
  bottom right, one instance: a second Windows + P moves the choice) and
  `Identify.qml`; the Display page got the arrangement, Identify, Multiple
  displays, main display, orientation and refresh rate, and reads the
  displays again when Qt reports screens added, removed or changed.
- Windows + P: KScreen's `kglobalaccel/org.kde.kscreen.desktop` holds
  Meta+P; a "none" for it in `/etc/xdg/kglobalshortcutsrc` was ignored, so
  `update-app-names` hides it like Spectacle's (new trigger on
  `/usr/share/kglobalaccel`). The test VM had stored the earlier conflict
  as `Project=none` in the user's kglobalshortcutsrc; new systems never
  have the conflict.
- Verified: veltos-settings 110 tests and veltos-desktop 123 tests in the
  package build; dev VM with the rebuilt packages: Windows + P flyout (also
  Turkish), every choice checked with `kscreen-doctor -o`, Settings with two
  displays, Identify on both screens, main display moved, the page following
  Windows + P, unplug and re-plug (`tests/results/2026-10-25-monitors/`).
  Not tested: real monitors, laptops (lid, eDP), projectors, a taskbar on
  the second screen (Plasma shows the taskbar on the main display only).

## 2026-10-25 — VeltOS AI, the assistant pane

Item 22 of the product owner's list: a Copilot-like assistant on the right
edge with ChatGPT, Claude, Gemini and Copilot on the user's own keys, able
to act on the system.

- Checked first: Debian 13 has `qml6-module-org-kde-layershell` 6.3.4
  (layer-shell-qt's QML attached type `Window`: anchors, layer,
  exclusionZone, keyboardInteractivity, scope; from window.h of v6.3.4);
  no unlocked Secret Service in the session (kwalletd6 is only
  activatable under its own name and asks for a wallet password), so keys
  go into `~/.config/veltos/ai.json` with mode 600, said in the pane.
- Services, checked on 2026-10-25: OpenAI's changelog recommends the GPT-6
  family and its newest models call tools only through the Responses API,
  so ChatGPT uses `/v1/responses` (stateless, `store: false`, output items
  sent back unchanged, reasoning items included); Anthropic's Messages API
  at `anthropic-version: 2026-10-21` (Claude Opus 5.5 by default, thinking
  blocks with signatures sent back, `eager_input_streaming` on the tools,
  `fallbacks: "default"`); Gemini's `streamGenerateContent` (the docs now
  lead with the Interactions API; generateContent is kept, with parts sent
  back as received so thought signatures stay); Microsoft offers no API key
  for its consumer Copilot, so "Copilot" is Azure OpenAI's v1 Responses API
  on the user's resource, which the pane says. Models are listed from each
  service with the user's key.
- New package `veltos-ai`: `providers.py` (requests, SSE, the three stream
  formats, errors, models), `tools.py` (13 actions, schema checks, titles,
  running them through VeltOS Settings' helpers), `config.py`, `app.py`
  (conversation with tool rounds, "Allow"/"Don't allow", Stop, one pane per
  user, live theme), QML pane. App icon: the VeltOS "V" with sparkles.
- Found while testing: a test module making a QCoreApplication before the
  window test made the latter abort (QQuickWindow needs a QGuiApplication);
  layer-shell-qt prints "is not a wayland window" offscreen (filtered in the
  window tests); the pane stayed dark after it switched the system to light
  mode, so it now watches kdeglobals.
- Verified: 21 package tests; dev VM: the pane docked with windows making
  room, Windows + C closing it, a stand-in service's conversation with a
  read-only action and two allowed theme switches that really changed the
  system and the pane (`tests/results/2026-10-25-veltos-ai/`). Not tested:
  real conversations (no API keys on the development machine).

## 2026-10-25 — VeltOS Weather

Item 21 of the product owner's list: a Weather app like Windows 11's,
without an API key, from an open source.

- Data source, checked on 2026-10-25: Open-Meteo (open-source weather
  API) has forecasts, air quality, place search (GeoNames) and an ERA5
  archive without a key; its terms allow free non-commercial use (no ads,
  no subscriptions: VeltOS qualifies), 10,000 calls a day per IP address,
  data under CC BY 4.0. MET Norway's API was the alternative; its terms
  ask apps with many users to call it through their own caching proxy.
  Parameter names and answers were checked against real answers for
  Istanbul (kept as test data).
- New package `veltos-weather` (PySide6/QML, the Clock's structure):
  `openmeteo.py` (URLs with four-decimal coordinates, User-Agent, a disk
  cache: forecast 15 min, air quality 1 h, records 30 days, the saved
  answer offline), `conditions.py` (WMO codes → Windows' words and 17
  pictures, skies, units as Windows pairs them, wind directions, AQI and
  UV bands, the moon's phase from the mean synodic month, sentences),
  `app.py` (backend, background thread, settings in
  `~/.config/veltos/weather.json`), QML pages. First start: the city of
  the computer's time zone becomes home. Pictures and glyphs are drawn
  by `tools/weather-icons.py`; the app icon (sun behind a cloud) by
  veltos-fluent-icons' `app-icons.py`.
- Found while building it: Qt 6.8's Item has FINAL properties that a
  QML property named `top` cannot override ("Cannot override FINAL
  property": the whole page did not load); a function named `y` in a
  delegate replaces Item's `y`.
- Verified: 22 package tests (real answers, no network); dev VM with live
  data: first start in İstanbul, search, Ankara's history and favorite
  card, dark and light themes (`tests/results/2026-10-25-weather/`).
- Not done: Windows' Maps page; the device's location (item 40).

## 2026-10-25 — One menu on a right-click in Notepad

Item 20 of the product owner's list ("a right-click in a text document
opens two menus; keep the Windows one").

- Reproduced in the dev VM: a right-click in VeltOS Notepad's text opened
  KDE's text menu (Spell checking, Undo, Redo, Cut, Copy, Paste, Delete,
  Select All) on top of Notepad's own (the whole Edit menu). Notepad uses
  the `org.kde.desktop` Qt Quick style (a QApplication, for the desktop's
  file dialogs), whose TextArea opens `TextFieldContextMenu` from a
  TapHandler on the right button (`onLongPressed` with a 1 ms threshold)
  and on the Menu key; nothing in the instance can turn it off. The
  desktop's and File Explorer's menus for a text file were single.
- Notepad's text is now `QtQuick.Templates`' TextArea (the control
  without a style: no menu, no mobile handles) with the implicit size the
  styles give it. The right button, the Menu key and Shift+F10 open a
  short text menu as Windows does (Undo, Cut, Copy, Paste, Delete, Select
  all); the Edit menu in the menu bar is unchanged. Other VeltOS apps with
  text fields have no menu of their own there, so KDE's text menu is
  their only one.
- Verified: 21 Notepad tests (new: the text is a plain `QQuickTextArea`,
  the Menu key opens exactly one menu with the six actions); dev VM:
  one menu, Copy from it and paste, the text cursor
  (`tests/results/2026-10-25-notepad-one-menu/`).

## 2026-10-25 — New > Word, PowerPoint and Excel documents

Item 19 of the product owner's list: the desktop's and File Explorer's
New menu with blank Word, Excel and PowerPoint documents.

- How the files are made, checked in the dev VM first (LibreOffice 25.2):
  an empty `.docx` or `.pptx` opens in Writer / Impress as a new document
  (title "Yeni Word Belgesi.docx — VeltOS Office Writer", the Word icon,
  Turkish, Carlito 11 / the title slide) and Ctrl+S saves a real Word
  file without a question (5 KB, `file`: "Microsoft Word 2007+"). That is
  what Windows does (an empty new Word document) and keeps the user's
  defaults (language, paper size, VeltOS' fonts). An empty `.xlsx` also
  opened, but Calc's window had a plain document icon in the title bar
  and on the taskbar (reproduced twice); so a new Excel worksheet is a
  small workbook, as Windows copies a template for it: veltos-office
  `blank.py` writes it (Calibri 11, first sheet "Sayfa1"/"Sheet1"), and
  it opened with the Excel icon. Qt names empty Office files by their
  extension; GIO calls them `application/x-zerosize`.
- veltos-office: `blank.py` and `/usr/libexec/veltos-office/blank-document
  PATH...` (fills new, empty files; never touches a file with content).
  File Explorer (`Backend.newItems`, `createNew`) and the desktop
  (`desktop-new DIR word|slides|sheet NAME`, `VeltOSDesktop.qml`) offer
  Folder, then Word Document, PowerPoint Presentation, Text Document,
  Excel Worksheet, Windows 11's order with Office (by extension), only
  while veltos-office is installed.
- Found and fixed on the way: (1) a click on a File Explorer menu item
  also reached the item under the menu (New > Word Document over the
  navigation pane also opened Home): the menu's TapHandlers took only a
  passive grab; now `ReleaseWithinBounds`, also in the same menu of Mail,
  Media Player, Notepad, PDF Reader and Photos. (2) Two New in a row: the
  first name box, closing, reset the rename and closed the new item's box
  too (and a binding loop warning); the box now knows its item by path.
  (3) The desktop's New did nothing for a user without
  `~/.config/user-dirs.dirs` (`.` of a missing file under `set -e`).
- Verified: package tests (office 20, File Explorer 77 with the Office
  kinds and two New in a row, desktop 122 with `desktop-new`'s kinds,
  Mail/Media/Notepad/PDF/Photos); dev VM: the desktop's New submenu,
  "Yeni Excel Çalışma Sayfası.xlsx" made on the desktop with its name
  open and opened in Calc with the Excel icon; File Explorer's New menu,
  "Yeni Word Belgesi.docx" opened in Writer
  (`tests/results/2026-10-25-new-office-documents/`). Not tested: opening
  the files in Microsoft Office.

## 2026-10-25 — Uninstalled Windows programs disappear completely

Item 18 of the product owner's list: an uninstalled Windows program still
showed.

- Reproduced in the dev VM with 7-Zip 26.04: its own uninstaller (started
  from Settings > Apps > Windows programs) removed its files and its Start
  menu `.lnk` files inside the Windows environment, but Wine's menu builder
  only ever adds Linux menu entries: two `.desktop` files under
  `~/.local/share/applications/wine/Programs/7-Zip/`, their `.menu` files,
  the `.directory` files and four icons stayed, so Start search still found
  "7-Zip File Manager" and "7-Zip Help"; VeltOS' installation record kept
  a "7-Zip" row in Settings.
- veltos-winapps: `shortcuts.remove_stale` reads each Wine entry of the
  environment (Start menu, desktop, `wine-extension-*`), works out what it
  opens from its Exec line (the `.lnk` as a Windows path, `start /unix`
  paths, or the ProgID of `start /ProgIDOpen`; format checked in Wine 10.0's
  `winemenubuilder.c`) and removes the entry when that is gone (case
  ignored, as on Windows), with its `.menu`, empty folders and their
  `.directory` files, icons no remaining entry uses and the MIME type Wine
  made up for a removed file type. `programs.forget_removed` also drops
  records whose shortcuts are all gone. Settings runs it after Uninstall
  and when the Windows programs page opens (programs removed by their own
  uninstaller elsewhere), veltos-run after every program it ran.
- Verified: 31 package tests (Exec lines as the VM had them, a home with a
  removed and a kept program); dev VM: the old leftovers vanished when the
  page opened, then a fresh install / uninstall from Settings left nothing
  (`find` empty, Settings empty, Start search without 7-Zip;
  `tests/results/2026-10-25-windows-uninstall/`).

## 2026-10-25 — A Windows 11 style notice after a crash

Item 17 of the product owner's list: DrKonqi's "x closed unexpectedly"
notification in Windows 11's design.

- What happened before (Konsole killed with SIGSEGV in the dev VM):
  systemd-coredump records the crash, DrKonqi's system service passes the
  record as JSON to the user's `drkonqi-coredump-launcher.socket`, and the
  per-crash `drkonqi-coredump-launcher@.service` starts DrKonqi: a toast
  from "Sistem bildirimleri" with `tools-report-bug` (a red "!"),
  "Report Bug" (to KDE's bug tracker) and "Restart Application", and a
  sad-face tray icon afterwards.
- veltos-taskmanager now replaces that service's program (drop-in
  `drkonqi-coredump-launcher@.service.d/veltos-crash-notice.conf`) with
  `/usr/libexec/veltos-taskmanager/crash-notice` (`crash.py`): it reads the
  record, finds the app from the unit Plasma started it in
  (`app-org.kde.konsole-48606.scope`, `app-veltos\x2dcalculator@….service`)
  or the program it ran, and sends one notification with the app's name,
  icon and desktop entry, "<App> closed unexpectedly", a short
  explanation and "Restart" (through Gio). Programs without an app
  (background services) get no notice, as on Windows. KCrash's metadata
  file is removed. DrKonqi's sign-in pick-up of earlier crashes is turned
  off (it would announce them again and scan the journal at sign-in).
- Found while testing: "Restart" first did nothing, because the
  service's unit ends when the script exits and systemd killed the
  detached `kioclient` with it; the script now waits for kioclient.
- Verified: 48 package tests (records of Terminal, Calculator and a
  daemon; texts; pick-up ignored); dev VM: the toasts, "Yeniden başlat"
  bringing Terminal back in its own scope, silence for a crashed
  `xembedsniproxy` (`tests/results/2026-10-25-crash-notice/`).

## 2026-10-25 — Apps start faster; cleaner exits

Item 15 of the product owner's list: apps open slowly after a click.

- Measured first (`tests/results/2026-10-25-app-start/starttime.py`: an
  app's launcher with QQmlApplicationEngine.load patched to report the
  first drawn frame): in the dev VM the apps draw their first frame
  0.3-0.6 s after starting, of which Python/PySide6 imports take about
  0.2 s and compiling the QML 0.1-0.35 s, because every launcher turned
  Qt's QML disk cache off (packaged files share one time stamp, so Qt
  kept stale compiled QML after updates, AGENTS.md).
- `veltos_controls.use()` (veltos-desktop, already called by every
  QGuiApplication app) now points `QML_DISK_CACHE_PATH` at
  `~/.cache/veltos-qml/<app>-<hash of its QML files and PySide6's
  version>` and turns the cache on; an update gives new files a new
  folder and removes the app's old ones. QML loading went down 20-50 %
  (Mail 0.82 → 0.61 s to the first frame; with the CPU limited to 25 %,
  Settings 2.22 → 1.80 s). The rest is imports and the first frame drawn
  by llvmpipe.
- The taskbar already shows a starting app's button at once.
- Stability: the welcome window, Settings, File Explorer's picker,
  Calendar, Clock and the Windows program installer returned from
  `main()` with the QML engine still alive, so at exit its bindings ran
  against deleted objects (TypeErrors in the user journal); they delete
  the engine first now. Crash dumps in the dev VM since the last boot:
  Konsole (fixed in item 10) and one ksplashqml abort while `systemctl
  restart sddm` killed the session (Wayland display gone; a test
  artefact).
- Verified: veltos-desktop tests (the cache folder follows the files);
  dev VM: the timings above.

## 2026-10-25 — Sample pictures, music and a video

Item 14 of the product owner's list: the default wallpapers in Photos,
and a nice video and sound that come with the system.

- Nothing third-party: `veltos-desktop/tools/sample-media.py` synthesizes
  a 63 s ambient song in D major (pads, bass and a soft FM bell
  arpeggio with a ping-pong echo, pure Python, a fixed random seed) and
  makes a 31 s video from four VeltOS wallpapers (slow zooms, 1 s
  cross-fades) and an end card with the logo on VeltOS' navy, with the
  song as sound. The results are committed (`samples/`, 1.3 MB + 3.3 MB)
  so package builds need no ffmpeg; the tool documents how to make them
  again. First attempts: a looped still image fed to ffmpeg's zoompan
  multiplied the frames (zoompan makes `d` frames per input frame), and
  the bells were bright (modulation lowered, a 4 kHz low-pass added).
- veltos-desktop installs them in `/usr/share/veltos/samples/{Music,
  Videos}` and links every wallpaper (light and dark, 3840x2160) into
  `samples/Wallpapers`. Photos' and Media Player's default libraries
  include these folders ("Duvar kağıtları", "Örnek videolar",
  "Örnek müzikler"), as Windows' libraries included its sample files.
- The repository checks treat .mp3/.mp4/.ogg/.wav/.webm as binary
  (`.gitattributes`, `tests/repo`).
- Verified: package tests (the samples in the built tree, the default
  folders); dev VM: Photos with 17 items and the sample folders, Media
  Player's album with its cover, the song playing, the video in the
  video library (`tests/results/2026-10-25-sample-media/`).

## 2026-10-25 — Task Manager: GPU usage

Item 13 of the product owner's list.

- New `veltos_taskmanager/gpu.py`, no administrator rights needed: the
  kernel's DRM fdinfo (`/proc/PID/fdinfo`, `drm-engine-<engine>` busy
  nanoseconds, or `drm-cycles-*` for xe) of the user's processes gives
  each engine's utilization per GPU and per process (the busiest engine,
  as Windows shows); which fds are DRM is looked up every 5 s, the
  counters every second. amdgpu adds `gpu_busy_percent`, VRAM/GTT memory
  and the temperature; NVIDIA's driver reports through nvidia-smi.
- Performance lists "GPU 0", "GPU 1" ... after the network (name from
  lspci, utilization over 60 s, the 3D/compute/video/copy engines,
  dedicated and shared GPU memory, temperature, driver, location); a
  driver that reports nothing (nouveau, virtual machines) says so instead
  of showing 0 %. Processes has a GPU column with the total above it,
  empty when no driver publishes per-process figures.
- Background processes without an icon showed Fluent's
  `application-x-executable` (a window with "!", like a warning); a plain
  program window drawn by VeltOS replaces it (also in "Open with").
- Verified: 43 package tests (recorded i915, xe and amdgpu fdinfo, amdgpu
  sysfs, nvidia-smi, the window with a fake GPU); dev VM: the virtio GPU
  page and the empty GPU column
  (`tests/results/2026-10-25-taskmanager-gpu/`). Not observed on a real
  GPU.

## 2026-10-24 (night) — Num Lock on by default, the user's choice kept

Item 12 of the product owner's list.

- KWin sets Num Lock only when it starts, from `kcminputrc` `[Keyboard]
  NumLock` (0 on, 1 off, 2 unchanged; `Xkb::updateKeymap`, KWin 6.3).
  `/etc/xdg/kcminputrc` now says 0, which also reaches the sign-in
  screen's KWin.
- Windows keeps the state the user left: `veltos-numlock.service` (user
  unit, wanted by `plasma-workspace.target`, `After=plasma-kwin_wayland`
  so it stops first) runs `/usr/libexec/veltos/numlock-state` when the
  session ends. It reads the keyboards' Num Lock lights
  (`/sys/class/leds/*::numlock/brightness`, which KWin keeps in step) and
  writes the user's NumLock (0 or 1); without a light it changes nothing.
- Verified: package tests (the script with recorded lights, the unit and
  the default); dev VM: on in a new session, off after the key, saved as
  1 when the unit stopped, off in the next session
  (`tests/results/2026-10-24-numlock/`). Not observed: a sign-out through
  Start (the `org.kde.Shutdown.logout` call did not end the live session).

## 2026-10-24 (evening) — Windows 11 scroll bars: no line beside them

Items 11 and 16 of the product owner's list: "Open with" showed an extra
line pointing down, Settings Home a straight line left of the scroll bar.

- Both were the same thing: KDE's platform theme gives every
  QGuiApplication the `org.kde.breeze` Qt Quick style, whatever
  `QT_QUICK_CONTROLS_STYLE` says (plasma-integration
  `setQtQuickControlsTheme`), and Breeze's ScrollBar draws a
  `Kirigami.Separator` along the bar whenever it is shown.
- veltos-desktop ships a Qt Quick Controls style of its own,
  `org.veltos.controls` (`/usr/share/veltos/qml`): a Windows 11 ScrollBar
  (a 2 px rounded bar at the edge that widens to 6 px with a faint
  rounded track under the pointer) and a ScrollView that uses it (Breeze's
  ScrollView would create Breeze's bars); every other control falls back
  to Breeze (`import org.kde.breeze` in its qmldir). Every VeltOS app that
  is a QGuiApplication calls `veltos_controls.use()` right after creating
  it, which sets the style with QQuickStyle (after the platform theme has
  chosen) and adds the import path; tests keep "Basic". Kirigami chooses
  its platform plugin (KDE's colours) by the style's name, so a link
  `org.veltos.controls.so` to Breeze's plugin sits in
  `/usr/share/veltos/qt-plugins` (without it Kirigami said "Failed to
  find a Kirigami platform plugin" and fell back to its plain colours).
- File Explorer's "Open with" submenu: "Choose another app" had Fluent's
  `application-x-executable` icon (a window with "!"); no icon now.
- Verified: all twenty packages' tests; dev VM: "Select an app" with More
  apps, Settings Home, File Explorer, the submenu; pixel rows beside the
  bar show only the bar (`tests/results/2026-10-24-scroll-bars/`).

## 2026-10-24 (evening) — Terminal: right-click, Ctrl+C / Ctrl+V, its name

Item 10 of the product owner's list: the Terminal closed on a
right-click, Ctrl+C and Ctrl+V did not copy and paste.

- The crash (dev VM, `coredumpctl`): SIGSEGV in KXmlGui under
  `Konsole::MainWindow::updateHamburgerMenu`. While the menu bar is hidden
  Konsole adds its hamburger menu to the right-click menu and fills it on
  showing, and that code needs the toolbars; VeltOS' layout files
  (`konsole/*.rc`) had removed them to look like Windows Terminal. They are
  back with `hidden="true"`: no toolbar is shown and the menu works.
- Windows Terminal's keys through the layout file's ActionProperties:
  Ctrl+C is a shortcut of Copy, which Konsole enables only while text is
  selected, so Ctrl+C copies a selection and otherwise still reaches the
  program (interrupt); Ctrl+V pastes. Konsole's Ctrl+Shift+C/V and
  Ctrl+Ins/Shift+Ins stay. The right-click menu is Windows Terminal's
  short one (Copy, Paste, Find, Select All, Split View, Clear Scrollback,
  and Konsole's own "Menu").
- The window said "— Konsole" in a Turkish session: Plasma 6.3's
  startplasma sets LANGUAGE from `plasma-localerc` after running the
  session scripts, so `tr@veltos:tr` (the program-name catalogs) became
  `tr` whenever Settings or the welcome window had written that file.
  `veltos-session.sh` now adds the pseudo-language to the file itself
  (startplasma reads it right after the script). This affected every
  renamed program title, not only the Terminal.
- Verified: veltos-desktop package tests (layout files, keys, the session
  script with plasma-localerc); dev VM: right-clicks with and without a
  selection, new tab, Ctrl+C interrupting `sleep 100`, Ctrl+C copying and
  Ctrl+V pasting, the title "— Terminal" after signing in again
  (`tests/results/2026-10-24-terminal/`).

## 2026-10-24 (evening) — VeltOS Graphics Cards

Item 9 of the product owner's list: find NVIDIA and AMD cards and install
their driver completely and properly, in a "Graphics Cards" app that is
also in Settings.

- New package `veltos-graphics` (architecture 2.27). The cards come from
  `lspci -vmmnnk` (PCI class 03xx), the details from sysfs, `eglinfo -B`
  (GBM platform) and `vulkaninfo`; reading runs in a thread so the window
  opens at once. Each card shows its name, the driver in use, an InfoBar
  with one button and Properties. NVIDIA: `nvidia-detect` (installed
  first) names the series, `pkcon install` puts in that driver and
  `linux-headers-amd64` (DKMS), a legacy card that Debian 13 has no driver
  for says so; afterwards "Restart now", and with Secure Boot on a
  one-time password for `mokutil --import /var/lib/dkms/mok.pub`. AMD and
  Intel: the firmware and Mesa's OpenGL/Vulkan drivers installed if
  missing; "Check for updates" runs `pkcon refresh`, asks apt which of
  them has a newer version and updates only those. Virtual machines'
  cards: nothing to install.
- Settings > System > Display has "Related settings > Graphics cards";
  new icons: the app (a graphics card with two fans) and a symbolic one
  for Settings, both VeltOS drawings in veltos-fluent-icons.
- Found in the dev VM with the real pkcon (a recorded RTX 4060 `lspci`
  entry, `out/vm/gfx-fake.py`): the driver installed and DKMS built
  `nvidia-current/550.163.01`; "Use the open-source driver" then hung,
  because pkcon asked which `nvidia-driver-libs` (amd64 or i386, Wine's)
  was meant and waited for an answer: names now carry the architecture and
  pkcon's input is closed. Removing only `nvidia-driver` left 37 packages
  (also with `--autoremove`); the whole NVIDIA set is now removed by name,
  after which only `nvidia-detect` stayed. `pkcon update NAME` fails with
  "No packages were found" when NAME has no update, hence the apt check.
  polkit refuses a program started with `runuser` (no session): test with
  `systemd-run --machine=velt@.host --user`.
- Verified: 43 package tests; dev VM: Start search, the virtio card, the
  recorded AMD card's update check, the NVIDIA install and removal,
  Settings' row (`tests/results/2026-10-24-graphics-cards/`). Not tested:
  real GPUs, Secure Boot, an actual driver update.

## 2026-10-24 (afternoon) — Search the web with Google

Item 8 of the product owner's list: the best match said "Search
DuckDuckGo for …"; it should search Google, with a nice icon and text.

- The row came from KDE's web shortcuts runner (DuckDuckGo is KDE's
  default web shortcut): a generic icon, the kind "App", and in the dark
  theme the Plasma "Open" button drew white on white.
- The taskbar's search window and Start leave that runner out (and KDE's
  settings modules, which Start still listed) and add a row of their own
  under the results: the query, "Search with Google" / "Google'da ara" and
  a magnifier whose ring has Google's four colours (VeltOS artwork, not
  Google's "G" logo), under a "Search the web" heading; with no other
  result it is the best match. The card on the right says "Open results
  in browser"; it opens `https://www.google.com/search?q=` with the query in
  the default browser. Keyboard: Down reaches the row, Enter opens it. The
  "No results" message went (the web row is always there), and the
  card's action is now a Windows 11 style row instead of Plasma's button.
- Verified: 115 package tests (runners, the Google URL, the icon in both
  packages); dev VM: no results (Google row as best match), "not" (Notepad,
  Snipping Tool, then the web row), Down Down Enter opened
  `firefox-esr https://www.google.com/search?q=not`; Start the same
  (`tests/results/2026-10-24-search-google/`).

## 2026-10-24 (afternoon) — The taskbar follows light/dark and the accent every time

Item 7 of the product owner's list: "the taskbar did not change with the
theme and colour once, later it did".

- Scripted as Settings does it, every switch worked (6 light/dark, 7
  accent/mode changes; taskbar background and the active app's line
  sampled after each), so the Plasma side was sound.
- The difference was in Settings: the light/dark switch ran as a detached
  process (`plasma-apply-lookandfeel` takes seconds) and every accent change
  as a separate thread; an accent chosen while the mode switch was still
  running could be undone by the global theme's colour scheme, and the
  mode switch alone sent no palette notice. Settings now runs appearance
  changes one after another (`_appearance`, a lock around the job), and
  the mode switch is `Personalization.set_mode`: the global theme, then the
  chosen accent again (which sends KGlobalSettings' PaletteChanged), or the
  notice alone.
- Verified: 102 package tests (the mode switch applies the accent after
  the global theme and ends with the notice; a second appearance change
  waits for the first); dev VM through the window: dark then red within
  0.5 s, and light, green, dark within about 2 s, both ended with the
  taskbar, kdeglobals and plasmarc in the last state
  (`tests/results/2026-10-24-taskbar-theme/`).

## 2026-10-24 (afternoon) — "is not responding" in Windows 11's design

Item 6 of the product owner's list. KWin shows its helper
`kwin_killer_helper` (a KDE message box: "… is not responding. Do you want
to terminate this application?", "Terminate", "Wait Longer") when a
window that does not answer is closed. Its source (KWin 6.3.6,
`src/helpers/killer/killer.cpp`) gave the interface: `--pid --hostname
--windowname --applicationname --wid --timestamp`, and how it ends the
program (DrKonqi note, SIGABRT, SIGKILL after 4 s, KAuth for other users).

- veltos-taskmanager diverts the helper to its own window
  (`notresponding.py`, `NotResponding.qml`): Windows 11's wording and
  layout, the program's icon and name from its desktop file, equal buttons
  in a grey bar (the Turkish "Programın yanıt vermesini bekle" did not fit
  next to the other button at first: the buttons now share the width and
  wrap). Other users' and remote programs go to KDE's helper.
- Found while testing: the window's height bound to its own minimum looped
  ("Binding loop detected for property minimumHeight"); with the frozen
  program's desktop file name the window shows that program's icon (it
  showed a generic picture) and groups with it on the taskbar.
- Verified: 30 package tests; dev VM: Notepad stopped with SIGSTOP, Alt+F4
  opened the new window after KWin's ping timed out; "Close the program"
  ended it, "Wait" left it running (`tests/results/2026-10-24-not-responding/`).

## 2026-10-24 (afternoon) — No boot menu: start screen with "F6  Recovery"

Item 5 of the product owner's list: after installing, the boot menu
(VeltOS, Advanced options, Recovery) appeared; it should not, a small
"F6 for recovery" hint with a key icon should sit in the bottom right
corner instead, and F6 should open recovery.

- **Why the menu appeared**: VeltOS' menu was already hidden, but Debian's
  `00_header` shows it for 30 s after a start that did not finish
  (`recordfail`), common in VirtualBox (stalls) and after a power loss.
  `35_veltos` now keeps it hidden then (VeltOS counts such starts and opens
  Automatic Repair after two); dual-boot PCs still get it for 5 s.
- **Start screen**: `start-screen` (veltos-boot, standard library) writes
  `/boot/grub/veltos/start-hint.tga` and `start.tga` at update-grub for the
  first mode of `GRUB_GFXMODE` and the system's language: the boot
  splash's background and logo at the splash's place, and the hint (a key
  cap "F6" and "Recovery" / "Kurtarma") 28 px from the bottom right corner,
  pre-rendered at build time (twice as large for 4K). `35_veltos` shows it
  with `background_image -m stretch` while GRUB waits; every VeltOS entry
  puts the picture without the hint back before Linux loads.
- **F6**: `--hotkey=f6` on "VeltOS Recovery"; GRUB 2.12's hidden wait
  starts an entry's hotkey (read in `grub-core/normal/menu.c`; `f6` is one
  of `menuentry.c`'s key names).
- **Found in QEMU**: GRUB loaded the picture but the screen stayed black
  while it waited: gfxterm paints a new background only when it next draws;
  `clear` after `background_image` fixed it (also in the entries).
- **Verified**: 33 package tests (start screen at a mode, 4K, languages,
  fallback mode; the GRUB scripts with stand-ins: hint, recordfail, dual
  boot, failure, no recovery; F6 and the start screen in the entries);
  GRUB 2.12 (grub-pc-bin, grub-mkrescue) in QEMU with the generated
  pictures: the start screen with "[F6] Kurtarma" while waiting, F6 started
  the Recovery entry with the plain start screen
  (`tests/results/2026-10-24-start-screen-f6/`). Not yet seen in a full
  installation: the next ISO's installation test checks it.

## 2026-10-24 (afternoon) — Drive icons: USB stick and Windows drive

Item 4 of the product owner's list: "make the flash drive icon nicer, like
Windows 11; put Windows 11's icon on Windows NTFS drives".

- USB sticks showed Fluent's dark stick with an eject badge; the Windows
  drive had a small blue "app window" on top of the disk. New drawings in
  `veltos-fluent-icons/tools/draw-icons.py`: a USB stick in the local
  disk's family (light grey body seen slightly from above, metal plug, blue
  light) for `drive-removable-media`, `-usb` and `-usb-pendrive`, and the
  Windows drive with a framed blue window (glazing bars) on its front —
  not Microsoft's four-pane logo, which VeltOS does not ship (trademark;
  architecture "Icons"). The large drawings fill more of their frame
  (File Explorer's 44 px tiles showed the disk 25 px wide).
- File Explorer: a removable drive shows the USB stick even when it is
  NTFS (Windows does the same); fixed NTFS drives keep the Windows drive.
- Verified: icon package and File Explorer tests (one new); dev VM with a
  removable disk from `scsi_debug removable=1` (FAT32 "VELTUSB") and the
  NTFS partitions of the installer test: This PC and the navigation pane
  (`tests/results/2026-10-24-drive-icons/`).

## 2026-10-24 (afternoon) — Wi-Fi and Bluetooth lists in Quick Settings

Item 3 of the product owner's list: the taskbar's Wi-Fi and Bluetooth
only led to Settings; they should list networks and devices as Windows 11
does.

- **What**: the arrows on Quick Settings' Wi-Fi and Bluetooth tiles push a
  page into the flyout (StackView, sliding in from the right, back to the
  tiles when the flyout closes). Wi-Fi: Plasma's NetworkModel through
  AppletProxyModel (sorted as KDE's applet sorts) and a KSortFilterProxyModel
  for wireless rows; Connect / the key in place / Disconnect through
  plasma-nm's Handler, as KDE's applet calls it; "Connect automatically"
  goes into the NetworkManager profile with `nmcli` (UUIDs checked, changed
  only when it differs). Bluetooth: bluedevil's DevicesProxyModel for paired
  devices, BluezQt's device list for new ones, discovery while the page is
  open, `pair()` then trusted and connected.
- **Found in the VM**: holding a row with `DelayModelUpdatesRole` while it
  was open froze its data, so a connected network still said "Connect";
  KDE's applet holds a row only while its key is typed, and so does VeltOS
  now. Confirming the pairing code in Plasma's notification closes the
  flyout and destroyed the page that waited for the pairing, so the device
  was paired but neither trusted nor connected; pairing now lives in the
  applet itself. Kvantum-less Plasma buttons have no accent look
  (`highlighted` drew a plain button); `AccentButton.qml` draws Windows 11's
  filled one.
- **How it was tested** (dev VM only, `out/vm/wifisim.sh`, `btsim.sh`):
  three `mac80211_hwsim` radios, two of them access points made by hostapd
  ("VeltOS-Home" WPA2, "Cafe-Guest" open) with dnsmasq for addresses (without
  DHCP NetworkManager stayed "activating"); `btvirt -l2` for two virtual
  Bluetooth controllers, the second discoverable through bluetoothctl.
  Toggling Wi-Fi off rfkills the simulated access points too; restart
  hostapd afterwards.
- **Verified**: 114 package tests; the screens in
  `tests/results/2026-10-24-quick-settings-wifi-bluetooth/` (Turkish
  session). Not checked: real Wi-Fi and Bluetooth hardware, enterprise
  (802.1X) networks, Bluetooth Disconnect (the virtual peers reconnect at
  once, the row stayed "Disconnecting…").

## 2026-10-24 (noon) — The installer's disk page: lists under their box, Windows 11 disk pictures

Item 2 of the product owner's list: "the area that opens overlaps, the disk
sizes look bad". Reproduced in the dev VM with a disk laid out like a
Windows PC (EFI, MSR, NTFS "Windows", recovery; `parted` on the VM's test
disk) at 1920x1080, 1024x768 and 800x600.

- **What overlapped**: the disk list (and the swap list) opened over its
  own box, 15 px up and left, its row's text over the box's text. Kvantum
  turns combo box lists into translucent menus with a shadow, reserves the
  shadow in `SC_ComboBoxListBoxPopup` and gives the list a transparent
  style sheet when it finds Qt's menu delegate. A style sheet alone
  (`combobox-popup: 0`) moved the list but not Kvantum's offset.
- **What looked bad**: Calamares paints the disk bars, the legend and the
  resize bar itself (PartitionBarsView, PartitionLabelsView,
  PartitionSplitterWidget) with Breeze colours, a white box behind the
  legend, `Qt::black`/`Qt::gray` text (unreadable in the dark look) and
  sizes such as "300.00 MiB" and "1628MiB"; no style sheet reaches that.
- **Decision** (architecture 2.25): an installer Qt style,
  `veltos-installer`, a QProxyStyle over Kvantum in a small C++ plugin in
  `calamares-settings-veltos/style/`. It takes over the paint events of
  those three classes and draws the same model at the places Calamares
  computes (`visualRect`; the splitter after Calamares has painted, which
  sets its handle position, with the same arithmetic), so choosing and
  dragging work unchanged; it keeps Kvantum off combo lists and puts them
  under their box; it writes sizes as VeltOS Disk Management does, also
  in the disk list (an identity proxy model, rows unchanged, no change
  signal) and in labels. Alternatives: patching or copying Calamares'
  partition module (a fork of ~20,000 lines), or hiding the pictures with
  the style sheet (no sizes at all).
- **Found on the way**: the Turkish translation writes Calamares' MiB as
  "MB" ("1628 MB olarak küçültülecek"); sizes without "i" are rewritten
  from 1024 on. Dragging right did nothing because Calamares limits the
  shrinking partition to leave VeltOS its required space; dragging left
  worked (1.59 GB -> 1.12 GB). At 800x600 the installer window does not fit
  the screen (Next below the taskbar); Windows 11 itself needs 720p, noted
  in Known gaps.
- **Verified**: 65 package tests (5 new: the plugin in light, dark and
  Turkish against PySide6 stand-ins named like Calamares' classes); the
  dev VM with the rebuilt package: alongside, replace, erase, encryption,
  both lists, light, dark with a red accent, Turkish. Screenshots before
  and after: `tests/results/2026-10-24-installer-disk-page/`.
- Not checked: a full installation with the new style (no job changed),
  VirtualBox.

## 2026-10-24 (morning) — VeltOS Mail rewritten in the layout of the new Outlook

The product owner's new list of 37 items (2026-10-23, in Turkish; tracked
in `docs/dev/status.md`), first priority: "write VeltOS Mail again, exactly
Outlook: the icon, the sign-in screen, the mail environment, everything".

- **Decision** (architecture 2.24): VeltOS Mail is its own app now,
  `packages/veltos-mail` (PySide6/QML), and Thunderbird leaves the image;
  its autoconfig and style sheets left veltos-desktop. Protocols come from
  Python's imaplib, smtplib and email; HTML mail is shown by Qt WebEngine
  with JavaScript off, a script-free Content-Security-Policy, cleaned
  markup and internet pictures blocked until "Show pictures".
- **Window**: the new Outlook's layout (README of the package lists every
  part): blue header with the centred search, app bar, Home/View/Help with
  the simplified ribbon, folder pane with Favorites, Focused/Other with
  date groups, reading pane, compose in the reading pane, Settings, People,
  "Add your account". Icon: first an Office-style blue tile in front of an
  envelope; the product owner did not like it and sent a picture of the new
  Outlook's icon, so it is now a big open envelope in blue-to-violet
  gradients with the letter inside and the lid folded back, and a small dark
  blue tile with a white O at the bottom left (a VeltOS drawing in
  `veltos-fluent-icons/tools/app-icons.py`, checked rendered at 160, 48 and
  32 px).
- **Accounts**: provider settings for Gmail, Yahoo, iCloud, Yandex, AOL,
  GMX, Zoho, Mail.ru, Fastmail (app-password note and link where needed);
  other domains: the IMAP hosts imap./mail./DOMAIN are tried with a 10 s
  limit each, then the first SMTP server that takes a connection; a
  refused password ends the search. Outlook.com accounts need OAuth
  (Microsoft ended passwords for IMAP on 2024-09-16; checked on the web):
  implemented (PKCE, loopback), but VeltOS has no registered client id, so
  the page says so and offers Outlook on the web.
- **Bugs found while testing** (all now covered by tests): Python 3.13's
  strict `getaddresses` returned no recipient when Cc/Bcc were empty
  (mail went to nobody); headers with raw UTF-8 came back as
  `Header(unknown-8bit)` with replacement characters ("Toplant��"); the
  message list's rows read deleted model objects on every reset (54 QML
  errors); WebEngine aborted when another test module had made the
  QCoreApplication first; a send failure marked the account's IMAP as
  unreachable; the server search took minutes (every IMAP guess repeated
  for each SMTP guess, 25 s each); a QML binding closed the add-account page
  before "You're all set!"; the Turkish ribbon ran out of the window (now
  measured: labels when they fit, else icons).
- **Verified**: 24 tests in the package build (as root in the builder,
  WebEngine offscreen) and in the VM; in the dev VM against real servers
  (Dovecot IMAPS with its certificate trusted, Postfix submission with
  STARTTLS and Dovecot SASL, set up by `out/vm/mailseed.py` and
  `mailsmtp.sh`): sync, reading, Other tab, blocked pictures bar, reply
  delivered (`/var/mail/velt`) with a copy in Sent Items and the answered
  arrow on the original, the add-account flow typed through the UI, dark
  mode and Turkish, Start search "outlook". Screenshots:
  `tests/results/2026-10-24-veltos-mail/`.
- **Host clock**: the developer PC's clock is 3 hours behind (Windows time
  not synchronised), so apt refused fresh Debian signatures; builds used a
  snapshot.debian.org mirror of 2026-10-23 12:00 UTC (AGENTS.md).
- Not checked: real Gmail/Yahoo/iCloud accounts (needs the owner's app
  passwords), OAuth, mailboxes with thousands of messages, printing.

## 2026-10-23 (late evening) — Website: minimum requirements, both languages proofread, opaque header, logo link

The product owner on the website: put the minimum system requirements where
the "In a virtual machine" card was; check the English and Turkish texts
("especially the Turkish is broken: no inverted or broken sentences");
the page slides visibly behind the top bar; the logo does not go back to
the top.

- **Minimum system requirements** card next to "Build the ISO" (the
  separate requirements box below the cards is gone): 64-bit x86, 4 GB of
  memory, 20 GB of storage, UEFI (Secure Boot) or BIOS, any graphics,
  "tested in virtual machines only". Memory says 4 GB, not the installer's
  own 2 GB limit: every test so far ran with 4 GB or more, and the live
  desktop uses about 1.5 GB at rest. The virtual machine tips (4 GB, 25 GB,
  3D acceleration, the VirtualBox freeze with Hyper-V) moved to a new FAQ
  entry.
- **Languages**: all 192 texts read again in both languages. Turkish was
  rewritten as Turkish rather than word by word (for example "oturum
  açmadan masaüstüne", which reads as "without signing in", is now
  "oturum açılışından masaüstüne"; "Kaputun altında" is "Perde arkası"),
  with the names the OS itself shows: VeltOS Mail (not "Posta"), VeltOS
  Mağaza, Bu bilgisayar, Görev Görünümü, Başlangıç Onarımı, Komut İstemi,
  and "üretici yazılımı" for firmware as in Windows. English: awkward
  sentences fixed ("The download link is published here soon", a dangling
  "saving"), gallery tabs shortened. New keys: the firmware badge and the
  accessibility labels of the menu, the numbers, the gallery tabs, the
  footer and the picture viewer, which were English in both languages.
  Turkish numbers use a decimal comma and "sn" ("4,0 sn"), also after
  switching languages. The 404 page's texts were rewritten too.
- **Top bar**: opaque (it was 92 % opaque after its blur was removed for
  smoother scrolling, so the page showed through). The menu turns into the
  drop-down at 1120 px instead of 1080 px: the Turkish names did not fit on
  one line at 1081 px and the page scrolled sideways.
- **Logo**: its link pointed at `#top`, the id of the sticky header itself,
  which is always "in view", so the browser did not scroll. The id is gone
  (HTML scrolls `#top` to the top of the document) and a click handler
  scrolls smoothly and keeps `#top` out of the address.
- **README**: its roadmap table removed as well (product owner, after the
  website's); plans live in `docs/dev/status.md` ("Next steps").
- Checked in headless Edge: both logo links return to the top at 1440 and
  375 px; the menu fits or folds at 1000-1440 px in both languages; seven
  widths without overlaps or sideways scrolling; counters "4,0 sn"/"3 sn"
  in Turkish and "4.0 s"/"3 s" after switching; no script errors; every
  text has its Turkish version.

## 2026-10-23 (evening) — Website: download section, no roadmap, smoother scrolling; encrypted installation

- **Encrypted installation** of ISO `20261023-061442` (QEMU, UEFI): "Erase
  disk" + "Encrypt system", 45 jobs, `boot-check` passed; the VeltOS
  password screen at start-up, the sign-in screen about 9 s after the
  password, `tries=0` in crypttab, the desktop after signing in, no failed
  units or core dumps (`tests/results/2026-10-23-installation-bios/`).
- The product owner on the website: remove the roadmap ("Where VeltOS is
  going"); scrolling stutters; the copy button sits on the build commands;
  feature a direct ISO download (the link comes later); on phones the
  "Ready in about 2 s" card disappears.
- **Roadmap** section and menu entry removed (the README keeps its table).
- **Download**: the menu's last entry, the hero's main button and a new
  panel at the top of the download section (version, 64-bit, ISO size,
  firmware, Debian 13; the SHA-256 with a copy button; three steps). The
  link lives in one place, `<meta name="veltos-iso-url">`; empty, the
  button reads "Download ISO · Soon" and a note points to building the ISO;
  checked with a test link in a copy of the site (both buttons link to the
  file, the checksum shows). A GitHub release file must be under 2 GiB and
  the ISO is 2.28 GiB, so it needs another host.
- **Copy button**: the build commands' block has its own bar with "bash"
  and Copy (the button no longer floats over the first line); on phones the
  commands wrap instead of scrolling sideways. Its class no longer shares
  the footer's `.copy` rule.
- **Phones**: the three floating cards in the hero stay (the "ready" card
  was hidden below 640 px) and are placed apart; checked in headless Edge
  at 320, 360, 375, 414, 768, 1024 and 1440 px: no card covers another, the
  copy button covers nothing, the page is never wider than the screen.
- **Scrolling**: the background glows were three 460-620 px circles under
  `filter: blur(90px)` that moved all the time, and the header blurred what
  scrolled under it (`backdrop-filter`); both are drawn again for every
  frame. Now the glows are radial gradients moved by the compositor, the
  header is nearly opaque, the pulsing dots animate transform/opacity
  instead of box-shadow, the hero's endless animations rest while it is
  scrolled away, pictures decode asynchronously, and the scroll handler no
  longer measures every section on each event (IntersectionObservers).
  Measured honestly: in Edge on the developer PC (Intel UHD, 144 Hz)
  neither a scripted scroll nor a traced wheel scroll showed dropped frames
  even before the change, so the stutter the owner saw was most likely in
  another browser (the app's built-in pane, where the page had been shown)
  or while VMs and ISO builds kept the CPU busy; the removed effects are
  the ones known to stutter in software-rendered and embedded browsers and
  on weak GPUs. Not measured on a phone.

## 2026-10-23 (afternoon) — Website, README and handoff files for publishing the repository

The product owner asked for a comprehensive website (desktop and mobile,
animated, light and dark, English and Turkish with English and dark as the
defaults, GitHub Pages, no back end, opening complete from `index.html`
with a double-click), an English README, the agent and README files
finalised, `CLAUDE.md` without the Turkish-language note, the Markdown docs
moved into a folder, and the repository checked for secrets before they
push it.

- **Website** (`docs/`, https://veltos.ahmetfurkandemir.com/): one static
  page (hero, numbers, features, apps, screenshots, Windows programs,
  download and build, specifications, roadmap, FAQ) plus `404.html`,
  `CNAME`, `.nojekyll`, `robots.txt`, `sitemap.xml`; Inter as WOFF2
  subsets (OFL), the OS's own icons, no external requests, cookies or
  analytics. Screenshots from the installed QEMU system (previous entry).
  Every number and claim was checked against the ISO's package list, the
  test reports and the packages' READMEs; untested items were taken out
  (VMware/Hyper-V support) and the measurement method is stated (start-up
  4.0 s and sign-in 3 s, installed system in QEMU, 2026-10-23). Checked:
  all 196 texts have a Turkish version; served over HTTP (images load, no
  console errors, gallery tabs and language switch work); opened from
  `file://` in headless Edge with a throw-away profile (styles, fonts,
  pictures). A bug of the first draft, found there: a second `show()`
  function replaced the gallery's, and nothing on the page appeared.
- **Docs**: `docs/*.md` moved to `docs/dev/` (`git mv`, 61 references in
  23 files updated; every relative Markdown link resolves).
- **README.md** rewritten for GitHub (screenshots, highlights, what is
  inside, try/build, versions from the ISO's package list, testing,
  principles, layout, roadmap, trademarks); `packages/README.md` lists all
  25 packages with their test counts; `tests/README.md`, `build/README.md`
  and `CONTRIBUTING.md` brought up to date; `AGENTS.md` has a website
  section and an updated map; `CLAUDE.md` only points at `AGENTS.md`.
- **Repository checks**: a new `tests/repo` check keeps the website's icons
  identical to the system's; the line-ending check skips the website's
  binary types; `.gitattributes` marks them binary; `.gitignore` adds
  `/.claude/`, editor folders and operating-system files. Secret scan of
  the whole tree: no keys, tokens, host paths, private addresses or test
  passwords (the maintainer address is only in Debian packaging and the
  About page, as before).

## 2026-10-23 (day) — Tests of the smaller ISO: installed systems without initramfs (fixed), VirtualBox stalls, website pictures

The ISO of the morning's work (`20261023-045821`, sha256
`8e705fa4594a55d1b95e154ec05b978c86c33fa9ffd1552d4a384efe60d3cdaf`) is
2,445,506,560 bytes: 2.45 GB instead of 3.62 GB (−32 %), with nothing
removed (architecture 2.23). Its build's 25 package runs ran 688 unit
tests, and the image check passed.

- **Boot tests** (`build/run.sh test`, QEMU/KVM, 4 vCPU, 4 GB, no 3D):
  UEFI, BIOS and — for the first time — Secure Boot (OVMF with Microsoft's
  keys, "SecureBoot enabled" in the guest) passed every check. Live
  start (`systemd-analyze`): UEFI 6.2 s (8.3 s with the previous ISO),
  BIOS 5.6 s (6.4 s), Secure Boot 5.7 s; plasmashell after 20.0 / 18.8 /
  16.2 s; 1.5 GB in use when idle, as before.
- **Windows programs** (`build/run.sh test-winapps`): 7-Zip 26.04
  installed through `veltos-run` with the stripped Wine libraries and was
  recorded; the check for its Start shortcut failed because the test
  itself passed the shortcut file names, which contain spaces, through
  `xargs` (it now uses `find -exec`). Start's search showed both
  shortcuts; right after the installation the File Manager's icon was a
  "?" in that live session. On the installed system below the same
  installation showed the icon in Start; not reproduced since.
- **VirtualBox** (a throw-away VM with the product owner's settings):
  the live desktop was up 80 s after the VM started and the installer
  opened in two seconds, but then the whole VM stopped for 60–232 s at a
  time and went on only when a key was pressed (VBox.log: "TM: Giving up
  catch-up attempt at a 123 317 370 647 ns lag", "Guest seems to be
  unresponsive"). A second VM stopped in GRUB's menu, before Linux ran
  (`debugvm info cpumguest`: real mode, interrupts off, the same
  instruction for minutes, 0 % CPU), and pausing/resuming did not help.
  The throw-away VMs of 2026-10-22 have the same 60 s stalls in their
  logs. VirtualBox 7.2.20 runs in NEM mode on this host (VT-x is taken by
  Hyper-V, which Docker Desktop/WSL2 use); upstream reports the same
  behaviour for other guests, Windows 11 included
  (https://github.com/VirtualBox/virtualbox/issues/722, open: "guest
  constantly hangs until clicking mouse"; Whonix forum: Debian 13 guests
  hang with 7.2.10 in NEM mode). Not a VeltOS fault, and most likely what
  the product owner saw as slow starts and stutter in VirtualBox; nothing
  in the guest can fix a VM that the hypervisor does not run. The
  installation test moved to QEMU (BIOS, like the owner's VM).
- **Installed systems did not start** (QEMU, BIOS): the installation
  finished in about two minutes ("VeltOS is ready"), and the installed
  system stopped at "Kernel panic — not syncing: VFS: Unable to mount root
  fs on unknown-block(0,0)": `/boot` had no initrd.img and grub.cfg no
  initrd line. The ISO no longer carries the live system's initramfs in
  its file system (architecture 2.23), and the installer's `initramfs`
  job made nothing: while Calamares runs from the live medium, the
  target's `update-initramfs` is live-tools' wrapper, which sees
  `boot=live` in `/proc/cmdline` and a read-only medium and exits with "I:
  update-initramfs is disabled". Earlier ISOs copied the live initramfs
  into the installed system, so this never showed. Fixes
  (calamares-settings-veltos): the live packages (live-tools among them)
  are removed before the initramfs job, and a new `boot-check` job stops
  an installation whose kernel has no initramfs or whose boot menu does
  not load it (unit tests: 53 OK). Checked in the VM with the rebuilt
  package: the initramfs job took about 16 s, boot-check passed, and the
  installed system started — `systemd-analyze` 4.09 s (kernel 2.27 s +
  userspace 1.82 s), the sign-in screen about 13 s after the VM started
  (BIOS and GRUB's 2 s included), the desktop 2.9 s after signing in. The
  boot-resolution job, which failed every installation in VirtualBox this
  morning, recorded `GRUB_GFXMODE=1920x1080,…` through pkexec.
- **The ISO with the fix** (`20261023-061442`, sha256 `9d8afa18…`,
  2,445,506,560 bytes; copy on the owner's Desktop as
  `VeltOS-20261023-061442.iso`): 694 unit tests and the image check
  passed; boot tests UEFI 19/19, BIOS 18/18, Secure Boot 20/20
  (`systemd-analyze` 7.0 / 5.6 / 5.7 s), `test-winapps` 7/7 (Start's
  search showed 7-Zip File Manager with its icon this time). A BIOS
  installation from it in QEMU took about 110 s, the initramfs job 12 s,
  boot-check passed, and the installed system started (`systemd-analyze`
  3.98 s, plasmashell 2.9 s after signing in, no failed units, no core
  dumps); a UEFI installation too (45 jobs, boot-check passed, firmware
  entry "VeltOS" through shim, `systemd-analyze` 4.22 s, signed in).
  Evidence: `tests/results/2026-10-23-installation-bios/`.
- **Website pictures**: taken in that installed system (English, 1920x1080,
  a test account "Jordan Lee" with sample documents, pictures and a
  sample mailbox, all VM-only test data): Start, File Explorer with two tabs,
  Settings, Store (after `apt update`), Word's start screen, VeltOS Mail,
  dark mode with the Nebula theme, Automatic Repair's options (the repair
  window started in the session); the installer's first page from the
  live session. Not kept in the repository as test evidence; they are
  the website's pictures.

## 2026-10-23 (morning) — VirtualBox: the installation failed at its end; a lighter, themed installer; faster live start; a smaller ISO

The 38-item ISO (`20261022-214526`) installed in a throw-away VirtualBox
VM with the product owner's settings (BIOS, PIIX3, VMSVGA, 3D off, 16 MB,
4 GB, 4 CPUs; `out/vbox/vbox-install-vm.sh`). The product owner opened it
in their VirtualBox window five seconds after it started and, asked in
chat, said "you drive, I watch" — then went through the installer pages
themselves; the installation ran with their choices.

- **The installation failed at its end**: "boot-resolution: --root is for
  the installer only". Calamares runs through pkexec, so `PKEXEC_UID` is
  in the environment of its jobs, and veltos-boot's helper refuses `--root`
  to callers that came through pkexec. The job had only been run by unit
  tests, never by Calamares. It now calls the helper without that
  variable and can no longer fail an installation (tests with
  `PKEXEC_UID` set and a failing helper).
- While waiting for the owner's answer the owner wrote: fix the installer
  link (clickable), centre a Windows 11 loading animation on the first
  page, steps in the chosen language, the system's theme and colours in
  the installer; the system still starts slowly and stutters; can the
  ISO go under 2 GB (1.8–1.9) — without compromising quality, graphics or
  animation.
- **Stutter**: measured over the VM's serial port (top), the desktop with
  the welcome window was 99 % idle; Calamares on its first page took
  140 % CPU and KWin 110 %. Disabling animations one by one in the live
  VM found the cause: the slideshow's first slide floats from the moment
  Calamares starts (it is loaded at start and visible behind the pages),
  redrawing the window 60 times a second with Mesa's software rasterizer.
  With the fixes in architecture 2.23 (animations only where shown, Qt
  Quick's software renderer where Mesa draws in software, slow motions at
  20 steps a second there): Calamares 24 % with every animation running
  (VirtualBox), 6 % and KWin 19 % (QEMU).
- **Installer look** (calamares-settings-veltos README, "The session's
  look"): light or dark with the user's accent everywhere (QML through
  `VeltTheme.js`, C++ pages through a generated style sheet; Calamares
  applies the branding's `stylesheet.qss` to its main window itself, so
  that file is now a link to the generated one — the first try left a
  light frame around the dark pages), the side bar's steps in English or
  Turkish and switching at once, the website on two lines and a link
  (opened as the user by a 127.0.0.1 helper), the first page's Windows 11
  progress ring in the middle while the page loads, "Checking this PC…"
  while Calamares checks, Qt's own buttons ("Close") in Turkish. Seen in
  the QEMU dev VM with the rebuilt package: light, dark with a red accent
  (welcome, location, keyboard, disk), the Turkish side bar. Found there:
  `config.isNextEnabled` stays false in a QML welcome page (the status
  line never went away); it follows `ViewManager.nextEnabled` now; and
  root's QML cache kept the old page after `dpkg -i` (same file times).
- **Live start** in that VM: kernel 14.1 s + userspace 18.2 s; blame:
  live-config 11.1 s (on the critical chain), `ldconfig.service` 10.6 s
  (no `/etc/.updated` in the image), console-setup 3.2 s, sddm 2.9 s.
  live-config's components timed warm in the VM: user-setup 1.1 s, tzdata
  0.8 s, ~30 others ~90 ms each. Fixes in architecture 2.23.
- **ISO size**: analysed in the builder (package sizes from the image's
  dpkg status, files from `unsquashfs -lls`, each candidate's
  zstd-compressed share, compression settings on 3.9 GB of the image).
  The owner was offered the measured trade-offs and chose "lossless only";
  the lossless savings are listed in architecture 2.23 (about 1 GB of the
  3.62 GB ISO). Not done because they would remove something: xz, Wine
  Mono/Gecko on demand, translations other than English/Turkish, and
  anything under 2 GB.
- Also: `/etc/motd` says VeltOS (veltos-base; the Command Prompt and
  text consoles showed Debian's text).

## 2026-10-23 (night) — The product owner's 38 items: installer, start-up, Automatic Repair, Calendar, VeltOS Mail

The product owner's second list of 2026-10-22 (38 items, in Turkish,
"do every item, skip nothing"), plus three messages during the work
(remove the Kurdish keyboard layouts; add the VeltOS website
https://veltos.ahmetfurkandemir.com/ next to ahmetfurkandemir.com and in
a few more places such as updates). What was done for each item; "VM"
means seen in the QEMU dev VM (UEFI, no 3D) with the rebuilt packages,
"unit" means only package tests cover it.

1. **Taskbar previews like Windows 11**: a KWin script
   (`veltos-desktop/kwin/scripts/veltostaskbarpreview`, architecture 2.19)
   draws one card per window (icon, title, close button, live picture)
   with KWin's own thumbnails, which work in software rendering; pointing
   at a card shows that window alone (Peek). VM: cards and Peek; two File
   Explorer windows gave two cards with live pictures.
2. **Show desktop** wider and flush with the screen's right edge (the
   panel's right margin removed, `org.kde.panel.json`). VM: about 17 px
   at the very edge (hover).
3. **Tray tooltip** "Close popup" stayed over the open tray flyout:
   the expander arrow's tooltip is off while the flyout is open
   (`org.kde.plasma.private.systemtray.json`). VM: no tooltip over the
   open flyout.
4. **LibreOffice Draw** hidden from Start, search and "Open with"
   (`update-app-names`: NoDisplay and no MIME types); it stays installed
   because Impress (PowerPoint) depends on it. Unit.
5. **Save dialog**: the file type box no longer runs off the window and
   the portal dialog follows the session language ("Dosya adı", "Kayıt
   türü", "Kaydet", "İptal"). VM.
6. **Installer** in the Windows 11 setup look (architecture 2.15): VeltOS
   QML for the welcome, location, keyboard, users and finished steps
   (illustrations, sliding pages), the partition page restyled, message
   boxes and the error dialog styled (`-stylesheet`), a new slideshow
   with screenshots of VeltOS apps, Back/Next/Cancel hidden while
   installing; the log appears only on the finished page of a failed
   installation. Kurdish keyboard layouts are not offered. VM: every page,
   a full installation (about 3.5 min, "VeltOS hazır"), and a deliberately
   failing job showing the styled error and the log box.
7. **Notifications** in Windows 11 style: toasts slide in from the right
   (KWin effect `veltostoast`), the "…" menu turns the app's
   notifications off or opens Settings. VM: a toast with the app's name,
   "…" and close, its menu ("Bildirim ayarlarına git"; turning off needs
   a sending app, the test toast had none). On the way: Fluent's
   `view-more-symbolic` is the horizontal "…".
8. **Firefox icon** smaller, like the other icons: `pad-app-icon`
   (veltos-fluent-icons) wraps Firefox's own icon with Windows-like
   margins at installation and, through a dpkg trigger, whenever Firefox
   updates it. VM.
9. **Start-up screen size** (architecture 2.16): the installer writes the
   screen's preferred mode for GRUB and the splash; at sign-in the mode
   the screen is set to is kept in step (pkexec helper, polkit action).
   Unit (7 tests and the installer job's test); VM (installed, UEFI):
   after signing in at 1920x1080 the next start's frame buffer was
   1920x1080 (it was 1024x768 before). VirtualBox: see the next entry
   (2026-10-23, morning).
10. **Faster start and sign-in** (architecture 2.17): AppArmor's profile
    cache built into the image (11 s → none at boot); xdg-desktop-portal's
    GTK "last resort" for Lockdown (25 s) and plasmashell's wait for the
    portal removed. VM (installed system): `systemd-analyze` 3.85 s
    (kernel 2.1 s + userspace 1.7 s); the desktop about 2 s after signing
    in (was about 30 s).
11. **Properties** of files and folders in File Explorer and on the
    desktop: a Windows 11 Properties window (General, Security, Details;
    OK, Cancel, Apply), and Windows' menu for files on the desktop. VM.
12. **Recycle Bin**: the desktop icon shows full and empty again (the
    desktop watches the trash itself), "Restore all items", Cut and
    Properties in its menus. VM: full, then empty after emptying.
13. **Automatic Repair** (new package `veltos-recovery`, architecture
    2.18): GRUB counts starts, two unfinished starts open a Windows 11
    style repair screen on the frame buffer with Restart, Startup Repair,
    Safe mode, Command Prompt, Problem details, Continue and Turn off.
    VM: see the verification below; three faults found there and fixed.
14. **KDE's old settings and file manager** cannot be opened by users:
    KDE's settings programs are root-only (dpkg-statoverride) and
    redirect to VeltOS Settings, `keditfiletype` included; Dolphin is not
    in the image. VM: the `*.kde` programs root-only. Found there: the
    redirect itself was root-only too, so `systemsettings` and
    `kcmshell6` said "Permission denied" to users instead of opening
    VeltOS Settings — `kinfocenter.kde` is KDE's symlink to
    `systemsettings` (now the redirect) and the postinst's chmod followed
    it. The postinst skips symlinks and restores the redirect's mode (with
    a test running it in a sandbox); after that `systemsettings` opened
    VeltOS Settings.
15. **Search "no results"**: icon and text centred in the window,
    Windows 11 style. Unit; in the VM every query also gets the web
    search result, so the message did not appear.
16. **Nested grey boxes** around menus: Kvantum's menu was drawn as a
    square body inside a rounded frame; VeltOS' Kvantum theme now draws
    one rounded box (`tools/fluent.py`). VM: the desktop menu, light and
    dark.
17. **Tab in Settings** jumped to the navigation: the text fields were not
    in the Tab chain. Fixed in Settings, File Explorer and its dialogs,
    Store, Media Player, Clock, Office, Photos, PDF Reader, Disk
    Management and the password prompt. VM: reproduced before the fix;
    after it Tab went Full name → User name → Password in Add account.
18. **Text pointer** (I-beam) over the text fields of the same apps. Unit
    (the VM's screenshots do not show the pointer under Wayland).
19. **User Account Control** in the session language with OK/Cancel
    ("Tamam"/"İptal"): the agent passes the full locale to polkit, the
    VeltOS shield stands in for programs without an icon. VM: polkit's
    message in Turkish, "Tamam"/"İptal", the shield for AccountsService.
20. **Adding a user failed** on installed systems: the calls lacked
    D-Bus' interactive flag, so AccountsService answered "Authentication
    is required" without asking; now the VeltOS password prompt appears
    (5 minutes to answer). Names are taken as typed, as on Windows
    ("Ayşe Yılmaz" → login name `ayseyilmaz`, full name kept). VM: a user
    created with the password prompt (live system without its allow-all
    rule), then on the installed system — where it asked twice (create,
    then set the password: each `gdbus` call is a new process, and polkit
    keeps an administrator answer only for the process that got it). Both
    calls now run in one helper process (`veltos_settings/admin_calls.py`,
    the hash through standard input, not the command line): VM, one
    prompt, the account created with its password (`passwd -S`: P).
21. **Task View icon** no longer filled black (drawn as outlines). VM.
22. **Windows programs** in Settings at once and in the Windows 11
    "Installed apps" layout: read from Wine's registry files (architecture
    2.21) instead of starting Wine's uninstaller window. Unit (registry
    fixture); VM: the page at once, with its empty state (no Windows
    program installed in that VM).
23. **Firefox downloads**: Windows 11 style download toast (progress,
    Open file / Open folder) replacing Plasma's job item. VM: during and
    after a large download.
24. **Store**: the Apps tab's selection line no longer covers the label.
    VM.
25. **File Explorer's Home icon** in the accent colour (tab, navigation
    pane, address bar). VM.
26. **This PC, Recycle Bin and Store** on the desktop cannot be deleted,
    cut or renamed, not even from a terminal (architecture 2.20). VM:
    `rm` refused for the three, the user's own files deletable.
27. **Camera icon** redrawn wider, in the proportions of the others.
    Rendered and compared.
28. **Taskbar right-click**: "Taskbar settings" and "Task Manager", and a
    new Settings > Personalization > Taskbar page (search box style,
    Task View, alignment, Show desktop). VM: the menu, and the page
    showing the taskbar's current settings.
29. **Default taskbar pins**: File Explorer, Firefox, Settings, Store,
    Camera, Photos, Media Player (for new users; Plasma's layout script).
    VM: a user added in Settings signed in to exactly these seven, in
    this order.
30. **Sound indicator** on taskbar buttons: a round badge with a Fluent
    speaker, for every app playing sound (Firefox too). VM: the badge on
    Media Player while it played a tone.
31. **Several windows of one app**: the stacked button shows only a
    second plate's edge in the plate's own colours (the first version
    looked like two different boxes). VM: two File Explorer windows.
32. **Brightness bar** at the bottom like the volume one, also when the
    brightness changes in Quick Settings. VM.
33. **Media Player full screen**: the control bar stays centred (both
    sides of the bar equally wide); the volume slider works again (the
    logarithmic conversion is done in QML). VM: in full screen the
    buttons and the time bar in the middle of the screen (with a sound
    file; the VM has no video encoder to make a test video).
34. **File dialog drop-down** in the wrong place when first opened: the
    menu's position was computed from its size before the new items were
    laid out; it now follows the size (and is never wider than the
    window, long file types shortened). VM: Notepad's Save As, the type
    list on the first click right above the box, as wide as it.
35. **Clipboard and devices flyouts** in Windows 11 style: "Clipboard
    history" with Clear all and the copied items as cards (a click pastes
    it back, "…" deletes it), the device list as Windows-like rows. VM:
    the clipboard flyout (a doubled heading fixed afterwards) and the
    devices flyout ("Donanımı Güvenle Kaldır" with the VM's disc; a QML
    error that kept it from loading was fixed on the way).
36. **Calendar app** (new package `veltos-calendar`): Windows 11 Calendar
    layout (day, work week, week, month, year; quick event card and
    editor; repeats; reminders rung by VeltOS Clock's agent, no new
    resident process); one iCalendar file. Unit (store and window). VM:
    the first start showed the left pane across the window and the
    calendar as a strip at its edge — a layout whose children fill their
    width expands itself unless told not to; the pane now has a fixed
    width and a test checks both widths. After the fix: the month view,
    a click on a day opening the quick card, an event saved and shown and
    written to the `.ics` file. Seen afterwards in that screenshot: the
    small month calendar labelled Monday "Pz" (Qt's "Pzt" cut to two
    letters, which reads as Pazar, Sunday); it now uses the taskbar
    clock's two-letter names ("Pt Sa Ça Pe Cu Ct Pa"), with a test.
37. **VeltOS Mail** like Outlook (architecture 2.22): Thunderbird named
    "VeltOS Mail" everywhere it is listed, Outlook's blue title band with
    the name and a centred search box, the simplified ribbon below it
    (New mail filled), the reading pane with the subject first and a
    round sender picture, the new message window without a menu bar and
    with a filled Send button, the add-account card naming VeltOS Mail,
    the account page without Thunderbird's story, donation request and
    links, names only in the message list. VM (installed, a test account
    with three messages): every one of these. Found on the way: a
    `mail-header.css` with a default XUL namespace matched nothing; file
    URLs generated on Windows had backslashes (no Mail style sheet
    loaded); the compose window's hidden menu bar left a strip of labels.
38. **Store in a second desktop**: a second Store window opens on the
    current desktop. VM.

Also: modal dialogs (those with a parent window, like message boxes)
have only a Close button (Aurorae; unit — a parentless `kdialog` question
in the VM still had Minimise, see known gaps), the VeltOS website in
Settings' About and Windows Update pages, the installer's side bar, the
live welcome window, `os-release` (`HOME_URL`, `SUPPORT_URL`) and the
README.

Automatic Repair in the VM (installed system, packages of this change):
a normal start set `veltos_failed=1` and `veltos-boot-ok` cleared it 10 s
after the sign-in screen; with the count at 2 GRUB started "VeltOS
Recovery" and the screen came up in Turkish at 1024x768; Advanced
options, Problem details (the previous start's error), Startup Repair
(all six steps, then "Başlangıç Onarımı tamamlandı") and Restart (normal
start) worked. Fixed after the VM showed them:

- "Choose an option" did not fit 1024x768 (one column; Back over a tile,
  the last tile off the screen): two columns whenever two tiles fit,
  narrower margins on small screens, and a test at 1024x768 and 800x600.
- Command Prompt never appeared and the screen waited for ever: Qt's
  linuxfb keeps its console in graphics mode and Linux ignores console
  switches then. The window now ends (status 3), `run-recovery` opens a
  sign-in on the next console with the system's console font (the
  kernel's font had no "ı"/"İ") and a hint, and brings the window back on
  the options after `exit`. VM: signed in, `exit`, back on the options.
- Safe mode stayed black: Debian's kernel has no simpledrm, so with
  `nomodeset` there is no DRM device and Wayland cannot run.
  `veltos-safe-graphics` switches SDDM to X11 for such starts and the
  sign-in screen starts Plasma on X11 (fbdev). The first packaged version
  still showed a black screen: Plymouth's frame-buffer renderer leaves
  the console in graphics mode, so Linux ignored the switch to SDDM's
  console and Xorg waited in `vt_waitactive`; the service now runs after
  Plymouth and sets the console back to text mode. VM: a safe start from
  the boot entry (`nomodeset`), the X11 sign-in screen by itself, the
  desktop as an X11 session at 1920x1080 (GRUB's mode, see item 9); the
  next normal start without the setting and on Wayland, although SDDM
  remembered the X11 session.
- Item 9 seen in passing: after a sign-in at 1920x1080 the safe start's
  frame buffer was 1920x1080 too (GRUB took the mode the sign-in sync
  wrote), where the first recovery start had 1024x768.
- After the repair finished, Enter went to the options page's hidden Back
  button; the keyboard now starts on the shown page's own button.

ISO of this work: `veltos-0.1.0-dev-20261022-214526` (sha256 e25a55c2…,
3.62 GB). Every package's tests passed in its build (644 tests in 24
packages, and the 7 repository tests); the verify hook: "all checks
passed". QEMU boot tests: UEFI 19/19 (the AppArmor cache check is new),
plasmashell after 19.0 s (18.8 s with the previous ISO), AppArmor 0.0 s;
BIOS 18/18, plasmashell after 16.4 s (18.9 s). Afterwards, from the VM
screenshots and a review: the Calendar weekday letters (item 36) and the
desktop guard, which had no tests and made the desktop writable for the
user's group even when that group is shared with other accounts (now only
for user private groups, Debian's default; 15 tests on a fake account's
home, those that change owners run as root in the package build).

## 2026-10-22 (17:00) — Windows 11 polish batch: desktop menus, Disk Management, search, taskbar colour

The product owner's list of 24 items (in Turkish, 2026-10-22 midday),
what was done for each and how it was checked:

- **Office Save/Open dialogs, Photos "Add folder", VeltOS dialog
  everywhere (1, 23)**: the regression of ISO 093321 (plasmashell's
  drop-in took the portal theme from every program started from Start,
  see the 13:30 entry below) is fixed in the source; the boot test's
  check is back to its original form (`xdgdesktopportal` in plasmashell's
  environment).
- **"LibreOffice" flashing on the taskbar (2)**: `/etc/xdg/kwinrulesrc`
  (veltos-desktop) keeps windows of class `soffice` (LibreOffice's
  start-up window, before the module sets its own class) off the taskbar.
  Seen by the owner in VirtualBox. In QEMU a KWin script logging every new
  window saw only the start screen (`libreoffice-writer`, "Word") and
  Writer's own window (`libreoffice-writer`, "Untitled 1 — VeltOS Office
  Writer"): no extra window there; what QEMU shows is the Word button
  leaving the taskbar for a moment between the start screen closing and
  Writer's window appearing. The rule is unit-tested only.
- **File Explorer's Home icon in the accent colour (3)**: `NavPane.qml`,
  the Home row's icon is a mask in `Theme.accent`.
- **Personalization icons (4, 5)**: Fluent's `preferences-color` and
  `preferences-desktop-theme` symbolic icons and a VeltOS
  `veltos-colour-mode` icon (half sun / half moon) in veltos-fluent-icons;
  Settings' Home and Personalization rows use them.
- **Colour mode on Settings' Home jumped to "Browse themes" (5)**: the
  drop-down's popup was not modal, so the press that closed it also hit
  the row underneath (TapHandlers take a passive grab); `VComboBox`'s popup
  is modal (no dim) and the rows' TapHandlers use `ReleaseWithinBounds`.
- **Volume OSD at the bottom (6)**: `plasma-overrides/files/osd/` (a
  shell-package override — plasmashell 6.3 loads the OSD from the desktop
  shell package, not from the global theme, where a first version sat
  unused): a rounded card above the taskbar, icon, Windows 11 slider and
  percentage, rising in with a fade. KWin centres OSD windows at two
  thirds of the screen (Placement::placeOnScreenDisplay), so the window
  is 2/3 of the screen minus 80 px tall and its bottom edge, where the
  card sits, ends 24 px above the taskbar (KWin script measured the
  window at 342 × 640 px, bottom at 1008 of 1080).
- **Disk Management (7)**: new package `veltos-disks` (see
  `docs/dev/architecture.md` 2.14): the volume list over the disk map, menus
  and dialogs of Windows' Disk Management on UDisks2; KDE Partition
  Manager hidden and out of the image; Settings > Storage and Win+X open
  it.
- **Task View (8)**: desktop cards show the windows on that desktop
  (`KWin.WindowThumbnail` per window, scaled from `frameGeometry`),
  right-click or double-click switches to the desktop, the selection
  frame wraps the card.
- **Add keyboard (9)**: 50 layouts with Turkish first (Q, F, Alt-Q) and
  the most common ones after; the dialog opens on Turkish.
- **Tab in Settings (11)**: the navigation items are not in the Tab chain
  (`activeFocusOnTab: false`), so Tab moves to the next control of the page.
- **Desktop refresh, new items, protected icons (12, 16, 17, 18)**: Plasma's
  folder view gets `VeltOSDesktop.qml` (override `org.kde.desktopcontainment`,
  `docs/dev/architecture.md` 2.3.8a): Windows 11's desktop menu (View, Sort by,
  Refresh, Paste, New, Display settings, Personalize, Open in Terminal),
  New > Folder / Text Document made at once with Windows' names
  (`desktop-new`) and the name box open, Refresh/F5 blink the icons, the
  Recycle Bin, This PC and the Store have their own small menu (no
  Delete/Rename/Cut; Empty Recycle Bin asks File Explorer's Windows 11
  question in a window of its own, `veltos-explorer --empty-recycle-bin`)
  and the Delete key, F2 and Ctrl+X skip them; the Store comes back at
  sign-in like the other two. File Explorer's New > Folder opens the name
  box once the listing shows the item (before, a slow folder found no row
  and kept "New folder"); F5 blinks the view.
- **Recycle Bin icon (13)**: a systemd user path unit watches the trash
  and touches the desktop launcher, so the desktop re-reads its icon
  (full/empty).
- **Nested grey boxes around menus (14)**: not reproduced in QEMU (every
  menu is one rounded box); left open in `docs/dev/status.md` with what is
  needed (a screenshot from the owner's VM).
- **Search window (15)**: a plain field with the accent line under it
  (the blue frame is gone), results in a Column (rows overlapped in the
  ListView when results arrived), only Windows' kinds of results
  (`runners` without KDE's settings modules), the best-match card filled
  again (it stayed empty: `best` read `Repeater.itemAt()` once and kept a
  destroyed row after the model reset), the window still slides up from
  the taskbar (KWin's sliding popups, `animated: true`). The box the owner
  saw around the taskbar's search box was Plasma's "expanded applet"
  highlight (`CompactApplet.qml`, `widgets/tabbar` active tab): off for
  the search box. Plasma's panel focus box (`Panel.qml`, "Panel Focus
  Indicator") now shows only when moving through the taskbar with Tab.
- **Dialogs (19)**: moving to the Recycle Bin asks nothing (`kiorc`
  `ConfirmTrash=false`, like Windows); Empty Recycle Bin from the desktop
  is VeltOS'; the rest is listed under known gaps.
- **App icons for .desktop files in Explorer (20)**: `files.desktop_entry`
  reads Name/Name[tr]/Icon; the type reads "Shortcut".
- **Media Player's category (21), Office and PDF in their own (24)**:
  `start-categories` maps Office;WordProcessor/Spreadsheet/Presentation
  and Office;Viewer to "Office"; Start shows every non-empty category
  (Entertainment with Media Player alone, before: three or more only).
- **Old KDE Settings / file manager never reachable (22)**: the search
  window's runners no longer list KDE's settings modules; KDE Partition
  Manager and the crash viewer are hidden; what the owner saw as "the old
  file manager" was most likely KDE's file dialog of ISO 093321 (item 1).
- **Taskbar colour transition (10)**, read as: the taskbar takes on the
  theme and the accent colour, with a smooth change. `TaskbarTint.qml`
  (added to Plasma's panel view, `Panel.qml`): a soft glow of the accent
  behind the centred icons over the light or dark background, a 0.6 s
  cross-fade and one band of colour sweeping across the bar when the
  accent or the mode changes; nothing moves at rest. On the way: the
  VeltOS Plasma themes carried their own `colors` file (Fluent's), so the
  taskbar, Start and the flyouts never followed the accent the user chose
  (Start's search field stayed VeltOS blue with a red accent); the themes
  now have none and Plasma follows the system scheme. And
  `plasma-apply-colorscheme --accent-color` does not tell plasmashell:
  Settings now sends KDE's PaletteChanged signal
  (`org.kde.KGlobalSettings.notifyChange 0 0`, as KDE's colours module
  does), and the change shows at once.

Verification in the live VM (QEMU/KVM, UEFI, no 3D, ISO 093321 with the
rebuilt packages installed; `tests/results/2026-10-22-windows11-polish/`):

- Desktop: the Windows 11 menu with its View and New submenus; New >
  Folder made "New folder (2)" with the name box open, "Photos" typed
  and entered renamed it; New > Text Document the same ("Notes.txt");
  the Recycle Bin's menu (Open, Empty Recycle Bin, Properties); Empty
  Recycle Bin opened File Explorer's question and Yes emptied the trash
  (0 files, the icon back to empty and the icon still second on the
  desktop). Found and fixed on the way: Plasma's folder view leaves
  right-clicks on empty desktop space to the containment (the override
  now accepts them), `urlForIndex` is not callable from QML (the item's
  file name comes from the delegate), `desktop:/` is never resolved to a
  path by the model (`desktop-new` resolves it), an immediate `rename()`
  edited the previously current item (the override waits until the new
  delegate is current), a plain `touch` moved the Recycle Bin to the end
  of the desktop (the date now alternates @2/@2.5), and
  `kioclient remove trash:/` does nothing (`ktrash6 --empty`).
- OSD: the volume flyout above the taskbar at 70 %, after moving the
  override from the global theme (never read) to the desktop shell
  package and sizing the window for KWin's placement.
- Settings: Colour mode Dark then Light on Home, the page staying on
  Home both times (the first fix, a modal popup, was not enough: the
  option rows' TapHandlers needed `ReleaseWithinBounds` too).
- Start: the Office category with Word, Excel, PowerPoint and PDF Reader;
  Entertainment with Media Player alone.
- File Explorer: the Desktop folder with the launchers as "Shortcut"
  with their icons; New > Folder with the name box open at once.
- Photos > Add a folder: the VeltOS Select Folder dialog.
- Disk Management on the VM's blank 40 GB virtio disk: "Not
  Initialized" with Initialize Disk…, initialized as GPT, New Simple
  Volume (NTFS "Data", 40 GB) made by UDisks2, its menu, Format as ext4
  through the warning, Delete Volume: `lsblk` confirmed each step
  (gpt → vda1 ntfs Data → no partition). Found on the way: the file
  system list was empty because the session's PATH has no `/usr/sbin`
  (fixed), the blank disk's menu lacked Initialize (`table` is
  undefined, not null, in QML), a ScrollView binding loop in the map.
- After a session restart (KWin and the panel read their QML at start):
  Task View's "Desktop 1" card with the File Explorer window on it, the
  frame on the card's edge, "New desktop", a right-click on "Desktop 2"
  switching to it and a double-click on "Desktop 1" switching back; the
  search window's best-match card filled in and no box around the
  taskbar's search box; Word started from Start, Blank document, Ctrl+S:
  the VeltOS Save dialog with "Word 2007 (.docx)"; Add a keyboard opening
  on Turkish Q; a long new name ("New Text Document (2).txt") in a box
  without a scroll bar; the taskbar's glow red with a red accent and the
  band crossing the bar when the accent changed from green to blue
  (frames); the Empty Recycle Bin window fixed-size with maximize
  disabled (Wayland ignores the window flags; minimize stays). Settings >
  Colours, a click on orange: the taskbar turned orange at once.
- ISO `veltos-0.1.0-dev-20261022-134251` (sha256 8b82b9a7443298b0…,
  3 621 720 064 bytes; verify hook: all checks passed): QEMU boot tests
  18/18 UEFI (`out/test-results/20261022-140957-uefi`, plasmashell after
  18.8 s, idle 1537 MiB) and 17/17 BIOS (`20261022-141158-bios`, 18.9 s),
  including "portal file dialogs" in plasmashell's environment, which the
  093321 ISO failed. Start in the test's screenshot shows the Office and
  Entertainment categories. VirtualBox: not run by me — the product
  owner attached this ISO to their own VM ("fdsa": BIOS, VMSVGA, 3D off,
  128 MB, 7 CPUs) four minutes after it was written, and an extra VM
  would have slowed the test they were judging. Earlier the same
  afternoon a throw-away VM booted the previous ISO in 7.5 minutes while
  Docker builds and the QEMU dev VM loaded the host (VirtualBox in
  Hyper-V/NEM mode); measure VirtualBox boots on an idle host.

## 2026-10-22 (12:30) — Session start +75 s since the 2026-10-21 evening: the portal platform theme

- The product owner: "it used to come at once". It did: the QEMU boot
  tests record "plasmashell running for live user" after 16–25 s from
  2026-10-18 to 2026-10-21 16:57, and after **92–96 s** for every ISO since
  2026-10-21 23:33 — on QEMU too, so neither VirtualBox nor llvmpipe. The
  kernel boot is unchanged (guest agent after 12–14 s); the +75 s is all
  inside the session start. The new reports' journal excerpts: `Failed to
  start plasma-ksplash.service` (48 s), `Failed to start
  xdg-desktop-portal.service` (98 s).
- In a VM (ISO 084833, 3D off), `systemd-analyze --user blame`: kcminit
  54 s, ksplash 40 s (timed out), plasmashell 27 s, kactivitymanagerd
  25.6 s, kded6 25.4 s, ksmserver 25.4 s, powerdevil 15.7 s, KDE's portal
  backend 14.5 s. The journal: `xdg-desktop-portal: Failed to create
  settings proxy: Error calling StartServiceByName for
  org.freedesktop.impl.portal.desktop.kde`, KSplash `WaitForName: Service
  was not registered within timeout`, the portal timing out after 90 s,
  dbus "Failed to activate service 'org.freedesktop.portal.Desktop': timed
  out" (`tests/results/2026-10-22-session-start/`). Cause: commit e676c2c
  (2026-10-21 23:11) gave the whole session
  `QT_QPA_PLATFORMTHEME=xdgdesktopportal` for the Windows 11 file dialogs.
  A Qt program starting with that theme first asks the portal (colour
  scheme) and blocks until the D-Bus timeout (25 s) when it does not
  answer; at session start it cannot: its backends (KDE's, a Qt program
  with the same theme) are Wayland clients of the very KWin that is
  blocked asking it. So kwin, kcminit, ksplash, kded6, ksmserver,
  kactivitymanagerd, plasmashell ... each waited 25 s in turn.
- Ruled out by measurement, same VM and ISO: the Wayland greeter of the
  same commit (session restart with it 150 s, with `DisplayServer=x11`
  135 s — noise; SDDM starts the autologin session within a second, so
  the greeter stays), and VeltOS' own portal backend (GLib, no Qt: run
  without the theme, 120 s and the portal still timed out).
- Fix, measured in the same VM (session restart: the desktop after
  **15 s**, 120–150 s before; the portal active, ksplash finished): a
  drop-in `Environment=QT_QPA_PLATFORMTHEME=kde` for every Plasma user
  service
  (`PLASMA_SERVICES` in veltos-desktop's build-assets.py, installed as
  `/usr/lib/systemd/user/<unit>.d/veltos-portal-theme.conf`), the same
  line in `veltos-auth-agent.service` (PySide6), and File Explorer's
  portal backend hands the dialogs it starts KDE's theme
  (`portal_platform_theme`). Programs the user starts keep the portal
  theme and their Windows 11 dialogs.
- ISO `veltos-0.1.0-dev-20261022-093321` built with all of it. Its live
  filesystem, listed with xorriso + unsquashfs in the builder, has the 25
  drop-ins (seven units were added to `PLASMA_SERVICES` after a package
  build, and `out/packages` still held that older package: the ISO build
  rebuilds the packages inside the build volume — AGENTS.md gotcha), the
  three helpers, the agent's `Environment=` line, the explorer change and
  a session script exporting only `LIBGL_ALWAYS_SOFTWARE=1`.
- Verified (ISO 093321): QEMU boot tests, plasmashell after **17.2 s**
  (UEFI, `out/test-results/20261022-100005-uefi`) and **16.4 s** (BIOS,
  `20261022-100224-bios`) — back from 92–97 s. VirtualBox cold boot with
  the owner's settings (BIOS, VMSVGA, 16 MB, 3D off; measured while the
  owner's own VM was running): the desktop at **75 s** from power-on
  (180–240 s before), Start and Task View rendering; with 3D on (128 MB)
  also 75 s. The sign-in screen (autologin switched off, SDDM restarted)
  painted in the 3D-off VM. One boot-test check now fails for the right
  reason: it grepped `xdgdesktopportal` in plasmashell's environment, and
  plasmashell runs with KDE's theme by design; `vmtest.py` now reads the
  user manager's environment (`systemctl --user show-environment`), which
  is what programs the user starts inherit — this changed check has not
  been run yet (usage limit); the rest passed (17/18, 16/17).
- That check was right and the change wrong (13:30): in the VM, Writer's
  Ctrl+S opened KDE's file dialog and `soffice.bin` had
  `QT_QPA_PLATFORMTHEME=kde` — programs started from Start inherit
  **plasmashell's** environment (KIO's launcher hands it to the transient
  unit), so the plasmashell drop-in took the Windows 11 file dialogs away
  from every program (ISO 093321 has this; Photos' "Add a folder" showed
  KDE's folder dialog too). plasmashell is out of `PLASMA_SERVICES` again
  and keeps the portal theme; by the time it starts, the portal and its
  backends come up without the chain above. `vmtest.py` checks
  plasmashell's environment as before.

## 2026-10-22 (11:45) — VirtualBox: llvmpipe alone, and only without 3D acceleration

- Product owner, testing ISO `veltos-0.1.0-dev-20261022-072126` in
  VirtualBox: the desktop takes long to appear ("it used to come at
  once"), grey boxes under the desktop icons' labels, and Task View shows
  "Desktop 1" black. The two visual ones came from the 04:00 fix being too
  blunt (the slowness has another cause, since the 2026-10-21 evening ISO;
  entry above):
  `QT_QUICK_BACKEND=software` (Qt Quick's software scene graph) paints
  slowly and cannot draw the labels' shadow effect, so Plasma puts a solid
  box behind each label; `KWIN_COMPOSE=Q` (QPainter) cannot render the
  Task View effect's `WindowThumbnail`s, so its previews are black.
- Two renderer experiments in a VM were void before one was valid: a
  `99-*.sh` file in `plasma-workspace/env` is sourced *before*
  `veltos-session.sh` and cannot unset what it exports (AGENTS.md
  gotcha). Editing the session script in the VM instead: with
  `LIBGL_ALWAYS_SOFTWARE=1` **alone** (Mesa llvmpipe), KWin's own OpenGL
  scene runs in software and paints (desktop ~105 s after the session
  restart, measured while another VM booted on the host), the labels have
  their shadows and no boxes, and Task View shows the live window and a
  real "Desktop 1" preview (`tests/results/2026-10-22-virtualbox-renderer/`).
  KWin still logs "Applying output config failed" and Xwayland's glamor
  lines; they are harmless here.
- The rule: a VM with 3D acceleration *on* gives real OpenGL (Mesa's
  svga driver, renderer "SVGA3D"), so forcing software on every
  VirtualBox VM would have crippled it. Nothing in sysfs or DMI tells 3D
  on from off (both: card0 + renderD128, the same vmwgfx parameters);
  `eglinfo -B` on the GBM platform does ("llvmpipe" = Mesa already fell
  back). New `/usr/libexec/veltos/needs-software-rendering` (VirtualBox by
  DMI AND that probe; only VirtualBox is probed) is the one place for the
  rule, used by `veltos-session.sh` and, before SDDM starts, by
  `sddm-virtualbox-env` (`ExecStartPre` drop-in
  `/usr/lib/systemd/system/sddm.service.d/veltos-virtualbox.conf`), which
  writes `/etc/sddm.conf.d/zz-veltos-virtualbox.conf` (the greeter's
  `GreeterEnvironment` plus `LIBGL_ALWAYS_SOFTWARE=1`) and the marker
  `/run/veltos/software-rendering` that `greeter-compositor` reads (the
  sddm user may not open the render node). The unconditional
  `QT_QUICK_BACKEND=software` the 04:00 change put in `GreeterEnvironment`
  is gone. `veltos-desktop` now depends on `mesa-utils` (eglinfo; glxinfo
  was already used by session-fixups). The greeter path in VirtualBox
  (the live ISO signs in automatically, so autologin was switched off in
  a VM and SDDM restarted): the ExecStartPre ran — the marker and the
  drop-in were there and the greeter's KWin was running — but whether
  the greeter painted could not be seen in that VM, which was still under
  the session-start deadlock of the 12:30 entry; re-tested with the
  fixed ISO (below, when run).
- Also: a `veltos-vm` QEMU container from 2026-10-21 had been running for
  15 h with 8 GB reserved (`build/run.sh vm stop` leaves the container up;
  gotcha), slowing every VM test today; removed. Docker's build cache
  (10.9 GB) pruned; the developer's C: was at 99 % with Docker's virtual
  disk at 94 GB — compacting it is the owner's call.

## 2026-10-22 (04:00) — Office apps named Word, Excel, PowerPoint; black screen in VirtualBox

- Product owner: the apps are to be called **Word, Excel and PowerPoint**
  and the Excel icon's letter is to be an **X**. Done in veltos-desktop's
  `update-app-names` (the generic names Word Processor / Spreadsheet /
  Presentation and their Turkish forms stay as search words), on the start
  screens (`strings.KINDS`), in the verify hook (`Name=Word`), and in
  `tools/app-icons.py` (W, X, P tiles). The names are Microsoft's product
  names; the product owner chose them for this distribution. The icons
  remain VeltOS drawings (no Microsoft files).
- Product owner: the ISO `veltos-0.1.0-dev-20261021-231629` stays on a
  black screen in their VirtualBox VM. The automatic boot tests (QEMU,
  UEFI and BIOS) had passed. Their VM: BIOS firmware, PIIX3, **VMSVGA with
  16 MB video memory, 3D off**. Reproduced in a throw-away VirtualBox VM
  with the owner's settings (scripts in `out/vbox/`, driven with
  VBoxManage; the owner's own VMs untouched). GRUB, the kernel and the
  Plymouth splash come up; the desktop does not. The journal (read over a
  serial port) shows the kernel's `vmwgfx ... unsupported hypervisor ...
  likely broken`, then KWin's Wayland session failing OpenGL on the VMSVGA
  display: `kwin_core: Failed to open drm node`, `EGL setup failed,
  disabling glamor`, `Failed to initialize glamor, falling back to sw`,
  `kwin_core: Applying output config failed!`, and KWin restarting while
  KSplash times out (`WaitForName ... not registered within timeout`).
  Probes at other settings: VMSVGA with **128 MB** VRAM reaches the
  desktop (slowly, ~4 min); VBoxSVGA stays black; 16 MB stays black. So
  the VMSVGA OpenGL path does not come up at 16 MB and is very slow even
  at 128 MB.
- Diagnosis, in two steps. First tried KWin's software compositor alone
  (`KWIN_COMPOSE=Q`); a clean cold boot of the ISO with it was **still
  black**. kscreen-doctor on the black VM showed the output enabled at
  1280x800 (a 4 MB framebuffer, well within 16 MB), so the mode/VRAM was
  not the wall; `KWIN_COMPOSE=Q` was confirmed set on kwin_wayland yet the
  compositor could not configure a working scene. The journal showed the
  real cause: with no OpenGL, not only KWin but **plasmashell and the QML
  apps** cannot get a GL context (`libEGL: failed to create dri2 screen`,
  `Applying output config failed`), so nothing paints.
- Fix: render the whole stack in software in VirtualBox. veltos-session.sh,
  when the DMI product/vendor is VirtualBox, exports `KWIN_COMPOSE=Q`
  (KWin's QPainter compositor), `QT_QUICK_BACKEND=software` (Qt Quick's
  software scene graph: plasmashell and every VeltOS QML app) and
  `LIBGL_ALWAYS_SOFTWARE=1` (Mesa llvmpipe). The SDDM greeter gets the
  same: the compositor through a new wrapper
  `/usr/libexec/veltos/greeter-compositor` (KWIN_COMPOSE/llvmpipe, DMI
  gated), and the greeter UI through `QT_QUICK_BACKEND=software` in
  `GreeterEnvironment` (unconditional: a login screen must always render,
  on any GPU or VM, and does not need the GPU). The session detection is
  DMI gated, so real GPUs, QEMU and other machines keep hardware
  rendering. Proven in a throw-away 16 MB VMSVGA VM with the owner's
  settings: with the three variables set and a fresh session, the full
  desktop (wallpaper, taskbar, icons) painted where it had stayed black.
  Note for the owner: 16 MB VRAM works with this fix; 128 MB is smoother.
  **Superseded at 11:45 the same day**: llvmpipe alone is right; the other
  two variables caused grey label boxes and a black Task View, and the
  rule became "VirtualBox without 3D acceleration" (see above).

## 2026-10-22 (00:30) — VeltOS Office: Microsoft 365's start screen in front of LibreOffice

Product owner: "Redo the Office apps (Word, Excel, PowerPoint) completely
with the Windows 11 theme; exactly like Microsoft's: content, theme,
animations." Rule 5 and the licence leave LibreOffice as the engine; what
VeltOS can make its own is everything the user sees first and around the
document (architecture 2.13).

- **Start screen** (`veltos-office word|sheet|slides`, PySide6/QML in
  `packages/veltos-office/veltos_office/`): the layout of Microsoft 365's
  start screen on Windows 11, the title bar and navigation rail in the
  app's colour (Word blue, Excel green, PowerPoint orange; black chrome in
  dark mode like Office's Black theme). Home: "Good morning / afternoon /
  evening", New with the blank tile and the first templates, "More
  templates →", Recent / Pinned with search, "Name" / "Date modified",
  rows grouped by Pinned / Today / Yesterday / This week / Last week /
  Older, a pin on hover, a right-click menu. New: every template as a
  grid with search. Open: Recent, This PC (Documents, Desktop, Downloads)
  and Browse through the VeltOS Open dialog. Account: picture, name,
  "Manage account", the theme, product information. Options: the start
  screen switch, clearing the recent list. Windows 11 animations: sections
  glide in one after the other, tiles lift with a shadow, the rail's
  indicator and the tabs' underline slide, the toggle; all off with
  Accessibility's animation switch. Text sizes follow the text size
  setting. English and Turkish.
- **Data**: recent files come from LibreOffice's own PickList history in
  `registrymodifications.xcu` (URL, title, the filter each file was opened
  with; filtered to the app's file types), plus what the start screen
  opened itself; pins and options in `~/.config/veltos-office/<kind>.json`.
  Templates: VeltOS' own (`tools/make-templates.py` writes flat ODF, the
  package build converts it with LibreOffice into .ott/.ots with
  thumbnails: meeting notes, report, to-do list; monthly budget with
  formulas, invoice, expense tracker with SUMIF, weekly schedule),
  LibreOffice's (business letters, business card, CV, résumé, the 23
  presentation designs) and the user's; thumbnails are the pictures inside
  the template files. Opening runs `libreoffice --nologo --writer`, `-n
  TEMPLATE` or the file; the screen leaves 2.5 s later.
- **Desktop entries** (veltos-desktop `update-app-names`): the Office
  entries run `veltos-office word|sheet|slides %U` when the start screen
  is installed (files open at once, no files: the start screen; the "New
  Document" actions pass `--blank`); without it the old lines stay.
- **LibreOffice** (`veltos-office.xcd`): product name "VeltOS Office", so
  titles read "Untitled 1 — VeltOS Office Writer" (like "Document1 -
  Word") and %PRODUCTNAME in dialogs says VeltOS Office; it is LibreOffice
  underneath, which About's version still says. An attempt to drop the
  module name from the title (empty `ooSetupFactoryUIName`) did nothing:
  the property is localized and an unlocalized empty value does not
  replace it.
- **Coloured title bars**: the Aurorae frame (VeltOS' changed copy of
  KWin's QML, `plasma-overrides/aurorae.json`) tints the title bar of
  LibreOffice's windows in the app's colour with white caption and
  white-glyph buttons (new "-ondark" states in every caption button SVG,
  `tools/fluent.py`); the dark frame stays dark. The first version told
  the windows by `decoration.client.windowClass`, which KDecoration3 does
  not expose to QML (the title bar stayed light): they are told by their
  caption ("… — VeltOS Office Writer"). Verified after a sign-out:
  Writer's title bar in Word blue with white caption and buttons.
- **Document window** (product owner: the editing windows too must look
  like Microsoft's): LibreOffice's Start Center gets light colours. The
  sidebar strip at the right of documents (Office has none) stays: it is
  not a window-state docking window, so an .xcd layer cannot turn it off
  by default; View > Sidebar (Ctrl+F5) toggles it. The ribbon's tab row in the app's colour was tried
  with LibreOffice's GTK plug-in and GTK CSS (`SAL_USE_VCLPLUGIN=gtk3`,
  a per-app `GTK_THEME`): `notebook > header` coloured the tabs only,
  the quick toolbar and the menu button at the ends of the row are not
  GTK nodes, builder ids are not CSS names, and the window background
  also paints the document canvas and status bar. The result (a blue
  segment behind the tabs, GTK-styled dialogs) looked less like Office
  than the Qt plug-in with the Windows 11 widget style, so LibreOffice
  stays on `libreoffice-kf6`; the experiment is removed.
- **Icons** (product owner: like Microsoft Office's on Windows 11 and
  consistent): the three Office icons are redrawn in the composition of
  Microsoft 365's icons, a coloured tile with the app's initial in front
  of a page / sheet / slide, with VeltOS' own letters (W, S, P for Word
  Processor, Spreadsheet, Presentation) and the Word blue / Excel green /
  PowerPoint orange; the same drawings stand for the file types.
  Microsoft's files are not used.
- Verified in the live VM (`tests/results/2026-10-22-office-start-screen/`):
  the three start screens in their colours with VeltOS' and LibreOffice's
  templates and thumbnails, all five pages, Turkish, the start screen
  opened from Start's pinned "Word Processor" through the rewritten
  entry, "Meeting notes" and "Blank document" opening Writer with the
  Tabbed interface and the "VeltOS Office Writer" title, the start screen
  leaving afterwards. Unit tests: 24 in veltos-office (texts, PickList,
  pins, templates with thumbnails, command lines, the window for every app
  in English and Turkish offscreen), the desktop entry rewrite and the
  frame change in veltos-desktop.
- Found: the .docx/.xlsx/.pptx defaults of 2026-10-21 never applied: the
  Save dialog offered .odt. LibreOffice parses `share/registry/*.xcd` in
  name order unless a file names dependencies, and later files win; the
  document factories are set in writer.xcd / calc.xcd / impress.xcd,
  which sort after veltos-office.xcd. The layer now depends on them (and
  the test checks the dependencies are installed).
- Learnt: a program started by a `systemd-run --user` service dies with
  the service's cgroup when the main process exits (the first template
  test showed no LibreOffice; `-p KillMode=process` or starting from
  Start). `pkill -f` with a pattern that also appears in the same `vm
  exec` text kills that shell. Terminating the live user's session
  (`loginctl terminate-user`) left SDDM's relogin crashed and the live
  console autologin on tty3; `systemctl restart sddm` brought Plasma back
  (about two minutes).
- Found while building the ISO: `veltos-photos`' gallery search matched
  the query against each picture's **absolute** path, so a term that
  occurred in the folders above Pictures (a user name, or `mkdtemp`'s
  random name in the package test) matched every file. The Turkish UI
  test failed at random for this reason and stopped the ISO build. The
  search now matches the path **within** the library folder (the scan
  folder prefix is stripped); a regression test adds a library under a
  temp dir whose name holds the query term and checks it matches
  nothing. Both photos test classes (EN and TR) pass.
- Not done: LibreOffice's own tab strip is not in the app's colour and the
  document window has no animations (LibreOffice changes); closing the
  last document shows LibreOffice's Start Center; dark mode of the start
  screen and the templates' look in Calc/Impress on screen not checked.

## 2026-10-21 (23:30) — Windows 11 dialogs everywhere: file dialogs, the password prompt, Clock, search, fixes

Product owner's list of 2026-10-21 (evening), item by item:

- **File dialogs** ("every open/save/folder window must be the current
  Windows 11 one"): File Explorer gained a dialog mode (`veltos-explorer
  --pick`, `picker.py` + `qml/Picker.qml`): Windows 11's Open / Save As /
  Select Folder built from Explorer's own address bar, navigation pane
  and views, with the file name box, the file type drop-down, New folder,
  "already exists, replace?" and the last folder remembered. Other
  programs reach it through the desktop portal: `veltos-explorer
  --portal` (`portal.py`, GLib/GDBus) is the
  `org.freedesktop.impl.portal.FileChooser` backend, chosen for Plasma
  sessions by `/etc/xdg/xdg-desktop-portal/kde-portals.conf`; the session
  sets `QT_QPA_PLATFORMTHEME=xdgdesktopportal` (Qt's portal theme, which
  wraps the KDE theme for everything but file dialogs; package
  `qt6-xdgdesktopportal-platformtheme`) and `GTK_USE_PORTAL=1`, Firefox and
  Mail get `widget.use-xdg-desktop-portal.file-picker=1`. VeltOS Settings
  picks account pictures and wallpapers with it instead of `kdialog`.
  Verified in the live VM: the dialog alone (Open, filters, Esc ->
  `{"paths": []}`), Firefox's Ctrl+O arriving in the VeltOS dialog
  through the portal ("Open File - Mozilla Firefox", "All Files"), and
  with `QT_QPA_PLATFORMTHEME=xdgdesktopportal` set for the session:
  Konsole's "Save Output" (Save As with "Plain text document") and
  LibreOffice Writer's Open, which then opened the chosen file.
  LibreOffice's Qt file picker sends **two** OpenFile requests for one
  Ctrl+O (same window and title, two request tokens; seen with a log in
  the backend): two VeltOS dialogs appeared. The backend now lets an
  identical request from the same window within three seconds join the
  first dialog and answers both with the same result (unit-tested with
  stand-ins; LibreOffice then showed one dialog and opened the file once).
  Also learnt: a backend that exits at start makes xdg-desktop-portal drop
  the whole FileChooser interface ("No such interface"), and Qt programs
  then fall back to KDE's dialog without any message.
- **"Open with" / "choose an app"**: Windows 11's "Select an app to open
  this .txt file" window (`openwith.py` + `qml/OpenWith.qml`, `veltos-explorer
  --open-with FILE`): the apps that claim the type, "More apps", Always /
  Just once (Always records the default in mimeapps.list). File Explorer's
  "Open with" menu ends with "Choose another app", and a file no app
  claims opens this window instead of KDE's. Offscreen tests only.
- **Password prompt** ("authentication required" is still KDE's): new
  package `veltos-auth`, a polkit authentication agent (GLib) with a
  prompt in the layout of Windows 11's User Account Control window
  (PySide6/QML: blue band with the new VeltOS shield-and-padlock icon
  (`veltos-auth.svg`: the VeltOS V centred on a shield, a padlock
  badge; the product owner asked for the V and a password icon in one
  logo, and for the V to be centred; seen in the prompt, its title bar
  and the taskbar),
  the question, program, details, the administrator's picture, password,
  Yes/No). The password is checked by polkit's own setuid helper
  (`polkit-agent-helper-1`, line protocol in `helper.py`). KDE's
  `plasma-polkit-agent.service` is masked. Verified in the live VM (with
  the live "sudo without password" rule moved aside): `pkexec /bin/true`
  from the session showed the prompt, a wrong password kept it open with
  "The password is incorrect. Try again.", the right one made polkit log
  "successfully authenticated as unix-user:velt"; the agent registered
  for unix-session:1 after KDE's agent was stopped.
- **Accounts**: the "Change" password button did nothing because
  `SettingRow`'s and `VButton`'s TapHandlers both saw the tap (passive
  grabs) and toggled the panel twice; rows now ignore taps on their
  control, buttons take an exclusive grab (VM: the panel opens). The
  change itself then failed ("The password could not be changed"): the
  pseudo-terminal conversation with `passwd` took the newline after an
  answer for a new prompt and sent the next answer too early, so the last
  prompt was never answered (traced with a transcript in the VM). It now
  looks only at output after the last answer; the package test's fake
  `passwd` behaves like the real one (echo off, newline, pause). Verified
  in the VM: the fixed function changed the live user's password with
  the real `passwd` (shadow hash changed), and the Settings page shows
  the Change panel on the first click. "Add account" could not be
  reproduced: in the live VM session `Accounts.add_user` created the user
  with its password at once (the live rule needs no prompt); on an
  installed system the prompt is now VeltOS'.
- **Accessibility > Text size** did nothing visible: the KDE fonts were
  written but VeltOS' own apps use fixed pixel sizes. Every VeltOS app now
  reads the size (`textScale`, the KDE font size over 10 pt) and scales
  its text (`Theme.qml`); Settings follows the slider at once, the others
  at their next start (Explorer while open). Settings also sends KDE's
  `notifyChange(FontChanged)` signal so KDE programs re-read fonts.
  Seen at 150 % in the live VM (Settings, File Explorer); Explorer's
  Home tiles and the Recent list's date column had fixed widths and
  overlapped at that size, they scale now.
- **Lock screen**: "Never" in the lock-after list (turns Autolock off).
- **Default apps page empty**: `/usr/share/applications/mimeinfo.cache`
  did not exist in the image (`desktop-file-utils` was missing; GTK
  programs need it too), and the page never looked at VeltOS' own
  `kde-mimeapps.list` next to the applications. Both fixed; with nothing
  recorded the first app that opens the type is shown.
- **Searching files switch fell back to off**: `balooctl6` was not in the
  image (`baloo6` added) and the state was read from the indexer's status
  instead of its setting. Off by default (`/etc/xdg/baloofilerc`).
- **Store "something went wrong"**: the real reason is now shown
  (permission not given / not in the catalogue / download failed /
  another installation running / PackageKit's text), and old or missing
  package lists are refreshed before an install (an installed system
  keeps the image's lists until something refreshes them). In the live VM
  `pkcon install` itself worked without a prompt.
- **Taskbar search**: the search box opens Windows 11's search window
  (a VeltOS plasmoid popup, centred like Start): a search field, "Top
  apps" (Start's pinned apps) while empty, results on the left with the
  best match and "Open" on the right while typing. Seen in the live VM:
  the empty window with its hint (the live user has no usage history,
  so "Top apps" is empty), and "calc" listing Calculator as the best
  match with its Open card. The first build put the card in the middle
  of the window: the left column now takes 56 % of the width.
- **Taskbar progress**: a thin accent bar under the icon
  (TaskProgressOverlay.qml replaced through update-plasma-overrides)
  instead of Plasma's fill behind it. Seen in the live VM during a
  Firefox download from a slow local HTTP server: the thin bar under
  the Firefox icon, next to Plasma's download count badge.
- **Firefox downloads panel**: a VeltOS style sheet (`firefox/downloads.css`,
  rounded card, accent progress line, quiet "Show all downloads").
  Seen in the live VM while the same file downloaded.
- **Sign-in screen size** ("small, then the resolution changes"): SDDM
  started an X11 greeter; it now runs the greeter in KWin on Wayland with
  Plasma's command line (`DisplayServer=wayland`, `CompositorCommand`),
  so the greeter and the session pick the same mode. Verified in the live
  VM with the autologin file moved aside: the greeter filled the whole
  1920×1080 screen (lock view, then the sign-in view), and signing in with
  the password started the session (`tests/results/2026-10-21-windows-dialogs/`).
  Note: `/etc/sddm.conf` (live-config's autologin) overrides every
  `sddm.conf.d` file.
- **Sounds**: all VeltOS sounds synthesised again, softer: a slow
  attack, fewer upper partials, a detuned second voice, a low-pass and a
  small room reverb, at -6 dBFS; new `alarm-clock-elapsed` for Clock.
  Listened to by nobody yet (no audio in the VM).
- **Clock**: new package `veltos-clock` (Windows 11 Clock layout: Focus
  sessions, Timer, Alarm, Stopwatch, World clock) with `veltos-clock-agent`,
  which rings alarms and timers while the app is closed (notification with
  Snooze/Dismiss, the alarm sound). Unit tests (when alarms ring, timers,
  the window in English and Turkish). On screen in the live VM: all five
  pages (the navigation column first filled the whole window; it is now
  220 px), an alarm set from the app rang through the agent with the
  app closed (notification "VeltOS Clock · Alarm · Tea time" with
  Snooze and Dismiss, the alarm sound through pw-play), Clock pinned in
  Start with its own icon.
- **Installer slideshow**: seven animated slides (words fade in, a picture
  of the system glides in) with screenshots of Start, Settings, File
  Explorer and the Store taken in the VM, texts in the installer's
  language. The QML loads with Calamares' slideshow module in the VM
  (19 items); not yet watched during an installation.
- **Windows programs**: when Bottles, Lutris or PlayOnLinux are installed
  the runner first asks which to use (none of the three is in Debian 13,
  so VeltOS cannot preinstall them from a signed archive; the product
  owner decides about Flatpak); the Done page scrolls its list of new
  programs instead of pushing the buttons up; the runner has its own App
  Installer icon; Windows programs get `AppsUseLightTheme` from the
  VeltOS light/dark mode at every start (Wine 10's Light theme has no
  dark variant, so Wine's own controls stay light). Verified in the live
  VM with 7-Zip 26.04's installer: the runner's page while Wine set
  itself up, the installer's own window, then "7-Zip is installed"
  with the two new Start entries and Open buttons, Done in its place at
  the bottom right; 7-Zip then appeared in Start's All list. The runner
  has its own flat App Installer icon in the taskbar.
- **Icons**: This PC with a thinner bezel; "logo and name" of This PC /
  Recycle Bin kept (they are Windows' names already; Microsoft's own
  icon files cannot be copied).
- **File Explorer**: typing `cmd`, `terminal` or `powershell` into the
  address box opens the Terminal at the folder, as Windows does.
- KDE buttons without icons (`ShowIconsOnPushButtons=false`) make KDE's
  remaining dialogs (new folder on the desktop) plainer.
- **Old Store**: Discover is not in the image (verify hook); nothing of
  VeltOS opens it. A system installed from an older ISO may still have it.
- Not done: the desktop's "Create New > Folder" still uses KDE's name
  dialog (KNewFileMenu is C++ in the folder view; VeltOS cannot replace
  it from QML); Bottles/Lutris/PlayOnLinux are not preinstalled.
- Build: a full `build/run.sh packages` stopped at `packages/veltos-disks`
  (the Disk Management draft has no `debian/`); the script now skips
  directories without `debian/rules`. `deb.debian.org` delivered about
  20 KB/s to the builder this evening; `VELTOS_DEBIAN_MIRROR` and
  `VELTOS_SECURITY_MIRROR` now also rewrite the builder's own apt
  sources (with ftp.de.debian.org a full package build took about
  12 minutes). The repository test's tree walk stat-ed a LibreOffice
  symlink extracted under `out/` before skipping the folder (Windows
  cannot stat it); it now prunes `.git`, `out` and `__pycache__`.
- Screenshots of the checks: `tests/results/2026-10-21-windows-dialogs/`.

## 2026-10-21 (20:00) — Mail: Outlook-like "Add your account"

- Product owner: Mail still opened on an old-looking sign-in page. It was
  Thunderbird's account setup tab with its octopus illustrations and
  Mozilla links: `mail.css` never reached it because the page is
  `about:accountsetup`, not a `chrome://messenger/content/` URL (found by
  extracting `omni.ja` of Debian's Thunderbird 140.17 ESR in the builder
  and searching for the page's URL).
- Now: one centred card like Outlook's "Add your account" with the Mail
  icon, VeltOS' title and text (English/Turkish, replaced only while the
  page shows its first step), the illustration column hidden, Windows 11
  fields (accent line under the focused field) and buttons. The "cancel"
  question names Mail instead of Thunderbird. Mail uses the accent chosen
  in Settings (`AccentColor`) instead of a fixed blue.
- Verified in a live VM (fresh profile): the card, the cancel question,
  "use without an account" leading to the Outlook-like main window. Not
  checked: adding a real account (needs credentials), Turkish texts on
  screen, dark mode.

## 2026-10-21 (19:40) — VeltOS Office (LibreOffice for Windows users)

- Product owner: Word, Excel and PowerPoint like Windows 11's Office.
  VeltOS does not write an office suite: new package `veltos-office`
  depends on Debian's LibreOffice 25.2.3 (Writer, Calc, Impress, the KF6
  integration, Colibre icons, Carlito/Caladea/Liberation fonts; names and
  versions checked with `apt-cache` in the builder) and adds one
  configuration layer, `share/registry/veltos-office.xcd`: Tabbed
  (ribbon-like) interface, Colibre icons, Microsoft formats by default
  without the "Keep current format?" question, Carlito as default font
  (11 pt in Writer), no tip of the day / donation / get-involved /
  what's-new bars, crash reports off. Debian's "DebianTalk" presentation
  template is diverted out of the template folders.
- Names: "Word Processor", "Spreadsheet", "Presentation" (Turkish "Kelime
  İşlemci", "Hesap Tablosu", "Sunu"); Microsoft's product names are only
  search words, the icons are original drawings without letters. Window
  titles and About still say LibreOffice (honest: it is LibreOffice).
- Found while testing: (1) a toolbar mode is chosen by its `CommandArg`
  ("notebookbar.ui"), not by its node name ("Tabbed"): with the name,
  LibreOffice kept menus and toolbars. (2) Properties of an extensible
  group (VCL `DefaultFonts`) need `oor:type`; without it LibreOffice ended
  at start with an uncaught RuntimeException. Both are now covered by the
  package tests, which check the layer against the schema and data of the
  LibreOffice it is built with.
- Verified in a live VM: Start search "word" finds Word Processor; Writer,
  Calc and Impress open with the Tabbed interface, Colibre icons and
  Carlito; Impress's template list has no DebianTalk. Not checked: dark
  mode icons, Turkish interface on screen, opening real .docx/.xlsx/.pptx
  files, printing.
- ISO build started in the background at the product owner's request
  (from 25d7dae; its veltos-office package was built after the fix in
  ef172e2).

## 2026-10-21 (19:16) — VeltOS PDF Reader replaces Okular

- Product owner: the document viewer must become a modern PDF app like
  the one on Windows 11. New package `veltos-pdf` (PySide6/QML on QtQuick
  Pdf, i.e. PDFium): Home with recent files, tabs, continuous pages with
  selectable text, quick tool rail (search, thumbnails, bookmarks, rotate,
  fit width, print, properties), floating page/zoom bar, read mode, full
  screen, passwords, printing through the system dialog. Original name
  and artwork: no Adobe names or logos. Okular leaves the image; PDF files
  open in PDF Reader (`DEFAULT_APPS`), Start's pinned Okular becomes it,
  the icon family's document viewer icon is drawn for `veltos-pdf`.
- Found while testing: Qt 6.8's `PdfMultiPageView` lays its pages out
  again when the scale changes but before its column width follows the
  new scale, so after zooming out (or opening the side panel) the pages
  sat off-centre and partly outside the window; VeltOS lays them out once
  more (`relayoutPages`). Fit width/page now keeps fitting when the room
  changes. A tab that is not shown has no size: fitting it to zero width
  made the view's rows empty (QML warning in the tests); it is fitted when
  it gets a size. QtPdf marks line breaks in search context with a return
  symbol; the results show spaces.
- All VeltOS apps with their own frame (File Explorer, Notepad, Photos,
  Media Player, PDF Reader) dimmed the transparent shadow margin around
  the window behind dialogs as well; `Scrim.qml` dims only the window.
- Media Player's search also looked at the folders of a file: with a
  temporary folder name containing "2" every song matched "song 2" (the
  test failed only sometimes). It now looks at the file name only.
- Verified: 6 unit tests for PDF Reader (PDFs written with QPdfWriter,
  window offscreen EN/TR, damaged file), all tests of the five apps;
  VM (live, packages installed): a 19-page PDF opened by `xdg-open`,
  thumbnails, bookmarks, search with 160 results and highlights, zoom out
  centred, properties dialog (dimming inside the window only), app menu,
  Home with the recent file. Not checked: printing, password-protected
  files on screen (only the unit-level status), very large PDFs.

## 2026-10-21 (18:46) — VeltOS Media Player (Windows 11 Media Player)

- New package `veltos-media` (PySide6/QML, Qt Multimedia FFmpeg backend)
  in Windows 11 Media Player's layout: navigation pane with search, Home
  (recent media, Open file(s)), music library (songs, albums, artists;
  tags and covers through mutagen), video library (frames through
  ffmpegthumbnailer), play queue (shuffle keeps the playing item first;
  repeat off/all/one; previous restarts within 3 s), playlists, player bar
  and "now playing" (video, or the album picture on its blurred copy).
  Audio and video files open in it (`DEFAULT_APPS`). Before it the image
  had no video player at all (KDE's list named Elisa, not installed).
- Found while testing: a delegate's `required property int index` does
  not reach a component's own `property int index` (every row was drawn as
  row 0); SongRow takes `rowIndex`.
- Verified: 11 unit tests (queue, WAV files tagged with mutagen, window
  offscreen EN/TR); VM (live): sample songs and videos made by
  `out/vm/media-samples.py` (WAV with ID3 tags and covers, MJPEG AVI from
  Pillow frames): albums with covers, album playing with the position
  advancing, video thumbnails, a video played to its end. Not checked:
  hearing the sound (the VM has no audio), long files, subtitles.

## 2026-10-21 (18:29) — VeltOS Photos (Windows 11 Photos)

- Product owner: photo and video apps exactly like Windows 11's. New
  package `veltos-photos` (PySide6/QML) in Windows 11 Photos' layout:
  search in the title bar, navigation pane, the gallery grouped by month,
  the viewer with its toolbar, filmstrip and file information, "Edit
  image" (crop, rotate, flip, brightness, contrast, saturation, warmth;
  live preview with MultiEffect, the saved picture made by Pillow), slide
  show, favorites, set as background/lock screen, Recycle Bin.
- Verified in the builder: Debian 13 has ffmpegthumbnailer 2.2.3 (video
  thumbnails), python3-pil 11.1, qt6-image-formats-plugins 6.8.2 (WebP,
  TIFF, ...), python3-mutagen 1.47 (for Media Player), QtPdf for PySide6
  and QML (for the PDF reader).
- Default apps: pictures open in Photos (`DEFAULT_APPS`); Gwenview leaves
  the image; Start's pinned Gwenview becomes Photos.
- Verified: 15 unit tests (scan with EXIF dates, grouping, edits with real
  Pillow pictures incl. EXIF orientation, window offscreen EN/TR); VM
  (live): gallery of seven sample pictures in two months, viewer, edit
  view, saturation/warmth preview, "Save as copy" wrote
  "VeltOS-Ember - Copy.png" and showed it. Not checked: lock-screen picture
  on screen, libraries of thousands of pictures, HEIC.

## 2026-10-21 (15:17) — VeltOS Notepad (Windows 11 Notepad)

- Product owner: the text editor must be exactly Windows 11's Notepad.
  New package `veltos-notepad` (PySide6/QML, same frame technique as File
  Explorer): tabs in the title bar with the unsaved dot, File/Edit/View
  menus and Settings, find and replace panel at the top right, status bar
  with line/column, characters, zoom, line ending and encoding (both can
  be changed there), Settings page (app theme, font, word wrap, opening
  files, session). Encodings and line endings are detected and kept
  (`textfile.py`); Replace all is one Undo step (QTextCursor edit block);
  unsaved tabs are kept in a session file like Windows 11; a second start
  hands its files to the running Notepad over a local socket.
- Default apps: veltos-desktop's `update-app-names` now also writes
  `/var/lib/veltos/xdg/applications/kde-mimeapps.list` with the installed
  VeltOS apps per file type; Plasma reads it before KDE's
  `/usr/share/applications/kde-mimeapps.list` (checked: XDG_DATA_DIRS of the
  session is `/var/lib/veltos/xdg:/usr/local/share:/usr/share`). Text files
  → Notepad. KWrite leaves the image; Start's pinned KWrite becomes
  Notepad once.
- Found: PySide6 makes the QTextDocument of a QML TextArea unusable from
  Python when the QQuickTextDocument wrapper is dropped ("already
  deleted"); Notepad keeps both (probe in the builder: `out/vm/doctest.py`).
- Verified: 19 Notepad unit tests (offscreen window EN/TR); VM (live): a
  CRLF file opened with xdg-open in Notepad, File menu, typing (dot on the
  tab), find, Ctrl+S kept CRLF (od -c), Settings page. Not tested: printing
  to a real printer, very large files.

## 2026-10-21 (14:49) — Settings Home and Themes like Windows 11

- Product owner's screenshots: Windows 11 Settings Home (device card with
  the wallpaper, network and Windows Update status, Recommended settings,
  Bluetooth devices, Personalize your device) and Personalization >
  Themes (a theme grid of wallpapers with accent colours).
- Home rebuilt in that layout (two columns from 640 px): this PC's
  wallpaper, name, model and Rename; network ("Wired connection 1 —
  Connected", Wi-Fi "Connected, secured"); "VeltOS Update — Last checked:
  4 hours ago" (newest `/var/lib/apt/lists/*Release`); a VeltOS apps card
  in place of Windows' Microsoft account card; Recommended settings from a
  visit count; Bluetooth devices; six theme tiles, colour mode, Themes.
- Themes: eight themes (wallpaper + mode + accent). New wallpaper colour
  variants generated like the others: Nebula (purple glow), Ember (crimson
  bloom), Tide (teal flow), Dawn (silver flow), plus a dark preview
  (`screenshot-dark.png`) for every wallpaper. Applying runs the global
  theme first, then the wallpaper, then the accent. Found in the VM:
  `plasma-apply-colorscheme --accent-color` writes the colours but no
  `AccentColor`, so Settings could not read the choice back ("Blue" after
  a restart); Settings now records it with kwriteconfig6 like KDE's colours
  module.
- Bluetooth's "Add device" started KDE's Bluetooth wizard; it is now a
  VeltOS dialog (scan, list unpaired named devices, pair/trust/connect).
  Untested with real Bluetooth hardware (the VM has none).
- VM (live): Home in light and dark, Ember theme applied from Home (dark
  mode, red wallpaper and accent), Themes page shows "Ember / Red", back
  to VeltOS (light). Unit tests: veltos-settings 90 (themes, Add a device,
  recent settings, update time text), veltos-desktop 82.

## 2026-10-21 (14:30) — Disk Management and Firefox icons

- Disk Management showed Fluent's dull grey platter (product owner: "the
  icon is broken"); it now has a VeltOS drawing in the app family (the
  File Explorer local disk with a partition chart), also for gnome-disks.
- Firefox: Fluent redraws Mozilla's logo flat; Windows 11 shows the real
  one. Fluent's firefox* app icons are removed, so the theme falls back to
  firefox-esr's own hicolor icons (official branding, 16-128 px; checked
  in the VM). The package build fails if a Fluent copy comes back.
- VM (live): Start shows both; contact sheet of the whole family rendered
  with rsvg-convert (`out/vm/render-icons.sh`).

## 2026-10-21 (11:30) — Only VeltOS Settings opens; Start's quick link menu

- Product owner: KDE/Debian's settings must never open, on purpose or by
  accident. Audit in the live VM (visible menu entries, settings-like
  programs, autostart files): KDE Info Center ("System Information") was
  still in Start and opened KDE's settings window; Start's right-click
  offered KDE's "Edit Applications" (kmenuedit); plasma-desktop's
  Recommends brought Discover with its update notifier (autostart; "View
  updates" opened Discover), Kup backups and KDE Connect (daemons at every
  sign-in), KDE's handbook browser, menu editor and wallet manager.
- veltos-settings: `/usr/bin/kinfocenter` is diverted like `systemsettings`
  and `kcmshell6`; the redirect opens About for it. `KCM_PAGES` now maps
  every module VeltOS' KDE packages install (look, input, power, disks,
  Info Center modules ...) to a VeltOS page; a test checks that every
  target page exists (`kcm_updates` first pointed at an action id).
- Image: APT pins keep plasma-discover*, kup-backup, kdeconnect,
  khelpcenter, kmenuedit and kwalletmanager out (all Recommends, checked
  with `apt-cache show`/`rdepends` in the VM); the verify hook fails if one
  comes back or a redirect is missing.
- Start: hidden from Start (still renamed): System Information, Resource
  Monitor, Emoji (Windows + . still opens it). Right-click on the Start
  button opens Windows 11's quick link menu (Windows + X) with VeltOS
  targets. Plasma shows applet menus only through the panel's context
  menu plugin, and VeltOS' locked taskbar has none (libplasma 6.3.6
  `ContainmentItem::mousePressEvent` returns when the plugin has no
  actions), so the button opens a `PlasmaExtras.Menu` itself.
- Menus were 75 % opaque (Fluent, meant for blur): without blur the text
  behind showed through. VeltOS' Kvantum themes now draw menus 94 %
  opaque (`fluent.set_menu_opacity`).
- VM (live): kinfocenter opens Settings > About; Start right-click menu;
  menu show-through measured (darkest pixel over text behind the menu
  216 → 245). Unit tests: veltos-settings 80, veltos-desktop 81. The image
  with the new pins is not built yet.

## 2026-10-21 (10:40) — Clock flyout: Windows 11's two cards

- The product owner sent Windows 11 screenshots of the clock flyout: a
  notification centre card above a separate calendar card. Plasma gives
  an applet one popup; VeltOS keeps the calendar as the applet's popup
  and shows the notification centre as a second Plasma dialog
  (`PlasmaCore.Dialog`) placed 12 px above it, at the popup window's
  position. Read in libplasma 6.3.6 (`dialog.cpp`, `appletpopup.cpp`):
  the applet popup closes when it loses the focus unless the focus goes
  to a popup-type window, so the second card is of the *notification*
  type with `Qt.WindowDoesNotAcceptFocus` (KWin then never activates it);
  clicking it keeps the calendar open (VM). On Wayland a new position is
  applied with the next frame only, so the card draws one after moving.
- Notification centre: "Notifications", do-not-disturb button (accent
  when on; the taskbar shows Windows' bell with "z"), "Clear all"; the
  notifications grouped by app, newest app first (the model keeps the
  order of arrival; sorted by time and id), app heading with settings and
  clear buttons on hover, the newest notification as a card with time
  (time today, weekday this week, date before) and a chevron that folds
  its text, "+N notifications" unfolds the app's older ones, action
  buttons on unfolded cards, scrolls up to the top of the screen.
- Calendar card: long date without the year as heading ("21 Ekim
  Çarşamba") with a chevron that folds the month away (kept in the
  applet configuration), month with Windows' triangle arrows, Windows'
  two-letter weekday names (Turkish "Pt Sa Ça Pe Cu Ct Pa" through the
  translation), focus session row "– 30 min +" / "Focus" (5 to 240
  minutes in Windows' steps); a running session shows the time left and
  "Stop", turns on do-not-disturb until its end, survives a Plasma
  restart and ends with a "Focus session complete" notification from
  "Clock" (gdbus needed `--` before the arguments: it took the timeout
  -1 for an option). Win+N opens the flyout (layout script).
- VM (live, ISO 20261021-060905 with the new package): light and dark,
  grouping and unfolding, do-not-disturb on/off, folding the month (the
  upper card follows), focus start/stop, the end notification (session
  end simulated with a near end time), Win+N. 80 veltos-desktop unit
  tests (new: clock translations incl. plural strings, two-card set-up).
  Not checked: Turkish texts on screen (translations compiled and
  tested), the sound hint of the end notification.

## 2026-10-21 (09:15) — Camera: Windows 11 shutter

- The shutter now carries the mode's picture like Windows 11's Camera: a
  camera on the white disc for photos, a red dot for videos, a red square
  while recording. VM (virtual webcam): both modes.

## 2026-10-21 (09:10) — Mail in the look of Windows 11's Outlook

- The product owner wants Mail to look exactly like Windows'. Windows 11's
  mail app is now "Outlook for Windows" (app bar, folder pane, card list,
  reading pane; Wikipedia's screenshot used for reference). Writing a mail
  client is out of proportion (IMAP/SMTP/OAuth); Thunderbird 140's layout
  already has those parts, so VeltOS restyles it:
  `veltos-desktop/mail/mail.css`, registered by Thunderbird's autoconfig
  as a user style sheet, scoped with `@-moz-document` to Thunderbird's own
  windows (never the mails it shows). Selectors and variables were read
  from Thunderbird 140.17's omni.ja (about3Pane.css, threadCard.css,
  tree-listbox.css, messageHeader.css, spacesToolbar.css).
- Look: window background (light Mica-like) behind the app bar, folder
  pane and toolbar; the message list and reading pane as white cards with
  rounded corners; rounded rows with an accent bar for the selected folder
  and message; unread subjects in the accent colour; "New message" filled
  with the accent; flat Reply/Forward buttons; light and dark.
  Defaults: folders, list and reading pane side by side
  (`mail.pane_config.dynamic` 2), mails in the normal font
  (`mail.fixed_width_messages` false).
- VM (installed system, local Inbox with sample mails): layout as above.
  Not checked: dark mode, a real account.

## 2026-10-21 (09:00) — VeltOS Archive (WinRAR's layout)

- The product owner: an archive app for ZIP and RAR, WinRAR's look.
  Verified in the builder: Debian 13 has `7zip` 25.01 (main),
  `7zip-rar` 25.00 (non-free: RARLAB's unRAR code, the 7-Zip RAR plugin),
  `unrar` 7.1.8 and `rar` 7.11 (non-free); 7-Zip with 7zip-rar listed and
  extracted RAR4/RAR5 archives made with Debian's `rar`, including
  password-protected ones. 7-Zip shows a .tar.gz as one .tar inside a
  stream (`-txz.tar` failed), so compressed tars go through bsdtar.
- New package `veltos-archive` (PySide6 + QML): WinRAR's window (menu,
  toolbar of large pictures — Add, Extract To, Test, View, Delete, Find,
  Info — up button and archive path, Name/Size/Packed/Type/Modified/CRC32
  list, status bar with lock), Windows 11 controls and dialogs
  ("Extraction path and options", "Archive name and parameters",
  passwords with "wrong password" retry), and WinRAR's small progress
  window for File Explorer (`--extract-here`, `--extract-to-folder`,
  `--add`, `--add-to`). Creates ZIP (AES-256 passwords), 7Z (encrypted
  names), TAR.GZ/TAR.XZ/TAR.ZST; RAR creation needs RARLAB's proprietary
  `rar` and is shown disabled with a note.
- The image: `veltos-archive` and `7zip-rar` instead of KDE's Ark (verify
  hook: Ark absent, 7-Zip has the Rar5 codec); Start's Ark pin is swapped
  once (`archivePinned`); File Explorer's "Extract All…", new "Extract
  here", "Compress to ZIP file" and new "Add to archive…" run it.
- Archive files (.zip, .rar, .7z, tar archives) show the zipped folder
  icon like Windows (veltos-fluent-icons `branding/mimetypes/`).
- Package builds: veltos-archive 21 tests (real 7-Zip and bsdtar),
  veltos-explorer 38, veltos-desktop 76. VM (installed system, Ark
  removed): RAR5 opened from File Explorer in WinRAR's layout, Extract To
  with the default folder, password RAR asked for its password and asked
  again after a wrong one, "Add to archive…" made a .7z, "Extract here"
  on a ZIP, zipped-folder icons in File Explorer. The correct password of
  the test RAR was not typed in the VM (it has a Turkish letter the VM's
  key sender cannot type); passwords are covered by the unit tests.
- Known: the "Open archive" file dialog is Qt's own (QML) dialog, not
  KDE's, because the app is a QGuiApplication.

## 2026-10-21 (08:40) — Start: slides in, acrylic tint

- The product owner: Start should have Windows 11's quality (transparency,
  animation, icons). Frames taken while Start opened showed no animation
  (Plasma's popups have an `animated` property, off in CompactApplet.qml)
  and an almost opaque surface: VeltOS' Start painted a 94 % tint over
  Plasma's popup background, hiding the blur.
- `CompactApplet.qml` override: `animated: true` for the taskbar's
  flyouts, so KWin's sliding popups effect slides Start (and the other
  flyouts) in from the taskbar like Windows 11. VM: frames show the slide.
- Start's tint is now 35 %: with the blur effect Plasma's popup background
  is see-through ("acrylic"); without it (software rendering) Plasma uses
  the solid background, so text stays readable. The test VM has no blur
  (KWin reports `blur` not loaded with llvmpipe), so the acrylic look is
  **not yet seen**; it needs a PC with a GPU.
- The new icon family shows in Start (previous entry).

## 2026-10-21 (08:30) — One Windows 11 style family of app icons

- The product owner: Camera, Mail, the archive app, Calculator, Settings
  and the other default apps should have Windows 11 like icons that match
  each other. Windows 11's icons were looked at for reference (Wikipedia
  articles' logos); VeltOS draws its own (`veltos-fluent-icons/tools/
  app-icons.py`): objects rather than tiles, soft top-to-bottom gradients,
  light from the top left, the same faint contact shadow — Calculator,
  Camera, Mail (envelope), Snipping Tool, Store (bag with the VeltOS V),
  Settings (gear), Task Manager (chart), File Explorer (folder with a
  blue tab), Notepad (Text Editor), Photos, Document Viewer (PDF page),
  Archive (zipped folder), Media Player. No Microsoft file or logo is
  used.
- Each drawing is installed in `.Fluent-base/scalable/apps` under the
  VeltOS app's name and the names of the KDE/Debian apps it stands for
  (e.g. `thunderbird` gets the envelope, `org.kde.kwrite` the notepad); the
  VeltOS apps' own hicolor icons are the same drawings (non-Fluent themes).
- VM (installed system): Start shows the new family (pinned apps and the
  category cards).

## 2026-10-21 (08:10) — File Explorer: Windows 11 folder colours, whole pins

- The product owner sent Windows 11's File Explorer for reference: the
  special folders are coloured (Desktop blue, Downloads teal, Documents
  slate, Pictures blue, Music orange to pink, Videos purple, each with a
  white mark), plain folders yellow, Home an orange house; and the pins
  next to the pinned folders in VeltOS were cut in half.
- veltos-fluent-icons draws the special folders that way
  (`tools/draw-icons.py`, VeltOS drawings) with separate 16 px drawings
  for the navigation pane; `recolour-folders.py` keeps VeltOS's small
  drawings instead of dropping all small place icons. New icon
  `veltos-home` (orange house) next to every `user-home` of the Fluent
  themes; File Explorer's Home uses it (tab, address bar, navigation).
- Pins: the navigation pane's column was as wide as the pane while the
  scroll view shows only its `availableWidth`, so the right end of each
  row (the pin) was clipped. The column now takes `availableWidth`. The
  pin itself is an SVG (`qml/pin.svg`, a closed head and needle like
  Windows 11's) instead of open Canvas strokes that read as an "x".
- Package builds: veltos-fluent-icons (install checks), veltos-explorer
  38 tests. VM (installed system): coloured folders in Quick access and
  the navigation pane, orange Home, whole pins.

## 2026-10-21 (04:15) — New ISO checked screen by screen; Start centred

- ISO `veltos-0.1.0-dev-20261021-001546` (all work up to Mail; Camera
  came later): `build/run.sh test uefi` passed every check
  (`out/test-results/20261021-003040-uefi`).
- **Boot and installation recorded frame by frame** (`frames:` action,
  one screenshot per 1–8 s) for the product owner's "never show code or
  logs during installation and start-up": live boot = firmware logo,
  VeltOS splash, "Welcome" splash, desktop; installed system = firmware,
  boot splash, lock-style sign-in screen. The only text is OVMF's own
  "BdsDxe: loading Boot0001" line, printed by the VM firmware before
  VeltOS starts (real PCs show their maker's logo there). The installer,
  however, showed commands: the Summary page listed partition operations
  and the installation page "Running command
  /usr/libexec/veltos-installer/sources-media..." with a "Toggle log"
  button. Both are gone (commit cfe8fde); checked in the live VM with
  the rebuilt package: Users → confirmation → slideshow with only the
  progress bar → "All done".
- Installed system (same VM): sign-in screen with the default account
  picture; Mail found in Start and opened without the privacy tab after
  the fix; Camera with a virtual webcam (v4l2loopback fed by ffmpeg's
  test picture): preview, photo, video (H.264 after the fix).
- **Start centred like Windows 11**: Plasma places an applet's popup over
  its "visual parent"; the desktop shell's `CompactApplet.qml`
  (plasma-desktop-data 6.3.6) now gives the Start menu an empty item in
  the middle of the panel window as visual parent (override spec
  `org.kde.plasma.desktop.json`). VM: Start opens centred; the clock and
  Quick Settings flyouts still open over their buttons. veltos-desktop
  76 tests (new: the override applies to Plasma's file).

## 2026-10-21 (01:00) — Mail and Camera; ISO build fixed

- **ISO build failed** (first build since Dolphin left the image): the
  verify hook still required the `kde-plasma-desktop` metapackage, which
  the package list spells out without Dolphin. The hook now checks
  Plasma's main packages and the VeltOS apps; the fixed hook passed in
  the chroot of the failed build (the hook stops at its first failure, so
  the rest had never run).
- **Mail** (product owner: "an e-mail app, Windows 11 look"): writing a
  mail client is out of proportion; Debian's Thunderbird 140.17 ESR
  (verified with apt-cache in the builder; 70 MB package) is installed as
  "Mail"/"Posta", gets the VeltOS caption buttons through its autoconfig
  (`/usr/lib/thunderbird/veltos.cfg`, defaults in
  `/usr/share/thunderbird/defaults/pref/veltos.js`, the paths of
  Debian's package) and starts without the default-client question,
  start page or donation tab. Not yet checked in a VM.
- **Camera**: new package `veltos-camera` (PySide6 + Qt Multimedia 6.8;
  Debian's `libqt6multimedia6` contains the FFmpeg backend, verified by
  listing the package). Windows 11 Camera layout: picture over the whole
  window, Photo/Video, shutter, last capture, change camera, timer,
  settings (grid, sound with videos, save location), Pictures > Camera
  Roll. 10 unit tests; rendered offscreen (no-camera state, settings,
  video mode). Taking photos and videos is **untested**: QEMU has no
  camera.
- `tests/boot/vmpreview.py` gained `frames:SECONDS,STEP,NAME` to record a
  whole boot screen by screen (for the "no log output during boot and
  installation" request).

## 2026-10-21 (00:00) — Default account picture

- The product owner asked for a nice default account picture for "Velt"
  and new accounts. `veltos-desktop/artwork/user-avatar.svg` (VeltOS
  gradient disc, white person; VeltOS artwork) is rendered to
  `/usr/share/veltos/faces/default.png`.
- Where it shows: SDDM (`FacesDir=/usr/share/veltos/faces`, its
  `.face.icon` is the default for accounts without a picture);
  `session-defaults` copies it to `~/.face` and `~/.face.icon` at an
  account's first sign-in unless the account already has a picture (own
  files or AccountsService) — Debian packages may not ship files in
  /etc/skel (lintian error, tried first); Start's account button and VeltOS
  Settings fall back to it.
- Package builds: veltos-desktop 75 tests, veltos-settings 78 tests. VM
  (live, fresh session): `~/.face` created, picture in Start and in
  Settings > Accounts > Your info. The sign-in screen itself is not seen
  in the live system (automatic sign-in); untested there.

## 2026-10-20 (23:45) — Start in the layout of Windows 11's 2025 Start

- The product owner sent a screenshot of the current Windows 11 Start
  ("still not what I want"): search at the top, one scrolling page with
  Pinned, Recommended ("Show all") and "All" with "View: Category", the
  apps grouped into category cards of 2x2 icons, user and power at the
  bottom. (The phone panel on the right is Microsoft's Phone Link and is
  left out.)
- `StartMenu.qml` rewritten to that layout: 46 x 47 grid units; Pinned in
  8 columns, two rows until "Show all"; Recommended in 3 columns, two
  rows; "All" with a View menu (Category, Grid, List; check mark like
  Windows; kept in the applet's `allAppsView` setting). Category cards:
  four a row; the first three icons start their apps, the card (or the
  fourth place with four small icons) opens the category page.
  Calculator is pinned once for existing users (`calculatorPinned`).
- Categories: new helper `/usr/libexec/veltos/start-categories` prints
  {desktop id: category} from the `Categories` keys of the desktop files
  (user's first, then XDG_DATA_DIRS); the menu runs it through the
  executable data engine when it opens. Fewer than three apps in a
  category join "Other", as in Windows. Turkish names as Windows uses them
  ("Üretkenlik", "Yardımcı Programlar ve Araçlar", "Diğer", ...).
- Package build: 74 unit tests OK (3 new for the categories). VM (live):
  Start shows Pinned (12 apps), Recommended (empty message), All in
  categories (Productivity, Utilities & tools, Other); a category opens
  and Esc goes back; Grid and List views; the View menu.
- Known difference: Plasma places the popup above its own button, so
  Start is centred on the Start button, not on the screen as in Windows.

## 2026-10-20 (23:30) — VeltOS Calculator

- The product owner asked for a calculator "like Windows 11, in the same
  theme". New package `veltos-calculator` (PySide6 + QML, like the other
  VeltOS apps).
- Behaviour taken from Windows 11's Calculator: Standard runs operations
  in the order they are entered and shows the running result above the
  number; Scientific respects precedence and has parentheses; "=" repeats;
  % depends on the pending operation; functions are written into the line
  above ("sqr(5)", "sin(30°)"); memory list with per-item MC/M+/M−;
  history; errors "Cannot divide by zero", "Result is undefined",
  "Overflow", "Invalid input"; 16 digits shown in Standard, 32 in
  Scientific, more kept (so 1 ÷ 3 × 3 = 1); "1.e+16" style exponents.
- Decimal arithmetic throughout (Python `decimal`, 60-digit working
  precision): trigonometry by series with exact values at multiples of a
  quarter turn (cos 90° = 0, tan 90° = Invalid input, sin π = 0 with the
  π key), inverse functions through arctangent, logarithms and powers from
  `decimal`. Only n! of a non-integer uses floating point (gamma, 15
  digits).
- Window: title row with navigation, mode name, Keep on top and History;
  memory row; DEG/F-E and the Trigonometry/Function flyouts in Scientific;
  keypad with lighter digit keys and the accent "=" (VeltOS palette,
  light and dark); History/Memory beside the keypad from 640 px width,
  over it below; navigation pane with Standard, Scientific and Settings
  (app theme, About). Keep on top shrinks the window to the basic keypad
  and sets KWin's "keep above" through a KWin script (Wayland clients
  cannot do it themselves).
- The calculator key: KCalc 25.04's desktop file (downloaded in the
  builder) uses `X-KDE-Shortcuts=Calculator`; VeltOS Calculator uses the
  same. Pinned in Start for new users (`main.xml`); the verify hook
  checks the shortcut.
- Problems found on the way: Qt's StyledText has no `<sup>` (x² read
  "x2", now RichText); a QML property called `checked` broke the settings
  page (FINAL property of Qt's buttons); `findChild` misses Repeater
  delegates; `apt-get install` of a same-version local `.deb` left the old
  veltos-desktop in the VM (AGENTS.md gotchas).
- Package build: 42 unit tests OK (veltos-desktop: 71). VM (live, fresh
  session): Calculator pinned in Start, 12 + 7 × 3 = 57 in Standard
  ("19 × 3 =" above), 2 + 3 × 4 = 14 in Scientific, navigation pane,
  Trigonometry flyout, Keep on top stayed above the active welcome window.
- Not done: Graphing, Programmer and Date calculation modes, unit
  converters.

## 2026-10-20 (23:05) — Welcome window: language can be changed again

- The product owner: the English/Türkçe switch of the live welcome window
  could be used once and then the installer took over; it should be
  possible to come back and choose again, and the choice should change the
  language of the running live system.
- VM check first (live, 8 GB): the switch itself works in both directions
  and as often as wanted (sign out, SDDM signs in again, desktop, apps,
  the welcome window and the installer in the new language). What was
  missing: "Install VeltOS" quit the welcome window, so after closing the
  installer there was no way back to the language switch.
- `veltos-live-welcome` now hides the window while `install-veltos` runs
  (QProcess) and shows it again when the installer closes (or cannot
  start). New unit test with a fake `install-veltos`; package build: 21
  tests OK.
- VM: Türkçe → "VeltOS'u kurun" → the installer in Turkish → İptal/Evet →
  the welcome window is back → English → session and window in English.
- Note: a welcome window started from outside the session (guest agent)
  cannot start the installer (pkexec refuses a process outside the active
  session); test with the autostarted window.

## 2026-10-20 (23:00) — Windows programs start without a question

- The product owner: double-clicking an `.exe`, `.msi`, `.bat` or `.cmd`
  file must start the installer at once; the App Installer question
  ("Install 7-Zip on VeltOS?", "Add to Start", an information bar and an
  Install button) came first.
- `veltos-run` now starts the file as soon as it opens (Windows behaviour):
  the "confirm" page, the "Add to Start" check box for programs that need
  no installation (and the launcher writer behind it) and the unused
  `VCheckBox` are gone. The information bar that Windows programs can
  read and change personal files (Wine is not a sandbox) now shows while
  the environment is prepared and the program starts.
- `tests/boot/winapps_vmtest.py` no longer presses Enter for the question.
- Package build: 21 unit tests OK. VM (live, 8 GB): File Explorer >
  Downloads > Enter on `7z2604-x64.exe` → "Setting up Windows
  compatibility…" at once → 7-Zip's own installer → "7-Zip is installed"
  with 7-Zip File Manager and 7-Zip Help. With the earlier 4 GB VM the
  same click showed "Not enough free space" (the live system keeps files
  in RAM; the check is right).
- Log headings of earlier entries today said 2026-10-21; the commits were
  made on 2026-10-20 and the headings are corrected.

## 2026-10-20 (22:30) — Windows drives in File Explorer

- The product owner wanted Windows (NTFS) drives visible, safe file
  exchange and a Windows mark on them.
- **Mounting**: udisks2 2.10.1 (Debian 13) tries the kernel's ntfs3 first
  and, by default, allows file names Windows cannot use. VeltOS sets
  `/etc/udisks2/mount_options.conf` (veltos-explorer): ntfs-3g first, both
  drivers with `windows_names`. ntfs-3g 2022.10.3 mounts a Windows that
  did not shut down completely (Fast Startup, hibernation) read only by
  itself; File Explorer detects the read-only mount (/proc/self/mounts)
  and explains it the Windows way (start Windows, Shift + Shut down). If
  a read-write mount fails, it retries read only.
- **No password for administrators**: `/usr/share/polkit-1/rules.d/
  50-veltos-drives.rules` lets active local users in the sudo group mount
  internal file systems (udisks2 asks for an administrator password by
  default, in KDE's polkit window).
- **This PC**: Windows' recovery and reserved partitions are hidden; a
  Windows drive has its own icon (`drive-harddisk-windows`: the local disk
  with a blue window mark — not Microsoft's four-pane logo, which is a
  trademark VeltOS does not ship); a drive holding `Windows/System32`
  without a label is called "Windows"; inside a drive the address bar
  reads "This PC > <drive>" instead of "Local Disk > media > velt > …".
  KDE shortens an icon name it cannot find in the theme before looking in
  hicolor, so the icon is installed in the Fluent themes next to
  drive-harddisk.
- VM (live) with a 1.1 GB NTFS partition on a loop device: shown with the
  Windows icon, opened from File Explorer without a password (ntfs-3g,
  files owned by the user), writing works, `bad:name.txt` refused; with a
  hibernation file the drive opened read only and the explanation showed.
  (Commands run through the VM's guest agent are outside the session, so
  polkit refused them; File Explorer started from the taskbar worked.)

## 2026-10-20 (18:15) — Stacked taskbar button for several windows

- An app with several windows showed Plasma's "+" under its taskbar icon
  (the theme's `group-expander` picture). Like Windows 11, it now shows a
  stacked button: a second plate peeks out on the right while the button
  is pointed at or active, and no plus sign (two more replacements in
  the task manager override: GroupExpanderOverlay hidden, a plate behind
  the button frame in Task.qml). VM: two File Explorer windows.

## 2026-10-20 (18:10) — Terminal follows light and dark

- The product owner wanted the Terminal to change with light/dark mode
  and a nicer look. Two profiles now: "VeltOS Light" (Windows Terminal's
  One Half Light colours) and "VeltOS Dark" (Campbell).
  `system/terminal-theme light|dark` sets the default profile, the tab
  style and switches open terminals over Konsole's D-Bus
  (`org.kde.konsole.Session.setProfile`); it runs at sign-in (from the
  theme in kdeglobals) and from VeltOS Settings' Light/Dark switch. A
  profile the user chose is left alone.
- Tabs like Windows Terminal: rounded top corners, the selected tab in the
  colour of the terminal, own close crosses for light and dark. Konsole
  25.04 ignores `TabBarStyleSheet` unless `TabBarUseUserStyleSheet` points
  to a file (read in `ViewContainer.cpp`), so the styles are
  `/usr/share/veltos/konsole/tabs-{light,dark}.css`.
- VM: dark and light terminals with two tabs, close buttons visible in
  both; switching the theme recoloured an open terminal (its tab style
  changes with the next window — Konsole does not reload it).

## 2026-10-20 (18:05) — Settings without KDE's settings windows, pins in File Explorer

The product owner asked that KDE's old settings never open ("Change
account settings" in Start opened KDE's Users page) and that the icons in
Settings be alike.

- **Every KDE settings module in VeltOS Settings was replaced** by a page
  of its own (15 new pages): Notifications (do not disturb, sounds,
  banners per app), Power & battery, Night light, Multitasking, Mouse,
  Touchpad, Typing (keyboard layouts), Lock screen, Default apps, Startup,
  Your info, Sign-in options (change the password), Other users (add,
  administrator, remove), Language & region, Accessibility (text size,
  animations), Searching files. Settings that have no page yet (VPN and
  wired details, proxy, firewall, fonts, pointer style, per-app volume,
  display arrangement, game controllers, tablets, on-screen keyboard,
  spelling) were removed instead of opening KDE's window. The "More …
  settings" links of the existing pages went too; Date & time sets the
  time by hand in Settings.
- **`systemsettings` and `kcmshell6` are diverted** (veltos-settings
  preinst, KDE's at `*.kde`) to `veltos-settings-redirect`, which maps the
  module name to a page (`catalog.KCM_PAGES`, Home for others). So Start's
  "Change account settings" (KCMLauncher → `systemsettings kcm_users`),
  KRunner results and KDE programs' "Configure" links open VeltOS
  Settings. The Ctrl+Alt+Del "Change a password" and Quick Settings'
  night light now call VeltOS Settings directly.
- How settings are applied (checked in source or the VM): KDE config files
  through `kwriteconfig6 --notify` (Plasma's notifications watch
  plasmanotifyrc; keys from plasma-workspace 6.3.6 kcfg files),
  PowerDevil `reparseConfiguration`, KWin `reconfigure`, keyboard layouts
  with the `org.kde.keyboard.reloadConfig` signal; mouse and touchpad
  through KWin's `org.kde.KWin.InputDevice` D-Bus properties (read in the
  VM) and kcminputrc `[Libinput][vendor][product][name]`; users through
  AccountsService (accountsservice 23.13.9 in the image); the password
  through `passwd` in a pseudo terminal. `xdg-mime query` failed for
  text/plain in the session ("Illegal number", xdg-utils), so default apps
  are read from and written to mimeapps.list directly; Okular opens PDFs
  through a hidden helper entry, offered under Document Viewer's name.
- **Icons**: the cards and the navigation pane use Fluent's monochrome
  `-symbolic` icons in the text colour at one size (all names checked in
  the VM); a test rejects any other icon on the pages.
- Start: "Log Out" reads "Sign out"; Spectacle in the pinned apps is
  swapped for Snipping Tool once. Windows + Space switches the keyboard
  layout for new users (`/etc/xdg/kglobalshortcutsrc`).
- **File Explorer**: the pin next to pinned folders was Fluent's 12 px
  `window-pin` icon, which showed as a cut "x"; it is now a drawn push pin
  (VM: whole and sharp).
- VM (live, rebuilt packages): `systemsettings kcm_users` and Start's
  "Change account settings" opened Accounts > Your info; Apps, Default
  apps (Firefox, Photos found; others fixed afterwards) and Power pages.
  Not yet checked on screen: adding a user (polkit prompt is still KDE's
  window), changing the password, mouse settings on real hardware.

## 2026-10-20 (night, latest) — VeltOS Snipping Tool

- **New package `veltos-snip`**: Windows 11's Snipping Tool. Print Screen
  or Windows + Shift + S freezes and dims the screen with the snipping bar
  (Rectangle, Window, Full screen, Freeform, close); the snip goes to the
  clipboard, into `Pictures/Screenshots/Screenshot YYYY-MM-DD HHMMSS.png`
  and a notification with the picture ("Snip copied to clipboard") opens
  it for markup. Windows + Print Screen saves the whole screen. The app
  window has "+ New", mode, delay, ballpoint pen, highlighter, eraser,
  crop, undo/redo, Save and Copy.
- Capture: KWin gives screenshots on Wayland only to programs it trusts
  (`org.kde.KWin.ScreenShot2` is restricted); the tool runs Spectacle in
  the background for one full-desktop picture (`spectacle --background
  --nonotify --fullscreen --output`, 0.37 s in the VM) and does the rest.
  Window mode gets the window frames from a KWin script that calls back
  over D-Bus.
- Shortcuts: `X-KDE-Shortcuts` in the tool's desktop actions. Spectacle's
  shortcuts are switched off by `update-app-names` (copy without the keys,
  plus `kglobalaccel/org.kde.spectacle.desktop` with `NoDisplay=true`,
  which kglobalacceld 6.3.6 skips — read in its source) and Spectacle is
  hidden from Start. Plasma's clipboard keeps pictures now
  (`/etc/xdg/klipperrc` `IgnoreImages=false`; Klipper's default ignores
  them, klipper.kcfg 6.3.6), so a snip stays pasteable after the tool ends.
- Package names checked in the VM (`apt-cache policy`): kde-spectacle
  4:6.3.5-2, libglib2.0-bin 2.84.4, qml6-module-qtqml-models 6.8.2.
- VM (live, rebuilt packages): kglobalaccel lists Print and Meta+Shift+S
  for the tool and nothing for Spectacle; Print showed the dimmed screen
  and the bar; a dragged rectangle was saved and the notification showed
  it; selecting the notification opened the markup window; pen and
  highlighter drew. Found on the way: the notification number was read
  from gdbus' "(uint32 5,)" with the digits of "uint32" (325), so the
  click was not recognised — fixed and tested.
- Not yet: video recording, "Save as" dialog, several screens with
  different scale factors (untested).

## 2026-10-20 (night, later) — Terminal like Windows Terminal, Task View desktops

- **Terminal** (Konsole) in the look of Windows Terminal: VeltOS profile
  with the Campbell colours, Cascadia Mono 12 (`fonts-cascadia-code`
  2407.24-1, Debian main, added to the image), bar cursor, 120 x 30,
  9001 lines of history; tabs always shown with a "+" button; no toolbars
  (copies of Konsole 25.04.2's `konsoleui.rc`/`sessionui.rc` without them,
  same numbers as the built-in files, which were read from Konsole's
  library in the VM: 20 and 36). Found on the way: a comment with the
  word "version" before `<gui>` made KXMLGUI skip the files; Konsole's
  see-through window showed other windows through the tab bar — the
  Terminal launchers now pass `--notransparency`. **Terminal icon**: a
  dark window with a grey tab strip, ">" and "_" (original drawing after
  the product owner's Windows Terminal reference; 16 px version).
  VM: Terminal opened with the profile, no toolbars, opaque tab bar.
  VM: the new icon on the taskbar (after restarting plasmashell).
- **Virtual desktops** checked in the VM: windows appear only on their
  own desktop and in its taskbar; pinned apps (File Explorer, Firefox,
  ...) appear on every desktop, as on Windows 11. Task View now shows a
  desktop's windows while the pointer is on its card, like Windows 11
  (VM: Desktop 2 showed only its Terminal, Desktop 1 its two windows).

## 2026-10-20 (night) — product owner's list, first part

Requests from the product owner's long list; everything below was built
(`build/run.sh packages ...`, unit tests passing) and, where stated,
checked in the live VM (ISO 20261020-083729 with the rebuilt packages
installed, 4 GB RAM).

- **Maximised windows: square close-button hover.** The red hover of the
  close button rounds the window's top right corner; on a maximised
  window that rounding showed in the screen corner. KWin's Aurorae engine
  has no button pictures for maximised windows, so `update-plasma-overrides`
  now also changes KWin's Aurorae QML (`/usr/share/kwin/aurorae`, located
  through `XDG_DATA_DIRS` like Plasma's packages): a button SVG may have
  `hover-maximized` / `pressed-maximized` pictures, used while the window
  is maximised (`plasma-overrides/aurorae.json`, three exact
  replacements in `AuroraeButton.qml` of KWin 6.3.6). The script's paths
  changed to share roots (`--source /usr/share`, `--out /var/lib/veltos/xdg`).
  VM: rounded hover on a normal window, square hover when maximised
  (after signing out and in, KWin loads the QML at start).
- **No spinning circle** over a taskbar button while its app starts
  (Task.qml override). VM: none while Firefox started.
- **Desktop order** Install VeltOS, Recycle Bin, This PC, VeltOS Store
  (date order with fixed old dates); **Store on the desktop and pinned to
  the taskbar** (layout script for new users, once for existing users by
  `session-fixups`). VM: both.
- **Dolphin removed** from the image (only VeltOS File Explorer):
  `kde-plasma-desktop` replaced by its dependencies without
  `kde-baseapps`, Dolphin pinned out; the verify hook rejects it. Needs an
  ISO build to be seen.
- **File Explorer answers "show in folder"** (`org.freedesktop.FileManager1`,
  D-Bus activated `veltos-explorer --filemanager1`); a file argument opens
  its folder with the file selected. VM: `ShowItems` opened Downloads with
  the file selected — after moving Dolphin's service file away, because
  this older live system still has Dolphin and dbus picked Dolphin's
  (two services for one name are undefined; the new image has only ours).
  **Scrolling** with the mouse wheel works in long folders (fixed earlier
  tonight; VM).
- **Icons:** small (16–24 px) Local Disk and Recycle Bin icons drawn on a
  16 px grid (the scaled-down large ones looked cut off); "Close" in menus,
  dialogs and tabs is a thin monochrome cross like Windows 11 instead of
  Fluent's red disc. VM: taskbar menu "Close".
- **Settings > System > About:** Developer Ahmet Furkan Demir, email and
  website as links. VM: shown.
- **Windows program runner:** `.bat` and `.cmd` files open in the runner
  ("Run hello.cmd?"), run by Wine's `start` like a double click in
  Explorer; `.cmd` gets the batch MIME type (`veltos-winapps.xml`, shared-
  mime-info 2.4 has only `*.bat`). The runner window now has the Windows
  11 App Installer layout (question and publisher/version left, icon
  right, InfoBar, check box, accent button, thin progress bar) in the
  VeltOS palette instead of KDE controls. VM: confirmation page, "not
  enough space" page (live session with 4 GB RAM). **Not observed:** the
  batch file's console window — the live VM had too little memory to
  create the Windows environment; that Wine opens one comes from Wine
  10.0's `start.c` (ShellExecuteEx without `SEE_MASK_NO_CONSOLE`).
- **Bottles** (asked as a second engine next to Wine) is not in Debian 13
  (checked on packages.debian.org); it is only on Flathub, which the
  "signed Debian archives only" rule excludes. Waiting for the product
  owner's decision.

## 2026-10-20 (evening, again) — ISO 20261020-083729, black UEFI boot menu, lock screen

- **ISO 20261020-083729** (everything up to the Store): verify hook passed;
  boot test **BIOS PASS**, **UEFI FAIL twice** (black screen, no boot in
  313 s). Investigation: the old ISO drew the boot menu when F4 was
  pressed, the new one stayed black and GRUB waited (Enter booted it). The
  two ISOs' GRUB files were identical except `splash.png`, whose only
  change is the build date text; putting the old picture into the new ISO
  (xorriso) brought the menu back, and so did the *new* picture rewritten
  without filters and compression. So GRUB's PNG reader fails on some
  compressed pictures; because the boot test pressed F4, it hit the
  invisible menu (config.cfg draws text outside the theme black on black).
  Fix: `build/scripts/plain-png.py` rewrites every GRUB picture
  unfiltered and uncompressed — in the image by the binary hook
  `9100-veltos-grub-png`, for installed systems in veltos-boot's GRUB
  theme (copy of the tool, kept identical by a repository test). The boot
  test now repeats F4 until the menu is drawn, checks that it was drawn
  and repeats Enter until it is gone. With F4 sent earlier the same ISO
  passed all 17 UEFI checks. **The fix still needs an ISO build.**
- **Windows 11 lock screen** (Win+L, Ctrl+Alt+Del > Lock): the time and
  date on the picture, then (click or key) the blurred picture with the
  account picture, the name, the password box (show button, arrow), the
  power menu and battery. kscreenlocker takes the lock screen from
  Plasma's desktop *shell* package, so `update-plasma-overrides` now also
  handles shell packages and whole-file replacements (only while Plasma's
  file has the recorded sha256). Verified in the VM: lock, wrong password
  ("The password is incorrect. Try again."), unlock.
- **Folder and local disk icons** in the look of Windows 11 (yellow
  folder; Desktop, Downloads, Documents, Pictures, Music, Videos with
  coloured marks; disk slab) drawn by `tools/draw-icons.py`. Fluent's
  scalable place icons are symbolic links, which the package now replaces
  too. Built, not yet seen on screen.

## 2026-10-20 (later still) — VeltOS Store, Windows 11 style bin and PC icons

- **VeltOS Store** (new package `veltos-store`, PySide6/QML) in the
  Microsoft Store layout: navigation rail (Home, Apps, Gaming, Library),
  search box, featured banner, rows of app tiles, category chips, app
  pages, Library with "Get updates". Catalogue: Debian's AppStream data
  through `gir1.2-appstream-1.0` (1.0.5-1, Debian main; 2091 desktop apps
  load in 0.9 s in the VM); installs through `pkcon` (PackageKit). Start
  and Settings use it instead of Discover (hidden, still installed).
  Verified in the live VM: Home, VLC's page, Install (5.6 s, no password
  in the live session), Open (VLC started), Library with VeltOS's names,
  "Uninstall" of Firefox refused because apt would also remove parts of
  VeltOS. Found on the way: the image's AppStream data had outdated
  screenshot addresses (404 on appstream.debian.org; the media folder
  hash changes with package updates) — the Store now refreshes data older
  than two days and hides screenshots that fail; Start did not swap the
  pinned Discover because its favourites model was not ready on first
  open (it now retries); pkcon run outside the session (guest agent) gets
  no authentication agent — test installs from the session.
- **Recycle Bin and This PC icons** redrawn after the product owner's
  Windows 11 references (`tools/draw-icons.py`): glass bin with grey foot
  and blue recycling arrows, empty and full of crumpled paper; monitor
  with a cyan-to-blue screen on a grey stand. Original drawings in that
  look; Microsoft's files are not used.

## 2026-10-20 (late night) — Ctrl+Alt+Del, power key, locked taskbar, toasts, wallpapers

Product owner requests, tested in the live VM of ISO 20261019-222530 by
installing the rebuilt packages (`dpkg -i`, then signing out and in):

- **Live welcome language switch closed the window without changing the
  language**: the sign-out request was sent without waiting and was lost
  when the window quit. It now waits for the D-Bus reply (unit test).
  Verified: English/Türkçe sign out and back in in the chosen language.
- **Ctrl+Alt+Del** shows Windows' security options screen
  (`plasma/logout/Logout.qml`): blurred sign-in wallpaper, Lock, Switch
  user, Sign out, Change a password (KDE's Users page), Task Manager,
  Cancel, and the power button with Sleep / Shut down / Restart in the
  bottom-right corner. Programs are started through Plasma5Support's
  "executable" engine with `setsid -f`. Verified: screen, power menu, Task
  Manager opens. A program asking to shut down still gets the small card.
- **Power key** (VirtualBox "send the shutdown signal") now shuts down
  like Windows (`/etc/xdg/powerdevilrc PowerButtonAction=8`). Plasma
  showed its logout screen, which cannot appear over the lock screen.
  **Not yet observed** (it ends the VM; to check on the next ISO).
- **Taskbar locked** like Windows: no "Add Widgets", no edit mode or panel
  settings; taskbar items offer no "Configure …" dialogs. Plasma's applets
  follow the lock of the whole shell, not of their panel, so
  `session-fixups` locks every applet (also those in the tray, twice,
  because loading applets may restore their old lock state) and the kiosk
  key `plasma/allow_configure_when_locked=false` hides the dialogs. The
  shell itself is not locked (SystemImmutable would also block the D-Bus
  scripts used by Settings and `plasma-apply-wallpaperimage`).
  Right-click menus (`system/context-menus`, written before plasmashell
  starts): the desktop keeps its file entries only, the empty taskbar
  shows none, taskbar buttons say "Pin to taskbar" / "Unpin from taskbar".
  Verified in the VM.
- **Notifications** (Plasma override): toasts in the bottom-right corner
  12 px from the edge, Windows' width, no line under the app name, picture
  on the left, action buttons of equal width, newest toast nearest the
  taskbar; no bell in the tray — the clock shows the unread count in an
  accent circle (and a muted bell for "do not disturb") and opens the
  notification centre. Plasma's pop-up model lists the oldest first even
  with `sortOrder` changed (tried), so the positioning loop is reversed;
  `Layout.horizontalStretchFactor` did not give equal button widths,
  `RowLayout.uniformCellSizes` did. Verified with test notifications.
- **"Disks & Devices"** is now "Safely Remove Hardware" (Turkish
  "Donanımı Güvenle Kaldır"): small flyout, one list, no sideways scroll
  bar; tray flyouts have no settings or pin buttons. Verified.
- **Window frames like Windows 11's Mica**: the title bar has the colour of
  the VeltOS apps' window background (no white bar above a grey window);
  the minimise glyph sits on whole pixels. KWin had chosen **105 %
  display scale** for the VM screen, which blurred every 1 px line and all
  text; `display-scale` gives each new screen the nearest 25 % step
  (Windows' steps) once, at sign-in. Verified: 100 %, crisp buttons.
- **Icons**: original VeltOS "This PC" (monitor with a blue bloom) and
  Recycle Bin (frosted bin, empty/full) in the Windows 11 style replace
  Fluent's `computer` and `user-trash(-full)` at all sizes — Microsoft's
  icons are not used (copyright).
- **Wallpapers**: new default "VeltOS Bloom" (soft translucent petals
  around the centre) plus "VeltOS Flow", "VeltOS Glow" and the previous
  design as "VeltOS Lake", each light and dark (`tools/wallpapers.py`);
  Settings hides KDE's "Next". Verified on the desktop (light).
- Taskbar window tooltips use a plain close glyph instead of KDE's red one.

Problems: `pkill -f` patterns in `vm exec` killed the shell running them
again (the welcome window then was not restarted); a host-side unit test
run left `__pycache__` in the tree and the repository test failed the
package build; Bash heredocs turned `\` + newline in Python sources into
real newlines again (fixed with the Edit tool).

## 2026-10-20 (night) — ISO with all of today's work; Konqueror out

- ISO `veltos-0.1.0-dev-20261019-222530` (everything up to the Task
  Manager): verify hook passed; boot tests UEFI PASS (16 checks) and BIOS
  PASS (15), no crashed processes. Its live session showed Konqueror as
  the first pinned app in Start: `preferred://browser` fell back to it
  because Debian's KDE defaults name Falkon (not installed), and
  Konqueror (recommended by kde-baseapps) also preloads itself at every
  sign-in (it showed in Task Manager's Startup apps).
- Fix: Konqueror pinned out of the image (verify hook checks it) and
  `BrowserApplication=firefox-esr.desktop` in kdeglobals.
- The ISO with this fix (20261020-021732) passed the verify hook (no
  Konqueror), but copying it to `out/` failed: the host's C: drive was
  full (325 MB free; eight 3.5 GB ISOs in `out/iso`). Superseded ISO
  outputs were deleted (kept: 20261019-174700, used for the encrypted
  install test, and 20261019-222530, the latest tested one); 22 GB free
  again. Docker Desktop stopped answering after the disk had been full
  and needs a restart; the fix is therefore **not yet in a built ISO**.
  Keep `out/iso` small (`build/run.sh clean` or delete old builds).


## 2026-10-20 (evening) — VeltOS Task Manager

New package `veltos-taskmanager` (PySide6/QML, psutil 7.0.0 from Debian):
Processes, Performance and Startup apps in the Windows 11 layout,
Ctrl+Shift+Esc (`X-KDE-Shortcuts`), one instance per user (local socket).
KDE's System Monitor is renamed "Resource Monitor"; Start pins Task
Manager. Verified in the VM: Ctrl+Shift+Esc opens it; Firefox shows as one
app with its 11 processes; Performance shows the CPU graph and figures;
Startup apps lists the autostart entries; a second Ctrl+Shift+Esc does not
start a second copy.

Problems: the kernel cuts process names to 15 characters
("veltos-taskman"), so apps are matched by their command line; a process
list replaced every second would lose scroll position and hover, so rows
are updated in place (`model.py`); `data` is a reserved QML property name.
While testing, `kbuildsycoca6` run without `XDG_MENU_PREFIX=plasma-` emptied
the application database (taskbar showed "?" icons) until it was rebuilt
with the session's variables; and one `vm upload` did not replace the
package in the VM - check the installed files after `dpkg -i`.

## 2026-10-20 (later) — Task View, sounds, animations, toasts

- **Task View** like Windows 11 as a KWin QML scene effect
  (`veltostaskview`, public `org.kde.kwin` API only): window thumbnails
  with icon/title/close, desktops strip with "New desktop" and remove,
  Meta+Tab and the taskbar button. Verified in the VM: opens with
  Meta+Tab, hover/close, switching to a second desktop ("No open
  windows"), creating and removing a desktop; helper windows that skip
  the window switcher are left out (the Wayland recording bridge showed).
  KWin keeps a loaded effect's QML: re-login after changing it.
- **No animations in VMs**: KWin had loaded none of its animation effects
  (scale, squash, slidingpopups, slide, maximize...) because it renders
  with llvmpipe. `KWIN_EFFECTS_FORCE_ANIMATIONS=1` in the session script
  (KWin reads it; verified that all of them load after re-login). CPU is
  used only while an animation runs; not measured on real hardware yet.
- **Sounds**: original VeltOS sound theme synthesised at build time
  (`tools/sounds.py`; Windows' sounds are Microsoft's and not shipped),
  login chime enabled. Not listened to (the VM has no audio output).
- **Toasts**: no timeout bar, monochrome close glyph (second
  `update-plasma-overrides` spec). Verified with two test notifications.
- ISO `veltos-0.1.0-dev-20261019-215605` (first part of the day): verify
  hook passed incl. the override check; boot tests not run yet.

## 2026-10-20 — Windows 11 polish: start-up, flyouts, Firefox, File Explorer fix

### Product-owner feedback that drove this work

Dark mode left the taskbar light; an app icon bounced under the pointer
while programs started; "use Windows 11 pointers"; Firefox and other
programs still had "Debian" minimise/close buttons; the status and
notification area and Start should be exactly Windows 11; File Explorer
"does not open any more, shows an error"; broken Turkish text in Settings
(Apps > Windows programs); garbled taskbar window previews; a flat-line
loading screen; text scrolling at start-up; the shutdown menu of the power
key looked like Debian; the on-screen keyboard covered the sign-in screen;
This PC and Recycle Bin on the desktop; File Explorer and Settings icons;
plus larger requests (Task View, Task Manager, Control Panel, animations
and sounds, Wine dialogs, Store) that are not done yet (see status).

### Causes found and fixes

- **File Explorer did not start on Turkish systems**:
  `QTimer(self, singleShot=True, interval=250)` - PySide6 maps keyword
  arguments to setters with the C `toupper()`, which turns `interval` into
  `setİnterval` in a Turkish locale (reproduced in the VM with
  `setlocale(tr_TR.UTF-8)`). Setters now; a repository test rejects the
  pattern; the builder image has `tr_TR.UTF-8` and the Turkish test classes
  of File Explorer and Settings run in it.
- **Broken Turkish text** ("kal dır", "program lar"): Qt Quick's
  distance-field text at the VM's 105 % scale; offscreen renders were fine
  in every locale. All VeltOS QML programs now use native text rendering.
- **Dark taskbar**: the global theme writes `kdedefaults/plasmarc`, the
  taskbar watches the user's `plasmarc` file only, and `kwriteconfig6` did
  not write a value equal to the kdedefaults one; a KConfig change signal
  sent by hand did not help either. Settings now edits the file directly
  (verified: taskbar dark at once on a first switch).
- **Firefox buttons**: Firefox draws its own round libadwaita-style buttons
  and ignores GTK themes (hover showed pink/white circles). An autoconfig
  style sheet gives them the VeltOS 46 x 32 buttons and red close
  (verified on hover). KDE's GTK module produced empty button images for
  our Aurorae frames, so a VeltOS GTK theme (Breeze + our buttons) covers
  other GTK programs.
- **Launch icon at the pointer**: KWin's startup feedback; it never shows a
  busy pointer on Wayland, so it is off. **Pointers**: Debian's default
  `x-cursor-theme` was Adwaita; Fluent cursors are now the default.
- **Sign-in keyboard**: SDDM's default `InputMethod=qtvirtualkeyboard`.
- **Previews**: KWin renders with llvmpipe in the VM and its captures are
  garbled; with software rendering the taskbar shows titles only
  (`session-fixups`, autostart one-shot).
- New: Windows-like "Welcome" splash (blurred sign-in wallpaper, dot
  spinner) instead of the progress line; VeltOS power screen
  (`Logout.qml`); flyouts float with rounded corners
  (`ContainmentPrefersFloatingApplets` kept set by our plasmoids); Start
  (pill search box, Windows buttons, one-line labels, neutral avatar,
  "More" page, File Explorer pinned); clock flyout = notification centre +
  Windows calendar; hidden-icons flyout with icons only through the new
  `update-plasma-overrides` mechanism (architecture 2.3.8); This PC and
  Recycle Bin desktop icons that come back; new File Explorer and Settings
  icons; quiet kernel/systemd options; `xwaylandvideobridge` kept out of
  the image.

### Verified (installed encrypted VM, packages installed with dpkg)

Sign-in without on-screen keyboard -> Welcome splash -> desktop with the
two icons; Start, Quick Settings, clock and hidden-icons flyouts floating;
power screen; notification centre with two test notifications; Firefox
buttons and hover states; File Explorer running in a Turkish locale;
Settings Windows-programs page in Turkish; dark taskbar on a first switch;
`x-cursor-theme`, SDDM, klaunchrc, grub.cfg options in place. Package
tests: veltos-desktop 53, veltos-explorer 31, veltos-settings 57,
veltos-boot 22, calamares-settings-veltos 19, veltos-winapps 20, repo 6.

Not yet: a new ISO with all of this; on-screen check of the quiet start-up
and shutdown; the pointer theme in X11 programs.

### Problems hit

- A new Settings test shifted test order and exposed a teardown bug: a QML
  engine deleted later printed "backend is null" into the next test. The
  engine is now destroyed in `tearDown`.
- Git Bash heredocs turned `\n` in Python sources into real newlines
  several times; such edits are done with the editor tools now.

## 2026-10-19 (night) — Encrypted installation verified, unlock screen like Windows

### Installation test on the fixed ISO

ISO `veltos-0.1.0-dev-20261019-170820`, VM (UEFI), "Erase disk" +
"Encrypt system": Calamares finished; firmware entry `Boot0009* VeltOS`;
`grub.cfg` has the "VeltOS" entries again; booting the disk shows the
password box on the VeltOS boot screen, the correct password leads to
the sign-in screen and the desktop. The three bugs of the previous test
are fixed. Evidence: `tests/results/2026-10-19-encrypted-install-uefi/`.

### Problems seen on the password screen (fixed)

- The prompt read "Please unlock disk luks-<uuid>:" (cryptsetup's text,
  with Calamares' mapping name) in a **monospace** font, and the box, the
  text and the keyboard indicator were drawn over the logo.
  - Font: Debian's plymouth initramfs hook copies only fontconfig's default
    and monospace fonts; the theme asked for Cantarell, which was not in
    the initramfs, and fontconfig chose DejaVu Sans Mono. veltos-boot now
    has an initramfs hook that copies Inter; the theme uses Inter.
  - Texts: the hook changes the initramfs copy of cryptsetup's shell
    functions (`/usr/lib/veltos-boot/unlock-texts`): "Enter the password
    to unlock this PC", after a wrong password "The password is incorrect.
    Try again.", no technical splash messages for a wrong password or a
    successful unlock. A first version showed the warning as a Plymouth
    message; it stayed on screen while the next (correct) password was
    being checked, so the warning now replaces the prompt.
  - Layout: `DialogVerticalAlignment=.6` (below the logo; unit test checks
    600-2160 px screen heights).
- After three wrong passwords cryptsetup gives up and the system falls to
  a recovery shell. Calamares' fstab module drops `crypttabOptions` when
  `/boot` is unencrypted, so a new installer job `crypttab-tries` adds
  `tries=0` (unlimited, crypttab(5)) to entries with a typed password.
- Lintian: `repeated-trigger-name update-initramfs` — `dh_installinitramfs`
  adds the trigger for the new hook; veltos-boot's own `.triggers` file
  was removed.

Verified in the installed VM with the new packages (`dpkg -i`, installer
job run by hand): Inter and the new texts in the initramfs (`lsinitramfs`,
`unmkinitramfs`); prompt below the logo; four wrong passwords in a row
without a recovery shell; correct password -> spinner without messages ->
sign-in screen.

### ISO `veltos-0.1.0-dev-20261019-174700`

- Verify hook passed (new checks: Inter in the live initramfs, installer
  runs `crypttab-tries`, initramfs hook installed).
- Boot tests: UEFI PASS, BIOS PASS (all checks, no crashed processes).
- **Encrypted installation repeated on this ISO**: Calamares ran
  `crypttab-tries` (crypttab `... none tries=0`), "All done"; boot: prompt
  -> wrong password -> "The password is incorrect. Try again." -> correct
  password -> sign-in screen; no failed systemd units.
- Package tests: veltos-boot 22 (was 14), calamares-settings-veltos 19
  (was 17), repo 4.
- Not tested on this ISO: a plain (unencrypted) installation, Secure Boot,
  `test-winapps`, BIOS installation.

### Seen during the installation, not changed yet

- The installer's partition and user pages still use Calamares' own
  icons and layout (only colours and controls are styled).
- Calamares' confirmation dialog has minimise/maximise buttons.
- The keyboard indicator on the password screen ("us") is Plymouth's
  pre-rendered image (bold, not Inter).

## 2026-10-19 (evening) — File Explorer, Settings pages, taskbar, installer, encryption fix

### Product-owner feedback that drove this work

- VirtualBox stopped the installed system at start-up (fixed: GRUB video
  mode, commit 8d06195). Later: an install with "Encrypt system" ended in
  `grub rescue` after the GRUB password prompt.
- "Settings, files, app windows — everything Windows 11", "the taskbar more
  like Windows, translucent", "the installer looks like old Qt", "logo like
  my sketch (V of two bars)", "no Debian anywhere", "File Explorer exactly
  like Windows 11" (with screenshots), "dark mode leaves the taskbar
  white", "show desktop at the bottom right", "Control Panel inside
  Settings", "every window's close/minimise buttons like Windows 11",
  dialogs and confirmations Windows 11 style.
- Asked to ship Windows 11's own wallpapers: declined (Microsoft's
  copyright; an ISO with them could not be shared); original artwork kept.

### Implemented

- **VeltOS File Explorer** (new package `veltos-explorer`): see its README.
  Replaces Dolphin as the default for folders and on the taskbar.
- **Settings**: built-in Wi-Fi, Bluetooth, Sound, Display, Background,
  Colours, Date & time pages (`devices.py` + QML pages, Windows 11 toggles,
  sliders, drop-downs); About shows "OS build" (from
  `/usr/lib/veltos/build-info`, written by the ISO build) instead of the
  kernel; separate Control Panel entry removed; light/dark switch now
  updates the taskbar at once.
- **Taskbar**: 48 px, see-through (opacity in the Plasma theme, translucent
  panel mode, acrylic-like blur where available); Search box, Task View,
  new clock (time over date, same size, four-digit year, calendar),
  show-desktop corner.
- **Window frames**: VeltOS-drawn caption buttons in Windows 11 metrics
  (46×32, thin glyphs, grey hover, red close with the rounded corner),
  32 px title bar, left title with app icon.
- **Logo**: new "V" of two slanted bars (product owner's sketch) in every
  package; wallpaper without logo or text.
- **Installer**: QML side bar with steps and check marks, Back / accent
  Next / Cancel, style sheet for all controls, Kvantum style for its
  dialogs (root).
- **Yellow folders** like Windows 11; coloured place icons at small sizes.
- **No Debian in sight**: console banner, GRUB kernel titles, About page,
  KDE "About this System" page hidden; `systemd-timesyncd` added for
  automatic time.
- **Encryption fix**: `partition.conf` with an unencrypted `/boot`
  (`noEncrypt`), `cryptsetup-initramfs` and `console-setup` in the image,
  `KEYMAP=y` in the initramfs. Before, `/boot` was inside LUKS (GRUB text
  prompt, one try, US keyboard) and the initramfs could not unlock the
  system at all.

### Problems hit (and fixed)

- File Explorer crashed when started from the taskbar but not from the
  test tools: Qt's QML disk cache kept compiled QML of the previous package
  (all packaged files share one time stamp). QML disk cache is now off in
  every VeltOS QML app.
- File Explorer and its tests crashed at exit (QMimeData on the
  clipboard deleted after Python shut down).
- Kirigami found no icons with the "Basic" Qt Quick style outside Plasma.
- Plasma ignored the theme change written to `kdedefaults` until the next
  sign-in.
- Settings' first Wi-Fi code (`nmcli … passwd-file`) made NetworkManager
  ask password agents, which opened the "KDE Wallet" wizard; replaced by
  D-Bus `AddAndActivateConnection` with the key. NetworkManager passes
  `need-auth` once even with a key; a wrong key is detected by the state
  reason.
- Shell heredocs turned `\b` and `\1` into control characters in Python
  sources twice; `tests/repo` now rejects control characters.

### Test runs

- ISO `veltos-0.1.0-dev-20261019-125115`: boot tests UEFI and BIOS PASS
  (16 checks each, no crashed processes), with File Explorer as launcher
  and Dolphin/System Settings hidden.
- Package tests: veltos-desktop 47, veltos-explorer 30, veltos-settings 55,
  veltos-boot 14, calamares-settings-veltos 15, veltos-base 6,
  veltos-winapps 20, tests/repo 4.
- The encryption fix and the new caption buttons are in the next ISO; see
  below.

### Installation test (VM, UEFI, "Erase disk" + "Encrypt system")

First installation test in a VM since the VirtualBox fix. Calamares
finished ("All done"): EFI 300 MiB, `/boot` 1 GiB ext4 unencrypted,
system 38.7 GiB LUKS1; crypttab asks at start-up (`none`), the initramfs
has cryptsetup, the keymap and the boot screen's password box; Calamares
skipped the keyfile because `/boot` is unencrypted. **The installed system
did not start**: the firmware went to its setup page. Causes found:

1. `/boot/grub/grub.cfg` had **no VeltOS entry**. In the image build
   grub-common was unpacked before veltos-boot's preinst diverted
   `/etc/grub.d/10_linux`, so dpkg left Debian's script as
   `10_linux.dpkg-new` and the VeltOS wrapper found nothing to run (it
   exited 0 silently). Every installation since commit 8d06195 was
   affected. Fixed: veltos-boot `Pre-Depends: grub-common`, the postinst
   repairs the stale file, the wrapper now fails update-grub (and the
   installer) when Debian's script is missing, the verify hook checks it.
2. The firmware entry was still called "debian": a shell quoting accident
   had collapsed the doubled backslashes of the `efi-label` helper's grep
   pattern for the `\EFI\debian\` path into single ones, so its grep failed. Fixed with `grep -F`; the helper now has a test
   with fake efibootmgr output.
3. `hwclock` is in `util-linux-extra` in Debian 13; added to the image.

The fixed ISO is tested in the next entry.

## 2026-10-19 (later) — Windows 11 look, Settings app, start-up like Windows

### Product-owner feedback that drove this work

- "The Windows program runner does not work" (fixed earlier the same day,
  commit 65b676c) and "the interface is very bad": files, settings, menus,
  search must be redone, simple, light, like Windows 11; the ISO start-up
  looks bad; it must not be recognisable as Debian.
- After a first round: "still not good"; the clock/date is far too big;
  remove the "Türkçe" boot menu entry; it must not look like Linux at all.

### Implemented

- **Windows 11 look from Fluent-kde** (pinned commit 44794f29c89d,
  SHA-256 checked, `veltos-desktop/tools/fluent.py`): Kvantum application
  style, Aurorae window frames (minimise/maximise/close on the right, app
  icon and left-aligned title), Plasma theme, colour schemes; Windows blue
  replaced by the VeltOS accent; Windows/Manjaro/KDE logos removed.
  Problems found in VM screenshots and fixed: 75 % opaque frames (need
  blur) made title bars and inactive windows see-through → solid variant;
  1 px seam under every window → `BorderBottom=1`; Fluent Light's
  translucent highlight made Kirigami apps use Qt's default blue → accent;
  translucent popups unreadable without blur → opaque unless blur exists.
- **Windows-familiar names** in Start/search (`update-app-names`, dpkg
  trigger, overrides in `/var/lib/veltos/xdg`) and **inside the programs**
  (pseudo-language catalogs `en@veltos`/`tr@veltos`): "Home — File
  Explorer". KDE System Settings is "Control Panel". Developer/KDE extras
  hidden from Start; KDE-only Settings pages hidden (kiosk).
- **VeltOS Settings** (new package `veltos-settings`): Windows 11 layout,
  Home, theme, About/rename PC, Storage, Windows programs, search, EN/TR;
  other settings open KDE's modules.
- **File Explorer**: Windows-like side bar, icon-only toolbar, zip as
  folders, no Templates/Public folders.
- **Taskbar**: Windows-sized two-line clock, tray reduced to network,
  sound, battery, notifications (rest behind "^"), pins File Explorer,
  Firefox, Settings; no show-desktop button; shut down/restart without a
  confirmation screen.
- **Start-up**: hidden boot menu (Esc/F4), boot text invisible, beep
  removed, Inter fonts and rounded highlight when the menu is shown, no
  Turkish entry. **Plymouth splash now actually shows** (see problems).
  SDDM waits for Plymouth.
- **Sign-in screen**: new SDDM theme in Windows 11 layout (time/date →
  picture, name, password; power menu), Inter font, tested offscreen.
- **Live system**: welcome window (Try / Install, English / Türkçe switch
  with automatic re-sign-in), no screen lock/sleep, Turkish locale and
  Firefox Turkish language pack in the image.

### Problems hit (and fixed)

- The VeltOS boot splash had never been shown: Debian's
  `plymouthd.defaults` names a theme that is not installed, so every
  initramfs had only the text splash; after diverting it, the two-step
  plugin still failed because `lock.png` was a symlink into a theme not in
  the initramfs. Found with `plymouth.debug`; images are now copies and
  the verify hook checks the initramfs.
- GRUB fell back to the firmware text console ("glyphs too large to fit on
  screen") because the Inter fonts were loaded before gfxterm started.
- GRUB highlight boxes overlapped the next entry (border slices are drawn
  outside the item) and the countdown bar was a text line tall (any
  `text` property).
- `qt-style-kvantum` has no system-wide theme setting; Lintian rejects
  files in `/etc/skel` → Plasma session script.
- Heredocs in the agent's shell collapse `\\`; several edits had to be
  redone with the file editor (environment quirk, recorded in memory).

### Latest test runs

ISO `veltos-0.1.0-dev-20261019-064631` (verify hook passed):

- UEFI boot test `20261019-065930-uefi`: all 16 checks pass (incl. VeltOS
  Plymouth theme in the initramfs, welcome window, application names,
  per-user defaults, no crashed processes). Screenshots: hidden boot menu
  revealed with F4 (themed, three entries), VeltOS boot splash, desktop
  with welcome window, Start menu.
- BIOS boot test `20261019-070134-bios`: all checks pass.
- Measurements (UEFI, 4 vCPU, 4 GiB, no 3D): systemd-analyze 7.9 s;
  plasmashell running 19.1 s after VM start (the boot menu no longer
  waits); idle used RAM 1691 MiB (baseline 1696 MiB). Largest optional
  processes: Discover notifier 254 MiB RSS, xwaylandvideobridge 151 MiB,
  kdeconnectd 148 MiB, kaccess 133 MiB — candidates for the next
  lightweight pass.
- In the live VM (packages installed on the previous ISO): Settings app
  pages, "Home — File Explorer" / "Welcome — Text Editor" titles, the
  sign-in screen in `sddm-greeter-qt6 --test-mode` (lock view and sign-in
  view).
- Not run: Secure Boot test, Calamares installation, `test-winapps` on
  this ISO; nothing on real hardware.

## 2026-10-19 — "VeltOS everywhere", Windows 11 UI, Windows programs

### Product-owner feedback that drove this work

- After installing the first ISO: "it is just Debian". Nothing may mention
  Debian; installer, boot, menus, settings must all be VeltOS.
- Interface quality like Windows 11: simple icons, a real Start menu,
  soft visuals (a reference image: sky, misty lake, blue ribbon bloom,
  two-blade "V" logo).
- Double-click `.exe` support; automatic hardware support; the audience is
  Windows users and gamers who should not have to learn anything.

### Implemented

- **VeltOS Start** (`org.veltos.startmenu`): Windows 11 style launcher on
  Plasma's kicker models; English/Turkish. Verified in VM: open with Meta,
  pinned grid, All apps, search, context menu.
- **Crash found and fixed**: plasmashell segfaulted at login with the new
  menu. `coredumpctl` + Debian debug symbols located it in Plasma 6.3's
  `SystemModel::refresh()` (null `favoritesModel`); the menu now creates
  that model only after the root model is populated. Boot tests now fail
  on any core dump.
- **Fluent icons/cursors** (`veltos-fluent-icons`) from a pinned,
  checksum-verified release; found that upstream draws `start-here*` and
  Wine icons as Microsoft's Windows logo → replaced with the VeltOS logo /
  removed. Inter as UI font.
- **New visual identity**: two-blade "V" logo; procedurally generated
  "Velt Bloom" wallpaper (sky, sunrise glow, misty hills, lake, layered
  blue petals with radial shading and soft shadows, logo + name); light
  and dark variants. VeltOS Light is now the default theme.
- **VeltOS installer** (`calamares-settings-veltos`), **boot splash and
  GRUB theme** (`veltos-boot`); KDE Welcome Center removed from the image.
- **Windows programs**: `veltos-winapps` (`veltos-run`, default handler
  for `.exe`/`.msi`), `veltos-wine-addons` (Wine Mono 9.4.0 / Gecko 2.47.4,
  SHA-256 pinned to the values in Wine's source), Wine 10 with 32-bit
  support and DXVK in the image.
- Firmware: explicit redistributable list instead of live-build's
  automatic one, which had built non-redistributable Broadcom firmware
  downloads (`firmware-b43*-installer`) into the earlier ISOs. Those ISOs
  were only used for local testing.
- Tooling: `build/run.sh preview` (install fresh packages into a live VM
  and screenshot a scripted interaction), `build/run.sh test-winapps`,
  `fetch-upstream.py` (pinned + verified third-party downloads),
  repository consistency tests (logo copies, CRLF).

### Problems hit (and fixed)

- CRLF files written by Python on Windows broke `debian/rules`.
- `dh_auto_test` runs before `dh_auto_install` (checks moved).
- Debian version ordering with `~` (`10.0~repack-6` < `10.0`).
- `.list.binary` needs `apt-utils` on the build host, and BIOS/UEFI GRUB
  packages must be in separate lists (they conflict).

## 2026-10-18 — Milestones 0 and 1 started

### Environment inspection (developer host)

- Host: Windows 11 Pro, Intel Core i7-13620H (10C/16T), 32 GB RAM,
  NVIDIA RTX 4070 Laptop + Intel UHD Graphics. No native Linux, QEMU or
  WSL distribution; Docker Desktop 28.3.3 (WSL2 backend) installed.
- Privileged Debian trixie containers work → live-build can run in Docker.
- `/dev/kvm` was absent in containers. The WSL2 kernel
  (6.6.87.2-microsoft-standard-WSL2) has `CONFIG_KVM_INTEL=m` and the module
  file exists; `modprobe kvm_intel` in Docker's VM (via `nsenter -t 1`)
  made `/dev/kvm` available with `nested=Y`. Automated in `build/run.sh test`.

### Upstream facts verified (packages.debian.org / tracker.debian.org)

- Debian 13 trixie is stable; latest point release 13.7 (2026-09-12).
- trixie versions: live-build 1:20250505+deb13u1, linux-image-amd64
  6.12.113-1 (backports 7.2.6), plasma-desktop 4:6.3.6-1, Mesa 25.0.7
  (backports 26.1.6), Wine 10.0~repack-6, Calamares 3.3.14-1,
  nvidia-graphics-drivers 550.163.01-2, QEMU 10.0.13, OVMF 2025.02.
- live-build in trixie: default BIOS loader is isolinux unless dracut is
  used; GRUB templates in `/usr/share/live/build/bootloaders/grub-pc` serve
  both BIOS and UEFI and can be overridden file by file; no menu timeout in
  the template; splash.svg is rendered at 800x600 for GRUB.
- live-config 11.0.5 has an SDDM component that writes autologin for the
  live user and picks the `plasma.desktop` (Wayland) session.
- Debian's `desktop-base` (Debian artwork, owns `/etc/xdg/kcm-about-distrorc`)
  is pulled only through sddm's Recommends on `sddm-theme-debian-breeze`.
  `/etc/xdg/kdeglobals` and `/etc/xdg/kscreenlockerrc` are not owned by any
  trixie package (apt-file), so `veltos-desktop` can ship them.
- Breeze colour schemes live in `kde-style-breeze-data`.

### Decisions

Recorded with trade-offs in `docs/dev/architecture.md`: Debian 13 stable base,
Debian kernel, Plasma 6.3 customised via packages (no fork), GRUB for BIOS
and UEFI, Secure Boot via Debian shim, zstd squashfs, NVIDIA proprietary
driver not preinstalled (Hardware Manager will handle it), Calamares with
Debian settings as a stopgap, container-only builds.

### Implemented

- Repository skeleton, `.gitattributes` (LF), GPL-3 `LICENSE`.
- `build/builder/Dockerfile` (trixie pinned by digest), `build/run.sh`,
  `build/scripts/build-packages.sh`, `build/scripts/build-iso.sh`.
- `packages/veltos-base`: os-release via dpkg diversion; 4 unit tests.
- `packages/veltos-desktop`: global themes, centered taskbar layout
  script, Breeze-derived colour schemes, Velt Bloom wallpaper (light/dark,
  7 sizes), splash, SDDM/lock screen branding, logo; 9 unit tests.
- live-build configuration, branded GRUB menu + splash, verification hook.
- `tests/boot/vmtest.py` VM boot test.

### Product-owner feedback applied

- Wallpaper redesigned to follow the Windows 11 "Bloom" style (translucent
  folded petals, soft shadows, light and dark variants) while forming the
  VeltOS "V"; the logo now uses the same petals.
- All repository content in English; READMEs and `AGENTS.md` describe rules
  and status so other people and AI agents can continue the work.

### Problems hit and fixed

- `dpkg-checkbuilddeps` prints "unmet" in lower case; the build-deps parser
  expected "Unmet". Fixed, and `build-essential` added to the builder image.
- Files from the Windows bind mount appear executable; debhelper then
  executed `debian/veltos-base.install` as a dh-exec script. Build scripts
  now normalise file modes.
- `docker build` received a Git Bash `/c/...` path; `run.sh` now passes the
  Windows-style path from `pwd -W`.
- Rewriting the wallpaper's root `<svg>` tag dropped the `xlink` namespace;
  the script now edits only width/height/viewBox (covered by a unit test).

### Verified so far

- `build/run.sh packages`: both packages build; 13 unit tests pass.

### First ISO build and UEFI boot test

- First `build/run.sh iso` succeeded in ~10 min (cold cache):
  `veltos-0.1.0-dev-amd64.hybrid.iso`, 2,607,017,984 bytes. The verify hook
  passed.
- UEFI boot test: system up in 16 s (guest agent), Plasma Wayland session
  in 25 s, no failed units, centered taskbar + VeltOS start button +
  wallpaper confirmed in the screenshot and in the Plasma config.
- **Failure found:** the booted system's `/etc/os-release` said Debian
  (`IMAGE_ID=live`). Cause: live-build's `bootstrap_debootstrap` replaces the
  `/etc/os-release` symlink with a copy of Debian's file. The build hook only
  checked `/usr/lib/os-release`, so it passed. Visible effects: boot menu
  footer "VeltOS 13", KDE Welcome Center "Welcome to Debian". Would also
  have affected installed systems.
- Fix: hook `8000-veltos-os-release.hook.chroot` restores the symlink; the
  verify hook now checks both paths. Rebuilt and retested (next entry).
- Other observations from the first run (not fixed yet): "Install Debian"
  desktop icon from calamares-settings-debian; KDE Welcome Center opens on
  live login; live-session idle RAM 1709 MiB with Welcome Center (333 MiB),
  Discover notifier (241 MiB), KDE Connect (145 MiB) as the largest optional
  consumers.
