"""Places of File Explorer: the user's folders, pinned folders, drives,
the Recycle Bin and recent files. Pure Python; commands go through `run`
so tests can replace them."""

import json
import os
import re
import shlex
import subprocess
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

HOME = Path.home()


def run(command, timeout=20):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                stdin=subprocess.DEVNULL)
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or HOME / ".local/share")


# --- The user's folders -------------------------------------------------------------

# (key in user-dirs.dirs, default folder name, icon)
USER_DIRS = [
    ("DESKTOP", "Desktop", "user-desktop"),
    ("DOWNLOAD", "Downloads", "folder-download"),
    ("DOCUMENTS", "Documents", "folder-documents"),
    ("PICTURES", "Pictures", "folder-pictures"),
    ("MUSIC", "Music", "folder-music"),
    ("VIDEOS", "Videos", "folder-videos"),
]


def user_dirs(home=None):
    """[(key, path, icon)] from ~/.config/user-dirs.dirs (XDG), with the
    English defaults where it says nothing."""
    home = Path(home or HOME)
    values = {}
    try:
        text = (config_home() / "user-dirs.dirs").read_text(encoding="utf-8")
    except OSError:
        text = ""
    for match in re.finditer(r'^XDG_(\w+)_DIR="(.*)"$', text, re.M):
        values[match.group(1)] = match.group(2).replace("$HOME", str(home))
    result = []
    for key, default, icon in USER_DIRS:
        path = Path(values.get(key) or home / default)
        if path != home:          # "not set" in user-dirs means the home folder
            result.append((key, str(path), icon))
    return result


def folder_icon(path, home=None):
    """The special icon of a user folder, else "folder"."""
    path = str(path)
    home = str(home or HOME)
    if path == home:
        return "user-home"
    for _key, folder, icon in user_dirs(home):
        if folder == path:
            return icon
    return "folder"


# --- Pinned folders (Quick access) --------------------------------------------------

class Pins:
    """Folders pinned to Quick access, kept in ~/.config/veltos-explorer.json
    together with the other preferences."""

    def __init__(self, path=None):
        self.path = Path(path or config_home() / "veltos-explorer.json")
        self.data = self._load()

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def pinned(self):
        if "pinned" not in self.data:
            return [path for _k, path, _i in user_dirs()]
        return [p for p in self.data["pinned"] if isinstance(p, str)]

    def pin(self, path):
        pins = self.pinned()
        if path not in pins:
            self.data["pinned"] = pins + [path]
            self.save()

    def unpin(self, path):
        self.data["pinned"] = [p for p in self.pinned() if p != path]
        self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()


# --- Drives ---------------------------------------------------------------------------

# Partition types Windows keeps for itself (not shown, like in Windows).
WINDOWS_HIDDEN_TYPES = {
    "de94bba4-06d1-4d40-a16a-bfd50179d6ac",     # Windows Recovery Environment
    "e3c9e316-0b5c-4db8-817d-f92df00215ae",     # Microsoft reserved
    "0x27",                                      # MBR: Windows recovery
}
NTFS = ("ntfs", "ntfs3")


def mount_options(mounts_text=None):
    """{mount point: options} of the mounted file systems."""
    if mounts_text is None:
        try:
            mounts_text = Path("/proc/self/mounts").read_text()
        except OSError:
            mounts_text = ""
    result = {}
    for line in mounts_text.splitlines():
        fields = line.split()
        if len(fields) >= 4:
            point = fields[1].replace("\\040", " ")
            result[point] = fields[3].split(",")
    return result


def drive_icon(drive):
    """Distinguish USB sticks, other removable drives and fixed NTFS drives."""
    if drive.get("usb"):
        return "drive-removable-media-usb"
    if drive.get("removable"):
        return "drive-removable-media"
    if drive.get("windows"):
        return "drive-harddisk-windows"
    return "drive-harddisk"


def _system_mount(point):
    return (point in ("/", "/boot", "/boot/efi", "/efi", "/usr", "/var")
            or point.startswith("/boot/") or point.startswith("/efi/")
            or point.startswith("/usr/") or point.startswith("/var/")
            or point.startswith("/run/live/"))


def _tree_has_system_mount(device):
    mounts = [point for point in (device.get("mountpoints") or []) if point]
    return (any(_system_mount(point) for point in mounts)
            or any(_tree_has_system_mount(child) for child in (device.get("children") or [])))


def drives(runner=run, live=None, mounts_text=None):
    """Drives for This PC. Keep every volume on the running system's
    physical disk out of the Format menu, even when it is not mounted."""
    code, out = runner(["lsblk", "--json", "--bytes", "-o",
                        "NAME,PATH,LABEL,SIZE,FSTYPE,MOUNTPOINTS,RM,HOTPLUG,RO,TRAN,TYPE,FSSIZE,FSUSED,PARTTYPE"])
    try:
        tree = json.loads(out)["blockdevices"] if code == 0 else []
    except (ValueError, KeyError, TypeError):
        tree = []
    result = []
    options = mount_options(mounts_text)

    def walk(devices, removable, transport, system_disk, read_only):
        for dev in devices or []:
            transport_here = (dev.get("tran") or transport or "").lower()
            removable_here = (removable or bool(dev.get("rm")) or bool(dev.get("hotplug"))
                              or transport_here == "usb")
            read_only_here = read_only or bool(dev.get("ro"))
            fstype = dev.get("fstype") or ""
            mounts = [m for m in (dev.get("mountpoints") or []) if m]
            if fstype and fstype not in ("swap", "squashfs", "iso9660", "LVM2_member",
                                          "crypto_LUKS") and dev.get("type") in ("part", "disk", "lvm"):
                parttype = (dev.get("parttype") or "").lower()
                small = int(dev.get("size") or 0) < 600 * 1024 ** 2
                efi = parttype == "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
                hidden = mounts and all(m.startswith(("/boot", "/run/live", "/usr/lib/live")) for m in mounts)
                windows_own = parttype in WINDOWS_HIDDEN_TYPES
                if not (efi or hidden or windows_own or (small and not removable_here and not mounts)):
                    mount = "/" if "/" in mounts else (mounts[0] if mounts else "")
                    windows = fstype in NTFS
                    system = any(_system_mount(point) for point in mounts)
                    readonly = read_only_here or bool(mount and "ro" in options.get(mount, []))
                    drive = {
                        "device": dev.get("path", ""),
                        "label": dev.get("label") or "",
                        "mount": mount,
                        "size": int(dev.get("fssize") or dev.get("size") or 0),
                        "used": int(dev.get("fsused") or 0),
                        "removable": removable_here,
                        "usb": transport_here == "usb",
                        "system": system,
                        "systemDisk": system_disk,
                        "canFormat": bool(dev.get("path") and not system and not system_disk and not readonly),
                        "fstype": fstype,
                        "windows": windows,
                        "windowsSystem": bool(windows and mount and os.path.isdir(os.path.join(mount, "Windows", "System32"))),
                        "readonly": readonly,
                    }
                    drive["icon"] = drive_icon(drive)
                    result.append(drive)
            walk(dev.get("children"), removable_here, transport_here, system_disk, read_only_here)

    for device in tree:
        walk([device], False, "", _tree_has_system_mount(device), False)
    # The live system's root is an overlay that lsblk does not show.
    live = Path("/run/live/medium").is_dir() if live is None else live
    if live and not any(d["system"] for d in result):
        try:
            st = os.statvfs("/")
            size, free = st.f_blocks * st.f_frsize, st.f_bavail * st.f_frsize
        except OSError:
            size = free = 0
        result.insert(0, {"device": "", "label": "", "mount": "/", "size": size, "used": size - free,
                          "removable": False, "usb": False, "system": True, "systemDisk": True,
                          "canFormat": False, "fstype": "overlay", "windows": False,
                          "windowsSystem": False, "readonly": False, "icon": "drive-harddisk"})
    result.sort(key=lambda d: (not d["system"], d["removable"], d["label"].lower(), d["device"]))
    return result


def mount(device, runner=run, windows=False, mounts_text=None):
    """Mount a partition (udisks; polkit may ask for the password). Returns
    (mount point or "", read only). A Windows drive that Windows did not
    shut down completely (Fast Startup, hibernation) is refused for writing
    by ntfs-3g (VeltOS' udisks setting, /etc/udisks2/mount_options.conf);
    it is then opened read only, so its file system stays intact."""
    def mounted(code, out):
        match = re.search(r" at (/.+?)\.?\s*$", out.strip()) if code == 0 else None
        return match.group(1) if match else ""

    code, out = runner(["udisksctl", "mount", "--no-user-interaction", "-b", device], timeout=60)
    if code != 0:
        code, out = runner(["udisksctl", "mount", "-b", device], timeout=300)
    point = mounted(code, out)
    if point:
        # ntfs-3g 2022 itself falls back to read only for a hibernated
        # Windows ("Falling back to read-only mount", VM 2026-10-21).
        return point, "ro" in mount_options(mounts_text).get(point, [])
    if not windows:
        return "", False
    code, out = runner(["udisksctl", "mount", "-b", device, "-o", "ro"], timeout=300)
    point = mounted(code, out)
    return point, bool(point)


def eject(device, runner=run):
    if runner(["udisksctl", "unmount", "-b", device], timeout=60)[0] != 0:
        return False
    parent = re.sub(r"p?\d+$", "", device)
    runner(["udisksctl", "power-off", "-b", parent], timeout=60)
    return True


# --- The desktop's system icons ----------------------------------------------------------

# "This PC", the Recycle Bin and the VeltOS Store on the desktop stay, like
# Windows' system icons (veltos-desktop: the session puts them there and
# its desktop guard makes them root's, so not even a terminal removes them).
DESKTOP_SYSTEM_ICONS = ("recycle-bin.desktop", "this-pc.desktop", "veltos-store.desktop")


def desktop_dir():
    return next((path for key, path, _icon in user_dirs() if key == "DESKTOP"), str(HOME / "Desktop"))


def is_desktop_system_icon(path, desktop=None):
    path = Path(path)
    return path.name in DESKTOP_SYSTEM_ICONS and str(path.parent) == str(desktop or desktop_dir())


# --- Recycle Bin ----------------------------------------------------------------------

def trash_dir():
    return data_home() / "Trash"


def trash_items(trash=None):
    """Items in the Recycle Bin with their original location and deletion
    date (freedesktop.org trash: files/ and info/*.trashinfo)."""
    trash = Path(trash or trash_dir())
    items = []
    try:
        names = os.listdir(trash / "files")
    except OSError:
        return items
    for name in names:
        info = trash / "info" / (name + ".trashinfo")
        original, deleted = "", ""
        try:
            text = info.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"^Path=(.*)$", text, re.M)
            original = urllib.parse.unquote(match.group(1)) if match else ""
            match = re.search(r"^DeletionDate=(.*)$", text, re.M)
            deleted = match.group(1).strip() if match else ""
        except OSError:
            pass
        items.append({"name": name, "path": str(trash / "files" / name), "original": original,
                      "deleted": deleted})
    return items


def restore(item_path, trash=None):
    """Move a Recycle Bin item back where it was. Returns "" or a reason:
    "exists" (something is there now), "unknown" (no original location)."""
    trash = Path(trash or trash_dir())
    name = Path(item_path).name
    info = trash / "info" / (name + ".trashinfo")
    original = next((i["original"] for i in trash_items(trash) if i["name"] == name), "")
    if not original:
        return "unknown"
    target = Path(original)
    if not target.is_absolute():
        target = Path("/") / target
    if target.exists() or target.is_symlink():
        return "exists"
    target.parent.mkdir(parents=True, exist_ok=True)
    os.rename(item_path, target)
    info.unlink(missing_ok=True)
    return ""


# --- Recent files ----------------------------------------------------------------------

def recent_files(limit=20):
    """Recently opened files, newest first, from the freedesktop.org list
    (recently-used.xbel) and KDE's RecentDocuments."""
    found = {}
    xbel = data_home() / "recently-used.xbel"
    try:
        root = ET.parse(xbel).getroot()
        for bookmark in root.iter("bookmark"):
            href = bookmark.get("href", "")
            if not href.startswith("file://"):
                continue
            path = urllib.parse.unquote(urllib.parse.urlparse(href).path)
            stamp = bookmark.get("visited") or bookmark.get("modified") or ""
            found[path] = max(found.get(path, ""), stamp)
    except (OSError, ET.ParseError):
        pass
    recent_dir = data_home() / "RecentDocuments"
    try:
        for desktop in recent_dir.glob("*.desktop"):
            text = desktop.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"^URL(?:\[\$e\])?=(.*)$", text, re.M)
            if not match:
                continue
            url = match.group(1).strip().replace("$HOME", str(HOME))
            path = urllib.parse.unquote(urllib.parse.urlparse(url).path) if url.startswith("file:") else url
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(desktop.stat().st_mtime))
            found[path] = max(found.get(path, ""), stamp)
    except OSError:
        pass
    items = [(stamp, path) for path, stamp in found.items() if os.path.isfile(path)]
    items.sort(reverse=True)
    return [path for _stamp, path in items[:limit]]


# --- Applications ---------------------------------------------------------------------

def application_dirs():
    dirs = [data_home() / "applications"]
    for base in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":"):
        if base:
            dirs.append(Path(base) / "applications")
    return dirs


def read_desktop_entry(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    section = re.search(r"^\[Desktop Entry\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
    if not section:
        return None
    values = {}
    for line in section.group(1).splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    if values.get("Type", "Application") != "Application" or values.get("NoDisplay") == "true" \
            or values.get("Hidden") == "true" or "Exec" not in values:
        return None
    return values


def applications_for(mime, lang="en"):
    """Applications that open a file type: [{id, name, icon}], from the
    MimeType= of installed .desktop files."""
    seen, result = set(), []
    for directory in application_dirs():
        try:
            files = sorted(directory.glob("*.desktop"))
        except OSError:
            continue
        for path in files:
            if path.name in seen:
                continue
            # The first file of a name wins, a hidden one too (VeltOS'
            # NoDisplay copies hide the originals behind them, as in Start).
            seen.add(path.name)
            entry = read_desktop_entry(path)
            if entry is None:
                continue
            types = [t for t in entry.get("MimeType", "").split(";") if t]
            if mime in types:
                name = entry.get(f"Name[{lang}]") or entry.get("Name", path.stem)
                result.append({"id": path.name, "name": name, "icon": entry.get("Icon", ""),
                               "path": str(path)})
    result.sort(key=lambda a: a["name"].casefold())
    return result


def exec_command(desktop_path, files):
    """The command a .desktop file runs for `files` (field codes per the
    Desktop Entry spec: %f %F %u %U; others dropped)."""
    entry = read_desktop_entry(desktop_path)
    if entry is None:
        return []
    args = shlex.split(entry["Exec"])
    command, placed = [], False
    for arg in args:
        if arg in ("%f", "%u"):
            command.append(files[0] if files else "")
            placed = True
        elif arg in ("%F", "%U"):
            command.extend(files)
            placed = True
        elif re.fullmatch(r"%[a-zA-Z]", arg):
            continue
        else:
            command.append(arg.replace("%%", "%"))
    if not placed:
        command.extend(files)
    return command
