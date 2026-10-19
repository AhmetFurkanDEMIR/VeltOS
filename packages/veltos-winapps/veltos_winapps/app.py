"""VeltOS Windows app runner: what happens when a user opens an .exe/.msi.

    veltos-run FILE

Flow: confirm (name, publisher, icon) -> prepare the Windows environment
(first time only) -> run the installer/program -> report the result with
"Open" buttons for the shortcuts the installer created, or a readable error.
"""

import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QProcessEnvironment, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import exeinfo, shortcuts
from .strings import Texts
from .winenv import Environment, has_hardware_vulkan, live_session, slugify

QML_DIR = Path(__file__).resolve().parent / "qml"
# A portable program that is still running after this long is considered
# started; the runner window then gets out of the way.
STARTED_AFTER_MS = 5000


class Runner(QObject):
    changed = Signal()

    def __init__(self, path, texts=None):
        super().__init__()
        self.t = texts or Texts()
        self.info = exeinfo.inspect(path)
        self.env = None
        self.log_path = None
        self._log = None
        self._queue = []
        self._process = None
        self._setup = False
        self._before = {}
        self._new_apps = []
        self._page = "confirm" if self.info.valid else "invalid"
        self._title = self._body = ""
        self._exit_code = 0
        self._needed_mb = 0
        self._icon_url = ""
        if self.info.icon_png:
            icon = Path(tempfile.mkdtemp(prefix="veltos-run-")) / "icon.png"
            icon.write_bytes(self.info.icon_png)
            self._icon_url = QUrl.fromLocalFile(str(icon)).toString()
        self._set_texts()

    # --- properties for QML -------------------------------------------------

    @Property(str, notify=changed)
    def page(self):
        return self._page

    @Property(str, notify=changed)
    def title(self):
        return self._title

    @Property(str, notify=changed)
    def body(self):
        return self._body

    @Property(str, notify=changed)
    def iconUrl(self):
        return self._icon_url

    @Property(str, notify=changed)
    def appName(self):
        return self.info.name

    @Property(str, notify=changed)
    def subtitle(self):
        publisher = self.info.publisher or self.t.get("unknown_publisher")
        kind = self.t.get("kind_installer" if self.info.is_installer else "kind_program")
        arch = {"x86": " · 32-bit", "x64": " · 64-bit"}.get(self.info.arch, "")
        return f"{publisher} — {kind}{arch}"

    @Property(bool, notify=changed)
    def isInstaller(self):
        return self.info.is_installer

    @Property("QVariantList", notify=changed)
    def newApps(self):
        return [{"name": a["name"], "path": a["path"]} for a in self._new_apps]

    @Slot(str, result=str)
    def tr(self, key):
        return self.t.get(key, name=self.info.name, code=self._exit_code)

    # --- flow ---------------------------------------------------------------

    def _go(self, page):
        self._page = page
        self._set_texts()
        self.changed.emit()

    def _set_texts(self):
        name = self.info.name
        texts = {
            "invalid": ("not_windows", None),
            "confirm": ("confirm_install", "confirm_install_body") if self.info.is_installer
            else ("confirm_run", "confirm_run_body"),
            "preparing": ("preparing", "preparing_body"),
            "running": ("installing", "installing_body") if self.info.is_installer else ("running", None),
            "waiting": ("waiting", None),
            "done": ("done", "done_body" if self._new_apps else "done_nothing"),
            "failed": ("failed_install" if self.info.is_installer else "failed", "failed_body"),
            "nospace": ("no_space", "no_space_live" if live_session() else "no_space_body"),
        }[self._page]
        values = {"name": name, "code": self._exit_code, "needed": self._needed_mb}
        self._title = self.t.get(texts[0], **values)
        self._body = self.t.get(texts[1], **values) if texts[1] else ""

    @Slot(bool)
    def start(self, add_to_start):
        self._add_to_start = add_to_start
        self.env = Environment()
        ok, needed = self.env.enough_space()
        if not ok:
            # Say so up front instead of letting an installer fail with "disk full".
            self._needed_mb = needed // (1024 * 1024)
            self._go("nospace")
            return
        self.log_path = self.env.new_log()
        self._log = open(self.log_path, "a", encoding="utf-8", errors="replace")
        self._before = shortcuts.snapshot()
        if not self.env.ready:
            self._go("preparing")
            self.env.write_setup_files()
            self._setup = True
            self._queue = self.env.setup_commands(vulkan=has_hardware_vulkan())
            self._run_next(on_done=self._prepared)
        else:
            self._launch()

    def _prepared(self):
        self._setup = False
        self.env.mark_prepared()
        self._launch()

    def _run_next(self, on_done):
        if not self._queue:
            on_done()
            return
        command = self._queue.pop(0)
        self._start_process(command, lambda code: self._run_next(on_done) if code == 0
                            else self._fail(code))

    def _start_process(self, command, finished):
        self._log.write(f"\n$ {' '.join(command)}\n")
        self._log.flush()
        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        variables = self.env.setup_env({}) if self._setup else self.env.env({})
        for key, value in variables.items():
            environment.insert(key, value)
        if self._setup:
            # No display: Wine prepares the environment silently instead of
            # showing its own (Windows 2000 style) progress window. Without
            # DISPLAY, Wine 10 falls back to the default Wayland socket, so
            # point WAYLAND_DISPLAY at a socket that does not exist.
            environment.remove("DISPLAY")
            environment.insert("WAYLAND_DISPLAY", "veltos-no-display")
        process.setProcessEnvironment(environment)
        process.setWorkingDirectory(str(self.info.path.parent))
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(
            lambda: self._log.write(bytes(process.readAllStandardOutput()).decode("utf-8", "replace")))
        process.finished.connect(lambda code, _status: finished(code))
        # finished() is not emitted when the program cannot be started at all.
        process.errorOccurred.connect(
            lambda err: finished(127) if err == QProcess.ProcessError.FailedToStart else None)
        self._process = process
        process.start(command[0], command[1:])

    def _launch(self):
        self._go("running")
        self._started_at = time.monotonic()
        self._start_process(self.env.run_command(self.info.path, self.info.kind), self._program_finished)
        if not self.info.is_installer:
            QTimer.singleShot(STARTED_AFTER_MS, self._hide_if_running)

    def _hide_if_running(self):
        if self._process and self._process.state() != QProcess.NotRunning and self._page == "running":
            if self._add_to_start:
                self._write_launcher()
            QGuiApplication.instance().allWindows()[0].hide()

    def _write_launcher(self):
        shortcuts.write_launcher(slugify(self.info.name), self.info.name,
                                 self.info.path, self.env.prefix, self.info.icon_png)

    def _program_finished(self, code):
        self._exit_code = code
        if not self.info.is_installer:
            ran_long = time.monotonic() - self._started_at > STARTED_AFTER_MS / 1000
            if code == 0 or ran_long:
                if self._add_to_start and not ran_long:
                    self._write_launcher()
                QGuiApplication.instance().quit()
            else:
                self._fail(code)
            return
        # Installers often start helper processes and exit early: wait until
        # everything in the environment has finished before looking for the
        # shortcuts it created.
        self._go("waiting")
        self._start_process(self.env.wait_command(), lambda _code: self._install_finished(code))

    @Slot()
    def finishWaiting(self):
        if self._process and self._process.state() != QProcess.NotRunning:
            self._process.kill()

    def _install_finished(self, code):
        after = shortcuts.snapshot()
        self._new_apps = shortcuts.entries_for_prefix(shortcuts.changed(self._before, after), self.env.prefix)
        if code != 0 and not self._new_apps:
            self._fail(code)
            return
        self.env.save_record(self.info.name, publisher=self.info.publisher,
                             version=self.info.version, installer=str(self.info.path),
                             installed_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                             shortcuts=[a["path"] for a in self._new_apps])
        self._go("done")

    def _fail(self, code):
        self._exit_code = code
        self._go("failed")

    @Slot(int)
    def openApp(self, index):
        entry = self._new_apps[index]
        QProcess.startDetached("kioclient", ["exec", entry["path"]])
        QGuiApplication.instance().quit()

    @Slot()
    def showDetails(self):
        if self.log_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_path)))

    @Slot()
    def cancel(self):
        if self._process and self._process.state() != QProcess.NotRunning:
            self._process.kill()
        QGuiApplication.instance().quit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    # Text drawn like KDE programs (FreeType, hinted) instead of Qt Quick's
    # distance-field glyphs, which looked uneven at fractional display
    # scales ("kal dır", "program lar" at 105 %, VM 2026-10-20).
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-run")
    app.setDesktopFileName("veltos-run")
    app.setWindowIcon(QIcon.fromTheme("veltos-logo"))
    if len(argv) < 2:
        print("usage: veltos-run FILE.exe|FILE.msi", file=sys.stderr)
        return 2
    runner = Runner(Path(argv[1]).resolve())
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("runner", runner)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
