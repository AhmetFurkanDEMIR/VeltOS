"""Light/dark and the accent colour while a VeltOS window is open.

VeltOS Settings, Quick Settings and VeltOS AI switch them by writing
~/.config/kdeglobals; Windows 11's apps follow such a switch at once, and
so does every VeltOS window (product owner, 2026-11-01: the App Installer
kept its light page after the system went dark, only its frame changed).

ThemeWatch watches the config folder and kdeglobals (tools such as
kwriteconfig6 replace the file, which drops a watch on the file itself),
reads the look again a moment after a change and emits `changed` when
light/dark or the accent differ. An app's darkMode and accent properties
notify with it, and its Theme.qml, bound to them, repaints.

The same file is in every package that needs it (each builds on its own);
tests/repo checks that the copies match veltos-store's.
"""

import os
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


class ThemeWatch(QObject):
    """`read()` returns (dark, accent). Without `read` (tests) nothing is
    watched and the look stays `initial`."""

    changed = Signal()

    def __init__(self, read=None, parent=None, initial=None, delay=300):
        super().__init__(parent)
        self._read = read
        self.dark, self.accent = initial if initial is not None else (read() if read else (False, ""))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay)
        self._timer.timeout.connect(self.check)
        self._watcher = QFileSystemWatcher(self)
        if read:
            self._watch()
            self._watcher.directoryChanged.connect(self._timer.start)
            self._watcher.fileChanged.connect(self._timer.start)

    def _watch(self):
        home = config_home()
        watched = set(self._watcher.files()) | set(self._watcher.directories())
        for path in (home, home / "kdeglobals"):
            if path.exists() and str(path) not in watched:
                self._watcher.addPath(str(path))

    def check(self):
        """Read the look again; True when it changed."""
        if not self._read:
            return False
        self._watch()
        dark, accent = self._read()
        if (bool(dark), accent or "") == (self.dark, self.accent):
            return False
        self.dark, self.accent = bool(dark), accent or ""
        self.changed.emit()
        return True
