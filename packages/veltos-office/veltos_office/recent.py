"""Recent and pinned files of the VeltOS Office start pages.

LibreOffice keeps its recent documents (with the filter each one was opened
with) in the user profile, registrymodifications.xcu, as the "PickList"
history: an ItemList of URLs with Title/Filter/Thumbnail properties and an
OrderList (0 = most recent). The start page reads that list, adds the
files it opened itself (LibreOffice writes its list only later) and keeps
the pins and options of each app in ~/.config/veltos-office/<kind>.json.
"""

import datetime
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OOR = "{http://openoffice.org/2001/registry}"
PICKLIST = "HistoryInfo['PickList']"

EXTENSIONS = {
    "word": {".docx", ".doc", ".docm", ".dotx", ".dot", ".odt", ".ott", ".fodt", ".rtf", ".txt", ".wpd", ".uot"},
    "sheet": {".xlsx", ".xls", ".xlsm", ".xltx", ".xlt", ".ods", ".ots", ".fods", ".csv", ".tsv", ".uos", ".dif",
              ".slk"},
    "slides": {".pptx", ".ppt", ".pptm", ".ppsx", ".pps", ".potx", ".pot", ".odp", ".otp", ".fodp", ".uop"},
}
# Words in LibreOffice filter names, for files whose extension says nothing.
FILTER_WORDS = {
    "word": ("word", "writer", "text", "rtf"),
    "sheet": ("calc", "excel", "csv"),
    "slides": ("impress", "powerpoint"),
}
ICONS = {"word": "x-office-document", "sheet": "x-office-spreadsheet", "slides": "x-office-presentation"}
MAX_RECENT = 50


def profile_dir(home=None):
    home = Path(home or Path.home())
    return home / ".config/libreoffice/4/user"


def config_file(kind, home=None):
    """~/.config/veltos-office/<kind>.json (XDG_CONFIG_HOME respected)."""
    base = os.environ.get("XDG_CONFIG_HOME") if home is None else ""
    config = Path(base) if base else Path(home or Path.home()) / ".config"
    return config / "veltos-office" / f"{kind}.json"


def url_to_path(url):
    if url.startswith("file://"):
        return urllib.request.url2pathname(urllib.parse.urlsplit(url).path)
    return ""


def kind_of(path, filter_name=""):
    """Which app a file belongs to ("word", "sheet", "slides" or "")."""
    suffix = Path(path).suffix.lower()
    for kind, extensions in EXTENSIONS.items():
        if suffix in extensions:
            return kind
    lowered = (filter_name or "").lower()
    for kind, words in FILTER_WORDS.items():
        if any(word in lowered for word in words):
            return kind
    return ""


def picklist(xcu_path):
    """LibreOffice's recent documents, most recent first:
    [{"path", "title", "filter"}]. Missing or unreadable file: []."""
    try:
        root = ET.parse(xcu_path).getroot()
    except (OSError, ET.ParseError):
        return []
    items, order = {}, {}
    # The items, nodes and props carry no namespace prefix in the file.
    for item in root.iter():
        if item.tag not in ("item", f"{OOR}item"):
            continue
        path = item.get(f"{OOR}path") or ""
        if PICKLIST not in path:
            continue
        for node in item.findall("node"):
            name = node.get(f"{OOR}name") or ""
            props = {}
            for prop in node.findall("prop"):
                value = prop.find("value")
                props[prop.get(f"{OOR}name")] = "" if value is None or value.text is None else value.text
            if path.endswith("/ItemList"):
                items[name] = props
            elif path.endswith("/OrderList"):
                try:
                    order[int(name)] = props.get("HistoryItemRef", "")
                except ValueError:
                    continue
    result, seen = [], set()
    urls = [order[i] for i in sorted(order)] + [u for u in items if u not in order.values()]
    for url in urls:
        local = url_to_path(url)
        if not local or local in seen:
            continue
        seen.add(local)
        props = items.get(url, {})
        result.append({"path": local, "title": props.get("Title", ""), "filter": props.get("Filter", "")})
    return result


class Store:
    """Pins, the start page's own recent list and options of one app."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = {"pinned": [], "recent": [], "show_home": True}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded = {}
        if isinstance(loaded, dict):
            for key, default in self.data.items():
                value = loaded.get(key, default)
                if isinstance(value, type(default)):
                    self.data[key] = value

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    @property
    def pinned(self):
        return list(self.data["pinned"])

    def pin(self, path, on=True):
        pins = [p for p in self.data["pinned"] if p != path]
        if on:
            pins.insert(0, path)
        self.data["pinned"] = pins
        self.save()

    @property
    def show_home(self):
        return bool(self.data["show_home"])

    def set_show_home(self, on):
        self.data["show_home"] = bool(on)
        self.save()

    def note_opened(self, path, when=None):
        when = when if when is not None else datetime.datetime.now().timestamp()
        entries = [e for e in self.data["recent"] if isinstance(e, dict) and e.get("path") != path]
        entries.insert(0, {"path": path, "opened": when})
        self.data["recent"] = entries[:MAX_RECENT]
        self.save()

    def own_recent(self):
        return [e["path"] for e in self.data["recent"] if isinstance(e, dict) and isinstance(e.get("path"), str)]

    def forget(self, path):
        self.data["recent"] = [e for e in self.data["recent"] if not (isinstance(e, dict) and e.get("path") == path)]
        self.data["pinned"] = [p for p in self.data["pinned"] if p != path]
        self.save()

    def clear_recent(self):
        self.data["recent"] = []
        self.save()


def group_of(moment, now):
    """"today", "yesterday", "this_week", "last_week" or "older"."""
    day = moment.date()
    today = now.date()
    if day >= today:
        return "today"
    if day == today - datetime.timedelta(days=1):
        return "yesterday"
    week_start = today - datetime.timedelta(days=today.weekday())
    if day >= week_start:
        return "this_week"
    if day >= week_start - datetime.timedelta(days=7):
        return "last_week"
    return "older"


MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
    "tr": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım",
           "Aralık"],
}
WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "tr": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"],
}


def clock_text(moment, lang):
    if lang == "tr":
        return moment.strftime("%H:%M")
    hour = moment.hour % 12 or 12
    return f"{hour}:{moment.minute:02d} {'PM' if moment.hour >= 12 else 'AM'}"


def modified_text(moment, lang, now):
    """"12m ago", "Yesterday at 3:15 PM", "Tuesday at 10:00 AM", "October 15"
    (Microsoft 365's wording)."""
    delta = now - moment
    seconds = delta.total_seconds()
    if 0 <= seconds < 3600:
        minutes = max(1, int(seconds // 60))
        return f"{minutes} dk önce" if lang == "tr" else f"{minutes}m ago"
    group = group_of(moment, now)
    if group == "today":
        hours = int(seconds // 3600)
        if 0 < hours < 24:
            return f"{hours} sa önce" if lang == "tr" else f"{hours}h ago"
        return clock_text(moment, lang)
    if group == "yesterday":
        return f"Dün {clock_text(moment, lang)}" if lang == "tr" else f"Yesterday at {clock_text(moment, lang)}"
    if group in ("this_week", "last_week") and (now.date() - moment.date()).days < 7:
        weekday = WEEKDAYS[lang][moment.weekday()]
        return f"{weekday} {clock_text(moment, lang)}" if lang == "tr" else f"{weekday} at {clock_text(moment, lang)}"
    month = MONTHS[lang][moment.month - 1]
    if moment.year == now.year:
        return f"{moment.day} {month}" if lang == "tr" else f"{month} {moment.day}"
    return f"{moment.day} {month} {moment.year}" if lang == "tr" else f"{month} {moment.day}, {moment.year}"


def folder_text(path, home=None):
    home = str(home or Path.home())
    folder = str(Path(path).parent)
    if folder == home:
        return "~"
    if folder.startswith(home + os.sep):
        return "~" + folder[len(home):]
    return folder


def recent_files(kind, lang, store, xcu_path=None, now=None, home=None, exists=os.path.exists,
                 mtime=os.path.getmtime):
    """The app's recent files, most recent first, as the start page shows
    them: [{"name", "path", "folder", "modifiedText", "group", "pinned",
    "icon"}]. Files that no longer exist are left out. LibreOffice's list
    comes first (it is ordered by last use); files the start page opened
    itself and LibreOffice has not recorded yet come before it."""
    now = now or datetime.datetime.now()
    xcu_path = xcu_path or profile_dir(home) / "registrymodifications.xcu"
    pins = store.pinned
    ordered = []
    for path in store.own_recent():
        if kind_of(path) == kind:
            ordered.append(path)
    for entry in picklist(xcu_path):
        if kind_of(entry["path"], entry["filter"]) == kind:
            ordered.append(entry["path"])
    for path in pins:
        if kind_of(path) == kind:
            ordered.append(path)
    result, seen = [], set()
    for path in ordered:
        if path in seen or not exists(path):
            continue
        seen.add(path)
        try:
            moment = datetime.datetime.fromtimestamp(mtime(path))
        except (OSError, OverflowError, ValueError):
            moment = now
        result.append({
            "name": Path(path).name,
            "path": path,
            "folder": folder_text(path, home),
            "modifiedText": modified_text(moment, lang, now),
            "modified": moment.timestamp(),
            "group": group_of(moment, now),
            "pinned": path in pins,
            "icon": ICONS[kind],
        })
        if len(result) >= MAX_RECENT:
            break
    return result
