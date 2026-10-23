# veltos-winapps

Added 2026-10-21: when Bottles, Lutris or PlayOnLinux are installed (none
is in Debian 13; they are found by their desktop entries, Flatpak's
included), the runner first asks "How do you want to open X?" with
VeltOS' own environment recommended; the Done page scrolls its list of
new programs; the runner has its own App Installer icon (`veltos-run`);
Windows programs are told the VeltOS light/dark mode at every start
(`AppsUseLightTheme`; Wine 10's Light theme has no dark variant, so
Wine's own controls stay light).

Opens Windows programs on VeltOS with a double click.

## User experience

1. The user double-clicks `setup.exe` (or any `.exe`/`.msi`, or a
   `.bat`/`.cmd` batch file) in File Explorer, Firefox's downloads or on
   the desktop.
2. **`veltos-run`** starts it at once, as Windows does — no question
   first. Its window, in the layout of the Windows 11 App Installer, shows
   what is happening ("Installing X", "Starting X…") with the
   **publisher, version and 32/64-bit** read from the file itself, the
   program's **icon** on the right, a thin progress bar and an information
   bar saying that Windows programs can access personal files. For
   programs that need no installation and batch files the window goes away
   once the program runs.
3. First time only: "Setting up Windows compatibility…" while a private
   Windows environment is created.
4. The program's own installer runs as on Windows. A batch file runs in
   cmd in its own console window (Wine's `start`, like a double click in Windows).
5. "X is installed — you can find it in Start", with "Open" buttons for the
   shortcuts the installer created. Those shortcuts appear in VeltOS Start
   (Wine creates standard desktop entries).
6. On failure: a plain-language message, the exit code and "Show details"
   (log file).

English and Turkish texts (`veltos_winapps/strings.py`).

## How it works

| Module | Role |
|---|---|
| `exeinfo.py` | Reads PE headers/resources (python3-pefile): name, publisher, version, icon, architecture, .NET, GUI/console; detects installers (Inno Setup, NSIS, InstallShield, WiX, MSI, …) by signature, version info and file name |
| `winenv.py` | One Windows environment (Wine prefix) shared by all programs, like the single C: drive of a Windows PC: `~/.local/share/veltos/windows/` (the prefix in `prefix/`, records of installed programs in `records/`, logs in `logs/`); a prefix per program was tried first and cost ~1.7 GB each. 64-bit prefix with 32-bit support; DXVK installed via `dxvk-setup` when a real Vulkan GPU is present |
| `shortcuts.py` | Finds the Start menu entries an installer created (only those for its prefix) |
| `programs.py` | The installed Windows programs as Windows 11's Settings > Apps > Installed apps lists them, read from the environment's registry files (`prefix/system.reg`, `prefix/user.reg`: the `Uninstall` keys and their `Wow6432Node` twin): name, publisher, version, size, install date and the icon's `.exe`, newest first; Wine's own parts (Wine Mono, Wine Gecko), system components and updates are left out. Reading the files takes milliseconds; Wine's own "Add/Remove Programs" window took many seconds (product owner, 2026-10-22). `uninstall_command` runs the program's own uninstaller through Wine (`wine uninstaller --remove KEY`) and waits until every Windows process has ended (`wineserver -w`). Used by VeltOS Settings > Apps > Windows programs (veltos-settings) |
| `app.py` + `qml/` | PySide6 + Qt Quick window (`Main.qml`; Windows 11 button `VButton`; colours in `Theme.qml`, light/dark and accent from the KDE settings); runs each step with QProcess, logs to `logs/` |
| `strings.py` | UI texts |

Installed files: Python package in `/usr/lib/python3/dist-packages/`,
`/usr/bin/veltos-run`, `/usr/share/applications/veltos-run.desktop`
(handler for the `.exe`/`.msi` and batch file MIME types),
`/etc/xdg/mimeapps.list` (makes it the default handler) and
`/usr/share/mime/packages/veltos-winapps.xml` (`*.cmd` is a batch file
too; shared-mime-info 2.4 knows only `*.bat`).

Wine Mono and Gecko come from `veltos-wine-addons`, so creating an
environment needs no download.

`/usr/libexec/veltos/strip-wine-dlls` removes the debug information from
Wine's own Windows DLLs (`/usr/lib/*/wine/*-windows/`) with MinGW's strip:
Debian builds them with DWARF debug information, which was 1.3 GB of the
2.0 GB Wine installs and 235 MB of the compressed ISO (2026-10-23). It runs
from the postinst and, through a dpkg trigger on those folders, whenever
Wine is installed or updated. The code is unchanged and Wine still loads
them as its builtin DLLs (their "Wine builtin DLL" mark stays; the ISO's
verify hook checks both); only debuggers lose Wine's symbols, and
`dpkg --verify` lists the files as changed.

## Limits (honest list)

- Not every Windows program works. Wine covers a large share of desktop
  software, but programs with kernel drivers, some DRM/anti-cheat, and
  some recent Microsoft/Adobe products fail or misbehave.
- Wine is **not a security sandbox**: Windows programs and batch files
  run as the user and can read and change the user's files. The window
  says so while it prepares and starts the program (the product owner
  asked for no question before a program starts, like Windows).
- Bottles (a second engine was asked for) is not in Debian 13; only Wine
  from Debian is used.
- Installed Windows programs are listed and uninstalled in VeltOS
  Settings > Apps > Windows programs (`programs.py`, laid out like
  Windows 11's Installed apps); there is no separate manager window.
- Not yet: per-program compatibility profiles, automatic runtime
  installation (winetricks verbs) and a compatibility database. See
  `docs/dev/status.md`.

## Tests

`tests/test_winapps.py` (package build, no Wine needed): PE inspection on
generated PE files, installer detection, environment naming and
variables, shortcut detection, the installed-programs list read from a
registry file (`tests/data/system.reg`: names with escapes, publisher,
date, size, icon, newest first; Wine's own entries, updates and system
components left out) and the uninstall command, translation
completeness, and `strip-wine-dlls` with a stand-in strip tool (only
Windows programs and libraries, nothing without the tool, the trigger).
End-to-end in a VM: `build/run.sh test-winapps` (installs 7-Zip through
the runner; fixture pinned in `tests/boot/winapps-fixtures.json`).
