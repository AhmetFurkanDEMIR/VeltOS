"""VeltOS AI: Python backend of the side panel (Windows 11 Copilot's pane).

    veltos-ai            open the panel, or close it if it is open (Windows + C)

The conversation goes to the service chosen in the panel's settings
(providers.py) with the user's own key; actions on the computer
(tools.py) wait for the user's "Allow". One panel per user: a second
start hands "toggle" to the running one (a local socket) and ends. A
closed panel's process ends after ten idle minutes.
"""

import configparser
import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import config, providers, strings, tools

QML_DIR = Path(__file__).resolve().parent / "qml"
MAX_ROUNDS = 10            # tool rounds in one answer
IDLE_EXIT_MS = 10 * 60 * 1000

SYSTEM_PROMPT = """You are VeltOS AI, the assistant built into VeltOS, a desktop operating system based on Debian \
with a Windows 11-like interface (Start, the taskbar, File Explorer, Settings, VeltOS Store, Word/Excel/PowerPoint \
through VeltOS Office). Answer in the language the user writes in. Be helpful and concise; use Markdown for lists \
and code.

You can act on this computer only through the tools you are given. When the user asks for something a tool does, \
call the tool rather than describing the steps: the panel asks the user to allow every change before it happens. \
If no tool fits, say so and explain how to do it in VeltOS (for example Settings > Bluetooth & devices). Never claim \
an action happened unless its tool result says ok. Do not include internal or system XML tags in your response."""


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


class Backend(QObject):
    messagesChanged = Signal()
    settingsChanged = Signal()
    busyChanged = Signal()
    modelsChanged = Signal()
    toggleRequested = Signal()
    lookChanged = Signal()
    _event = Signal(int, str, object)
    _actionDone = Signal(int, int, bool, str)
    _modelsLoaded = Signal(str, object, str)

    def __init__(self, lang=None, opener=None, settings_file=None, threaded=True, starter=None, runner=None,
                 parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._opener = opener
        self._settings_file = settings_file
        self._threaded = threaded
        self._starter = starter or tools.start
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
        self._rounds = 0
        self._models = []
        self._models_busy = False
        self._models_error = ""
        self._event.connect(self._on_event)
        self._actionDone.connect(self._on_action_done)
        self._modelsLoaded.connect(self._on_models)
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
            result.append({"id": name, "title": providers.PROVIDERS[name]["title"],
                           "keyUrl": providers.PROVIDERS[name]["keys"], "hasKey": bool(key),
                           "keyHint": ("…" + key[-4:]) if len(key) > 8 else "",
                           "model": entry.get("model", ""), "endpoint": entry.get("endpoint", "")})
        return result

    @Property(str, notify=settingsChanged)
    def provider(self):
        return self.data.get("provider", "")

    @Property(str, notify=settingsChanged)
    def providerTitle(self):
        name = self.data.get("provider", "")
        if name not in providers.PROVIDERS:
            return ""
        model = self.data["services"][name].get("model", "")
        return providers.PROVIDERS[name]["title"].split(" (")[0] + (f" · {model}" if model else "")

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

    def _save(self):
        try:
            config.save(self.data, self._settings_file)
        except OSError as error:
            print(f"veltos-ai: cannot save settings: {error}", file=sys.stderr)
        self.settingsChanged.emit()

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
        key = {"key": "error_key", "rate": "error_rate", "network": "error_network",
               "model": "error_model"}.get(getattr(error, "kind", ""), "")
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

    @Slot(str)
    def send(self, text):
        text = text.strip()
        if not text or self._busy:
            return
        if not config.ready(self.data):
            self._add("error", self.text("no_key"))
            return
        name = self.data["provider"]
        if self.history_provider and self.history_provider != name:
            self.history = []
        self.history_provider = name
        self._adapter = providers.adapter(name, self.data["services"][name])
        self._adapter.add_user(self.history, text[:8000])
        self._add("user", text)
        self._rounds = 0
        self._start_turn()

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
        adapter, history, tool_list = self._adapter, list(self.history), self._tools()
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
            if not current["text"]:
                current["text"] = self.text("stopped")
            self._set_busy(False)
            self.messagesChanged.emit()
            return
        if self._failed is not None:
            if not current["text"]:
                self._messages.remove(current)
            self._add("error", self.error_text(self._failed))
            self._set_busy(False)
            return
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

    def _handle_calls(self):
        generation = self._generation
        for index, call in enumerate(self._calls):
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
            self._start_turn()

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


def toggle_running():
    """Hands "toggle" to a running panel; True if there was one."""
    socket = QLocalSocket()
    socket.connectToServer(socket_name())
    if not socket.waitForConnected(500):
        return False
    socket.write(b"toggle\n")
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def main(argv=None):
    argv = sys.argv if argv is None else argv
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")
    os.environ["QML_DISABLE_DISK_CACHE"] = "1"
    app = QGuiApplication(argv)
    if toggle_running():
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
    backend = Backend()
    server = QLocalServer()
    QLocalServer.removeServer(socket_name())
    server.listen(socket_name())

    def on_connection():
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            connection.readyRead.connect(lambda c=connection: backend.toggleRequested.emit())
    server.newConnection.connect(on_connection)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    idle = QTimer()
    idle.setSingleShot(True)
    idle.setInterval(IDLE_EXIT_MS)
    idle.timeout.connect(lambda: app.quit() if not window.isVisible() and not backend.busy else idle.start())
    window.visibleChanged.connect(lambda visible: idle.stop() if visible else idle.start())
    window.show()
    window.requestActivate()
    code = app.exec()
    del engine
    return code
