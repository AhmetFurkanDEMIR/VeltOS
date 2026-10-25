"""VeltOS Settings window: Python backend for the QML user interface.

    veltos-settings [PAGE]      (PAGE: home, system, about, storage, ...)
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import Property, QLocale, QObject, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import accounts, apps, catalog, devices, inputs, prefs, strings, sysinfo, taskbar

QML_DIR = Path(__file__).resolve().parent / "qml"
LOOK_AND_FEEL = {False: "org.veltos.light", True: "org.veltos.dark"}
DESKTOP_THEME = {False: "VeltOS", True: "VeltOS-Dark"}
# The global theme writes the Plasma theme into ~/.config/kdedefaults, which
# the running taskbar does not notice: it watches the user's own plasmarc
# file (KDirWatch). kwriteconfig6 does not write a value equal to the
# kdedefaults one, so on a first switch nothing changed and the taskbar
# stayed light (VM test 2026-10-19); the file is therefore edited directly
# ([Theme] name=, other groups kept, same file so the watcher sees it).
# The operating system's website (product owner, 2026-10-22); also in
# /etc/os-release (HOME_URL, veltos-base).
VELTOS_WEBSITE = "https://veltos.ahmetfurkandemir.com/"

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
# The Terminal follows the theme (veltos-desktop).
[ -x /usr/libexec/veltos/terminal-theme ] && /usr/libexec/veltos/terminal-theme "$3"
true
'''


def detached(command, env=None):
    """Start a program that outlives Settings (its own session, no output)."""
    subprocess.Popen(command, env=env, start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


def windows_programs():
    """The installed Windows programs, as Windows 11's Settings > Apps >
    Installed apps lists them: from the Windows environment's registry
    (veltos_winapps.programs: what can be uninstalled), with the Start menu
    shortcut that veltos-run recorded for a program ("Open"); programs
    veltos-run started without installing them (no registry entry) too."""
    try:
        from veltos_winapps.programs import forget_removed, installed_programs
        from veltos_winapps.winenv import installed_apps
    except ImportError:
        return []
    # Programs removed by their own uninstaller: no Start menu entries or
    # records left behind (Wine's menu builder only ever adds them).
    forget_removed()
    records = []
    for record in installed_apps():
        shortcuts = [s for s in record.get("shortcuts", []) if Path(s).exists()]
        records.append({"name": record.get("name", ""), "publisher": record.get("publisher") or "",
                         "version": record.get("version") or "",
                         "installed": (record.get("installed_at") or "")[:10],
                         "shortcut": shortcuts[0] if shortcuts else ""})

    def same_program(record, program):
        a, b = record["name"].casefold().strip(), program["name"].casefold()
        return bool(a) and (a in b or b in a)

    apps, used = [], set()
    for program in installed_programs():
        record = next((r for i, r in enumerate(records) if i not in used and same_program(r, program)), None)
        if record is not None:
            used.add(records.index(record))
        apps.append({"key": program["key"], "name": program["name"],
                     "publisher": program["publisher"] or (record or {}).get("publisher", ""),
                     "version": program["version"] or (record or {}).get("version", ""),
                     "installed": program["date"] or (record or {}).get("installed", ""),
                     "sizeKb": program["sizeKb"], "exe": program["icon"],
                     "shortcut": (record or {}).get("shortcut", ""), "icon": ""})
    for index, record in enumerate(records):
        if index not in used:
            apps.append(dict(record, key="", sizeKb=0, exe="", icon=""))
    return apps


def program_icon(exe, cache_dir=None):
    """A PNG of the program's own icon (from its .exe), cached; "" if none."""
    if not exe:
        return ""
    cache = Path(cache_dir or (Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
                               / "veltos" / "program-icons"))
    target = cache / (re.sub(r"[^A-Za-z0-9._-]", "_", exe.strip("/"))[-120:] + ".png")
    if target.exists():
        return str(target)
    try:
        import pefile
        from veltos_winapps.exeinfo import extract_icon_png
        pe = pefile.PE(exe, fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
        data = extract_icon_png(pe, 64)
    except Exception:  # not a readable program file: the generic icon
        return ""
    if not data:
        return ""
    cache.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return str(target)


def system_tools(runner=devices.run, lang="en"):
    """The objects that read and change system settings (devices.py,
    prefs.py, inputs.py, accounts.py, apps.py)."""
    return SimpleNamespace(network=devices.Network(runner), bluetooth=devices.Bluetooth(runner),
                           sound=devices.Sound(runner), display=devices.Display(runner),
                           personal=devices.Personalization(runner), time=devices.Time(runner),
                           prefs=prefs.Preferences(runner), inputs=inputs.Inputs(runner),
                           accounts=accounts.Accounts(runner), defaults=apps.DefaultApps(runner, lang=lang),
                           startup=apps.StartupApps(lang=lang), taskbar=taskbar.Taskbar(runner))


# Recently used settings (Home > Recommended settings), most used first.
RECENT_FILE = "veltos/settings-recent.json"
DEFAULT_RECENT = [["time", "datetime"], ["apps", "defaultapps"], ["personalization", "lockscreen"]]


def recent_settings(visits, count=3):
    """[page id, item id] of the most visited settings, filled up with
    Windows' usual three."""
    ranked = sorted(visits.items(), key=lambda kv: (-kv[1].get("count", 0), -kv[1].get("last", 0)))
    result = [key.split("/", 1) for key, _ in ranked if "/" in key][:count]
    for default in DEFAULT_RECENT:
        if len(result) >= count:
            break
        if default not in result:
            result.append(default)
    return result


def duration_label(lang, minutes):
    """"5 minutes", "1 hour", "Never" as Windows lists them."""
    if minutes == 0:
        return strings.text(lang, "never")
    if minutes % 60 == 0:
        hours = minutes // 60
        return strings.text(lang, "one_hour") if hours == 1 else strings.text(lang, "hours", count=hours)
    return strings.text(lang, "one_minute") if minutes == 1 else strings.text(lang, "minutes", count=minutes)


def format_label(name):
    """"Türkçe (Türkiye)" for tr_TR, in the language of the format itself."""
    locale = QLocale(name)
    return f"{locale.nativeLanguageName()} ({locale.nativeTerritoryName()})"


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
    prefsChanged = Signal()
    taskbarChanged = Signal()
    inputsChanged = Signal()
    accountsChanged = Signal()
    appsChanged = Signal()
    # "password", "adduser": "" when it worked, otherwise a text key.
    accountResult = Signal(str, str)

    def __init__(self, lang=None, start=detached, start_page="home", system=None, threaded=True):
        super().__init__()
        self.lang = lang or strings.language()
        self._start = start
        self._dark = sysinfo.dark_mode()
        self._about = None
        self._storage = None
        self._windows_apps = None
        self._start_page = start_page
        self.system = system or system_tools(lang=self.lang)
        self.jobs = Jobs(threaded)
        # Light/dark, theme and accent changes run one after another: side by
        # side (the mode switch was a separate process, every job a thread)
        # one change's colour scheme could undo the other's accent, and the
        # taskbar once kept its old colours (product owner, 2026-10-23).
        self._appearance_lock = threading.Lock()
        self._network = {"available": False, "enabled": False, "connection": {}, "networks": [],
                         "loaded": False, "scanning": False, "connecting": "", "failed": ""}
        self._bluetooth = {"available": False, "powered": False, "devices": [], "loaded": False,
                           "busy": "", "found": [], "scanning": False, "pairing": "", "pairFailed": ""}
        self._sound = {"outputs": [], "inputs": [], "loaded": False}
        self._display = {"outputs": [], "loaded": False}
        self._personal = {"wallpapers": [], "wallpaper": "", "accent": "",
                          "accents": devices.ACCENTS, "loaded": False}
        self._time = {"timezone": "", "automatic": False, "canAutomatic": True, "zones": [],
                      "loaded": False}
        self._prefs = {"loaded": False}
        self._taskbar = {"loaded": False, "available": False, "trayItems": []}
        self._inputs = {"loaded": False, "hasMouse": False, "hasTouchpad": False}
        self._accounts = {"loaded": False, "me": {"name": sysinfo.user_name(), "realName": sysinfo.user_name(),
                                                  "icon": "", "admin": False}, "others": []}
        self._apps = {"loaded": False, "groups": [], "startup": [], "notificationApps": []}
        self._uninstalling = set()

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

    @Property(str, constant=True)
    def veltosWebsite(self):
        return VELTOS_WEBSITE

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
            self._load_program_icons()
        return self._windows_apps

    def _load_program_icons(self):
        """The programs' own icons, read from their .exe files off the UI thread."""
        apps = list(self._windows_apps or [])

        def work():
            return {app["exe"]: program_icon(app["exe"]) for app in apps if app.get("exe")}

        def done(icons):
            if not icons or self._windows_apps is None:
                return
            self._windows_apps = [dict(app, icon=icons.get(app.get("exe"), "") or app.get("icon", ""))
                                  for app in self._windows_apps]
            self.changed.emit()
        self.jobs.submit(work, done)

    @Property("QVariantList", notify=changed)
    def uninstalling(self):
        return sorted(self._uninstalling)

    @Slot(str)
    def uninstallWindowsApp(self, key):
        """Settings > Apps: "Uninstall" of a Windows program runs its own
        uninstaller through Wine; the list follows when it is done."""
        try:
            from veltos_winapps.programs import uninstall_command
            from veltos_winapps.winenv import Environment
        except ImportError:
            return
        command = uninstall_command(key)
        if command is None or key in self._uninstalling:
            return
        self._uninstalling.add(key)
        self.changed.emit()
        environment = Environment()

        def work():
            import subprocess
            try:
                subprocess.run(command, env=environment.env(), stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
            except (OSError, subprocess.SubprocessError):
                pass
            # Start menu and desktop entries, icons and the record go too.
            from veltos_winapps.programs import forget_removed
            forget_removed(environment)

        def done(_result):
            self._uninstalling.discard(key)
            self._windows_apps = None
            self.changed.emit()
        self.jobs.submit(work, done)

    @Property(str, constant=True)
    def userName(self):
        return sysinfo.user_name()

    @Property(bool, notify=changed)
    def darkMode(self):
        return self._dark

    @Property(float, notify=prefsChanged)
    def textScale(self):
        """Accessibility > Text size as a factor for Settings' own texts;
        follows the slider at once (the optimistic prefs value)."""
        percent = self._prefs.get("textSize") if isinstance(self._prefs, dict) else None
        if not isinstance(percent, (int, float)):
            percent = self.system.prefs.text_size()
        return max(1.0, min(2.25, float(percent) / 100))

    @Slot()
    def refresh(self):
        self._about = self._storage = self._windows_apps = None
        self._dark = sysinfo.dark_mode()
        self.changed.emit()

    # --- actions --------------------------------------------------------------

    def _appearance(self, work):
        def serial():
            with self._appearance_lock:
                return work()
        self.jobs.submit(serial)

    @Slot(bool)
    def setDarkMode(self, dark):
        if dark == self._dark:
            return
        # The global theme switches colours, Plasma theme, window frames and
        # (through the kvantum / kvantum-dark style key) the application style.
        mode = ["sh", "-c", APPLY_THEME, "sh", LOOK_AND_FEEL[dark], DESKTOP_THEME[dark],
                "dark" if dark else "light"]
        accent = self._personal.get("accent", "")
        self._appearance(lambda: self.system.personal.set_mode(mode, accent))
        self._dark = dark
        self.changed.emit()

    @Slot(str)
    def runAction(self, action):
        if action == "store":
            self._start(["veltos-store"])
        elif action == "updates":
            self._start(["veltos-store", "--updates"])
        elif action == "disk-management":
            self._start(["veltos-disks"])      # VeltOS Disk Management (Windows 11 layout)
        elif action == "graphics":
            self._start(["veltos-graphics"])   # VeltOS Graphics Cards (drivers, properties)
        elif action == "website":
            self._start(["xdg-open", VELTOS_WEBSITE])
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

    # Add a device: VeltOS' own dialog (BluetoothPage, HomePage), not
    # KDE's Bluetooth wizard.
    @Slot()
    def discoverBluetooth(self):
        if self._bluetooth.get("scanning"):
            return
        self._update("_bluetooth", self.bluetoothChanged, {"scanning": True, "found": [], "pairFailed": ""})
        self.jobs.submit(lambda: self.system.bluetooth.discover(),
                         lambda found: self._update("_bluetooth", self.bluetoothChanged,
                                                    {"scanning": False, "found": found or []}))

    @Slot(str)
    def pairBluetooth(self, mac):
        self._update("_bluetooth", self.bluetoothChanged, {"pairing": mac, "pairFailed": ""})

        def done(ok):
            found = [d for d in self._bluetooth.get("found", []) if not ok or d["mac"] != mac]
            self._update("_bluetooth", self.bluetoothChanged,
                         {"pairing": "", "pairFailed": "" if ok else mac, "found": found})
            self.refreshBluetooth()
        self.jobs.submit(lambda: self.system.bluetooth.pair(mac), done)

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
        self._appearance(lambda: self.system.personal.set_accent(color))

    # --- Personalization > Themes ------------------------------------------------------------

    @Property("QVariantList", constant=True)
    def themes(self):
        i = 0 if self.lang == "en" else 1
        result = []
        for theme in devices.THEMES:
            contents = Path("/usr/share/wallpapers") / theme["wallpaper"] / "contents"
            preview = contents / ("screenshot-dark.png" if theme["dark"] else "screenshot.png")
            result.append({"id": theme["id"], "title": theme["title"][i], "colour": theme["colour"][i],
                           "dark": theme["dark"], "accent": theme["accent"], "wallpaper": theme["wallpaper"],
                           "preview": QUrl.fromLocalFile(str(preview)).toString() if preview.exists() else ""})
        return result

    @Property(str, notify=personalChanged)
    def currentTheme(self):
        return devices.current_theme(self._personal.get("wallpaper", ""), self._dark,
                                     self._personal.get("accent", ""))

    @Slot(str)
    def applyTheme(self, theme_id):
        theme = next((t for t in devices.THEMES if t["id"] == theme_id), None)
        if theme is None:
            return
        path = next((w["path"] for w in self._personal.get("wallpapers", []) if w["name"] == theme["wallpaper"]),
                    str(Path("/usr/share/wallpapers") / theme["wallpaper"]))
        dark = theme["dark"]
        mode = None
        if dark != self._dark:
            mode = ["sh", "-c", APPLY_THEME, "sh", LOOK_AND_FEEL[dark], DESKTOP_THEME[dark],
                    "dark" if dark else "light"]
            self._dark = dark
            self.changed.emit()
        self._update("_personal", self.personalChanged, {"wallpaper": path, "accent": theme["accent"]})
        self._appearance(lambda: self.system.personal.apply_theme(path, theme["accent"], mode))

    # --- Home ---------------------------------------------------------------------------------

    @Property(str, notify=changed)
    def updateChecked(self):
        return strings.text(self.lang, "last_checked").replace(
            "{when}", sysinfo.ago(sysinfo.last_update_check(), self.lang))

    def _recent_path(self):
        return devices.config_home() / RECENT_FILE

    def _visits(self):
        try:
            data = json.loads(self._recent_path().read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    @Property("QVariantList", notify=changed)
    def recentSettings(self):
        return recent_settings(self._visits())

    @Slot(str, str)
    def recordVisit(self, page_id, page):
        """Count a visit to a built-in page (for Recommended settings)."""
        item_id = next((item["id"] for p in catalog.PAGES if p["id"] == page_id
                        for item in p["items"] if item.get("page") == page), "")
        if not item_id:
            return
        visits = self._visits()
        entry = visits.setdefault(f"{page_id}/{item_id}", {})
        entry["count"] = entry.get("count", 0) + 1
        entry["last"] = int(time.time())
        path = self._recent_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(visits), encoding="utf-8")
        except OSError:
            pass

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

    @Slot(str, str, result=bool)
    def setDateTime(self, date, clock):
        """Set the date and time by hand (timedatectl; polkit may ask)."""
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not re.fullmatch(r"\d{1,2}:\d{2}", clock):
            return False
        hours, minutes = (int(v) for v in clock.split(":"))
        if hours > 23 or minutes > 59:
            return False
        self.jobs.submit(lambda: devices.run(["timedatectl", "set-time", f"{date} {hours:02d}:{minutes:02d}:00"],
                                             timeout=300), lambda _r: self.refreshTime())
        return True

    # --- settings kept in KDE files (prefs.py) ------------------------------------------------

    @Property("QVariantMap", notify=prefsChanged)
    def prefs(self):
        return self._prefs

    @Slot()
    def refreshPrefs(self):
        tools = self.system.prefs

        def work():
            state = tools.state()
            state["formatOptions"] = [{"value": name, "label": format_label(name)}
                                      for name in tools.available_formats()]
            return state
        self.jobs.submit(work, self._merge("_prefs", self.prefsChanged))

    @Slot(str, "QVariant")
    def setPref(self, name, value):
        if name not in prefs.SETTINGS:
            return
        self._update("_prefs", self.prefsChanged, {name: value})
        self.jobs.submit(lambda: self.system.prefs.set(name, value))

    # --- Personalization > Taskbar (taskbar.py) ------------------------------------------------

    @Property("QVariantMap", notify=taskbarChanged)
    def taskbar(self):
        return self._taskbar

    @Slot()
    def refreshTaskbar(self):
        self.jobs.submit(lambda: self.system.taskbar.state(self.lang), self._merge("_taskbar", self.taskbarChanged))

    @Slot(str, "QVariant")
    def setTaskbar(self, name, value):
        # QML numbers arrive as floats.
        if name == "search" and isinstance(value, float) and value.is_integer():
            value = int(value)
        if taskbar.valid(name, value) is None:
            return
        self._update("_taskbar", self.taskbarChanged, {name: value})
        self.jobs.submit(lambda: self.system.taskbar.set(name, value))

    @Slot(str, bool)
    def setTrayIcon(self, item_id, shown):
        items = [dict(item, shown=shown) if item.get("id") == item_id else item
                 for item in self._taskbar.get("trayItems", [])]
        self._update("_taskbar", self.taskbarChanged, {"trayItems": items})
        self.jobs.submit(lambda: self.system.taskbar.set_tray_item(item_id, shown))

    @Slot(bool)
    def setDoNotDisturb(self, on):
        self._update("_prefs", self.prefsChanged, {"doNotDisturb": on})
        self.jobs.submit(lambda: self.system.prefs.set_do_not_disturb(on))

    @Slot(bool)
    def setAnimations(self, on):
        self._update("_prefs", self.prefsChanged, {"animations": on})
        self.jobs.submit(lambda: self.system.prefs.set_animations(on))

    @Slot(bool)
    def setFileSearch(self, on):
        self._update("_prefs", self.prefsChanged, {"fileSearch": on})
        self.jobs.submit(lambda: self.system.prefs.set_file_search(on))

    @Slot(int)
    def setTextSize(self, percent):
        self._update("_prefs", self.prefsChanged, {"textSize": percent})
        self.jobs.submit(lambda: self.system.prefs.set_text_size(percent))

    @Slot(str)
    def setLanguage(self, code):
        self._update("_prefs", self.prefsChanged, {"language": code})
        self.jobs.submit(lambda: self.system.prefs.set_language(code))

    @Slot(str)
    def setFormats(self, name):
        options = [o["value"] for o in self._prefs.get("formatOptions", [])]
        self._update("_prefs", self.prefsChanged, {"formats": name})
        self.jobs.submit(lambda: self.system.prefs.set_formats(name, options))

    @Slot("QVariantList")
    def setLayouts(self, layouts):
        layouts = [str(l) for l in layouts]
        self._update("_prefs", self.prefsChanged, {"layouts": layouts})
        self.jobs.submit(lambda: self.system.prefs.set_layouts(layouts))

    @Property("QVariantList", constant=True)
    def layoutOptions(self):
        index = 2 if self.lang == "tr" else 1
        return [{"value": entry[0], "label": entry[index]} for entry in prefs.KEYBOARD_LAYOUTS]

    @Property("QVariantList", constant=True)
    def timeoutOptions(self):
        """Screen off / sleep choices, values in seconds."""
        return [{"value": m * 60, "label": duration_label(self.lang, m)} for m in prefs.TIMEOUT_MINUTES]

    @Property("QVariantList", constant=True)
    def lockOptions(self):
        return [{"value": m, "label": duration_label(self.lang, m)} for m in prefs.LOCK_MINUTES]

    @Property("QVariantList", constant=True)
    def powerActionOptions(self):
        names = ("sleep", "hibernate", "shutdown", "screenoff", "nothing")
        return [{"value": prefs.POWER_ACTIONS[n], "label": strings.text(self.lang, "action_" + n)} for n in names]

    @Property("QVariantList", constant=True)
    def languageOptions(self):
        return [{"value": "en", "label": "English (United States)"}, {"value": "tr", "label": "Türkçe"}]

    # --- Mouse and touchpad (inputs.py) ------------------------------------------------------

    @Property("QVariantMap", notify=inputsChanged)
    def inputs(self):
        return self._inputs

    @Slot()
    def refreshInputs(self):
        self.jobs.submit(self.system.inputs.state, self._merge("_inputs", self.inputsChanged))

    @Slot(str, "QVariant", str)
    def setInput(self, prop, value, target):
        """target: "mouse", "touchpad" or "all"."""
        key = {("leftHanded", "all"): "leftHanded", ("pointerAcceleration", "mouse"): "speed",
               ("scrollFactor", "mouse"): "scrollFactor", ("naturalScroll", "mouse"): "mouseNaturalScroll",
               ("enabled", "touchpad"): "touchpadOn", ("tapToClick", "touchpad"): "tapToClick",
               ("naturalScroll", "touchpad"): "touchpadNaturalScroll",
               ("pointerAcceleration", "touchpad"): "touchpadSpeed"}.get((prop, target))
        if key:
            self._update("_inputs", self.inputsChanged, {key: value})
        touchpad = {"mouse": False, "touchpad": True}.get(target)
        self.jobs.submit(lambda: self.system.inputs.set(prop, value, touchpad))

    # --- Accounts (accounts.py) ------------------------------------------------------------

    @Property("QVariantMap", notify=accountsChanged)
    def accounts(self):
        return self._accounts

    @Slot()
    def refreshAccounts(self):
        self.jobs.submit(self.system.accounts.state, self._merge("_accounts", self.accountsChanged))

    @Slot(str)
    def setRealName(self, name):
        self.jobs.submit(lambda: self.system.accounts.set_real_name(name), lambda _ok: self.refreshAccounts())

    @Slot()
    def choosePicture(self):
        pictures = Path.home() / "Pictures"
        start = pictures if pictures.is_dir() else Path.home()
        title = strings.text(self.lang, "choose_file")

        def done(path):
            if path:
                self.jobs.submit(lambda: self.system.accounts.set_picture(path),
                                 lambda _ok: self.refreshAccounts())
        self.jobs.submit(lambda: self.system.personal.pick_image(start, title), done)

    @Slot(str, str, str)
    def changePassword(self, current, new, confirm):
        if new != confirm:
            self.accountResult.emit("password", "passwords_differ")
            return
        self.jobs.submit(lambda: accounts.change_password(current, new),
                         lambda error: self.accountResult.emit("password", error or ""))

    @Slot(str, str, str, bool)
    def addUser(self, username, full_name, password, admin):
        def done(error):
            self.accountResult.emit("adduser", error or "")
            self.refreshAccounts()
        self.jobs.submit(lambda: self.system.accounts.add_user(username.strip(), full_name, password, admin), done)

    @Slot(str)
    def removeUser(self, username):
        self.jobs.submit(lambda: self.system.accounts.remove_user(username), lambda _ok: self.refreshAccounts())

    @Slot(str, bool)
    def setAdmin(self, username, admin):
        self.jobs.submit(lambda: self.system.accounts.set_admin(username, admin),
                         lambda _ok: self.refreshAccounts())

    # --- Apps > Default apps, Startup; notification senders (apps.py) -----------------------

    @Property("QVariantMap", notify=appsChanged)
    def apps(self):
        return self._apps

    @Slot()
    def refreshApps(self):
        tools = self.system

        def work():
            return {"groups": tools.defaults.state()["groups"], "startup": tools.startup.entries(),
                    "notificationApps": tools.prefs.notification_apps(lang=self.lang)}
        self.jobs.submit(work, self._merge("_apps", self.appsChanged))

    @Slot(str, str)
    def setDefaultApp(self, group_id, desktop):
        groups = [dict(g, current=desktop) if g["id"] == group_id else g for g in self._apps["groups"]]
        self._update("_apps", self.appsChanged, {"groups": groups})
        self.jobs.submit(lambda: self.system.defaults.set_default(group_id, desktop))

    @Slot(str, bool)
    def setStartupEnabled(self, entry_id, on):
        entries = [dict(e, enabled=on) if e["id"] == entry_id else e for e in self._apps["startup"]]
        self._update("_apps", self.appsChanged, {"startup": entries})
        self.jobs.submit(lambda: self.system.startup.set_enabled(entry_id, on))

    @Slot(str, bool)
    def setAppBanners(self, entry, on):
        senders = [dict(a, banners=on) if a["id"] == entry else a for a in self._apps["notificationApps"]]
        self._update("_apps", self.appsChanged, {"notificationApps": senders})
        self.jobs.submit(lambda: self.system.prefs.set_app_banners(entry, on))


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    try:  # Windows 11 scroll bars (veltos-desktop's org.veltos.controls)
        from veltos_controls import use as use_veltos_controls
        use_veltos_controls()
    except ImportError:
        pass
    # Text drawn like KDE programs (FreeType, hinted) instead of Qt Quick's
    # distance-field glyphs, which looked uneven at fractional display
    # scales ("kal dır", "program lar" at 105 %, VM 2026-10-20).
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-settings")
    app.setApplicationDisplayName(strings.text(strings.language(), "app_title"))
    app.setDesktopFileName("veltos-settings")
    app.setWindowIcon(QIcon.fromTheme("veltos-settings"))
    # A VeltOS page id or a KDE settings module name (the redirect of
    # systemsettings / kcmshell6 passes those).
    start_page = catalog.page_for_module(argv[1]) if len(argv) > 1 else "home"
    backend = Backend(start_page=start_page)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    code = app.exec()
    # The QML goes first: deleted after the objects it reads, its bindings
    # ran once more against dead ones ("Cannot call method ... of null").
    del engine
    return code
