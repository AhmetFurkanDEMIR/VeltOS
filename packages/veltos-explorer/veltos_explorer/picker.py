"""VeltOS file dialog: "Open", "Save As" and "Select Folder" in the layout
of Windows 11's dialogs, built from File Explorer's own parts (address
bar, navigation pane, folder views).

    veltos-explorer --pick < request.json

The request is one JSON object on standard input:

    mode            "open" (default), "save" or "folder"
    title           window title (default: Open / Save As / Select Folder)
    multiple        several files may be chosen (open)
    filters         [{"name": "Pictures", "patterns": ["*.png"], "mimes": ["image/jpeg"]}]
    current_filter  index into filters
    current_folder  where to start (default: the last folder used, else Documents)
    current_name    the name offered (save)
    accept_label    text of the accept button (default: Open / Save / Select Folder)

The answer is one JSON object on standard output, {"paths": [...],
"filter": index}; a cancelled dialog answers {"paths": []} with exit code
1. VeltOS Settings calls this directly; every other program's file dialogs
reach it through the file chooser portal (portal.py).
"""

import fnmatch
import json
import os
import shlex
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication

from . import places, strings
from .models import SPECIAL

MODES = ("open", "save", "folder")
# Where the dialog remembers its last folder (per user).
STATE_KEY = "pickerFolder"


def normalise_filters(filters, all_files_text):
    """Filters as the dialog uses them; "All files" when a program sends
    none, so the drop-down is never empty."""
    result = []
    for item in filters or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        patterns = [str(p) for p in item.get("patterns", []) if p]
        mimes = [str(m) for m in item.get("mimes", []) if m]
        if not name:
            name = " ".join(patterns + mimes) or all_files_text
        result.append({"name": name, "patterns": patterns, "mimes": mimes})
    if not result:
        result.append({"name": all_files_text, "patterns": ["*"], "mimes": []})
    return result


def matches(item, filt):
    """Whether a file (an item of a folder listing) passes a filter."""
    if item.get("isDir"):
        return True
    if not filt["patterns"] and not filt["mimes"]:
        return True
    name = item["name"].lower()
    for pattern in filt["patterns"]:
        if fnmatch.fnmatchcase(name, pattern.lower()):
            return True
    mime = item.get("mime", "")
    for wanted in filt["mimes"]:
        if mime == wanted or (wanted.endswith("/*") and mime.startswith(wanted[:-1])):
            return True
    return False


def split_names(text):
    """The names typed into the file name box: one, or several in quotes
    ("a.txt" "b.txt"), as Windows writes a multiple selection."""
    text = text.strip()
    if not text:
        return []
    if text.startswith('"'):
        try:
            return [n for n in shlex.split(text) if n]
        except ValueError:
            return [text.strip('"')]
    return [text]


def default_suffix(filt):
    """".txt" for a filter whose patterns are one extension, else ""."""
    suffixes = set()
    for pattern in filt["patterns"]:
        if pattern.startswith("*.") and "*" not in pattern[2:] and "?" not in pattern[2:]:
            suffixes.add(pattern[1:].lower())
    return next(iter(suffixes)) if len(suffixes) == 1 else ""


def decide(mode, folder, text, selected, multiple, filt=None, exists=os.path.exists, is_dir=os.path.isdir):
    """What the accept button does with the file name box `text` and the
    items selected in the list (`selected`: [{"path", "isDir"}]):

    ("paths", [...])   the dialog is answered with these files
    ("confirm", path)  save: the file exists, ask before replacing
    ("navigate", path) the box names a folder: go there
    ("error", key)     a message (strings.py key)
    """
    names = split_names(text)
    if mode == "folder":
        if not names:
            dirs = [s["path"] for s in selected if s["isDir"]]
            return ("paths", [dirs[0] if len(dirs) == 1 else folder])
        path = names[0] if os.path.isabs(names[0]) else os.path.join(folder, names[0])
        if is_dir(path):
            return ("paths", [os.path.normpath(path)])
        return ("error", "folder_not_found")
    if not names:
        files = [s["path"] for s in selected if not s["isDir"]]
        if mode == "open" and files:
            return ("paths", files if multiple else files[:1])
        return ("error", "file_name_missing")
    paths = [n if os.path.isabs(n) else os.path.join(folder, n) for n in names]
    if len(paths) == 1 and is_dir(paths[0]):
        return ("navigate", os.path.normpath(paths[0]))
    if mode == "open":
        missing = [p for p in paths if not exists(p)]
        if missing:
            return ("error", "file_not_found")
        return ("paths", [os.path.normpath(p) for p in (paths if multiple else paths[:1])])
    path = paths[0]
    if "/" in names[0] and not os.path.isabs(names[0]) and not is_dir(os.path.dirname(path)):
        return ("error", "folder_not_found")
    if not os.path.splitext(path)[1] and filt is not None:
        path += default_suffix(filt)
    path = os.path.normpath(path)
    if is_dir(path):
        return ("navigate", path)
    if exists(path):
        return ("confirm", path)
    return ("paths", [path])


def start_folder(request, prefs=None):
    """The folder the dialog opens in: the one asked for, else the one
    used last time, else Documents (Windows' habit), else the home folder."""
    wanted = request.get("current_folder") or ""
    if wanted and os.path.isdir(os.path.expanduser(wanted)):
        return os.path.expanduser(wanted)
    current_file = request.get("current_file") or ""
    if current_file and os.path.isdir(os.path.dirname(current_file)):
        return os.path.dirname(current_file)
    last = prefs.get(STATE_KEY, "") if prefs is not None else ""
    if last and os.path.isdir(last):
        return last
    documents = {key: path for key, path, _icon in places.user_dirs()}.get("DOCUMENTS")
    if documents and Path(documents).is_dir():
        return str(documents)
    return str(Path.home())


class Picker(QObject):
    """The dialog's state for QML: mode, filters and the file name box;
    `accept` works out the answer, `finish` writes it."""

    changed = Signal()
    message = Signal(str)
    confirmReplace = Signal(str, str)       # path, name
    done = Signal(int)                      # exit code

    def __init__(self, request, lang=None, out=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.out = out or sys.stdout
        self.backend = None
        mode = str(request.get("mode") or "open")
        self.mode = mode if mode in MODES else "open"
        self.multiple = bool(request.get("multiple")) and self.mode == "open"
        self.filters = normalise_filters(request.get("filters"), self.text("all_files"))
        index = request.get("current_filter", 0)
        self._index = index if isinstance(index, int) and 0 <= index < len(self.filters) else 0
        self._name = str(request.get("current_name") or "") if self.mode == "save" else ""
        current_file = str(request.get("current_file") or "")
        if self.mode == "save" and current_file and not self._name:
            self._name = os.path.basename(current_file)
        self._title = str(request.get("title") or "") or self.text(
            {"open": "open_title", "save": "save_as_title", "folder": "select_folder_title"}[self.mode])
        label = str(request.get("accept_label") or "").replace("_", "").replace("&", "")
        self._accept = label or self.text({"open": "open", "save": "save", "folder": "select_folder"}[self.mode])
        self.result = None

    def text(self, key):
        return strings.text(self.lang, key)

    # --- for QML ------------------------------------------------------------------------

    @Property(str, constant=True)
    def modeName(self):
        return self.mode

    @Property(str, constant=True)
    def title(self):
        return self._title

    @Property(str, constant=True)
    def acceptLabel(self):
        return self._accept

    @Property(bool, constant=True)
    def allowsMultiple(self):
        return self.multiple

    @Property(str, constant=True)
    def initialName(self):
        return self._name

    @Property("QStringList", constant=True)
    def filterNames(self):
        return [f["name"] for f in self.filters]

    @Property(int, notify=changed)
    def filterIndex(self):
        return self._index

    @Slot(int)
    def setFilter(self, index):
        if 0 <= index < len(self.filters) and index != self._index:
            self._index = index
            self.changed.emit()
            if self.backend is not None:
                self.backend.current_tab().load(keep_selection=True)

    def filter_items(self, items):
        """Folder listings in the dialog: only what the filter lets through
        (folders always; in folder mode only folders)."""
        if self.mode == "folder":
            return [i for i in items if i.get("isDir")]
        current = self.filters[self._index]
        return [i for i in items if matches(i, current)]

    def _selected(self):
        tab = self.backend.current_tab() if self.backend is not None else None
        return tab.model.selected_items() if tab is not None else []

    @Slot(result=str)
    def selectionText(self):
        """What the selection puts into the file name box."""
        chosen = self._selected()
        if self.mode == "folder":
            dirs = [i for i in chosen if i["isDir"]]
            return dirs[0]["name"] if len(dirs) == 1 else ""
        files = [i for i in chosen if not i["isDir"]]
        if not files:
            return ""
        if len(files) == 1 or not self.multiple:
            return files[0]["name"]
        return " ".join('"' + f["name"] + '"' for f in files)

    @Slot(str)
    def accept(self, text):
        tab = self.backend.current_tab()
        folder = tab.location
        if folder in SPECIAL:
            # Home / This PC: only a full path makes sense here.
            names = split_names(text)
            if names and os.path.isabs(names[0]):
                folder = os.path.dirname(names[0]) or "/"
            else:
                self.message.emit(self.text("choose_folder_first"))
                return
        what, value = decide(self.mode, folder, text, self._selected(), self.multiple, self.filters[self._index])
        if what == "paths":
            self.finish(value)
        elif what == "confirm":
            self.confirmReplace.emit(value, os.path.basename(value))
        elif what == "navigate":
            tab.navigate(value)
        else:
            self.message.emit(self.text(value))

    @Slot(list)
    def chosen(self, paths):
        """Files chosen in the list (a double-click)."""
        files = [p for p in paths if not os.path.isdir(p)]
        if files:
            self.finish(files if self.multiple else files[:1])

    @Slot(list)
    def finish(self, paths):
        paths = [str(p) for p in paths]
        if self.backend is not None:
            folder = os.path.dirname(paths[0]) if paths and self.mode != "folder" else (paths[0] if paths else "")
            if folder:
                self.backend.prefs.set(STATE_KEY, folder)
        self.result = {"paths": paths, "filter": self._index}
        self.out.write(json.dumps(self.result) + "\n")
        self.out.flush()
        self.done.emit(0)

    @Slot()
    def cancel(self):
        if self.result is not None:
            return
        self.result = {"paths": []}
        self.out.write(json.dumps(self.result) + "\n")
        self.out.flush()
        self.done.emit(1)


def read_request(stream=None):
    """The request from standard input (an empty or broken one opens a
    plain Open dialog)."""
    stream = stream or sys.stdin
    try:
        data = json.loads(stream.read() or "{}")
    except (OSError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def run(request, argv=None):
    """Show the dialog; returns the exit code (0 chosen, 1 cancelled)."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine
    from .app import QML_DIR, Backend, prepare_application

    app = prepare_application(argv or sys.argv, "veltos-explorer")
    picker = Picker(request)
    backend = Backend(open_paths=[start_folder(request, places.Pins())], item_filter=picker.filter_items)
    backend.picker = picker
    picker.backend = backend
    code = {"value": 1}

    def finished(exit_code):
        code["value"] = exit_code
        app.exit(exit_code)
    picker.done.connect(finished)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("picker", picker)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Picker.qml")))
    if not engine.rootObjects():
        return 2
    app.exec()
    if picker.result is None:
        picker.cancel()
    return code["value"]
