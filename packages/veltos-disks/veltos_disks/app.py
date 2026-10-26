"""VeltOS Disk Management: Windows 11's Disk Management (the volume list
over the disk map) on UDisks2. PySide6 + QML. disks.py reads the disks
and builds the UDisks2 calls; this module shows them and runs the calls
(busctl, in a thread so the window stays alive; UDisks2 asks for the
administrator's password through polkit, the VeltOS prompt)."""

import argparse
import configparser
import os
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import disks, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
# The window re-reads the disks this often (a USB stick plugged in); only
# while it is open.
POLL_SECONDS = 5
ROLE_PARTS = {"efi": "part_efi", "recovery": "part_recovery", "reserved": "part_reserved",
              "bios_boot": "part_bios", "swap": "part_swap", "logical": "part_logical",
              "optical": "part_optical", "data": "part_data"}


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
    """Settings > Accessibility > Text size (the KDE font size over its
    default of 10 pt), as every VeltOS app follows it."""
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


def run_command(command, timeout=3600):
    """(exit code, stdout, stderr) of a busctl call; formatting a large
    volume without the quick option takes long."""
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as error:
        return 1, "", str(error)
    return proc.returncode, proc.stdout, proc.stderr


def detached(command):
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def parse_args(argv):
    parser = argparse.ArgumentParser(prog=Path(argv[0]).name)
    parser.add_argument("--format", dest="format_device", metavar="DEVICE",
                        help="open the Format dialog for a volume such as /dev/sdb1")
    args = parser.parse_args(argv[1:])
    if args.format_device and not args.format_device.startswith("/dev/"):
        parser.error("--format requires a device path under /dev")
    return args


class Backend(QObject):
    changed = Signal()
    busyChanged = Signal()
    message = Signal(str)                       # an error, shown in a dialog
    _finished = Signal(str, int, str, str)      # action, exit code, stdout, stderr (from the worker)

    def __init__(self, lang=None, reader=disks.read_objects, runner=run_command, start=detached,
                 formats=None, threaded=True, statvfs=os.statvfs, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._reader = reader
        self._runner = runner
        self._start = start
        self._threaded = threaded
        self._statvfs = statvfs
        self._formats = formats if formats is not None else disks.available_formats()
        self._disks, self._volumes, self._error = [], [], ""
        self._busy = ""
        self._after = None          # what to do with a successful reply (open a mount point)
        self._dark = dark_mode()
        self._accent = accent()
        self._finished.connect(self._done)
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_SECONDS * 1000)
        self._timer.timeout.connect(self.refresh)
        self.refresh()

    def start(self):
        self._timer.start()

    # --- reading ------------------------------------------------------------------

    def t(self, key, **values):
        text = self._texts[key]
        return text.format(**values) if values else text

    @Slot()
    def refresh(self):
        if self._busy:
            return
        try:
            objects = self._reader()
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
            self._disks, self._volumes = [], []
            self._error = self.t("udisks_error", error=disks.error_text(str(error)) or str(error))
        else:
            raw = disks.build(objects, self._statvfs)
            self._disks = [self._disk_view(disk) for disk in raw]
            self._volumes = [segment for disk in self._disks for segment in disk["segments"]
                             if segment["kind"] == "volume"]
            self._error = ""
        self.changed.emit()

    def _disk_view(self, disk):
        view = dict(disk)
        number = disk["number"]
        view["title"] = self.t("cdrom_n" if disk["kind"] == "cdrom" else "disk_n", number=number)
        if disk["kind"] == "cdrom":
            view["kindText"] = self.t("dvd")
            view["statusText"] = self.t("online") if disk["media"] else self.t("no_media")
        else:
            view["kindText"] = self.t("removable") if disk["removable"] else self.t("basic")
            if disk["table"] is None and not any(s["kind"] == "volume" for s in disk["segments"]):
                view["statusText"] = self.t("not_initialized")
            elif disk["readOnly"]:
                view["statusText"] = self.t("read_only")
            else:
                view["statusText"] = self.t("online")
        view["sizeText"] = disks.size_text(disk["size"], self.lang)
        view["segments"] = [self._segment_view(segment, disk) for segment in disk["segments"]]
        return view

    def _segment_view(self, segment, disk):
        view = dict(segment)
        view["sizeText"] = disks.size_text(segment["size"], self.lang)
        view["diskTitle"] = self.t("cdrom_n" if disk["kind"] == "cdrom" else "disk_n", number=disk["number"])
        view["diskModel"] = disk["model"]
        view["drive"] = disk["drive"]
        view["table"] = disk["table"] or ""
        if segment["kind"] == "unallocated":
            view.update(title=self.t("unallocated"), fsText="", statusText="", mounted=False, name="")
            return view
        if segment["kind"] == "free":
            view.update(title=self.t("free"), fsText="", statusText="", mounted=False, name="")
            return view
        mounted = bool(segment["mounts"])
        parts = []
        if segment["role"] in ROLE_PARTS:
            parts.append(self.t(ROLE_PARTS[segment["role"]]))
        if "/" in segment["mounts"] or any(m.startswith("/run/live") for m in segment["mounts"]):
            parts.append(self.t("part_system"))
        if "/boot" in segment["mounts"]:
            parts.append(self.t("part_boot"))
        if segment["readOnly"] and segment["role"] != "optical":
            parts.append(self.t("part_readonly"))
        if not parts and segment["role"] == "primary":
            parts.append(self.t("part_primary"))
        if segment["label"]:
            name = segment["label"]
        elif "/" in segment["mounts"]:
            name = self.t("local_disk")
        elif segment["role"] == "efi":
            name = ""
        else:
            name = self.t("partition_of", disk=disk["number"], number=segment["number"] or 1)
        free = segment["free"]
        view.update(
            title=name, name=name, mounted=mounted,
            fsText=segment["fs"] if segment["hasFilesystem"] or segment["fs"] else self.t("raw"),
            statusText=self.t("healthy_with", parts=", ".join(parts)) if parts else self.t("healthy"),
            layoutText=self.t("simple"), typeText=self.t("basic"),
            freeText=disks.size_text(free, self.lang) if free is not None else "",
            usedText=disks.size_text(segment["size"] - free, self.lang) if free is not None else "",
            percentFree=f"{round(100 * free / segment['size'])} %" if free is not None and segment["size"] else "",
            mountText=segment["mounts"][0] if mounted else self.t("not_mounted"),
            canOpen=segment["hasFilesystem"],
            canMount=segment["hasFilesystem"] and not mounted and not segment["system"],
            canUnmount=segment["hasFilesystem"] and mounted and not segment["system"],
            canEject=segment["removable"] or segment["diskKind"] == "cdrom",
            canLabel=segment["hasFilesystem"] and not segment["system"] and not segment["readOnly"]
                     and segment["diskKind"] != "cdrom",
            canFormat=not segment["system"] and not segment["readOnly"] and segment["diskKind"] != "cdrom"
                      and segment["role"] not in ("efi", "bios_boot", "reserved"),
            canDelete=not segment["system"] and not segment["readOnly"] and segment["diskKind"] != "cdrom"
                      and segment["number"] > 0 and segment["role"] not in ("efi", "bios_boot", "reserved"))
        return view

    # --- properties for QML ----------------------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(float, notify=changed)
    def textScale(self):
        return text_scale()

    @Property(bool, notify=changed)
    def darkMode(self):
        return self._dark

    @Property(str, notify=changed)
    def accent(self):
        return self._accent

    @Property("QVariantList", notify=changed)
    def disks(self):
        return self._disks

    @Property("QVariantList", notify=changed)
    def volumes(self):
        return self._volumes

    @Property("QVariantList", constant=True)
    def formats(self):
        return list(self._formats)

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(bool, notify=busyChanged)
    def busy(self):
        return bool(self._busy)

    @Property(str, notify=busyChanged)
    def busyText(self):
        return self.t("working") if self._busy else ""

    # --- actions -------------------------------------------------------------------

    def find(self, target):
        """The segment dict of an object path (a volume)."""
        for disk in self._disks:
            for segment in disk["segments"]:
                if segment.get("object") == target:
                    return segment
        return None

    def commands_for(self, action, target, options):
        """The busctl calls (in order) of an action, or None when it is
        not allowed; `target` is the volume's or the disk's object path."""
        options = dict(options or {})
        segment = self.find(target)
        if action == "mount":
            return [disks.mount_command(target)] if segment and segment["canMount"] else None
        if action == "unmount":
            return [disks.unmount_command(target)] if segment and segment["canUnmount"] else None
        if action == "open":
            if not segment or not segment["canOpen"]:
                return None
            return [] if segment["mounted"] else [disks.mount_command(target)]
        if action == "eject":
            if not segment or not segment["canEject"]:
                return None
            steps = [disks.unmount_command(target)] if segment["mounted"] else []
            return steps + [disks.eject_command(segment["drive"])]
        if action == "label":
            if not segment or not segment["canLabel"]:
                return None
            return [disks.set_label_command(target, str(options.get("label", "")))]
        if action == "format":
            if not segment or not segment["canFormat"]:
                return None
            fstype = str(options.get("fs", ""))
            if fstype not in self._formats:
                return None
            steps = [disks.unmount_command(target)] if segment["mounted"] else []
            return steps + [disks.format_command(target, fstype, str(options.get("label", "")),
                                                 bool(options.get("quick", True)))]
        if action == "delete":
            if not segment or not segment["canDelete"]:
                return None
            steps = [disks.unmount_command(target)] if segment["mounted"] else []
            return steps + [disks.delete_command(target)]
        if action == "initialize":
            # Only a blank disk, as Windows offers it: a partition table is
            # never written over an existing one from here.
            disk = next((d for d in self._disks if d["object"] == target), None)
            style = str(options.get("style", "gpt"))
            if (not disk or disk["readOnly"] or disk["kind"] == "cdrom" or disk["table"] is not None
                    or any(s["kind"] == "volume" for s in disk["segments"]) or style not in ("gpt", "dos")):
                return None
            return [disks.initialize_command(target, style)]
        if action == "create":
            disk = next((d for d in self._disks if d["object"] == target), None)
            fstype = str(options.get("fs", ""))
            if not disk or not disk["table"] or disk["readOnly"] or fstype not in self._formats:
                return None
            return [disks.create_command(target, disk["table"], int(options.get("offset", 0)),
                                         int(options.get("size", 0)), fstype, str(options.get("label", "")),
                                         bool(options.get("quick", True)))]
        return None

    @Slot(str, str, "QVariantMap", result=bool)
    def act(self, action, target, options):
        """Run an action on a volume or disk; False when it is not allowed
        or something is still running."""
        if self._busy:
            return False
        commands = self.commands_for(action, target, options)
        if commands is None:
            if action in ("format", "delete", "label") and self.find(target) and self.find(target)["system"]:
                self.message.emit(self.t("system_volume"))
            return False
        segment = self.find(target)
        self._after = None
        if action == "open":
            if not commands:
                self._open_folder(segment["mounts"][0])
                return True
            self._after = "open"
        self._busy = action
        self.busyChanged.emit()
        if self._threaded:
            threading.Thread(target=self._work, args=(action, commands), daemon=True).start()
        else:
            self._work(action, commands)
        return True

    def _work(self, action, commands):
        code, out, err = 0, "", ""
        for command in commands:
            code, out, err = self._runner(command)
            if code != 0:
                break
        self._finished.emit(action, code, out, err)

    @Slot(str, int, str, str)
    def _done(self, action, code, out, err):
        self._busy = ""
        self.busyChanged.emit()
        if code != 0:
            self.message.emit(self.t("failed", error=disks.error_text(err) or self.t("unknown")))
        elif self._after == "open":
            point = disks.mount_point_of(out)
            if point:
                self._open_folder(point)
        self._after = None
        self.refresh()

    def _open_folder(self, path):
        self._start(["veltos-explorer", path])


def main(argv=None):
    argv = sys.argv if argv is None else argv
    args = parse_args(argv)
    app = QGuiApplication([argv[0]])
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-disks")
    app.setDesktopFileName("veltos-disks")
    app.setWindowIcon(QIcon.fromTheme("veltos-disks"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("formatDeviceRequest", args.format_device or "")
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    backend.start()
    code = app.exec()
    del engine
    return code
