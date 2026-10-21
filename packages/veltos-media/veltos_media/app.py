"""VeltOS Media Player: Windows 11's Media Player on VeltOS.

The window (qml/Main.qml) has the navigation pane (search, Home, Music
library, Video library, Play queue, Playlists, Settings), the pages, the
player bar at the bottom and the "now playing" view (the video, or the
album picture of a song). Qt Multimedia (FFmpeg) plays in QML; this module
keeps the library (library.py: tags and covers through mutagen), the play
queue with shuffle and repeat (playqueue.py), playlists, recent media,
the volume and the settings.
"""

import configparser
import json
import os
import subprocess
import sys
import threading
import traceback
import urllib.parse
from pathlib import Path

from PySide6.QtCore import (QFileSystemWatcher, QObject, QSettings, Qt, QUrl, Property, Signal, Slot)
from PySide6.QtGui import QGuiApplication, QIcon, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow

from . import library, playqueue, strings, thumbs

VERSION = "0.1"
QML_DIR = Path(__file__).resolve().parent / "qml"
THEMES = ("light", "dark", "system")
MAX_RECENT = 24


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


class ThumbnailProvider(QQuickImageProvider):
    """image://thumb/<mtime>/<quoted path>: a video's frame (shared
    freedesktop.org thumbnail cache, ffmpegthumbnailer)."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image,
                         QQuickImageProvider.Flag.ForceAsynchronousImageLoading)

    def requestImage(self, image_id, size, requested_size):
        try:
            _mtime, quoted = image_id.split("/", 1)
            image = thumbs.thumbnail(urllib.parse.unquote(quoted), "video", "large")
        except Exception:  # never take a page down for one file
            traceback.print_exc()
            image = QImage()
        if image.isNull():
            image = QImage(1, 1, QImage.Format.Format_ARGB32)
            image.fill(0)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


class Backend(QObject):
    themeChanged = Signal()
    settingsChanged = Signal()
    libraryChanged = Signal()
    queueChanged = Signal()
    currentChanged = Signal()
    playlistsChanged = Signal()
    recentChanged = Signal()
    volumeChanged = Signal()
    message = Signal(str)
    _scanned = Signal(object)

    def __init__(self, lang=None, settings=None, scan=True, parent=None):
        super().__init__(parent)
        self._lang = lang or strings.language()
        self._texts = strings.texts(self._lang)
        self._settings = settings if settings is not None else QSettings(
            str(config_home() / "veltos/media.conf"), QSettings.Format.IniFormat)
        self.queue = playqueue.PlayQueue()
        self.queue.shuffle = self._settings.value("shuffle", False) in (True, "true", "1", 1)
        repeat = str(self._settings.value("repeat", "off"))
        self.queue.repeat = repeat if repeat in playqueue.REPEAT_MODES else "off"
        self._songs, self._videos = [], []
        self._by_path = {}
        self._scanning = False
        self._token = 0
        self._system_dark = system_dark()
        self._accent = system_accent()
        self._watcher = QFileSystemWatcher(self)
        for path in (config_home(), config_home() / "kdeglobals"):
            if path.exists():
                self._watcher.addPath(str(path))
        self._watcher.directoryChanged.connect(self._reread_theme)
        self._watcher.fileChanged.connect(self._reread_theme)
        self._scanned.connect(self._take_scan, Qt.QueuedConnection)
        self._cache_file = cache_home() / "veltos/media-index.json"
        self._cover_dir = cache_home() / "veltos/media-covers"
        if scan:
            self.refresh()

    # --- theme and settings -------------------------------------------------------------

    def _reread_theme(self, *_args):
        dark, accent = system_dark(), system_accent()
        if (dark, accent) != (self._system_dark, self._accent):
            self._system_dark, self._accent = dark, accent
            self.themeChanged.emit()

    def _list(self, key):
        value = self._settings.value(key, [])
        if value in (None, ""):
            return []
        return [value] if isinstance(value, str) else list(value)

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
        theme = str(self._settings.value("theme", "system"))
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

    @Property(int, notify=volumeChanged)
    def volume(self):
        try:
            return max(0, min(100, int(self._settings.value("volume", 80))))
        except (TypeError, ValueError):
            return 80

    @Slot(int)
    def setVolume(self, value):
        self._save("volume", max(0, min(100, int(value))))
        self.volumeChanged.emit()

    @Property(bool, notify=volumeChanged)
    def muted(self):
        return self._settings.value("muted", False) in (True, "true", "1", 1)

    @Slot(bool)
    def setMuted(self, on):
        self._save("muted", bool(on))
        self.volumeChanged.emit()

    # --- library ----------------------------------------------------------------------------

    @Property("QStringList", notify=settingsChanged)
    def musicFolders(self):
        return self._list("musicFolders") or [str(library.user_dir("MUSIC", "Music"))]

    @Property("QStringList", notify=settingsChanged)
    def videoFolders(self):
        return self._list("videoFolders") or [str(library.user_dir("VIDEOS", "Videos"))]

    @Slot(str, str)
    def addFolder(self, kind, url):
        path = QUrl(url).toLocalFile() if url.startswith("file:") else url
        if not path or not Path(path).is_dir():
            return
        key = "musicFolders" if kind == "music" else "videoFolders"
        folders = self.musicFolders if kind == "music" else self.videoFolders
        if path not in folders:
            self._save(key, folders + [path])
            self.settingsChanged.emit()
            self.refresh()

    @Slot(str, str)
    def removeFolder(self, kind, path):
        key = "musicFolders" if kind == "music" else "videoFolders"
        folders = [f for f in (self.musicFolders if kind == "music" else self.videoFolders) if f != path]
        self._save(key, folders)
        self.settingsChanged.emit()
        self.refresh()

    @Slot(str, result=str)
    def folderName(self, path):
        return Path(path).name or path

    @Property(bool, notify=libraryChanged)
    def scanning(self):
        return self._scanning

    @Slot()
    def refresh(self):
        if self._scanning:
            return
        self._scanning = True
        self.libraryChanged.emit()
        music, videos = self.musicFolders, self.videoFolders

        def work():
            try:
                cache = library.load_cache(self._cache_file)
                result = library.scan(music, videos, self._cover_dir, cache)
                library.save_cache(self._cache_file, result[0] + result[1])
            except Exception:
                traceback.print_exc()
                result = ([], [])
            self._scanned.emit(result)
        threading.Thread(target=work, daemon=True).start()

    def scan_now(self):
        """Scan in this thread (tests)."""
        self._take_scan(library.scan(self.musicFolders, self.videoFolders, self._cover_dir))

    def _take_scan(self, result):
        self._songs, self._videos = result or ([], [])
        self._by_path = {e["path"]: e for e in self._songs + self._videos}
        self._scanning = False
        self.libraryChanged.emit()
        self.recentChanged.emit()
        self.playlistsChanged.emit()

    @Property("QVariantList", notify=libraryChanged)
    def songs(self):
        return self._songs

    @Property("QVariantList", notify=libraryChanged)
    def albums(self):
        return library.albums(self._songs)

    @Property("QVariantList", notify=libraryChanged)
    def artists(self):
        return library.artists(self._songs)

    @Property("QVariantList", notify=libraryChanged)
    def videos(self):
        return self._videos

    def entry(self, path):
        """The library entry of a path, or one read now (files opened from
        File Explorer that are not in the library)."""
        path = str(path)
        if path in self._by_path:
            return self._by_path[path]
        kind = library.kind_of(path)
        if kind == "audio":
            entry = library.song(path, self._cover_dir)
        elif kind == "video":
            entry = library.video(path)
        else:
            entry = {"path": path, "kind": "video", "title": Path(path).stem, "duration": 0}
        self._by_path[path] = entry
        return entry

    @Slot(int, result=str)
    def durationText(self, seconds):
        return library.duration_text(seconds)

    @Slot(int, result=str)
    def songCount(self, count):
        return self._texts["one_song"] if count == 1 else self._texts["songs_count"].format(count=count)

    @Slot(str, result=str)
    def fileUrl(self, path):
        return QUrl.fromLocalFile(path).toString() if path else ""

    @Slot(str, int, result=str)
    def thumbUrl(self, path, mtime):
        return f"image://thumb/{mtime}/{urllib.parse.quote(path, safe='')}"

    @Slot(str, result="QVariantList")
    def search(self, text):
        words = text.lower().split()
        if not words:
            return []

        # The file name, not its folders: every song under a folder named
        # "2024" matched "2" (the test failed with such temporary folders).
        def hit(e):
            haystack = " ".join([str(e.get(k, "")) for k in ("title", "artist", "album")]
                                + [Path(e.get("path", "")).name]).lower()
            return all(w in haystack for w in words)
        return [e for e in self._songs + self._videos if hit(e)][:200]

    # --- playing --------------------------------------------------------------------------

    @Property("QVariantMap", notify=currentChanged)
    def current(self):
        return self.queue.current or {}

    @Property(int, notify=currentChanged)
    def playToken(self):
        """Changes on every play request, so QML restarts the same file too."""
        return self._token

    def _started(self):
        self._token += 1
        current = self.queue.current
        if current:
            recent = [current["path"]] + [p for p in self._list("recent") if p != current["path"]]
            self._save("recent", recent[:MAX_RECENT])
            self.recentChanged.emit()
        self.currentChanged.emit()
        self.queueChanged.emit()

    @Slot("QStringList", int)
    def playPaths(self, paths, start):
        """Play a list (a page's songs, an album, files) from `start`."""
        entries = [self.entry(p if not p.startswith("file:") else QUrl(p).toLocalFile()) for p in paths]
        if not entries:
            return
        self.queue.play(entries, start)
        self._started()

    @Slot()
    def shuffleAll(self):
        if self._songs:
            self.queue.set_shuffle(True)
            self._save("shuffle", True)
            self.queue.play(self._songs, int.from_bytes(os.urandom(2), "big") % len(self._songs))
            self._started()

    @Slot("QStringList")
    def addToQueue(self, paths):
        was_empty = self.queue.current is None
        self.queue.add([self.entry(p) for p in paths])
        if was_empty:
            self._started()
        else:
            self.queueChanged.emit()

    @Slot("QStringList")
    def playNext(self, paths):
        """Put songs right after the current one."""
        if self.queue.current is None:
            self.playPaths(paths, 0)
            return
        items = self.queue.in_order()
        at = self.queue.index + 1
        items[at:at] = [self.entry(p) for p in paths]
        shuffle = self.queue.shuffle
        self.queue.shuffle = False
        self.queue.play(items, self.queue.index)
        self.queue.shuffle = shuffle
        self.queueChanged.emit()

    @Slot()
    def next(self):
        if self.queue.next(finished=False) is not None:
            self._started()

    @Slot()
    def previous(self):
        if self.queue.previous() is not None:
            self._started()

    @Slot(result=bool)
    def ended(self):
        """The current item played to its end: the next one, or stop."""
        if self.queue.next(finished=True) is None:
            return False
        self._started()
        return True

    @Property("QVariantList", notify=queueChanged)
    def queueItems(self):
        return self.queue.in_order()

    @Property(int, notify=queueChanged)
    def queueIndex(self):
        return self.queue.index

    @Slot(int)
    def goQueue(self, position):
        if self.queue.go(position) is not None:
            self._started()

    @Slot(int)
    def removeFromQueue(self, position):
        playing = self.queue.index == position
        self.queue.remove(position)
        self.queueChanged.emit()
        if playing:
            self._started()

    @Slot()
    def clearQueue(self):
        self.queue.clear()
        self._token += 1
        self.queueChanged.emit()
        self.currentChanged.emit()

    @Property(bool, notify=queueChanged)
    def shuffle(self):
        return self.queue.shuffle

    @Slot(bool)
    def setShuffle(self, on):
        self.queue.set_shuffle(on)
        self._save("shuffle", on)
        self.queueChanged.emit()

    @Property(str, notify=queueChanged)
    def repeat(self):
        return self.queue.repeat

    @Slot()
    def cycleRepeat(self):
        self._save("repeat", self.queue.cycle_repeat())
        self.queueChanged.emit()

    # --- recent media and playlists --------------------------------------------------------

    @Property("QVariantList", notify=recentChanged)
    def recent(self):
        return [self.entry(p) for p in self._list("recent") if Path(p).exists()][:12]

    def _playlists(self):
        try:
            data = json.loads(str(self._settings.value("playlists", "[]")))
            return [p for p in data if isinstance(p, dict) and "name" in p]
        except ValueError:
            return []

    def _save_playlists(self, playlists):
        self._save("playlists", json.dumps(playlists))
        self.playlistsChanged.emit()

    @Property("QVariantList", notify=playlistsChanged)
    def playlists(self):
        result = []
        for p in self._playlists():
            entries = [self.entry(path) for path in p.get("paths", []) if Path(path).exists()]
            result.append({"name": p["name"], "items": entries,
                           "cover": next((e.get("cover") for e in entries if e.get("cover")), "")})
        return result

    @Slot(str, result=str)
    def createPlaylist(self, name):
        name = name.strip() or self._texts["untitled_playlist"]
        playlists = self._playlists()
        base, n = name, 2
        while any(p["name"] == name for p in playlists):
            name = f"{base} ({n})"
            n += 1
        playlists.append({"name": name, "paths": []})
        self._save_playlists(playlists)
        return name

    @Slot(str, "QStringList")
    def addToPlaylist(self, name, paths):
        playlists = self._playlists()
        for p in playlists:
            if p["name"] == name:
                p["paths"] = p.get("paths", []) + [path for path in paths if path not in p.get("paths", [])]
        self._save_playlists(playlists)

    @Slot(str, int)
    def removeFromPlaylist(self, name, index):
        playlists = self._playlists()
        for p in playlists:
            if p["name"] == name and 0 <= index < len(p.get("paths", [])):
                p["paths"].pop(index)
        self._save_playlists(playlists)

    @Slot(str)
    def deletePlaylist(self, name):
        self._save_playlists([p for p in self._playlists() if p["name"] != name])

    # --- desktop --------------------------------------------------------------------------

    @Slot(str)
    def showInFolder(self, path):
        url = QUrl.fromLocalFile(path).toString()
        try:
            subprocess.Popen(["dbus-send", "--session", "--type=method_call", "--dest=org.freedesktop.FileManager1",
                              "/org/freedesktop/FileManager1", "org.freedesktop.FileManager1.ShowItems",
                              f"array:string:{url}", "string:"], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass


def main(argv=None):
    argv = sys.argv if argv is None else argv
    files = [a for a in argv[1:] if not a.startswith("-")]
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-media")
    app.setDesktopFileName("veltos-media")
    app.setWindowIcon(QIcon.fromTheme("veltos-media"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    qml = QQmlApplicationEngine()
    qml.addImageProvider("thumb", ThumbnailProvider())
    qml.rootContext().setContextProperty("backend", backend)
    qml.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not qml.rootObjects():
        return 1
    window = qml.rootObjects()[0]
    from .frame import follow_frame
    follow_frame(window)
    if files:
        paths = [QUrl(f).toLocalFile() if f.startswith("file:") else str(Path(f).absolute()) for f in files]
        backend.playPaths(paths, 0)
        window.setProperty("nowPlaying", True)
    code = app.exec()
    sys.stdout.flush()
    os._exit(code)
