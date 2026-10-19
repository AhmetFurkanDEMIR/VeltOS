# veltos-settings

**Settings** ("Ayarlar"): the everyday settings app of VeltOS, laid out like
Windows 11 Settings. Written from scratch in Python (PySide6) and QML; KDE's
complete System Settings stays available as **Control Panel** for advanced
options.

## What the user sees

- Navigation pane: account picture and name, "Find a setting" search box,
  Home, System, Bluetooth & devices, Network & internet, Personalization,
  Apps, Accounts, Time & language, Gaming, Accessibility, Privacy &
  security, VeltOS Update, and Control Panel at the bottom.
- Pages of cards (icon, title, description). A chevron means a page inside
  Settings; a "new window" mark means the setting opens in its own window.
- Built into Settings:
  - **Home**: this PC (name, model, VeltOS version, Rename), Light/Dark
    theme, recommended settings;
  - **Personalization**: Light/Dark theme with previews (applies the VeltOS
    Light/Dark global theme with `plasma-apply-lookandfeel`);
  - **System > About**: device name (rename through `hostnamectl`, which
    asks for the administrator password), model, processor, RAM, graphics,
    system type, VeltOS version and kernel, with "Copy" buttons;
  - **System > Storage**: used and free space per drive (the live system
    is labelled as running in memory);
  - **Apps > Windows programs**: programs installed from `.exe`/`.msi`
    files by `veltos-run`, with Open and "Uninstall a program" (Wine's
    uninstaller), and the note that Wine is not a security sandbox.
- Everything else opens the matching KDE settings module (`kcmshell6
  kcm_…`) in its own window: display, sound, notifications, power,
  Bluetooth, mouse, keyboard, network, date and time, language, users,
  accessibility, screen lock, firewall, …; "Check for updates" and "Get
  apps" open the Store (Discover).
- English and Turkish. Search folds case, Turkish letters and punctuation
  ("hoparlor" finds "Hoparlör", "wifi" finds "Wi-Fi") and knows Windows
  words ("control panel", "notepad" style keywords).

`veltos-settings PAGE` opens a page directly (`about`, `storage`,
`windows-apps`, or a page id such as `system`).

## Layout

| Path | What |
|---|---|
| `veltos_settings/catalog.py` | Pages and items (EN/TR texts, icons, KDE module or built-in page or action, search keywords), search |
| `veltos_settings/sysinfo.py` | Facts: OS, CPU, RAM, GPUs (`lspci -mm`), DMI model, PC name, drives, dark mode |
| `veltos_settings/strings.py` | Texts of the built-in pages |
| `veltos_settings/app.py` | Backend object for QML (texts, facts, actions) and `main()` |
| `veltos_settings/qml/` | Window (`Main.qml`), pages and components, `Theme` singleton (colours) |
| `bin/veltos-settings`, `data/veltos-settings.desktop` | Launcher ("Settings" / "Ayarlar") |

## Tests

`tests/test_catalog.py` (every item opens exactly one thing; every KDE
module named is installed in the image; texts in both languages without
"Debian"/"KDE"; unique ids; search), `tests/test_sysinfo.py` (parsing with
a fake file system, `lspci` output, drives, PC names, dark mode),
`tests/test_ui.py` (loads the real window offscreen in English and
Turkish, visits every page, fails on any QML warning, checks that items
start the right commands and the theme switch applies the global theme).

## Not done yet

- Most detailed settings are KDE's own pages in separate windows; they are
  styled like the rest of VeltOS but are not Windows-like in layout.
- Windows programs can only be uninstalled through Wine's own uninstaller
  window.
- No automatic update checks yet (VeltOS Update opens the Store).
