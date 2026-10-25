"""File operations of VeltOS File Explorer.

Copying, moving, deleting and opening go through KDE's file engine (KIO)
with `kioclient`: it shows progress in the notification area, asks what to
do when a file already exists, and moves to the Recycle Bin (trash:/) the
freedesktop.org way. VeltOS does not reimplement any of that. Renaming and
creating new items are single local calls done here.
"""

import os
import subprocess
import sys
from pathlib import Path

from . import files, places


def trash_url(path, trash=None):
    """KIO's address of an item in the home Recycle Bin (trash:/0-NAME), or
    the path itself for anything else."""
    files_dir = Path(trash or places.trash_dir()) / "files"
    try:
        relative = Path(path).relative_to(files_dir)
    except ValueError:
        return str(path)
    return "trash:/0-" + str(relative)


def detached(command, cwd=None):
    """Start a program that outlives File Explorer, without output."""
    subprocess.Popen(command, cwd=cwd, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Started with KIO (`kioclient exec`): launchers and Windows programs. The
# desktop portal opens documents only; it does not run programs.
LAUNCHERS = (".desktop", ".exe", ".msi", ".bat", ".cmd", ".com")


def is_program(path):
    """A launcher, a Windows program, or a script or Linux program that may
    run (execute bit and a #! line or ELF header)."""
    path = str(path)
    if path.lower().endswith(LAUNCHERS):
        return True
    if not os.access(path, os.X_OK):
        return False
    try:
        with open(path, "rb") as handle:
            head = handle.read(4)
    except OSError:
        return False
    return head == b"\x7fELF" or head.startswith(b"#!")


def portal_open(path):
    """Open a document with its default app through Qt, which asks the
    desktop portal with an activation token: an app that is already open
    (Firefox, VeltOS Notepad) comes to the front with the file. kioclient
    has no window and so no token; such apps stayed behind (VM 2026-10-25)."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


class Operations:
    """Each method starts the work and returns at once (KIO shows progress);
    `start` can be replaced in tests."""

    def __init__(self, start=detached, open_document=portal_open):
        self.start = start
        self.open_document = open_document

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
            # Items cut in the Recycle Bin leave it through KIO's trash, which
            # also drops their .trashinfo (a plain move left it behind).
            sources = [trash_url(s) for s in sources]
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
        # ktrash6 empties the trash; `kioclient remove trash:/` returned 0
        # and left everything in it (VM, 2026-10-22). The question was asked
        # by the caller (Windows 11 dialog) already.
        self.start(["ktrash6", "--empty"])

    def open(self, path):
        """Open with the default app (folders are handled by the caller):
        programs through KIO, documents through the portal."""
        if is_program(path):
            self.start(["kioclient", "exec", str(path)])
        else:
            self.open_document(str(path))

    def open_with(self, desktop_path, paths):
        command = places.exec_command(desktop_path, [str(p) for p in paths])
        if command:
            self.start(command)

    def properties(self, paths):
        """Windows 11's Properties window (properties.py), not KDE's dialog."""
        paths = [str(p) for p in paths]
        if paths:
            self.start([sys.executable, "-m", "veltos_explorer", "--properties", *paths])

    def terminal(self, folder):
        # Opaque window: see update-app-names (veltos-desktop).
        self.start(["konsole", "--notransparency", "--workdir", str(folder)], cwd=str(folder))

    def compress(self, sources, folder):
        """Make a .zip of the items (VeltOS Archive's progress window)."""
        if not sources:
            return ""
        base = Path(sources[0]).stem if len(sources) == 1 else Path(folder).name or "Archive"
        name = files.unique_name(folder, base + ".zip")
        self.start(["veltos-archive", "--add-to", str(Path(folder) / name), *sources])
        return name

    def add_to_archive(self, sources):
        """WinRAR's "Add to archive...": name, format and password first."""
        if sources:
            self.start(["veltos-archive", "--add", *sources])

    def extract(self, archive, folder):
        """Extract all into a folder named like the archive (VeltOS Archive)."""
        self.start(["veltos-archive", "--extract-to-folder", str(archive)])

    def extract_here(self, archive):
        """WinRAR's "Extract Here": next to the archive."""
        self.start(["veltos-archive", "--extract-here", str(archive)])

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
