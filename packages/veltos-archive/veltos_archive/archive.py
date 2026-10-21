"""Archives through 7-Zip (Debian's 7zip, with 7zip-rar for RAR) and
bsdtar (libarchive-tools, for .tar.* archives VeltOS creates).

Everything here builds commands and reads their output; running them is
left to the caller (the window runs them with QProcess to show progress,
the tests run them with subprocess).

Compressed tar archives (.tar.gz, .tar.xz, ...) are listed and extracted
with bsdtar: 7-Zip shows them as a compressed stream holding one .tar
file, while WinRAR (and VeltOS) show what is inside.

7-Zip reads ZIP, 7Z, RAR (all versions, with 7zip-rar), TAR, GZ, BZ2, XZ,
ZST, ISO, CAB, ARJ, LZH, WIM and more; VeltOS creates ZIP, 7Z and
TAR.GZ/TAR.XZ/TAR.ZST archives. Creating RAR archives needs RARLAB's
proprietary rar program, which VeltOS does not ship.
"""

import datetime
import os
import re
from pathlib import Path, PurePosixPath

SEVEN_ZIP = "7z"
BSDTAR = "bsdtar"

# Formats VeltOS creates: key -> (label, file name ending)
CREATE_FORMATS = {
    "zip": ("ZIP", ".zip"),
    "7z": ("7Z", ".7z"),
    "tar.gz": ("TAR.GZ", ".tar.gz"),
    "tar.xz": ("TAR.XZ", ".tar.xz"),
    "tar.zst": ("TAR.ZST", ".tar.zst"),
}
# Compression level names (WinRAR's) -> 7-Zip -mx value
LEVELS = {"store": 0, "fastest": 1, "fast": 3, "normal": 5, "good": 7, "best": 9}
# File name endings 7-Zip opens (for "Open archive" and the desktop file).
ARCHIVE_ENDINGS = (".zip", ".7z", ".rar", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz",
                   ".tar.zst", ".tzst", ".gz", ".bz2", ".xz", ".zst", ".lz", ".lzma", ".z", ".iso", ".cab",
                   ".arj", ".lzh", ".lha", ".wim", ".cpio", ".deb", ".rpm", ".jar", ".apk", ".xpi", ".001")


# Compressed tar archives, handled by bsdtar (see the module text).
TAR_ENDINGS = (".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tbz", ".tar.xz", ".txz", ".tar.zst", ".tzst",
               ".tar.lz", ".tar.lzma", ".tlz", ".tar.z", ".taz")
MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                                      "Nov", "Dec"), 1)}


def is_compressed_tar(path):
    name = str(path).lower()
    return any(name.endswith(e) for e in TAR_ENDINGS)


def tar_type(path):
    name = str(path).lower()
    for ending, label in ((".gz", "TAR.GZ"), (".tgz", "TAR.GZ"), (".bz2", "TAR.BZ2"), (".tbz2", "TAR.BZ2"),
                          (".tbz", "TAR.BZ2"), (".xz", "TAR.XZ"), (".txz", "TAR.XZ"), (".zst", "TAR.ZST"),
                          (".tzst", "TAR.ZST"), (".lz", "TAR.LZ"), (".tlz", "TAR.LZ"), (".lzma", "TAR.LZMA"),
                          (".z", "TAR.Z"), (".taz", "TAR.Z")):
        if name.endswith(ending):
            return label
    return "TAR"


def environment(base=None):
    """7-Zip names files by the locale: UTF-8, but English messages."""
    env = dict(os.environ if base is None else base)
    env["LC_ALL"] = "C.UTF-8"
    env.pop("LANGUAGE", None)
    return env


def password_switch(password):
    # Always pass -p: without it 7-Zip asks on the terminal and hangs.
    return "-p" + (password or "")


def create_format(path):
    """The creation format for an archive name ("x.tar.gz" -> "tar.gz")."""
    name = str(path).lower()
    for key, (_label, ending) in sorted(CREATE_FORMATS.items(), key=lambda kv: -len(kv[1][1])):
        if name.endswith(ending):
            return key
    return ""


def is_archive_name(path):
    name = str(path).lower()
    return any(name.endswith(e) for e in ARCHIVE_ENDINGS)


# --- listing -----------------------------------------------------------------------------------

def list_command(archive, password=""):
    return [SEVEN_ZIP, "l", "-slt", password_switch(password), "--", str(archive)]


def parse_block(lines):
    entry = {}
    for line in lines:
        key, sep, value = line.partition(" = ")
        if sep:
            entry[key.strip()] = value
        elif line.endswith(" ="):
            entry[line[:-2].strip()] = ""
    return entry


def parse_time(text):
    text = text.strip()
    if not text:
        return None
    try:
        return datetime.datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def to_int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return 0


def parse_listing(text):
    """7-Zip's `l -slt` output -> (info, entries, error).

    info: {"type", "physicalSize", "solid", "headersEncrypted", "comment"}
    entries: [{"path", "isDir", "size", "packed", "modified", "crc",
               "encrypted", "method"}]
    error: "" or "password" (encrypted headers, wrong or no password),
           "unsupported" (not an archive 7-Zip can open), or 7-Zip's message.
    """
    error = ""
    for line in text.splitlines():
        if "ERROR:" in line or "Can not open" in line or "Cannot open" in line:
            if "encrypted archive" in line or "Wrong password" in line:
                error = "password"
            elif re.search(r"open the file as (\[[\w.]+\] )?archive", line):
                error = "unsupported"
            elif not error:
                error = line.split(":", 2)[-1].strip() or "error"
    head, sep, body = text.partition("\n----------\n")
    info_lines = head.split("\n--\n", 1)[1].splitlines() if "\n--\n" in head else []
    raw_info = parse_block(info_lines)
    info = {
        "type": raw_info.get("Type", ""),
        "physicalSize": to_int(raw_info.get("Physical Size")),
        "solid": raw_info.get("Solid", "") == "+",
        "headersEncrypted": raw_info.get("Encrypted", "") == "+",
        "comment": raw_info.get("Comment", ""),
        "method": raw_info.get("Method", ""),
    }
    entries = []
    if sep:
        for block in re.split(r"\n\s*\n", body):
            raw = parse_block(block.strip().splitlines())
            if "Path" not in raw:
                continue
            path = raw["Path"].replace("\\", "/").strip("/")
            if not path:
                continue
            entries.append({
                "path": path,
                "isDir": raw.get("Folder") == "+" or raw.get("Attributes", "").startswith("D"),
                "size": to_int(raw.get("Size")),
                "packed": to_int(raw.get("Packed Size")),
                "modified": parse_time(raw.get("Modified", "")),
                "crc": raw.get("CRC", ""),
                "encrypted": raw.get("Encrypted", "") == "+",
                "method": raw.get("Method", ""),
            })
    return info, entries, error


class Tree:
    """The entries of an archive as folders (archives may list a file
    without its folders, e.g. "a/b/c.txt" only)."""

    def __init__(self, entries):
        self.entries = {}
        for entry in entries:
            self.entries[entry["path"]] = dict(entry)
        for path in list(self.entries):
            parent = PurePosixPath(path).parent
            while str(parent) not in (".", ""):
                key = str(parent)
                if key not in self.entries:
                    self.entries[key] = {"path": key, "isDir": True, "size": 0, "packed": 0, "modified": None,
                                         "crc": "", "encrypted": False, "method": ""}
                parent = parent.parent

    def children(self, folder=""):
        folder = folder.strip("/")
        result = []
        for path, entry in self.entries.items():
            parent = str(PurePosixPath(path).parent)
            if (parent if parent != "." else "") == folder:
                item = dict(entry)
                item["name"] = PurePosixPath(path).name
                if item["isDir"]:
                    item["size"], item["packed"] = self.folder_sizes(path)
                result.append(item)
        return result

    def folder_sizes(self, folder):
        prefix = folder + "/"
        size = packed = 0
        for path, entry in self.entries.items():
            if path.startswith(prefix) and not entry["isDir"]:
                size += entry["size"]
                packed += entry["packed"]
        return size, packed

    def is_folder(self, path):
        return path == "" or (path in self.entries and self.entries[path]["isDir"])

    def totals(self):
        files = [e for e in self.entries.values() if not e["isDir"]]
        folders = [e for e in self.entries.values() if e["isDir"]]
        return {"files": len(files), "folders": len(folders),
                "size": sum(e["size"] for e in files), "packed": sum(e["packed"] for e in files),
                "encrypted": any(e["encrypted"] for e in files)}

    def expand(self, paths):
        """Selected items -> the archive paths to name for 7-Zip (folders
        with everything inside)."""
        result = []
        for path in paths:
            result.append(path)
            if self.is_folder(path):
                prefix = path + "/"
                result.extend(p for p in self.entries if p.startswith(prefix))
        return sorted(set(result))


def tar_list_command(archive):
    return [BSDTAR, "-t", "-v", "-f", str(archive)]


def parse_tar_listing(text, path="", now=None):
    """bsdtar's `-tv` output (ls -l like lines) -> (info, entries, error)."""
    now = now or datetime.datetime.now()
    entries = []
    error = ""
    for line in text.splitlines():
        if line.startswith("bsdtar:"):
            if "Unrecognized archive format" in line or "Error opening archive" in line:
                error = "unsupported"
            elif not error:
                error = line.split(":", 1)[1].strip()
            continue
        parts = line.split(None, 8)
        if len(parts) < 9 or not parts[0][:1] in "-dlbcph":
            continue
        mode, _links, _user, _group, size, month, day, time_or_year, name = parts
        if mode.startswith("l") and " -> " in name:
            name = name.split(" -> ", 1)[0]
        modified = None
        if month in MONTHS and day.isdigit():
            try:
                if ":" in time_or_year:
                    hour, minute = (int(x) for x in time_or_year.split(":"))
                    modified = datetime.datetime(now.year, MONTHS[month], int(day), hour, minute)
                    if modified > now + datetime.timedelta(days=1):
                        modified = modified.replace(year=now.year - 1)
                else:
                    modified = datetime.datetime(int(time_or_year), MONTHS[month], int(day))
            except ValueError:
                modified = None
        path_in = name.strip("/")
        if not path_in:
            continue
        entries.append({"path": path_in, "isDir": mode.startswith("d"), "size": to_int(size), "packed": 0,
                        "modified": modified, "crc": "", "encrypted": False, "method": ""})
    info = {"type": tar_type(path), "physicalSize": 0, "solid": True, "headersEncrypted": False,
            "comment": "", "method": ""}
    if entries:
        error = ""
    return info, entries, error


def tar_extract_command(archive, destination, members=(), overwrite="rename"):
    """bsdtar cannot rename: "rename" and "skip" keep existing files."""
    keep = ["-k"] if overwrite in ("rename", "skip") else []
    return [BSDTAR, "-x", "-v", *keep, "-f", str(archive), "-C", str(destination), "--"] + list(members)


def tar_test_command(archive):
    return [BSDTAR, "-t", "-f", str(archive)]


# --- operations --------------------------------------------------------------------------------

def extract_command(archive, destination, members=(), password="", overwrite="rename"):
    """Extract (with the paths inside the archive). overwrite: "rename",
    "overwrite" or "skip" (WinRAR's choices, without the questions)."""
    mode = {"rename": "-aou", "overwrite": "-aoa", "skip": "-aos"}[overwrite]
    return ([SEVEN_ZIP, "x", "-y", mode, "-bsp1", "-bso0", password_switch(password),
             f"-o{destination}", "--", str(archive)] + list(members))


def extract_flat_command(archive, destination, member, password=""):
    """One file without its folders (to view it)."""
    return [SEVEN_ZIP, "e", "-y", "-aoa", "-bso0", password_switch(password), f"-o{destination}", "--",
            str(archive), member]


def test_command(archive, password=""):
    return [SEVEN_ZIP, "t", "-bsp1", "-bso0", password_switch(password), "--", str(archive)]


def delete_command(archive, members):
    return [SEVEN_ZIP, "d", "-bsp1", "-bso0", "--", str(archive)] + list(members)


def add_command(archive, names, fmt, level="normal", password="", encrypt_names=False):
    """(command, needs cwd) to add `names` (relative to the working folder)
    to `archive` in format `fmt`."""
    if fmt in ("zip", "7z"):
        command = [SEVEN_ZIP, "a", f"-t{fmt}", f"-mx={LEVELS.get(level, 5)}", "-bsp1", "-bso0", "-y"]
        if password:
            command.append(password_switch(password))
            if fmt == "7z" and encrypt_names:
                command.append("-mhe=on")
            if fmt == "zip":
                command.append("-mem=AES256")
        return command + ["--", str(archive)] + list(names)
    flag = {"tar.gz": "-z", "tar.xz": "-J", "tar.zst": "--zstd"}[fmt]
    return [BSDTAR, "-c", flag, "-f", str(archive), "--"] + list(names)


def can_delete(info):
    return info.get("type", "").lower() in ("zip", "7z", "tar")


def can_add_to(info):
    return info.get("type", "").lower() in ("zip", "7z", "tar")


def append_command(archive, names, info, password=""):
    """Add files to an existing ZIP/7Z/TAR archive."""
    fmt = info.get("type", "").lower()
    command = [SEVEN_ZIP, "a", f"-t{fmt}", "-bsp1", "-bso0", "-y"]
    if password:
        command.append(password_switch(password))
    return command + ["--", str(archive)] + list(names)


PERCENT = re.compile(r"(\d{1,3})%")


def progress(text):
    """The last percentage in a chunk of 7-Zip's -bsp1 output, or None."""
    found = PERCENT.findall(text)
    return min(100, int(found[-1])) if found else None


def errors(text):
    """(kind, message) of a finished 7-Zip/bsdtar run's output."""
    if "Wrong password" in text or "Can not open encrypted archive" in text:
        return "password", ""
    lines = [line.strip() for line in text.splitlines()
             if line.startswith("ERROR") or "Error:" in line or line.startswith("bsdtar:")]
    if lines:
        return "error", "\n".join(lines[:6])
    return "", ""


# --- names ---------------------------------------------------------------------------------------

def archive_stem(path):
    """"photos.tar.gz" -> "photos" (also .part1.rar, .7z.001)."""
    name = Path(path).name
    for _round in range(2):             # "x.7z.001": ".001", then ".7z"
        lower = name.lower()
        for ending in sorted(ARCHIVE_ENDINGS, key=len, reverse=True):
            if lower.endswith(ending) and len(name) > len(ending):
                name = name[: -len(ending)]
                break
        else:
            break
    name = re.sub(r"\.part0*1$", "", name, flags=re.IGNORECASE)
    return name or "Archive"


def unique_path(path, is_dir=False):
    """"x.zip" -> "x (2).zip" when x.zip exists (Windows' naming)."""
    path = Path(path)
    if not path.exists():
        return path
    stem, suffix = (path.name, "") if is_dir else (archive_stem(path), path.name[len(archive_stem(path)):])
    number = 2
    while True:
        candidate = path.with_name(f"{stem} ({number}){suffix}")
        if not candidate.exists():
            return candidate
        number += 1


def default_archive_name(sources, fmt="zip"):
    """WinRAR's default: the item's name, or the folder's for several."""
    sources = [Path(s) for s in sources]
    if len(sources) == 1:
        base = sources[0].stem if sources[0].is_file() else sources[0].name
    else:
        base = sources[0].parent.name or "Archive"
    return base + CREATE_FORMATS[fmt][1]


def common_parent(paths):
    paths = [Path(p).resolve() for p in paths]
    parent = paths[0].parent
    for p in paths[1:]:
        while parent not in p.parents and parent != p.parent:
            parent = parent.parent
    return parent
