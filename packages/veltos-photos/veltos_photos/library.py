"""The pictures and videos of VeltOS Photos: the folders (Pictures and
Videos, plus those the user adds), each item's date (when it was taken,
from EXIF, else the file's time) and the gallery grouped by month, newest
first, as Windows 11 Photos shows it."""

import datetime
import json
import os
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".avif", ".heic",
                  ".heif", ".jxl", ".ico", ".svg"}
VIDEO_SUFFIXES = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".wmv", ".3gp", ".mpg", ".mpeg", ".ogv"}
# Folders that are not worth scanning (thumbnail caches, Wine prefixes).
SKIP_DIRS = {".thumbnails", ".cache", ".Trash", ".git", "node_modules", "drive_c"}
MAX_ITEMS = 50000


def user_dir(name, fallback):
    """An XDG user folder (PICTURES, VIDEOS) from user-dirs.dirs."""
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "user-dirs.dirs"
    try:
        for line in config.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"XDG_{name}_DIR="):
                value = line.split("=", 1)[1].strip().strip('"')
                return Path(value.replace("$HOME", str(home)))
    except OSError:
        pass
    return home / fallback


def default_folders():
    return [user_dir("PICTURES", "Pictures"), user_dir("VIDEOS", "Videos")]


def kind_of(path):
    suffix = Path(path).suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return ""


def exif_date(path):
    """When a photo was taken (EXIF DateTimeOriginal), or None."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            value = exif.get_ifd(0x8769).get(0x9003) or exif.get(0x0132)
    except Exception:  # broken or exotic files: use the file time
        return None
    if not value:
        return None
    try:
        return datetime.datetime.strptime(str(value).strip()[:19], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def scan(folders, cache=None):
    """Every picture and video in the folders: [{path, kind, date (ISO),
    size}], newest first. `cache` maps path -> previous entry; entries
    whose file did not change are reused (EXIF is read once)."""
    cache = cache or {}
    items, seen = [], set()
    for folder in folders:
        folder = Path(folder)
        for root, dirs, files in os.walk(folder, followlinks=False):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for name in files:
                kind = kind_of(name)
                if not kind:
                    continue
                path = os.path.join(root, name)
                if path in seen:
                    continue
                seen.add(path)
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                old = cache.get(path)
                if old and old.get("mtime") == int(st.st_mtime) and old.get("size") == st.st_size:
                    items.append(old)
                    continue
                taken = exif_date(path) if kind == "image" and Path(name).suffix.lower() in (
                    ".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".webp", ".png") else None
                date = taken or datetime.datetime.fromtimestamp(st.st_mtime)
                items.append({"path": path, "kind": kind, "date": date.isoformat(timespec="seconds"),
                              "taken": taken is not None, "mtime": int(st.st_mtime), "size": st.st_size})
                if len(items) >= MAX_ITEMS:
                    break
    items.sort(key=lambda item: (item["date"], item["path"]), reverse=True)
    return items


def load_cache(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {item["path"]: item for item in data if isinstance(item, dict) and "path" in item}
    except (OSError, ValueError, TypeError):
        return {}


def save_cache(path, items):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def month_key(item):
    return item["date"][:7]


def rows(items, columns, month_title):
    """The gallery as rows for a list view: a heading per month, then rows
    of `columns` items. `month_title(year, month)` names the heading."""
    columns = max(1, columns)
    result, current, row = [], None, []
    for item in items:
        key = month_key(item)
        if key != current:
            if row:
                result.append({"type": "row", "items": row})
                row = []
            current = key
            year, month = int(key[:4]), int(key[5:7])
            result.append({"type": "header", "title": month_title(year, month), "items": []})
        row.append(item)
        if len(row) == columns:
            result.append({"type": "row", "items": row})
            row = []
    if row:
        result.append({"type": "row", "items": row})
    return result


def siblings(path):
    """The pictures and videos in a file's folder, by name (the viewer's
    filmstrip when Photos opens a file)."""
    folder = Path(path).parent
    try:
        names = sorted((p for p in folder.iterdir() if p.is_file() and kind_of(p.name)),
                       key=lambda p: p.name.lower())
    except OSError:
        names = [Path(path)]
    result = []
    for p in names:
        try:
            st = p.stat()
        except OSError:
            continue
        result.append({"path": str(p), "kind": kind_of(p.name),
                       "date": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                       "taken": False, "mtime": int(st.st_mtime), "size": st.st_size})
    return result
