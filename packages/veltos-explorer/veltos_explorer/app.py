"""VeltOS File Explorer: Python backend for the QML user interface.

    veltos-explorer [FOLDER|URL ...]     (no argument: Home)
"""

import os
import sys
import urllib.parse
from pathlib import Path

from PySide6.QtCore import (Property, QFileSystemWatcher, QMimeData, QObject, Qt, QUrl, Signal,
                            Slot)
from PySide6.QtGui import QGuiApplication, QIcon, QRegion
from PySide6.QtQml import QQmlApplicationEngine

from . import files, models, ops, places, strings, thumbnails
from .models import HOME, SPECIAL, THIS_PC, TRASH, Jobs, MimeTypes, Tab

QML_DIR = Path(__file__).resolve().parent / "qml"
CUT_MIME = "application/x-kde-cutselection"
GNOME_MIME = "x-special/gnome-copied-files"
# Folders that open with large icons (pictures), like Windows.
PICTURE_VIEWS = ("PICTURES", "VIDEOS")


def to_path(argument):
    """A command-line argument or URL as a local path, or a special place."""
    if argument in SPECIAL:
        return argument
    if argument.startswith("file:"):
        return urllib.parse.unquote(urllib.parse.urlparse(argument).path) or "/"
    if argument.startswith("trash:"):
        return TRASH
    return os.path.abspath(os.path.expanduser(argument))


class Backend(QObject):
    tabsChanged = Signal()
    currentChanged = Signal()
    placesChanged = Signal()
    drivesChanged = Signal()
    clipboardChanged = Signal()
    settingsChanged = Signal()
    message = Signal(str)                  # a short error to show

    def __init__(self, lang=None, start=None, threaded=True, runner=places.run, open_paths=()):
        super().__init__()
        self.lang = lang or strings.language()
        self.jobs = Jobs(threaded)
        self.ops = ops.Operations(start) if start else ops.Operations()
        self.runner = runner
        self.prefs = places.Pins()
        self.mime = MimeTypes(self.lang)
        self._drives = []
        self._recent = []
        self._tabs = []
        self._current = 0
        self._clipboard = {"paths": [], "cut": False}
        for path in open_paths or [HOME]:
            self._tabs.append(Tab(self, to_path(path), self))
        self._dark = self.read_dark_mode()
        # kdeglobals is replaced (not edited) when it changes: watch its folder.
        self.config_watcher = QFileSystemWatcher(self)
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        if config_dir.is_dir():
            self.config_watcher.addPath(str(config_dir))
        self.config_watcher.directoryChanged.connect(self._config_changed)
        self.refreshDrives()
        self.refreshRecent()
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.dataChanged.connect(self._clipboard_changed)

    # --- texts ---------------------------------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot(str, str, str, result=str)
    def format(self, key, field, value):
        return strings.text(self.lang, key).replace("{" + field + "}", value)

    @Property(str, constant=True)
    def language(self):
        return self.lang

    # --- places --------------------------------------------------------------------------

    def resolve(self, location):
        location = location.strip()
        if location in SPECIAL:
            return location
        if location.lower() in ("this pc", "bu bilgisayar"):
            return THIS_PC
        path = to_path(location)
        if os.path.isdir(path):
            return str(Path(path))
        if os.path.exists(path):
            self.ops.open(path)
            return None
        self.message.emit(self.text("cannot_open").replace("{name}", location))
        return None

    def location_title(self, location):
        if location == HOME:
            return self.text("home")
        if location == THIS_PC:
            return self.text("this_pc")
        if location == TRASH:
            return self.text("recycle_bin")
        if location == "/":
            return self.text("local_disk")
        path = Path(location)
        if path == Path.home():
            return path.name
        return path.name or location

    def location_icon(self, location):
        return {HOME: "go-home", THIS_PC: "computer", TRASH: "user-trash"}.get(
            location, places.folder_icon(location))

    @Property("QVariantList", notify=placesChanged)
    def pinned(self):
        result = []
        for path in self.prefs.pinned():
            if os.path.isdir(path):
                result.append({"name": Path(path).name, "path": path,
                               "icon": places.folder_icon(path)})
        return result

    @Slot(str)
    def pin(self, path):
        self.prefs.pin(path)
        self.placesChanged.emit()

    @Slot(str)
    def unpin(self, path):
        self.prefs.unpin(path)
        self.placesChanged.emit()

    @Slot(str, result=bool)
    def isPinned(self, path):
        return path in self.prefs.pinned()

    @Property("QVariantList", notify=drivesChanged)
    def drives(self):
        return self._drives

    @Slot()
    def refreshDrives(self):
        def done(result):
            if isinstance(result, list):
                for d in result:
                    d["title"] = self.drive_title(d)
                    free = max(0, d["size"] - d["used"])
                    d["freeText"] = (strings.text(self.lang, "free_of", free=files.human_size(free),
                                                  total=files.human_size(d["size"]))
                                     if d["mount"] else self.text("not_mounted"))
                    d["fraction"] = d["used"] / d["size"] if d["size"] and d["mount"] else 0
                self._drives = result
                self.drivesChanged.emit()
        self.jobs.submit(lambda: places.drives(self.runner), done)

    def drive_title(self, drive):
        if drive["system"]:
            return self.text("local_disk")
        if drive["label"]:
            return drive["label"]
        name = self.text("usb_drive") if drive["removable"] else self.text("local_disk")
        return f"{name} ({files.human_size(drive['size'])})"

    @Slot(str)
    def openDrive(self, device):
        drive = next((d for d in self._drives if d["device"] == device or d["mount"] == device), None)
        if drive is None:
            return
        if drive["mount"]:
            self.current_tab().navigate(drive["mount"])
            return

        def done(mount_point):
            if isinstance(mount_point, str) and mount_point:
                self.refreshDrives()
                self.current_tab().navigate(mount_point)
        self.jobs.submit(lambda: places.mount(drive["device"], self.runner), done)

    @Slot(str)
    def ejectDrive(self, device):
        self.jobs.submit(lambda: places.eject(device, self.runner), lambda _r: self.refreshDrives())

    @Property("QVariantList", notify=placesChanged)
    def recent(self):
        return self._recent

    @Slot()
    def refreshRecent(self):
        def done(paths):
            if not isinstance(paths, list):
                return
            model = models.FolderModel(self.lang)
            result = []
            for path in paths:
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                item = files.entry_for(path, st, self.mime)
                item["modifiedText"] = model.format_time(st.st_mtime)
                item["folder"] = self.location_title(str(Path(path).parent)) \
                    if Path(path).parent == Path.home() else str(Path(path).parent).replace(str(Path.home()), "~", 1)
                result.append(item)
            self._recent = result
            self.placesChanged.emit()
        self.jobs.submit(lambda: places.recent_files(20), done)

    # --- settings ------------------------------------------------------------------------

    @Property(bool, notify=settingsChanged)
    def showHidden(self):
        return bool(self.prefs.get("show_hidden", False))

    @Slot(bool)
    def setShowHidden(self, show):
        self.prefs.set("show_hidden", bool(show))
        self.settingsChanged.emit()
        for tab in self._tabs:
            tab.load(keep_selection=True)

    @property
    def show_hidden(self):
        return bool(self.prefs.get("show_hidden", False))

    def view_for(self, location):
        views = self.prefs.get("views", {})
        if isinstance(views, dict) and views.get(location) in models.VIEW_MODES:
            return views[location]
        if location == THIS_PC:
            return "tiles"
        for key, path, _icon in places.user_dirs():
            if path == location and key in PICTURE_VIEWS:
                return "large"
        return "details"

    def remember_view(self, location, mode):
        views = self.prefs.get("views", {})
        views = dict(views) if isinstance(views, dict) else {}
        views[location] = mode
        if len(views) > 500:
            views.pop(next(iter(views)))
        self.prefs.set("views", views)

    # --- tabs ----------------------------------------------------------------------------

    @Property("QVariantList", notify=tabsChanged)
    def tabs(self):
        return list(self._tabs)

    @Property(int, notify=currentChanged)
    def currentIndex(self):
        return self._current

    @Property(QObject, notify=currentChanged)
    def current(self):
        return self.current_tab()

    def current_tab(self):
        return self._tabs[self._current]

    @Slot(int)
    def setCurrentIndex(self, index):
        if 0 <= index < len(self._tabs) and index != self._current:
            self._current = index
            self.currentChanged.emit()

    @Slot(str)
    def newTab(self, location=HOME):
        tab = Tab(self, self.resolve(location) or HOME, self)
        self._tabs.insert(self._current + 1, tab)
        self._current += 1
        self.tabsChanged.emit()
        self.currentChanged.emit()

    @Slot(int, result=bool)
    def closeTab(self, index):
        """Close a tab; False when it was the last one (the window closes)."""
        if not 0 <= index < len(self._tabs):
            return True
        if len(self._tabs) == 1:
            return False
        tab = self._tabs.pop(index)
        tab.deleteLater()
        if self._current >= len(self._tabs) or index < self._current:
            self._current = max(0, self._current - 1)
        self.tabsChanged.emit()
        self.currentChanged.emit()
        return True

    # --- opening -------------------------------------------------------------------------

    @Slot(str)
    def open(self, path):
        """Open an item: folders in the current tab, files with their app."""
        if path in SPECIAL or os.path.isdir(path):
            self.current_tab().navigate(path)
        else:
            self.ops.open(path)

    @Slot()
    def openSelection(self):
        tab = self.current_tab()
        chosen = tab.model.selected_items()
        folders = [i for i in chosen if i["isDir"]]
        if len(folders) == 1 and len(chosen) == 1:
            tab.navigate(folders[0]["path"])
            return
        for item in chosen:
            if item["isDir"]:
                self.newTab(item["path"])
            else:
                self.ops.open(item["path"])

    @Slot(str)
    def openInNewTab(self, path):
        self.newTab(path)

    @Slot(str, result="QVariantList")
    def appsFor(self, path):
        mime_name, _type, _icon = self.mime(path, os.path.isdir(path))
        return places.applications_for(mime_name, self.lang)

    @Slot(str)
    def openWith(self, desktop_path):
        paths = [i["path"] for i in self.current_tab().model.selected_items()]
        if paths:
            self.ops.open_with(desktop_path, paths)

    @Slot()
    def properties(self):
        tab = self.current_tab()
        chosen = tab.model.selected_items()
        target = chosen[0]["path"] if chosen else tab.location
        if target not in SPECIAL:
            self.ops.properties(target)

    @Slot(str)
    def propertiesOf(self, path):
        if path and path not in SPECIAL:
            self.ops.properties(path)

    @Slot(str)
    def terminalAt(self, path):
        self.ops.terminal(path if os.path.isdir(path) else str(Path.home()))

    @Slot(str)
    def copyPathText(self, path):
        QGuiApplication.clipboard().setText(f'"{path}"')

    @Slot(str)
    def openLocation(self, path):
        """"Open file location": the folder, with the file selected."""
        tab = self.current_tab()
        tab._select_after = path
        tab.navigate(str(Path(path).parent))

    @Slot()
    def newWindow(self):
        ops.detached([sys.executable, "-m", "veltos_explorer"])

    @Property(bool, notify=settingsChanged)
    def darkMode(self):
        return self._dark

    def _config_changed(self, _path=""):
        """Follow a switch between light and dark mode while open."""
        dark = self.read_dark_mode()
        if dark != self._dark:
            self._dark = dark
            self.settingsChanged.emit()

    @staticmethod
    def read_dark_mode():
        config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kdeglobals"
        for path in (config, Path("/etc/xdg/kdeglobals")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                if line.startswith(("LookAndFeelPackage=", "ColorScheme=")):
                    return "dark" in line.lower()
        return False

    @Slot()
    def openTerminal(self):
        location = self.current_tab().location
        self.ops.terminal(location if location not in SPECIAL else str(Path.home()))

    # --- clipboard -----------------------------------------------------------------------

    def _selected_paths(self):
        return [i["path"] for i in self.current_tab().model.selected_items()]

    def _set_clipboard(self, paths, cut):
        data = QMimeData()
        data.setUrls([QUrl.fromLocalFile(p) for p in paths])
        data.setData(CUT_MIME, b"1" if cut else b"0")
        data.setData(GNOME_MIME, ("cut" if cut else "copy").encode() + b"".join(
            b"\n" + QUrl.fromLocalFile(p).toEncoded().data() for p in paths))
        data.setText("\n".join(paths))
        QGuiApplication.clipboard().setMimeData(data)
        self._clipboard = {"paths": list(paths), "cut": cut}
        self._mark_cut()

    def _clipboard_changed(self):
        data = QGuiApplication.clipboard().mimeData()
        paths = [u.toLocalFile() for u in data.urls() if u.isLocalFile()] if data else []
        cut = bool(data and data.data(CUT_MIME).data() == b"1")
        self._clipboard = {"paths": paths, "cut": cut}
        self._mark_cut()
        self.clipboardChanged.emit()

    def _mark_cut(self):
        for tab in self._tabs:
            tab.model.set_cut(self.cut_paths_in(tab.location))
        self.clipboardChanged.emit()

    def cut_paths_in(self, location):
        if not self._clipboard["cut"]:
            return []
        return [p for p in self._clipboard["paths"] if str(Path(p).parent) == location]

    @Property(bool, notify=clipboardChanged)
    def canPaste(self):
        return bool(self._clipboard["paths"])

    @Slot()
    def copy(self):
        paths = self._selected_paths()
        if paths:
            self._set_clipboard(paths, False)

    @Slot()
    def cut(self):
        paths = self._selected_paths()
        if paths:
            self._set_clipboard(paths, True)

    @Slot()
    def copyAsPath(self):
        paths = self._selected_paths() or [self.current_tab().location]
        QGuiApplication.clipboard().setText("\n".join(f'"{p}"' for p in paths))

    @Slot()
    @Slot(str)
    def paste(self, destination=""):
        destination = destination or self.current_tab().location
        if destination in SPECIAL or not os.path.isdir(destination):
            return
        paths = [p for p in self._clipboard["paths"] if os.path.exists(p)]
        if not paths:
            return
        if self._clipboard["cut"]:
            self.ops.move(paths, destination)
            QGuiApplication.clipboard().clear()
            self._clipboard = {"paths": [], "cut": False}
            self._mark_cut()
        else:
            self.ops.copy(paths, destination)

    @staticmethod
    def _local_paths(urls):
        paths = [QUrl(u).toLocalFile() if isinstance(u, str) else u.toLocalFile() for u in urls]
        return [p for p in paths if p and os.path.exists(p)]

    @Slot(list, str)
    def drop(self, urls, destination):
        """Files dropped on a folder: moved within a drive, copied between
        drives (Windows' rule); holding Ctrl copies, Shift moves."""
        paths = [p for p in self._local_paths(urls) if p != destination]
        if not paths or destination in SPECIAL or not os.path.isdir(destination):
            return
        if destination == TRASH:
            self.ops.trash(paths)
            return
        modifiers = QGuiApplication.queryKeyboardModifiers()
        same_drive = all(os.stat(p).st_dev == os.stat(destination).st_dev for p in paths)
        if modifiers & Qt.ControlModifier or (not same_drive and not modifiers & Qt.ShiftModifier):
            self.ops.copy(paths, destination)
        else:
            self.ops.move(paths, destination)

    @Slot(list)
    def dropToTrash(self, urls):
        self.ops.trash(self._local_paths(urls))

    # --- changing items --------------------------------------------------------------

    @Slot(bool)
    def deleteSelection(self, permanently):
        tab = self.current_tab()
        paths = self._selected_paths()
        if not paths:
            return
        if tab.location == TRASH or permanently:
            self.ops.delete(paths)
        else:
            self.ops.trash(paths)

    @Slot(str, str, result=str)
    def rename(self, path, new_name):
        """"" when renamed, else the message to show."""
        reason = ops.Operations.rename(path, new_name)
        if not reason:
            new_path = str(Path(path).parent / new_name.strip())
            tab = self.current_tab()
            tab._select_after = new_path
            tab.load(keep_selection=False)
            return ""
        return {"exists": self.text("rename_exists"), "invalid": self.text("rename_invalid"),
                "empty": self.text("rename_empty")}.get(reason, reason)

    @Slot(str)
    def createNew(self, what):
        tab = self.current_tab()
        folder = tab.location
        if folder in SPECIAL:
            return
        try:
            if what == "folder":
                name = self.ops.new_folder(folder, self.text("new_folder_name"))
            else:
                name = self.ops.new_file(folder, self.text("new_text_name"))
        except OSError as error:
            self.message.emit(error.strerror or str(error))
            return
        path = str(Path(folder) / name)
        tab._select_after = path
        tab.load()
        tab.request_rename(path)

    @Slot()
    def compress(self):
        tab = self.current_tab()
        paths = self._selected_paths()
        if paths and tab.location not in SPECIAL:
            self.ops.compress(paths, tab.location)

    @Slot(str)
    def extract(self, path):
        self.ops.extract(path, str(Path(path).parent))

    @Slot(str, result=bool)
    def isArchive(self, path):
        return self.mime(path, False)[0] in ("application/zip", "application/x-7z-compressed",
                                             "application/x-rar", "application/vnd.rar",
                                             "application/x-compressed-tar", "application/x-xz-compressed-tar",
                                             "application/x-bzip-compressed-tar", "application/x-tar",
                                             "application/zstd", "application/x-zstd-compressed-tar")

    # --- Recycle Bin ---------------------------------------------------------------------

    def trash_entries(self):
        model = models.FolderModel(self.lang)
        result = []
        for item in places.trash_items():
            try:
                st = os.lstat(item["path"])
            except OSError:
                continue
            entry = files.entry_for(item["path"], st, self.mime)
            entry["original"] = str(Path(item["original"]).parent) if item["original"] else ""
            entry["deletedText"] = models.deleted_text(item["deleted"], model)
            result.append(entry)
        return result

    @Slot()
    def restoreSelection(self):
        problems = [places.restore(p) for p in self._selected_paths()]
        if "exists" in problems:
            self.message.emit(self.text("restore_exists"))
        self.current_tab().load()

    @Slot()
    def emptyTrash(self):
        self.ops.empty_trash()

    # --- thumbnails ----------------------------------------------------------------------

    def make_thumbnails(self, tab, items, generation):
        pictures = [i for i in items if i.get("mime") in thumbnails.PICTURE_TYPES][:400]
        if not pictures:
            return
        large = tab.viewMode in ("large", "xlarge")

        def work():
            made = {}
            for item in pictures:
                if generation != tab._generation:
                    break
                thumb = thumbnails.cached(item["path"], large) or thumbnails.make(item["path"], large)
                if thumb:
                    made[item["path"]] = "file://" + thumb
            return made

        def done(made):
            if isinstance(made, dict) and generation == tab._generation:
                for path, thumb in made.items():
                    tab.model.update_item(path, thumbnail=thumb)
        self.jobs.submit(work, done)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    app.setApplicationName("veltos-explorer")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-explorer")
    if not QIcon.themeName() or QIcon.themeName() == "hicolor":
        # Started outside Plasma (no platform theme): use the system's icons.
        QIcon.setThemeName(icon_theme())
    app.setWindowIcon(QIcon.fromTheme("system-file-manager"))
    backend = Backend(open_paths=argv[1:])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    follow_frame(engine.rootObjects()[0])
    code = app.exec()
    # Leave without Python's and Qt's clean-up: files copied to the
    # clipboard are a QMimeData made in Python, and Qt deleting it after
    # Python has shut down crashes the process (PySide6 6.8). The data stays
    # available through the clipboard manager. Preferences are already saved.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def icon_theme():
    """The icon theme named in kdeglobals ([Icons] Theme), else Fluent."""
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kdeglobals"
    for path in (config, Path("/etc/xdg/kdeglobals")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        section = text.split("[Icons]", 1)
        if len(section) == 2:
            for line in section[1].splitlines():
                if line.startswith("["):
                    break
                if line.startswith("Theme="):
                    return line.split("=", 1)[1].strip()
    return "Fluent"


def follow_frame(window):
    """Clicks on the drawn shadow around the window go to what is behind
    it: the input region is the frame only (the mask is an input region on
    Wayland)."""
    def update(*_args):
        margin = int(window.property("shadow") or 0)
        if margin:
            window.setMask(QRegion(margin, margin, max(1, window.width() - 2 * margin),
                                   max(1, window.height() - 2 * margin)))
        else:
            window.setMask(QRegion())
    for signal in (window.widthChanged, window.heightChanged, window.visibilityChanged):
        signal.connect(update)
    update()
