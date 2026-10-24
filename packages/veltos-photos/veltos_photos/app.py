"""VeltOS Photos: Windows 11's Photos on VeltOS.

The window (qml/Main.qml) has the navigation pane (Gallery, Favorites,
folders, Settings), the gallery grouped by month and the viewer (zoom,
rotate, edit, delete, favorite, file information, filmstrip). This module
scans the folders (library.py), serves thumbnails to QML (thumbs.py,
image://thumb/...), keeps the favorites and settings, and does the file
work: rotate and edit (edit.py), Recycle Bin, clipboard, desktop and lock
screen backgrounds.
"""

import configparser
import datetime
import os
import subprocess
import sys
import threading
import traceback
import urllib.parse
from pathlib import Path

from PySide6.QtCore import (QAbstractListModel, QByteArray, QFileSystemWatcher, QLocale, QModelIndex,
                            QObject, QSettings, QSize, Qt, QTimer, QUrl, Property, Signal, Slot)
from PySide6.QtGui import QGuiApplication, QIcon, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow

from . import edit, library, strings, thumbs

VERSION = "0.1"
QML_DIR = Path(__file__).resolve().parent / "qml"
THEMES = ("light", "dark", "system")
TILE_SIZES = {"small": 120, "medium": 180, "large": 260}


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def cache_home():
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")


def kde_value(group, key):
    home = config_home()
    for path in (home / "kdeglobals", home / "kdedefaults/kdeglobals", Path("/etc/xdg/kdeglobals")):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return ""



def text_scale():
    """Text size chosen in Settings > Accessibility (the KDE font size over
    its default of 10 pt): the VeltOS apps scale their text with it, as
    Windows apps follow Windows' text size."""
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0

def system_dark():
    return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")


def system_accent():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def human_size(size):
    for unit in ("bytes", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size} {unit}" if unit == "bytes" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def detached(command):
    try:
        subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def run(command, timeout=30):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


class ThumbnailProvider(QQuickImageProvider):
    """image://thumb/<kind>/<flavour>/<mtime>/<quoted path>: the cached or
    new thumbnail, made in Qt's image loading threads (the file time makes
    QML load it again after the picture changed)."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image,
                         QQuickImageProvider.Flag.ForceAsynchronousImageLoading)

    def requestImage(self, image_id, size, requested_size):
        try:
            kind, flavour, _mtime, quoted = image_id.split("/", 3)
            image = thumbs.thumbnail(urllib.parse.unquote(quoted), kind, flavour)
        except Exception:  # never take the gallery down for one file
            traceback.print_exc()
            image = QImage()
        if image.isNull():
            image = QImage(1, 1, QImage.Format.Format_ARGB32)
            image.fill(0)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


class IconProvider(QQuickImageProvider):
    """image://icon/<name>: an icon of the desktop's icon theme."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    def requestPixmap(self, name, size, requested_size):
        side = max(requested_size.width(), requested_size.height(), 16) if requested_size.isValid() else 32
        pixmap = QIcon.fromTheme(name).pixmap(side, side)
        if pixmap.isNull():               # no such icon (tests, other desktops)
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(side, side)
            pixmap.fill(Qt.transparent)
        if size is not None:
            size.setWidth(pixmap.width())
            size.setHeight(pixmap.height())
        return pixmap


class RowsModel(QAbstractListModel):
    """The gallery as rows: month headings and rows of items."""

    ROLES = {Qt.UserRole: b"type", Qt.UserRole + 1: b"title", Qt.UserRole + 2: b"items"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def roleNames(self):
        return {role: QByteArray(name) for role, name in self.ROLES.items()}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.rows):
            return None
        name = self.ROLES.get(role, b"title").decode()
        return self.rows[index.row()].get(name)

    def reset(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class Backend(QObject):
    themeChanged = Signal()
    settingsChanged = Signal()
    libraryChanged = Signal()
    viewerChanged = Signal()
    favoritesChanged = Signal()
    message = Signal(str)
    _scanned = Signal(object)

    def __init__(self, lang=None, settings=None, scan=True, parent=None):
        super().__init__(parent)
        self._lang = lang or strings.language()
        self._texts = strings.texts(self._lang)
        self._settings = settings if settings is not None else QSettings(
            str(config_home() / "veltos/photos.conf"), QSettings.Format.IniFormat)
        self.rows = RowsModel(self)
        self._items = []
        self._visible = []
        self._columns = 4
        self._page = "gallery"
        self._query = ""
        self._scanning = False
        self._viewer = []
        self._viewer_index = -1
        self._system_dark = system_dark()
        self._accent = system_accent()
        self._watcher = QFileSystemWatcher(self)
        for path in (config_home(), config_home() / "kdeglobals"):
            if path.exists():
                self._watcher.addPath(str(path))
        self._watcher.directoryChanged.connect(self._reread_theme)
        self._watcher.fileChanged.connect(self._reread_theme)
        self._scanned.connect(self._take_scan, Qt.QueuedConnection)
        self._cache_file = cache_home() / "veltos/photos-index.json"
        if scan:
            self.refresh()

    # --- theme and settings -------------------------------------------------------------

    def _reread_theme(self, *_args):
        dark, accent = system_dark(), system_accent()
        if (dark, accent) != (self._system_dark, self._accent):
            self._system_dark, self._accent = dark, accent
            self.themeChanged.emit()

    def _value(self, key, default):
        value = self._settings.value(key, default)
        if isinstance(default, list):
            if value in (None, ""):
                return []
            return [value] if isinstance(value, str) else list(value)
        return str(value)

    def _save(self, key, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(str, constant=True)
    def version(self):
        return VERSION

    @Property(str, notify=themeChanged)
    def theme(self):
        theme = self._value("theme", "system")
        return theme if theme in THEMES else "system"

    @Slot(str)
    def setTheme(self, theme):
        if theme in THEMES:
            self._save("theme", theme)
            self.themeChanged.emit()

    @Property(float, notify=themeChanged)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, notify=themeChanged)
    def darkMode(self):
        return self._system_dark if self.theme == "system" else self.theme == "dark"

    @Property(str, notify=themeChanged)
    def accent(self):
        return self._accent

    @Property(str, notify=settingsChanged)
    def filter(self):
        value = self._value("filter", "all")
        return value if value in ("all", "image", "video") else "all"

    @Slot(str)
    def setFilter(self, value):
        self._save("filter", value)
        self.settingsChanged.emit()
        self._relayout()

    @Property(str, notify=settingsChanged)
    def sort(self):
        return "oldest" if self._value("sort", "newest") == "oldest" else "newest"

    @Slot(str)
    def setSort(self, value):
        self._save("sort", value)
        self.settingsChanged.emit()
        self._relayout()

    @Property(str, notify=settingsChanged)
    def tileSize(self):
        value = self._value("tileSize", "medium")
        return value if value in TILE_SIZES else "medium"

    @Property(int, notify=settingsChanged)
    def tilePixels(self):
        return TILE_SIZES[self.tileSize]

    @Slot(str)
    def setTileSize(self, value):
        if value in TILE_SIZES:
            self._save("tileSize", value)
            self.settingsChanged.emit()

    # --- folders --------------------------------------------------------------------------

    @Property("QStringList", notify=settingsChanged)
    def folders(self):
        chosen = self._value("folders", [])
        return chosen if chosen else [str(p) for p in library.default_folders()]

    @Slot(str)
    def addFolder(self, url):
        path = QUrl(url).toLocalFile() if url.startswith("file:") else url
        if not path or not Path(path).is_dir():
            return
        folders = self.folders
        if path not in folders:
            self._save("folders", folders + [path])
            self.settingsChanged.emit()
            self.refresh()

    @Slot(str)
    def removeFolder(self, path):
        folders = [f for f in self.folders if f != path]
        self._save("folders", folders if folders else [])
        self.settingsChanged.emit()
        self.refresh()

    @Slot(str, result=str)
    def folderName(self, path):
        sample = {str(library.SAMPLES / "Wallpapers"): "sample_wallpapers",
                  str(library.SAMPLES / "Videos"): "sample_videos"}.get(path)
        if sample:
            return self._texts[sample]
        return Path(path).name or path

    # --- library and gallery ----------------------------------------------------------------

    @Property(bool, notify=libraryChanged)
    def scanning(self):
        return self._scanning

    @Property(int, notify=libraryChanged)
    def count(self):
        return len(self._visible)

    @Property(int, notify=libraryChanged)
    def total(self):
        return len(self._items)

    @Property(QObject, constant=True)
    def galleryRows(self):
        return self.rows

    @Property(str, notify=libraryChanged)
    def page(self):
        return self._page

    @Slot(str)
    def setPage(self, page):
        self._page = page
        self._relayout()

    @Property(str, notify=libraryChanged)
    def query(self):
        return self._query

    @Slot(str)
    def setQuery(self, text):
        self._query = text.strip()
        self._relayout()

    @Slot(int)
    def setColumns(self, columns):
        columns = max(1, columns)
        if columns != self._columns:
            self._columns = columns
            self._relayout()

    @Slot()
    def refresh(self):
        if self._scanning:
            return
        self._scanning = True
        self.libraryChanged.emit()
        folders = self.folders

        def work():
            try:
                cache = library.load_cache(self._cache_file)
                items = library.scan(folders, cache)
                library.save_cache(self._cache_file, items)
            except Exception:
                traceback.print_exc()
                items = []
            self._scanned.emit(items)
        threading.Thread(target=work, daemon=True).start()

    def scan_now(self):
        """Scan in this thread (tests)."""
        self._take_scan(library.scan(self.folders))

    def _take_scan(self, items):
        self._items = items or []
        self._scanning = False
        self._relayout()

    def _filtered(self):
        favorites = set(self.favorites)
        items = self._items
        if self._page == "favorites":
            items = [i for i in items if i["path"] in favorites]
        elif self._page.startswith("folder:"):
            folder = self._page[len("folder:"):].rstrip("/") + "/"
            items = [i for i in items if i["path"].startswith(folder)]
        if self.filter != "all":
            items = [i for i in items if i["kind"] == self.filter]
        if self._query:
            # Match the query against each picture's path *within* its library
            # folder, not its absolute path: otherwise a search term that
            # happens to occur in the folders above Pictures (a user name, a
            # temp dir) would match every file.
            words = self._query.lower().split()
            roots = sorted((f.rstrip("/") + "/" for f in self.folders), key=len, reverse=True)

            def under_root(path):
                low = path.lower()
                for root in roots:
                    if low.startswith(root.lower()):
                        return low[len(root):]
                return low

            items = [i for i in items if all(w in under_root(i["path"]) for w in words)]
        if self.sort == "oldest":
            items = list(reversed(items))
        return items

    def _month_title(self, year, month):
        return QLocale().standaloneMonthName(month, QLocale.FormatType.LongFormat) + f" {year}"

    def _relayout(self):
        self._visible = self._filtered()
        self.rows.reset(library.rows(self._visible, self._columns, self._month_title))
        self.libraryChanged.emit()

    @Slot(int, result=str)
    def countText(self, count):
        return self._texts["one_item"] if count == 1 else self._texts["items"].format(count=count)

    @Slot(str, str, int, result=str)
    def thumbUrl(self, path, kind, mtime):
        return f"image://thumb/{kind}/large/{mtime}/{urllib.parse.quote(path, safe='')}"

    @Slot(str, str, int, result=str)
    def bigThumbUrl(self, path, kind, mtime):
        return f"image://thumb/{kind}/x-large/{mtime}/{urllib.parse.quote(path, safe='')}"

    @Slot(result=str)
    def firstVisible(self):
        return self._visible[0]["path"] if self._visible else ""

    @Slot(str, int, result=str)
    def fileUrl(self, path, mtime):
        """The picture's URL; the file time makes QML read it again after
        it was rotated or edited."""
        url = QUrl.fromLocalFile(path)
        url.setQuery(f"v={mtime}")
        return url.toString()

    # --- favorites ------------------------------------------------------------------------

    @Property("QStringList", notify=favoritesChanged)
    def favorites(self):
        return self._value("favorites", [])

    @Slot(str, result=bool)
    def isFavorite(self, path):
        return path in self.favorites

    @Slot(str)
    def toggleFavorite(self, path):
        favorites = self.favorites
        favorites = [f for f in favorites if f != path] if path in favorites else favorites + [path]
        self._save("favorites", favorites)
        self.favoritesChanged.emit()
        if self._page == "favorites":
            self._relayout()

    # --- viewer ---------------------------------------------------------------------------

    @Slot(str)
    def openInViewer(self, path):
        """Open from the gallery: the viewer steps through what is shown."""
        self._viewer = list(self._visible)
        self._viewer_index = next((i for i, item in enumerate(self._viewer) if item["path"] == path), -1)
        if self._viewer_index < 0:
            self._viewer = library.siblings(path)
            self._viewer_index = next((i for i, item in enumerate(self._viewer) if item["path"] == path), 0)
        self.viewerChanged.emit()

    def open_file(self, path):
        """Open a file given on the command line: its folder's pictures."""
        path = str(Path(path).expanduser().absolute())
        self._viewer = library.siblings(path)
        self._viewer_index = next((i for i, item in enumerate(self._viewer) if item["path"] == path), 0)
        self.viewerChanged.emit()

    @Property("QVariantList", notify=viewerChanged)
    def viewerItems(self):
        return self._viewer

    @Property(int, notify=viewerChanged)
    def viewerIndex(self):
        return self._viewer_index

    @Property("QVariantMap", notify=viewerChanged)
    def viewerItem(self):
        if 0 <= self._viewer_index < len(self._viewer):
            return self._viewer[self._viewer_index]
        return {}

    @Slot(int)
    def viewerGo(self, index):
        if 0 <= index < len(self._viewer):
            self._viewer_index = index
            self.viewerChanged.emit()

    @Slot(int)
    def viewerStep(self, delta):
        self.viewerGo(self._viewer_index + delta)

    @Slot()
    def closeViewer(self):
        self._viewer, self._viewer_index = [], -1
        self.viewerChanged.emit()

    @Slot(str, result="QVariantMap")
    def fileInfo(self, path):
        facts = edit.info(path)
        try:
            st = os.stat(path)
        except OSError:
            return {}
        locale = QLocale()
        item = next((i for i in self._viewer if i["path"] == path), None) or {}
        taken = item.get("date") if item.get("taken") else None
        if taken is None:
            date = library.exif_date(path)
            taken = date.isoformat(timespec="seconds") if date else None
        fmt = QLocale.FormatType.LongFormat

        def when(iso):
            moment = datetime.datetime.fromisoformat(iso)
            return f"{locale.toString(moment.date(), fmt)} {moment.strftime('%H:%M')}"
        return {
            "name": Path(path).name,
            "taken": when(taken) if taken else "",
            "modified": when(datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")),
            "dimensions": f"{facts['width']} x {facts['height']}" if facts["width"] else "",
            "megapixels": f"{facts['width'] * facts['height'] / 1e6:.1f} MP" if facts["width"] else "",
            "size": human_size(st.st_size),
            "location": str(Path(path).parent),
            "camera": facts["camera"], "lens": facts["lens"],
            "exposure": " · ".join(v for v in (facts["exposure"], facts["iso"], facts["focal"]) if v),
        }

    # --- file actions ---------------------------------------------------------------------

    def _changed_file(self, old, new=None):
        """A file was rotated, edited, saved as a copy or deleted: update the
        viewer and the gallery without a full rescan."""
        new = new or old
        stat = None
        try:
            stat = os.stat(new)
        except OSError:
            pass
        for collection in (self._items, self._viewer):
            for i, item in enumerate(list(collection)):
                if item["path"] == old:
                    if stat is None:
                        collection.pop(i)
                    elif new == old:
                        collection[i] = dict(item, mtime=int(stat.st_mtime), size=stat.st_size)
                    break
        if stat is not None and new != old:
            entry = {"path": new, "kind": library.kind_of(new),
                     "date": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                     "taken": False, "mtime": int(stat.st_mtime), "size": stat.st_size}
            self._items.insert(0, entry)
            at = next((i for i, item in enumerate(self._viewer) if item["path"] == old), -1)
            self._viewer.insert(at + 1, entry)
            self._viewer_index = at + 1
        self._viewer_index = min(self._viewer_index, len(self._viewer) - 1)
        self._relayout()
        self.viewerChanged.emit()

    @Slot(str, result=bool)
    def rotate(self, path):
        """Turn a picture 90° clockwise and save it, as Windows does."""
        try:
            edit.save(path, rotation=90)
        except Exception as error:  # read-only folder, unknown format
            self.message.emit(self._texts["cant_save"].format(error=error))
            return False
        self._changed_file(path)
        return True

    @Slot(str, "QVariantMap", bool, result=str)
    def saveEdit(self, path, edits, as_copy):
        target = edit.copy_name(path, self._texts["copy_word"]) if as_copy else None
        params = {"rotation": int(edits.get("rotation", 0)), "flip": bool(edits.get("flip", False)),
                  "crop": edits.get("crop") or None}
        for name in edit.ADJUSTMENTS:
            params[name] = int(edits.get(name, 0))
        try:
            saved = edit.save(path, target, **params)
        except Exception as error:
            self.message.emit(self._texts["cant_save"].format(error=error))
            return ""
        self._changed_file(path, saved)
        return saved

    @Slot(str, result=bool)
    def deleteFile(self, path):
        ok = run(["kioclient", "move", QUrl.fromLocalFile(path).toString(), "trash:/"]) \
            or run(["gio", "trash", path])
        if ok:
            favorites = [f for f in self.favorites if f != path]
            self._save("favorites", favorites)
            self._changed_file(path)
        return ok

    @Slot(str)
    def copyImage(self, path):
        image = QImage(path)
        if not image.isNull():
            QGuiApplication.clipboard().setImage(image)
            self.message.emit(self._texts["copied"])

    @Slot(str)
    def setBackground(self, path):
        if run(["plasma-apply-wallpaperimage", path]):
            self.message.emit(self._texts["background_set"])

    @Slot(str)
    def setLockScreen(self, path):
        url = QUrl.fromLocalFile(path).toString()
        base = ["kwriteconfig6", "--file", "kscreenlockerrc", "--group", "Greeter", "--group", "Wallpaper",
                "--group", "org.kde.image", "--group", "General"]
        if run(base + ["--key", "Image", url]) and run(base + ["--key", "PreviewImage", url]):
            self.message.emit(self._texts["lock_set"])

    @Slot(str)
    def showInFolder(self, path):
        url = QUrl.fromLocalFile(path).toString()
        detached(["dbus-send", "--session", "--type=method_call", "--dest=org.freedesktop.FileManager1",
                  "/org/freedesktop/FileManager1", "org.freedesktop.FileManager1.ShowItems",
                  f"array:string:{url}", "string:"])

    @Slot(str)
    def playVideo(self, path):
        if not detached(["veltos-media", path]):
            detached(["xdg-open", path])


def main(argv=None):
    argv = sys.argv if argv is None else argv
    files = [a for a in argv[1:] if not a.startswith("-")]
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-photos")
    app.setDesktopFileName("veltos-photos")
    app.setWindowIcon(QIcon.fromTheme("veltos-photos"))
    backend = Backend()
    if files:
        path = Path(QUrl(files[0]).toLocalFile() if files[0].startswith("file:") else files[0])
        if library.kind_of(path.name) == "video":
            backend.playVideo(str(path))
            return 0
        backend.open_file(path)
    app.setApplicationDisplayName(backend.texts["app_title"])
    qml = QQmlApplicationEngine()
    qml.addImageProvider("thumb", ThumbnailProvider())
    qml.addImageProvider("icon", IconProvider())
    qml.rootContext().setContextProperty("backend", backend)
    qml.rootContext().setContextProperty("openedFile", bool(files))
    qml.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not qml.rootObjects():
        return 1
    from .frame import follow_frame
    follow_frame(qml.rootObjects()[0])
    code = app.exec()
    sys.stdout.flush()
    os._exit(code)
