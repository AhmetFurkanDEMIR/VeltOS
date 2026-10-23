"""VeltOS Properties window: Windows 11's Properties of files, folders and
drives instead of KDE's dialog.

    veltos-explorer --properties PATH... (file:// URLs and desktop:/NAME too)

General: icon and name (renaming), type, the app that opens the file
("Change..." opens the "Select an app" window), location, size and size
on disk (counted in the background for folders), what a folder contains,
created / modified / accessed, the Read-only and Hidden attributes. A
drive shows its type, file system and a used / free pie, a Recycle Bin
item its original location and deletion date. Security: owner, group and
the read / write / run permissions (changeable by the owner). Details: the
facts as a list (picture size for pictures). OK, Cancel and Apply as on
Windows. Nothing here needs the administrator password; what the user may
not change is shown, not offered.
"""

import datetime
import grp
import os
import pwd
import re
import stat
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path

from PySide6.QtCore import Property, QDateTime, QLocale, QObject, Qt, QUrl, Signal, Slot

from . import ops, places, strings

QML_DIR = Path(__file__).resolve().parent / "qml"


def resolve(argument):
    """A local path from a path, a file:// URL or desktop:/NAME."""
    text = str(argument)
    if text.startswith("file://"):
        return urllib.parse.unquote(urllib.parse.urlparse(text).path)
    if text.startswith("desktop:/"):
        desktop = next((path for key, path, _icon in places.user_dirs() if key == "DESKTOP"),
                       str(Path.home() / "Desktop"))
        return str(Path(desktop) / urllib.parse.unquote(text[len("desktop:/"):]).lstrip("/"))
    return os.path.abspath(text)


def group_digits(number, lang):
    """1,264 (English) or 1.264 (Turkish), as Windows writes byte counts."""
    text = f"{number:,}"
    return text.replace(",", ".") if lang == "tr" else text


def size_text(size, lang):
    """Windows' "1.23 KB (1,264 bytes)"; Turkish "1,23 KB (1.264 bayt)"."""
    unit_bytes = strings.text(lang, "bytes")
    if size < 1024:
        return f"{group_digits(size, lang)} {unit_bytes}"
    value = float(size)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024
        if value < 1024 or unit == "TB":
            break
    shown = f"{value:.0f}" if value >= 100 else (f"{value:.1f}" if value >= 10 else f"{value:.2f}")
    if lang == "tr":
        shown = shown.replace(".", ",")
    return f"{shown} {unit} ({group_digits(size, lang)} {unit_bytes})"


def date_text(timestamp, lang):
    """"Thursday, October 22, 2026, 4:39:12 PM" / "22 Ekim 2026 Perşembe, 16:39:12"."""
    if not timestamp:
        return ""
    moment = QDateTime.fromSecsSinceEpoch(int(timestamp))
    if lang == "tr":
        return QLocale(QLocale.Language.Turkish, QLocale.Country.Turkey).toString(moment, "d MMMM yyyy dddd, HH:mm:ss")
    return QLocale(QLocale.Language.English, QLocale.Country.UnitedStates).toString(
        moment, "dddd, MMMM d, yyyy, h:mm:ss AP")


def birth_time(path):
    """When the file was made, where the file system records it, else 0."""
    try:
        value = getattr(os.stat(path, follow_symlinks=False), "st_birthtime", 0)
        if value:
            return value
        out = subprocess.run(["stat", "-c", "%W", "--", path], capture_output=True, text=True, timeout=5).stdout
        return int(out.strip() or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0


def mounts(text=None):
    """[(mount point, device, file system)] from /proc/self/mounts."""
    if text is None:
        try:
            text = Path("/proc/self/mounts").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
    result = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            point = parts[1].encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8", "replace")
            result.append((point, parts[0], parts[2]))
    return result


def trash_info(path, trash=None):
    """(original location, deletion date) of a Recycle Bin item, or None."""
    trash = Path(trash or places.trash_dir())
    try:
        Path(path).relative_to(trash / "files")
    except ValueError:
        return None
    for item in places.trash_items(trash):
        if item["path"] == str(path):
            return item["original"], item["deleted"]
    return "", ""


def default_application(mime, lang="en", config_dirs=None):
    """The app that opens the type ({name, icon, id}), as Settings > Default
    apps and File Explorer decide it: mimeapps.list, then any app that
    claims the type."""
    home = places.config_home()
    dirs = config_dirs or [home, Path("/etc/xdg"), Path("/usr/share/applications")]
    by_id = {app["id"]: app for app in places.applications_for(mime, lang)}
    for folder in dirs:
        for name in ("mimeapps.list", "kde-mimeapps.list"):
            try:
                text = (Path(folder) / name).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            section = re.search(r"^\[Default Applications\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
            if not section:
                continue
            match = re.search(r"^" + re.escape(mime) + r"=(.*)$", section.group(1), re.M)
            if not match:
                continue
            for desktop_id in (d.strip() for d in match.group(1).split(";")):
                if desktop_id in by_id:
                    return by_id[desktop_id]
                for directory in places.application_dirs():
                    entry = places.read_desktop_entry(Path(directory) / desktop_id) if desktop_id else None
                    if entry is not None:
                        return {"id": desktop_id, "name": entry.get(f"Name[{lang}]") or entry.get("Name", desktop_id),
                                "icon": entry.get("Icon", "")}
    apps = list(by_id.values())
    return apps[0] if apps else None


def count_tree(paths, stop, report):
    """Sizes, files and folders under the paths; `report(totals)` now and
    then (Windows counts up while it looks)."""
    totals = {"bytes": 0, "disk": 0, "files": 0, "folders": 0}
    last = time.monotonic()
    stack = []
    for path in paths:
        try:
            info = os.stat(path, follow_symlinks=False)
        except OSError:
            continue
        if stat.S_ISDIR(info.st_mode):
            stack.append(path)
        else:
            totals["files"] += 1
            totals["bytes"] += info.st_size
            totals["disk"] += info.st_blocks * 512
    while stack and not stop.is_set():
        folder = stack.pop()
        try:
            entries = list(os.scandir(folder))
        except OSError:
            continue
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISDIR(info.st_mode):
                totals["folders"] += 1
                stack.append(entry.path)
            else:
                totals["files"] += 1
                totals["bytes"] += info.st_size
                totals["disk"] += info.st_blocks * 512
        if time.monotonic() - last > 0.25:
            report(dict(totals))
            last = time.monotonic()
    return totals


class Properties(QObject):
    """What Properties.qml shows, and the changes it applies."""

    changed = Signal()
    finished = Signal()
    message = Signal(str)
    _counted = Signal(object, bool)

    def __init__(self, arguments, lang=None, start=ops.detached, threaded=True, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.start = start
        self.paths = [resolve(a) for a in arguments if str(a)]
        self._stop = threading.Event()
        self._totals = {"bytes": 0, "disk": 0, "files": 0, "folders": 0}
        self._counting = False
        self._counted.connect(self._take_totals, Qt.ConnectionType.QueuedConnection)
        self._info = self._describe()
        self._count(threaded)

    # --- reading ------------------------------------------------------------------------

    def text(self, key):
        return strings.text(self.lang, key)

    def _describe(self):
        from .models import MimeTypes
        mime_types = MimeTypes(self.lang)
        info = {"kind": "missing", "name": "", "icon": "document-properties", "typeName": "", "location": "",
                "opensWith": None, "created": "", "modified": "", "accessed": "", "readOnly": False,
                "hidden": False, "owner": "", "group": "", "mode": 0, "canChangeMode": False, "canRename": False,
                "fileSystem": "", "used": 0, "free": 0, "capacity": 0, "original": "", "deleted": "",
                "details": [], "mime": ""}
        existing = [p for p in self.paths if os.path.lexists(p)]
        if not existing:
            info["name"] = os.path.basename(self.paths[0]) if self.paths else ""
            return info
        if len(existing) > 1:
            parents = {os.path.dirname(p) for p in existing}
            kinds = {mime_types(p, os.path.isdir(p))[1] for p in existing}
            info.update(kind="multiple", icon="document-multiple",
                        name=self.text("files_and_folders"),
                        typeName=kinds.pop() if len(kinds) == 1 else self.text("multiple_types"),
                        location=self.text("all_in").replace("{folder}", parents.pop()) if len(parents) == 1 else "",
                        canRename=False)
            first = os.stat(existing[0])
            info["readOnly"] = all(not (os.stat(p).st_mode & stat.S_IWUSR) for p in existing)
            info["hidden"] = all(os.path.basename(p).startswith(".") for p in existing)
            info["canChangeMode"] = all(os.stat(p).st_uid == os.getuid() for p in existing)
            info["mode"] = stat.S_IMODE(first.st_mode)
            return info

        path = existing[0]
        st = os.stat(path, follow_symlinks=False)
        is_dir = stat.S_ISDIR(st.st_mode) or (os.path.isdir(path) and not os.path.islink(path))
        mime, type_name, icon = mime_types(path, is_dir)
        name = os.path.basename(path.rstrip("/")) or path
        info.update(name=name, icon=icon, typeName=type_name, mime=mime,
                    location=os.path.dirname(path.rstrip("/")) or "/",
                    created=date_text(birth_time(path), self.lang), modified=date_text(st.st_mtime, self.lang),
                    accessed=date_text(st.st_atime, self.lang),
                    readOnly=not (st.st_mode & stat.S_IWUSR), hidden=name.startswith("."),
                    mode=stat.S_IMODE(st.st_mode), canChangeMode=st.st_uid == os.getuid(),
                    canRename=os.access(os.path.dirname(path.rstrip("/")) or "/", os.W_OK))
        try:
            info["owner"] = pwd.getpwuid(st.st_uid).pw_name
        except KeyError:
            info["owner"] = str(st.st_uid)
        try:
            info["group"] = grp.getgrgid(st.st_gid).gr_name
        except KeyError:
            info["group"] = str(st.st_gid)

        # The Recycle Bin itself (its desktop icon's Properties): what is in it.
        if os.path.normpath(path) == os.path.normpath(str(Path(places.trash_dir()) / "files")):
            try:
                full = bool(os.listdir(path))
            except OSError:
                full = False
            info.update(kind="folder", name=self.text("recycle_bin"), icon="user-trash-full" if full else "user-trash",
                        location="", canRename=False, canChangeMode=False, created="", accessed="")
            return info

        mounted = {point: (device, fs) for point, device, fs in mounts()}
        trash = trash_info(path)
        if is_dir and path.rstrip("/") in mounted or path == "/":
            device, fs = mounted.get(path.rstrip("/") or "/", ("", ""))
            try:
                vfs = os.statvfs(path)
                capacity = vfs.f_blocks * vfs.f_frsize
                free = vfs.f_bavail * vfs.f_frsize
            except OSError:
                capacity = free = 0
            info.update(kind="drive", icon="drive-harddisk", typeName=self.text("local_disk"),
                        fileSystem=fs.upper() if fs in ("ntfs", "ntfs3", "vfat", "exfat") else fs,
                        capacity=capacity, free=free, used=max(0, capacity - free), canRename=False,
                        name=name if path != "/" else self.text("local_disk"))
            if fs in ("vfat", "exfat", "ntfs", "ntfs3") or "/media/" in path or "/run/media/" in path:
                info["typeName"] = self.text("removable_disk")
                info["icon"] = "drive-removable-media"
        elif trash is not None:
            info.update(kind="trash", original=trash[0], canRename=False)
            info["deleted"] = self._trash_date(trash[1])
        elif is_dir:
            info.update(kind="folder")
        else:
            info.update(kind="file")
            app = default_application(mime, self.lang)
            info["opensWith"] = {"name": app["name"], "icon": app["icon"]} if app else None
        info["details"] = self._details(path, info, mime)
        return info

    def _trash_date(self, value):
        try:
            moment = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
        return date_text(moment.timestamp(), self.lang)

    def _details(self, path, info, mime):
        rows = [(self.text("name"), info["name"]), (self.text("type"), info["typeName"]),
                (self.text("folder_path"), info["location"])]
        if mime.startswith("image/"):
            from PySide6.QtGui import QImageReader
            size = QImageReader(path).size()
            if size.isValid():
                rows.append((self.text("dimensions"), f"{size.width()} x {size.height()}"))
        rows += [(self.text("date_created"), info["created"]), (self.text("date_modified"), info["modified"]),
                 (self.text("owner_column"), info["owner"])]
        return [{"label": label, "value": value} for label, value in rows if value]

    def _count(self, threaded):
        kind = self._info["kind"]
        if kind in ("missing", "drive"):
            return
        targets = [p for p in self.paths if os.path.lexists(p)]

        def work():
            return count_tree(targets, self._stop, lambda totals: self._counted.emit(totals, False))

        self._counting = True
        if threaded:
            threading.Thread(target=lambda: self._counted.emit(work(), True), daemon=True).start()
        else:
            self._take_totals(work(), True)

    @Slot(object, bool)
    def _take_totals(self, totals, done):
        self._totals = totals
        if done:
            self._counting = False
        self.changed.emit()

    def stop(self):
        self._stop.set()

    # --- for QML -------------------------------------------------------------------------

    @Slot(str, result=str)
    def tr(self, key):
        return self.text(key)

    @Property(bool, constant=True)
    def darkMode(self):
        from .app import Backend
        return Backend.read_dark_mode()

    @Property(float, constant=True)
    def textScale(self):
        from .app import Backend
        return Backend.read_text_scale()

    @Property(str, constant=True)
    def accentColor(self):
        from .app import Backend
        return Backend.read_accent_color()

    @Property("QVariantMap", notify=changed)
    def info(self):
        return self._info

    @Property(str, notify=changed)
    def title(self):
        return self.text("properties_title").replace("{name}", self._info["name"])

    @Property(str, notify=changed)
    def sizeText(self):
        if self._info["kind"] == "drive":
            return ""
        return size_text(self._totals["bytes"], self.lang)

    @Property(str, notify=changed)
    def sizeOnDiskText(self):
        if self._info["kind"] == "drive":
            return ""
        return size_text(self._totals["disk"], self.lang)

    @Property(str, notify=changed)
    def containsText(self):
        totals = self._totals
        files = self.text("files_count").replace("{count}", group_digits(totals["files"], self.lang))
        folders = self.text("folders_count").replace("{count}", group_digits(totals["folders"], self.lang))
        return f"{files}, {folders}"

    @Property(bool, notify=changed)
    def counting(self):
        return self._counting

    @Property("QVariantMap", constant=True)
    def drive(self):
        info = self._info
        capacity = info["capacity"]
        return {"used": size_text(info["used"], self.lang), "free": size_text(info["free"], self.lang),
                "capacity": size_text(capacity, self.lang),
                "usedFraction": info["used"] / capacity if capacity else 0.0,
                "short": [places_size(info["used"], self.lang), places_size(info["free"], self.lang),
                          places_size(capacity, self.lang)]}

    @Slot()
    def changeApp(self):
        if self._info["kind"] == "file" and self.paths:
            self.start([sys.executable, "-m", "veltos_explorer", "--open-with", self.paths[0]])

    @Slot(str, bool, bool, int, result=bool)
    def apply(self, name, read_only, hidden, mode):
        """Rename, attributes and permissions; False (and a message) when
        something could not be done."""
        info = self._info
        kind = info["kind"]
        if kind in ("missing", "drive", "trash"):
            return True
        try:
            if kind != "multiple" and info["canChangeMode"] and mode != info["mode"] and 0 <= mode <= 0o7777:
                os.chmod(self.paths[0], mode)
                info["mode"] = mode
                info["readOnly"] = not (mode & stat.S_IWUSR)
            if read_only != info["readOnly"]:
                for path in self.paths:
                    current = stat.S_IMODE(os.stat(path).st_mode)
                    os.chmod(path, current & ~stat.S_IWUSR if read_only else current | stat.S_IWUSR)
                info["readOnly"] = read_only
                info["mode"] = stat.S_IMODE(os.stat(self.paths[0]).st_mode)
            if kind != "multiple":
                name = name.strip()
                if hidden != info["hidden"]:
                    name = ("." + name.lstrip(".")) if hidden else name.lstrip(".")
                if name != info["name"]:
                    if not name or "/" in name or name in (".", "..") or name.strip(".") == "":
                        self.message.emit(self.text("bad_name"))
                        return False
                    target = os.path.join(os.path.dirname(self.paths[0].rstrip("/")), name)
                    if os.path.lexists(target):
                        self.message.emit(self.text("name_exists"))
                        return False
                    os.rename(self.paths[0], target)
                    self.paths[0] = target
                    info["name"] = name
                    info["hidden"] = name.startswith(".")
            else:
                for index, path in enumerate(self.paths):
                    base = os.path.basename(path)
                    if hidden != base.startswith("."):
                        new = ("." + base) if hidden else base.lstrip(".")
                        target = os.path.join(os.path.dirname(path), new)
                        if new and not os.path.lexists(target):
                            os.rename(path, target)
                            self.paths[index] = target
                info["hidden"] = hidden
        except OSError as error:
            self.message.emit(self.text("properties_failed").replace("{reason}", error.strerror or str(error)))
            return False
        self.changed.emit()
        return True

    @Slot()
    def close(self):
        self.stop()
        self.finished.emit()


def places_size(size, lang):
    """"23.4 GB" without the byte count (beside the pie)."""
    return size_text(size, lang).split(" (")[0]


def run(argv):
    from PySide6.QtQml import QQmlApplicationEngine

    from .app import prepare_application
    arguments = [a for a in argv[1:] if a != "--properties"]
    app = prepare_application([argv[0]], "veltos-explorer")
    # The title is "notes.txt Properties", as on Windows, without
    # " — File Explorer" (Qt adds the display name to window titles).
    app.setApplicationDisplayName("")
    properties = Properties(arguments)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("properties", properties)
    engine.rootContext().setContextProperty("backend", properties)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Properties.qml")))
    if not engine.rootObjects():
        return 1
    properties.finished.connect(app.quit)
    code = app.exec()
    properties.stop()
    return code
