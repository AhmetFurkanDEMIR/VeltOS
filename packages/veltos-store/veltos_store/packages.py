"""Installed packages and install / uninstall / update jobs.

Jobs run PackageKit's command-line client (`pkcon`) one after another, in
a pseudo terminal that answers its "Proceed with changes?" (ptyrun.py):
`pkcon -y` would make the transaction non-interactive and polkit would
refuse without asking. So PackageKit asks for the administrator password
through the session's authentication agent (VeltOS' prompt), also for a
standard user. Output is read in the C locale:

    Status: 	Downloading packages
    Percentage:	45
    Fatal error: Failed to obtain authentication.
"""

import re
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal

STATUS = {  # pkcon status -> text key in strings.py
    "Waiting for authentication": "authorising",
    "Downloading packages": "downloading",
    "Downloading": "downloading",
    "Installing packages": "installing",
    "Installing": "installing",
    "Removing packages": "removing",
    "Removing": "removing",
    "Updating packages": "updating",
}


# Removing an app must not take VeltOS itself with it (removing Dolphin
# would remove the kde-plasma-desktop metapackage, for example).
PROTECTED = ("veltos-", "calamares-settings-veltos", "kde-plasma-desktop", "plasma-desktop",
             "plasma-workspace", "kwin-", "sddm", "task-", "firefox-esr", "packagekit", "python3-pyside6")


def removal_is_protected(package, run=subprocess.run):
    """True if uninstalling the package would remove a part of VeltOS
    (apt-get's simulation, no administrator rights needed)."""
    if package.startswith(PROTECTED):
        return True
    try:
        result = run(["apt-get", "-s", "remove", package], capture_output=True, text=True, timeout=120,
                     env={"LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})
    except (OSError, subprocess.SubprocessError):
        return True
    removed = re.findall(r"^Remv (\S+)", result.stdout, re.M)
    return any(name.startswith(PROTECTED) for name in removed)


def installed_packages(run=subprocess.run):
    """Names of the installed packages (dpkg)."""
    try:
        result = run(["dpkg-query", "-W", "-f", "${Package}\t${db:Status-Abbrev}\n"],
                     capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return set()
    names = set()
    for line in result.stdout.splitlines():
        name, _, status = line.partition("\t")
        if status.startswith("ii"):
            names.add(name.split(":")[0])
    return names


def parse_progress(line):
    """(kind, value) for one line of `pkcon -p` output: ("percent", 45),
    ("status", "downloading"), ("error", text) or None."""
    line = line.rstrip("\n")
    match = re.match(r"^Percentage:\s*(\d+)", line)
    if match:
        return ("percent", min(100, int(match.group(1))))
    match = re.match(r"^Status:\s*(.+?)\s*$", line)
    if match:
        key = STATUS.get(match.group(1))
        return ("status", key) if key else None
    if line.startswith("Fatal error:"):
        return ("error", line.partition(":")[2].strip())
    return None


def failure_key(error):
    """A text key (strings.py) for PackageKit's error message, or "" for
    one that has no better wording than "something went wrong"."""
    text = (error or "").lower()
    if "authentication" in text or "not authorized" in text or "permission" in text:
        return "failed_auth"
    if "could not find" in text or "no packages were found" in text or "not found" in text \
            or "could not be found" in text:
        return "failed_not_found"
    if any(word in text for word in ("download", "network", "resolve", "fetch", "connect", "timed out",
                                     "temporary failure", "mirror")):
        return "failed_network"
    if "lock" in text or "another" in text or "busy" in text or "in use" in text:
        return "failed_busy"
    return ""


def lists_need_refresh(lists_dir="/var/lib/apt/lists", max_age_days=7, now=None):
    """Whether the package lists are missing or old: an installed system
    whose lists were last fetched when the image was built cannot find
    newer packages (and finds none at all when the lists are gone)."""
    import glob
    import os
    import time
    packages_files = glob.glob(os.path.join(lists_dir, "*_Packages")) + glob.glob(os.path.join(lists_dir, "*_Packages.*"))
    if not packages_files:
        return True
    newest = max(os.path.getmtime(f) for f in packages_files)
    return ((now or time.time()) - newest) > max_age_days * 86400


def count_updates(output):
    """Number of packages `pkcon -p get-updates` lists."""
    _, found, results = output.partition("Results:")
    if not found:
        return 0
    return sum(1 for line in results.splitlines() if re.search(r"\.\S+ \(.*\)\s*$", line))


class Jobs(QObject):
    """Queue of pkcon jobs: ("install" | "remove" | "update", package)."""

    changed = Signal()
    finished = Signal(str, str, bool)   # action, package, process exit OK

    def __init__(self, program="pkcon", parent=None, needs_refresh=lists_need_refresh):
        super().__init__(parent)
        self.program = program
        self.needs_refresh = needs_refresh
        self.queue = []
        self.current = None      # (action, package)
        self.percent = -1
        self.status = ""
        self.error = ""
        self.process = None

    def busy(self, package):
        return (self.current and self.current[1] == package) or any(p == package for _a, p in self.queue)

    def state(self, package):
        """"" / "waiting" / status key, and the percentage."""
        if self.current and self.current[1] == package:
            return self.status or {"install": "installing", "remove": "removing"}.get(self.current[0], "updating")
        if any(p == package for _a, p in self.queue):
            # Waiting behind the list refresh its own install asked for.
            return "refreshing" if self.current and self.current[0] == "refresh" else "waiting"
        return ""

    def add(self, action, package):
        if self.busy(package):
            return
        if action == "install" and self.needs_refresh() and not any(a == "refresh" for a, _p in self.queue) \
                and not (self.current and self.current[0] == "refresh"):
            # Old or missing package lists: fetch them first, or the app
            # "could not be found" (an installed system keeps the image's
            # lists until something refreshes them).
            self.queue.append(("refresh", ""))
        self.queue.append((action, package))
        self.changed.emit()
        self._next()

    def _arguments(self, action, package):
        # No -y: see the module's text (interactive transactions).
        if action == "install":
            return ["-p", "install", package]
        if action == "remove":
            return ["-p", "remove", package]
        if action == "refresh":
            return ["-p", "refresh"]
        return ["-p", "update"]

    def _next(self):
        if self.process is not None or not self.queue:
            return
        self.current = self.queue.pop(0)
        self.percent, self.status, self.error = -1, "", ""
        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C")
        environment.insert("LANGUAGE", "C")
        # ptyrun comes from the same place as this module (the tests run
        # from the source tree).
        here = str(Path(__file__).resolve().parent.parent)
        environment.insert("PYTHONPATH", here + (":" + environment.value("PYTHONPATH")
                                                 if environment.contains("PYTHONPATH") else ""))
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._done)
        process.errorOccurred.connect(self._failed_to_start)
        self.process = process
        process.start(sys.executable, ["-m", "veltos_store.ptyrun", self.program, *self._arguments(*self.current)])
        self.changed.emit()

    def _read(self):
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        for line in data.splitlines():
            parsed = parse_progress(line)
            if not parsed:
                continue
            kind, value = parsed
            if kind == "percent":
                self.percent = value
            elif kind == "status":
                self.status = value
            else:
                self.error = value
        self.changed.emit()

    def _failed_to_start(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.error = "pkcon"
            self._done(1, QProcess.ExitStatus.CrashExit)

    def _done(self, code, status):
        if self.process is None:
            return
        action, package = self.current
        if code == 127 and not self.error:
            self.error = "pkcon"           # ptyrun could not start pkcon
        ok = status == QProcess.ExitStatus.NormalExit and code == 0 and not self.error
        self.process.deleteLater()
        self.process = None
        self.current = None
        self.finished.emit(action, package, ok)
        self.changed.emit()
        self._next()
