"""Qt models of VeltOS File Explorer: the items of a folder (FolderModel)
and a tab with its location and history (Tab)."""

import datetime
import os
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import (Property, QAbstractListModel, QByteArray, QDateTime,
                            QFileSystemWatcher, QLocale, QMimeDatabase, QModelIndex, QObject, Qt,
                            QTimer, QUrl, Signal, Slot)

from . import files, places, strings, thumbnails

HOME, THIS_PC, TRASH = "home:", "thispc:", "trash:"
SPECIAL = (HOME, THIS_PC, TRASH)
VIEW_MODES = ("details", "tiles", "small", "medium", "large", "xlarge")


class Jobs(QObject):
    """Runs slow work off the UI thread, hands results back on it.
    `threaded=False` runs at once (tests)."""

    _finished = Signal(object, object)

    def __init__(self, threaded=True):
        super().__init__()
        self.threaded = threaded
        self._finished.connect(self._deliver, Qt.QueuedConnection)

    @staticmethod
    def _call(work):
        try:
            return work()
        except Exception as error:   # handed to the callback, never lost
            if not isinstance(error, OSError):
                traceback.print_exc()
            return error

    def submit(self, work, done=None):
        if not self.threaded:
            result = self._call(work)
            if done is not None:
                done(result)
            return
        threading.Thread(target=lambda: self._finished.emit(done, self._call(work)), daemon=True).start()

    @Slot(object, object)
    def _deliver(self, done, result):
        if done is not None:
            done(result)


class MimeTypes:
    """File type name and icon, from the shared MIME database (by file name
    first, so listing does not read every file)."""

    def __init__(self, lang):
        self.db = QMimeDatabase()
        self.lang = lang
        self.cache = {}

    def __call__(self, path, is_dir):
        if is_dir:
            return files.FOLDER_MIME, strings.text(self.lang, "file_folder"), places.folder_icon(path)
        suffix = os.path.splitext(path)[1].lower()
        if suffix and suffix in self.cache:
            return self.cache[suffix]
        mime = self.db.mimeTypeForFile(path, QMimeDatabase.MatchExtension)
        if mime.isDefault() and not suffix:
            mime = self.db.mimeTypeForFile(path)       # look inside (no extension)
        comment = mime.comment() or strings.text(self.lang, "file")
        icon = mime.iconName() if mime.iconName() else mime.genericIconName()
        result = (mime.name(), comment, icon or "text-x-generic")
        if suffix:
            self.cache[suffix] = result
        return result


def date_format(locale=None):
    """Short date with a four-digit year and short time ("6/25/2022 9:56 PM")."""
    locale = locale or QLocale()
    date = locale.dateFormat(QLocale.ShortFormat)
    if "yyyy" not in date:
        date = date.replace("yy", "yyyy")
    return date + " " + locale.timeFormat(QLocale.ShortFormat)


class FolderModel(QAbstractListModel):
    """Items of one folder (or search results, or the Recycle Bin), with
    the selection."""

    ROLES = ["name", "path", "isDir", "sizeText", "modifiedText", "type", "icon", "thumbnail",
             "selected", "cut", "folder", "original", "deletedText"]

    countChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, lang="en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self.items = []
        self.selection = set()
        self.cut_paths = set()
        self.anchor = -1
        self.current = -1
        self.fmt = date_format()
        self.locale = QLocale()
        self.thumb_generation = 0

    # --- Qt model -------------------------------------------------------------------

    def roleNames(self):
        return {Qt.UserRole + i: QByteArray(name.encode()) for i, name in enumerate(self.ROLES)}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.items):
            return None
        item = self.items[index.row()]
        name = self.ROLES[role - Qt.UserRole] if role >= Qt.UserRole else "name"
        if name == "selected":
            return item["path"] in self.selection
        if name == "cut":
            return item["path"] in self.cut_paths
        if name == "sizeText":
            return "" if item["isDir"] else self.locale.toString(files.size_kb(item["size"])) + " KB"
        if name == "modifiedText":
            return self.format_time(item.get("modified"))
        if name == "deletedText":
            return item.get("deletedText", "")
        return item.get(name, "")

    def format_time(self, stamp):
        if not stamp:
            return ""
        return self.locale.toString(QDateTime.fromSecsSinceEpoch(int(stamp)), self.fmt)

    # --- contents -------------------------------------------------------------------

    def set_items(self, items, keep_selection=False):
        previous = self.selection if keep_selection else set()
        self.beginResetModel()
        self.items = items
        paths = {i["path"] for i in items}
        self.selection = previous & paths
        self.anchor = self.current = -1
        self.endResetModel()
        self.countChanged.emit()
        self.selectionChanged.emit()

    def row_of(self, path):
        for row, item in enumerate(self.items):
            if item["path"] == path:
                return row
        return -1

    def update_item(self, path, **values):
        row = self.row_of(path)
        if row >= 0:
            self.items[row].update(values)
            index = self.index(row)
            self.dataChanged.emit(index, index)

    def _changed_all(self):
        if self.items:
            self.dataChanged.emit(self.index(0), self.index(len(self.items) - 1))
        self.selectionChanged.emit()

    @Property(int, notify=countChanged)
    def count(self):
        return len(self.items)

    # --- selection ------------------------------------------------------------------

    @Slot(int, str)
    def select(self, row, mode="single"):
        """Click (single), Ctrl+click (toggle), Shift+click (range),
        Ctrl+Shift+click (addRange)."""
        if not 0 <= row < len(self.items):
            if mode == "single":
                self.selection = set()
                self._changed_all()
            return
        path = self.items[row]["path"]
        if mode == "toggle":
            self.selection ^= {path}
            self.anchor = row
        elif mode in ("range", "addRange") and self.anchor >= 0:
            low, high = sorted((self.anchor, row))
            rows = {self.items[r]["path"] for r in range(low, high + 1)}
            self.selection = (self.selection | rows) if mode == "addRange" else rows
        else:
            self.selection = {path}
            self.anchor = row
        self.current = row
        self._changed_all()

    @Slot(list)
    def selectRows(self, rows):
        self.selection = {self.items[r]["path"] for r in rows if 0 <= r < len(self.items)}
        self._changed_all()

    @Slot()
    def selectAll(self):
        self.selection = {i["path"] for i in self.items}
        self._changed_all()

    @Slot()
    def selectNone(self):
        self.selection = set()
        self._changed_all()

    @Slot()
    def invertSelection(self):
        self.selection = {i["path"] for i in self.items} - self.selection
        self._changed_all()

    @Slot(str)
    def selectPath(self, path):
        row = self.row_of(path)
        self.selection = {path} if row >= 0 else set()
        self.anchor = self.current = row
        self._changed_all()

    def selected_items(self):
        return [i for i in self.items if i["path"] in self.selection]

    @Property(int, notify=selectionChanged)
    def selectedCount(self):
        return len(self.selection)

    @Property(str, notify=selectionChanged)
    def selectedSize(self):
        chosen = self.selected_items()
        if not chosen or any(i["isDir"] for i in chosen):
            return ""
        return files.human_size(sum(i["size"] for i in chosen))

    @Property(int, notify=selectionChanged)
    def currentRow(self):
        return self.current

    @Slot(int, result="QVariantMap")
    def get(self, row):
        if not 0 <= row < len(self.items):
            return {}
        item = dict(self.items[row])
        item["modifiedText"] = self.format_time(item.get("modified"))
        item["selected"] = item["path"] in self.selection
        return item

    @Slot(result="QVariantList")
    def selectedList(self):
        return [dict(i) for i in self.selected_items()]

    @Slot(result=list)
    def selectedUrls(self):
        """file:// URLs of the selection, encoded for text/uri-list."""
        return [QUrl.fromLocalFile(i["path"]).toString(QUrl.FullyEncoded) for i in self.selected_items()]

    @Slot(str, result=int)
    def findPrefix(self, prefix):
        """Row of the first item after the current one starting with the
        typed letters (type-ahead)."""
        prefix = prefix.casefold()
        count = len(self.items)
        # A new first letter moves on to the next match; more letters refine
        # the current one.
        start = self.current + 1 if len(prefix) == 1 else max(self.current, 0)
        for step in range(count):
            row = (start + step) % count
            if self.items[row]["name"].casefold().startswith(prefix):
                return row
        return -1

    def set_cut(self, paths):
        self.cut_paths = set(paths)
        self._changed_all()


class Tab(QObject):
    """One File Explorer tab: a location, its history and its items."""

    changed = Signal()
    loadingChanged = Signal()
    renameRequested = Signal(str)       # path of a new item to rename at once

    def __init__(self, backend, location, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.lang = backend.lang
        self.model = FolderModel(self.lang, self)
        self._location = ""
        self._history = []
        self._future = []
        self._view = "details"
        self._sort = "name"
        self._descending = False
        self._loading = False
        self._error = ""
        self._query = ""
        self._generation = 0
        self._select_after = ""
        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(lambda _p: self._reload_soon.start())
        # Setters, not QTimer(interval=...): PySide6 maps keyword arguments to
        # setters with the C library's toupper(), which in a Turkish locale
        # turns "interval" into "setİnterval" - File Explorer did not start
        # on Turkish systems (2026-10-20).
        self._reload_soon = QTimer(self)
        self._reload_soon.setSingleShot(True)
        self._reload_soon.setInterval(250)
        self._reload_soon.timeout.connect(lambda: self.load(keep_selection=True))
        self.navigate(location, remember=False)

    # --- location ---------------------------------------------------------------------

    @Property(str, notify=changed)
    def location(self):
        return self._location

    @Property(str, notify=changed)
    def kind(self):
        if self._query:
            return "search"
        if self._location in SPECIAL:
            return {HOME: "home", THIS_PC: "thispc", TRASH: "trash"}[self._location]
        return "folder"

    @Property(str, notify=changed)
    def title(self):
        return self.backend.location_title(self._location)

    @Property(str, notify=changed)
    def icon(self):
        return self.backend.location_icon(self._location)

    @Property("QVariantList", notify=changed)
    def crumbs(self):
        """Address bar parts: [{name, location}], like "This PC > Local
        Disk > home > velt" in Windows, but from the nearest known place."""
        loc = self._location
        if loc in SPECIAL:
            return [{"name": self.backend.location_title(loc), "location": loc}]
        path = Path(loc)
        home = Path.home()
        parts = []
        known = next((Path(p) for _k, p, _i in places.user_dirs()
                      if Path(p) == path or Path(p) in path.parents), None)
        if known is not None:
            parts.append({"name": known.name, "location": str(known)})
            rel = path.relative_to(known).parts
            current = known
        elif path == home or home in path.parents:
            parts.append({"name": self.backend.location_title(str(home)), "location": str(home)})
            rel = path.relative_to(home).parts
            current = home
        else:
            parts.append({"name": self.backend.location_title(THIS_PC), "location": THIS_PC})
            parts.append({"name": self.backend.text("local_disk"), "location": "/"})
            rel = path.parts[1:]
            current = Path("/")
        for part in rel:
            current = current / part
            parts.append({"name": part, "location": str(current)})
        return parts

    @Property(bool, notify=changed)
    def canBack(self):
        return bool(self._history)

    @Property(bool, notify=changed)
    def canForward(self):
        return bool(self._future)

    @Property(bool, notify=changed)
    def canUp(self):
        return self._location not in (HOME,) and self.parent_location() != ""

    @Property("QVariantList", notify=changed)
    def recentLocations(self):
        seen, result = set(), []
        for loc in reversed(self._history):
            if loc not in seen and loc != self._location:
                seen.add(loc)
                result.append({"name": self.backend.location_title(loc), "location": loc,
                               "icon": self.backend.location_icon(loc)})
        return result[:10]

    def parent_location(self):
        loc = self._location
        if loc in (HOME, THIS_PC):
            return ""
        if loc == TRASH:
            return HOME
        path = Path(loc)
        if path == Path.home():
            return THIS_PC
        if path == Path("/"):
            return THIS_PC
        return str(path.parent)

    @Slot(str)
    def navigate(self, location, remember=True):
        location = self.backend.resolve(location)
        if location is None:
            return
        if remember and self._location and location != self._location:
            self._history.append(self._location)
            self._future = []
        self._go(location)

    def _go(self, location, query=""):
        previous = self._location
        self._location = location
        self._query = query
        if self.watcher.directories():
            self.watcher.removePaths(self.watcher.directories())
        if location not in SPECIAL and not query and os.path.isdir(location):
            self.watcher.addPath(location)
        elif location == TRASH:
            files_dir = places.trash_dir() / "files"
            if files_dir.is_dir():
                self.watcher.addPath(str(files_dir))
        self._view = self.backend.view_for(location)
        self.model.set_cut(self.backend.cut_paths_in(location))
        self._select_after = previous if previous and Path(previous).parent == Path(location) else ""
        self.changed.emit()
        self.load()

    @Slot()
    def back(self):
        if self._history:
            self._future.append(self._location)
            self._go(self._history.pop())

    @Slot()
    def forward(self):
        if self._future:
            self._history.append(self._location)
            self._go(self._future.pop())

    @Slot()
    def up(self):
        parent = self.parent_location()
        if parent:
            self.navigate(parent)

    # --- contents ---------------------------------------------------------------------

    @Property(bool, notify=loadingChanged)
    def loading(self):
        return self._loading

    @Property(str, notify=loadingChanged)
    def error(self):
        return self._error

    @Property(str, notify=changed)
    def query(self):
        return self._query

    @Slot()
    def refresh(self):
        if self._location == THIS_PC:
            self.backend.refreshDrives()
        self.load(keep_selection=True)

    def load(self, keep_selection=False):
        self._generation += 1
        generation = self._generation
        location, query = self._location, self._query
        if location in (HOME, THIS_PC) and not query:
            self.model.set_items([])
            self._set_loading(False, "")
            return
        show_hidden = self.backend.show_hidden
        mime = self.backend.mime

        def work():
            if location == TRASH:
                return self.backend.trash_entries()
            if query:
                base = str(Path.home()) if location in (HOME, THIS_PC) else location
                return files.search(base, query, show_hidden, mime,
                                    cancelled=lambda: generation != self._generation)
            return files.list_folder(location, show_hidden, mime)

        def done(result):
            if generation != self._generation:
                return
            if isinstance(result, Exception):
                self.model.set_items([])
                key = "no_access" if isinstance(result, PermissionError) else "cannot_open"
                self._set_loading(False, self.backend.text(key).replace("{name}", Path(location).name))
                return
            self.model.set_items(files.sort_items(result, self._sort, self._descending), keep_selection)
            if self._select_after:
                self.model.selectPath(self._select_after)
                self._select_after = ""
            self._set_loading(False, "")
            self.backend.make_thumbnails(self, result, generation)

        self._set_loading(True, "")
        self.backend.jobs.submit(work, done)

    def _set_loading(self, loading, error):
        self._loading = loading
        self._error = error
        self.loadingChanged.emit()

    @Slot(str)
    def search(self, query):
        query = query.strip()
        if query == self._query:
            return
        if query and not self._query:
            self._history.append(self._location)
            self._future = []
        self._go(self._location, query)

    # --- view and sorting -------------------------------------------------------------

    @Property(str, notify=changed)
    def viewMode(self):
        return self._view

    @Slot(str)
    def setViewMode(self, mode):
        if mode in VIEW_MODES:
            self._view = mode
            self.backend.remember_view(self._location, mode)
            self.changed.emit()

    @Property(str, notify=changed)
    def sortKey(self):
        return self._sort

    @Property(bool, notify=changed)
    def sortDescending(self):
        return self._descending

    @Slot(str, bool)
    def setSort(self, key, descending):
        if key not in files.SORT_KEYS:
            return
        self._sort, self._descending = key, descending
        self.model.beginResetModel()
        self.model.items = files.sort_items(self.model.items, key, descending)
        self.model.endResetModel()
        self.changed.emit()

    @Slot(str)
    def sortBy(self, key):
        """Click on a column header: same column flips the order."""
        self.setSort(key, not self._descending if key == self._sort else False)

    # --- Model for QML ------------------------------------------------------------------

    @Property(QObject, constant=True)
    def items(self):
        return self.model

    def request_rename(self, path):
        self.renameRequested.emit(path)


def deleted_text(stamp, model):
    try:
        moment = datetime.datetime.fromisoformat(stamp)
    except ValueError:
        return stamp
    return model.format_time(moment.timestamp())
