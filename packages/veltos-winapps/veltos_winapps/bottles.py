"""Bottles as the way to open Windows programs (product owner, 2026-10-27:
"the user chooses Wine or Bottles during installation; a proper Bottles
set-up for opening Windows programs"; Bottles from Flathub approved by the
product owner the same day, as an exception to Debian-only sources).

- The choice: `runner=wine|bottles` in ~/.config/veltos/windows-apps.conf
  (Settings) or /etc/veltos/windows-apps.conf (the installer). No file: the
  runner asks when Bottles is installed, as before.
- Bottles is Flathub's com.usebottles.bottles (not in Debian 13). The first
  start installs it system-wide when the installer's choice was Bottles
  (veltos-store's firstupdate.py, `install_commands("--system")`);
  Settings installs it for the user (`--user`, no administrator rights).
- At sign-in `veltos-run --bottles-setup` prepares a bottle named "VeltOS"
  (Bottles' "Application" environment) once Bottles is there: Bottles
  downloads its own Wine (Soda) and DXVK for it, about 1.5 GB (seen in the
  dev VM, 2026-10-27).
- veltos-run runs a Windows program straight in the VeltOS bottle
  (`bottles-cli run -b VeltOS -e FILE` with flatpak's --file-forwarding:
  the file reaches the sandbox through the document portal; Bottles has no
  access to the home folder). Handing the file to Bottles' window instead
  asked "Select Bottle" for every program (installed dev VM, 2026-10-31).

Flatpak's sandbox does not make Windows programs safe: Bottles runs them
with Wine like VeltOS does.
"""

import configparser
import os
import shutil
import subprocess
import time
from pathlib import Path

APP_ID = "com.usebottles.bottles"
FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"
BOTTLE = "VeltOS"
SYSTEM_CONF = Path("/etc/veltos/windows-apps.conf")
DESKTOPS = [Path("/var/lib/flatpak/exports/share/applications") / f"{APP_ID}.desktop"]
SETUP_WAIT = 2 * 3600          # sign-in: wait this long for the first start to install Bottles


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def user_conf():
    return config_home() / "veltos" / "windows-apps.conf"


def read_runner(path):
    parser = configparser.RawConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return ""
    value = parser.get("Windows programs", "runner", fallback="").strip().lower()
    return value if value in ("wine", "bottles") else ""


def preference(user=None, system=None):
    """"wine", "bottles" or "" (not chosen: ask when Bottles is there)."""
    return read_runner(user or user_conf()) or read_runner(system or SYSTEM_CONF)


def set_preference(runner, user=None):
    path = Path(user or user_conf())
    if runner not in ("wine", "bottles"):
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"[Windows programs]\nrunner={runner}\n", encoding="utf-8")
        return True
    except OSError:
        return False


def desktop_file(user_data=None):
    """Bottles' desktop entry (system or user Flatpak install), or None."""
    for path in [*DESKTOPS, Path(user_data or data_home()) / f"flatpak/exports/share/applications/{APP_ID}.desktop"]:
        if path.is_file():
            return path
    return None


def installed(user_data=None):
    return desktop_file(user_data) is not None


def install_commands(scope="--user"):
    """The commands that install Bottles from Flathub (scope --user or --system)."""
    return [["flatpak", "remote-add", scope, "--if-not-exists", "flathub", FLATHUB],
            ["flatpak", "install", scope, "-y", "--noninteractive", "flathub", APP_ID]]


def bottle_dir(user_home=None):
    home = Path(user_home or Path.home())
    return home / ".var/app" / APP_ID / "data/bottles/bottles" / BOTTLE


def ready(user_data=None, user_home=None):
    """Bottles installed and the VeltOS bottle made. Bottles handed a file
    before it has any bottle stays running without a window ("No such file
    or directory: .../data/bottles/bottles", VM 2026-10-27), so until then
    VeltOS opens Windows programs itself."""
    return installed(user_data) and bottle_dir(user_home).is_dir()


def setup_command():
    return ["flatpak", "run", "--command=bottles-cli", APP_ID, "new", "--bottle-name", BOTTLE,
            "--environment", "application"]


def open_command(path, user_data=None):
    """Runs a Windows program in the VeltOS bottle, without Bottles'
    "Select Bottle" question; [] when Bottles is not installed."""
    if not desktop_file(user_data):
        return []
    # "@@ FILE @@": flatpak hands the file in through the document portal
    # (/run/user/UID/doc/...), so it may be anywhere in the home folder.
    return ["flatpak", "run", "--file-forwarding", "--command=bottles-cli", APP_ID,
            "run", "-b", BOTTLE, "-e", "@@", str(path), "@@"]


def setup(runner=subprocess.run, wait=time.sleep, deadline=None, first_update_done=Path("/var/lib/veltos/first-update-done"),
          log=None):
    """At sign-in: when the choice is Bottles, waits for Bottles (the first
    start installs it) and makes the VeltOS bottle once. True when there is
    nothing (more) to do."""
    if preference() != "bottles" or bottle_dir().is_dir():
        return True
    if not shutil.which("flatpak"):
        return False
    end = deadline if deadline is not None else time.monotonic() + SETUP_WAIT
    while not installed():
        # The first start may still be installing Bottles; after it, give up.
        if first_update_done.exists() and not installed():
            return False
        if time.monotonic() > end:
            return False
        wait(30)
    try:
        result = runner(setup_command(), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3 * 3600)
    except (OSError, subprocess.SubprocessError) as error:
        if log:
            log.write(f"bottles-cli: {error}\n")
        return False
    if log:
        log.write((result.stdout or "")[-4000:] + (result.stderr or "")[-4000:])
    return result.returncode == 0 and bottle_dir().is_dir()
