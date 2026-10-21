"""VeltOS Snipping Tool: Windows 11's Snipping Tool on VeltOS.

    veltos-snip                 the app window (New, mode, delay, markup)
    veltos-snip --snip          Print Screen / Windows + Shift + S: dim the
                                screen, pick a rectangle, window, full
                                screen or freeform shape
    veltos-snip --full-screen   Windows + Print Screen: the whole screen at once
    veltos-snip FILE            open a picture for markup

A snip is copied to the clipboard and saved in Pictures/Screenshots, and a
notification offers to mark it up, like Windows. See capture.py for how
the screen is captured.
"""

import configparser
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import (QCoreApplication, QEventLoop, QObject, QProcess, QSettings, QTimer, QUrl,
                            Property, Signal, Slot, SLOT, ClassInfo)
from PySide6.QtGui import QGuiApplication, QIcon, QImage
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import capture, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
MODES = ("rect", "window", "full", "free")
DELAYS = (0, 3, 5, 10)
# Time for the app window to disappear before the screen is captured.
HIDE_MS = 450
WINDOWS_TIMEOUT_MS = 1500
TOAST_MS = 6000
LINGER_S = 20
TOAST_WAIT_MS = 60000
DBUS_SERVICE = "org.veltos.SnippingTool"
DBUS_PATH = "/SnippingTool"
DBUS_INTERFACE = "org.veltos.SnippingTool"


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
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def detached(command):
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def gvariant_string(text):
    return "'" + str(text).replace("\\", "\\\\").replace("'", "\\'") + "'"


def toast_command(texts, image_path):
    """gdbus call that shows the "Snip copied to clipboard" notification.
    (gdbus reads the method's argument types from D-Bus introspection;
    PySide6 cannot send the unsigned replaces_id itself.)"""
    hints = "{'desktop-entry': <'veltos-snip'>"
    if image_path:
        hints += ", 'image-path': <" + gvariant_string(QUrl.fromLocalFile(str(image_path)).toString()) + ">"
    hints += "}"
    return ["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
            "--object-path", "/org/freedesktop/Notifications",
            "--method", "org.freedesktop.Notifications.Notify",
            gvariant_string(texts["app_title"]), "0", gvariant_string("veltos-snip"),
            gvariant_string(texts["toast_title"]), gvariant_string(texts["toast_body"]),
            "['default', " + gvariant_string(texts["toast_action"]) + "]", hints, str(TOAST_MS)]


def toast_id(gdbus_output):
    """The notification number from gdbus' reply "(uint32 42,)"."""
    match = re.search(r"uint32 (\d+)", gdbus_output or "")
    return int(match.group(1)) if match else None


class Settings:
    """Mode, delay and auto-save, kept between runs (~/.config/veltos-snip.conf)."""

    def __init__(self, store=None):
        self.store = store or QSettings("veltos-snip", "veltos-snip")

    def get(self, key, default):
        value = self.store.value(key, default)
        if isinstance(default, bool):
            return value in (True, "true", "1", 1)
        if isinstance(default, int):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        return str(value)

    def set(self, key, value):
        self.store.setValue(key, value)
        self.store.sync()


# --- Capture: frozen screen, selection, crop --------------------------------------------

@ClassInfo({"D-Bus Interface": DBUS_INTERFACE})
class WindowReceiver(QObject):
    """Receives the window list from the KWin script (see capture.py)."""
    received = Signal(str)

    @Slot(str)
    def setWindows(self, data):  # noqa: N802 (D-Bus method name)
        self.received.emit(data)


def query_windows(timeout_ms=WINDOWS_TIMEOUT_MS):
    """Frames of the current desktop's windows from KWin, bottom to top;
    [] if KWin does not answer (Window mode then works like Rectangle)."""
    try:
        from PySide6.QtDBus import QDBusConnection, QDBusInterface
    except ImportError:
        return []
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        return []
    receiver = WindowReceiver()
    service = f"{DBUS_SERVICE}.p{os.getpid()}"
    if not bus.registerObject(DBUS_PATH, receiver, QDBusConnection.RegisterOption.ExportAllSlots) \
            or not bus.registerService(service):
        return []
    result = []
    loop = QEventLoop()
    receiver.received.connect(lambda data: (result.extend(capture.parse_windows(data)), loop.quit()))
    plugin = f"veltos-snip-{os.getpid()}"
    script = Path(tempfile.mkdtemp(prefix="veltos-snip-")) / "windows.js"
    script.write_text(capture.window_script(service, DBUS_PATH, DBUS_INTERFACE), encoding="utf-8")
    scripting = QDBusInterface("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", bus)
    reply = scripting.call("loadScript", str(script), plugin)
    arguments = reply.arguments()
    if arguments and isinstance(arguments[0], int) and arguments[0] >= 0:
        QDBusInterface("org.kde.KWin", f"/Scripting/Script{arguments[0]}", "org.kde.kwin.Script", bus).call("run")
        QTimer.singleShot(timeout_ms, loop.quit)
        loop.exec()
    scripting.call("unloadScript", plugin)
    bus.unregisterService(service)
    bus.unregisterObject(DBUS_PATH)
    return result


class Snipper(QObject):
    """Shows the frozen screen (Overlay.qml, one window per screen) and turns
    the user's choice into a picture: `finished(QImage)` or `cancelled`."""
    changed = Signal()
    finished = Signal(QImage)
    cancelled = Signal()
    failed = Signal()

    def __init__(self, texts, mode="rect", capture_image=None, windows=None, overlay=True, parent=None):
        super().__init__(parent)
        self._texts = texts
        self._overlay = overlay              # False: the whole screen at once
        self._mode = mode if mode in MODES else "rect"
        self._dark = dark_mode()
        self._accent = accent()
        self._image = capture_image          # tests pass a picture instead of capturing
        self._windows = windows
        self._hovered = -1
        self._screen_urls = []
        self._origin = (0, 0)
        self._scale = 1.0
        self._engine = None
        self._process = None
        self._tmp = Path(tempfile.mkdtemp(prefix="veltos-snip-"))

    # Properties for Overlay.qml
    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(float, constant=True)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(str, constant=True)
    def accent(self):
        return self._accent

    @Property(str, notify=changed)
    def mode(self):
        return self._mode

    @Property("QVariantList", notify=changed)
    def windows(self):
        return list(self._windows or [])

    @Slot(str)
    def setMode(self, mode):
        if mode in MODES and mode != self._mode:
            self._mode = mode
            self.changed.emit()
        if mode == "full":
            self.captureFull()

    @Slot(int, result=str)
    def screenImage(self, index):
        return self._screen_urls[index] if 0 <= index < len(self._screen_urls) else ""

    @Slot(float, float, result=int)
    def windowAt(self, x, y):
        return capture.window_at(self._windows or [], x, y)

    # Flow
    def start(self):
        if self._windows is None:
            self._windows = query_windows() if self._overlay else []
        if self._image is not None:
            self._show()
            return
        path = self._tmp / "screen.png"
        self._process = QProcess(self)
        self._process.finished.connect(lambda code, _status: self._captured(path, code))
        self._process.errorOccurred.connect(
            lambda error: self._captured(path, 127) if error == QProcess.ProcessError.FailedToStart else None)
        command = capture.capture_command(path)
        self._process.start(command[0], command[1:])

    def _captured(self, path, code):
        image = QImage(str(path)) if code == 0 else QImage()
        if image.isNull():
            self.failed.emit()
            return
        self._image = image
        self._show()

    def _show(self):
        if not self._overlay:
            self.captureFull()
            return
        screens = QGuiApplication.screens()
        left = min(s.geometry().x() for s in screens)
        top = min(s.geometry().y() for s in screens)
        right = max(s.geometry().x() + s.geometry().width() for s in screens)
        self._origin = (left, top)
        self._scale = self._image.width() / max(1, right - left)
        self._screen_urls = []
        for index, screen in enumerate(screens):
            g = screen.geometry()
            part = capture.crop(self._image, (g.x() - left) * self._scale, (g.y() - top) * self._scale,
                                g.width() * self._scale, g.height() * self._scale) or QImage()
            file = self._tmp / f"screen-{index}.png"
            part.save(str(file))
            self._screen_urls.append(QUrl.fromLocalFile(str(file)).toString())
        self._engine = QQmlApplicationEngine()
        self._engine.rootContext().setContextProperty("backend", self)
        self._engine.load(QUrl.fromLocalFile(str(QML_DIR / "Overlay.qml")))
        if not self._engine.rootObjects():
            self.failed.emit()

    def _close(self):
        if self._engine is not None:
            for root in self._engine.rootObjects():
                root.setProperty("active", False)
            self._engine.deleteLater()
            self._engine = None

    def _pixels(self, x, y):
        return (x - self._origin[0]) * self._scale, (y - self._origin[1]) * self._scale

    def _done(self, image):
        self._close()
        if image is None or image.isNull():
            self.cancelled.emit()
        else:
            self.finished.emit(image)

    @Slot(float, float, float, float)
    def captureRect(self, x, y, width, height):  # noqa: N802
        left, top = self._pixels(x, y)
        self._done(capture.crop(self._image, left, top, width * self._scale, height * self._scale))

    @Slot(int)
    def captureWindow(self, index):  # noqa: N802
        windows = self._windows or []
        if 0 <= index < len(windows):
            w = windows[index]
            self.captureRect(w["x"], w["y"], w["width"], w["height"])

    @Slot()
    def captureFull(self):  # noqa: N802
        self._done(self._image.copy())

    @Slot("QVariantList")
    def captureFree(self, points):  # noqa: N802
        pixels = []
        for i in range(0, len(points) - 1, 2):
            pixels.extend(self._pixels(float(points[i]), float(points[i + 1])))
        self._done(capture.freeform(self._image, pixels))

    @Slot()
    def cancel(self):
        self._done(None)


# --- Snip done: clipboard, file, notification ----------------------------------------

class Delivery(QObject):
    """Copies a snip to the clipboard, saves it and shows the notification;
    `markUp` when the user selects the notification."""
    markUp = Signal()
    finishedChanged = Signal()

    def __init__(self, texts, auto_save=True, start=detached, notify=True):
        super().__init__()
        self.texts = texts
        self.auto_save = auto_save
        self.start = start
        self.notify = notify
        self.path = None
        self.toast_id = None
        self.toast_open = False

    def deliver(self, image, now=None):
        QGuiApplication.clipboard().setImage(image)
        now = now or datetime.datetime.now()
        if self.auto_save:
            folder = capture.screenshots_dir()
            folder.mkdir(parents=True, exist_ok=True)
            self.path = capture.unique_path(folder, now)
        else:
            self.path = Path(tempfile.mkdtemp(prefix="veltos-snip-")) / now.strftime(capture.NAME_FORMAT + ".png")
        image.save(str(self.path))
        if self.notify:
            self._toast()
        return self.path

    def _toast(self):
        self._watch()
        try:
            out = subprocess.run(toast_command(self.texts, self.path), capture_output=True, text=True,
                                 timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            return
        self.toast_id = toast_id(out)
        self.toast_open = self.toast_id is not None

    def _watch(self):
        try:
            from PySide6.QtDBus import QDBusConnection
        except ImportError:
            return
        bus = QDBusConnection.sessionBus()
        for name, slot in (("ActionInvoked", "onActionInvoked(QDBusMessage)"),
                           ("NotificationClosed", "onNotificationClosed(QDBusMessage)")):
            bus.connect("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                        "org.freedesktop.Notifications", name, self, SLOT(slot))

    def _ours(self, message):
        arguments = message.arguments()
        return bool(arguments) and self.toast_id is not None and int(arguments[0]) == self.toast_id

    @Slot("QDBusMessage")
    def onActionInvoked(self, message):  # noqa: N802
        if self._ours(message):
            self.toast_open = False
            self.markUp.emit()
            self.finishedChanged.emit()

    @Slot("QDBusMessage")
    def onNotificationClosed(self, message):  # noqa: N802
        if self._ours(message):
            self.toast_open = False
            self.finishedChanged.emit()


# --- The app window ------------------------------------------------------------------

class Editor(QObject):
    """Backend of Main.qml: New snip, mode, delay, markup, save and copy."""
    changed = Signal()
    hideRequested = Signal()
    showRequested = Signal()

    def __init__(self, lang=None, settings=None, start=detached, snipper_factory=None):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._settings = settings or Settings()
        self._start = start
        self._snipper_factory = snipper_factory or (lambda mode: Snipper(self._texts, mode))
        self._snipper = None
        self._image = QImage()
        self._image_url = ""
        self._counter = 0
        self._message = ""
        self._saved = ""
        self._dark = dark_mode()
        self._accent = accent()
        self._tmp = Path(tempfile.mkdtemp(prefix="veltos-snip-"))

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(float, constant=True)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, constant=True)
    def darkMode(self):
        return self._dark

    @Property(str, constant=True)
    def accent(self):
        return self._accent

    @Property(bool, notify=changed)
    def hasImage(self):
        return not self._image.isNull()

    @Property(str, notify=changed)
    def imageUrl(self):
        return self._image_url

    @Property(int, notify=changed)
    def imageWidth(self):
        return self._image.width()

    @Property(int, notify=changed)
    def imageHeight(self):
        return self._image.height()

    @Property(str, notify=changed)
    def mode(self):
        return self._settings.get("mode", "rect")

    @Property(int, notify=changed)
    def delay(self):
        return self._settings.get("delay", 0)

    @Property(bool, notify=changed)
    def autoSave(self):
        return self._settings.get("autoSave", True)

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property(bool, notify=changed)
    def canShowSaved(self):
        return bool(self._saved)

    @Slot(str)
    def setMode(self, mode):
        if mode in MODES:
            self._settings.set("mode", mode)
            self.changed.emit()

    @Slot(int)
    def setDelay(self, seconds):
        if seconds in DELAYS:
            self._settings.set("delay", seconds)
            self.changed.emit()

    @Slot(bool)
    def setAutoSave(self, on):
        self._settings.set("autoSave", bool(on))
        self.changed.emit()

    def set_image(self, image):
        self._image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self._counter += 1
        path = self._tmp / f"snip-{self._counter}.png"
        self._image.save(str(path))
        self._image_url = QUrl.fromLocalFile(str(path)).toString()
        self._message = ""
        self._saved = ""
        self.changed.emit()

    @Slot(str, result=bool)
    def openFile(self, path):  # noqa: N802
        image = QImage(path)
        if image.isNull():
            return False
        self.set_image(image)
        return True

    # New snip from the window: hide it, wait the delay, snip, show the result.
    @Slot()
    def newSnip(self):  # noqa: N802
        self.hideRequested.emit()
        QTimer.singleShot(HIDE_MS + 1000 * self.delay, self._snip)

    def _snip(self):
        self._snipper = self._snipper_factory(self.mode)
        self._snipper.finished.connect(self._snipped)
        self._snipper.cancelled.connect(self.showRequested)
        self._snipper.failed.connect(self._snip_failed)
        self._snipper.start()

    def _snipped(self, image):
        self.set_image(image)
        QGuiApplication.clipboard().setImage(self._image)
        if self.autoSave:
            self._save_image(self._image)
        self.showRequested.emit()

    def _snip_failed(self):
        self._message = self._texts["capture_failed"]
        self.changed.emit()
        self.showRequested.emit()

    # Markup: the strokes live in QML and come here as JSON.
    def _composed(self, strokes_json):
        try:
            strokes = json.loads(strokes_json or "[]")
        except ValueError:
            strokes = []
        return capture.compose(self._image, strokes)

    def _save_image(self, image):
        folder = capture.screenshots_dir()
        folder.mkdir(parents=True, exist_ok=True)
        path = capture.unique_path(folder, datetime.datetime.now())
        image.save(str(path))
        self._saved = str(path)
        self._message = self._texts["saved"]
        self.changed.emit()
        return path

    @Slot(str)
    def save(self, strokes_json):
        if self.hasImage:
            self._save_image(self._composed(strokes_json))

    @Slot(str)
    def copy(self, strokes_json):
        if self.hasImage:
            QGuiApplication.clipboard().setImage(self._composed(strokes_json))
            self._message = self._texts["copied"]
            self._saved = ""
            self.changed.emit()

    @Slot(float, float, float, float, str)
    def applyCrop(self, x, y, width, height, strokes_json):  # noqa: N802
        if not self.hasImage:
            return
        part = capture.crop(self._composed(strokes_json), x, y, width, height)
        if part is not None:
            self.set_image(part)

    @Slot(str, float, float, float, result=str)
    def eraseAt(self, strokes_json, x, y, radius):  # noqa: N802
        """The strokes that the eraser at x, y does not touch (JSON)."""
        try:
            strokes = json.loads(strokes_json or "[]")
        except ValueError:
            return "[]"
        return json.dumps([s for s in strokes if not capture.stroke_hit(s, x, y, radius)])

    @Slot()
    def showInFolder(self):  # noqa: N802
        if self._saved:
            self._start(["veltos-explorer", self._saved])

    @Slot()
    def dismissMessage(self):  # noqa: N802
        self._message = ""
        self.changed.emit()


# --- Entry points ----------------------------------------------------------------------

def overlay_lock():
    """One screen overlay at a time (Print Screen pressed twice)."""
    name = f"veltos-snip-overlay-{os.getuid()}"
    probe = QLocalSocket()
    probe.connectToServer(name)
    if probe.waitForConnected(300):
        return None
    server = QLocalServer()
    QLocalServer.removeServer(name)
    server.listen(name)
    return server


def open_editor(editor, image=None):
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", editor)
    if image is not None:
        editor.set_image(image)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    return engine


def run_snip(app, full_screen=False):
    """Print Screen: snip, deliver, then wait for the notification."""
    lock = overlay_lock()
    if lock is None:
        return 0
    settings = Settings()
    texts = strings.texts(strings.language())
    delivery = Delivery(texts, auto_save=settings.get("autoSave", True))
    snipper = Snipper(texts, settings.get("mode", "rect"), overlay=not full_screen)
    state = {"engine": None, "editor": None, "delivered": False}

    def maybe_quit():
        if state["delivered"] and state["engine"] is None and not delivery.toast_open:
            # On Wayland the program that copied serves the clipboard. Plasma's
            # clipboard (Klipper, images kept: /etc/xdg/klipperrc) takes the
            # snip over when this program ends; wait a little while it is
            # still ours so Klipper surely has it.
            waited = datetime.datetime.now() - state["delivered_at"]
            if QGuiApplication.clipboard().ownsClipboard() and waited < datetime.timedelta(seconds=LINGER_S):
                return
            app.quit()

    def mark_up():
        editor = Editor()
        state["editor"] = editor
        engine = open_editor(editor, QImage(str(delivery.path)))
        state["engine"] = engine
        root = engine.rootObjects()[0] if engine.rootObjects() else None
        if root is not None:
            root.destroyed.connect(lambda: (state.update(engine=None), maybe_quit()))
            root.closing.connect(lambda _close: (state.update(engine=None), QTimer.singleShot(0, maybe_quit)))

    def finished(image):
        lock.close()
        delivery.deliver(image)
        state["delivered"] = True
        state["delivered_at"] = datetime.datetime.now()
        if not delivery.toast_open:
            maybe_quit()
        # The notification may stay in the notification centre; stop
        # waiting for it after a minute.
        QTimer.singleShot(TOAST_WAIT_MS, lambda: (setattr(delivery, "toast_open", False), maybe_quit()))

    def give_up():
        lock.close()
        app.quit()

    delivery.markUp.connect(mark_up)
    delivery.finishedChanged.connect(maybe_quit)
    QGuiApplication.clipboard().dataChanged.connect(lambda: QTimer.singleShot(0, maybe_quit))
    # Also look now and then: Wayland tells a program without windows late
    # that another one took the clipboard.
    poll = QTimer()
    poll.setInterval(2000)
    poll.timeout.connect(maybe_quit)
    poll.start()
    snipper.finished.connect(finished)
    snipper.cancelled.connect(give_up)
    snipper.failed.connect(give_up)
    snipper.start()
    return app.exec()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-snip")
    app.setDesktopFileName("veltos-snip")
    app.setWindowIcon(QIcon.fromTheme("veltos-snip"))
    app.setQuitOnLastWindowClosed(False)
    texts = strings.texts(strings.language())
    app.setApplicationDisplayName(texts["app_title"])
    args = argv[1:]
    if "--snip" in args or "--full-screen" in args:
        code = run_snip(app, full_screen="--full-screen" in args)
    else:
        editor = Editor()
        files = [a for a in args if not a.startswith("--")]
        if files:
            editor.openFile(files[0])
        engine = open_editor(editor)
        if not engine.rootObjects():
            return 1
        # Quit when the window is closed, not when it hides for a new snip
        # or the overlay windows go away.
        engine.rootObjects()[0].closing.connect(lambda _close: QTimer.singleShot(0, app.quit))
        code = app.exec()
    # Qt deletes the clipboard data after Python has shut down: leave at once
    # (see AGENTS.md, PySide6 clipboard).
    sys.stdout.flush()
    os._exit(code)
