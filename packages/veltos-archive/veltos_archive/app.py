"""VeltOS Archive: WinRAR's window on VeltOS (Windows 11 look).

    veltos-archive [ARCHIVE]                     the archive window
    veltos-archive --extract-here ARCHIVE...     extract next to the archive
    veltos-archive --extract-to-folder ARCHIVE...
                                                 extract into "<name>/" next to it
    veltos-archive --add FILE...                 "Add to archive..." (asks name, format)
    veltos-archive --add-to ARCHIVE FILE...      create ARCHIVE at once

The window lists an archive like WinRAR (Name, Size, Packed, Type,
Modified, CRC32, folders inside the archive), with WinRAR's toolbar (Add,
Extract To, Test, View, Delete, Find, Info). The command-line modes show
only WinRAR's small progress window, so File Explorer's "Extract all" and
"Compress" use this app. See archive.py for the commands.
"""

import configparser
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from PySide6.QtCore import (QElapsedTimer, QLocale, QMimeDatabase, QObject, QProcess, QProcessEnvironment,
                            QTimer, QUrl, Property, Signal, Slot)
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import archive, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
SORT_KEYS = ("name", "size", "packed", "type", "modified", "crc")


def kde_value(group, key):
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
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

def dark_mode():
    return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")


def accent():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def group_digits(number, lang):
    text = f"{int(number):,}"
    return text.replace(",", ".") if lang == "tr" else text


class Job(QObject):
    """One 7-Zip or bsdtar run, with WinRAR's progress (QProcess)."""
    changed = Signal()
    done = Signal()

    def __init__(self, kind, title, command, cwd=None, parent=None, entries=0):
        super().__init__(parent)
        self.kind = kind
        # bsdtar prints no percentage: count its "x name" lines instead.
        self.entries = entries
        self._done_entries = 0
        self._title = title
        self.command = command
        self.cwd = cwd
        self._percent = 0
        self._running = False
        self._ok = False
        self._error = ""
        self._error_kind = ""
        self._output = ""
        self._timer = QElapsedTimer()
        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self.changed)
        self.process = None
        self.cancelled = False

    @Property(str, notify=changed)
    def title(self):
        return self._title

    @Property(int, notify=changed)
    def percent(self):
        return self._percent

    @Property(bool, notify=changed)
    def running(self):
        return self._running

    @Property(bool, notify=changed)
    def ok(self):
        return self._ok

    @Property(str, notify=changed)
    def errorKind(self):
        return self._error_kind

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(str, notify=changed)
    def elapsed(self):
        seconds = self._timer.elapsed() // 1000 if self._timer.isValid() else 0
        return str(datetime.timedelta(seconds=int(seconds)))

    def start(self):
        process = QProcess(self)
        env = QProcessEnvironment()
        for key, value in archive.environment().items():
            env.insert(key, value)
        process.setProcessEnvironment(env)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        if self.cwd:
            process.setWorkingDirectory(str(self.cwd))
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._finished)
        process.errorOccurred.connect(self._failed_to_start)
        self.process = process
        self._running = True
        self._timer.start()
        self._tick.start()
        process.start(self.command[0], self.command[1:])
        self.changed.emit()

    def _read(self):
        chunk = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        self._output += chunk
        if self.entries:
            self._done_entries += sum(1 for line in chunk.splitlines() if line.startswith("x "))
            value = min(99, 100 * self._done_entries // self.entries)
        else:
            value = archive.progress(chunk.replace("\b", " "))
        if value is not None and value != self._percent:
            self._percent = value
            self.changed.emit()

    def _failed_to_start(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._finish(False, "error", f"{self.command[0]} could not be started")

    def _finished(self, code, _status):
        if self.cancelled:
            self._finish(False, "cancelled", "")
            return
        kind, message = archive.errors(self._output)
        self._finish(code == 0 and not kind, kind if kind else ("" if code == 0 else "error"),
                     message or ("" if code == 0 else self._output.strip()[-400:]))

    def _finish(self, ok, kind, message):
        if not self._running:
            return
        self._running = False
        self._tick.stop()
        self._ok = ok
        if ok:
            self._percent = 100
        self._error_kind = kind
        self._error = message
        self.changed.emit()
        self.done.emit()

    @Slot()
    def cancel(self):
        if self.process and self._running:
            self.cancelled = True
            self.process.kill()


class Backend(QObject):
    changed = Signal()
    listingChanged = Signal()
    jobChanged = Signal()
    passwordNeeded = Signal(str)          # "open", "extract", "view", "test"
    notice = Signal(str, str)             # title, body (errors, results)
    extracted = Signal(str)               # destination folder (or the new archive's)
    opened = Signal()                     # an archive was listed

    def __init__(self, lang=None, opener=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.t = strings.texts(self.lang)
        self._open = opener or (lambda url: QDesktopServices.openUrl(url))
        self._dark = dark_mode()
        self._accent = accent()
        self._mime = QMimeDatabase()
        self._locale = QLocale(QLocale.Language.Turkish if self.lang == "tr" else QLocale.Language.English,
                               QLocale.Country.Turkey if self.lang == "tr" else QLocale.Country.UnitedStates)
        self.path = None
        self.info = {}
        self.tree = archive.Tree([])
        self._folder = ""
        self._password = ""
        self._pending = None
        self._sort = "name"
        self._ascending = True
        self._find = ""
        self._busy = False
        self._job = None
        self._listing = None
        self._temp = None
        self.tar = False

    # --- properties --------------------------------------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self.t

    @Property(float, constant=True)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(str, constant=True)
    def accent(self):
        return self._accent

    @Property(bool, notify=listingChanged)
    def isOpen(self):
        return self.path is not None

    @Property(str, notify=listingChanged)
    def archiveName(self):
        return self.path.name if self.path else ""

    @Property(str, notify=listingChanged)
    def folder(self):
        return self._folder

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(QObject, notify=jobChanged)
    def job(self):
        return self._job

    @Property(str, notify=listingChanged)
    def sortKey(self):
        return self._sort

    @Property(bool, notify=listingChanged)
    def sortAscending(self):
        return self._ascending

    @Property(str, notify=listingChanged)
    def findQuery(self):
        return self._find

    @Property(bool, notify=listingChanged)
    def canDelete(self):
        return self.path is not None and archive.can_delete(self.info) and not self.info.get("solid")

    @Property(bool, notify=listingChanged)
    def canAdd(self):
        return self.path is None or archive.can_add_to(self.info)

    @Property(bool, notify=listingChanged)
    def locked(self):
        return bool(self.info.get("headersEncrypted")) or self.tree.totals()["encrypted"]

    @Property(str, notify=listingChanged)
    def headerText(self):
        if not self.path:
            return ""
        place = self.path.name + ("\\" + self._folder.replace("/", "\\") if self._folder else "")
        return self.t["header"].format(name=place, type=self.info.get("type", "").upper(),
                                       size=group_digits(self.tree.totals()["size"], self.lang))

    @Property(str, notify=listingChanged)
    def totalText(self):
        rows = self._rows()
        files = [r for r in rows if not r["isDir"]]
        folders = [r for r in rows if r["isDir"]]
        size = group_digits(sum(r["sizeValue"] for r in rows), self.lang)
        if folders:
            return self.t["total"].format(folders=len(folders), files=len(files), size=size)
        return self.t["total_files"].format(files=len(files), size=size)

    @Property("QVariantList", notify=listingChanged)
    def rows(self):
        return self._rows()

    @Property("QVariantList", notify=listingChanged)
    def infoRows(self):
        if not self.path:
            return []
        totals = self.tree.totals()
        ratio = f"{round(100 * totals['packed'] / totals['size'])}%" if totals["size"] else "-"
        yes, no = self.t["yes"], self.t["no"]
        return [
            {"label": self.t["info_type"], "value": self.info.get("type", "").upper()},
            {"label": self.t["info_files"], "value": group_digits(totals["files"], self.lang)},
            {"label": self.t["info_folders"], "value": group_digits(totals["folders"], self.lang)},
            {"label": self.t["info_size"], "value": group_digits(totals["size"], self.lang)},
            {"label": self.t["info_packed"], "value": group_digits(self.info.get("physicalSize")
                                                                   or totals["packed"], self.lang)},
            {"label": self.t["info_ratio"], "value": ratio},
            {"label": self.t["info_solid"], "value": yes if self.info.get("solid") else no},
            {"label": self.t["info_locked"], "value": yes if self.locked else no},
        ]

    # --- rows ----------------------------------------------------------------------------------

    def type_name(self, name, is_dir):
        if is_dir:
            return self.t["folder_type"]
        mime = self._mime.mimeTypeForFile(name, QMimeDatabase.MatchMode.MatchExtension)
        if mime.isValid() and not mime.isDefault():
            comment = mime.comment()
            if comment:
                return comment[:1].upper() + comment[1:]
        ext = PurePosixPath(name).suffix.lstrip(".").upper()
        return self.t["file_type"].format(ext=ext) if ext else self.t["file_type_plain"]

    def icon_name(self, name, is_dir):
        if is_dir:
            return "folder"
        mime = self._mime.mimeTypeForFile(name, QMimeDatabase.MatchMode.MatchExtension)
        return mime.iconName() if mime.isValid() else "text-x-generic"

    def _rows(self):
        if not self.path:
            return []
        if self._find:
            query = self._find.lower()
            items = [dict(e, name=PurePosixPath(e["path"]).name) for e in self.tree.entries.values()
                     if not e["isDir"] and query in PurePosixPath(e["path"]).name.lower()]
        else:
            items = self.tree.children(self._folder)
        rows = []
        for item in items:
            modified = item.get("modified")
            rows.append({
                "name": item["name"] if not self._find else item["path"],
                "path": item["path"],
                "isDir": item["isDir"],
                "sizeValue": item["size"],
                "packedValue": item["packed"],
                "size": group_digits(item["size"], self.lang),
                "packed": group_digits(item["packed"], self.lang),
                "type": self.type_name(item["name"], item["isDir"]),
                "modifiedValue": modified.isoformat() if modified else "",
                "modified": self._locale.toString(modified, QLocale.FormatType.ShortFormat) if modified else "",
                "crc": item.get("crc", ""),
                "encrypted": item.get("encrypted", False),
                "icon": self.icon_name(item["name"], item["isDir"]),
            })
        key = {"name": lambda r: r["name"].lower(), "size": lambda r: r["sizeValue"],
               "packed": lambda r: r["packedValue"], "type": lambda r: r["type"].lower(),
               "modified": lambda r: r["modifiedValue"], "crc": lambda r: r["crc"]}[self._sort]
        rows.sort(key=key, reverse=not self._ascending)
        rows.sort(key=lambda r: not r["isDir"])       # folders first, like WinRAR
        return rows

    @Slot("QVariantList", result=str)
    def selectionText(self, paths):
        selected = [r for r in self._rows() if r["path"] in paths]
        if not selected:
            return self.totalText
        size = group_digits(sum(r["sizeValue"] for r in selected), self.lang)
        if len(selected) == 1:
            return self.t["selected_one"].format(size=size)
        return self.t["selected"].format(count=len(selected), size=size)

    # --- opening -------------------------------------------------------------------------------

    @Slot(str)
    def openArchive(self, location):
        path = Path(QUrl(location).toLocalFile() if location.startswith("file:") else location)
        if not path.is_file():
            return
        self.path = path.resolve()
        self.info = {}
        self.tree = archive.Tree([])
        self._folder = ""
        self._find = ""
        self._password = ""
        self.listingChanged.emit()
        self._list()

    def _list(self):
        self._set_busy(True)
        process = QProcess(self)
        env = QProcessEnvironment()
        for key, value in archive.environment().items():
            env.insert(key, value)
        process.setProcessEnvironment(env)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.finished.connect(lambda _code, _status: self._listed(process))
        process.errorOccurred.connect(
            lambda error: self._listed(process) if error == QProcess.ProcessError.FailedToStart else None)
        self._listing = process
        self.tar = archive.is_compressed_tar(self.path)
        command = (archive.tar_list_command(self.path) if self.tar
                   else archive.list_command(self.path, self._password))
        process.start(command[0], command[1:])

    def _listed(self, process):
        if process is not self._listing:
            return
        self._listing = None
        self._set_busy(False)
        text = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        if self.tar:
            info, entries, error = archive.parse_tar_listing(text, self.path)
        else:
            info, entries, error = archive.parse_listing(text)
        if error == "password":
            wrong = bool(self._password)
            self._password = ""
            self._pending = self._list
            self.passwordNeeded.emit("wrong" if wrong else "open")
            return
        if error and not entries:
            name = self.path.name
            self.path = None
            self.listingChanged.emit()
            self.notice.emit(self.t["failed"], self.t["unsupported"].format(name=name))
            return
        self.info = info
        self.tree = archive.Tree(entries)
        self.listingChanged.emit()
        self.opened.emit()

    def _set_busy(self, busy):
        if busy != self._busy:
            self._busy = busy
            self.changed.emit()

    @Slot(str)
    def setPassword(self, password):
        """The password dialog was confirmed: retry what needed it."""
        self._password = password
        pending, self._pending = self._pending, None
        if pending:
            pending()

    @Slot()
    def cancelPassword(self):
        if self._pending == self._list:
            self.path = None
            self.listingChanged.emit()
        self._pending = None

    # --- browsing ------------------------------------------------------------------------------

    @Slot()
    def goUp(self):
        if self._find:
            self.setFind("")
        elif self._folder:
            parent = str(PurePosixPath(self._folder).parent)
            self._folder = "" if parent == "." else parent
            self.listingChanged.emit()

    @Slot(str)
    def openRow(self, path):
        if self.tree.is_folder(path):
            self._find = ""
            self._folder = path
            self.listingChanged.emit()
        else:
            self.viewItem(path)

    @Slot(str)
    def sortBy(self, key):
        if key not in SORT_KEYS:
            return
        if key == self._sort:
            self._ascending = not self._ascending
        else:
            self._sort, self._ascending = key, True
        self.listingChanged.emit()

    @Slot(str)
    def setFind(self, query):
        self._find = query.strip()
        self.listingChanged.emit()

    # --- operations ----------------------------------------------------------------------------

    def _needs_password(self, then, reason):
        if self.locked and not self._password:
            self._pending = then
            self.passwordNeeded.emit(reason)
            return True
        return False

    def _run(self, kind, title, command, cwd=None, after=None, entries=0):
        job = Job(kind, title, command, cwd, self, entries)

        def finished():
            if job.errorKind == "password":
                self._password = ""
                self._pending = lambda: self._run(kind, title, command_with_password(command), cwd, after)
                self.passwordNeeded.emit("wrong")
            elif job.ok:
                if after:
                    after()
            elif job.errorKind != "cancelled":
                self.notice.emit(self.t["failed"], job.error)
            self.jobChanged.emit()

        def command_with_password(old):
            return [("-p" + self._password) if part.startswith("-p") and not part.startswith("-ps") else part
                    for part in old]

        job.done.connect(finished)
        self._job = job
        self.jobChanged.emit()
        job.start()
        return job

    @Slot(result=str)
    def archiveFolder(self):
        return str(self.path.parent) if self.path else ""

    @Slot(result=str)
    def defaultDestination(self):
        if not self.path:
            return str(Path.home())
        return str(self.path.parent / archive.archive_stem(self.path))

    @Slot(str, "QVariantList", str)
    def extract(self, destination, paths, overwrite="rename"):
        """Extract the selected items (all when none) to `destination`."""
        if not self.path:
            return
        if self._needs_password(lambda: self.extract(destination, paths, overwrite), "extract"):
            return
        destination = str(Path(destination).expanduser())
        Path(destination).mkdir(parents=True, exist_ok=True)
        members = self.tree.expand(paths) if paths else []
        if self.tar:
            # bsdtar extracts a folder with everything in it: name the selection only.
            command = archive.tar_extract_command(self.path, destination, paths, overwrite)
            count = len(members) if members else len(self.tree.entries)
        else:
            command = archive.extract_command(self.path, destination, members, self._password, overwrite)
            count = 0
        self._run("extract", self.t["extracting"].format(name=self.path.name), command,
                  after=lambda: self.extracted.emit(destination), entries=count)

    @Slot()
    def test(self):
        if not self.path or self._needs_password(self.test, "test"):
            return
        name = self.path.name
        command = archive.tar_test_command(self.path) if self.tar else archive.test_command(self.path, self._password)
        self._run("test", self.t["testing"].format(name=name), command,
                  after=lambda: self.notice.emit(self.t["test"], self.t["test_ok"].format(name=name)))

    @Slot("QVariantList")
    def deleteItems(self, paths):
        if not self.path or not paths or not self.canDelete:
            return
        members = self.tree.expand(paths)
        self._run("delete", self.t["deleting"].format(name=self.path.name),
                  archive.delete_command(self.path, members), after=self._list)

    @Slot(str)
    def viewItem(self, path):
        if not self.path or self.tree.is_folder(path):
            return
        if self._needs_password(lambda: self.viewItem(path), "view"):
            return
        if self._temp is None:
            base = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir())
            self._temp = Path(tempfile.mkdtemp(prefix="veltos-archive-", dir=base))
        if self.tar:
            target = self._temp / path
            command = archive.tar_extract_command(self.path, self._temp, [path], "overwrite")
        else:
            target = self._temp / PurePosixPath(path).name
            command = archive.extract_flat_command(self.path, self._temp, path, self._password)
        self._run("view", self.t["extracting"].format(name=self.path.name), command,
                  after=lambda: self._open(QUrl.fromLocalFile(str(target))))

    @Slot("QVariantList")
    def addFiles(self, urls):
        """Files dropped on (or added to) the open ZIP/7Z/TAR archive."""
        paths = [Path(QUrl(u).toLocalFile() if str(u).startswith("file:") else str(u)) for u in urls]
        paths = [p for p in paths if p.exists()]
        if not paths or not self.path or not archive.can_add_to(self.info):
            return
        parent = archive.common_parent(paths)
        names = [str(p.resolve().relative_to(parent)) for p in paths]
        command = archive.append_command(self.path, names, self.info, self._password)
        self._run("add", self.t["adding"].format(name=self.path.name), command, cwd=parent, after=self._list)

    @Slot("QVariantList", str, str, str, str, bool)
    def createArchive(self, sources, target, fmt, level, password, encrypt_names):
        paths = [Path(QUrl(s).toLocalFile() if str(s).startswith("file:") else str(s)) for s in sources]
        paths = [p for p in paths if p.exists()]
        if not paths:
            return
        parent = archive.common_parent(paths)
        target = Path(target).expanduser()
        if not target.is_absolute():
            target = parent / target
        if fmt not in archive.CREATE_FORMATS:
            fmt = archive.create_format(target) or "zip"
        names = [str(p.resolve().relative_to(parent)) for p in paths]
        command = archive.add_command(target, names, fmt, level, password, encrypt_names)
        self._run("add", self.t["adding"].format(name=target.name), command, cwd=parent,
                  after=lambda: self.extracted.emit(str(target.parent)))

    @Slot("QVariantList", result=str)
    def defaultArchiveName(self, sources):
        paths = [Path(QUrl(s).toLocalFile() if str(s).startswith("file:") else str(s)) for s in sources]
        return archive.default_archive_name(paths) if paths else "Archive.zip"

    @Slot(str, str, result=str)
    def withFormat(self, name, fmt):
        """"photos.zip" + "7z" -> "photos.7z"."""
        if fmt not in archive.CREATE_FORMATS:
            return name
        stem = archive.archive_stem(name) if archive.is_archive_name(name) else name
        return stem + archive.CREATE_FORMATS[fmt][1]

    @Slot(str)
    def showFolder(self, folder):
        self._open(QUrl.fromLocalFile(folder))

    @Slot()
    def cancelJob(self):
        if self._job:
            self._job.cancel()

    def cleanup(self):
        if self._temp:
            shutil.rmtree(self._temp, ignore_errors=True)


# --- command-line modes (File Explorer) -------------------------------------------------------------

def run_window(backend, qml, properties=None):
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    for key, value in (properties or {}).items():
        engine.rootContext().setContextProperty(key, value)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / qml)))
    return engine


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-archive")
    app.setDesktopFileName("veltos-archive")
    app.setWindowIcon(QIcon.fromTheme("veltos-archive"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    args = argv[1:]
    mode = args[0] if args and args[0].startswith("--") else ""
    files = [a for a in args if not a.startswith("--")]
    task = {"mode": mode, "files": files}
    if mode in ("--extract-here", "--extract-to-folder", "--add", "--add-to"):
        engine = run_window(backend, "Task.qml", {"task": task})
    else:
        engine = run_window(backend, "Main.qml")
        if files:
            backend.openArchive(files[0])
    if not engine.rootObjects():
        return 1
    code = app.exec()
    backend.cleanup()
    del engine
    return code
