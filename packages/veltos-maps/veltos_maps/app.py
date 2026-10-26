"""VeltOS Maps window backend."""

import configparser
import os
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import strings

QML_DIR = Path(__file__).resolve().parent / "qml"
MAPS_URL = "https://www.google.com/maps"


def geoclue_location(cancel_event):
    """Wait for one GeoClue fix, with cancellation and a bounded timeout."""
    import gi

    gi.require_version("Geoclue", "2.0")
    from gi.repository import Gio, Geoclue, GLib

    cancellable = Gio.Cancellable()
    timed_out = threading.Event()
    finished = threading.Event()

    def cancel_if_requested():
        while not finished.wait(0.1):
            if cancel_event.is_set():
                cancellable.cancel()
                return

    cancellation_watcher = threading.Thread(target=cancel_if_requested, daemon=True)
    timeout = threading.Timer(25, lambda: (timed_out.set(), cancellable.cancel()))
    cancellation_watcher.start()
    timeout.start()
    try:
        simple = Geoclue.Simple.new_sync("veltos-maps", Geoclue.AccuracyLevel.EXACT, cancellable)
        location = simple.get_location()
        if location is None:
            raise RuntimeError("GeoClue returned no location")
        return float(location.get_latitude()), float(location.get_longitude())
    except GLib.Error as error:
        if cancel_event.is_set():
            return None
        if timed_out.is_set():
            raise TimeoutError("GeoClue did not return a location within 25 seconds") from error
        raise RuntimeError(str(error)) from error
    finally:
        finished.set()
        timeout.cancel()


def trusted_google_url(value):
    """Only keep secure Google-owned pages in the embedded map view."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "google.com" or host.endswith(".google.com"))


def settings_value(filename, group, key, default=""):
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (home / filename, home / "kdedefaults" / filename, Path("/etc/xdg") / filename):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return default


class Backend(QObject):
    mapUrlChanged = Signal()
    locationChanged = Signal()
    statusChanged = Signal()
    locationLookupFinished = Signal(int, float, float, str)

    def __init__(self, lang=None, runner=subprocess.run, start_url=MAPS_URL,
                 location_provider=geoclue_location, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._runner = runner
        self._location_provider = location_provider
        self._map_url = start_url
        self._location_enabled = False
        self._status = ""
        self._location_request_id = 0
        self._location_cancel_event = None
        self._location_worker = None
        self.locationLookupFinished.connect(self._finish_location_request)
        config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config").expanduser()
        self._config_path = config_home / "kdeglobals"
        self._config_watcher = QFileSystemWatcher(self)
        if config_home.is_dir():
            self._config_watcher.addPath(str(config_home))
        if self._config_path.is_file():
            self._config_watcher.addPath(str(self._config_path))
        self._config_watcher.fileChanged.connect(self._queue_location_refresh)
        self._config_watcher.directoryChanged.connect(self._queue_location_refresh)
        self._config_refresh_timer = QTimer(self)
        self._config_refresh_timer.setSingleShot(True)
        self._config_refresh_timer.setInterval(100)
        self._config_refresh_timer.timeout.connect(self._refresh_location_after_config_change)
        self.refreshLocation()

    @Property(str, constant=True)
    def appTitle(self):
        return strings.text(self.lang, "app_title")

    @Property(bool, constant=True)
    def darkMode(self):
        return settings_value("kdeglobals", "KDE", "LookAndFeelPackage").endswith(".dark")

    @Property(str, constant=True)
    def accent(self):
        parts = [part for part in settings_value("kdeglobals", "General", "AccentColor").split(",")
                 if part.strip().isdigit()]
        return "#%02x%02x%02x" % tuple(int(part) for part in parts[:3]) if len(parts) >= 3 else ""

    @Property(float, constant=True)
    def textScale(self):
        parts = settings_value("kdeglobals", "General", "font").split(",")
        try:
            return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
        except ValueError:
            return 1.0

    @Property(str, notify=mapUrlChanged)
    def mapUrl(self):
        return self._map_url

    @Property(bool, notify=locationChanged)
    def locationEnabled(self):
        return self._location_enabled

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot()
    def refreshLocation(self):
        was_enabled = self._location_enabled
        try:
            result = self._runner(
                ["kreadconfig6", "--file", "kdeglobals", "--group", "Privacy",
                 "--key", "LocationServicesEnabled", "--default", "false"],
                check=False, capture_output=True, text=True)
        except OSError as error:
            self._location_enabled = False
            self._set_error(str(error))
            if was_enabled:
                self.cancelLocationRequest()
            self.locationChanged.emit()
            return
        if result.returncode:
            self._location_enabled = False
            self._set_error(result.stderr.strip() or "kreadconfig6 failed")
        else:
            self._location_enabled = result.stdout.strip().lower() in ("true", "1", "yes", "on")
            self._set_error("")
        if was_enabled and not self._location_enabled:
            self.cancelLocationRequest()
        self.locationChanged.emit()

    @Slot(str)
    def _queue_location_refresh(self, _path):
        self._config_refresh_timer.start()

    @Slot()
    def _refresh_location_after_config_change(self):
        if self._config_path.is_file() and str(self._config_path) not in self._config_watcher.files():
            self._config_watcher.addPath(str(self._config_path))
        self.refreshLocation()

    @Slot(str)
    def search(self, query):
        query = query.strip()
        if not query:
            return
        self._map_url = f"{MAPS_URL}/search/?{urlencode({'api': '1', 'query': query})}"
        self.mapUrlChanged.emit()

    @Slot(str, result=bool)
    def isGoogleMapsUrl(self, value):
        return trusted_google_url(value)

    @Slot(str, result=bool)
    def canShareLocation(self, origin):
        return self._location_enabled and trusted_google_url(origin)

    @Slot()
    def requestCurrentLocation(self):
        if not self._location_enabled:
            self._set_status(strings.text(self.lang, "location_disabled"))
            return
        self.cancelLocationRequest()
        self._location_request_id += 1
        request_id = self._location_request_id
        cancel_event = threading.Event()
        self._location_cancel_event = cancel_event
        self._set_status(strings.text(self.lang, "location_progress"))
        self._location_worker = threading.Thread(
            target=self._request_location, args=(request_id, cancel_event), daemon=True)
        self._location_worker.start()

    def _request_location(self, request_id, cancel_event):
        try:
            coordinates = self._location_provider(cancel_event)
            if coordinates is None:
                return
            latitude, longitude = (float(value) for value in coordinates)
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("GeoClue returned coordinates outside the valid range")
            self.locationLookupFinished.emit(request_id, latitude, longitude, "")
        except Exception as error:
            self.locationLookupFinished.emit(request_id, 0.0, 0.0, str(error))

    @Slot(int, float, float, str)
    def _finish_location_request(self, request_id, latitude, longitude, error):
        if request_id != self._location_request_id or not self._location_enabled:
            return
        self._location_cancel_event = None
        if error:
            self._set_status(strings.text(self.lang, "location_failed", error=error))
            return
        self._map_url = f"{MAPS_URL}/@{latitude:.6f},{longitude:.6f},16z"
        self.mapUrlChanged.emit()
        self._set_status(strings.text(self.lang, "location_ready"))

    @Slot()
    def cancelLocationRequest(self):
        self._location_request_id += 1
        if self._location_cancel_event is not None:
            self._location_cancel_event.set()
            self._location_cancel_event = None

    @Slot(bool)
    def setLocationEnabled(self, enabled):
        try:
            result = self._runner(
                ["kwriteconfig6", "--notify", "--file", "kdeglobals", "--group", "Privacy",
                 "--type", "bool", "--key", "LocationServicesEnabled", "true" if enabled else "false"],
                check=False, capture_output=True, text=True)
        except OSError as error:
            self._set_error(str(error))
            return
        if result.returncode:
            self._set_error(result.stderr.strip() or "kwriteconfig6 failed")
            return
        self._location_enabled = bool(enabled)
        if not self._location_enabled:
            self.cancelLocationRequest()
        self._set_error("")
        self.locationChanged.emit()

    @Slot(str)
    def openExternal(self, target):
        try:
            parsed = urlsplit(target)
        except ValueError:
            self._set_status(strings.text(self.lang, "open_failed"))
            return
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            self._set_status(strings.text(self.lang, "open_failed"))
            return
        if not QDesktopServices.openUrl(QUrl(target)):
            self._set_status(strings.text(self.lang, "open_failed"))

    @Slot()
    def openLocationSettings(self):
        try:
            subprocess.Popen(["veltos-settings", "location"], start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except OSError as error:
            self._set_status(strings.text(self.lang, "settings_error", error=str(error)))

    def _set_error(self, detail):
        message = strings.text(self.lang, "location_error", error=detail) if detail else ""
        self._set_status(message)

    def _set_status(self, message):
        if message != self._status:
            self._status = message
            self.statusChanged.emit()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    QtWebEngineQuick.initialize()
    app = QGuiApplication(argv)
    from veltos_controls import use as use_veltos_controls
    use_veltos_controls()
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-maps")
    app.setDesktopFileName("veltos-maps")
    app.setWindowIcon(QIcon.fromTheme("veltos-maps"))
    backend = Backend()
    app.aboutToQuit.connect(backend.cancelLocationRequest)
    app.setApplicationDisplayName(backend.appTitle)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
