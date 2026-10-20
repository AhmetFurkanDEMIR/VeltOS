"""VeltOS Settings window: Python backend for the QML user interface.

    veltos-settings [PAGE]      (PAGE: home, system, about, storage, ...)
"""

import subprocess
import sys
import threading
import traceback
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import Property, QObject, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import catalog, devices, strings, sysinfo

QML_DIR = Path(__file__).resolve().parent / "qml"
LOOK_AND_FEEL = {False: "org.veltos.light", True: "org.veltos.dark"}
DESKTOP_THEME = {False: "VeltOS", True: "VeltOS-Dark"}
# The global theme writes the Plasma theme into ~/.config/kdedefaults, which
# the running taskbar does not notice: it watches the user's own plasmarc
# file (KDirWatch). kwriteconfig6 does not write a value equal to the
# kdedefaults one, so on a first switch nothing changed and the taskbar
# stayed light (VM test 2026-10-19); the file is therefore edited directly
# ([Theme] name=, other groups kept, same file so the watcher sees it).
APPLY_THEME = r'''plasma-apply-lookandfeel --apply "$1" >/dev/null 2>&1
f="${XDG_CONFIG_HOME:-$HOME/.config}/plasmarc"
touch "$f"
awk -v name="$2" '
    /^\[/ { if (theme && !done) { print "name=" name; done = 1 } theme = ($0 == "[Theme]") }
    theme && /^name=/ { if (!done) { print "name=" name; done = 1 } next }
    { print }
    END { if (!done) { if (!theme) print "[Theme]"; print "name=" name } }
' "$f" > "$f.veltos" && cat "$f.veltos" > "$f"
rm -f "$f.veltos"
'''


def detached(command, env=None):
    """Start a program that outlives Settings (its own session, no output)."""
    subprocess.Popen(command, env=env, start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


def windows_programs():
    """Records of Windows programs installed through veltos-run, if any."""
    try:
        from veltos_winapps.winenv import installed_apps
    except ImportError:
        return []
    apps = []
    for record in installed_apps():
        shortcuts = [s for s in record.get("shortcuts", []) if Path(s).exists()]
        apps.append({
            "name": record.get("name", ""),
            "publisher": record.get("publisher") or "",
            "version": record.get("version") or "",
            "installed": (record.get("installed_at") or "")[:10],
            "shortcut": shortcuts[0] if shortcuts else "",
        })
    return apps


def system_tools(runner=devices.run):
    """The objects that read and change system settings (devices.py)."""
    return SimpleNamespace(network=devices.Network(runner), bluetooth=devices.Bluetooth(runner),
                           sound=devices.Sound(runner), display=devices.Display(runner),
                           personal=devices.Personalization(runner), time=devices.Time(runner))


class Jobs(QObject):
    """Runs slow system commands off the UI thread and hands the result to a
    callback on the UI thread. `threaded=False` runs them at once (tests)."""

    _finished = Signal(object, object)

    def __init__(self, threaded=True):
        super().__init__()
        self.threaded = threaded
        self._finished.connect(self._deliver, Qt.QueuedConnection)

    @staticmethod
    def _call(work):
        try:
            return work()
        except Exception:  # a parsing bug must not take Settings down
            traceback.print_exc()
            return None

    def submit(self, work, done=None):
        if not self.threaded:
            result = self._call(work)
            if done is not None:
                done(result)
            return
        threading.Thread(target=lambda: self._finished.emit(done, self._call(work)),
                         daemon=True).start()

    @Slot(object, object)
    def _deliver(self, done, result):
        if done is not None:
            done(result)


class Backend(QObject):
    changed = Signal()
    networkChanged = Signal()
    bluetoothChanged = Signal()
    soundChanged = Signal()
    displayChanged = Signal()
    personalChanged = Signal()
    timeChanged = Signal()

    def __init__(self, lang=None, start=detached, start_page="home", system=None, threaded=True):
        super().__init__()
        self.lang = lang or strings.language()
        self._start = start
        self._dark = sysinfo.dark_mode()
        self._about = None
        self._storage = None
        self._windows_apps = None
        self._start_page = start_page
        self.system = system or system_tools()
        self.jobs = Jobs(threaded)
        self._network = {"available": False, "enabled": False, "connection": {}, "networks": [],
                         "loaded": False, "scanning": False, "connecting": "", "failed": ""}
        self._bluetooth = {"available": False, "powered": False, "devices": [], "loaded": False,
                           "busy": ""}
        self._sound = {"outputs": [], "inputs": [], "loaded": False}
        self._display = {"outputs": [], "loaded": False}
        self._personal = {"wallpapers": [], "wallpaper": "", "accent": "",
                          "accents": devices.ACCENTS, "loaded": False}
        self._time = {"timezone": "", "automatic": False, "canAutomatic": True, "zones": [],
                      "loaded": False}

    # --- texts and structure ------------------------------------------------

    @Slot(str, result=str)
    def text(self, key):
        return strings.text(self.lang, key)

    @Slot(str, str, result=str)
    def format(self, key, value):
        """Text with one placeholder ({name}, {count}, {date}, ...) filled in."""
        template = strings.text(self.lang, key)
        field = template[template.index("{") + 1:template.index("}")]
        return template.replace("{" + field + "}", value)

    @Property("QVariantList", constant=True)
    def pages(self):
        return catalog.localized_pages(self.lang)

    @Property(str, constant=True)
    def startPage(self):
        return self._start_page

    @Slot(str, result="QVariantList")
    def search(self, query):
        return catalog.search(query, self.lang)

    # --- facts ----------------------------------------------------------------

    @Property("QVariantMap", notify=changed)
    def about(self):
        if self._about is None:
            self._about = sysinfo.about()
        return self._about

    @Property("QVariantList", notify=changed)
    def storage(self):
        if self._storage is None:
            self._storage = sysinfo.storage()
        return self._storage

    @Property("QVariantList", notify=changed)
    def windowsApps(self):
        if self._windows_apps is None:
            self._windows_apps = windows_programs()
        return self._windows_apps

    @Property(str, constant=True)
    def userName(self):
        return sysinfo.user_name()

    @Property(bool, notify=changed)
    def darkMode(self):
        return self._dark

    @Slot()
    def refresh(self):
        self._about = self._storage = self._windows_apps = None
        self._dark = sysinfo.dark_mode()
        self.changed.emit()

    # --- actions --------------------------------------------------------------

    @Slot(bool)
    def setDarkMode(self, dark):
        if dark == self._dark:
            return
        # The global theme switches colours, Plasma theme, window frames and
        # (through the kvantum / kvantum-dark style key) the application style.
        self._start(["sh", "-c", APPLY_THEME, "sh", LOOK_AND_FEEL[dark], DESKTOP_THEME[dark]])
        self._dark = dark
        self.changed.emit()

    @Slot(str)
    def openModule(self, kcm):
        self._start(["kcmshell6", kcm])

    @Slot(str)
    def runAction(self, action):
        if action == "control-panel":
            self._start(["systemsettings"])
        elif action == "store":
            self._start(["veltos-store"])
        elif action == "updates":
            self._start(["veltos-store", "--updates"])
        elif action == "disk-management":
            self._start(["partitionmanager"])
        elif action == "uninstall-windows":
            try:
                from veltos_winapps.winenv import Environment, wine_tool
            except ImportError:
                return
            environment = Environment()
            self._start([wine_tool("wine"), "uninstaller"], env=environment.env())
        else:
            raise ValueError(f"unknown action {action!r}")

    @Slot(str)
    def openWindowsApp(self, shortcut):
        if shortcut:
            self._start(["kioclient", "exec", shortcut])

    @Slot(str, result=bool)
    def renamePc(self, name):
        name = name.strip()
        if not sysinfo.valid_pc_name(name):
            return False
        # hostnamed asks for the administrator password through polkit.
        self._start(["hostnamectl", "set-hostname", name])
        if self._about is not None:
            self._about = dict(self._about, pcName=name)
            self.changed.emit()
        return True

    @Slot(str)
    def copyText(self, value):
        QGuiApplication.clipboard().setText(value)

    # --- built-in pages: shared helpers ---------------------------------------------

    def _update(self, name, signal, values):
        setattr(self, name, dict(getattr(self, name), **values))
        signal.emit()

    def _merge(self, name, signal, extra=None):
        """Callback that merges a state dict (and `extra`) into a property."""
        def done(result):
            self._update(name, signal, dict(result or {}, loaded=True, **(extra or {})))
        return done

    # --- Network & internet > Wi-Fi ------------------------------------------------

    @Property("QVariantMap", notify=networkChanged)
    def network(self):
        return self._network

    @Slot(bool)
    def refreshNetwork(self, rescan):
        self._update("_network", self.networkChanged, {"scanning": True})
        self.jobs.submit(lambda: self.system.network.state(rescan),
                         self._merge("_network", self.networkChanged, {"scanning": False}))

    @Slot(bool)
    def setWifi(self, on):
        values = {"enabled": on}
        if not on:
            values.update(networks=[], connection={})
        self._update("_network", self.networkChanged, values)
        self.jobs.submit(lambda: self.system.network.set_wifi(on),
                         lambda _ok: self.refreshNetwork(on))

    @Slot(str, str, str)
    def connectWifi(self, ssid, password, security):
        self._update("_network", self.networkChanged, {"connecting": ssid, "failed": ""})

        def done(ok):
            self._update("_network", self.networkChanged,
                         {"connecting": "", "failed": "" if ok else ssid})
            self.refreshNetwork(False)
        self.jobs.submit(lambda: self.system.network.connect(ssid, password, security), done)

    @Slot()
    def disconnectWifi(self):
        self.jobs.submit(self.system.network.disconnect, lambda _ok: self.refreshNetwork(False))

    @Slot(str)
    def forgetWifi(self, ssid):
        self.jobs.submit(lambda: self.system.network.forget(ssid),
                         lambda _ok: self.refreshNetwork(False))

    # --- Bluetooth & devices > Bluetooth ---------------------------------------------

    @Property("QVariantMap", notify=bluetoothChanged)
    def bluetooth(self):
        return self._bluetooth

    @Slot()
    def refreshBluetooth(self):
        self.jobs.submit(self.system.bluetooth.state,
                         self._merge("_bluetooth", self.bluetoothChanged))

    @Slot(bool)
    def setBluetooth(self, on):
        self._update("_bluetooth", self.bluetoothChanged, {"powered": on})
        self.jobs.submit(lambda: self.system.bluetooth.set_powered(on),
                         lambda _ok: self.refreshBluetooth())

    @Slot(str, bool)
    def connectBluetooth(self, mac, on):
        self._update("_bluetooth", self.bluetoothChanged, {"busy": mac})

        def done(_ok):
            self._update("_bluetooth", self.bluetoothChanged, {"busy": ""})
            self.refreshBluetooth()
        self.jobs.submit(lambda: self.system.bluetooth.connect(mac, on), done)

    @Slot(str)
    def removeBluetooth(self, mac):
        self.jobs.submit(lambda: self.system.bluetooth.remove(mac),
                         lambda _ok: self.refreshBluetooth())

    @Slot()
    def addBluetoothDevice(self):
        self._start(["bluedevil-wizard"])

    # --- System > Sound ----------------------------------------------------------------

    @Property("QVariantMap", notify=soundChanged)
    def sound(self):
        return self._sound

    @Slot()
    def refreshSound(self):
        self.jobs.submit(self.system.sound.state, self._merge("_sound", self.soundChanged))

    @Slot(str, str)
    def setSoundDevice(self, kind, name):
        self.jobs.submit(lambda: self.system.sound.set_default(kind, name),
                         lambda _ok: self.refreshSound())

    @Slot(str, int)
    def setVolume(self, kind, percent):
        self.jobs.submit(lambda: self.system.sound.set_volume(kind, percent))

    @Slot(str, bool)
    def setMuted(self, kind, muted):
        self.jobs.submit(lambda: self.system.sound.set_muted(kind, muted),
                         lambda _ok: self.refreshSound())

    # --- System > Display ----------------------------------------------------------------

    @Property("QVariantMap", notify=displayChanged)
    def display(self):
        return self._display

    @Slot()
    def refreshDisplay(self):
        self.jobs.submit(self.system.display.state, self._merge("_display", self.displayChanged))

    @Slot(int, float)
    def setScale(self, output_id, scale):
        self.jobs.submit(lambda: self.system.display.set_scale(output_id, scale),
                         lambda _ok: self.refreshDisplay())

    @Slot(int, str)
    def setResolution(self, output_id, mode_id):
        self.jobs.submit(lambda: self.system.display.set_mode(output_id, mode_id),
                         lambda _ok: self.refreshDisplay())

    # --- Personalization > Background, Colours -------------------------------------------

    @Property("QVariantMap", notify=personalChanged)
    def personal(self):
        return self._personal

    @Property(str, notify=personalChanged)
    def accent(self):
        return self._personal.get("accent", "")

    @Slot()
    def refreshPersonal(self):
        personal = self.system.personal
        self.jobs.submit(lambda: {"wallpapers": personal.wallpapers(),
                                  "wallpaper": personal.current_wallpaper(),
                                  "accent": personal.accent()},
                         self._merge("_personal", self.personalChanged))

    @Slot(str)
    def setWallpaper(self, path):
        self._update("_personal", self.personalChanged, {"wallpaper": path})
        self.jobs.submit(lambda: self.system.personal.set_wallpaper(path))

    @Slot()
    def browseWallpaper(self):
        pictures = Path.home() / "Pictures"
        start = pictures if pictures.is_dir() else Path.home()
        title = strings.text(self.lang, "browse_photos")

        def done(path):
            if path:
                self.setWallpaper(path)
        self.jobs.submit(lambda: self.system.personal.pick_image(start, title), done)

    @Slot(str)
    def setAccent(self, color):
        self._update("_personal", self.personalChanged, {"accent": color})
        self.jobs.submit(lambda: self.system.personal.set_accent(color))

    # --- Time & language > Date & time -----------------------------------------------------

    @Property("QVariantMap", notify=timeChanged)
    def time(self):
        return self._time

    @Slot()
    def refreshTime(self):
        self.jobs.submit(self.system.time.state, self._merge("_time", self.timeChanged))

    @Slot(str)
    def setTimezone(self, zone):
        known = [z["value"] for z in self._time["zones"]] or None
        self.jobs.submit(lambda: self.system.time.set_timezone(zone, known),
                         lambda _ok: self.refreshTime())

    @Slot(bool)
    def setAutomaticTime(self, on):
        self._update("_time", self.timeChanged, {"automatic": on})
        self.jobs.submit(lambda: self.system.time.set_automatic(on),
                         lambda _ok: self.refreshTime())


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    # Text drawn like KDE programs (FreeType, hinted) instead of Qt Quick's
    # distance-field glyphs, which looked uneven at fractional display
    # scales ("kal dır", "program lar" at 105 %, VM 2026-10-20).
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-settings")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-settings")
    app.setWindowIcon(QIcon.fromTheme("veltos-settings"))
    start_page = argv[1] if len(argv) > 1 else "home"
    backend = Backend(start_page=start_page)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
