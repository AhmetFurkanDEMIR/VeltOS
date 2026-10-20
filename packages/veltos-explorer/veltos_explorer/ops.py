"""File operations of VeltOS File Explorer.

Copying, moving, deleting and opening go through KDE's file engine (KIO)
with `kioclient`: it shows progress in the notification area, asks what to
do when a file already exists, and moves to the Recycle Bin (trash:/) the
freedesktop.org way. VeltOS does not reimplement any of that. Renaming and
creating new items are single local calls done here.
"""

import os
import subprocess
from pathlib import Path

from . import files, places


def detached(command, cwd=None):
    """Start a program that outlives File Explorer, without output."""
    subprocess.Popen(command, cwd=cwd, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Operations:
    """Each method starts the work and returns at once (KIO shows progress);
    `start` can be replaced in tests."""

    def __init__(self, start=detached):
        self.start = start

    def copy(self, sources, destination):
        """Copy into a folder. A copy into the same folder gets Windows'
        "name - Copy" name instead of a conflict question."""
        destination = str(destination)
        same = [s for s in sources if str(Path(s).parent) == destination]
        other = [s for s in sources if s not in same]
        if other:
            self.start(["kioclient", "--interactive", "copy", *other, destination + "/"])
        for source in same:
            target = Path(destination) / files.copy_name(destination, Path(source).name,
                                                         Path(source).is_dir())
            self.start(["kioclient", "--interactive", "copy", source, str(target)])

    def move(self, sources, destination):
        destination = str(destination)
        sources = [s for s in sources if str(Path(s).parent) != destination
                   and not destination.startswith(s.rstrip("/") + "/") and s != destination]
        if sources:
            self.start(["kioclient", "--interactive", "move", *sources, destination + "/"])

    def trash(self, sources):
        """Move to the Recycle Bin (can be restored)."""
        if sources:
            self.start(["kioclient", "--interactive", "move", *sources, "trash:/"])

    def delete(self, sources):
        """Delete for good (the caller asks first)."""
        if sources:
            self.start(["kioclient", "--interactive", "remove", *sources])

    def empty_trash(self):
        self.start(["kioclient", "--interactive", "remove", "trash:/"])

    def open(self, path):
        """Open with the default app (folders are handled by the caller)."""
        self.start(["kioclient", "exec", str(path)])

    def open_with(self, desktop_path, paths):
        command = places.exec_command(desktop_path, [str(p) for p in paths])
        if command:
            self.start(command)

    def properties(self, path):
        self.start(["kioclient", "openProperties", str(path)])

    def terminal(self, folder):
        # Opaque window: see update-app-names (veltos-desktop).
        self.start(["konsole", "--notransparency", "--workdir", str(folder)], cwd=str(folder))

    def compress(self, sources, folder):
        """Make a .zip of the items (Ark, in batch mode)."""
        if not sources:
            return ""
        base = Path(sources[0]).stem if len(sources) == 1 else Path(folder).name or "Archive"
        name = files.unique_name(folder, base + ".zip")
        self.start(["ark", "--batch", "--add-to", str(Path(folder) / name), *sources])
        return name

    def extract(self, archive, folder):
        """Extract all into a folder named like the archive (Ark)."""
        self.start(["ark", "--batch", "--autosubfolder", "--destination", str(folder), str(archive)])

    @staticmethod
    def new_folder(folder, name):
        name = files.unique_name(folder, name, is_dir=True)
        os.mkdir(Path(folder) / name)
        return name

    @staticmethod
    def new_file(folder, name):
        name = files.unique_name(folder, name)
        with open(Path(folder) / name, "x", encoding="utf-8"):
            pass
        return name

    @staticmethod
    def rename(path, new_name):
        """Rename in place. Returns "" or the reason it was refused
        ("empty", "invalid", "exists", or the system's error text). Never
        replaces another item (os.rename would, silently)."""
        path = Path(path)
        reason = files.check_new_name(path.parent, path.name, new_name)
        if reason:
            return reason
        new_name = new_name.strip()
        if new_name == path.name:
            return ""
        target = path.parent / new_name
        try:
            if target.exists() and new_name.casefold() == path.name.casefold():
                # Only the case changes (a.txt -> A.txt) on a case-insensitive drive.
                temporary = path.parent / files.unique_name(path.parent, "." + new_name + ".renaming")
                os.rename(path, temporary)
                os.rename(temporary, target)
            else:
                os.rename(path, target)
        except OSError as error:
            return error.strerror or str(error)
        return ""
