"""VeltOS AI: Python backend of the side panel (Windows 11 Copilot's pane)
and of its window.

    veltos-ai            open the panel, or close it if it is open (Windows + C,
                         the taskbar button)
    veltos-ai --window   open VeltOS AI as a normal window (Start, search)

The conversation goes to the service chosen in the panel's settings
(providers.py) with the user's own key; actions on the computer
(tools.py) wait for the user's "Allow". One panel per user: a second
start hands "toggle" to the running one (a local socket) and ends. A
closed panel's process ends after ten idle minutes; the conversation is
kept until "New chat" (conversation.py).
"""

import configparser
import json
import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import (Property, QAbstractListModel, QByteArray, QFileSystemWatcher, QMetaObject, QModelIndex,
                            QObject, Qt, QTimer, QUrl, Signal, Slot)
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import config, conversation, intents, local, providers, strings, tools

QML_DIR = Path(__file__).resolve().parent / "qml"
MAX_ROUNDS = 10            # tool rounds in one answer
IDLE_EXIT_MS = 10 * 60 * 1000

SYSTEM_PROMPT = """You are VeltOS AI, the assistant built into VeltOS, a desktop operating system based on Debian \
with a Windows 11-like interface (Start, the taskbar, File Explorer, Settings, VeltOS Store, Word/Excel/PowerPoint \
through VeltOS Office). Answer in the language the user writes in. Be helpful and concise; use Markdown for lists \
and code.

You can act on this computer only through the tools you are given. When the user asks for something a tool does, \
call the tool rather than describing the steps: the panel asks the user to allow every change before it happens. \
Prefer the specific tools; use run_command only when none fits, with a short, safe command, and explain what it does. \
Actions that need administrator rights (installing apps, updates, run_command with administrator) make VeltOS ask \
for the administrator's password. If nothing can do it, say so and explain how to do it in VeltOS (for example \
Settings > Bluetooth & devices). Never claim an action happened unless its tool result says ok. Do not include \
internal or system XML tags in your response.

Do exactly what the user asked and nothing more: no other action, no setting the user did not mention, no \
information the user did not ask for. After an action, answer in one short sentence. Summarise command output in a \
few lines; never paste long output."""


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
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def accent_colour():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def socket_name():
    return f"veltos-ai-{os.getuid()}"


def command_output(result, limit=4000):
    """The output part of run_command's result, its last `limit` characters."""
    try:
        output = json.loads(result).get("output") or ""
    except (ValueError, AttributeError):
        output = ""
    output = output.rstrip()
    return ("…\n" + output[-limit:]) if len(output) > limit else output


class ChatModel(QAbstractListModel):
    """The conversation's rows for ChatView, changed in place: rows are
    added, removed and updated one at a time. The list was a JavaScript
    array made again for every streamed piece (every 60 ms): the view made
    every message again, lost its place and jumped, and text could not be
    selected while an answer came (product owner, 2026-10-31)."""

    countChanged = Signal()
    ROLES = ("mid", "kind", "body", "status", "title", "detail")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self._roles = {Qt.ItemDataRole.UserRole + i: name.encode() for i, name in enumerate(self.ROLES)}

    def roleNames(self):
        return {k: QByteArray(v) for k, v in self._roles.items()}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role):
        if not index.isValid() or not 0 <= index.row() < len(self.rows):
            return None
        name = self._roles.get(role)
        return self.rows[index.row()].get(name.decode()) if name else None

    @Property(int, notify=countChanged)
    def count(self):
        return len(self.rows)

    @staticmethod
    def row(message):
        return {"mid": message["id"], "kind": message["kind"], "body": message.get("text") or "",
                "status": message.get("state") or "", "title": message.get("title") or "",
                "detail": message.get("detail") or ""}

    def sync(self, messages):
        new = [self.row(m) for m in messages]
        ids = [r["mid"] for r in new]
        wanted = set(ids)
        before = len(self.rows)
        kept = [r["mid"] for r in self.rows if r["mid"] in wanted]
        remaining = iter(ids)
        if not all(mid in remaining for mid in kept):
            # Messages are only added and removed; anything else is shown anew.
            self.beginResetModel()
            self.rows = new
            self.endResetModel()
        else:
            for i in range(len(self.rows) - 1, -1, -1):
                if self.rows[i]["mid"] not in wanted:
                    self.beginRemoveRows(QModelIndex(), i, i)
                    del self.rows[i]
                    self.endRemoveRows()
            for position, row in enumerate(new):
                if position < len(self.rows) and self.rows[position]["mid"] == row["mid"]:
                    if self.rows[position] != row:
                        self.rows[position] = row
                        index = self.index(position)
                        self.dataChanged.emit(index, index)
                else:
                    self.beginInsertRows(QModelIndex(), position, position)
                    self.rows.insert(position, row)
                    self.endInsertRows()
        if len(self.rows) != before:
            self.countChanged.emit()


class Backend(QObject):
    messagesChanged = Signal()
    sent = Signal()                  # the user sent a message: the chat goes to its end
    settingsChanged = Signal()
    busyChanged = Signal()
    modelsChanged = Signal()
    toggleRequested = Signal()
    windowRequested = Signal()
    lookChanged = Signal()
    localChanged = Signal()
    downloadChanged = Signal()
    hubChanged = Signal()
    _downloadProgress = Signal(int, int, float)
    _downloadDone = Signal(bool, str)
    _hubLoaded = Signal(str, object, str)
    _event = Signal(int, str, object)
    _actionDone = Signal(int, int, bool, str)
    _modelsLoaded = Signal(str, object, str)
    _openUrl = Signal(str)

    def __init__(self, lang=None, opener=None, settings_file=None, threaded=True, starter=None, runner=None,
                 conversation_file=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._opener = opener
        self._settings_file = settings_file
        self._threaded = threaded
        self._starter = starter or self._start
        self._runner = runner or tools.run
        self.data = config.load(settings_file)
        self.history = []
        self.history_provider = ""
        self._messages = []
        self._next_id = 1
        self._busy = False
        self._generation = 0
        self._cancel = threading.Event()
        self._adapter = None
        self._calls = []
        self._results = {}
        self._stop = ""
        self._failed = None
        self._command_done = False
        self._rounds = 0
        self._models = []
        self._models_busy = False
        self._models_error = ""
        self._event.connect(self._on_event)
        self._actionDone.connect(self._on_action_done)
        self._openUrl.connect(self.openUrl)
        self._modelsLoaded.connect(self._on_models)
        # The local model (local.py): downloads and Hugging Face.
        self._download = {"active": False, "file": "", "title": "", "done": 0, "total": 0, "speed": 0.0,
                          "error": ""}
        self._download_cancel = None
        self._hub = {"busy": False, "error": "", "query": "", "results": [], "repo": "", "files": []}
        self._downloadProgress.connect(self._on_download_progress)
        self._downloadDone.connect(self._on_download_done)
        self._hubLoaded.connect(self._on_hub)
        self._flush = QTimer(self)
        self._flush.setInterval(60)
        self._flush.setSingleShot(True)
        self._flush.timeout.connect(self.messagesChanged.emit)
        # The pane follows light/dark and the accent at once: it can switch
        # the theme itself ("Switch to light mode").
        self._dark = kde_value("KDE", "LookAndFeelPackage").endswith(".dark")
        self._accent = accent_colour()
        self._watcher = QFileSystemWatcher(self)
        self._kdeglobals = str(Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kdeglobals")
        self._watch()
        self._watcher.fileChanged.connect(lambda _path: QTimer.singleShot(300, self._reload_look))
        self._chat = ChatModel(self)
        self.messagesChanged.connect(lambda: self._chat.sync(self._messages))
        # The conversation is kept between starts (conversation.py), written
        # when no answer is on its way.
        self._conversation_file = conversation_file
        self._save_timer = QTimer(self)
        self._save_timer.setInterval(400)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_conversation)
        self.messagesChanged.connect(self._save_timer.start)
        self.busyChanged.connect(self._save_timer.start)
        self._restore_conversation()

    def _restore_conversation(self):
        if not self._conversation_file:
            return
        state = conversation.load(self._conversation_file)
        self._messages = state["messages"]
        self.history = state["history"]
        self.history_provider = state["provider"]
        self._next_id = max((m["id"] for m in self._messages), default=0) + 1
        self.messagesChanged.emit()

    @Slot()
    def save_conversation(self):
        if not self._conversation_file or self._busy:
            return
        try:
            if self._messages:
                conversation.save(self._conversation_file, self._messages, self.history, self.history_provider)
            else:
                conversation.clear(self._conversation_file)
        except OSError:
            pass

    # --- look and texts -----------------------------------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    def _watch(self):
        if os.path.exists(self._kdeglobals) and self._kdeglobals not in self._watcher.files():
            self._watcher.addPath(self._kdeglobals)

    def _reload_look(self):
        self._watch()          # an editor replacing the file drops the watch
        dark = kde_value("KDE", "LookAndFeelPackage").endswith(".dark")
        accent = accent_colour()
        if (dark, accent) != (self._dark, self._accent):
            self._dark, self._accent = dark, accent
            self.lookChanged.emit()

    @Property(bool, notify=lookChanged)
    def darkMode(self):
        return self._dark

    @Property(str, notify=lookChanged)
    def accent(self):
        return self._accent

    @Property(float, constant=True)
    def textScale(self):
        return text_scale()

    @Slot(str)
    def copyText(self, text):
        QGuiApplication.clipboard().setText(text)

    @Slot(str)
    def openUrl(self, url):
        if url.startswith(("https://", "http://")):
            QDesktopServices.openUrl(QUrl(url))

    # --- settings --------------------------------------------------------------------------------------

    @Property("QVariantList", notify=settingsChanged)
    def services(self):
        result = []
        for name in providers.ORDER:
            entry = self.data["services"][name]
            key = entry.get("key", "")
            result.append({"id": name, "title": self.service_title(name),
                           "keyUrl": providers.PROVIDERS[name]["keys"], "hasKey": bool(key),
                           "keyHint": ("…" + key[-4:]) if len(key) > 8 else "",
                           "model": entry.get("model", ""), "endpoint": entry.get("endpoint", "")})
        return result

    def service_title(self, name):
        """The service's name; the local model's in the session's language
        (it showed "Local model (free, offline)" in Turkish, 2026-10-31)."""
        if name == "local":
            return strings.text(self.lang, "local_title")
        return providers.PROVIDERS[name]["title"]

    @Property(str, notify=settingsChanged)
    def provider(self):
        return self.data.get("provider", "")

    @Property(str, notify=settingsChanged)
    def providerTitle(self):
        name = self.data.get("provider", "")
        if name not in providers.PROVIDERS:
            return ""
        model = self.data["services"][name].get("model", "")
        return self.service_title(name).split(" (")[0] + (f" · {model}" if model else "")

    @Property(bool, notify=settingsChanged)
    def ready(self):
        return config.ready(self.data)

    @Property(bool, notify=settingsChanged)
    def actionsAllowed(self):
        return bool(self.data.get("actions", True))

    @Slot(bool)
    def setActionsAllowed(self, allowed):
        self.data["actions"] = bool(allowed)
        self._save()

    @Slot(str, str, str, str)
    def saveService(self, name, key, model, endpoint):
        """Saves a service's key, model and endpoint and makes it the chosen one.
        An empty key keeps the saved one."""
        if name not in providers.PROVIDERS:
            return
        entry = self.data["services"][name]
        if key.strip():
            entry["key"] = key.strip()
        entry["model"] = model.strip() or providers.PROVIDERS[name]["model"]
        entry["endpoint"] = endpoint.strip()
        if self.data.get("provider") != name:
            self.newChat()
        self.data["provider"] = name
        self._save()

    @Slot(str)
    def removeKey(self, name):
        if name in providers.PROVIDERS:
            self.data["services"][name]["key"] = ""
            self._save()

    @Slot()
    def reloadSettings(self):
        """Reads the settings again when VeltOS Settings changed them (its
        VeltOS AI page writes the same file) while the pane kept running."""
        data = config.load(self._settings_file)
        if data != self.data:
            if data.get("provider") != self.data.get("provider"):
                self.newChat()
            self.data = data
            self.settingsChanged.emit()

    def _save(self):
        try:
            config.save(self.data, self._settings_file)
        except OSError as error:
            print(f"veltos-ai: cannot save settings: {error}", file=sys.stderr)
        self.settingsChanged.emit()

    # --- the local model (local.py) --------------------------------------------------------------------

    @Property(bool, constant=True)
    def localEngine(self):
        return local.engine_available()

    @Property("QVariantMap", notify=localChanged)
    def localDefault(self):
        d = local.DEFAULT_MODEL
        return {"title": d["title"], "file": d["file"], "size": local.size_text(d["size"]),
                "installed": local.model_path(d["file"]) is not None, "license": d["license"]}

    @Property("QVariantList", notify=localChanged)
    def localModels(self):
        chosen = self.data["services"]["local"].get("model", "")
        return [{"file": m["file"], "size": local.size_text(m["size"]), "active": m["file"] == chosen}
                for m in local.installed()]

    @Property("QVariantMap", notify=downloadChanged)
    def download(self):
        d = dict(self._download)
        d["percent"] = int(100 * d["done"] / d["total"]) if d["total"] else 0
        d["progress"] = strings.text(self.lang, "download_progress", done=local.size_text(d["done"]),
                                     total=local.size_text(d["total"]) if d["total"] else "?",
                                     speed=local.size_text(int(d["speed"])) + "/s")
        return d

    def _start_download(self, url, file, size, sha256, title):
        name = local.safe_name(file)
        if not name or self._download["active"]:
            return
        self._download = {"active": True, "file": name, "title": title or name, "done": 0, "total": size,
                          "speed": 0.0, "error": ""}
        self.downloadChanged.emit()
        cancel = threading.Event()
        self._download_cancel = cancel

        def work():
            try:
                ok = local.download(url, local.models_dir() / name, size, sha256,
                                    lambda done, total, speed: self._downloadProgress.emit(done, total, speed),
                                    cancel, self._opener)
                self._downloadDone.emit(ok, "")
            except local.DownloadError as error:
                self._downloadDone.emit(False, str(error) or "download")
        self._spawn(work)

    @Slot()
    def downloadDefault(self):
        d = local.DEFAULT_MODEL
        self._start_download(local.resolve_url(d["repo"], d["file"], d["revision"]), d["file"], d["size"],
                             d["sha256"], d["title"])

    @Slot(str, str, str, str)
    def downloadHub(self, repo, file, size, sha256):
        try:
            size_value = int(size or 0)
        except ValueError:
            size_value = 0
        self._start_download(local.resolve_url(repo, file), file, size_value, sha256, f"{repo} · {file}")

    @Slot()
    def cancelDownload(self):
        if self._download_cancel is not None:
            self._download_cancel.set()

    @Slot(int, int, float)
    def _on_download_progress(self, done, total, speed):
        self._download.update(done=done, total=total or self._download["total"], speed=speed)
        self.downloadChanged.emit()

    @Slot(bool, str)
    def _on_download_done(self, ok, error):
        file = self._download["file"]
        self._download.update(active=False, error=error)
        self._download_cancel = None
        self.downloadChanged.emit()
        if ok:
            self.useLocalModel(file)
        self.localChanged.emit()

    @Slot(str)
    def useLocalModel(self, file):
        """The downloaded model becomes VeltOS AI's (local) service."""
        if local.model_path(file) is None:
            return
        self.data["services"]["local"]["model"] = local.safe_name(file)
        if self.data.get("provider") != "local":
            self.newChat()
        self.data["provider"] = "local"
        self._save()
        self.localChanged.emit()

    @Slot(str)
    def deleteLocalModel(self, file):
        path = local.model_path(file)
        if path is None:
            return
        try:
            path.unlink()
        except OSError:
            return
        if self.data["services"]["local"].get("model") == path.name:
            local.SERVER_INSTANCE.stop()
            self.settingsChanged.emit()
        self.localChanged.emit()

    @Property("QVariantMap", notify=hubChanged)
    def hub(self):
        return dict(self._hub, files=[dict(f, sizeText=local.size_text(f["size"]),
                                           sizeValue=str(f["size"])) for f in self._hub["files"]])

    @Slot(str)
    def searchHub(self, query):
        query = query.strip()
        if not query:
            return
        self._hub.update(busy=True, error="", query=query, repo="", files=[], results=[])
        self.hubChanged.emit()

        def work():
            try:
                self._hubLoaded.emit("results", local.search(query, self._opener), "")
            except local.DownloadError as error:
                self._hubLoaded.emit("results", [], str(error) or "network")
        self._spawn(work)

    @Slot(str)
    def openHubRepo(self, repo):
        self._hub.update(busy=True, error="", repo=repo, files=[])
        self.hubChanged.emit()

        def work():
            try:
                self._hubLoaded.emit("files", local.repo_files(repo, self._opener), "")
            except local.DownloadError as error:
                self._hubLoaded.emit("files", [], str(error) or "network")
        self._spawn(work)

    @Slot()
    def closeHubRepo(self):
        self._hub.update(repo="", files=[], error="")
        self.hubChanged.emit()

    @Slot(str, object, str)
    def _on_hub(self, kind, found, error):
        self._hub.update(busy=False, error=error)
        self._hub[kind] = list(found or [])
        self.hubChanged.emit()

    # --- models ---------------------------------------------------------------------------------------

    @Property("QVariantList", notify=modelsChanged)
    def models(self):
        return self._models

    @Property(bool, notify=modelsChanged)
    def modelsBusy(self):
        return self._models_busy

    @Property(str, notify=modelsChanged)
    def modelsError(self):
        return self._models_error

    @Slot(str, str, str)
    def loadModels(self, name, key, endpoint):
        if name not in providers.PROVIDERS:
            return
        settings = dict(self.data["services"][name])
        if key.strip():
            settings["key"] = key.strip()
        settings["endpoint"] = endpoint.strip()
        adapter = providers.adapter(name, settings)
        self._models, self._models_busy, self._models_error = [], True, ""
        self.modelsChanged.emit()

        def work():
            try:
                found = providers.list_models(adapter, self._opener)
                self._modelsLoaded.emit(name, found, "")
            except providers.ServiceError as error:
                self._modelsLoaded.emit(name, [], self.error_text(error))
        self._spawn(work)

    @Slot(str, object, str)
    def _on_models(self, name, found, error):
        self._models = list(found or [])
        self._models_busy = False
        self._models_error = error
        self.modelsChanged.emit()

    @Slot(str, str, result=str)
    def pickModel(self, name, current):
        return providers.pick_model(name, self._models, current) if name in providers.PROVIDERS else current

    # --- the conversation ------------------------------------------------------------------------------

    @Property("QVariantList", notify=messagesChanged)
    def messages(self):
        return [dict(m) for m in self._messages]

    @Property(QObject, constant=True)
    def chat(self):
        return self._chat

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    def _set_busy(self, busy):
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    def _add(self, kind, text="", **extra):
        message = {"id": self._next_id, "kind": kind, "text": text, "state": "", "title": ""}
        message.update(extra)
        self._next_id += 1
        self._messages.append(message)
        self.messagesChanged.emit()
        return message

    def _spawn(self, work):
        if self._threaded:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()

    def error_text(self, error):
        if getattr(error, "kind", "") == "local":
            return strings.text(self.lang, "error_local", detail=str(getattr(error, "detail", ""))[:200])
        key = {"key": "error_key", "rate": "error_rate", "network": "error_network",
               "model": "error_local_model" if self.data.get("provider") == "local" else "error_model"}.get(
            getattr(error, "kind", ""), "")
        if key:
            return self.text(key)
        return strings.text(self.lang, "error_other", detail=str(getattr(error, "detail", error))[:300])

    @Slot()
    def newChat(self):
        self.stop()
        self._generation += 1
        self.history = []
        self.history_provider = ""
        self._messages = []
        self._calls = []
        self._results = {}
        self.messagesChanged.emit()
        self._set_busy(False)
        self.save_conversation()

    @Slot(str)
    def send(self, text):
        text = text.strip()
        if not text or self._busy:
            return
        if not config.ready(self.data):
            self._add("error", self.text("no_key"))
            return
        name = self.data["provider"]
        self._adapter = providers.adapter(name, self.data["services"][name])
        self._add("user", text)
        self.sent.emit()
        if self.history_provider != name:
            # Another service than the one the conversation was with (or a
            # conversation without one): it is told the conversation's words
            # so far. The history was emptied before, and the model knew
            # nothing of what the panel still showed.
            self.history = self._transcript(self._adapter)
        else:
            self._adapter.add_user(self.history, text[:8000])
        self.history_provider = name
        self._rounds = 0
        self._command_done = False
        # The local model: a short command it might get wrong becomes its
        # action at once (intents.py); the model then words the answer.
        command = intents.match(text, self.lang) if name == "local" and self.data.get("actions", True) else None
        if command and tools.validate(*command) is not None:
            self._start_command(*command)
            return
        self._start_turn()

    def _transcript(self, adapter):
        """The conversation's words (the user's messages and the answers)
        in the service's format; actions' results are not told again. Turns
        of one side in a row are joined (an answer that failed): some
        services refuse two user turns in a row."""
        turns = []
        for message in self._messages:
            role = {"user": "user", "assistant": "assistant"}.get(message["kind"])
            text = message.get("text") or ""
            if role is None or not text or message.get("state") in ("refused", "streaming"):
                continue
            if message.get("state") == "stopped" and text == self.text("stopped"):
                continue
            if turns and turns[-1][0] == role:
                turns[-1][1] += "\n\n" + text
            else:
                turns.append([role, text])
        while turns and turns[0][0] != "user":
            turns.pop(0)
        history = []
        for role, text in turns:
            (adapter.add_user if role == "user" else adapter.add_assistant)(history, text[:8000])
        return history

    def _start_command(self, name, arguments):
        """Runs a recognised command as if the model had asked for it: an
        assistant turn with the tool call goes into the history, and the
        panel asks "Allow" as for any action."""
        call = {"id": "veltos_command", "name": name, "input": arguments}
        self.history.append({"role": "assistant", "content": "", "tool_calls": [
            {"id": call["id"], "type": "function",
             "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)}}]})
        self._generation += 1
        self._cancel.clear()
        self._calls, self._results, self._stop, self._failed = [call], {}, "", None
        self._current = {"text": "", "state": ""}
        self._set_busy(True)
        self._rounds = 1
        self._handle_calls()
        self.messagesChanged.emit()

    def _tools(self):
        if self.data.get("actions", True):
            return tools.TOOLS
        return [t for t in tools.TOOLS if t["name"] in tools.READ_ONLY]

    def _start_turn(self):
        self._generation += 1
        generation = self._generation
        self._cancel.clear()
        self._calls, self._results, self._stop, self._failed = [], {}, "", None
        self._current = self._add("assistant", "", state="streaming")
        self._set_busy(True)
        # After a recognised command the model only words the answer: given
        # the tools again, the local model went on to "install slack" after
        # "install sl" had worked (installed dev VM, 2026-10-31). The local
        # model also gets no tools after any action: it went on with other
        # actions nobody asked for (night light, brightness after "switch to
        # light mode", product owner 2026-11-01).
        local_follow_up = self.data.get("provider") == "local" and self._rounds >= 1
        tool_list = [] if self._command_done or local_follow_up else self._tools()
        adapter, history = self._adapter, list(self.history)
        cancel = self._cancel

        def work():
            try:
                for kind, payload in providers.stream(adapter, history, SYSTEM_PROMPT, tool_list, self._opener,
                                                      cancel.is_set):
                    self._event.emit(generation, kind, payload)
                    if cancel.is_set():
                        break
            except providers.ServiceError as error:
                self._event.emit(generation, "error", error)
            except Exception as error:   # an unexpected answer must not end the panel
                self._event.emit(generation, "error", providers.ServiceError("other", str(error)))
            self._event.emit(generation, "finished", None)
        self._spawn(work)

    @Slot(int, str, object)
    def _on_event(self, generation, kind, payload):
        if generation != self._generation:
            return
        if kind == "text":
            self._current["text"] += payload
            if not self._flush.isActive():
                self._flush.start()
        elif kind == "tool":
            self._calls.append(payload)
        elif kind == "end":
            self._stop = payload.get("stop", "")
        elif kind == "error":
            self._failed = payload
        elif kind == "finished":
            self._finish_turn()

    def _finish_turn(self):
        current = self._current
        current["state"] = ""
        if self._cancel.is_set():
            current["state"] = "stopped"
            if current["text"]:
                # The model is told what it had said when the user stopped it.
                self._adapter.add_assistant(self.history, current["text"])
            else:
                current["text"] = self.text("stopped")
            self._set_busy(False)
            self.messagesChanged.emit()
            return
        if self._failed is not None:
            if not current["text"]:
                self._messages.remove(current)
            if self._command_done:
                # A recognised command already did its work; only the
                # model's words are missing (it could not start): no error.
                self._add("assistant", self.text("command_done"))
            else:
                self._add("error", self.error_text(self._failed))
            self._command_done = False
            self._set_busy(False)
            return
        self._command_done = False
        if self._stop == "refusal":
            current["text"] = self.text("refused")
            current["state"] = "refused"
            self._set_busy(False)
            self.messagesChanged.emit()
            return
        self.history.extend(self._adapter.turn)
        if not current["text"] and self._calls:
            self._messages.remove(current)
        if self._calls and self._rounds < MAX_ROUNDS:
            self._rounds += 1
            self._handle_calls()
        else:
            self._set_busy(False)
        self.messagesChanged.emit()

    # --- actions ----------------------------------------------------------------------------------------

    def _asked_text(self):
        """The user's last message, and the answer before it (a "yes" to a
        question the assistant asked counts for what it asked about)."""
        texts, user_seen = [], False
        for message in reversed(self._messages):
            if message["kind"] == "user":
                if user_seen:
                    break
                user_seen = True
                texts.append(message.get("text") or "")
            elif message["kind"] == "assistant" and user_seen:
                texts.append(message.get("text") or "")
                break
        return "\n".join(texts)

    def _handle_calls(self):
        generation = self._generation
        asked = self._asked_text()
        for index, call in enumerate(self._calls):
            if not tools.asked_for(call.get("name", ""), asked):
                # Not shown and not done; the service is told why.
                self._results[index] = (False, '{"ok": false, "error": "Not done: the user did not ask for this. '
                                               'Do not do it unless the user asks for it."}')
                continue
            arguments = tools.validate(call.get("name", ""), call.get("input"))
            title = tools.title(call.get("name", ""), arguments, self.lang)
            message = self._add("action", "", title=title, state="", call=index)
            call["message"] = message["id"]
            if arguments is None:
                self._record(index, False, '{"ok": false, "error": "The action or its arguments are not valid."}',
                             "failed")
            elif tools.needs_approval(call["name"]) and not self.data.get("actions", True):
                self._record(index, False, '{"ok": false, "error": "Actions are turned off in VeltOS AI settings."}',
                             "denied")
            elif tools.needs_approval(call["name"]):
                call["arguments"] = arguments
                message["state"] = "ask"
            else:
                call["arguments"] = arguments
                message["state"] = "running"
                self._run_action(generation, index)
        self.messagesChanged.emit()
        self._maybe_continue()

    def _start(self, command):
        """Actions' programs; a web page goes through Qt in the main thread
        (the portal, with the pane's activation token), so the browser
        comes to the front: an xdg-open child has no token (VM 2026-10-25).
        Actions run in a worker thread, hence the signal."""
        if len(command) == 2 and command[0] == "xdg-open":
            self._openUrl.emit(command[1])
            return
        tools.start(command)

    def _message(self, message_id):
        return next((m for m in self._messages if m["id"] == message_id), None)

    def _record(self, index, ok, output, state):
        self._results[index] = (ok, output)
        message = self._message(self._calls[index].get("message"))
        if message is not None:
            message["state"] = state
        self.messagesChanged.emit()

    def _run_action(self, generation, index):
        call = self._calls[index]

        def work():
            try:
                ok, output = tools.execute(call["name"], call["arguments"], self.lang, self._starter, self._runner)
            except Exception as error:
                ok, output = False, '{"ok": false, "error": %s}' % repr(str(error))
            self._actionDone.emit(generation, index, ok, output)
        self._spawn(work)

    @Slot(int, int, bool, str)
    def _on_action_done(self, generation, index, ok, output):
        if generation != self._generation:
            return
        if ok and self._calls[index].get("id") == "veltos_command":
            self._command_done = True
        if self._calls[index].get("name") == "run_command":
            # The command's output under its card, folded away (long output
            # stretched the conversation, product owner 2026-11-01).
            message = self._message(self._calls[index].get("message"))
            if message is not None:
                message["detail"] = command_output(output)
        self._record(index, ok, output, "done" if ok else "failed")
        self._maybe_continue()

    @Slot(int)
    def allowAction(self, message_id):
        self._decide(message_id, True)

    @Slot(int)
    def denyAction(self, message_id):
        self._decide(message_id, False)

    def _decide(self, message_id, allowed):
        message = self._message(message_id)
        if message is None or message.get("state") != "ask":
            return
        index = message["call"]
        if allowed:
            message["state"] = "running"
            self.messagesChanged.emit()
            self._run_action(self._generation, index)
        else:
            self._record(index, False, '{"ok": false, "error": "The user did not allow this action."}', "denied")
            self._maybe_continue()

    def _maybe_continue(self):
        if self._busy and self._calls and len(self._results) == len(self._calls):
            results = [(call, self._results[i][1], not self._results[i][0]) for i, call in enumerate(self._calls)]
            self._adapter.add_tool_results(self.history, results)
            confirmation = self._confirmation()
            if confirmation:
                self._adapter.add_assistant(self.history, confirmation)
                self._add("assistant", confirmation)
                self._set_busy(False)
                return
            self._start_turn()

    def _confirmation(self):
        """With the local model, switches that all worked are confirmed in
        VeltOS' own words (tools.done_text) instead of the model's."""
        if self.data.get("provider") != "local":
            return ""
        texts = []
        for index, call in enumerate(self._calls):
            ok = self._results[index][0]
            text = tools.done_text(call.get("name", ""), call.get("arguments"), self.lang) if ok else ""
            if not text:
                return ""
            texts.append(text)
        return " ".join(texts)

    @Slot()
    def stop(self):
        if not self._busy:
            return
        self._cancel.set()
        waiting = [m for m in self._messages if m.get("state") in ("ask", "running")]
        for message in waiting:
            message["state"] = "denied"
        if self._calls and self._current.get("state") != "streaming":
            # Waiting for an answer about an action: the turn ends here. The
            # service still gets a result for every call it made (the next
            # message would be refused without them).
            results = [(call, self._results[i][1] if i in self._results else
                        '{"ok": false, "error": "The user stopped the answer."}',
                        not (i in self._results and self._results[i][0])) for i, call in enumerate(self._calls)]
            self._adapter.add_tool_results(self.history, results)
            self._calls = []
            self._generation += 1
            self._set_busy(False)
        self.messagesChanged.emit()


def toggle_running(request="toggle"):
    """Hands "toggle" (the pane) or "window" to a running VeltOS AI, with
    this start's activation token; True if there was one."""
    socket = QLocalSocket()
    socket.connectToServer(socket_name())
    if not socket.waitForConnected(500):
        return False
    token = os.environ.get("XDG_ACTIVATION_TOKEN", "")
    socket.write(f"{request} {token}\n".encode())
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def take_request(backend, data):
    words = bytes(data).decode("utf-8", "replace").split()
    if len(words) > 1:
        os.environ["XDG_ACTIVATION_TOKEN"] = words[1]
    backend.reloadSettings()
    if words and words[0] == "window":
        backend.windowRequested.emit()
    else:
        backend.toggleRequested.emit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    app = QGuiApplication(argv)
    as_window = "--window" in argv[1:]
    if toggle_running("window" if as_window else "toggle"):
        return 0
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-ai")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-ai")
    app.setWindowIcon(QIcon.fromTheme("veltos-ai"))
    app.setQuitOnLastWindowClosed(False)
    backend = Backend(conversation_file=conversation.path())
    server = QLocalServer()
    QLocalServer.removeServer(socket_name())
    server.listen(socket_name())

    def on_connection():
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            connection.readyRead.connect(lambda c=connection: take_request(backend, c.readAll()))
    server.newConnection.connect(on_connection)
    app.aboutToQuit.connect(local.SERVER_INSTANCE.stop)
    app.aboutToQuit.connect(backend.save_conversation)
    # The pane (Main.qml, the taskbar button and Windows + C) and the window
    # (AppWindow.qml, Start and search) share one conversation; each is
    # made the first time it is asked for.
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    windows = {}
    idle = QTimer()
    idle.setSingleShot(True)
    idle.setInterval(IDLE_EXIT_MS)

    def any_visible():
        return any(w.isVisible() for w in windows.values())
    idle.timeout.connect(lambda: app.quit() if not any_visible() and not backend.busy else idle.start())

    def make(kind):
        if kind not in windows:
            before = len(engine.rootObjects())
            engine.load(QUrl.fromLocalFile(str(QML_DIR / ("AppWindow.qml" if kind == "window" else "Main.qml"))))
            if len(engine.rootObjects()) == before:
                return None
            windows[kind] = engine.rootObjects()[-1]
            windows[kind].visibleChanged.connect(lambda _v: idle.stop() if any_visible() else idle.start())
        return windows[kind]

    def open_window():
        window = make("window")
        if window is not None:
            window.setProperty("visible", True)
            window.raise_()
            window.requestActivate()

    def toggle_pane():
        pane = make("pane")
        if pane is not None:
            QMetaObject.invokeMethod(pane, "toggle")
    backend.windowRequested.connect(open_window)
    backend.toggleRequested.connect(toggle_pane)
    if as_window:
        open_window()
    else:
        toggle_pane()
    if not windows:
        return 1
    code = app.exec()
    del engine
    return code
