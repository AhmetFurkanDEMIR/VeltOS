"""The driver log the user can read and copy (product owner, 2026-10-27:
"users should be able to see the logs"): what VeltOS Graphics Cards ran
and what pkcon answered (kept in the user's state folder), the system's
driver state (kernel, loaded modules, NVIDIA's modesetting, DKMS, Secure
Boot), DKMS's build log and dpkg's history of the driver packages. All of
it is readable without administrator rights; the kernel's own messages
need them (`journalctl -k`) and are added on request."""

import datetime
import os
import re
import subprocess
from pathlib import Path

MAX_LOG = 512 * 1024
DKMS = Path("/var/lib/dkms")
KERNEL_PATTERN = re.compile(r"nvidia|nouveau|amdgpu|radeon|i915|\bxe\b|drm|dkms|secure boot|lockdown|"
                            r"key was rejected|module verification|firmware", re.I)
DRIVER_PACKAGES = re.compile(r" (nvidia-\S+|libnvidia-\S+|firmware-(amd|intel|nvidia)-\S+|linux-(image|headers)-\S+"
                             r"|mesa-\S+|libgl1-mesa-dri\S*) ")


def state_dir():
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base) / "veltos-graphics"


def log_file():
    return state_dir() / "driver.log"


def append(text):
    """Adds a job's output to the log, keeping its last 512 KB."""
    path = log_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_bytes() if path.exists() else b""
        data = (old + text.encode("utf-8", "replace"))[-MAX_LOG:]
        path.write_bytes(data)
    except OSError:
        pass


def heading(text):
    return f"\n== {text} " + "=" * max(4, 70 - len(text)) + "\n"


def stamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run(command, timeout=20):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env={"LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})
        return (result.stdout + result.stderr).strip()
    except (OSError, subprocess.SubprocessError) as error:
        return f"({command[0]}: {error})"


def read(path, limit=None):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-limit:] if limit else text


def module_parameters(root=Path("/sys/module")):
    rows = []
    for module in ("nvidia_drm", "nvidia", "nouveau"):
        folder = root / module
        if not folder.is_dir():
            continue
        values = []
        for name in ("modeset", "fbdev"):
            value = read(folder / "parameters" / name).strip()
            if value:
                values.append(f"{name}={value}")
        version = read(folder / "version").strip()
        rows.append(f"{module}: loaded" + (f", version {version}" if version else "")
                    + (", " + ", ".join(values) if values else ""))
    return rows


def dkms_logs(root=DKMS):
    """The newest build logs of DKMS's NVIDIA modules (dkms 3 keeps the log of
    a failed build in build/make.log, of the others per kernel)."""
    logs = sorted((p for pattern in ("nvidia*/*/build/make.log", "nvidia*/*/*/*/log/make.log")
                   for p in root.glob(pattern)), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[:2]


def dpkg_history(path=Path("/var/log/dpkg.log"), limit=60):
    lines = [line for line in read(path).splitlines()
             if " status installed " in line or " remove " in line or " purge " in line]
    return [line for line in lines if DRIVER_PACKAGES.search(line + " ")][-limit:]


def report(runner=run):
    """The whole text the log window shows."""
    out = [f"VeltOS Graphics Cards — driver log ({stamp()})"]
    out.append(heading("System"))
    out.append(f"Linux {os.uname().release}")
    out.append(runner(["mokutil", "--sb-state"]) or "mokutil: no answer")
    out.extend(module_parameters() or ["No graphics kernel module of NVIDIA or Nouveau is loaded."])
    out.append(heading("Graphics cards"))
    out.append(runner(["lspci", "-nnk", "-d", "::0300"]) + "\n" + runner(["lspci", "-nnk", "-d", "::0302"]))
    out.append(heading("Screens (DRM connectors)"))
    connectors = []
    for status in sorted(Path("/sys/class/drm").glob("card*-*/status")):
        connectors.append(f"{status.parent.name}: {read(status).strip()}")
    out.extend(connectors or ["(none)"])
    out.append(heading("DKMS"))
    out.append(runner(["dkms", "status"]) or "(no DKMS modules)")
    for path in dkms_logs():
        out.append(heading(f"DKMS build log {path}"))
        out.append(read(path, 20000))
    out.append(heading("Driver packages (dpkg.log)"))
    out.extend(dpkg_history() or ["(no changes logged)"])
    out.append(heading("VeltOS Graphics Cards jobs"))
    out.append(read(log_file(), 60000).strip() or "(no installation, update or removal yet)")
    return "\n".join(out).strip() + "\n"


def kernel_messages(text):
    """The kernel's lines about graphics drivers from `journalctl -k`."""
    lines = [line for line in text.splitlines() if KERNEL_PATTERN.search(line)]
    return heading("Kernel messages (this start)") + ("\n".join(lines[-400:]) or "(none about graphics)") + "\n"
