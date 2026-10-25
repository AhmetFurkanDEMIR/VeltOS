"""VeltOS Notepad: Windows 11's Notepad on VeltOS.

The window (qml/Main.qml) has the tabs in the title bar, the File / Edit /
View menus with Settings on the right, the text, the find and replace
panel and the status bar (line and column, characters, zoom, line ending,
encoding). This module keeps the tabs (TabsModel), reads and writes the
files (textfile.py), finds and replaces in the editors' documents, keeps
the session (unsaved tabs come back, as in Windows 11), the settings and
the recent files, prints, and makes a second start hand its files to the
running Notepad.
"""

import configparser
import json
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import (QAbstractListModel, QByteArray, QDateTime, QFileSystemWatcher, QLocale,
                            QModelIndex, QObject, QSettings, Qt, QTimer, QUrl, Property, Signal, Slot)
from PySide6.QtGui import QFontDatabase, QIcon, QTextCursor, QTextDocument
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import strings, textfile

VERSION = "0.1"
QML_DIR = Path(__file__).resolve().parent / "qml"
THEMES = ("light", "dark", "system")
FONT_STYLES = ("regular", "italic", "bold", "bold_italic")
ZOOM_STEPS = (10, 25, 50, 67, 75, 80, 90, 100, 110, 125, 150, 175, 200, 250, 300, 400, 500)
MAX_RECENT = 10


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def kde_value(group, key):
    """A kdeglobals value as the session sees it (user, kdedefaults, /etc/xdg)."""
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


def server_name():
    return f"veltos-notepad-{os.getuid()}"


def looks_binary(text):
    """Many control characters: probably not a text file."""
    sample = text[:4096]
    controls = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\t\f\v\x1b")
    return bool(sample) and controls > len(sample) * 0.05


class TabsModel(QAbstractListModel):
    """The open tabs. The texts live in the editors (QTextDocument); a tab
    keeps its file, encoding, line ending and the text to load at first."""

    ROLES = ("tabId", "title", "path", "modified", "encoding", "eol", "initialText", "cursor")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs = []

    def roleNames(self):
        return {Qt.UserRole + i: QByteArray(name.encode()) for i, name in enumerate(self.ROLES)}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.tabs)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.tabs):
            return None
        name = self.ROLES[role - Qt.UserRole] if role >= Qt.UserRole else "title"
        return self.tabs[index.row()].get(name)

    def add(self, tab, row=None):
        row = len(self.tabs) if row is None else row
        self.beginInsertRows(QModelIndex(), row, row)
        self.tabs.insert(row, tab)
        self.endInsertRows()
        return row

    def remove(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        tab = self.tabs.pop(row)
        self.endRemoveRows()
        return tab

    def update(self, row, **values):
        self.tabs[row].update(values)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)

    def row_of(self, tab_id):
        for row, tab in enumerate(self.tabs):
            if tab["tabId"] == tab_id:
                return row
        return -1


class Backend(QObject):
    tabsChanged = Signal()
    currentChanged = Signal()
    settingsChanged = Signal()
    themeChanged = Signal()
    recentChanged = Signal()
    # Asks the window: a message, save as for a tab, select a range.
    message = Signal(str)
    saveAsRequested = Signal(int)
    selectRange = Signal(int, int, int)       # tab id, start, end

    def __init__(self, lang=None, settings=None, session_file=None, restore=True, parent=None):
        # restore=False: a window opened with "New window"; it neither
        # restores nor keeps the session (the first window does).
        super().__init__(parent)
        self._lang = lang or strings.language()
        self._texts = strings.texts(self._lang)
        self._settings = settings if settings is not None else QSettings(
            str(config_home() / "veltos/notepad.conf"), QSettings.Format.IniFormat)
        self._session_file = Path(session_file) if session_file else data_home() / "veltos/notepad/session.json"
        self.model = TabsModel(self)
        self._docs = {}            # tab id -> QTextDocument
        self._quick = {}           # tab id -> QQuickTextDocument (see attach)
        self._next_id = 1
        self._current = -1
        self._zoom = 100
        self._system_dark = system_dark()
        self._accent = system_accent()
        self._watcher = QFileSystemWatcher(self)
        for path in (config_home(), config_home() / "kdeglobals"):
            if path.exists():
                self._watcher.addPath(str(path))
        self._watcher.directoryChanged.connect(self._reread_theme)
        self._watcher.fileChanged.connect(self._reread_theme)
        # Windows 11 Notepad keeps unsaved work without asking.
        self._autosave = QTimer(self)
        self._autosave.setInterval(15000)
        self._autosave.timeout.connect(self.saveSession)
        self._keeps_session = restore
        if restore and self.continueSession:
            self._restore_session()
        if not self.model.tabs:
            self.newTab()
        if restore:
            self._autosave.start()

    # --- theme ----------------------------------------------------------------------------------

    def _reread_theme(self, *_args):
        dark, accent = system_dark(), system_accent()
        kdeglobals = str(config_home() / "kdeglobals")
        if kdeglobals not in self._watcher.files() and Path(kdeglobals).exists():
            self._watcher.addPath(kdeglobals)
        if (dark, accent) != (self._system_dark, self._accent):
            self._system_dark, self._accent = dark, accent
            self.themeChanged.emit()

    @Property(float, notify=themeChanged)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, notify=themeChanged)
    def darkMode(self):
        theme = self.theme
        return self._system_dark if theme == "system" else theme == "dark"

    @Property(str, notify=themeChanged)
    def accent(self):
        return self._accent

    # --- settings -------------------------------------------------------------------------------

    def _value(self, key, default):
        value = self._settings.value(key, default)
        if isinstance(default, bool):
            return value in (True, "true", "1", 1)
        if isinstance(default, int):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        return str(value)

    def _save(self, key, value):
        self._settings.setValue(key, value)
        self._settings.sync()
        self.settingsChanged.emit()

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(str, constant=True)
    def version(self):
        return VERSION

    @Property(str, notify=settingsChanged)
    def theme(self):
        theme = self._value("theme", "system")
        return theme if theme in THEMES else "system"

    @Slot(str)
    def setTheme(self, theme):
        if theme in THEMES:
            self._save("theme", theme)
            self.themeChanged.emit()

    @Property(str, notify=settingsChanged)
    def fontFamily(self):
        return self._value("fontFamily", "Cascadia Mono")

    @Property(int, notify=settingsChanged)
    def fontSize(self):
        return max(6, min(72, self._value("fontSize", 11)))

    @Property(str, notify=settingsChanged)
    def fontStyle(self):
        style = self._value("fontStyle", "regular")
        return style if style in FONT_STYLES else "regular"

    @Slot(str, int, str)
    def setFont(self, family, size, style):
        self._settings.setValue("fontFamily", family)
        self._settings.setValue("fontSize", max(6, min(72, size)))
        self._save("fontStyle", style if style in FONT_STYLES else "regular")

    @Property("QStringList", constant=True)
    def fontFamilies(self):
        return sorted(set(QFontDatabase.families()), key=str.lower)

    @Property(bool, notify=settingsChanged)
    def wordWrap(self):
        return self._value("wordWrap", True)

    @Slot(bool)
    def setWordWrap(self, on):
        self._save("wordWrap", on)

    @Property(bool, notify=settingsChanged)
    def statusBar(self):
        return self._value("statusBar", True)

    @Slot(bool)
    def setStatusBar(self, on):
        self._save("statusBar", on)

    @Property(bool, notify=settingsChanged)
    def continueSession(self):
        return self._value("continueSession", True)

    @Slot(bool)
    def setContinueSession(self, on):
        self._save("continueSession", on)

    @Property(bool, notify=settingsChanged)
    def openInNewWindow(self):
        return self._value("openInNewWindow", False)

    @Slot(bool)
    def setOpenInNewWindow(self, on):
        self._save("openInNewWindow", on)

    # Zoom: the window's text size, as Windows (not saved).
    @Property(int, notify=settingsChanged)
    def zoom(self):
        return self._zoom

    @Slot(int)
    def stepZoom(self, direction):
        if direction == 0:
            self._zoom = 100
        elif direction > 0:
            self._zoom = next((z for z in ZOOM_STEPS if z > self._zoom), ZOOM_STEPS[-1])
        else:
            self._zoom = next((z for z in reversed(ZOOM_STEPS) if z < self._zoom), ZOOM_STEPS[0])
        self.settingsChanged.emit()

    # --- recent files ---------------------------------------------------------------------------

    @Property("QStringList", notify=recentChanged)
    def recentFiles(self):
        value = self._settings.value("recent", [])
        files = [value] if isinstance(value, str) else list(value or [])
        return [f for f in files if f and Path(f).exists()][:MAX_RECENT]

    def _remember(self, path):
        files = [str(path)] + [f for f in self.recentFiles if f != str(path)]
        self._settings.setValue("recent", files[:MAX_RECENT])
        self._settings.sync()
        self.recentChanged.emit()

    # --- tabs -----------------------------------------------------------------------------------

    @Property(QObject, constant=True)
    def tabs(self):
        return self.model

    @Property(int, notify=tabsChanged)
    def tabCount(self):
        return len(self.model.tabs)

    @Property(int, notify=currentChanged)
    def currentIndex(self):
        return self._current

    @Property("QVariantMap", notify=currentChanged)
    def current(self):
        return dict(self.model.tabs[self._current]) if 0 <= self._current < len(self.model.tabs) else {}

    @Slot(int)
    def setCurrentIndex(self, row):
        if 0 <= row < len(self.model.tabs) and row != self._current:
            self._current = row
            self.currentChanged.emit()

    def _new_tab(self, path="", text="", encoding="UTF-8", eol="LF", modified=False, cursor=0, row=None):
        tab = {"tabId": self._next_id, "title": Path(path).name if path else self._texts["untitled"],
               "path": str(path), "modified": modified, "encoding": encoding, "eol": eol,
               "initialText": text, "cursor": cursor}
        self._next_id += 1
        return self.model.add(tab, row)

    @Slot()
    def newTab(self):
        row = self._new_tab(row=self._current + 1 if self._current >= 0 else None)
        self._current = row
        self.currentChanged.emit()
        self.tabsChanged.emit()

    def _blank(self, row):
        tab = self.model.tabs[row]
        doc = self._docs.get(tab["tabId"])
        text = doc.toPlainText() if doc is not None else tab["initialText"]
        return not tab["path"] and not tab["modified"] and text == ""

    @Slot("QStringList")
    def openPaths(self, paths):
        """Open files in tabs (one already open is shown); a blank Untitled
        tab is replaced, as in Windows."""
        for raw in paths:
            path = Path(QUrl(raw).toLocalFile() if raw.startswith("file:") else raw).expanduser()
            try:
                path = path.resolve()
            except OSError:
                pass
            existing = next((row for row, t in enumerate(self.model.tabs) if t["path"] == str(path)), -1)
            if existing >= 0:
                self._current = existing
                continue
            try:
                text, encoding, eol = textfile.load(path, self._lang)
            except (OSError, ValueError):
                self.message.emit(self._texts["cant_open"].format(name=path.name))
                continue
            if looks_binary(text):
                self.message.emit(self._texts["binary_file"].format(name=path.name))
            replace = self._current if 0 <= self._current < len(self.model.tabs) and self._blank(self._current) else -1
            if replace >= 0:
                old = self.model.remove(replace)
                self._docs.pop(old["tabId"], None)
                self._quick.pop(old["tabId"], None)
                row = self._new_tab(path, text, encoding, eol, row=replace)
            else:
                row = self._new_tab(path, text, encoding, eol)
            self._current = row
            self._remember(path)
        self.currentChanged.emit()
        self.tabsChanged.emit()

    @Slot(int, result=bool)
    def needsSaving(self, row):
        return 0 <= row < len(self.model.tabs) and self.model.tabs[row]["modified"]

    @Slot(int)
    def closeTab(self, row):
        """Close without asking (the window asks about unsaved changes)."""
        if not 0 <= row < len(self.model.tabs):
            return
        tab = self.model.remove(row)
        self._docs.pop(tab["tabId"], None)
        self._quick.pop(tab["tabId"], None)
        if not self.model.tabs:
            self._new_tab()
        self._current = min(max(0, self._current - (1 if row < self._current else 0)), len(self.model.tabs) - 1)
        self.currentChanged.emit()
        self.tabsChanged.emit()

    @Slot(int, int)
    def moveTab(self, row, to):
        if row == to or not 0 <= row < len(self.model.tabs) or not 0 <= to < len(self.model.tabs):
            return
        tab = self.model.remove(row)
        self.model.add(tab, to)
        self._current = to
        self.currentChanged.emit()

    # --- documents --------------------------------------------------------------------------

    @Slot(int, QObject)
    def attach(self, tab_id, quick_document):
        """An editor tells which document holds a tab's text. PySide6 ties
        the QTextDocument wrapper to the QQuickTextDocument one: both are
        kept, or the document is unusable from Python once QML's object is
        collected (offscreen test, 2026-10-21)."""
        doc = quick_document.textDocument() if hasattr(quick_document, "textDocument") else quick_document
        if not isinstance(doc, QTextDocument):
            return
        self._docs[tab_id] = doc
        self._quick[tab_id] = quick_document
        row = self.model.row_of(tab_id)
        if row >= 0:
            modified = self.model.tabs[row]["modified"]
            doc.setModified(modified)
            self.model.tabs[row]["initialText"] = ""
        doc.modificationChanged.connect(lambda changed, tab_id=tab_id: self._modified(tab_id, changed))

    def _modified(self, tab_id, changed):
        row = self.model.row_of(tab_id)
        if row >= 0 and self.model.tabs[row]["modified"] != changed:
            self.model.update(row, modified=changed)
            if row == self._current:
                self.currentChanged.emit()

    def _text(self, row):
        tab = self.model.tabs[row]
        doc = self._docs.get(tab["tabId"])
        return doc.toPlainText() if doc is not None else tab["initialText"]

    @Slot(int, result=bool)
    def save(self, row):
        if not 0 <= row < len(self.model.tabs):
            return False
        tab = self.model.tabs[row]
        if not tab["path"]:
            self.saveAsRequested.emit(row)
            return False
        return self._write(row, Path(tab["path"]))

    @Slot(int, str, result=bool)
    def saveAs(self, row, url):
        if not 0 <= row < len(self.model.tabs) or not url:
            return False
        path = Path(QUrl(url).toLocalFile() if url.startswith("file:") else url)
        if not path.suffix and not path.exists():
            path = path.with_suffix(".txt")      # Notepad adds .txt
        return self._write(row, path)

    def _write(self, row, path):
        tab = self.model.tabs[row]
        try:
            textfile.save(path, self._text(row), tab["encoding"], tab["eol"], self._lang)
        except OSError:
            self.message.emit(self._texts["cant_save"].format(name=path.name))
            return False
        self.model.update(row, path=str(path), title=path.name, modified=False)
        doc = self._docs.get(tab["tabId"])
        if doc is not None:
            doc.setModified(False)
        self._remember(path)
        if row == self._current:
            self.currentChanged.emit()
        return True

    @Slot()
    def saveAll(self):
        for row in range(len(self.model.tabs)):
            if self.model.tabs[row]["modified"]:
                self.save(row)

    @Slot(int, str)
    def setEol(self, row, eol):
        if 0 <= row < len(self.model.tabs) and eol in textfile.EOLS:
            self.model.update(row, eol=eol, modified=True)
            self.currentChanged.emit()

    @Slot(int, str)
    def setEncoding(self, row, encoding):
        if 0 <= row < len(self.model.tabs) and encoding in textfile.ENCODINGS:
            self.model.update(row, encoding=encoding, modified=True)
            self.currentChanged.emit()

    @Property("QStringList", constant=True)
    def encodings(self):
        return list(textfile.ENCODINGS)

    # --- positions, find and replace ------------------------------------------------------------

    @Slot(int, int, result="QVariantList")
    def lineColumn(self, tab_id, position):
        doc = self._docs.get(tab_id)
        if doc is None:
            return [1, 1]
        block = doc.findBlock(max(0, position))
        if not block.isValid():
            block = doc.lastBlock()
        return [block.blockNumber() + 1, position - block.position() + 1]

    @Slot(int, int, result=int)
    def positionOfLine(self, tab_id, line):
        doc = self._docs.get(tab_id)
        if doc is None:
            return 0
        block = doc.findBlockByNumber(max(0, min(line, doc.blockCount()) - 1))
        return block.position()

    @Slot(int, result=int)
    def lineCount(self, tab_id):
        doc = self._docs.get(tab_id)
        return doc.blockCount() if doc is not None else 1

    def _flags(self, match_case, forward=True):
        flags = QTextDocument.FindFlag(0)
        if match_case:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward
        return flags

    @Slot(int, str, int, bool, bool, bool, result="QVariantList")
    def find(self, tab_id, query, position, forward, match_case, wrap):
        """[start, end] of the next match from a position, [] if none."""
        doc = self._docs.get(tab_id)
        if doc is None or not query:
            return []
        flags = self._flags(match_case, forward)
        found = doc.find(query, position, flags)
        if found.isNull() and wrap:
            found = doc.find(query, 0 if forward else doc.characterCount() - 1, flags)
        if found.isNull():
            return []
        return [found.selectionStart(), found.selectionEnd()]

    @Slot(int, str, str, bool, result=int)
    def replaceAll(self, tab_id, query, replacement, match_case):
        """Replace every match as one step that Undo takes back at once."""
        doc = self._docs.get(tab_id)
        if doc is None or not query:
            return 0
        flags = self._flags(match_case)
        count = 0
        editor = QTextCursor(doc)
        editor.beginEditBlock()
        found = doc.find(query, 0, flags)
        while not found.isNull():
            found.insertText(replacement)
            count += 1
            found = doc.find(query, found.position(), flags)
        editor.endEditBlock()
        return count

    @Slot(result=str)
    def timeDate(self):
        """Windows' F5: the short time and date of the user's region."""
        locale = QLocale()
        now = QDateTime.currentDateTime()
        return f"{locale.toString(now.time(), QLocale.FormatType.ShortFormat)} " \
               f"{locale.toString(now.date(), QLocale.FormatType.ShortFormat)}"

    # --- printing -------------------------------------------------------------------------------

    @Slot(int)
    def printTab(self, row):
        if not 0 <= row < len(self.model.tabs):
            return
        try:
            from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        except ImportError:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setDocName(self.model.tabs[row]["title"])
        dialog = QPrintDialog(printer)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return
        doc = QTextDocument()
        doc.setPlainText(self._text(row))
        font = doc.defaultFont()
        font.setFamily(self.fontFamily)
        font.setPointSize(self.fontSize)
        doc.setDefaultFont(font)
        doc.print_(printer)

    # --- session ----------------------------------------------------------------------------

    @Slot()
    def saveSession(self):
        """Remember every tab; unsaved texts are kept in the session file."""
        if not self.continueSession or not self._keeps_session:
            return
        tabs = []
        for row, tab in enumerate(self.model.tabs):
            entry = {"path": tab["path"], "encoding": tab["encoding"], "eol": tab["eol"],
                     "modified": tab["modified"]}
            if tab["modified"] or not tab["path"]:
                entry["text"] = self._text(row)
            tabs.append(entry)
        data = {"version": 1, "current": self._current, "tabs": tabs}
        try:
            self._session_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._session_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.chmod(tmp, 0o600)
            tmp.replace(self._session_file)
        except OSError:
            pass

    def _restore_session(self):
        try:
            data = json.loads(self._session_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for entry in data.get("tabs", []) if isinstance(data, dict) else []:
            path = entry.get("path", "")
            text = entry.get("text")
            encoding = entry.get("encoding", "UTF-8")
            eol = entry.get("eol", "LF")
            if text is None:
                try:
                    text, encoding, eol = textfile.load(path, self._lang)
                except (OSError, ValueError):
                    continue
            elif not path and text == "":
                continue    # an empty Untitled tab is not worth keeping
            self._new_tab(path, text, encoding if encoding in textfile.ENCODINGS else "UTF-8",
                          eol if eol in textfile.EOLS else "LF", bool(entry.get("modified")) or not path)
        if self.model.tabs:
            self._current = max(0, min(int(data.get("current", 0)), len(self.model.tabs) - 1))

    @Property(bool, constant=True)
    def keepsSession(self):
        return self._keeps_session

    @Slot()
    def discardSession(self):
        self._session_file.unlink(missing_ok=True)

    @Slot(result=bool)
    def anyModified(self):
        return any(t["modified"] for t in self.model.tabs)

    # --- other windows ----------------------------------------------------------------------

    @Slot()
    def newWindow(self):
        import subprocess
        subprocess.Popen([sys.executable, "-m", "veltos_notepad", "--new-window"], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def bring_forward(window, token=""):
    """Show the window in front. KWin (Wayland) does that only with an
    activation token from the program that asked (the portal or Plasma
    gives one to the start that is handing over); Qt uses
    XDG_ACTIVATION_TOKEN for the next requestActivate()."""
    if token:
        os.environ["XDG_ACTIVATION_TOKEN"] = token
    window.show()
    window.raise_()
    window.requestActivate()


def handed_over(data):
    """(paths, token) of a hand-over message (older starts sent a list)."""
    if isinstance(data, dict):
        return [str(p) for p in data.get("paths", [])], str(data.get("token", ""))
    return [str(p) for p in data], ""


def hand_over(paths):
    """Give files to a Notepad that is already running; False if none is."""
    socket = QLocalSocket()
    socket.connectToServer(server_name())
    if not socket.waitForConnected(500):
        return False
    socket.write(json.dumps({"paths": [str(Path(p).expanduser().absolute()) for p in paths],
                             "token": os.environ.get("XDG_ACTIVATION_TOKEN", "")}).encode())
    socket.flush()
    socket.waitForBytesWritten(1000)
    socket.disconnectFromServer()
    return True


def listen(backend, window):
    """Accept files from later starts (opened as tabs, window raised)."""
    QLocalServer.removeServer(server_name())
    server = QLocalServer(backend)
    if not server.listen(server_name()):
        return None

    def connection():
        socket = server.nextPendingConnection()

        def read():
            try:
                paths, token = handed_over(json.loads(bytes(socket.readAll()).decode() or "[]"))
            except ValueError:
                return
            if paths:
                backend.openPaths(paths)
            else:
                backend.newTab()
            bring_forward(window, token)
        socket.readyRead.connect(read)
    server.newConnection.connect(connection)
    return server


def main(argv=None):
    argv = sys.argv if argv is None else argv
    new_window = "--new-window" in argv
    files = [a for a in argv[1:] if not a.startswith("--")]
    # QApplication (not QGuiApplication): the file and print dialogs are the
    # desktop's (Plasma's) ones.
    from PySide6.QtWidgets import QApplication
    app = QApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-notepad")
    app.setDesktopFileName("veltos-notepad")
    app.setWindowIcon(QIcon.fromTheme("veltos-notepad"))
    # Settings > Opening files: "Open in a new window" gives files their
    # own window instead of a tab in the running Notepad.
    if files and not new_window:
        settings = QSettings(str(config_home() / "veltos/notepad.conf"), QSettings.Format.IniFormat)
        new_window = settings.value("openInNewWindow", False) in (True, "true", "1", 1)
    if not new_window and hand_over(files):
        return 0
    backend = Backend(restore=not new_window)
    app.setApplicationDisplayName(backend.texts["app_title"])
    if files:
        backend.openPaths(files)
    qml = QQmlApplicationEngine()
    qml.rootContext().setContextProperty("backend", backend)
    qml.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not qml.rootObjects():
        return 1
    window = qml.rootObjects()[0]
    from .frame import follow_frame
    follow_frame(window)
    server = None if new_window else listen(backend, window)
    code = app.exec()
    if not new_window:
        backend.saveSession()
    del server
    sys.stdout.flush()
    os._exit(code)
