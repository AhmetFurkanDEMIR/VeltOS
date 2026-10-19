"""Folder contents, sorting and formatting for VeltOS File Explorer.

Pure Python (no Qt) so it can be tested anywhere: the Qt model in
models.py wraps these functions. File types and icons come from a
`mime` callable (QMimeDatabase in the app, a stub in tests).
"""

import math
import os
import re
import stat
from pathlib import Path

FOLDER_MIME = "inode/directory"


def natural_key(name):
    """Windows-like ordering: "file2" before "file10", case-insensitive."""
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", name)]


def entry_for(path, st, mime=None):
    """One item of a folder listing (a dict, ready for QML)."""
    path = Path(path)
    is_dir = stat.S_ISDIR(st.st_mode)
    mime_name, type_text, icon = (FOLDER_MIME, "", "folder") if is_dir else ("", "", "")
    if mime is not None:
        mime_name, type_text, icon = mime(str(path), is_dir)
    return {
        "name": path.name,
        "path": str(path),
        "isDir": is_dir,
        "size": 0 if is_dir else st.st_size,
        "modified": st.st_mtime,
        "hidden": path.name.startswith("."),
        "mime": mime_name,
        "type": type_text,
        "icon": icon,
    }


def list_folder(folder, show_hidden=False, mime=None):
    """Items of a folder. Raises OSError (PermissionError, ...) when the
    folder cannot be read; skips items that vanish while listing."""
    items = []
    with os.scandir(folder) as it:
        for de in it:
            if not show_hidden and de.name.startswith("."):
                continue
            try:
                st = de.stat()          # follows links, like Windows shortcuts
            except OSError:
                try:
                    st = de.stat(follow_symlinks=False)
                except OSError:
                    continue
            items.append(entry_for(de.path, st, mime))
    return items


SORT_KEYS = ("name", "modified", "type", "size")


def sort_items(items, key="name", descending=False):
    """Folders first (as Windows), then by the column; ties by name."""
    if key not in SORT_KEYS:
        raise ValueError(key)

    def column(item):
        if key == "name":
            return natural_key(item["name"])
        if key == "type":
            return (item["type"].casefold(), natural_key(item["name"]))
        return (item[key], natural_key(item["name"]))
    folders = sorted((i for i in items if i["isDir"]), key=column, reverse=descending)
    files = sorted((i for i in items if not i["isDir"]), key=column, reverse=descending)
    return folders + files


def size_kb(size):
    """Size as File Explorer's Details view shows it: whole KB, rounded up."""
    return 0 if size == 0 else max(1, math.ceil(size / 1024))


def human_size(size):
    """1.17 MB style, as File Explorer's status bar and properties."""
    if size < 1024:
        return f"{size} bytes"
    value = float(size)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024
        if value < 1024 or unit == "TB":
            if value >= 100:
                return f"{value:.0f} {unit}"
            if value >= 10:
                return f"{value:.1f} {unit}"
            return f"{value:.2f} {unit}"
    return f"{size} bytes"


def split_ext(name, is_dir=False):
    """("report", ".pdf"); folders and ".hidden" names have no extension."""
    if is_dir or "." not in name.lstrip("."):
        return name, ""
    stem, ext = name.rsplit(".", 1)
    return stem, "." + ext


def unique_name(folder, name, is_dir=False):
    """A name not yet used in the folder: "New folder", "New folder (2)",
    ... and "a.txt", "a (2).txt"."""
    if not (Path(folder) / name).exists():
        return name
    stem, ext = split_ext(name, is_dir)
    for n in range(2, 10000):
        candidate = f"{stem} ({n}){ext}"
        if not (Path(folder) / candidate).exists():
            return candidate
    raise FileExistsError(name)


def copy_name(folder, name, is_dir=False):
    """Name for a copy pasted into the same folder: "a - Copy.txt",
    "a - Copy (2).txt" (Windows)."""
    stem, ext = split_ext(name, is_dir)
    candidate = f"{stem} - Copy{ext}"
    n = 2
    while (Path(folder) / candidate).exists():
        candidate = f"{stem} - Copy ({n}){ext}"
        n += 1
    return candidate


INVALID_NAME = re.compile(r"[/\x00]")


def check_new_name(folder, old, new):
    """None if `old` may be renamed to `new` in `folder`, else the reason:
    "empty", "invalid", "exists"."""
    new = new.strip()
    if not new or new in (".", ".."):
        return "empty"
    if INVALID_NAME.search(new) or len(new.encode("utf-8")) > 255:
        return "invalid"
    if new != old and (Path(folder) / new).exists() and new.casefold() != old.casefold():
        return "exists"
    return None


def search(folder, query, show_hidden=False, mime=None, cancelled=lambda: False, limit=2000):
    """Items below `folder` whose name contains every word of the query
    (case-insensitive), like File Explorer's search box."""
    words = query.casefold().split()
    results = []
    if not words:
        return results
    for root, dirs, files in os.walk(folder, onerror=lambda _e: None):
        if cancelled():
            break
        if not show_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]
        for name in dirs + files:
            folded = name.casefold()
            if all(w in folded for w in words):
                path = os.path.join(root, name)
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                item = entry_for(path, st, mime)
                item["folder"] = root
                results.append(item)
                if len(results) >= limit:
                    return results
    return results
