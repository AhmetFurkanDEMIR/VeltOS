"""Installed packages and install / uninstall / update jobs.

Jobs run PackageKit's command-line client (`pkcon`) one after another;
PackageKit asks for the administrator password through the session's
authentication agent, as Discover does. Output is read in the C locale:

    Status: 	Downloading packages
    Percentage:	45
    Fatal error: Failed to obtain authentication.
"""

import re
import subprocess

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

    def __init__(self, program="pkcon", parent=None):
        super().__init__(parent)
        self.program = program
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
            return "waiting"
        return ""

    def add(self, action, package):
        if self.busy(package):
            return
        self.queue.append((action, package))
        self.changed.emit()
        self._next()

    def _arguments(self, action, package):
        if action == "install":
            return ["-p", "-y", "install", package]
        if action == "remove":
            return ["-p", "-y", "remove", package]
        return ["-p", "-y", "update"]

    def _next(self):
        if self.process is not None or not self.queue:
            return
        self.current = self.queue.pop(0)
        self.percent, self.status, self.error = -1, "", ""
        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C")
        environment.insert("LANGUAGE", "C")
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._done)
        process.errorOccurred.connect(self._failed_to_start)
        self.process = process
        process.start(self.program, self._arguments(*self.current))
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
        ok = status == QProcess.ExitStatus.NormalExit and code == 0 and not self.error
        self.process.deleteLater()
        self.process = None
        self.current = None
        self.finished.emit(action, package, ok)
        self.changed.emit()
        self._next()
