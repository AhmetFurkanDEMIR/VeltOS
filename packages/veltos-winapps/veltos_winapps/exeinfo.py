"""Inspect a Windows program file before running it.

Reads the PE headers and resources of an .exe (with python3-pefile) to find
what a Windows user would see in Explorer: product name, publisher,
version and icon, plus what VeltOS needs to decide how to run it: 32/64-bit,
.NET or native, and whether it is an installer (and which kind). Batch
files (.bat, .cmd) are text files run by Windows' command interpreter.
"""

import io
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

# Byte signatures of common installer engines (searched near the start of
# the file, where the installer stub and its resources live).
INSTALLER_SIGNATURES = [
    (b"Inno Setup", "Inno Setup"),
    (b"Nullsoft.NSIS", "NSIS"),
    (b"NullsoftInst", "NSIS"),
    (b"InstallShield", "InstallShield"),
    (b"WiseMain", "Wise"),
    (b"Setup Factory", "Setup Factory"),
    (b"Advanced Installer", "Advanced Installer"),
    (b"WixBundleManifest", "WiX"),
    (b"Squirrel.Windows", "Squirrel"),
    (b"7zS.sfx", "7-Zip SFX"),
    (b";!@Install@!UTF-8!", "7-Zip SFX"),
]
NAME_HINTS = re.compile(r"(setup|install|installer|_inst\b|redist|vc_?redist)", re.IGNORECASE)
SCAN_BYTES = 24 * 1024 * 1024

MACHINES = {0x14C: "x86", 0x8664: "x64", 0xAA64: "arm64"}
BATCH_SUFFIXES = (".bat", ".cmd")
RT_ICON, RT_GROUP_ICON = 3, 14


@dataclass
class ExeInfo:
    path: Path
    kind: str                      # "exe", "msi" or "batch"
    name: str
    publisher: str = ""
    version: str = ""
    description: str = ""
    arch: str = "unknown"          # x86, x64, arm64, unknown
    dotnet: bool = False
    gui: bool = True
    installer: str = ""            # installer engine, "" if not an installer
    icon_png: bytes = field(default=b"", repr=False)
    valid: bool = True             # False if the file is not a usable PE/MSI

    @property
    def is_installer(self):
        return bool(self.installer)


def _clean(text):
    return " ".join(str(text).replace("\x00", " ").split())


def _version_strings(pe):
    strings = {}
    for info in getattr(pe, "FileInfo", None) or []:
        for entry in info:
            for table in getattr(entry, "StringTable", []) or []:
                for key, value in table.entries.items():
                    k = key.decode("utf-8", "ignore") if isinstance(key, bytes) else key
                    v = value.decode("utf-8", "ignore") if isinstance(value, bytes) else value
                    if _clean(v):
                        strings.setdefault(k, _clean(v))
    return strings


def _resource_entries(pe, type_id):
    root = getattr(pe, "DIRECTORY_ENTRY_RESOURCE", None)
    if root is None:
        return []
    for type_entry in root.entries:
        if type_entry.id == type_id:
            found = []
            for name_entry in type_entry.directory.entries:
                for lang_entry in name_entry.directory.entries:
                    found.append((name_entry.id, lang_entry.data.struct))
            return found
    return []


def extract_icon_png(pe, size=256):
    """Largest image of the first icon group, as PNG bytes (b"" if none)."""
    groups = _resource_entries(pe, RT_GROUP_ICON)
    icons = {res_id: entry for res_id, entry in _resource_entries(pe, RT_ICON)}
    if not groups or not icons:
        return b""
    data = pe.get_memory_mapped_image()
    _, group = groups[0]
    raw = data[group.OffsetToData:group.OffsetToData + group.Size]
    if len(raw) < 6:
        return b""
    _reserved, _type, count = struct.unpack_from("<HHH", raw, 0)
    entries, images = [], []
    for i in range(count):
        off = 6 + i * 14
        if off + 14 > len(raw):
            break
        w, h, colors, res, planes, bits, size_bytes, icon_id = struct.unpack_from("<BBBBHHIH", raw, off)
        icon = icons.get(icon_id)
        if icon is None:
            continue
        entries.append((w, h, colors, res, planes, bits))
        images.append(data[icon.OffsetToData:icon.OffsetToData + icon.Size])
    if not images:
        return b""
    # Re-assemble a standalone .ico file and let Pillow decode it.
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    directory = b""
    for (w, h, colors, res, planes, bits), image in zip(entries, images):
        directory += struct.pack("<BBBBHHII", w, h, colors, res, planes, bits, len(image), offset)
        offset += len(image)
    ico = header + directory + b"".join(images)
    try:
        from PIL import Image
        with Image.open(io.BytesIO(ico)) as img:
            sizes = sorted(img.info.get("sizes", {img.size}), key=lambda s: s[0] * s[1])
            img.size = sizes[-1]
            out = io.BytesIO()
            img.convert("RGBA").resize((size, size)).save(out, "PNG")
            return out.getvalue()
    except Exception:  # broken or unusual icon data: no icon rather than a crash
        return b""


def detect_installer(path, head_bytes, version_strings):
    for signature, engine in INSTALLER_SIGNATURES:
        if signature in head_bytes:
            return engine
    description = " ".join(version_strings.get(k, "") for k in ("FileDescription", "ProductName"))
    if re.search(r"\b(setup|installer|install)\b", description, re.IGNORECASE):
        return "generic"
    if NAME_HINTS.search(path.stem):
        return "generic"
    return ""


def inspect(path):
    """Describe the Windows program at `path` (never raises for bad files)."""
    path = Path(path)
    fallback_name = path.stem.replace("_", " ").replace("-", " ").strip() or path.name
    if path.suffix.lower() == ".msi":
        return ExeInfo(path=path, kind="msi", name=fallback_name, installer="MSI")
    if path.suffix.lower() in BATCH_SUFFIXES:
        # Windows shows a batch file by its file name. A file with NUL bytes
        # is not a batch file (cmd would stop at them).
        try:
            with open(path, "rb") as fh:
                valid = b"\0" not in fh.read(64 * 1024)
        except OSError:
            valid = False
        return ExeInfo(path=path, kind="batch", name=path.name, gui=False, valid=valid)

    try:
        import pefile
        pe = pefile.PE(str(path), fast_load=True)
        pe.parse_data_directories(directories=[
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"],
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR"],
        ])
    except Exception:
        return ExeInfo(path=path, kind="exe", name=fallback_name, valid=False)

    strings = _version_strings(pe)
    with open(path, "rb") as fh:
        head = fh.read(SCAN_BYTES)
    info = ExeInfo(
        path=path,
        kind="exe",
        name=strings.get("ProductName") or strings.get("FileDescription") or fallback_name,
        publisher=strings.get("CompanyName", ""),
        version=strings.get("ProductVersion") or strings.get("FileVersion", ""),
        description=strings.get("FileDescription", ""),
        arch=MACHINES.get(pe.FILE_HEADER.Machine, "unknown"),
        dotnet=hasattr(pe, "DIRECTORY_ENTRY_COM_DESCRIPTOR"),
        gui=pe.OPTIONAL_HEADER.Subsystem == 2,  # IMAGE_SUBSYSTEM_WINDOWS_GUI
        installer=detect_installer(path, head, strings),
    )
    info.icon_png = extract_icon_png(pe)
    pe.close()
    return info
