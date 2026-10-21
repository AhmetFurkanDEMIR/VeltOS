"""VeltOS PDF Reader: PDF documents in a modern reader layout (tabs with
Home and the open documents, a quick tool rail on the right, thumbnails
and bookmarks on the left, a floating page and zoom bar).

The pages are drawn by Qt PDF (PDFium) in QML (QtQuick.Pdf). This module
keeps the tabs and the recent files, checks passwords, prints (Qt's print
dialog, pages rendered with QPdfDocument), reads document facts and makes a
second start open its files as tabs of the running reader.
"""

import configparser
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import (QFileSystemWatcher, QLocale, QObject, QSettings, QSize, Qt, QUrl, Property, Signal,
                            Slot)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow

from . import strings

VERSION = "0.1"
QML_DIR = Path(__file__).resolve().parent / "qml"
THEMES = ("light", "dark", "system")
MAX_RECENT = 20


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


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


def server_name():
    return f"veltos-pdf-{os.getuid()}"


def open_document(path, password=""):
    """(QPdfDocument, status): "ok", "password" or "error"."""
    from PySide6.QtPdf import QPdfDocument
    document = QPdfDocument()
    if password:
        document.setPassword(password)
    error = document.load(str(path))
    if error == QPdfDocument.Error.None_:
        return document, "ok"
    if error == QPdfDocument.Error.IncorrectPassword:
        return document, "password"
    return document, "error"


class IconProvider(QQuickImageProvider):
    """image://icon/<name>: an icon of the desktop's icon theme."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    def requestPixmap(self, name, size, requested_size):
        side = max(requested_size.width(), requested_size.height(), 16) if requested_size.isValid() else 64
        pixmap = QIcon.fromTheme(name).pixmap(side, side)
        if pixmap.isNull():               # no such icon (tests, other desktops)
            pixmap = QPixmap(side, side)
            pixmap.fill(Qt.transparent)
        if size is not None:
            size.setWidth(pixmap.width())
            size.setHeight(pixmap.height())
        return pixmap


class Backend(QObject):
    themeChanged = Signal()
    tabsChanged = Signal()
    recentChanged = Signal()
    message = Signal(str)
    passwordNeeded = Signal(str, bool)     # path, wrong (a password was tried)

    def __init__(self, lang=None, settings=None, parent=None):
        super().__init__(parent)
        self._lang = lang or strings.language()
        self._texts = strings.texts(self._lang)
        self._settings = settings if settings is not None else QSettings(
            str(config_home() / "veltos/pdf.conf"), QSettings.Format.IniFormat)
        self._tabs = []          # {path, title, password}
        self._current = 0        # 0 = Home, n = tab n-1
        self._system_dark = system_dark()
        self._accent = system_accent()
        self._watcher = QFileSystemWatcher(self)
        for path in (config_home(), config_home() / "kdeglobals"):
            if path.exists():
                self._watcher.addPath(str(path))
        self._watcher.directoryChanged.connect(self._reread_theme)
        self._watcher.fileChanged.connect(self._reread_theme)

    def _reread_theme(self, *_args):
        dark, accent = system_dark(), system_accent()
        if (dark, accent) != (self._system_dark, self._accent):
            self._system_dark, self._accent = dark, accent
            self.themeChanged.emit()

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
            self._settings.setValue("theme", theme)
            self._settings.sync()
            self.themeChanged.emit()

    @Property(bool, notify=themeChanged)
    def darkMode(self):
        return self._system_dark if self.theme == "system" else self.theme == "dark"

    @Property(str, notify=themeChanged)
    def accent(self):
        return self._accent

    # --- tabs -----------------------------------------------------------------------------

    @Property("QVariantList", notify=tabsChanged)
    def tabs(self):
        return [{"path": t["path"], "title": t["title"], "password": t["password"],
                 "url": QUrl.fromLocalFile(t["path"]).toString()} for t in self._tabs]

    @Property(int, notify=tabsChanged)
    def currentIndex(self):
        """0 = Home, 1.. = the documents."""
        return self._current

    @Slot(int)
    def setCurrentIndex(self, index):
        if 0 <= index <= len(self._tabs) and index != self._current:
            self._current = index
            self.tabsChanged.emit()

    @Slot("QStringList")
    def openPaths(self, paths):
        for raw in paths:
            path = Path(QUrl(raw).toLocalFile() if raw.startswith("file:") else raw).expanduser()
            try:
                path = path.resolve()
            except OSError:
                pass
            self.openPath(str(path), "")

    @Slot(str, str)
    def openPath(self, path, password):
        existing = next((i for i, t in enumerate(self._tabs) if t["path"] == path), -1)
        if existing >= 0:
            self.setCurrentIndex(existing + 1)
            return
        try:
            _document, status = open_document(path, password)
        except ImportError:
            status = "ok"            # QML reports problems itself
        if status == "password":
            self.passwordNeeded.emit(path, bool(password))
            return
        if status == "error":
            self.message.emit(self._texts["cant_open"].format(name=Path(path).name))
            return
        self._tabs.append({"path": path, "title": Path(path).name, "password": password})
        self._current = len(self._tabs)
        self._remember(path)
        self.tabsChanged.emit()

    @Slot(int)
    def closeTab(self, index):
        """Close document tab `index` (1..)."""
        if 1 <= index <= len(self._tabs):
            self._tabs.pop(index - 1)
            if self._current >= index:
                self._current = max(0, self._current - 1)
            self.tabsChanged.emit()

    # --- recent files ----------------------------------------------------------------------

    def _recent_raw(self):
        try:
            data = json.loads(str(self._settings.value("recent", "[]")))
            return [r for r in data if isinstance(r, dict) and "path" in r]
        except ValueError:
            return []

    def _remember(self, path):
        entries = [{"path": path, "opened": int(datetime.datetime.now().timestamp())}]
        entries += [r for r in self._recent_raw() if r["path"] != path]
        self._settings.setValue("recent", json.dumps(entries[:MAX_RECENT]))
        self._settings.sync()
        self.recentChanged.emit()

    @Property("QVariantList", notify=recentChanged)
    def recent(self):
        locale = QLocale()
        result = []
        for entry in self._recent_raw():
            path = Path(entry["path"])
            try:
                size = path.stat().st_size
            except OSError:
                continue
            opened = datetime.datetime.fromtimestamp(entry.get("opened", 0))
            result.append({"path": str(path), "name": path.name, "folder": str(path.parent),
                           "size": human_size(size),
                           "opened": locale.toString(opened.date(), QLocale.FormatType.ShortFormat)
                           + " " + opened.strftime("%H:%M")})
        return result

    @Slot(str)
    def forget(self, path):
        entries = [r for r in self._recent_raw() if r["path"] != path]
        self._settings.setValue("recent", json.dumps(entries))
        self._settings.sync()
        self.recentChanged.emit()

    # --- document facts, printing, folder -------------------------------------------------------

    @Slot(str, result="QVariantMap")
    def fileFacts(self, path):
        try:
            st = os.stat(path)
        except OSError:
            return {}
        return {"name": Path(path).name, "folder": str(Path(path).parent), "size": human_size(st.st_size)}

    @Slot(float, float, result=str)
    def pageSizeText(self, width_pt, height_pt):
        """"210 x 297 mm (A4)" from PDF points."""
        w, h = width_pt * 25.4 / 72, height_pt * 25.4 / 72
        names = {(210, 297): "A4", (148, 210): "A5", (297, 420): "A3", (216, 279): "Letter", (216, 356): "Legal"}
        key = (round(min(w, h)), round(max(w, h)))
        name = next((n for (a, b), n in names.items() if abs(a - key[0]) <= 2 and abs(b - key[1]) <= 2), "")
        return f"{w:.0f} x {h:.0f} mm" + (f" ({name})" if name else "")

    @Slot(str, str)
    def printDocument(self, path, password):
        try:
            from PySide6.QtGui import QPainter
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        except ImportError:
            return
        document, status = open_document(path, password)
        if status != "ok":
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setDocName(Path(path).name)
        dialog = QPrintDialog(printer)
        dialog.setMinMax(1, document.pageCount())
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return
        first, last = printer.fromPage(), printer.toPage()
        if first == 0:
            first, last = 1, document.pageCount()
        painter = QPainter()
        if not painter.begin(printer):
            return
        try:
            for page in range(first - 1, last):
                if page > first - 1:
                    printer.newPage()
                rect = painter.viewport()
                size = document.pagePointSize(page)
                scale = min(rect.width() / max(1, size.width()), rect.height() / max(1, size.height()))
                target = QSize(int(size.width() * scale), int(size.height() * scale))
                image = document.render(page, target)
                painter.drawImage((rect.width() - target.width()) // 2, (rect.height() - target.height()) // 2,
                                  image)
        finally:
            painter.end()

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


def hand_over(paths):
    socket = QLocalSocket()
    socket.connectToServer(server_name())
    if not socket.waitForConnected(500):
        return False
    socket.write(json.dumps([str(Path(p).expanduser().absolute()) for p in paths]).encode())
    socket.flush()
    socket.waitForBytesWritten(1000)
    socket.disconnectFromServer()
    return True


def listen(backend, window):
    QLocalServer.removeServer(server_name())
    server = QLocalServer(backend)
    if not server.listen(server_name()):
        return None

    def connection():
        socket = server.nextPendingConnection()

        def read():
            try:
                paths = json.loads(bytes(socket.readAll()).decode() or "[]")
            except ValueError:
                return
            backend.openPaths(paths)
            window.show()
            window.raise_()
            window.requestActivate()
        socket.readyRead.connect(read)
    server.newConnection.connect(connection)
    return server


def main(argv=None):
    argv = sys.argv if argv is None else argv
    files = [a for a in argv[1:] if not a.startswith("-")]
    from PySide6.QtWidgets import QApplication
    app = QApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-pdf")
    app.setDesktopFileName("veltos-pdf")
    app.setWindowIcon(QIcon.fromTheme("veltos-pdf"))
    if hand_over(files):
        return 0
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    qml = QQmlApplicationEngine()
    qml.addImageProvider("icon", IconProvider())
    qml.rootContext().setContextProperty("backend", backend)
    qml.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not qml.rootObjects():
        return 1
    window = qml.rootObjects()[0]
    from .frame import follow_frame
    follow_frame(window)
    if files:
        backend.openPaths(files)
    server = listen(backend, window)
    code = app.exec()
    del server
    sys.stdout.flush()
    os._exit(code)
