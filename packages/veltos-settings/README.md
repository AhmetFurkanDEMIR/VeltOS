# veltos-settings

**Settings** ("Ayarlar"): the everyday settings app of VeltOS, laid out like
Windows 11 Settings. Written from scratch in Python (PySide6) and QML. KDE's
settings windows are never shown (product owner's rule): every page is
built in, and `systemsettings` / `kcmshell6` / `kinfocenter` open VeltOS Settings.

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
    `plasma-apply-colorscheme` does not), with the current theme's
    background/colour/sounds/cursor and "Custom" for own mixes; Background
    lists the installed wallpapers (VeltOS's first, KDE's "Next" left out);
  - **Bluetooth > Add a device**: VeltOS' own dialog (scan with
    `bluetoothctl`, pair, trust, connect; Plasma's Bluetooth agent asks for
    PINs), instead of KDE's Bluetooth wizard;
  - **System > About**: device name (rename through `hostnamectl`, which
    asks for the administrator password), model, processor, RAM, graphics,
    system type, VeltOS version and kernel, with "Copy" buttons;
  - **System > Storage**: used and free space per drive (the live system
    is labelled as running in memory);
  - **Apps > Windows programs**: programs installed from `.exe`/`.msi`
    files by `veltos-run`, with Open and "Uninstall a program" (Wine's
    uninstaller), and the note that Wine is not a security sandbox.
  - **System**: Display, Sound, Notifications (do not disturb, sounds,
    banners per app: plasmanotifyrc), Power & battery (screen off, sleep,
    power button, lid: powerdevilrc + PowerDevil reload), Night light
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
    VeltOS' own prompt, package veltos-auth);
  - **Accessibility > Text size** scales the KDE fonts and, through the
    `textScale` every VeltOS app reads from them, the apps' own texts
    (Settings at once, the others at their next start);
  - **Time & language**: Date & time (also setting it by hand), Language &
    region (plasma-localerc; applies after signing in again);
  - **Accessibility**: Text size (KDE fonts), Animation effects;
  - **Privacy & security**: Screen lock, Searching files (balooctl6).
- "Check for updates" and "Get apps" open VeltOS Store.
- `bin/veltos-settings-redirect`, installed as `/usr/bin/systemsettings`,
  `/usr/bin/kcmshell6` and `/usr/bin/kinfocenter` (KDE's programs are
  diverted to `*.kde` by the preinst), maps KDE module names to pages
  (`catalog.KCM_PAGES`, every module VeltOS' KDE packages install), so KDE
  programs' "Configure…" links, the Start menu and KRunner open VeltOS
  Settings; KDE Info Center opens About.
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
| `veltos_settings/accounts.py` | Users through AccountsService (`gdbus`), password change through `passwd` |
| `veltos_settings/inputs.py` | Mouse and touchpad through KWin's input devices (D-Bus) |
| `veltos_settings/apps.py` | Default apps (mimeapps.list) and startup apps (autostart) |
| `veltos_settings/sysinfo.py` | Facts: OS, CPU, RAM, GPUs (`lspci -mm`), DMI model, PC name, drives, dark mode |
| `veltos_settings/strings.py` | Texts of the built-in pages |
| `veltos_settings/app.py` | Backend object for QML (texts, facts, actions) and `main()` |
| `veltos_settings/qml/` | Window (`Main.qml`), pages and components, `Theme` singleton (colours) |
| `bin/veltos-settings`, `data/veltos-settings.desktop` | Launcher ("Settings" / "Ayarlar") |

## Tests

`tests/test_catalog.py` (every item opens exactly one thing, never a KDE
module; no page names a KDE module; every built-in page has a component;
monochrome icons; texts in both languages without "Debian"/"KDE"; unique
ids; search), `tests/test_prefs.py` (KDE files, commands, accounts with a
fake `passwd`, input devices, default and startup apps, the redirect), `tests/test_sysinfo.py` (parsing with
a fake file system, `lspci` output, drives, PC names, dark mode),
`tests/test_ui.py` (loads the real window offscreen in English and
Turkish, visits every page, fails on any QML warning, checks that items
start the right commands and the theme switch applies the global theme).

## Not done yet

- Not built in yet (left out rather than shown in KDE's window): VPN and
  wired network details, proxy, firewall, fonts and pointer style, per-app
  volume, display arrangement and refresh rate, game controllers, pen
  tablets, on-screen keyboard, spelling.
- Administrator password prompts (adding users, time zone, PC name) still
  come from KDE's polkit agent window.
- Windows programs can only be uninstalled through Wine's own uninstaller
  window.
- No automatic update checks yet (VeltOS Update opens the Store).

## App icon and text

`data/veltos-settings.svg` is the Settings icon (VeltOS artwork in the style of
Windows 11 app icons, CC-BY-SA-4.0), installed as
`/usr/share/icons/hicolor/scalable/apps/veltos-settings.svg`. The window draws its
text like KDE programs (`NativeTextRendering`): Qt Quick's default
distance-field text looked uneven at fractional display scales. Qt objects
are configured with setters, never keyword arguments (PySide6 resolves those
with the C library's `toupper()`, which broke in a Turkish locale).
