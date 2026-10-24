# veltos-settings

**Settings** ("Ayarlar"): the everyday settings app of VeltOS, laid out like
Windows 11 Settings. Written from scratch in Python (PySide6) and QML. KDE's
settings windows are never shown (product owner's rule): every page is
built in, and `systemsettings` / `kcmshell6` / `kinfocenter` / `keditfiletype`
open VeltOS Settings.

## What the user sees

- Navigation pane: account picture and name, "Find a setting" search box,
  Home, System, Bluetooth & devices, Network & internet, Personalization,
  Apps, Accounts, Time & language, Gaming, Accessibility, Privacy &
  security, VeltOS Update. Selecting the account picture opens Your info.
- Pages of cards with monochrome line icons (Fluent `-symbolic` icons in
  the text colour, one size, like Windows 11). A chevron means a page
  inside Settings; a "new window" mark means an app opens (Store).
- Built into Settings:
  - **Home** (Windows 11 24H2 layout): this PC (its wallpaper, name,
    model, Rename), the network and "VeltOS Update — Last checked" (time of
    the newest APT list) at the top; cards: VeltOS apps with "Open VeltOS
    Store", Recommended settings (the three most used built-in pages,
    counted in `~/.config/veltos/settings-recent.json`, Windows' three
    until then), Bluetooth devices (switch, paired devices, View all, Add
    device), Personalize your device (six themes, colour mode, Themes);
  - **Personalization**: the themes to apply at the top; **Themes**
    (`devices.THEMES`): eight themes, each a VeltOS wallpaper, light or
    dark mode and an accent colour (VeltOS light/dark, Lake, Nebula, Ember,
    Tide, Dawn, Flow), applied in order (global theme, wallpaper, accent,
    which is also recorded as `AccentColor` because
    `plasma-apply-colorscheme` does not, followed by KDE's PaletteChanged
    signal so the taskbar, Start and the flyouts change at once), with the
    current theme's
    background/colour/sounds/cursor and "Custom" for own mixes; Background
    lists the installed wallpapers (VeltOS's first, KDE's "Next" left out);
  - **Bluetooth > Add a device**: VeltOS' own dialog (scan with
    `bluetoothctl`, pair, trust, connect; Plasma's Bluetooth agent asks for
    PINs), instead of KDE's Bluetooth wizard;
  - **System > About**: device name (rename through `hostnamectl`, which
    asks for the administrator password), model, processor, RAM, graphics,
    system type, VeltOS version and kernel, with "Copy" buttons; the
    VeltOS website, https://veltos.ahmetfurkandemir.com/ (product owner,
    2026-10-22; also `HOME_URL` in os-release, veltos-base), which
    VeltOS Update lists too ("VeltOS website", opened with `xdg-open`);
  - **System > Storage**: used and free space per drive (the live system
    is labelled as running in memory);
  - **Apps > Windows programs**, like Windows 11's Installed apps: every
    installed Windows program with its own icon (read from its `.exe`,
    cached in `~/.cache/veltos/program-icons`), publisher, version,
    install date and size, read from the Windows environment's registry
    files at once (veltos-winapps `programs.py`; Wine's own "Add/Remove
    Programs" window took many seconds, product owner, 2026-10-22), plus
    programs `veltos-run` started without installing them; the note that
    Wine is not a security sandbox. Each row's "..." offers Open (the
    Start menu shortcut `veltos-run` recorded) and Uninstall, which asks
    first in a small flyout, as Windows does, then runs the program's own
    uninstaller through Wine; the list follows when it is done.
  - **Personalization > Taskbar** (`taskbar.py`, `TaskbarPage.qml`),
    Windows 11's taskbar settings: Taskbar items (Search: hide, search
    icon only, search icon and label, search box; Task view), Other
    system tray icons (Safely Remove Hardware and Eject Media, Input
    indicator, Media playback, Clipboard, Printers: on the taskbar or
    behind the "^" arrow) and Taskbar behaviors (alignment centre or
    left, automatically hide, badges on taskbar apps, combine taskbar
    buttons always / when the taskbar is full / never, the far corner
    shows the desktop). The values live in Plasma's taskbar itself (the
    panel and its applets) and are read and changed through plasmashell's
    scripting interface (`qdbus6 ... org.kde.PlasmaShell.evaluateScript`),
    which updates the running taskbar at once; the locked taskbar can
    still be changed by scripts. Only known values reach the scripts. The
    taskbar's right-click menu opens this page ("Taskbar settings",
    veltos-desktop).
  - **System**: Display, Sound, Notifications (do not disturb, sounds,
    banners per app: plasmanotifyrc), Power & battery (screen off, sleep,
    power button, lid: powerdevilrc + PowerDevil reload; Display's "Graphics
    cards" opens VeltOS Graphics Cards), Night light
    (KWin night colour), Multitasking (snap windows);
  - **Bluetooth & devices**: Bluetooth, Mouse and Touchpad (KWin's input
    devices over D-Bus, saved in kcminputrc), Typing (keyboard layouts,
    kxkbrc);
  - **Personalization > Lock screen** (kscreenlockerrc);
  - **Apps**: Default apps (browser, email, music, video, photos, PDF,
    text; ~/.config/mimeapps.list, hidden helper entries such as Okular's
    PDF entry shown under the app's name), Startup (autostart entries,
    turned off with a Hidden=true copy);
  - **Accounts**: Your info (picture and name through AccountsService;
    the picture is chosen in VeltOS File Explorer's Windows 11 style
    dialog, `veltos-explorer --pick`), Sign-in options (change the
    password through `passwd` in a pseudo terminal), Other users (add,
    make administrator, remove; the administrator password is asked by
    VeltOS' own prompt, package veltos-auth). Like Windows, the new user's
    name may be typed as a person writes it ("Ayşe Yılmaz"): the login
    name is made from it (`accounts.login_name`: "ayseyilmaz") and the
    typed name is kept as the full name; a name that already exists is
    refused. AccountsService calls that polkit may have to authorize
    (`DeleteUser`, `SetAccountType`, and setting the own name and
    picture) carry gdbus' `--interactive` flag and a 300 s timeout, so the
    VeltOS prompt can ask for the password: without them an installed
    system answered "Authentication is required" at once and adding a
    user failed (the live system allows everything; product owner,
    2026-10-22). Adding a user (`CreateUser`, then `SetPassword`) runs
    both calls in one helper process, `veltos_settings/admin_calls.py`
    (Gio, interactive authorization), so polkit asks once — it keeps an
    answer only for the process that got it, and two `gdbus` calls asked
    twice (VM, 2026-10-23); the password hash reaches the helper on
    standard input, never on a command line;
  - **Accessibility > Text size** scales the KDE fonts and, through the
    `textScale` every VeltOS app reads from them, the apps' own texts
    (Settings at once, the others at their next start);
  - **Time & language**: Date & time (also setting it by hand), Language &
    region (plasma-localerc; applies after signing in again);
  - **Accessibility**: Text size (KDE fonts), Animation effects;
  - **Privacy & security**: Screen lock, Searching files (balooctl6).
- "Check for updates" and "Get apps" open VeltOS Store.
- `bin/veltos-settings-redirect`, installed as `/usr/bin/systemsettings`,
  `/usr/bin/kcmshell6`, `/usr/bin/kinfocenter` and `/usr/bin/keditfiletype`
  (KDE's programs are diverted to `*.kde` by the preinst), maps KDE module
  names to pages (`catalog.KCM_PAGES`, every module VeltOS' KDE packages
  install), so KDE programs' "Configure…" links, the Start menu and
  KRunner open VeltOS Settings; KDE Info Center opens About, KDE's file
  type editor opens Default apps. The diverted `*.kde` programs may only
  be run by root (mode 0700 through `dpkg-statoverride` in the postinst,
  so KDE package updates keep it; removed again in the postrm): users
  cannot reach KDE's settings window even from a terminal (product owner,
  2026-10-22). Symlinks among them are skipped: `kinfocenter.kde` is
  KDE's link to `systemsettings`, i.e. to the redirect, and a chmod
  through it had locked the redirect too (VM, 2026-10-23); the postinst
  also gives the redirect its mode 0755 back.
- Text boxes (search, `VTextField`) are in the Tab order and show the
  text (I-beam) pointer, like Windows' (product owner, 2026-10-22).
- English and Turkish. Search folds case, Turkish letters and punctuation
  ("hoparlor" finds "Hoparlör", "wifi" finds "Wi-Fi") and knows Windows
  words ("control panel", "notepad" style keywords).

`veltos-settings PAGE` opens a page directly (`about`, `storage`,
`signin`, a page id such as `system`, or a KDE module name such as
`kcm_users`).

## Layout

| Path | What |
|---|---|
| `veltos_settings/catalog.py` | Pages and items (EN/TR texts, icons, built-in page or action, search keywords), search, KDE module → page map |
| `veltos_settings/prefs.py` | Settings kept in KDE configuration files (read like KConfig, written with `kwriteconfig6 --notify`) |
| `veltos_settings/accounts.py` | Users through AccountsService (`gdbus`, `--interactive` where polkit may ask), login names made from typed names, password change through `passwd` |
| `veltos_settings/admin_calls.py` | Several AccountsService calls in one process (one password prompt for adding a user); `python3 -m veltos_settings.admin_calls`, calls as JSON on standard input |
| `veltos_settings/taskbar.py` | Personalization > Taskbar: reads and changes Plasma's taskbar through plasmashell's scripting interface |
| `veltos_settings/inputs.py` | Mouse and touchpad through KWin's input devices (D-Bus) |
| `veltos_settings/apps.py` | Default apps (mimeapps.list) and startup apps (autostart) |
| `veltos_settings/sysinfo.py` | Facts: OS, CPU, RAM, GPUs (`lspci -mm`), DMI model, PC name, drives, dark mode |
| `veltos_settings/strings.py` | Texts of the built-in pages |
| `veltos_settings/app.py` | Backend object for QML (texts, facts, actions) and `main()`; the Windows programs list (veltos-winapps' registry reader and `veltos-run`'s records) with the programs' icons and Uninstall |
| `veltos_settings/qml/` | Window (`Main.qml`), pages and components, `Theme` singleton (colours) |
| `bin/veltos-settings`, `data/veltos-settings.desktop` | Launcher ("Settings" / "Ayarlar") |

## Tests

`tests/test_catalog.py` (every item opens exactly one thing, never a KDE
module; no page names a KDE module; every built-in page has a component;
monochrome icons; texts in both languages without "Debian"/"KDE"; unique
ids; search), `tests/test_prefs.py` (KDE files, commands, accounts with a
fake `passwd`, login names made from typed names, existing names refused,
the `--interactive` AccountsService calls with their timeout, adding a
user through one `admin_calls` process with the hash on standard input,
`admin_calls` against a fake bus, input devices, default and startup apps,
the redirect and the postinst's modes in a sandbox), `tests/test_sysinfo.py` (parsing with
a fake file system, `lspci` output, drives, PC names, dark mode),
`tests/test_taskbar.py` (the taskbar state read from the script's JSON,
defaults when Plasma does not answer, changes turned into scripts, values
that are not settings never reaching Plasma, the page and its texts),
`tests/test_ui.py` (loads the real window offscreen in English and
Turkish, visits every page including Taskbar, fails on any QML warning,
checks that items start the right commands, the website included, and
the theme switch applies the global theme).

## Not done yet

- Not built in yet (left out rather than shown in KDE's window): VPN and
  wired network details, proxy, firewall, fonts and pointer style, per-app
  volume, display arrangement and refresh rate, game controllers, pen
  tablets, on-screen keyboard, spelling.
- Windows programs have no Modify / Repair entries; Uninstall runs the
  program's own uninstaller, whose window may still appear.
- No automatic update checks yet (VeltOS Update opens the Store).

## App icon and text

`data/veltos-settings.svg` is the Settings icon (VeltOS artwork in the style of
Windows 11 app icons, CC-BY-SA-4.0), installed as
`/usr/share/icons/hicolor/scalable/apps/veltos-settings.svg`. The window draws its
text like KDE programs (`NativeTextRendering`): Qt Quick's default
distance-field text looked uneven at fractional display scales. Qt objects
are configured with setters, never keyword arguments (PySide6 resolves those
with the C library's `toupper()`, which broke in a Turkish locale).
