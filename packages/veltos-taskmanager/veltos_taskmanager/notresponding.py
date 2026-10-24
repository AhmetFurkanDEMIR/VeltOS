"""The Windows 11 "is not responding" window (VeltOS Task Manager).

When a window does not answer and the user closes it, KWin runs its helper
kwin_killer_helper with the program's pid, window title and desktop name.
veltos-taskmanager diverts that helper to bin/veltos-not-responding, which
shows this window in the look of Windows 11 (product owner, 2026-10-23)
instead of KDE's message box: "<App> is not responding", "Close the
program" and "Wait for the program to respond". Closing ends the program
as KWin's helper does (SIGABRT so the crash handler can record it, then
SIGKILL); programs of other users or on other hosts are left to KDE's
helper (kwin_killer_helper.kde), which can ask for permission.
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon, QWindow
from PySide6.QtQml import QQmlApplicationEngine

from . import app as taskmanager
from . import strings, system

QML = Path(__file__).resolve().parent / "qml" / "NotResponding.qml"
KDE_HELPER = "/usr/lib/x86_64-linux-gnu/libexec/kwin_killer_helper.kde"


def parse(argv):
    """KWin's options for its helper (src/helpers/killer/killer.cpp)."""
    parser = argparse.ArgumentParser(add_help=False)
    for name in ("pid", "hostname", "windowname", "applicationname", "wid", "timestamp"):
        parser.add_argument(f"--{name}", default="")
    args, _ = parser.parse_known_args(argv)
    return args


def desktop_entry(desktop_name, dirs=None):
    for directory in (dirs or system.APPLICATION_DIRS):
        entry = system.read_desktop(Path(directory) / f"{desktop_name}.desktop")
        if entry:
            return entry
    return {}


def app_info(desktop_name, lang="en", dirs=None):
    """Name and icon of the program from its desktop file (KWin passes the
    desktop file's name, e.g. "org.kde.kwrite")."""
    entry = desktop_entry(desktop_name, dirs)
    if not entry:
        return desktop_name, "application-x-executable"
    return (system.localized(entry, "Name", lang) or desktop_name,
            entry.get("Icon", "application-x-executable"))


def short_caption(caption, name):
    """The window title without the program's name, as KWin's helper does
    ("Untitled — Notepad" with the program "Notepad" gives "Untitled")."""
    for separator in (" — ", " – ", " - "):
        caption = caption.replace(separator + name, "")
    return caption


def alive(pid, proc=Path("/proc")):
    """Whether the process still runs (a zombie has ended)."""
    try:
        stat = (proc / str(pid) / "stat").read_text()
    except OSError:
        return False
    return stat.rsplit(")", 1)[-1].split()[:1] != ["Z"]


def note_for_drkonqi(pid, cache=None, proc=Path("/proc"), now=time.time):
    """As KWin's helper: an empty file that tells DrKonqi the program was
    ended because it did not respond
    (~/.cache/drkonqi/application-not-responding/EXE.BOOTID.PID.MSECS.json)."""
    try:
        exe = Path(os.readlink(proc / str(pid) / "exe")).name.split(" ")[0]
        boot = (proc / "sys/kernel/random/boot_id").read_text().strip().replace("-", "")
    except OSError:
        return None
    home = Path(cache or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    folder = home / "drkonqi" / "application-not-responding"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{exe}.{boot}.{pid}.{int(now() * 1000)}.json"
        path.touch(exist_ok=False)
    except OSError:
        return None
    return path


def end_program(pid, kill=os.kill, is_alive=alive, sleep=time.sleep, note=note_for_drkonqi):
    """End the program as KWin's helper does: SIGABRT first, so its crash
    handler (DrKonqi, coredumpd) can record the hang, then SIGKILL after 4 s.
    Returns False when the process belongs to someone else."""
    note(pid)
    try:
        kill(pid, signal.SIGABRT)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    for _ in range(16):
        if not is_alive(pid):
            return True
        sleep(0.25)
    try:
        kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        return False
    return True


class Backend(QObject):
    changed = Signal()

    def __init__(self, pid, caption, desktop_name, lang=None, dirs=None, end=end_program):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self.pid = pid
        self._end = end
        self.result = None          # "closed", "denied" or "wait"
        name, icon = app_info(desktop_name, self.lang, dirs)
        self._name, self._icon = name, icon
        # The title may carry the program's name in either language.
        window = caption
        for known in (name, desktop_entry(desktop_name, dirs).get("Name", ""), desktop_name):
            if known:
                window = short_caption(window, known)
        if window and window != name:
            self._heading = self._texts["nr_title_window"].format(app=name, window=window)
        else:
            self._heading = self._texts["nr_title"].format(app=name)
        self._dark = taskmanager.dark_mode()
        self._accent = taskmanager.accent()
        self._scale = taskmanager.text_scale()

    @Slot(str, result=str)
    def text(self, key):
        return self._texts.get(key, key)

    @Property(str, constant=True)
    def appName(self):
        return self._name

    @Property(str, constant=True)
    def appIcon(self):
        return self._icon

    @Property(str, constant=True)
    def heading(self):
        return self._heading

    # Read by Theme.qml.
    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(str, constant=True)
    def accent(self):
        return self._accent

    @Property(float, constant=True)
    def textScale(self):
        return self._scale

    @Slot()
    def closeProgram(self):
        self.result = "closed" if self._end(self.pid) else "denied"
        QGuiApplication.quit()

    @Slot()
    def wait(self):
        # Also called when the window closes (quit closes it too).
        if self.result is None:
            self.result = "wait"
        QGuiApplication.quit()


def kde_helper(argv):
    os.execv(KDE_HELPER, [KDE_HELPER, *argv])


def main(argv=None, run_kde_helper=kde_helper):
    argv = sys.argv[1:] if argv is None else argv
    args = parse(argv)
    try:
        pid = int(args.pid)
    except ValueError:
        pid = 0
    # Programs on other hosts, or calls this window cannot answer: KDE's
    # helper (its own checks and messages).
    if pid <= 0 or args.hostname != "localhost" or not args.applicationname:
        return run_kde_helper(argv)

    app = QGuiApplication(sys.argv[:1])
    # The program's own icon in the title bar and on the taskbar (Wayland
    # takes it from the desktop file).
    app.setDesktopFileName(args.applicationname)
    backend = Backend(pid, args.windowname, args.applicationname)
    app.setApplicationDisplayName(backend.appName)
    app.setWindowIcon(QIcon.fromTheme(backend.appIcon))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML)))
    if not engine.rootObjects():
        return run_kde_helper(argv)
    window = engine.rootObjects()[0]
    # On X11 (safe graphics) the window belongs to the program's window.
    if app.platformName() == "xcb" and args.wid.isdigit():
        parent = QWindow.fromWinId(int(args.wid))
        if parent is not None:
            window.setTransientParent(parent)
    window.requestActivate()
    app.exec()
    if backend.result == "denied":
        return run_kde_helper(argv)
    return 0
