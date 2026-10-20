"""Start menu and desktop shortcuts for Windows programs.

Wine adds shortcuts created by installers to the Linux menus itself
(~/.local/share/applications/wine/...), so they appear in VeltOS Start like
any other app. This module finds the ones an installer just created.
"""

import configparser
import subprocess
from pathlib import Path

from .winenv import data_home


def desktop_dir():
    try:
        out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True,
                             timeout=5).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return Path.home() / "Desktop"


def watched_dirs():
    return [data_home() / "applications", desktop_dir()]


def snapshot(dirs=None):
    """{path: mtime} of every .desktop file below the given directories."""
    state = {}
    for directory in dirs or watched_dirs():
        if directory.is_dir():
            for path in directory.rglob("*.desktop"):
                try:
                    state[path] = path.stat().st_mtime
                except OSError:
                    pass
    return state


def changed(before, after):
    return sorted(p for p, mtime in after.items() if before.get(p) != mtime)


def read_entry(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
        entry = parser["Desktop Entry"]
    except (configparser.Error, KeyError, UnicodeDecodeError):
        return None
    return {"path": str(path), "name": entry.get("Name", Path(path).stem),
            "icon": entry.get("Icon", ""), "exec": entry.get("Exec", "")}


def entries_for_prefix(paths, prefix):
    """Shortcuts among `paths` that start a program in the given Wine prefix."""
    found, seen = [], set()
    for path in paths:
        entry = read_entry(path)
        if entry and str(prefix) in entry["exec"] and entry["name"] not in seen:
            seen.add(entry["name"])
            found.append(entry)
    return found
