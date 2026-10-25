"""VeltOS Windows app runner: what happens when a user opens an .exe, .msi,
.bat or .cmd file.

    veltos-run FILE

Flow, like a double click in Windows (no question first): prepare the
Windows environment (first time only) -> run the installer/program at once
-> report the result with "Open" buttons for the shortcuts the installer
created, or a readable error. While it works, the window shows the
program (name, publisher, icon) and says that Windows programs can access
personal files (Wine is not a sandbox).
"""

import configparser
import os
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QProcessEnvironment, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import exeinfo, programs, shortcuts
from .strings import Texts
from .winenv import Environment, alternative_runners, has_hardware_vulkan, live_session

QML_DIR = Path(__file__).resolve().parent / "qml"
# A portable program that is still running after this long is considered
# started; the runner window then gets out of the way.
STARTED_AFTER_MS = 5000


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

def accent_colour():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


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
        # Bottles / Lutris / PlayOnLinux installed: ask which to use first.
        self._alternatives = alternative_runners() if self.info.valid else []
        self._chosen = "wine"
        self._page = ("choose" if self._alternatives else "running") if self.info.valid else "invalid"
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

    @Property("QStringList", notify=changed)
    def details(self):
        """Lines under the title, as in the Windows App Installer."""
        if not self.info.valid:
            return [self.info.path.name]
        if self.info.kind == "batch":
            return [self.t.get("kind_batch")]
        lines = [self.t.get("publisher", publisher=self.info.publisher or self.t.get("unknown_publisher"))]
        if self.info.version:
            lines.append(self.t.get("version", version=self.info.version))
        kind = self.t.get("kind_installer" if self.info.is_installer else "kind_program")
        arch = {"x86": " · 32-bit", "x64": " · 64-bit"}.get(self.info.arch, "")
        lines.append(kind + arch)
        return lines

    @Property(str, constant=True)
    def fallbackIcon(self):
        return "text-x-script" if self.info.kind == "batch" else "application-x-ms-dos-executable"

    @Property(bool, notify=changed)
    def isInstaller(self):
        return self.info.is_installer

    @Property(float, constant=True)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, constant=True)
    def darkMode(self):
        return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")

    @Property(str, constant=True)
    def accent(self):
        return accent_colour()

    @Property("QVariantList", notify=changed)
    def newApps(self):
        return [{"name": a["name"], "path": a["path"]} for a in self._new_apps]

    @Property("QVariantList", constant=True)
    def alternatives(self):
        """The ways to open the file: VeltOS' own Wine environment first,
        then the installed alternatives (choose page)."""
        options = [{"id": "wine", "name": self.t.get("runner_wine"), "icon": "veltos-run",
                    "description": self.t.get("runner_wine_desc")}]
        for alternative in self._alternatives:
            options.append({"id": alternative["id"], "name": alternative["name"], "icon": alternative["icon"],
                            "description": self.t.get("runner_" + alternative["id"] + "_desc")})
        return options

    def _get_chosen(self):
        return self._chosen

    def _set_chosen(self, value):
        if value != self._chosen:
            self._chosen = value
            self.changed.emit()

    chosenRunner = Property(str, _get_chosen, _set_chosen, notify=changed)

    @Slot(str)
    def chooseRunner(self, runner_id):
        """The choice on the choose page: VeltOS runs the file itself; an
        alternative gets the file the way a double-click would give it."""
        self._chosen = runner_id
        if runner_id == "wine":
            self._page = "running"
            self._set_texts()
            self.changed.emit()
            self.start()
            return
        for alternative in self._alternatives:
            if alternative["id"] == runner_id:
                QProcess.startDetached("kioclient", ["exec", alternative["desktop"], str(self.info.path)])
                QGuiApplication.instance().quit()
                return

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
            "choose": ("choose_runner", "choose_runner_body"),
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

    @Slot()
    def start(self):
        """Opening the file starts it at once, as in Windows (after the
        choice, when other runners are installed)."""
        if not self.info.valid or self._page == "choose":
            return
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
        # Windows programs follow the light/dark mode chosen in Settings
        # (the registry value Windows keeps for it), set at every start.
        self._queue = [self.env.theme_command(self.darkMode)]
        self._run_next(on_done=self._run_program)

    def _run_program(self):
        self._started_at = time.monotonic()
        self._start_process(self.env.run_command(self.info.path, self.info.kind), self._program_finished)
        if not self.info.is_installer:
            QTimer.singleShot(STARTED_AFTER_MS, self._hide_if_running)

    def _hide_if_running(self):
        if self._process and self._process.state() != QProcess.NotRunning and self._page == "running":
            QGuiApplication.instance().allWindows()[0].hide()

    def _program_finished(self, code):
        self._exit_code = code
        # A program may have been an uninstaller: Wine leaves its menu
        # entries behind (programs.forget_removed).
        programs.forget_removed(self.env)
        if not self.info.is_installer:
            ran_long = time.monotonic() - self._started_at > STARTED_AFTER_MS / 1000
            if code == 0 or ran_long:
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
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    # Text drawn like KDE programs (FreeType, hinted) instead of Qt Quick's
    # distance-field glyphs, which looked uneven at fractional display
    # scales ("kal dır", "program lar" at 105 %, VM 2026-10-20).
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-run")
    app.setDesktopFileName("veltos-run")
    app.setWindowIcon(QIcon.fromTheme("veltos-logo"))
    if len(argv) < 2:
        print("usage: veltos-run FILE.exe|FILE.msi|FILE.bat|FILE.cmd", file=sys.stderr)
        return 2
    runner = Runner(Path(argv[1]).resolve())
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("runner", runner)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    QTimer.singleShot(0, runner.start)
    code = app.exec()
    # The QML goes first: deleted after the objects it reads, its bindings
    # ran once more against dead ones ("Cannot call method ... of null").
    del engine
    return code
