"""Facts about this computer for VeltOS Settings (About, Storage, Home).

Everything is read from the running system with the standard library and
`lspci`; every function tolerates missing files and returns something
displayable, because Settings must open on any machine.
"""

import os
import platform
import pwd
import re
import shlex
import shutil
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path("/")

# File systems that hold user data (others are virtual: proc, tmpfs, ...).
DATA_FILESYSTEMS = {"ext4", "ext3", "btrfs", "xfs", "f2fs", "vfat", "exfat", "ntfs", "ntfs3",
                    "fuseblk", "overlay"}


def read(path, default=""):
    try:
        return (ROOT / str(path).lstrip("/")).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return default


def os_release():
    values = {}
    for line in read("/etc/os-release").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


def os_build():
    """The image build ("20261019.0804"), written into the image by the ISO
    build; shown as "OS build" like Windows shows its build number."""
    for line in read("/usr/lib/veltos/build-info").splitlines():
        if line.startswith("VELTOS_BUILD="):
            return line.split("=", 1)[1].strip()
    return os_release().get("BUILD_ID", "")


def cpu_model():
    names = re.findall(r"^model name\s*:\s*(.+)$", read("/proc/cpuinfo"), re.M)
    if not names:
        return platform.processor() or "", os.cpu_count() or 0
    return re.sub(r"\s+", " ", names[0]).strip(), len(names)


def memory_bytes():
    match = re.search(r"^MemTotal:\s+(\d+) kB", read("/proc/meminfo"), re.M)
    return int(match.group(1)) * 1024 if match else 0


def gpus(lspci_output=None):
    """Graphics adapters as "Vendor Device" strings (from `lspci -mm`)."""
    if lspci_output is None:
        try:
            lspci_output = subprocess.run(["lspci", "-mm"], capture_output=True, text=True,
                                          timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            return []
    result = []
    for line in lspci_output.splitlines():
        try:
            fields = shlex.split(line)
        except ValueError:
            continue
        if len(fields) >= 4 and fields[1] in ("VGA compatible controller", "3D controller",
                                              "Display controller"):
            # "Red Hat, Inc." and "NVIDIA Corporation" lose the company suffix.
            vendor = re.sub(r",? (Corporation|Corp\.|Inc\.|Co\., Ltd\.)$", "", fields[2])
            vendor = vendor.replace("Advanced Micro Devices, Inc. [AMD/ATI]", "AMD")
            result.append(f"{vendor} {fields[3]}".strip())
    return result


def device_model():
    vendor = read("/sys/class/dmi/id/sys_vendor").strip()
    product = read("/sys/class/dmi/id/product_name").strip()
    if product.lower() in ("", "to be filled by o.e.m.", "system product name", "default string"):
        product = ""
    return " ".join(part for part in (vendor, product) if part and part.lower() != "to be filled by o.e.m.")


def pc_name():
    """The name shown to people: the "pretty" hostname if set."""
    for line in read("/etc/machine-info").splitlines():
        if line.startswith("PRETTY_HOSTNAME="):
            name = line.split("=", 1)[1].strip().strip('"')
            if name:
                return name
    return socket.gethostname()


def valid_pc_name(name):
    """Names hostnamectl accepts as a pretty hostname and can turn into a
    static one: 1-63 visible characters, at least one letter or digit."""
    name = name.strip()
    return 0 < len(name) <= 63 and any(c.isalnum() for c in name) and name.isprintable()


def user_name():
    try:
        entry = pwd.getpwuid(os.getuid())
    except KeyError:
        return os.environ.get("USER", "")
    full = entry.pw_gecos.split(",", 1)[0].strip()
    return full or entry.pw_name


def human_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit in ("B", "KB") else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def about():
    release = os_release()
    cpu, threads = cpu_model()
    return {
        "pcName": pc_name(),
        "model": device_model(),
        "os": release.get("PRETTY_NAME", "VeltOS"),
        "version": release.get("VERSION", release.get("VERSION_ID", "")),
        "build": os_build(),
        "cpu": cpu,
        "threads": threads,
        "memory": human_size(memory_bytes()),
        "gpus": gpus(),
        "architecture": "64-bit" if platform.machine() in ("x86_64", "aarch64") else platform.machine(),
    }


def mounts(text=None):
    """(mount point, file system type, device) of mounted data file systems."""
    text = read("/proc/mounts") if text is None else text
    seen, result = set(), []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        device, target, fstype = fields[0], fields[1].replace("\\040", " "), fields[2]
        if fstype not in DATA_FILESYSTEMS or target in seen:
            continue
        if target.startswith(("/boot", "/snap", "/run/live", "/var/lib/docker")):
            continue
        if fstype == "overlay" and target != "/":
            continue
        seen.add(target)
        result.append((target, fstype, device))
    return result


def storage(mount_text=None, usage=shutil.disk_usage):
    drives = []
    for target, fstype, device in mounts(mount_text):
        try:
            total, used, free = usage(target)
        except OSError:
            continue
        if total == 0:
            continue
        drives.append({
            "mount": target,
            "system": target == "/",
            "live": fstype == "overlay",
            "removable": target.startswith(("/media/", "/run/media/")),
            "label": Path(target).name or "/",
            "total": human_size(total),
            "used": human_size(used),
            "free": human_size(free),
            "fraction": round(used / total, 4),
        })
    return drives


APT_LISTS = Path("/var/lib/apt/lists")


def last_update_check(lists=APT_LISTS):
    """When the package lists were last refreshed (apt or PackageKit), as
    seconds since 1970; 0 if never."""
    try:
        times = [p.stat().st_mtime for p in lists.iterdir() if p.name.endswith("Release")]
    except OSError:
        return 0
    return int(max(times)) if times else 0


def ago(seconds, lang, now=None):
    """'1 hour ago' style text for Windows Update's "Last checked"."""
    from . import strings
    if not seconds:
        return strings.text(lang, "never_checked")
    elapsed = max(0, int((now if now is not None else time.time()) - seconds))
    for limit, unit in ((60, None), (3600, "minute"), (86400, "hour"), (None, "day")):
        if limit is not None and elapsed < limit:
            break
    if unit is None:
        return strings.text(lang, "just_now")
    count = elapsed // {"minute": 60, "hour": 3600, "day": 86400}[unit]
    key = f"{unit}_ago" if count == 1 else f"{unit}s_ago"
    return strings.text(lang, key).replace("{count}", str(count))


def dark_mode():
    """True if the current global theme is VeltOS Dark (or any dark one)."""
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (config / "kdeglobals", Path("/etc/xdg/kdeglobals")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = re.search(r"^LookAndFeelPackage=(.+)$", text, re.M)
        if match:
            return "dark" in match.group(1).lower()
        match = re.search(r"^ColorScheme=(.+)$", text, re.M)
        if match:
            return "dark" in match.group(1).lower()
    return False
