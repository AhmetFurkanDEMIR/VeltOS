"""VeltOS Automatic Repair: the full-screen window of the recovery start.

Shown by veltos-recovery.service when GRUB starts the recovery entry (two
VeltOS starts in a row did not finish, or the user chose it). Runs as root
on the first console with Qt's linuxfb platform: no compositor, no GPU
driver needed (the recovery entry starts Linux with nomodeset).
"""

import os
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from . import repair, strings

QML = Path(__file__).resolve().parent / "qml" / "Main.qml"
# The package's own copy of the logo: the repair start must not depend on
# the desktop's icons, which may be what is broken.
LOGO = "/usr/share/veltos-recovery/veltos-logo.svg"
# Exit status that asks run-recovery for a sign-in on a text console
# (Command Prompt); the window starts again afterwards, on "Choose an
# option" (--options).
TERMINAL_EXIT = 3
# Shown on that console above the sign-in prompt (the service's
# RuntimeDirectory).
TERMINAL_HINT = "/run/veltos-recovery/terminal-hint"


class Backend(QObject):
    stepChanged = Signal(int, str, str)      # index, "running" / "ok" / "failed", output
    repairFinished = Signal(bool)
    busyChanged = Signal()
    terminalChanged = Signal()

    def __init__(self, lang=None, runner=subprocess.run, threaded=True, quit=None):
        super().__init__()
        self.lang = lang or repair.system_language()
        self._runner = runner
        self._threaded = threaded
        self._quit = quit or QGuiApplication.exit
        self._busy = False
        self._terminal = False

    def _start(self, target):
        if self._threaded:
            threading.Thread(target=target, daemon=True).start()
        else:
            target()

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Property(str, constant=True)
    def logo(self):
        return QUrl.fromLocalFile(LOGO).toString()

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    def _set_busy(self, busy):
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    @Property(bool, notify=terminalChanged)
    def terminalOpen(self):
        return self._terminal

    @Property("QVariantList", constant=True)
    def steps(self):
        return [self.text(key) for key, _command in repair.STEPS]

    @Slot()
    def restart(self):
        self._set_busy(True)
        self._start(lambda: repair.restart(self._runner))

    @Slot()
    def safeMode(self):
        self._set_busy(True)
        self._start(lambda: repair.safe_mode(self._runner))

    @Slot()
    def powerOff(self):
        self._set_busy(True)
        self._start(lambda: repair.power_off(self._runner))

    @Slot()
    def startRepair(self):
        if self._busy:
            return
        self._set_busy(True)

        def work():
            all_ok = True
            for index, (key, _command) in enumerate(repair.STEPS):
                self.stepChanged.emit(index, "running", "")
                ok, freed, output = repair.run_step(index, self._runner)
                if key == "step_space":
                    output = "\n".join(filter(None, [self.text("space_freed" if freed else "space_ok"), output]))
                all_ok = all_ok and ok
                self.stepChanged.emit(index, "ok" if ok else "failed", output)
            self._set_busy(False)
            self.repairFinished.emit(all_ok)
        self._start(work)

    @Slot(result=str)
    def problems(self):
        return repair.previous_problems(self._runner)

    @Slot()
    def openTerminal(self):
        """A sign-in on a text console (Command Prompt). The window ends
        for it: while Qt draws, its console is in graphics mode, and Linux
        ignores every switch to another console then ("Ignore all switches
        in KD_GRAPHICS+VT_AUTO mode", vt_ioctl.c) — a terminal opened next
        to the window never appeared and the screen waited for it for ever
        (VM, 2026-10-22). Qt gives the console back when it ends;
        run-recovery then opens the sign-in and afterwards this window
        again."""
        if self._terminal:
            return
        self._terminal = True
        self.terminalChanged.emit()
        try:
            with open(TERMINAL_HINT, "w", encoding="utf-8") as hint:
                hint.write(self.text("terminal_hint") + "\n\n")
        except OSError:
            pass
        self._quit(TERMINAL_EXIT)


def main(argv=None):
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
    app = QGuiApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("veltos-recovery")
    backend = Backend()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML)))
    if not engine.rootObjects():
        return 1
    code = app.exec()
    # The QML goes first: deleted after the backend, its bindings read a
    # dead backend ("Cannot call method 'text' of null" in the journal each
    # time the window closed for Command Prompt).
    del engine
    return code
