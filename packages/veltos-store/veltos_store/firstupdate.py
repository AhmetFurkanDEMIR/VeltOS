"""The first start of an installed VeltOS brings it up to date (product
owner, 2026-10-27: "after the first start run apt-get update and upgrade in
the background, with a Windows 11 style 'getting everything ready' window;
only on the first start").

veltos-first-update.service runs this as root once (it creates DONE at the
end, also when there was no internet: VeltOS Update brings the updates
later) and never in the live system. It waits for the network itself
(nm-online) instead of ordering the service after network-online.target,
so the sign-in screen is not held up. Progress goes to STATUS as JSON for
the window (firststart.py):

    {"state": "network" | "lists" | "download" | "install" | "bottles" | "done" | "offline" | "failed",
     "percent": 0-100, "packages": N}

When the installer's choice for Windows programs was Bottles
(/etc/veltos/windows-apps.conf, runner=bottles), Bottles is installed from
Flathub after the updates (state "bottles"; the same commands as
veltos-winapps' bottles.py). Without internet or after a failure the done
file waits, so the next start tries again, up to BOTTLES_ATTEMPTS times.

apt's own progress comes from APT::Status-Fd ("dlstatus:" and "pmstatus:"
lines); the download is the first half of the bar, the installation the
second. Everything apt prints also goes to /var/log/veltos-first-update.log.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

STATUS = Path("/run/veltos/first-update.json")
DONE = Path("/var/lib/veltos/first-update-done")
LOG = Path("/var/log/veltos-first-update.log")
WINDOWS_CONF = Path("/etc/veltos/windows-apps.conf")
BOTTLES_ATTEMPTS_FILE = Path("/var/lib/veltos/bottles-attempts")
BOTTLES_ATTEMPTS = 5
BOTTLES_DESKTOP = Path("/var/lib/flatpak/exports/share/applications/com.usebottles.bottles.desktop")
BOTTLES_COMMANDS = [
    ["flatpak", "remote-add", "--system", "--if-not-exists", "flathub",
     "https://dl.flathub.org/repo/flathub.flatpakrepo"],
    ["flatpak", "install", "--system", "-y", "--noninteractive", "flathub", "com.usebottles.bottles"],
]
SHOW_AFTER_DONE = 30 * 60        # a sign-in this soon after the update still says "ready"
APT_OPTIONS = ["-o", "APT::Status-Fd=1", "-o", "DPkg::Lock::Timeout=600", "-o", "Dpkg::Options::=--force-confdef",
               "-o", "Dpkg::Options::=--force-confold"]
ENVIRONMENT = {"DEBIAN_FRONTEND": "noninteractive", "LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
               "APT_LISTCHANGES_FRONTEND": "none"}


def write_status(state, percent=0, status=STATUS, **extra):
    data = {"state": state, "percent": max(0, min(100, int(percent))), "time": int(time.time()), **extra}
    try:
        status.parent.mkdir(parents=True, exist_ok=True)
        tmp = status.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.chmod(0o644)
        os.replace(tmp, status)
    except OSError:
        pass


def read_status(status=STATUS):
    try:
        data = json.loads(Path(status).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def progress(line):
    """(phase, percent of the phase) for an APT::Status-Fd line, or None."""
    match = re.match(r"^(dlstatus|pmstatus):[^:]*:([0-9.]+):", line)
    if not match:
        return None
    return ("download" if match.group(1) == "dlstatus" else "install"), float(match.group(2))


def overall(phase, percent):
    """The bar: download 0-50 %, installation 50-100 %."""
    return percent / 2 if phase == "download" else 50 + percent / 2


def online(runner=subprocess.run, timeout=120):
    """Waits until NetworkManager says the PC is online (or gives up)."""
    try:
        return runner(["nm-online", "-q", "-t", str(timeout)], timeout=timeout + 10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def run_apt(arguments, on_line, popen=subprocess.Popen, log=None):
    """Runs apt-get, giving each output line to on_line; the exit code."""
    try:
        process = popen(["apt-get", *APT_OPTIONS, *arguments], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, env=ENVIRONMENT)
    except OSError as error:
        if log:
            log.write(f"apt-get: {error}\n")
        return 127
    for line in process.stdout:
        if log:
            log.write(line)
        on_line(line.rstrip("\n"))
    return process.wait()


def upgradable(runner=subprocess.run):
    """How many packages the upgrade will change (apt-get -s)."""
    try:
        out = runner(["apt-get", "-s", "-o", "Debug::NoLocking=1", "full-upgrade"], capture_output=True, text=True,
                     env=ENVIRONMENT, timeout=300).stdout
    except (OSError, subprocess.SubprocessError):
        return 0
    return len(re.findall(r"^Inst ", out, re.M))


def wants_bottles(conf=WINDOWS_CONF):
    try:
        text = Path(conf).read_text(encoding="utf-8")
    except OSError:
        return False
    return any(line.strip().replace(" ", "") == "runner=bottles" for line in text.splitlines())


def install_bottles(runner=subprocess.run, log=None):
    """Bottles from Flathub, system-wide; True when it is there."""
    for command in BOTTLES_COMMANDS:
        try:
            result = runner(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3 * 3600)
        except (OSError, subprocess.SubprocessError) as error:
            if log:
                log.write(f"{command[0]}: {error}\n")
            return False
        if log:
            log.write(" ".join(command) + "\n" + (result.stdout or "")[-3000:] + (result.stderr or "")[-3000:])
        if result.returncode != 0:
            return False
    return True


def bottles_pending(attempts_file=BOTTLES_ATTEMPTS_FILE, conf=WINDOWS_CONF, desktop=BOTTLES_DESKTOP):
    """Bottles chosen, not installed and not given up yet: the done file waits."""
    if not wants_bottles(conf) or Path(desktop).exists():
        return False
    try:
        attempts = int(Path(attempts_file).read_text().strip() or 0)
    except (OSError, ValueError):
        attempts = 0
    return attempts < BOTTLES_ATTEMPTS


def count_attempt(attempts_file=BOTTLES_ATTEMPTS_FILE):
    try:
        attempts = int(Path(attempts_file).read_text().strip() or 0)
    except (OSError, ValueError):
        attempts = 0
    try:
        Path(attempts_file).parent.mkdir(parents=True, exist_ok=True)
        Path(attempts_file).write_text(f"{attempts + 1}\n")
    except OSError:
        pass


def main(status=STATUS, done=DONE, log_path=LOG, runner=subprocess.run, popen=subprocess.Popen, wait=online,
         conf=WINDOWS_CONF, attempts_file=BOTTLES_ATTEMPTS_FILE, bottles_desktop=BOTTLES_DESKTOP):
    try:
        log = open(log_path, "a", encoding="utf-8")
    except OSError:
        log = None

    def finish(state, code):
        if state == "done" and wants_bottles(conf) and not Path(bottles_desktop).exists():
            write_status("bottles", 0, status)
            if not install_bottles(runner, log):
                count_attempt(attempts_file)
        write_status(state, 100 if state == "done" else 0, status)
        if bottles_pending(attempts_file, conf, bottles_desktop):
            if log:
                log.write("== Bottles not installed yet: the next start tries again\n")
        else:
            try:
                done.parent.mkdir(parents=True, exist_ok=True)
                done.write_text(time.strftime("%Y-%m-%d %H:%M:%S ") + state + "\n", encoding="utf-8")
            except OSError:
                pass
        if log:
            log.write(f"== {state}\n")
            log.close()
        return code

    write_status("network", 0, status)
    if not wait(runner):
        if wants_bottles(conf):
            count_attempt(attempts_file)
        return finish("offline", 0)
    write_status("lists", 0, status)
    if run_apt(["update"], lambda line: None, popen, log) != 0:
        return finish("failed", 1)
    count = upgradable(runner)
    if count == 0:
        return finish("done", 0)
    last = {"value": -1}

    def on_line(line):
        parsed = progress(line)
        if parsed:
            value = overall(*parsed)
            if int(value) != last["value"]:
                last["value"] = int(value)
                write_status(parsed[0], value, status, packages=count)
    write_status("download", 0, status, packages=count)
    code = run_apt(["-y", "full-upgrade"], on_line, popen, log)
    return finish("done" if code == 0 else "failed", 0 if code == 0 else 1)


# --- whether the window shows (firststart.py; no Qt here: it runs at every sign-in) ---

def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def marker():
    return config_home() / "veltos" / "first-start-shown"


def live(cmdline=Path("/proc/cmdline")):
    try:
        return "boot=live" in cmdline.read_text().split()
    except OSError:
        return False


def should_show(done=DONE, status=STATUS, shown=None, cmdline=Path("/proc/cmdline"),
                now=None):
    if live(cmdline) or (shown or marker()).exists():
        return False
    if done.exists():
        try:
            return (now or time.time()) - done.stat().st_mtime < SHOW_AFTER_DONE
        except OSError:
            return False
    # Not done: the service runs (or is about to); without its status file
    # it may not be installed at all, then there is nothing to show.
    return status.exists() or Path("/etc/systemd/system/multi-user.target.wants/veltos-first-update.service").exists()


if __name__ == "__main__":
    sys.exit(main())
