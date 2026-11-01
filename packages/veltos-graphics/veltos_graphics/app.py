"""VeltOS Graphics Cards: the PC's graphics cards with their driver and
properties, and the right driver installed or updated with one button
(product owner, 2026-10-23). PySide6 + QML.

gpus.py reads the cards and drivers.py decides what each needs; the
packages are installed with PackageKit's `pkcon` (the administrator's
password goes through polkit, VeltOS' prompt), as VeltOS Store does."""

import configparser
import glob
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import (Property, QObject, QProcess, QProcessEnvironment, QStandardPaths, QUrl, Signal,
                            Slot)
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import diagnostics, drivers, gpus, strings, themewatch

QML_DIR = Path(__file__).resolve().parent / "qml"
DRIVER_KEYS = {"nvidia": "drv_nvidia", "nouveau": "drv_nouveau", "amdgpu": "drv_amdgpu", "radeon": "drv_radeon",
               "i915": "drv_i915", "xe": "drv_xe"}
REBOOT = ["dbus-send", "--session", "--type=method_call", "--dest=org.kde.Shutdown", "/Shutdown",
          "org.kde.Shutdown.logoutAndReboot"]
# No -y: it makes PackageKit's transaction non-interactive, and polkit then
# refused at once instead of asking for the administrator's password ("The
# driver could not be installed. Administrator permission was not given.",
# product owner, 2026-10-26, a laptop with an RTX 4070). pkcon runs in a
# pseudo terminal that answers its "Proceed with changes?" (ptyrun.py, as
# VeltOS Store does).
PKCON_ARGUMENTS = {"refresh": ["-p", "refresh"], "install": ["-p", "install"],
                   "update": ["-p", "update"], "remove": ["-p", "remove"]}


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


def lists_need_refresh(lists_dir="/var/lib/apt/lists", max_age_days=1):
    """Whether apt's package lists are missing or older than a day: a
    driver installed from old lists may no longer be on the mirror."""
    files = glob.glob(os.path.join(lists_dir, "*_Packages")) + glob.glob(os.path.join(lists_dir, "*_Packages.*"))
    if not files:
        return True
    return time.time() - max(os.path.getmtime(f) for f in files) > max_age_days * 86400


def size_text(size, lang):
    if size >= 1 << 30:
        text = f"{size / (1 << 30):.1f} GB"
    else:
        text = f"{round(size / (1 << 20))} MB"
    return text.replace(".", ",") if lang == "tr" else text


# pkcon's status lines the window words itself (the rest keep the step's text).
STATUS = {"Waiting in queue": "busy_waiting", "Waiting for package manager lock": "busy_waiting",
          "Waiting for authentication": "busy_permission", "Downloading packages": "busy_download",
          "Installing packages": "busy_installing"}


def parse_progress(line):
    """(kind, value) for a line of `pkcon -p` output (as VeltOS Store reads it)."""
    match = re.match(r"^Percentage:\s*(\d+)", line)
    if match:
        return ("percent", min(100, int(match.group(1))))
    match = re.match(r"^Status:\s*(.+?)\s*$", line)
    if match:
        return ("status", STATUS[match.group(1)]) if match.group(1) in STATUS else None
    if line.startswith(("Fatal error:", "Command failed:")):
        return ("error", line.partition(":")[2].strip())
    return None


def boot_card(slot, sysfs=Path("/sys/bus/pci/devices")):
    """Whether the firmware started the PC on this card (the one that draws)."""
    full = slot if slot.count(":") == 2 else f"0000:{slot}"
    try:
        return (sysfs / full / "boot_vga").read_text().strip() == "1"
    except OSError:
        return False


class Backend(QObject):
    cardsChanged = Signal()
    jobChanged = Signal()
    keyChanged = Signal()
    logChanged = Signal()
    lookChanged = Signal()
    logRequested = Signal()
    _collected = Signal(object)

    def __init__(self, lang=None, detect=gpus.detect, installed=drivers.installed_packages,
                 modules=drivers.loaded_modules, recommend=drivers.nvidia_detect, available=drivers.available,
                 renderer=gpus.renderer, vulkan=gpus.vulkan_devices, secure_boot=drivers.secure_boot,
                 key_enrolled=drivers.key_enrolled, memory=gpus.video_memory, version=gpus.driver_version,
                 is_boot=boot_card, start=detached, program="pkcon", needs_refresh=lists_need_refresh,
                 outdated=drivers.outdated, nvidia_packages=drivers.open_driver_packages, arch=None,
                 health=lambda sb: drivers.health(sb), kernel=drivers.running_kernel, report=diagnostics.report,
                 append_log=diagnostics.append, threaded=True):
        super().__init__()
        self._threaded = threaded
        self._loaded = False
        self._collected.connect(self._apply)
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._detect, self._installed, self._modules = detect, installed, modules
        self._recommend, self._available = recommend, available
        self._renderer, self._vulkan = renderer, vulkan
        self._secure_boot, self._key_enrolled = secure_boot, key_enrolled
        self._memory, self._version, self._is_boot = memory, version, is_boot
        self._start, self.program, self._needs_refresh = start, program, needs_refresh
        self._outdated, self._nvidia_packages = outdated, nvidia_packages
        self._arch = arch or drivers.native_arch()
        self._health, self._kernel = health, kernel
        self._report, self._append_log = report, append_log
        self._job_log = []
        self._log_text = ""
        self._log_note = ""
        self._cards = []
        self._raw = {}             # slot -> (card, plan)
        self._busy = ""            # slot of the card being worked on
        self._busy_text = ""
        self._percent = -1
        self._ask_restart = False
        self._restart_after = False
        self._messages = {}        # slot -> (text, ok) after a job
        self._key_message = ""
        self._key_busy = False
        self._steps = []
        self._step = ""
        self._job = ""
        self._error = ""
        self.process = None
        self._scale = text_scale()
        self._look = themewatch.ThemeWatch(lambda: (dark_mode(), accent()), self)
        self._look.changed.connect(self.lookChanged)

    # --- properties for QML ----------------------------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property("QVariantList", notify=cardsChanged)
    def cards(self):
        return self._cards

    @Property(str, notify=jobChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=jobChanged)
    def busyText(self):
        return self._busy_text

    @Property(int, notify=jobChanged)
    def percent(self):
        return self._percent

    @Property(str, notify=keyChanged)
    def keyMessage(self):
        return self._key_message

    # Light/dark and the accent follow the system while the window is open
    # (themewatch.py).
    @Property(bool, notify=lookChanged)
    def darkMode(self):
        return self._look.dark

    @Property(str, notify=lookChanged)
    def accent(self):
        return self._look.accent

    @Property(float, constant=True)
    def textScale(self):
        return self._scale

    @Property(str, notify=logChanged)
    def logText(self):
        return self._log_text

    @Property(str, notify=logChanged)
    def logNote(self):
        return self._log_note

    # --- reading the cards ------------------------------------------------------------------

    def _driver_name(self, card, driver):
        if card["kind"] == "virtual":
            return self._texts["drv_virtual"]
        if not driver:
            return self._texts["no_driver"]
        key = DRIVER_KEYS.get(driver)
        return self._texts[key] if key else driver

    @Property(bool, notify=cardsChanged)
    def loaded(self):
        return self._loaded

    @Property(bool, notify=cardsChanged)
    def keyNeeded(self):
        """NVIDIA's driver is installed, Secure Boot is on and the firmware
        does not know DKMS's key yet: without it the driver does not load
        after the restart."""
        return any(card.get("needsKey") for card in self._cards)

    @Slot()
    def refresh(self):
        """Reads the cards again. lspci, eglinfo, vulkaninfo and apt take a
        second or two together: they run in a thread so the window opens at
        once ("Looking for graphics cards…")."""
        if self._threaded:
            threading.Thread(target=lambda: self._collected.emit(self._collect()), daemon=True).start()
        else:
            self._apply(self._collect())

    def _apply(self, collected):
        self._cards, self._raw = collected
        self._loaded = True
        self.cardsChanged.emit()

    def _collect(self):
        cards = self._detect()
        installed = self._installed()
        modules = self._modules()
        render = self._renderer() if cards else {}
        vulkan = self._vulkan() if cards else []
        sb = self._secure_boot() if any(c["kind"] == "nvidia" for c in cards) else False
        result, raw = [], {}
        for card in cards:
            recommendation = ""
            if card["kind"] == "nvidia" and not any(p in installed for p in drivers.NVIDIA_DRIVERS):
                recommendation = self._recommend()
                if recommendation and recommendation != "unsupported" and not self._available(recommendation):
                    recommendation = "unsupported"
            status = None
            if card["kind"] == "nvidia" and any(p in installed for p in drivers.NVIDIA_DRIVERS):
                status = self._health(sb)
            plan = drivers.plan(card, installed, modules, recommendation, status)
            raw[card["slot"]] = (card, plan)
            state = plan["state"]
            text = self._texts.get("st_" + state + ("_" + plan["reason"] if plan.get("reason") else ""), "")
            if state == "missing":
                text = text.replace("{packages}", ", ".join(plan["packages"]))
            # Only the card the PC draws with gets the renderer's details (one
            # card: that one, even when sysfs does not say).
            draws = len(cards) == 1 or self._is_boot(card["slot"])
            result.append({
                "slot": card["slot"], "kind": card["kind"], "name": card["name"], "vendor": card["vendor"],
                "driverName": self._driver_name(card, plan["driver"]), "state": state, "stateText": text,
                "action": plan["action"], "packages": plan["packages"], "openDriver": plan["openDriver"],
                "reason": plan.get("reason", ""),
                "properties": self._properties(card, plan, render if draws else {}, vulkan if draws else [], sb),
                "needsKey": card["kind"] == "nvidia" and state in ("proprietary", "restart", "failed") and sb
                and not self._key_enrolled(),
                "message": self._messages.get(card["slot"], ("", True))[0],
                "messageOk": self._messages.get(card["slot"], ("", True))[1],
            })
        return result, raw

    def _properties(self, card, plan, render, vulkan, sb):
        t = self._texts
        rows = [(t["p_manufacturer"], card["vendor"]), (t["p_model"], card["name"]),
                (t["p_board"], card["subsystem"]),
                (t["p_pci"], f"{card['vendorId']}:{card['deviceId']}"), (t["p_slot"], card["slot"]),
                (t["p_kernel_driver"], card["driver"]), (t["p_modules"], ", ".join(card["modules"]))]
        if card["driver"]:
            rows.append((t["p_driver_version"], self._version(card["driver"])))
        if plan.get("version"):
            rows.append((t["p_package"], f"{plan['packages'][0]} {plan['version']}"))
        memory = self._memory(card["slot"])
        if memory:
            rows.append((t["p_memory"], size_text(memory, self.lang)))
        for key, field in (("p_renderer", "renderer"), ("p_gl", "glVersion"), ("p_mesa", "mesa")):
            rows.append((t[key], render.get(field, "")))
        rows.append((t["p_vulkan"], ", ".join(vulkan)))
        if card["kind"] == "nvidia":
            rows.append((t["p_secure_boot"], t["on"] if sb else t["off"]))
        return [{"label": label, "value": value} for label, value in rows if value]

    # --- jobs ----------------------------------------------------------------------------------

    @Slot(str)
    def installDriver(self, slot):
        card, plan = self._raw.get(slot, (None, None))
        if not card or plan["action"] != "install" or self._busy:
            return
        steps = [("refresh", [])] if self._needs_refresh() else []
        if card["kind"] == "nvidia":
            # nvidia-detect (non-free) knows which driver series a card needs.
            if "nvidia-detect" not in self._installed():
                steps.append(("install", ["nvidia-detect"]))
            steps.append(("detect", []))
        packages = list(plan["packages"])
        if card["kind"] == "nvidia":
            # DKMS builds for the kernels whose headers are installed: the
            # running kernel's too, in case the PC starts it again.
            headers = drivers.running_headers(self._kernel())
            if headers not in self._installed() and self._available(headers):
                packages.append(headers)
        steps.append(("install", packages))
        self._run(slot, "install", steps)

    @Slot(str)
    def repairDriver(self, slot):
        """NVIDIA's driver has no module for the running kernel: install its
        headers (DKMS then builds the module) and build it again."""
        card, plan = self._raw.get(slot, (None, None))
        if not card or plan["action"] != "repair" or self._busy:
            return
        steps = [("refresh", [])] if self._needs_refresh() else []
        headers = drivers.running_headers(self._kernel())
        if headers not in self._installed():
            steps.append(("install", [headers]))
        steps.append(("dkms", []))
        self._run(slot, "repair", steps)

    @Slot(str)
    def updateDriver(self, slot):
        card, plan = self._raw.get(slot, (None, None))
        if not card or plan["action"] != "update" or self._busy:
            return
        # The lists first, a part the driver lacks, then only the packages
        # that have a newer version.
        missing = list(plan.get("missing", []))
        steps = [("refresh", [])] + ([("install", missing)] if missing else [])
        installed = [p for p in plan["packages"] if p not in missing]
        # KWin uses an added GBM library from the next start on.
        self._run(slot, "update", steps + [("check", installed), ("update", [])], restart=bool(missing))

    @Slot(str)
    def useOpenDriver(self, slot):
        card, plan = self._raw.get(slot, (None, None))
        if not card or not plan["openDriver"] or self._busy:
            return
        packages = self._nvidia_packages()
        if packages:
            self._run(slot, "remove", [("remove", packages)])

    @Slot()
    def restart(self):
        self._ask_restart = False
        self._start(REBOOT)

    @Property(bool, notify=jobChanged)
    def askRestart(self):
        return self._ask_restart

    @Slot()
    def restartLater(self):
        self._ask_restart = False
        self.jobChanged.emit()

    def _run(self, slot, job, steps, restart=False):
        self._busy, self._job, self._steps, self._error = slot, job, steps, ""
        self._restart_after = restart
        self._messages.pop(slot, None)
        self._next()

    def _next(self):
        if not self._steps:
            return self._finish(True)
        action, packages = self._steps.pop(0)
        self._percent = -1
        if action == "detect":
            self._busy_text = self._texts["busy_detect"]
            self.jobChanged.emit()
            recommendation = self._recommend()
            if recommendation == "unsupported" or (recommendation and not self._available(recommendation)):
                self._error = "unsupported"
                self._steps = []
                return self._finish(False)
            if recommendation and self._steps and self._steps[0][0] == "install":
                self._steps[0][1][0] = recommendation
            return self._next()
        if action == "check":
            newer = self._outdated(packages)
            if not newer:
                self._steps = []
                self._job = "current"          # "The driver is up to date."
                return self._finish(True)
            self._steps[0] = ("update", newer)
            return self._next()
        self._busy_text = self._texts["busy_" + action]
        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C")
        environment.insert("LANGUAGE", "C")
        # ptyrun comes from the same place as this module (the tests run
        # from the source tree).
        here = str(Path(__file__).resolve().parent.parent)
        environment.insert("PYTHONPATH", here + (":" + environment.value("PYTHONPATH")
                                                 if environment.contains("PYTHONPATH") else ""))
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._done)
        process.errorOccurred.connect(self._failed_to_start)
        self.process = process
        self._step = action
        # Names with the architecture: VeltOS has i386 too (Wine), and pkcon
        # asks which one is meant when a name has both ("More than one
        # package matches"), waiting for an answer that never comes.
        names = [p if ":" in p else f"{p}:{self._arch}" for p in packages]
        if action == "dkms":
            # pkexec asks for the administrator's password (VeltOS' prompt).
            program, arguments = self.dkms_program, ["dkms", "autoinstall", "-k", self._kernel()]
            shown = [program, *arguments]
        else:
            program = sys.executable
            arguments = ["-m", "veltos_graphics.ptyrun", self.program, *PKCON_ARGUMENTS[action], *names]
            shown = [self.program, *PKCON_ARGUMENTS[action], *names]
        self._job_log.append(f"\n[{diagnostics.stamp()}] {' '.join(shown)}\n")
        process.start(program, arguments)
        process.closeWriteChannel()      # any other question ends instead of waiting
        self.jobChanged.emit()

    def _read(self):
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        self._job_log.append(data)
        for line in data.splitlines():
            parsed = parse_progress(line)
            if parsed and parsed[0] == "percent":
                self._percent = parsed[1]
            elif parsed and parsed[0] == "status":
                # "Installing" of NVIDIA's driver includes building it (DKMS),
                # minutes at 100 %: the text says so, so it does not look stuck.
                key = parsed[1]
                if key == "busy_installing" and self._step != "install":
                    key = "busy_" + self._step
                self._busy_text = self._texts.get(key, self._busy_text)
            elif parsed:
                self._error = parsed[1]
        self.jobChanged.emit()

    def _failed_to_start(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._error = "pkcon"
            self._done(1, QProcess.ExitStatus.CrashExit)

    def _done(self, code, status):
        if self.process is None:
            return
        self._job_log.append(f"\n(exit {code})\n")
        self.process.deleteLater()
        self.process = None
        # pkcon exits 5 when there was nothing to do ("nothing useful was
        # done": the driver is already up to date); not a failure then.
        ok = status == QProcess.ExitStatus.NormalExit and (code == 0 or (code == 5 and self._step != "install"))
        if ok:
            self._next()
        else:
            self._steps = []
            self._finish(False)

    def _finish(self, ok):
        slot, job = self._busy, self._job
        if ok:
            text = self._texts["done_" + job]
        elif self._error == "unsupported":
            text = self._texts["st_unsupported"]
        else:
            error = self._error.lower()
            if "authentication" in error or "not authorized" in error or "authorization" in error:
                detail = self._texts["failed_auth"]
            elif any(w in error for w in ("download", "network", "resolve", "fetch", "connect")):
                detail = self._texts["failed_network"]
            else:
                detail = self._error if self._error not in ("", "pkcon") else ""
            text = self._texts["failed_" + job].replace("{detail}", detail).strip()
        self._busy, self._busy_text, self._percent, self._job, self._step = "", "", -1, "", ""
        self._messages[slot] = (text, ok)
        if ok and (job in ("install", "repair", "remove") or self._restart_after):
            # The new driver starts with the next start: ask (product owner,
            # 2026-11-01: "ask the user to restart").
            self._ask_restart = True
        if self._job_log:
            self._append_log("".join(self._job_log) + f"[{diagnostics.stamp()}] {text}\n")
            self._job_log = []
        self.jobChanged.emit()
        self.refresh()

    # --- the driver log ----------------------------------------------------------------------

    @Slot()
    def openLog(self):
        self._log_text, self._log_note = self._report(), ""
        self.logChanged.emit()
        self.logRequested.emit()

    @Slot()
    def kernelLog(self):
        """Adds the kernel's messages about graphics drivers (journalctl -k
        needs administrator rights: pkexec asks for the password)."""
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        def finished(code, status):
            text = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            process.deleteLater()
            if status == QProcess.ExitStatus.NormalExit and code == 0:
                self._log_text += diagnostics.kernel_messages(text)
                self._log_note = ""
            else:
                self._log_note = self._texts["log_kernel_failed"]
            self.logChanged.emit()

        process.finished.connect(finished)
        process.start(self.kernel_program, ["journalctl", "-k", "-b", "--no-pager", "-o", "short-monotonic"])

    kernel_program = "pkexec"
    dkms_program = "pkexec"

    @Slot()
    def copyLog(self):
        QGuiApplication.clipboard().setText(self._log_text)
        self._log_note = self._texts["log_copied"]
        self.logChanged.emit()

    @Slot()
    def saveLog(self):
        """Saves the log in Documents and opens it (in Notepad)."""
        folder = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
                      or Path.home())
        path = folder / (self._texts["log_file"] + time.strftime(" %Y-%m-%d %H%M") + ".txt")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path.write_text(self._log_text, encoding="utf-8")
        except OSError:
            self._log_note = self._texts["log_save_failed"]
        else:
            self._log_note = self._texts["log_saved"].replace("{path}", str(path))
            if self.open_saved:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        self.logChanged.emit()

    open_saved = True

    # --- Secure Boot ------------------------------------------------------------------------

    @Slot(str, str)
    def registerKey(self, password, confirm, then_restart=False):
        """Asks the firmware to enrol DKMS's key at the next start (mokutil
        --import reads the one-time password twice from its input; pkexec
        asks for the administrator's password first)."""
        if not password or password != confirm:
            self._key_message = self._texts["sb_mismatch"]
            self.keyChanged.emit()
            return
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._key_busy = True
        self.keyChanged.emit()

        def finished(code, status):
            ok = status == QProcess.ExitStatus.NormalExit and code == 0
            self._key_message = self._texts["sb_registered"] if ok else self._texts["sb_failed"]
            self._key_busy = False
            process.deleteLater()
            self.keyChanged.emit()
            if ok and then_restart:
                self.restart()

        process.finished.connect(finished)
        process.start(self.key_program, ["mokutil", "--import", str(drivers.MOK_KEY)])
        process.write(f"{password}\n{password}\n".encode())
        process.closeWriteChannel()

    key_program = "pkexec"

    @Slot(str, str)
    def registerKeyAndRestart(self, password, confirm):
        """Right after installing NVIDIA's driver with Secure Boot on: the
        one-time password for the firmware's key screen, then the restart
        (product owner, 2026-11-02: ask for the Secure Boot password
        directly after the install, then "Restart now", as before)."""
        self.registerKey(password, confirm, True)

    @Property(bool, notify=keyChanged)
    def keyBusy(self):
        return self._key_busy


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-graphics")
    app.setDesktopFileName("veltos-graphics")
    app.setWindowIcon(QIcon.fromTheme("veltos-graphics"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    backend.refresh()
    code = app.exec()
    del engine
    return code
