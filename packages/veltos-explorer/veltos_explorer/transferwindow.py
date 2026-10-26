"""Windows 11's copy window: `veltos-explorer --transfer copy|move FOLDER
PATH...` (File Explorer's paste and drop, the desktop's paste).

The window (qml/Transfer.qml) shows "37% complete", what is copied from
where to where, a bar with Pause and Cancel and, with "More details", the
speed as a graph, the name, the time and the items remaining. A conflict
asks "Replace or Skip Files". Like Windows it appears only when the work
takes longer than a moment, and closes itself when everything went well;
errors stay on screen with Close.
"""

import os
import threading

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine

from . import files, strings, transfer

SHOW_AFTER_MS = 500
TICK_MS = 150
GRAPH_POINTS = 60


def folder_label(path):
    name = os.path.basename(os.path.normpath(path))
    return name or path


class TransferBackend(QObject):
    changed = Signal()
    conflictChanged = Signal()
    _asked = Signal()

    def __init__(self, job, base, lang=None, parent=None):
        """`job` is a transfer.Transfer whose ask callback is self.ask;
        `base` gives the theme values (app.EmptyBinBackend)."""
        super().__init__(parent)
        self.lang = lang or strings.language()
        self.job = job
        self._base = base
        self._details = False
        self._history = []
        self._pending = None
        self._answer = None
        self._answered = threading.Event()
        self._asked.connect(self.conflictChanged.emit)
        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._tick)

    # theme values for Theme.qml
    @Property(bool, constant=True)
    def darkMode(self):
        return self._base.darkMode

    @Property(str, constant=True)
    def accentColor(self):
        return self._base.accentColor

    @Property(float, constant=True)
    def textScale(self):
        return self._base.textScale

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    def t(self, key, **values):
        return strings.text(self.lang, key, **values)

    # --- the worker ----------------------------------------------------------------

    def start(self):
        threading.Thread(target=self.job.run, daemon=True).start()
        self._timer.start()

    def ask(self, item):
        """Called from the worker for a conflict: waits for the window."""
        self._pending = item
        self._answered.clear()
        self._asked.emit()
        self._answered.wait()
        self._pending = None
        self._asked.emit()
        return self._answer

    @Slot(str, bool)
    def answer(self, choice, for_all):
        if self._pending is None:
            return
        self._answer = (transfer.REPLACE if choice == "replace" else transfer.SKIP, bool(for_all))
        self._answered.set()

    def _tick(self):
        speed = self.job.speed()
        self._history.append(speed)
        self._history = self._history[-GRAPH_POINTS:]
        self.changed.emit()
        if self.job.finished:
            self._timer.stop()

    # --- what the window shows ------------------------------------------------------

    @Property(bool, notify=changed)
    def finished(self):
        return self.job.finished

    @Property(bool, notify=changed)
    def failed(self):
        return bool(self.job.errors or self.job.problems)

    @Property(int, notify=changed)
    def percent(self):
        return int(self.job.fraction * 100)

    @Property(str, notify=changed)
    def title(self):
        if self.job.paused:
            return self.t("transfer_paused_title", percent=self.percent)
        return self.t("transfer_percent", percent=self.percent)

    @Property(str, constant=True)
    def heading(self):
        sources = self.job.sources
        source = folder_label(os.path.dirname(sources[0])) if sources else ""
        key = "transfer_moving" if self.job.mode == "move" else "transfer_copying"
        count = max(1, self.job.total_items)
        if count == 1:
            return self.t(key + "_one", source=source, target=folder_label(self.job.destination))
        return self.t(key, count=count, source=source, target=folder_label(self.job.destination))

    @Property(str, notify=changed)
    def name(self):
        return self.t("transfer_name", name=self.job.current) if self.job.current else ""

    @Property(str, notify=changed)
    def speedText(self):
        speed = self.job.speed()
        return self.t("transfer_speed", speed=files.human_size(int(speed)) + "/s") if speed > 0 else ""

    @Property(str, notify=changed)
    def remaining(self):
        return self.t("transfer_time", time=transfer.duration_text(self.job.seconds_left(), self.lang))

    @Property(str, notify=changed)
    def itemsLeft(self):
        items = max(0, self.job.total_items - self.job.done_items)
        size = max(0, self.job.total_bytes - self.job.done_bytes)
        return self.t("transfer_items", items=items, size=files.human_size(size))

    @Property(bool, notify=changed)
    def paused(self):
        return self.job.paused

    @Property(bool, notify=changed)
    def details(self):
        return self._details

    @Property("QVariantList", notify=changed)
    def graph(self):
        """The speed history scaled to 0..1 (the graph behind the bar)."""
        top = max(self._history) if self._history else 0
        return [round(v / top, 3) if top else 0 for v in self._history]

    @Property(bool, notify=conflictChanged)
    def conflict(self):
        return self._pending is not None

    @Property(str, notify=conflictChanged)
    def conflictText(self):
        item = self._pending
        if item is None:
            return ""
        return self.t("transfer_conflict", name=os.path.basename(item.target),
                      folder=folder_label(os.path.dirname(item.target)))

    @Property(str, notify=changed)
    def errorText(self):
        lines = [f"{os.path.basename(path)}: {self.t('transfer_into_itself') if why == 'into_itself' else why}"
                 for path, why in self.job.problems + self.job.errors]
        return "\n".join(lines[:8]) + ("\n…" if len(lines) > 8 else "")

    @Slot()
    def toggleDetails(self):
        self._details = not self._details
        self.changed.emit()

    @Slot()
    def togglePause(self):
        if self.job.paused:
            self.job.resume()
        else:
            self.job.pause()
        self.changed.emit()

    @Slot()
    def cancel(self):
        self.job.cancel()
        if self._pending is not None:
            self._answer = (transfer.SKIP, True)
            self._answered.set()


def run(argv, prepare_application, base_factory):
    """`--transfer copy|move FOLDER PATH...`."""
    words = [a for a in argv[1:] if a != "--transfer"]
    if len(words) < 3 or words[0] not in ("copy", "move"):
        return 2
    mode, destination, sources = words[0], words[1], words[2:]
    sources = [s[7:] if s.startswith("file://") else s for s in sources]
    if not os.path.isdir(destination):
        return 1
    app = prepare_application([argv[0]], "veltos-explorer", "transfer_window")
    backend = None

    def ask(item):
        return backend.ask(item)

    job = transfer.Transfer(sources, destination, mode, ask=ask)
    backend = TransferBackend(job, base_factory())
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(os.path.join(os.path.dirname(__file__), "qml", "Transfer.qml"))))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    backend.start()
    # Shown only when the work takes a moment (or asks something).
    QTimer.singleShot(SHOW_AFTER_MS, lambda: window.setProperty("visible", True)
                      if not job.finished or backend.failed else None)
    backend.conflictChanged.connect(lambda: window.setProperty("visible", True) if backend.conflict else None)

    def done():
        if job.finished:
            if backend.failed and not job.cancelled:
                window.setProperty("visible", True)
            else:
                app.quit()
    backend.changed.connect(done)
    code = app.exec()
    del engine
    return code
