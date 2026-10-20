# veltos-winapps

Opens Windows programs on VeltOS with a double click.

## User experience

1. The user double-clicks `setup.exe` (or any `.exe`/`.msi`, or a
   `.bat`/`.cmd` batch file) in File Explorer, Firefox's downloads or on
   the desktop.
2. **`veltos-run`** shows a window in the layout of the Windows 11 App
   Installer: the question on the left — "Install X?" (installers), "Open
   X?" (programs that need no installation, with an "Add to Start" check
   box) or "Run X.bat?" (batch files) — with the **publisher, version and
   32/64-bit** read from the file itself, the program's **icon** on the
   right, an information bar saying that Windows programs can access
   personal files, and the action button at the bottom right.
3. First time only: "Setting up Windows compatibility…" while a private
   Windows environment is created.
4. The program's own installer runs as on Windows (a thin progress bar
   runs in the window meanwhile). A batch file runs in cmd in its own
   console window (Wine's `start`, like a double click in Windows).
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
| `winenv.py` | Wine prefixes under `~/.local/share/veltos/windows-apps/<program>/` (one per installed program, `shared/` for portable ones); 64-bit prefixes with 32-bit support; DXVK installed via `dxvk-setup` when a real Vulkan GPU is present |
| `shortcuts.py` | Finds the Start menu entries an installer created (only those for its prefix); writes launchers for portable programs |
| `app.py` + `qml/` | PySide6 + Qt Quick window (`Main.qml`; Windows 11 controls `VButton`, `VCheckBox`; colours in `Theme.qml`, light/dark and accent from the KDE settings); runs each step with QProcess, logs to `logs/` |
| `strings.py` | UI texts |

Installed files: Python package in `/usr/lib/python3/dist-packages/`,
`/usr/bin/veltos-run`, `/usr/share/applications/veltos-run.desktop`
(handler for the `.exe`/`.msi` and batch file MIME types),
`/etc/xdg/mimeapps.list` (makes it the default handler) and
`/usr/share/mime/packages/veltos-winapps.xml` (`*.cmd` is a batch file
too; shared-mime-info 2.4 knows only `*.bat`).

Wine Mono and Gecko come from `veltos-wine-addons`, so creating an
environment needs no download.

## Limits (honest list)

- Not every Windows program works. Wine covers a large share of desktop
  software, but programs with kernel drivers, some DRM/anti-cheat, and
  some recent Microsoft/Adobe products fail or misbehave.
- Wine is **not a security sandbox**: Windows programs and batch files
  run as the user and can read and change the user's files. The window
  says so before anything runs.
- Bottles (a second engine was asked for) is not in Debian 13; only Wine
  from Debian is used.
- Not yet: per-program compatibility profiles, automatic runtime
  installation (winetricks verbs), an "Installed Windows programs" manager
  with uninstall, and a compatibility database. See `docs/status.md`.

## Tests

`tests/test_winapps.py` (package build, no Wine needed): PE inspection on
generated PE files, installer detection, environment naming and
variables, shortcut detection/quoting, translation completeness.
End-to-end in a VM: `build/run.sh test-winapps` (installs 7-Zip through
the runner; fixture pinned in `tests/boot/winapps-fixtures.json`).
