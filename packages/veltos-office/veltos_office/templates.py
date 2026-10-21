"""Templates shown on the Home and New pages: VeltOS' own (built by
tools/make-templates.py into /usr/share/veltos-office/templates), the ones
that ship with LibreOffice, and the user's (LibreOffice's user template
folder). Thumbnails are the pictures stored inside the template files
(ODF: Thumbnails/thumbnail.png; Office Open XML: docProps/thumbnail.jpeg),
copied once into ~/.cache/veltos-office/thumbnails."""

import hashlib
import os
import zipfile
from pathlib import Path

from . import strings

LIBREOFFICE_TEMPLATES = Path("/usr/lib/libreoffice/share/template/common")
VELTOS_TEMPLATES = Path("/usr/share/veltos-office/templates")
# LibreOffice's template categories per app (its Calc folder is empty).
LIBREOFFICE_CATEGORIES = {
    "word": ("officorr", "offimisc", "personal"),
    "sheet": (),
    "slides": ("presnt",),
}
EXTENSIONS = {
    "word": {".ott", ".dotx", ".dot", ".odt"},
    "sheet": {".ots", ".xltx", ".xlt", ".ods"},
    "slides": {".otp", ".potx", ".pot", ".odp"},
}
THUMBNAIL_MEMBERS = ("Thumbnails/thumbnail.png", "docProps/thumbnail.jpeg", "docProps/thumbnail.png")


def user_template_dir(home=None):
    return Path(home or Path.home()) / ".config/libreoffice/4/user/template"


def cache_dir(home=None):
    base = os.environ.get("XDG_CACHE_HOME") if home is None else None
    return Path(base) / "veltos-office/thumbnails" if base else Path(home or Path.home()) / ".cache/veltos-office/thumbnails"


def thumbnail(template, cache):
    """Path of the template's thumbnail in the cache ("" if it has none)."""
    try:
        stamp = f"{template}|{os.path.getmtime(template)}|{os.path.getsize(template)}"
    except OSError:
        return ""
    key = hashlib.sha1(stamp.encode("utf-8")).hexdigest()
    for member in THUMBNAIL_MEMBERS:
        target = Path(cache) / (key + Path(member).suffix)
        if target.exists():
            return str(target)
    try:
        with zipfile.ZipFile(template) as archive:
            names = set(archive.namelist())
            for member in THUMBNAIL_MEMBERS:
                if member in names:
                    data = archive.read(member)
                    target = Path(cache) / (key + Path(member).suffix)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    tmp = target.with_suffix(target.suffix + ".tmp")
                    tmp.write_bytes(data)
                    tmp.replace(target)
                    return str(target)
    except (OSError, zipfile.BadZipFile, KeyError):
        return ""
    return ""


def files_in(folder, kind):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    found = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in EXTENSIONS[kind]:
            found.append(path)
    return found


def catalogue(kind, lang, veltos_dir=None, libreoffice_dir=None, user_dir=None, cache=None, with_thumbnails=True):
    """[{"id", "name", "path", "source", "thumbnail"}]: VeltOS' templates,
    then LibreOffice's, then the user's own."""
    veltos_dir = Path(veltos_dir) if veltos_dir is not None else VELTOS_TEMPLATES / kind
    libreoffice_dir = Path(libreoffice_dir) if libreoffice_dir is not None else LIBREOFFICE_TEMPLATES
    user_dir = Path(user_dir) if user_dir is not None else user_template_dir()
    cache = cache if cache is not None else cache_dir()
    groups = [("veltos", files_in(veltos_dir, kind))]
    for category in LIBREOFFICE_CATEGORIES[kind]:
        groups.append(("libreoffice", files_in(libreoffice_dir / category, kind)))
    groups.append(("you", files_in(user_dir, kind)))
    result, seen = [], set()
    for source, paths in groups:
        for path in paths:
            if path.stem in seen:
                continue
            seen.add(path.stem)
            result.append({
                "id": str(path),
                "name": strings.template_name(lang, path.stem),
                "path": str(path),
                "source": source,
                "thumbnail": ("file://" + thumbnail(path, cache)) if with_thumbnails and thumbnail(path, cache) else "",
            })
    return result


def search(items, query):
    query = query.strip().casefold()
    if not query:
        return list(items)
    return [item for item in items if query in item["name"].casefold() or query in Path(item["path"]).stem.casefold()]
