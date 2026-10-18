"""Start menu and desktop shortcuts for Windows programs.

Wine adds shortcuts created by installers to the Linux menus itself
(~/.local/share/applications/wine/...), so they appear in VeltOS Start like
any other app. This module finds the ones an installer just created, and
writes launchers for programs that need no installation.
"""

import configparser
import subprocess
from pathlib import Path

from .winenv import data_home, wine_tool


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


def quote_exec_arg(arg):
    """Quote one argument for a desktop entry Exec key (XDG spec)."""
    if arg and not any(c in arg for c in ' \t\n"\'\\><~|&;$*?#()`'):
        return arg
    escaped = arg.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return f'"{escaped}"'


def write_launcher(slug, name, exe_path, prefix, icon_png=b""):
    """Start menu entry for a program that runs without installation."""
    apps = data_home() / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    icon = "application-x-ms-dos-executable"
    if icon_png:
        icon_dir = data_home() / "icons/hicolor/256x256/apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        icon_file = icon_dir / f"veltos-win-{slug}.png"
        icon_file.write_bytes(icon_png)
        icon = str(icon_file)
    command = " ".join(quote_exec_arg(a) for a in [
        "env", f"WINEPREFIX={prefix}", wine_tool("wine"), "start", "/unix", str(exe_path)])
    path = apps / f"veltos-win-{slug}.desktop"
    path.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={name}\n"
        "Comment=Windows program\n"
        "Comment[tr]=Windows programı\n"
        f"Exec={command}\n"
        f"Icon={icon}\n"
        f"Path={Path(exe_path).parent}\n"
        "Categories=Wine;\n"
        "StartupNotify=true\n",
        encoding="utf-8")
    return path
