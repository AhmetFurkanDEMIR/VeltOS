"""VeltOS Maps window backend.

Google Maps (no Maps Platform key) in one VeltOS window: a second start
brings the open window forward (local socket, with the start's activation
token). Google's pages follow the app's language (Accept-Language and
`hl`). Location is opt-in (kdeglobals [Privacy] LocationServicesEnabled,
shared with Settings > Privacy & security > Location): "My location" asks
GeoClue once; when it finds nothing, the default location the user set
(~/.config/veltos/location.json, as Windows 11's "Default location") is
shown instead. `veltos-maps --set-default-location` (Settings' "Set
default") opens Maps with a bar that saves the map's centre as it.
"""

import configparser
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import strings

QML_DIR = Path(__file__).resolve().parent / "qml"
MAPS_URL = "https://www.google.com/maps"
# GeoClue's answer comes within seconds when a source knows the place (GPS,
# a modem, Wi-Fi through beaconDB); waiting longer only delays the default.
GEOCLUE_TIMEOUT = 15
SET_DEFAULT_ARGUMENT = "--set-default-location"
CENTRE = re.compile(r"/@(-?\d{1,2}(?:\.\d+)?),(-?\d{1,3}(?:\.\d+)?)")


def config_dir():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "veltos"


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path, data):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def map_centre(url):
    """(latitude, longitude) of a Google Maps address with "/@lat,lon,…", or None."""
    match = CENTRE.search(url or "")
    if not match:
        return None
    latitude, longitude = float(match.group(1)), float(match.group(2))
    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
        return latitude, longitude
    return None


def default_location(directory=None):
    """The default location (Settings and Maps share it), or None."""
    data = read_json(Path(directory or config_dir()) / "location.json")
    try:
        latitude, longitude = float(data["latitude"]), float(data["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
        return latitude, longitude
    return None


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
    timeout = threading.Timer(GEOCLUE_TIMEOUT, lambda: (timed_out.set(), cancellable.cancel()))
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
            raise TimeoutError(f"no location within {GEOCLUE_TIMEOUT} seconds") from error
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
    defaultChanged = Signal()
    noteChanged = Signal()
    raiseRequested = Signal()
    locationLookupFinished = Signal(int, float, float, str)

    def __init__(self, lang=None, runner=subprocess.run, start_url=MAPS_URL,
                 location_provider=geoclue_location, set_default=False, settings_dir=None, parent=None):
        super().__init__(parent)
        self.lang = lang or strings.language()
        self._hl = "tr" if self.lang == "tr" else "en"
        self._runner = runner
        self._location_provider = location_provider
        self._settings_dir = Path(settings_dir) if settings_dir else config_dir()
        self._map_url = self._localized(start_url) if start_url == MAPS_URL else start_url
        self._setting_default = bool(set_default)
        self._note_dismissed = bool(read_json(self._settings_dir / "maps.json").get("privacyNoteDismissed"))
        self._location_enabled = False
        self._status = ""
        self._status_kind = ""
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

    @Property(str, constant=True)
    def acceptLanguage(self):
        """Google's pages in the app's language (they followed the network's
        country before: Turkish pages in an English window)."""
        return "tr-TR,tr;q=0.9,en;q=0.5" if self._hl == "tr" else "en-US,en;q=0.9"

    @Property(str, notify=statusChanged)
    def statusKind(self):
        """"info", "progress" or "error": how the message bar looks."""
        return self._status_kind

    @Property(bool, notify=noteChanged)
    def privacyNoteVisible(self):
        return not self._note_dismissed

    @Slot()
    def dismissPrivacyNote(self):
        self._note_dismissed = True
        data = read_json(self._settings_dir / "maps.json")
        data["privacyNoteDismissed"] = True
        write_json(self._settings_dir / "maps.json", data)
        self.noteChanged.emit()

    # --- default location (Windows 11's "Default location") -----------------------------

    @Property(bool, notify=defaultChanged)
    def hasDefaultLocation(self):
        return default_location(self._settings_dir) is not None

    @Property(bool, notify=defaultChanged)
    def settingDefault(self):
        return self._setting_default

    @Slot()
    def startSettingDefault(self):
        self._setting_default = True
        self.defaultChanged.emit()

    @Slot()
    def cancelSettingDefault(self):
        self._setting_default = False
        self.defaultChanged.emit()

    @Slot(str)
    def saveDefaultFromView(self, url):
        """The centre of the map now shown becomes the default location."""
        centre = map_centre(url)
        if centre is None:
            self._set_status(strings.text(self.lang, "default_move_map"), "error")
            return
        latitude, longitude = centre
        if not write_json(self._settings_dir / "location.json",
                          {"latitude": round(latitude, 6), "longitude": round(longitude, 6)}):
            self._set_status(strings.text(self.lang, "default_save_failed"), "error")
            return
        self._setting_default = False
        self.defaultChanged.emit()
        self._set_status(strings.text(self.lang, "default_saved"), "info")

    @Slot()
    def showDefaultLocation(self):
        centre = default_location(self._settings_dir)
        if centre is not None:
            self._show(*centre)

    def _show(self, latitude, longitude):
        self._map_url = self._localized(f"{MAPS_URL}/@{latitude:.6f},{longitude:.6f},16z")
        self.mapUrlChanged.emit()

    def _localized(self, url):
        return url + ("&" if "?" in url else "?") + "hl=" + self._hl

    @Slot()
    def raiseWindow(self):
        self.raiseRequested.emit()

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
        self._map_url = f"{MAPS_URL}/search/?{urlencode({'api': '1', 'query': query, 'hl': self._hl})}"
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
            self._set_status(strings.text(self.lang, "location_disabled"), "error")
            return
        self.cancelLocationRequest()
        self._location_request_id += 1
        request_id = self._location_request_id
        cancel_event = threading.Event()
        self._location_cancel_event = cancel_event
        self._set_status(strings.text(self.lang, "location_progress"), "progress")
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
            centre = default_location(self._settings_dir)
            if centre is not None:
                self._show(*centre)
                self._set_status(strings.text(self.lang, "location_default_shown"), "info")
            else:
                self._set_status(strings.text(self.lang, "location_failed"), "error")
            return
        self._show(latitude, longitude)
        self._set_status(strings.text(self.lang, "location_ready"), "info")

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
        self._set_status(strings.text(self.lang, "location_turned_on" if enabled else "location_turned_off"), "info")
        self.locationChanged.emit()

    @Slot(str)
    def openExternal(self, target):
        try:
            parsed = urlsplit(target)
        except ValueError:
            self._set_status(strings.text(self.lang, "open_failed"), "error")
            return
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            self._set_status(strings.text(self.lang, "open_failed"), "error")
            return
        if not QDesktopServices.openUrl(QUrl(target)):
            self._set_status(strings.text(self.lang, "open_failed"), "error")

    @Slot()
    def openLocationSettings(self):
        try:
            subprocess.Popen(["veltos-settings", "location"], start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except OSError as error:
            self._set_status(strings.text(self.lang, "settings_error", error=str(error)), "error")

    @Slot()
    def clearStatus(self):
        self._set_status("")

    def _set_error(self, detail):
        message = strings.text(self.lang, "location_error", error=detail) if detail else ""
        self._set_status(message, "error" if detail else "")

    def _set_status(self, message, kind=""):
        if (message, kind) != (self._status, self._status_kind):
            self._status, self._status_kind = message, (kind if message else "")
            self.statusChanged.emit()


def socket_name():
    return f"veltos-maps-{os.getuid()}" if hasattr(os, "getuid") else "veltos-maps"


def hand_over(argv):
    """Gives the start to a running Maps window; True when there is one.
    The message carries this start's activation token, so the window may
    come to the front (KWin raises only with a token; AGENTS.md)."""
    socket = QLocalSocket()
    socket.connectToServer(socket_name())
    if not socket.waitForConnected(300):
        return False
    message = {"token": os.environ.get("XDG_ACTIVATION_TOKEN", ""), "setDefault": SET_DEFAULT_ARGUMENT in argv}
    socket.write((json.dumps(message) + "\n").encode())
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def take_message(backend, data):
    try:
        message = json.loads(bytes(data).decode() or "{}")
    except ValueError:
        message = {}
    if message.get("token"):
        os.environ["XDG_ACTIVATION_TOKEN"] = message["token"]
    if message.get("setDefault"):
        backend.startSettingDefault()
    backend.raiseWindow()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    QtWebEngineQuick.initialize()
    app = QGuiApplication(argv)
    if hand_over(argv):
        return 0
    from veltos_controls import use as use_veltos_controls
    use_veltos_controls()
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-maps")
    app.setDesktopFileName("veltos-maps")
    app.setWindowIcon(QIcon.fromTheme("veltos-maps"))
    backend = Backend(set_default=SET_DEFAULT_ARGUMENT in argv)
    app.aboutToQuit.connect(backend.cancelLocationRequest)
    server = QLocalServer()
    QLocalServer.removeServer(socket_name())
    server.listen(socket_name())

    def on_connection():
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            connection.readyRead.connect(lambda c=connection: take_message(backend, c.readAll()))
    server.newConnection.connect(on_connection)
    app.setApplicationDisplayName(backend.appTitle)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
