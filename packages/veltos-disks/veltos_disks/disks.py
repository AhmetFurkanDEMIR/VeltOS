"""Disks and volumes for VeltOS Disk Management, read from UDisks2.

UDisks2 (the system's disk service) is asked for all its objects with
`busctl --json=short` (one call, plain JSON, readable by every user). The
objects are turned into what Windows' Disk Management shows: disks ("Disk
0", "CD-ROM 0") with their partitions and unallocated space in disk order,
and the volume list with layout, type, file system, status, capacity and
free space. Changes (format, delete, new volume, label, initialize, mount,
eject) are UDisks2 method calls made with busctl as well; UDisks2 asks for
the administrator password through polkit where needed and refuses what it
must not do. This module only builds the calls; app.py runs them.
"""

import json
import os
import re
import shutil
import subprocess

SERVICE = "org.freedesktop.UDisks2"
PREFIX = "org.freedesktop.UDisks2."
MIB = 1024 * 1024
GIB = 1024 * MIB
TIB = 1024 * GIB
# Gaps smaller than this are alignment and table space, not unallocated
# space (Windows does not show them either).
MIN_GAP = 4 * MIB

# GPT partition types with a role of their own.
GPT_ROLES = {
    "c12a7328-f81f-11d2-ba4b-00a0c93ec93b": "efi",
    "e3c9e316-0b5c-4db8-817d-f92df00215ae": "reserved",
    "de94bba4-06d1-4d40-a16a-bfd50179d6ac": "recovery",
    "0657fd6d-a4ab-43c4-84e5-0933c84b4f4f": "swap",
    "21686148-6449-6e6f-744e-656564454649": "bios_boot",
}
MBR_ROLES = {"0xef": "efi", "0x82": "swap", "0x27": "recovery"}
# Partition types for new volumes: Microsoft basic data for the file
# systems Windows reads, Linux data for ext4.
NEW_TYPES = {
    "gpt": {"ntfs": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7", "exfat": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7",
            "vfat": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7", "ext4": "0fc63daf-8483-4772-8e79-3d69d8477de4"},
    "dos": {"ntfs": "0x07", "exfat": "0x07", "vfat": "0x0c", "ext4": "0x83"},
}
# Mount points of the running system: its volumes cannot be formatted or
# deleted (Windows greys these out for the system and boot volumes).
SYSTEM_MOUNTS = ("/", "/boot", "/boot/efi", "/efi", "/usr", "/var")
FORMATS = ("ntfs", "exfat", "vfat", "ext4")
MKFS = {"ntfs": ("mkfs.ntfs", "mkntfs"), "exfat": ("mkfs.exfat",), "vfat": ("mkfs.vfat", "mkfs.fat"),
        "ext4": ("mkfs.ext4",)}
FS_NAMES = {"ntfs": "NTFS", "exfat": "exFAT", "ext4": "ext4", "ext3": "ext3", "ext2": "ext2", "btrfs": "Btrfs",
            "xfs": "XFS", "f2fs": "F2FS", "iso9660": "CDFS", "udf": "UDF", "swap": "Swap",
            "crypto_LUKS": "LUKS", "LVM2_member": "LVM", "linux_raid_member": "RAID", "hfsplus": "HFS+",
            "apfs": "APFS", "squashfs": "SquashFS"}


def decode(value):
    """A busctl JSON value ({"type": ..., "data": ...}) as Python data;
    byte arrays (paths, mount points) as text."""
    kind, data = value.get("type"), value.get("data")
    if kind == "ay":
        return bytes(data).rstrip(b"\0").decode("utf-8", "replace")
    if kind == "aay":
        return [bytes(item).rstrip(b"\0").decode("utf-8", "replace") for item in data]
    return data


def objects_from_json(text):
    """{object path: {interface (short name): {property: value}}} from the
    output of GetManagedObjects."""
    reply = json.loads(text)
    raw = reply["data"][0]
    return {path: {iface.removeprefix(PREFIX): {name: decode(value) for name, value in props.items()}
                   for iface, props in ifaces.items()}
            for path, ifaces in raw.items()}


def read_objects():
    out = subprocess.run(["busctl", "--system", "--json=short", "call", SERVICE, "/org/freedesktop/UDisks2",
                          "org.freedesktop.DBus.ObjectManager", "GetManagedObjects"],
                         capture_output=True, text=True, timeout=10, check=True).stdout
    return objects_from_json(out)


def natural_key(text):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def size_text(size, lang="en"):
    """Sizes as Windows' Disk Management writes them: "512 MB",
    "40.00 GB", "1.82 TB" (binary units; Turkish with a decimal comma)."""
    if size >= TIB:
        text = f"{size / TIB:.2f} TB"
    elif size >= GIB:
        text = f"{size / GIB:.2f} GB"
    elif size >= MIB:
        text = f"{round(size / MIB)} MB"
    else:
        text = f"{max(0, round(size / 1024))} KB"
    return text.replace(".", ",") if lang == "tr" else text


def fs_name(block):
    kind, version = block.get("IdType", ""), block.get("IdVersion", "")
    if not kind:
        return "RAW" if block.get("IdUsage", "") == "" else block.get("IdUsage", "")
    if kind == "vfat":
        return "FAT32" if version.upper() == "FAT32" else ("FAT" if not version else version.upper())
    return FS_NAMES.get(kind, kind)


def role_of(partition, table_type):
    kind = str(partition.get("Type", "")).lower()
    if table_type == "dos":
        if partition.get("IsContainer"):
            return "extended"
        role = MBR_ROLES.get(kind, "")
        if role:
            return role
        return "logical" if partition.get("IsContained") else "primary"
    return GPT_ROLES.get(kind, "data")


def free_bytes(mount_points, statvfs=None):
    statvfs = statvfs or os.statvfs        # (the tests run on Windows too, which has no statvfs)
    for point in mount_points:
        try:
            st = statvfs(point)
        except OSError:
            continue
        return st.f_bavail * st.f_frsize
    return None


def is_system(mount_points):
    return any(p in SYSTEM_MOUNTS or p.startswith("/run/live") for p in mount_points)


def gaps(start, end, used, kind):
    """Unallocated stretches between `start` and `end` around the
    (offset, size) pairs in `used`."""
    result, cursor = [], start
    for offset, size in sorted(used):
        if offset - cursor >= MIN_GAP:
            result.append({"kind": kind, "offset": cursor, "size": offset - cursor})
        cursor = max(cursor, offset + size)
    if end - cursor >= MIN_GAP:
        result.append({"kind": kind, "offset": cursor, "size": end - cursor})
    return result


def build(objects, statvfs=None):
    """The disks, in Windows' order and numbering: hard disks and USB
    drives ("Disk 0", "Disk 1", ...), then optical drives ("CD-ROM 0")."""
    blocks = {p: o for p, o in objects.items() if "Block" in o}
    drives = {p: o["Drive"] for p, o in objects.items() if "Drive" in o}
    whole = [(p, o) for p, o in blocks.items()
             if "Partition" not in o and o["Block"].get("Drive", "/") in drives
             and not o["Block"].get("HintIgnore")]
    whole.sort(key=lambda item: (bool(drives[item[1]["Block"]["Drive"]].get("Optical")),
                                 natural_key(item[1]["Block"].get("Device", ""))))
    disks, counters = [], {"disk": 0, "cdrom": 0}
    for path, obj in whole:
        block, drive = obj["Block"], drives[obj["Block"]["Drive"]]
        kind = "cdrom" if drive.get("Optical") else "disk"
        number = counters[kind]
        counters[kind] += 1
        table = obj.get("PartitionTable", {}).get("Type", "") if "PartitionTable" in obj else None
        disk = {"object": path, "device": block.get("Device", ""), "drive": block["Drive"], "kind": kind,
                "number": number, "size": int(block.get("Size", 0) or drive.get("Size", 0)),
                "model": " ".join(x for x in (drive.get("Vendor", ""), drive.get("Model", "")) if x).strip(),
                "removable": bool(drive.get("Removable") or drive.get("MediaRemovable")),
                "table": table, "media": kind != "cdrom" or int(block.get("Size", 0)) > 0,
                "readOnly": bool(block.get("ReadOnly")), "segments": []}
        if kind == "cdrom":
            if disk["media"]:
                disk["segments"].append(volume_segment(path, obj, disk, "optical", 0, disk["size"], statvfs))
        elif table is None:
            if block.get("IdUsage") == "filesystem":       # a file system on the whole disk (USB sticks)
                disk["segments"].append(volume_segment(path, obj, disk, "primary", 0, disk["size"], statvfs))
            else:
                disk["segments"].append({"kind": "unallocated", "offset": 0, "size": disk["size"]})
        else:
            disk["segments"] = partition_segments(path, objects, disk, statvfs)
        for index, segment in enumerate(disk["segments"]):
            segment["index"] = index
            segment["disk"] = path
        disks.append(disk)
    return disks


def partition_segments(table_path, objects, disk, statvfs):
    parts = [(p, o) for p, o in objects.items()
             if "Partition" in o and o["Partition"].get("Table") == table_path]
    parts.sort(key=lambda item: item[1]["Partition"].get("Offset", 0))
    table_type = disk["table"]
    top, inner, container = [], [], None
    for path, obj in parts:
        part = obj["Partition"]
        role = role_of(part, table_type)
        offset, size = int(part.get("Offset", 0)), int(part.get("Size", 0))
        if role == "extended":
            container = (offset, size)
            continue
        segment = volume_segment(path, obj, disk, role, offset, size, statvfs)
        (inner if role == "logical" else top).append(segment)
    used = [(s["offset"], s["size"]) for s in top] + ([container] if container else [])
    segments = top + gaps(MIB, disk["size"], used, "unallocated")
    if container:
        segments += inner + gaps(container[0] + MIB, container[0] + container[1],
                                 [(s["offset"], s["size"]) for s in inner], "free")
    segments.sort(key=lambda s: s["offset"])
    return segments


def volume_segment(path, obj, disk, role, offset, size, statvfs):
    block, part = obj["Block"], obj.get("Partition", {})
    mounts = list(obj.get("Filesystem", {}).get("MountPoints", []) or [])
    return {"kind": "volume", "object": path, "device": block.get("Device", ""), "role": role,
            "offset": offset, "size": size, "number": int(part.get("Number", 0) or 0),
            "label": block.get("IdLabel", ""), "fsType": block.get("IdType", ""), "fs": fs_name(block),
            "uuid": block.get("IdUUID", ""), "name": part.get("Name", ""),
            "hasFilesystem": "Filesystem" in obj, "mounts": mounts, "free": free_bytes(mounts, statvfs),
            "system": is_system(mounts) or role == "efi" and bool(mounts), "readOnly": bool(block.get("ReadOnly")),
            "removable": disk["removable"], "diskKind": disk["kind"], "diskNumber": disk["number"]}


def volumes(disks):
    """The volume list (top pane): every volume of every disk."""
    return [s for d in disks for s in d["segments"] if s["kind"] == "volume"]


# Where the mkfs programs live: a user's PATH has no sbin directories (the
# dialog offered no file system at all in the VM, 2026-10-22). UDisks2 runs
# them as root; the app only asks which exist.
MKFS_PATH = "/usr/sbin:/sbin:/usr/bin:/bin"


def available_formats(which=None):
    """File systems this system can create (their mkfs program exists)."""
    if which is None:
        def which(program):
            return shutil.which(program, path=MKFS_PATH + os.pathsep + os.environ.get("PATH", ""))
    return [fs for fs in FORMATS if any(which(program) for program in MKFS[fs])]


# --- UDisks2 calls -----------------------------------------------------------------------------

def _call(path, interface, method, signature, *args):
    return ["busctl", "--system", "--json=short", "call", SERVICE, path, PREFIX + interface, method,
            signature, *[str(a) for a in args]]


def _options(**options):
    """busctl's a{sv} arguments: count, then name, type, value."""
    items = []
    for name, value in options.items():
        kind = "b" if isinstance(value, bool) else "s"
        items += [name.replace("_", "-"), kind, ("true" if value else "false") if kind == "b" else value]
    return [len(options), *items]


def mount_command(path):
    return _call(path, "Filesystem", "Mount", "a{sv}", 0)


def unmount_command(path):
    return _call(path, "Filesystem", "Unmount", "a{sv}", 0)


def format_options(fstype, label, quick):
    options = {}
    if label:
        options["label"] = label
    if not quick:
        options["erase"] = "zero"
    if fstype == "ext4":
        options["take_ownership"] = True     # the user who formats owns the new volume
    return options


def format_command(path, fstype, label, quick):
    return _call(path, "Block", "Format", "sa{sv}", fstype, *_options(**format_options(fstype, label, quick)))


def delete_command(path):
    return _call(path, "Partition", "Delete", "a{sv}", 0)


def set_label_command(path, label):
    return _call(path, "Filesystem", "SetLabel", "sa{sv}", label, 0)


def initialize_command(path, style):
    """Write an empty partition table: style "gpt" or "dos" (MBR)."""
    return _call(path, "Block", "Format", "sa{sv}", style, 0)


def create_command(table_path, table_type, offset, size, fstype, label, quick):
    """New partition with a file system; size 0 = all of the space from
    `offset` (UDisks2 aligns the partition)."""
    kind = NEW_TYPES.get(table_type, NEW_TYPES["gpt"])[fstype]
    name = label if table_type == "gpt" else ""
    return _call(table_path, "PartitionTable", "CreatePartitionAndFormat", "ttssa{sv}sa{sv}",
                 offset, size, kind, name, 0, fstype, *_options(**format_options(fstype, label, quick)))


def eject_command(drive_path):
    return _call(drive_path, "Drive", "Eject", "a{sv}", 0)


def error_text(stderr):
    """The useful part of busctl's error ("Call failed: ...")."""
    text = (stderr or "").strip().splitlines()
    message = text[-1] if text else ""
    return message.removeprefix("Call failed: ").strip()


def mount_point_of(reply):
    """The mount point from busctl's JSON reply to Mount."""
    try:
        return json.loads(reply)["data"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        return ""
