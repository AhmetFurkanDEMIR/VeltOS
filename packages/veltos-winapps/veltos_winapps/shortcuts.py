"""Start menu and desktop shortcuts for Windows programs.

Wine adds shortcuts created by installers to the Linux menus itself
(~/.local/share/applications/wine/...), so they appear in VeltOS Start like
any other app. This module finds the ones an installer just created, and
removes the ones whose program was uninstalled.
"""

import configparser
import os
import re
import shlex
import subprocess
from pathlib import Path

from .winenv import data_home


def desktop_dir():
    try:
        out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True,
                             timeout=5).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return Path.home() / "Desktop"


def watched_dirs():
    return [data_home() / "applications", desktop_dir()]


def snapshot(dirs=None):
    """{path: mtime} of every .desktop file below the given directories."""
    state = {}
    for directory in dirs or watched_dirs():
        if directory.is_dir():
            for path in directory.rglob("*.desktop"):
                try:
                    state[path] = path.stat().st_mtime
                except OSError:
                    pass
    return state


def changed(before, after):
    return sorted(p for p, mtime in after.items() if before.get(p) != mtime)


def read_entry(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
        entry = parser["Desktop Entry"]
    except (configparser.Error, KeyError, UnicodeDecodeError):
        return None
    return {"path": str(path), "name": entry.get("Name", Path(path).stem),
            "icon": entry.get("Icon", ""), "exec": entry.get("Exec", "")}


def windows_target(exec_line, prefix):
    """The file a Wine shortcut of this environment opens, as a path on
    VeltOS: the .lnk of a Start menu or desktop entry ("wine C:\\\\...\\\\x.lnk"
    or "wine start /unix /home/.../x.lnk") or the program of a file type
    (wine-extension-*.desktop). None for other entries."""
    if str(prefix) not in exec_line:
        return None
    # Desktop entry values escape "\" as "\\"; the Exec line then quotes
    # spaces and backslashes again ("Start\ Menu", "C:\\ProgramData").
    try:
        words = shlex.split(exec_line.replace("\\\\", "\\"))
    except ValueError:
        return None
    for word in words:
        if re.match(r"^[A-Za-z]:\\", word) and re.search(r"\.(lnk|exe|msi|bat|cmd)$", word, re.IGNORECASE):
            from .programs import windows_path
            return windows_path(prefix, word)
        if word.startswith("/") and word.lower().endswith(".lnk"):
            return Path(word)
    return None


def file_type(exec_line, prefix):
    """The ProgID a file-type entry of this environment opens with
    ("wine start /ProgIDOpen 7-Zip.7z %f", winemenubuilder), or None."""
    if str(prefix) not in exec_line:
        return None
    try:
        words = shlex.split(exec_line.replace("\\\\", "\\"))
    except ValueError:
        return None
    for index, word in enumerate(words[:-1]):
        if word.lower() == "/progidopen":
            return words[index + 1]
    return None


def registry_classes(prefix):
    """The ProgIDs registered in the environment (Software\\Classes of
    system.reg and user.reg), in lower case; None if neither file can be
    read."""
    found, read = set(), False
    for name in ("system.reg", "user.reg"):
        try:
            text = (Path(prefix) / name).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        read = True
        # A ProgID's own key, or the first part of one of its subkeys (Wine
        # writes a key without values only when it has no subkeys).
        for match in re.finditer(r"^\[Software\\\\Classes\\\\([^\\\]]+)", text, re.IGNORECASE | re.MULTILINE):
            found.add(match.group(1).casefold())
    return found if read else None


def program_gone(exec_line, prefix, classes=None):
    """Whether a Wine entry of this environment opens a shortcut, program
    or file type that no longer exists."""
    target = windows_target(exec_line, prefix)
    if target is not None:
        return not _exists(target)
    progid = file_type(exec_line, prefix)
    return progid is not None and classes is not None and progid.casefold() not in classes


def _exists(path):
    """Whether a file exists, ignoring case as Windows does."""
    if path.exists():
        return True
    parent = path.parent
    try:
        return parent.is_dir() and any(p.name.casefold() == path.name.casefold() for p in parent.iterdir())
    except OSError:
        return False


def remove_stale(prefix, home=None, desktop=None):
    """Removes Wine's menu, desktop and file-type entries of this environment
    whose shortcut or program no longer exists (an uninstaller removed it;
    Wine's menu builder only ever adds entries), with their .menu and
    .directory files, empty menu folders and icons nobody uses any more,
    as Windows' Start menu forgets an uninstalled program. Returns the
    removed entries."""
    data = Path(home) / ".local/share" if home else data_home()
    config = Path(home) / ".config" if home else Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    apps = data / "applications"
    wine_menu = apps / "wine"
    candidates = list(wine_menu.rglob("*.desktop")) if wine_menu.is_dir() else []
    candidates += list(apps.glob("wine-extension-*.desktop")) if apps.is_dir() else []
    desktop = Path(desktop) if desktop else desktop_dir()
    candidates += list(desktop.glob("*.desktop")) if desktop.is_dir() else []
    removed, icons, mime_types = [], set(), False
    classes = registry_classes(prefix)
    for path in candidates:
        entry = read_entry(path)
        if not entry or not program_gone(entry["exec"], prefix, classes):
            continue
        try:
            path.unlink()
        except OSError:
            continue
        removed.append(str(path))
        if entry["icon"]:
            icons.add(entry["icon"])
        if path.name.startswith("wine-extension-"):
            # The file type Wine made up for an extension nobody else knew.
            xml = data / "mime/packages" / f"x-{path.stem}.xml"
            try:
                xml.unlink()
                mime_types = True
            except OSError:
                pass
        if wine_menu in path.parents:
            relative = path.relative_to(wine_menu).with_suffix("")
            menu = config / "menus/applications-merged" / f"wine-{relative.as_posix().replace('/', '-')}.menu"
            try:
                menu.unlink()
            except OSError:
                pass
    if wine_menu.is_dir():
        for folder in sorted((p for p in wine_menu.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
            if any(folder.iterdir()):
                continue
            folder.rmdir()
            relative = folder.relative_to(wine_menu).as_posix().replace("/", "-")
            try:
                (data / "desktop-directories" / f"wine-{relative}.directory").unlink()
            except OSError:
                pass
    if icons:
        still_used = set()
        for path in candidates:
            entry = read_entry(path) if path.exists() else None
            if entry:
                still_used.add(entry["icon"])
        for icon in icons - still_used:
            # winemenubuilder's own icons ("1DA0_7-zip.0"), never a theme's.
            if not re.match(r"^[0-9A-F]{4}_", icon):
                continue
            for png in (data / "icons/hicolor").glob(f"*/apps/{icon}.png"):
                try:
                    png.unlink()
                except OSError:
                    pass
    if mime_types:
        try:
            subprocess.run(["update-mime-database", str(data / "mime")], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
    return removed


def entries_for_prefix(paths, prefix):
    """Shortcuts among `paths` that start a program in the given Wine prefix."""
    found, seen = [], set()
    for path in paths:
        entry = read_entry(path)
        if entry and str(prefix) in entry["exec"] and entry["name"] not in seen:
            seen.add(entry["name"])
            found.append(entry)
    return found
