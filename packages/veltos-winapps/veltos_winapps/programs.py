"""Installed Windows programs, as Windows 11 lists them in Settings >
Apps > Installed apps, read straight from the Windows environment's
registry files.

Wine keeps the registry as text (prefix/system.reg for HKEY_LOCAL_MACHINE,
prefix/user.reg for HKEY_CURRENT_USER). Programs register themselves under
Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall (and the 32-bit
Wow6432Node twin), with the name, publisher, version, size, date and the
command that removes them. Reading the files takes milliseconds; starting
Wine's own "Add/Remove Programs" window took many seconds (product owner,
2026-10-22: "it comes very late"). Removing a program still runs its own
uninstaller through Wine (`uninstaller --remove KEY`), as Windows does.

Programs installed in Bottles are listed too (product owner, 2026-11-01:
they were missing and could not be removed), from every bottle's own
registry files, marked "bottles" with the bottle's name; their key is
"bottles:BOTTLE:KEY", and removing one runs Wine's uninstaller inside
that bottle through Bottles' command line (bottles-cli run).
"""

import re
from pathlib import Path, PureWindowsPath

from .winenv import Environment, wine_tool

UNINSTALL_KEYS = (
    "software\\microsoft\\windows\\currentversion\\uninstall\\",
    "software\\wow6432node\\microsoft\\windows\\currentversion\\uninstall\\",
)
# Parts of the Windows environment itself, not programs the user installed.
HIDDEN_NAMES = re.compile(r"^(Wine Mono|Wine Gecko|Wine )", re.IGNORECASE)
VALUE_LINE = re.compile(r'^"((?:[^"\\]|\\.)*)"=(.*)$')


def unescape(text):
    """A string as Wine writes it in .reg files (\\\\, \\", \\n, \\xHHHH)."""
    out, i = [], 0
    while i < len(text):
        char = text[i]
        if char != "\\" or i + 1 >= len(text):
            out.append(char)
            i += 1
            continue
        nxt = text[i + 1]
        if nxt == "x":
            match = re.match(r"[0-9a-fA-F]{1,4}", text[i + 2:])
            if match:
                out.append(chr(int(match.group(0), 16)))
                i += 2 + len(match.group(0))
                continue
        out.append({"n": "\n", "r": "\r", "t": "\t", "0": "\0"}.get(nxt, nxt))
        i += 2
    return "".join(out)


def parse_value(data):
    """A value's data: a string, a number (dword) or None (anything else)."""
    data = data.strip()
    if data.startswith('str(2):"') and data.endswith('"'):
        return unescape(data[8:-1])
    if data.startswith('"') and data.endswith('"'):
        return unescape(data[1:-1])
    if data.startswith("dword:"):
        try:
            return int(data[6:], 16)
        except ValueError:
            return None
    return None


def uninstall_entries(text):
    """{key name: {value name: data}} of the Uninstall keys in a .reg text."""
    entries, current = {}, None
    for line in text.splitlines():
        if line.startswith("["):
            end = line.rfind("]")
            path = unescape(line[1:end]) if end > 0 else ""
            lower = path.lower()
            current = None
            for prefix in UNINSTALL_KEYS:
                if lower.startswith(prefix) and "\\" not in path[len(prefix):]:
                    current = entries.setdefault(path[len(prefix):], {})
                    break
            continue
        if current is None:
            continue
        match = VALUE_LINE.match(line)
        if match:
            current[unescape(match.group(1))] = parse_value(match.group(2))
    return entries


def install_date(value):
    """"20261022" -> "2026-10-22"."""
    if isinstance(value, str) and re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return ""


def windows_path(prefix, path):
    """C:\\Program Files\\x.exe -> the file in the environment (or None)."""
    if not isinstance(path, str) or not path.strip():
        return None
    path = path.strip().strip('"').split(",")[0].strip().strip('"')
    windows = PureWindowsPath(path)
    if not windows.drive:
        return None
    drive = windows.drive[0].lower()
    target = Path(prefix) / f"drive_{drive}" / Path(*windows.parts[1:])
    return target


BOTTLES_APP = "com.usebottles.bottles"


def bottles_root(home=None):
    """Where Flathub's Bottles keeps its bottles."""
    return Path(home or Path.home()) / ".var/app" / BOTTLES_APP / "data/bottles/bottles"


def bottles_prefixes(root=None):
    """The bottles (Wine prefixes) Bottles made, by name."""
    root = Path(root or bottles_root())
    try:
        return [p for p in sorted(root.iterdir()) if (p / "system.reg").is_file()]
    except OSError:
        return []


def programs_in(prefix, runner="wine", bottle=""):
    """{key: program} of one Wine prefix."""
    found = {}
    for name in ("system.reg", "user.reg"):
        try:
            text = (Path(prefix) / name).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for key, values in uninstall_entries(text).items():
            title = values.get("DisplayName")
            if not isinstance(title, str) or not title.strip() or HIDDEN_NAMES.match(title):
                continue
            if values.get("SystemComponent") == 1 or values.get("ParentKeyName"):
                continue
            if not values.get("UninstallString") and values.get("WindowsInstaller") != 1:
                continue
            icon = windows_path(prefix, values.get("DisplayIcon"))
            full_key = key if runner == "wine" else f"bottles:{bottle}:{key}"
            found[full_key] = {
                "key": full_key,
                "name": title.strip(),
                "publisher": values.get("Publisher") or "",
                "version": values.get("DisplayVersion") or "",
                "date": install_date(values.get("InstallDate")),
                "sizeKb": values.get("EstimatedSize") if isinstance(values.get("EstimatedSize"), int) else 0,
                "icon": str(icon) if icon is not None and icon.is_file() else "",
                "runner": runner,
                "bottle": bottle,
            }
    return found


def installed_programs(environment=None, bottles=None):
    """[{key, name, publisher, version, date, sizeKb, icon, runner, bottle}]
    newest first: VeltOS' Windows environment ("wine") and every bottle of
    Bottles ("bottles"); the programs' own entries only (no updates, system
    parts or Wine itself)."""
    environment = environment or Environment()
    found = programs_in(environment.prefix)
    for prefix in bottles_prefixes(bottles):
        found.update(programs_in(prefix, "bottles", prefix.name))
    return sorted(found.values(), key=lambda p: (p["date"], p["name"].casefold()), reverse=True)


def uninstall_command(key, environment=None, bottles=None):
    """The program's own uninstaller, through Wine; the shell waits until
    every Windows process has ended (installers often restart themselves
    from a temporary copy). A Bottles program's through Wine's uninstaller
    inside its bottle (bottles-cli). None for a key that is not a registry
    name."""
    if not isinstance(key, str) or not key or any(c in key for c in "\\\n\0"):
        return None
    if key.startswith("bottles:"):
        _word, bottle, real = (key.split(":", 2) + ["", ""])[:3]
        prefix = Path(bottles or bottles_root()) / bottle
        if not bottle or not real or "/" in bottle or not (prefix / "system.reg").is_file():
            return None
        uninstaller = prefix / "drive_c/windows/system32/uninstaller.exe"
        # bottles-cli takes the program's arguments after "--" (its "run"
        # parser's positional "args", Bottles' cli.py, checked 2026-11-01).
        return ["flatpak", "run", "--command=bottles-cli", BOTTLES_APP, "run", "-b", bottle,
                "-e", str(uninstaller), "--", "--remove", real]
    return ["sh", "-c", '"$1" uninstaller --remove "$2"; "$3" -w', "sh",
            wine_tool("wine"), key, wine_tool("wineserver")]


def forget_removed(environment=None):
    """After a program was uninstalled (from Settings, its own uninstaller or
    Wine's): its Start menu, desktop and file-type entries go
    (shortcuts.remove_stale), and so does VeltOS' record of the
    installation once none of its shortcuts is left, so Settings no longer
    lists it. Returns the removed entries."""
    import json
    from .shortcuts import remove_stale
    environment = environment or Environment()
    removed = remove_stale(environment.prefix)
    for record in sorted(environment.records.glob("*.json")) if environment.records.is_dir() else []:
        try:
            data = json.loads(record.read_text())
        except (OSError, ValueError):
            continue
        links = data.get("shortcuts") or []
        if links and not any(Path(link).exists() for link in links):
            try:
                record.unlink()
                removed.append(str(record))
            except OSError:
                pass
    return removed
