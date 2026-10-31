"""Moving items to the Recycle Bin and deleting them for good, without KDE's
windows.

File Explorer used `kioclient` for both; KIO then asked its questions and
reported its errors in windows of its own ("Warning — KIO Client"), with
the Wayland "W" icon on the taskbar (VM 2026-10-31; product owner: every
such window becomes VeltOS' Windows 11 one). VeltOS moves items to the
Recycle Bin with GLib's `gio trash` (the freedesktop.org trash KDE uses
too: ~/.local/share/Trash, or the drive's own .Trash-UID folder), deletes
with Python, and asks and reports in its own windows (app.py `--recycle`,
`--remove`). No Qt here.
"""

import os
import shutil
import subprocess
from pathlib import Path


def trash(paths, run=subprocess.run):
    """Move the items to the Recycle Bin; returns the ones that could not go
    there (a read-only drive, one without room for a trash folder)."""
    failed = []
    for path in paths:
        try:
            result = run(["gio", "trash", "--", str(path)], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
            ok = result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            ok = False
        if not ok and os.path.lexists(path):
            failed.append(str(path))
    return failed


def remove(paths):
    """Delete the items for good; returns [(path, reason)] for the ones (or
    the parts of folders) that stayed."""
    problems = []

    def failed(_function, path, error):
        error = error[1] if isinstance(error, tuple) else error
        problems.append((str(path), getattr(error, "strerror", None) or str(error)))

    for path in paths:
        path = str(path)
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path, onexc=failed)
            else:
                os.remove(path)
        except FileNotFoundError:
            continue
        except OSError as error:
            problems.append((path, error.strerror or str(error)))
        forget_trash_info(path)
    return problems


def trash_info(path):
    """The .trashinfo file of an item in a Recycle Bin folder (TRASH/files/NAME
    -> TRASH/info/NAME.trashinfo), or None for anything else."""
    path = Path(path)
    files_dir = path.parent
    if files_dir.name != "files":
        return None
    info = files_dir.parent / "info" / (path.name + ".trashinfo")
    return info if info.parent.is_dir() else None


def forget_trash_info(path):
    """An item that left a Recycle Bin (moved out or deleted) takes its
    .trashinfo with it, as KIO's trash did; a plain move left it behind."""
    if os.path.lexists(path):
        return
    info = trash_info(path)
    if info is not None:
        try:
            info.unlink()
        except OSError:
            pass
