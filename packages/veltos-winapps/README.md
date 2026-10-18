# veltos-winapps

Opens Windows programs on VeltOS with a double click.

## User experience

1. The user double-clicks `setup.exe` (or any `.exe`/`.msi`) in Dolphin,
   Firefox's downloads or on the desktop.
2. **`veltos-run`** shows a small dialog with the program's **name,
   publisher, icon, 32/64-bit** (read from the file itself) and asks
   "Install X on VeltOS?" (installers) or "Open X?" (programs that need no
   installation, with an "Add to Start" option). A note says Windows
   programs can access personal files.
3. First time only: "Setting up Windows compatibility…" while a private
   Windows environment is created.
4. The program's own installer runs as on Windows.
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
| `app.py` + `qml/Main.qml` | PySide6 + Qt Quick (Kirigami) dialog; runs each step with QProcess, logs to `<program>/logs/` |
| `strings.py` | UI texts |

Installed files: Python package in `/usr/lib/python3/dist-packages/`,
`/usr/bin/veltos-run`, `/usr/share/applications/veltos-run.desktop`
(handler for `.exe`/`.msi` MIME types) and `/etc/xdg/mimeapps.list`
(makes it the default handler).

Wine Mono and Gecko come from `veltos-wine-addons`, so creating an
environment needs no download.

## Limits (honest list)

- Not every Windows program works. Wine covers a large share of desktop
  software, but programs with kernel drivers, some DRM/anti-cheat, and
  some recent Microsoft/Adobe products fail or misbehave.
- Wine is **not a security sandbox**: Windows programs run as the user and
  can read the user's files. The dialog says so.
- Not yet: per-program compatibility profiles, automatic runtime
  installation (winetricks verbs), an "Installed Windows programs" manager
  with uninstall, and a compatibility database. See `docs/status.md`.

## Tests

`tests/test_winapps.py` (package build, no Wine needed): PE inspection on
generated PE files, installer detection, environment naming and
variables, shortcut detection/quoting, translation completeness.
End-to-end in a VM: `build/run.sh test-winapps` (installs 7-Zip through
the runner; fixture pinned in `tests/boot/winapps-fixtures.json`).
