"""VeltOS Camera: Windows 11's Camera on VeltOS.

The window (qml/Main.qml) shows the camera picture over the whole window
with the controls of Windows 11's Camera: Photo/Video, the shutter and
the last photo on the right, settings and the photo timer on the left.
The camera itself is Qt Multimedia's (QML `Camera`, `ImageCapture`,
`MediaRecorder`; on Linux its FFmpeg backend reads V4L2 cameras). This
module gives the window file names, the save folder, the last capture
and the settings.
"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QUrl, Property, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import files, strings

QML_DIR = Path(__file__).resolve().parent / "qml"
GRIDS = ("none", "thirds", "square", "cross")
TIMERS = (0, 2, 5, 10)


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


class Backend(QObject):
    changed = Signal()
    lastChanged = Signal()

    def __init__(self, lang=None, settings=None, folder=None, opener=None, parent=None):
        super().__init__(parent)
        self._lang = lang or strings.language()
        self._texts = strings.texts(self._lang)
        self._settings = settings if settings is not None else QSettings(
            str(config_home() / "veltos/camera.conf"), QSettings.Format.IniFormat)
        self._folder = Path(folder) if folder else files.camera_roll(self._lang)
        self._open = opener or (lambda url: QDesktopServices.openUrl(url))
        latest = files.latest_capture(self._folder)
        self._last = str(latest) if latest else ""

    def _value(self, key, default, allowed):
        value = self._settings.value(key, default)
        try:
            value = type(default)(value)
        except (TypeError, ValueError):
            return default
        return value if value in allowed else default

    def _save(self, key, value):
        self._settings.setValue(key, value)
        self._settings.sync()
        self.changed.emit()

    # --- properties --------------------------------------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(str, constant=True)
    def folderName(self):
        """"Pictures > Camera Roll" in the user's language, for Settings."""
        return f"{self._folder.parent.name} > {self._folder.name}"

    @Property(str, notify=changed)
    def grid(self):
        return self._value("grid", "none", GRIDS)

    @Property(int, notify=changed)
    def timer(self):
        return self._value("timer", 0, TIMERS)

    @Property(str, notify=changed)
    def mode(self):
        return self._value("mode", "photo", ("photo", "video"))

    @Property(bool, notify=changed)
    def recordAudio(self):
        return str(self._settings.value("audio", "true")).lower() != "false"

    @Property(str, notify=changed)
    def cameraId(self):
        return str(self._settings.value("camera", ""))

    @Property(str, notify=lastChanged)
    def lastCapture(self):
        return self._last

    @Property(str, notify=lastChanged)
    def lastCaptureUrl(self):
        return QUrl.fromLocalFile(self._last).toString() if self._last else ""

    @Property(bool, notify=lastChanged)
    def lastIsVideo(self):
        return bool(self._last) and files.is_video(self._last)

    # --- actions -----------------------------------------------------------------------------

    @Slot(str)
    def setGrid(self, grid):
        if grid in GRIDS:
            self._save("grid", grid)

    @Slot()
    def nextTimer(self):
        self._save("timer", TIMERS[(TIMERS.index(self.timer) + 1) % len(TIMERS)])

    @Slot(str)
    def setMode(self, mode):
        if mode in ("photo", "video"):
            self._save("mode", mode)

    @Slot(bool)
    def setRecordAudio(self, on):
        self._save("audio", "true" if on else "false")

    @Slot(str)
    def setCameraId(self, camera_id):
        self._save("camera", camera_id)

    @Slot(str, result=str)
    def newPhotoPath(self, _unused=""):
        self._folder.mkdir(parents=True, exist_ok=True)
        return str(files.new_path(self._folder, "photo"))

    @Slot(result=str)
    def newVideoUrl(self):
        self._folder.mkdir(parents=True, exist_ok=True)
        return QUrl.fromLocalFile(str(files.new_path(self._folder, "video"))).toString()

    @Slot(str)
    def captured(self, path_or_url):
        """A photo or video was saved (path or file: URL)."""
        url = QUrl(path_or_url)
        path = url.toLocalFile() if url.isLocalFile() else path_or_url
        if path:
            self._last = path
            self.lastChanged.emit()

    @Slot()
    def openLast(self):
        if self._last and Path(self._last).exists():
            self._open(QUrl.fromLocalFile(self._last))

    @Slot()
    def openFolder(self):
        self._folder.mkdir(parents=True, exist_ok=True)
        self._open(QUrl.fromLocalFile(str(self._folder)))


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-camera")
    app.setDesktopFileName("veltos-camera")
    app.setWindowIcon(QIcon.fromTheme("veltos-camera"))
    backend = Backend()
    app.setApplicationDisplayName(backend.texts["app_title"])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    code = app.exec()
    del engine
    return code
