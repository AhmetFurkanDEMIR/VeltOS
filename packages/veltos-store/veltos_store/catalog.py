"""VeltOS Store catalogue: the desktop apps that Debian's AppStream data
(DEP-11, downloaded by apt into /var/lib/swcatalog) describes.

AppStream is read through its GObject binding (gir1.2-appstream-1.0) in
load_appstream(); everything else works on plain dicts ("entries"), so the
tests use lists of dicts:

    id, name, summary, pkg, categories, keywords, icon, developer,
    license, homepage, desktop, quality
"""

import re
from pathlib import Path

ICON_ROOTS = (Path("/var/lib/swcatalog/icons"), Path("/usr/share/swcatalog/icons"))
CATALOG_DIR = Path("/var/lib/swcatalog/yaml")
# VeltOS's names for KDE programs and the ones it hides (update-app-names
# in veltos-desktop).
VELTOS_APPS = Path("/var/lib/veltos/xdg/applications")
# Older data than this is refreshed when the Store starts: screenshot
# addresses change with package updates (stale ones gave 404, VM test).
MAX_AGE_DAYS = 2

# Store categories, Microsoft Store style: id -> (AppStream categories,
# English, Turkish, icon). An app belongs to the first one that matches.
CATEGORIES = [
    ("games", {"Game"}, "Games", "Oyunlar", "applications-games-symbolic"),
    ("productivity", {"Office", "WordProcessor", "Spreadsheet", "Presentation", "Calendar",
                      "ContactManagement", "Finance", "ProjectManagement"},
     "Productivity", "Verimlilik", "x-office-document-symbolic"),
    ("photo", {"Graphics", "Photography", "2DGraphics", "3DGraphics", "RasterGraphics",
               "VectorGraphics", "AudioVideoEditing", "Scanning"},
     "Photo & design", "Fotoğraf ve tasarım", "camera-photo-symbolic"),
    ("music", {"AudioVideo", "Audio", "Video", "Music", "Player", "Recorder", "Midi", "Mixer", "TV"},
     "Music & video", "Müzik ve video", "audio-x-generic-symbolic"),
    ("social", {"Network", "Chat", "InstantMessaging", "Email", "WebBrowser", "IRCClient",
                "VideoConference", "Feed", "News"},
     "Internet & social", "İnternet ve sosyal", "internet-web-browser-symbolic"),
    ("developer", {"Development", "IDE", "Debugger", "RevisionControl", "WebDevelopment"},
     "Developer tools", "Geliştirici araçları", "applications-development-symbolic"),
    ("education", {"Education", "Science", "Math", "Astronomy", "Geography", "Languages"},
     "Education", "Eğitim", "applications-science-symbolic"),
    ("utilities", {"Utility", "System", "FileTools", "Archiving", "Security", "Settings",
                   "TextEditor", "Accessibility", "Monitor"},
     "Utilities & tools", "Yardımcı programlar ve araçlar", "applications-utilities-symbolic"),
]
CATEGORY_IDS = [c[0] for c in CATEGORIES]

# Curated by package name; only those in the catalogue are shown. The
# banner colours are VeltOS's own.
FEATURED = [
    ("libreoffice-writer", "#2F5EE6", "#5B3FE0"),
    ("gimp", "#6A4FE8", "#2FA8F0"),
    ("vlc", "#E8662F", "#C2398A"),
    ("krita", "#1E8FE0", "#4F7CFF"),
    ("obs-studio", "#3A3F58", "#5B3FE0"),
]
ESSENTIALS = ["libreoffice-writer", "libreoffice-calc", "libreoffice-impress", "vlc", "gimp",
              "thunderbird", "inkscape", "audacity", "obs-studio", "krita", "kdenlive",
              "shotwell", "transmission-qt", "keepassxc", "filezilla"]
CREATIVE = ["krita", "inkscape", "gimp", "blender", "kdenlive", "darktable", "shotcut",
            "audacity", "obs-studio", "openshot-qt", "lmms", "ardour", "rawtherapee",
            "digikam", "scribus"]
GAMES = ["supertuxkart", "0ad", "luanti", "minetest", "supertux", "wesnoth", "warzone2100",
         "frozen-bubble", "openttd", "hedgewars", "pingus", "neverball", "lutris",
         "xmoto", "openarena", "teeworlds", "kapman", "kpat", "kmines", "gnome-mines"]

ALLOWED_TAGS = {"p", "ul", "ol", "li", "em", "code", "b", "i", "br"}


def category_of(categories):
    """The Store category id of an app's AppStream categories."""
    wanted = set(categories or ())
    for cid, appstream, *_rest in CATEGORIES:
        if wanted & appstream:
            return cid
    return "utilities"


def category_title(cid, lang):
    for c in CATEGORIES:
        if c[0] == cid:
            return c[3] if lang == "tr" else c[2]
    return cid


def sanitise_description(markup):
    """AppStream description markup as Qt rich text: only paragraphs,
    lists and emphasis survive; attributes and other tags are dropped."""
    if not markup:
        return ""

    def tag(match):
        closing, name = match.group(1), match.group(2).lower()
        return f"<{closing}{name}>" if name in ALLOWED_TAGS else ""

    return re.sub(r"<(/?)([A-Za-z0-9]+)[^>]*>", tag, markup).strip()


def apply_veltos_names(entries, lang, directory=None):
    """Entries with the names VeltOS gives programs ("Archive Manager" for
    Ark), without the programs VeltOS hides (Dolphin, Discover, ...)."""
    import configparser
    directory = directory or VELTOS_APPS
    result = []
    for entry in entries:
        desktop = entry.get("desktop") or ""
        path = directory / desktop if desktop else None
        if path and path.is_file():
            parser = configparser.RawConfigParser(interpolation=None, strict=False)
            parser.optionxform = str
            try:
                parser.read(path, encoding="utf-8")
                group = parser["Desktop Entry"]
            except (configparser.Error, KeyError, UnicodeDecodeError):
                result.append(entry)
                continue
            if group.get("NoDisplay", "").lower() == "true" or group.get("Hidden", "").lower() == "true":
                continue
            name = group.get(f"Name[{lang}]") if lang != "en" else None
            entry = dict(entry, name=name or group.get("Name") or entry["name"])
        result.append(entry)
    return result


def catalog_age_days(directory=None, now=None):
    """Age of the newest AppStream file in days (None if there is none)."""
    import time
    directory = directory or CATALOG_DIR
    try:
        newest = max(f.stat().st_mtime for f in directory.iterdir() if f.is_file())
    except (OSError, ValueError):
        return None
    return ((now or time.time()) - newest) / 86400


def score(entry):
    """How well an app can be shown (icon, screenshots, text)."""
    return entry.get("quality", 0)


class Catalog:
    """Searchable list of entries (see the module documentation)."""

    def __init__(self, entries):
        self.entries = {}
        for entry in entries:
            entry = dict(entry)
            entry["category"] = category_of(entry.get("categories"))
            self.entries.setdefault(entry["id"], entry)
        self.by_pkg = {}
        for entry in sorted(self.entries.values(), key=lambda e: -score(e)):
            self.by_pkg.setdefault(entry["pkg"], entry)

    def __len__(self):
        return len(self.entries)

    def get(self, app_id):
        return self.entries.get(app_id)

    def package(self, pkg):
        return self.by_pkg.get(pkg)

    def picked(self, packages, limit=None):
        found = [self.by_pkg[p] for p in packages if p in self.by_pkg]
        return found[:limit] if limit else found

    def in_category(self, cid=None, games=False, limit=None):
        """Apps of one category (or all non-game apps / all games), the best
        described first."""
        if cid:
            items = [e for e in self.entries.values() if e["category"] == cid]
        else:
            items = [e for e in self.entries.values() if (e["category"] == "games") == games]
        items.sort(key=lambda e: (-score(e), e["name"].lower()))
        return items[:limit] if limit else items

    def search(self, text, limit=60):
        words = [w for w in re.split(r"\s+", text.strip().lower()) if w]
        if not words:
            return []
        results = []
        for entry in self.entries.values():
            name = entry["name"].lower()
            haystack = " ".join([name, entry.get("summary", "").lower(), entry["pkg"].lower(),
                                 " ".join(entry.get("keywords", ())).lower()])
            if not all(w in haystack for w in words):
                continue
            phrase = " ".join(words)
            rank = (0 if name == phrase else 1 if name.startswith(phrase)
                    else 2 if phrase in name else 3)
            results.append((rank, -score(entry), name, entry))
        results.sort(key=lambda r: r[:3])
        return [r[3] for r in results[:limit]]


# --- AppStream (on the system) -------------------------------------------------

def _cached_icon(component, AppStream):
    best = None
    for icon in component.get_icons():
        if icon.get_kind() == AppStream.IconKind.CACHED:
            width = icon.get_width() or 64
            for root in ICON_ROOTS:
                path = root / (component.get_origin() or "") / f"{width}x{width}" / icon.get_name()
                if path.exists() and (best is None or abs(width - 128) < abs(best[0] - 128)):
                    best = (width, path.as_uri())
        elif icon.get_kind() == AppStream.IconKind.STOCK and best is None:
            best = (0, icon.get_name())
    return best[1] if best else ""


def _entry(component, AppStream):
    developer = ""
    get_developer = getattr(component, "get_developer", None)
    if get_developer and get_developer():
        developer = get_developer().get_name() or ""
    desktop = ""
    launchable = component.get_launchable(AppStream.LaunchableKind.DESKTOP_ID)
    if launchable and launchable.get_entries():
        desktop = launchable.get_entries()[0]
    icon = _cached_icon(component, AppStream)
    description = component.get_description() or ""
    quality = ((3 if icon.startswith("file:") else 1 if icon else 0)
               + (1 if component.get_screenshots_all() else 0)
               + (1 if len(description) > 200 else 0))
    return {
        "id": component.get_id(),
        "name": component.get_name() or component.get_pkgname(),
        "summary": component.get_summary() or "",
        "pkg": component.get_pkgname(),
        "categories": list(component.get_categories() or ()),
        "keywords": list(component.get_keywords() or ()),
        "icon": icon,
        "developer": developer,
        "license": component.get_project_license() or "",
        "homepage": component.get_url(AppStream.UrlKind.HOMEPAGE) or "",
        "desktop": desktop,
        "quality": quality,
    }


def load_appstream():
    """(entries, details) from the system's AppStream data. details(id)
    returns the description and screenshot addresses of one app."""
    import gi
    gi.require_version("AppStream", "1.0")
    from gi.repository import AppStream

    pool = AppStream.Pool()
    pool.load(None)
    box = pool.get_components_by_kind(AppStream.ComponentKind.DESKTOP_APP)
    components, entries = {}, []
    for i in range(box.get_size()):
        component = box.index_safe(i)
        if not component.get_pkgname() or component.get_id() in components:
            continue
        components[component.get_id()] = component
        entries.append(_entry(component, AppStream))

    def details(app_id):
        component = components.get(app_id)
        if component is None:
            return {"description": "", "screenshots": []}
        shots = []
        for shot in component.get_screenshots_all():
            images = [im for im in shot.get_images() if im.get_url()]
            if not images:
                continue
            # The image closest to 752 px wide (AppStream's large thumbnail).
            image = min(images, key=lambda im: abs((im.get_width() or 752) - 752))
            shots.append(image.get_url())
        return {"description": sanitise_description(component.get_description()),
                "screenshots": shots[:6]}

    return entries, details
