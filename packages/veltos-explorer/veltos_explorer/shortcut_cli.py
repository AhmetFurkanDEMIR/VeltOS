"""Create a desktop shortcut for a local file or folder without opening Explorer."""

import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import ops, strings


def application_file(desktop_id, environ=None):
    """The file of an installed app's desktop id ("veltos-calculator.desktop"),
    looked up as menus do: XDG_DATA_HOME first, then XDG_DATA_DIRS."""
    import os
    environ = os.environ if environ is None else environ
    home = environ.get("XDG_DATA_HOME") or str(Path(environ.get("HOME", str(Path.home()))) / ".local/share")
    dirs = [home] + [d for d in (environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]
    for directory in dirs:
        candidate = Path(directory) / "applications" / desktop_id
        if candidate.is_file():
            return candidate
    return None


def source_path(argument):
    # Start's app entries pass their desktop id: a shortcut to the app, as
    # Windows makes from Start (2026-11-08; Plasma's "Add to Desktop" put a
    # widget on the desktop instead).
    if "/" not in argument and argument.endswith(".desktop") and not Path(argument).exists():
        found = application_file(argument)
        if found is None:
            raise ValueError(f"No app {argument}")
        return found
    parsed = urlsplit(argument)
    if parsed.scheme:
        if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
            raise ValueError("Only local files and folders can have desktop shortcuts.")
        argument = unquote(parsed.path)
    return Path(argument).expanduser()


def desktop_directory():
    result = subprocess.run(
        ["xdg-user-dir", "DESKTOP"], capture_output=True, check=True, text=True, timeout=5)
    directory = result.stdout.strip()
    if not directory:
        raise OSError("xdg-user-dir returned an empty Desktop path")
    path = Path(directory).expanduser()
    if not path.is_absolute():
        raise OSError(f"xdg-user-dir returned a non-absolute Desktop path: {directory}")
    return path


def notify(title, body, error=False):
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
    except (ImportError, ValueError) as exc:
        print(f"Could not show shortcut notification: {exc}", file=sys.stderr)
        return

    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        connection.call_sync(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            "Notify",
            GLib.Variant("(susssasa{sv}i)", (
                "File Explorer", 0, "dialog-error" if error else "edit-copy",
                title, body, [], {}, 5000)),
            Gio.DBusCallFlags.NONE,
            3000,
            None,
        )
    except GLib.Error as exc:
        print(f"Could not show shortcut notification: {exc.message}", file=sys.stderr)


def run(argv, desktop=None, notifier=None):
    arguments = [argument for argument in argv[1:] if argument != "--create-shortcut"]
    if len(arguments) != 1:
        print("Usage: veltos-explorer --create-shortcut FILE_OR_FOLDER", file=sys.stderr)
        return 2

    notify_user = notifier or notify
    try:
        source = source_path(arguments[0])
        desktop = Path(desktop) if desktop is not None else desktop_directory()
        target = ops.Operations.create_shortcut(source, desktop)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        message = strings.text(strings.language(), "shortcut_unavailable")
        notify_user("File Explorer", f"{message}\n{exc}", True)
        print(f"Could not create a desktop shortcut: {exc}", file=sys.stderr)
        return 1

    notify_user("File Explorer", strings.text(strings.language(), "shortcut_created"))
    print(target)
    return 0
