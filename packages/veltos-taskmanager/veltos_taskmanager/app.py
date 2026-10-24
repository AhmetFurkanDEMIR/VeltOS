"""VeltOS Task Manager: the Windows 11 Task Manager layout on VeltOS
(Processes, Performance, Startup apps). PySide6 + QML."""

import configparser
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import gpu, model, strings, system

QML_DIR = Path(__file__).resolve().parent / "qml"
HISTORY = 60  # seconds shown in the graphs, as Windows
# Windows' engine names (strings "engine_names", same order), and the
# drivers' engine names that belong to each (amdgpu, i915, xe, msm ...).
ENGINES = ("3d", "compute", "decode", "encode", "copy")
ENGINE_WORDS = {"3d": ("gfx", "render", "3d", "rcs"), "compute": ("compute", "ccs"),
                "decode": ("dec", "video", "vcs", "jpeg"), "encode": ("enc", "vecs", "video-enhance"),
                "copy": ("copy", "blitter", "bcs", "sdma", "dma")}


def engine_kind(engine):
    """Which of Windows' engines a driver's engine name is ("render" -> 3d)."""
    name = engine.lower()
    for exact in (True, False):     # "video-enhance" is encode, not "video" (decode)
        for kind, words in ENGINE_WORDS.items():
            if any(name == w if exact else name.startswith(w) for w in words):
                return kind
    return ""


def kde_value(group, key):
    """A kdeglobals value as the session sees it (user, kdedefaults, /etc/xdg)."""
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
    value = kde_value("General", "AccentColor")
    parts = [p for p in value.split(",") if p.strip().isdigit()]
    if len(parts) >= 3:
        return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3])
    return ""


def detached(command):
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Backend(QObject):
    changed = Signal()
    startupChanged = Signal()

    def __init__(self, lang=None, processes=None, performance=None, startup=None,
                 end_task=None, start=detached, gpus=None):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._processes = processes or system.Processes(apps=system.AppIndex(lang=self.lang))
        self._performance = performance or system.Performance()
        self._startup = startup or system.StartupApps(lang=self.lang)
        self._gpus = gpus if gpus is not None else gpu.Gpus()
        self._gpu = []
        self._end_task = end_task or system.end_task
        self._start = start
        self._search = ""
        self._rows = model.RowsModel(self)
        self._groups = {"apps": [], "background": [], "system": []}
        self._perf = {}
        self._history = {key: [0.0] * HISTORY for key in ("cpu", "memory", "disk", "net")}
        self._net_peak = 1.0
        self._process_count = 0
        self._dark = dark_mode()
        self._accent = accent()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self.refresh()

    # --- data ---------------------------------------------------------------------

    @Slot()
    def refresh(self):
        rows = self._processes.snapshot()
        self._process_count = sum(1 for r in rows if not r.get("kernel"))
        self._gpu = self._gpus.sample()
        for row in rows:
            row["gpu"] = self._gpus.per_process.get(row["pid"], 0.0)
        self._groups = system.group(rows, self.lang)
        for index, card in enumerate(self._gpu):
            history = self._history.setdefault(f"gpu{index}", [0.0] * HISTORY)
            self._history[f"gpu{index}"] = history[1:] + [card["busy"] or 0.0]
        perf = self._performance.sample()
        self._perf = perf
        net = perf["netSent"] + perf["netReceived"]
        self._net_peak = max(self._net_peak * 0.98, net, 1.0)
        for key, value in (("cpu", perf["cpu"]), ("memory", perf["memory"]), ("disk", perf["disk"]),
                           ("net", 100.0 * net / self._net_peak)):
            self._history[key] = self._history[key][1:] + [value]
        self._sync_rows()
        self.changed.emit()

    def _sync_rows(self):
        flat = []
        for group in self.groups:
            flat.append({"kind": "header", "key": "header:" + group["key"], "title": group["title"]})
            flat.extend(dict(item, kind="row") for item in group["items"])
        self._rows.sync(flat)

    def start(self):
        self._timer.start()

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(float, notify=changed)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, notify=changed)
    def darkMode(self):
        return self._dark

    @Property(str, notify=changed)
    def accent(self):
        return self._accent

    def _matches(self, item):
        return not self._search or self._search.lower() in item["name"].lower()

    @Property(QObject, constant=True)
    def rows(self):
        return self._rows

    @property
    def groups(self):
        result = []
        for key in ("apps", "background", "system"):
            items = [self._row(item) for item in self._groups[key] if self._matches(item)]
            if items:
                result.append({"key": key, "title": f"{self._texts[key]} ({len(items)})", "items": items})
        return result

    def _row(self, item):
        return {"key": item["key"], "name": item["name"], "icon": item["icon"],
                "count": item["count"], "cpu": item["cpu"],
                "cpuText": self._percent(item["cpu"]),
                "memory": item["memory"],
                "memoryText": system.human_bytes(item["memory"], self.lang),
                "memoryShare": 100.0 * item["memory"] / max(1, self._perf.get("memoryTotal", 1)),
                "gpu": item.get("gpu", 0.0),
                "gpuText": self._percent(item.get("gpu", 0.0)) if getattr(self._gpus, "tracking", True) else ""}

    def _percent(self, value):
        text = f"{value:.1f}%" if value < 10 else f"{value:.0f}%"
        return text.replace(".", ",") if self.lang == "tr" else text

    @Property("QVariantMap", notify=changed)
    def totals(self):
        busy = [card["busy"] for card in self._gpu if card["busy"] is not None]
        return {"cpu": self._percent(self._perf.get("cpu", 0.0)),
                "memory": self._percent(self._perf.get("memory", 0.0)),
                "gpu": self._percent(max(busy)) if busy else ""}

    @Property("QVariantList", notify=changed)
    def devices(self):
        """The Performance page's list: CPU, memory, disk, network, then
        every graphics device ("GPU 0", ...)."""
        return ["cpu", "memory", "disk", "net"] + [f"gpu{i}" for i in range(len(self._gpu))]

    def _gpu_info(self, index, card):
        t = self._texts
        human = lambda v: system.human_bytes(v, self.lang)    # noqa: E731
        busy = card["busy"]
        value = self._percent(busy) if busy is not None else t["not_available"]
        stats = [[t["utilization"], value]]
        labels = dict(zip(ENGINES, t["engine_names"].split("|")))
        named = {}
        for engine, share in card["engines"].items():
            label = labels.get(engine_kind(engine))
            if label:
                named[label] = max(named.get(label, 0.0), share)
        stats += [[label, self._percent(share)] for label, share in sorted(named.items(), key=lambda kv: -kv[1])[:3]]
        if card["dedicatedTotal"]:
            stats.append([t["dedicated_memory"],
                          f"{human(card['dedicatedUsed'] or 0)} / {human(card['dedicatedTotal'])}"])
        if card["sharedTotal"]:
            stats.append([t["shared_memory"], f"{human(card['sharedUsed'] or 0)} / {human(card['sharedTotal'])}"])
        if card["temperature"] is not None:
            stats.append([t["gpu_temperature"], f"{card['temperature']:.0f} °C"])
        stats += [[t["driver"], card["driver"]], [t["location"], card["slot"]]]
        return {"title": t["gpu_n"].replace("{n}", str(index)), "subtitle": card["name"], "value": value,
                "history": self._history.get(f"gpu{index}", [0.0] * HISTORY), "stats": stats,
                "note": "" if busy is not None else t["gpu_no_data"]}

    @Property("QVariantMap", notify=changed)
    def performance(self):
        p = self._perf
        t = self._texts
        human = lambda v: system.human_bytes(v, self.lang)    # noqa: E731
        rate = lambda v: human(v) + "/s"                       # noqa: E731
        speed = f"{p.get('cpuSpeed', 0) / 1000:.2f} GHz"
        return {
            "cpu": {"title": t["cpu"], "subtitle": system.cpu_model(), "value": self._percent(p.get("cpu", 0)),
                    "history": self._history["cpu"],
                    "stats": [[t["utilization"], self._percent(p.get("cpu", 0))],
                              [t["speed"], speed.replace(".", ",") if self.lang == "tr" else speed],
                              [t["processes_count"], str(self._process_count)],
                              [t["uptime"], system.uptime_text(p.get("uptime", 0))],
                              [t["cores"], str(p.get("cores", 0))],
                              [t["logical"], str(p.get("threadsLogical", 0))]]},
            "memory": {"title": t["memory"], "subtitle": human(p.get("memoryTotal", 0)),
                       "value": f"{human(p.get('memoryUsed', 0))} ({self._percent(p.get('memory', 0))})",
                       "history": self._history["memory"],
                       "stats": [[t["in_use"], human(p.get("memoryUsed", 0))],
                                 [t["available"], human(p.get("memoryAvailable", 0))],
                                 [t["total"], human(p.get("memoryTotal", 0))]]},
            "disk": {"title": t["disk"], "subtitle": "", "value": self._percent(p.get("disk", 0)),
                     "history": self._history["disk"],
                     "stats": [[t["read"], rate(p.get("diskRead", 0))],
                               [t["write"], rate(p.get("diskWrite", 0))]]},
            "net": {"title": t["network"], "subtitle": "",
                    "value": f"{t['send']} {rate(p.get('netSent', 0))}  {t['receive']} {rate(p.get('netReceived', 0))}",
                    "history": self._history["net"],
                    "stats": [[t["send"], rate(p.get("netSent", 0))],
                              [t["receive"], rate(p.get("netReceived", 0))]]},
            **{f"gpu{i}": self._gpu_info(i, card) for i, card in enumerate(self._gpu)},
        }

    @Property("QVariantList", notify=startupChanged)
    def startupApps(self):
        return self._startup.list()

    # --- actions ------------------------------------------------------------------

    @Slot(str)
    def setSearch(self, text):
        self._search = text
        self._sync_rows()
        self.changed.emit()

    @Slot(str)
    def endTask(self, key):
        for name in ("apps", "background", "system"):
            for item in self._groups[name]:
                if item["key"] == key:
                    self._end_task(item["pids"])
                    self.refresh()
                    return

    @Slot(str, bool)
    def setStartupEnabled(self, entry_id, enabled):
        self._startup.set_enabled(entry_id, enabled)
        self.startupChanged.emit()

    @Slot()
    def runNewTask(self):
        # Windows opens its Run box; KDE's is KRunner.
        self._start(["krunner"])


def instance_name():
    return f"veltos-taskmanager-{os.getuid()}"


def raise_running():
    """One Task Manager per user, like Windows: ask a running one to come
    to the front. True if there was one."""
    socket = QLocalSocket()
    socket.connectToServer(instance_name())
    if not socket.waitForConnected(500):
        return False
    socket.write(b"raise\n")
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def listen_for_raise(window):
    server = QLocalServer(window)
    QLocalServer.removeServer(instance_name())

    def show():
        connection = server.nextPendingConnection()
        if connection:
            connection.close()
        window.show()
        window.raise_()
        window.requestActivate()

    server.newConnection.connect(show)
    server.listen(instance_name())
    return server


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    if raise_running():
        return 0
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-taskmanager")
    app.setDesktopFileName("veltos-taskmanager")
    app.setWindowIcon(QIcon.fromTheme("veltos-taskmanager"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    server = listen_for_raise(engine.rootObjects()[0])  # noqa: F841 (kept alive)
    backend.start()
    code = app.exec()
    del engine
    return code
