"""MSI laptops in VeltOS Keyboard Lighting: Debian 13's kernel lights no MSI
keyboard (its msi-ec only sets the battery charge limits), so on an MSI
laptop without a keyboard light the app offers MSI's own msi-ec driver
(veltos-msi-ec, built on the PC with DKMS) and walks through it:

  1. pkexec /usr/libexec/veltos/msi-ec-firmware (no password: it only reads)
     says which EC firmware the laptop has and whether msi-ec lights its
     keyboard; nothing is offered when it does not;
  2. "Install": pkcon brings dkms and the kernel headers from Debian
     (through ptyrun, so PackageKit asks for the administrator's password
     in VeltOS' prompt), after a refresh of the package lists when they
     are old;
  3. pkexec /usr/libexec/veltos/msi-ec-driver install builds and loads it;
  4. with Secure Boot, DKMS's key is enrolled for the next start (mokutil,
     a one-time password as for NVIDIA's driver) and the PC restarts.

States (`state`): "" (nothing to show), "checking", "offer", "unsupported",
"busy", "key", "restart", "failed", "done".
"""

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QProcessEnvironment, Signal, Slot

FIRMWARE_HELPER = "/usr/libexec/veltos/msi-ec-firmware"
DRIVER_HELPER = "/usr/libexec/veltos/msi-ec-driver"
MOK_KEY = "/var/lib/dkms/mok.pub"
PACKAGES = ("dkms", "linux-headers-amd64")
REBOOT = ["dbus-send", "--session", "--type=method_call", "--dest=org.kde.Shutdown", "/Shutdown",
          "org.kde.Shutdown.logoutAndReboot"]


def available():
    """veltos-msi-ec is installed (Keyboard Lighting only recommends it)."""
    return Path(FIRMWARE_HELPER).exists() and Path(DRIVER_HELPER).exists()


def is_msi(dmi=Path("/sys/class/dmi/id")):
    try:
        return "micro-star" in (dmi / "sys_vendor").read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return False


def lists_need_refresh(lists_dir="/var/lib/apt/lists", max_age_days=1):
    """apt's package lists are missing (VeltOS' image leaves them out) or old."""
    import glob
    import time
    files = glob.glob(os.path.join(lists_dir, "*_Packages")) + glob.glob(os.path.join(lists_dir, "*_Packages.*"))
    return not files or time.time() - max(os.path.getmtime(f) for f in files) > max_age_days * 86400


def last_json(text):
    for line in reversed(text.strip().splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return {}


class MsiSetup(QObject):
    changed = Signal()
    finished = Signal(bool)          # True: the keyboard light is there now

    def __init__(self, texts, parent=None, kernel=None, needs_refresh=lists_need_refresh, start=None):
        super().__init__(parent)
        self.t = texts
        self._kernel = kernel or os.uname().release
        self._needs_refresh = needs_refresh
        self._start = start or (lambda command: QProcess.startDetached(command[0], command[1:]))
        self._state, self._text, self._detail, self._percent = "", "", "", -1
        self._key_message = ""
        self._info = {}
        self._steps = []
        self._process = None
        self._output = ""

    # --- what QML shows ---------------------------------------------------------------------

    @Property(str, notify=changed)
    def state(self):
        return self._state

    @Property(str, notify=changed)
    def text(self):
        return self._text

    @Property(str, notify=changed)
    def detail(self):
        return self._detail

    @Property(int, notify=changed)
    def percent(self):
        return self._percent

    @Property(str, notify=changed)
    def keyMessage(self):
        return self._key_message

    def _set(self, state, text="", detail=""):
        self._state, self._text, self._detail = state, text, detail
        self.changed.emit()

    # --- 1: which MSI laptop -------------------------------------------------------------------

    @Slot()
    def check(self):
        if self._process is not None or not available() or not is_msi():
            return
        self._set("checking", self.t["msi_checking"])
        self._run("pkexec", [FIRMWARE_HELPER], self._checked)

    def apply_status(self, info):
        """What the firmware helper said (also from the tests)."""
        self._info = info if isinstance(info, dict) else {}
        support = self._info.get("support") or {}
        model = self._info.get("model") or "MSI"
        fw = self._info.get("firmware") or ""
        if not self._info.get("msi"):
            return self._set("")
        if self._info.get("light"):
            return self._set("done")
        if fw and not (support.get("known") and support.get("keyboard")):
            # msi-ec does not know this firmware, or knows it without a
            # keyboard light (newer RGB models): nothing to install.
            reason = "msi_no_light" if support.get("known") else "msi_unknown"
            return self._set("unsupported", self.t[reason].replace("{model}", model),
                             self.t["msi_firmware"].replace("{firmware}", fw))
        text = self.t["msi_offer"].replace("{model}", model)
        detail = (self.t["msi_firmware"].replace("{firmware}", fw) + " · " + support.get("models", "")).strip(" ·") \
            if fw else self.t["msi_firmware_unread"]
        self._set("offer", text, detail)

    def _checked(self, code, output):
        self.apply_status(last_json(output) if code == 0 else {"msi": True})

    # --- 2, 3: install ----------------------------------------------------------------------

    @Slot()
    def install(self):
        if self._process is not None or self._state not in ("offer", "failed"):
            return
        names = [f"{p}:amd64" for p in (*PACKAGES, f"linux-headers-{self._kernel}")]
        self._steps = ([("refresh", ["-p", "refresh"])] if self._needs_refresh() else []) + \
                      [("packages", ["-p", "install", *names]), ("driver", [])]
        self._next()

    def _next(self):
        if not self._steps:
            return
        step, arguments = self._steps.pop(0)
        self._percent = -1
        if step == "driver":
            self._set("busy", self.t["msi_building"])
            self._run("pkexec", [DRIVER_HELPER, "install"], self._built)
        else:
            self._set("busy", self.t["msi_downloading"])
            self._run(sys.executable, ["-m", "veltos_lighting.ptyrun", "pkcon", *arguments], self._packages)

    def _packages(self, code, output):
        # pkcon exits 5 when there was nothing to do (already installed).
        if code in (0, 5):
            return self._next()
        self._steps = []
        lower = output.lower()
        if "authoriz" in lower or "authentic" in lower:
            reason = self.t["msi_failed_auth"]
        elif any(w in lower for w in ("download", "network", "resolve", "fetch", "connect")):
            reason = self.t["msi_failed_network"]
        else:
            reason = self.t["msi_failed_packages"]
        self._set("failed", reason, output.strip().splitlines()[-1] if output.strip() else "")

    def _built(self, code, output):
        result = last_json(output)
        reason = result.get("reason", "load" if code else "")
        if code == 0 and reason == "":
            self._set("done", self.t["msi_done"])
            self.finished.emit(True)
        elif reason == "key":
            self._set("key", self.t["msi_key"])
        elif reason in ("unsupported", "nolight"):
            self._set("unsupported", self.t["msi_no_light"].replace("{model}", self._info.get("model") or "MSI"))
        else:
            lines = [line for line in output.strip().splitlines() if line.strip()]
            self._set("failed", self.t["msi_failed_build"], lines[-2] if len(lines) > 1 else "")

    # --- 4: Secure Boot ---------------------------------------------------------------------

    @Slot(str, str)
    def registerKey(self, password, confirm):
        """mokutil --import reads the one-time password twice from its input;
        pkexec asks for the administrator's password first."""
        if not password or password != confirm:
            self._key_message = self.t["msi_key_mismatch"]
            return self.changed.emit()

        def registered(code, output):
            if code == 0:
                self._key_message = ""
                self._set("restart", self.t["msi_restart"])
            else:
                self._key_message = self.t["msi_key_failed"]
                self.changed.emit()
        self._run("pkexec", ["mokutil", "--import", MOK_KEY], registered, f"{password}\n{password}\n")

    @Slot()
    def restart(self):
        self._start(REBOOT)

    # --- processes --------------------------------------------------------------------------

    def _run(self, program, arguments, done, stdin=None):
        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C")
        environment.insert("LANGUAGE", "C")
        # ptyrun comes from the same place as this module (tests run from the source tree).
        here = str(Path(__file__).resolve().parent.parent)
        environment.insert("PYTHONPATH", here + (":" + environment.value("PYTHONPATH")
                                                 if environment.contains("PYTHONPATH") else ""))
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._output = ""

        def read():
            data = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            self._output += data
            for line in data.splitlines():
                if line.startswith("Percentage:"):
                    try:
                        self._percent = min(100, int(line.split(":", 1)[1].strip()))
                        self.changed.emit()
                    except ValueError:
                        pass

        def ended(code=1, status=QProcess.ExitStatus.CrashExit):
            if self._process is not process:
                return
            self._process = None
            process.deleteLater()
            done(code if status == QProcess.ExitStatus.NormalExit else 1, self._output)

        process.readyReadStandardOutput.connect(read)
        process.finished.connect(ended)
        process.errorOccurred.connect(lambda error: error == QProcess.ProcessError.FailedToStart and ended())
        self._process = process
        process.start(program, arguments)
        if stdin:
            process.write(stdin.encode())
        process.closeWriteChannel()
