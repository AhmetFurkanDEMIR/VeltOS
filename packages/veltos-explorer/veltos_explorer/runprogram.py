"""Starting a launcher (.desktop) or a Linux program from File Explorer
without KIO (`veltos-explorer --run PATH`).

`kioclient exec` asked about untrusted launchers in KDE's "Warning — KIO
Client" window with the Wayland "W" icon (VM, 2026-10-31). VeltOS follows
KDE's trust rule and asks Windows 11's question instead: a launcher in an
applications or autostart folder, or one marked executable (File Explorer's
and the desktop's shortcuts are), starts at once; one that came from
elsewhere (a download) and a Linux program outside the system's program
folders get "Open File - Security Warning" first (app.py). No Qt here.
"""

import configparser
import os
import subprocess
from pathlib import Path

SYSTEM_PROGRAMS = ("/usr/bin/", "/usr/sbin/", "/bin/", "/sbin/", "/usr/local/bin/", "/usr/games/",
                   "/usr/lib/", "/usr/libexec/", "/opt/")


def data_dirs():
    home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    system = [Path(p) for p in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if p]
    return [home, *system]


def config_dirs():
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    system = [Path(p) for p in (os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":") if p]
    return [home, *system]


def is_launcher(path):
    return str(path).lower().endswith(".desktop")


def trusted(path):
    """KDE's rule (KDesktopFile::isAuthorizedDesktopFile and KIO's
    executable check): launchers in an applications or autostart folder or
    marked executable; programs in the system's program folders."""
    path = os.path.realpath(path)
    if is_launcher(path):
        folders = [d / "applications" for d in data_dirs()] + [d / "autostart" for d in config_dirs()]
        for folder in folders:
            folder = os.path.realpath(folder) + os.sep
            if path.startswith(folder):
                return True
        return os.access(path, os.X_OK)
    return path.startswith(SYSTEM_PROGRAMS)


def entry(path):
    """[Desktop Entry] of a launcher as a dict ({} when unreadable)."""
    parser = configparser.RawConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return {}
    return dict(parser["Desktop Entry"]) if parser.has_section("Desktop Entry") else {}


def display_name(path, lang="en"):
    if is_launcher(path):
        values = entry(path)
        name = values.get(f"Name[{lang}]") or values.get("Name")
        if name:
            return name
    return os.path.basename(path)


def command(path):
    """(command, cwd, url): how to start it; url for a link launcher."""
    path = str(path)
    if is_launcher(path):
        values = entry(path)
        if values.get("Type") == "Link" and values.get("URL"):
            return None, None, values["URL"]
        # GLib starts the entry as Plasma would (Exec, field codes, Path,
        # Terminal); it shows no window of its own.
        return ["gio", "launch", path], None, None
    return [path], os.path.dirname(path) or None, None


def start(path, open_url=None):
    """Start it detached; False when it could not be started."""
    cmd, cwd, url = command(path)
    if url:
        if open_url is not None:
            return bool(open_url(url))
        cmd = ["xdg-open", url]
    try:
        subprocess.Popen(cmd, cwd=cwd, start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True
