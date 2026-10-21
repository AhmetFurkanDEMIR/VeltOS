"""VeltOS Store: apps for VeltOS in the layout of the Windows 11 Microsoft
Store (Home, Apps, Gaming, Library, app pages). The catalogue is Debian's
AppStream data; installing goes through PackageKit. PySide6 + QML."""

import configparser
import os
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from . import catalog, packages, strings

QML_DIR = Path(__file__).resolve().parent / "qml"


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

def accent():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02x%02x%02x" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def detached(command):
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Backend(QObject):
    catalogChanged = Signal()
    statesChanged = Signal()
    updatesChanged = Signal()
    loaded = Signal(object, object)   # entries, details function (from the loading thread)
    updatesFound = Signal(int)        # from the update check thread
    removalChecked = Signal(str, bool)  # package, protected (from the check thread)

    def __init__(self, lang=None, loader=catalog.load_appstream, installed=packages.installed_packages,
                 jobs=None, start=detached, update_checker=None, background=True, start_page="home",
                 refresher=None, protected=packages.removal_is_protected, names=catalog.apply_veltos_names):
        super().__init__()
        self._start_page = start_page
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self._loader = loader
        self._installed_source = installed
        self._start = start
        self._catalog = catalog.Catalog([])
        self._details = lambda _app_id: {"description": "", "screenshots": []}
        self._loading = True
        self._installed = set()
        self._revision = 0
        self._updates = -1          # -1: not checked yet
        self._checking = False
        self._update_checker = update_checker or self._pkcon_updates
        self._refresher = refresher if refresher is not None else self._refresh_if_old
        self._protected_check = protected
        self._names = names
        self._protected = set()
        self.jobs = jobs or packages.Jobs(parent=self)
        self.jobs.changed.connect(self._jobs_changed)
        self.jobs.finished.connect(self._job_finished)
        self._failed = set()
        self._failure_texts = {}
        self.loaded.connect(self._set_catalog)
        self.updatesFound.connect(self._set_updates)
        self.removalChecked.connect(self._removal_checked)
        if background:
            threading.Thread(target=self._load, daemon=True).start()
        else:
            self._load()

    # --- loading ------------------------------------------------------------------

    def _load(self):
        self._load_once()
        # Old or missing catalogue data: refresh the package lists (which
        # also renews the AppStream data) and load again.
        if self._refresher and self._refresher():
            self._load_once()

    def _load_once(self):
        try:
            entries, details = self._loader()
            entries = self._names(entries, self.lang)
        except Exception:     # no AppStream data or binding: show the "not available" page
            entries, details = [], None
        self._installed = self._installed_source()
        self.loaded.emit(entries, details)

    @staticmethod
    def _refresh_if_old():
        age = catalog.catalog_age_days()
        if age is not None and age < catalog.MAX_AGE_DAYS:
            return False
        try:
            result = subprocess.run(["pkcon", "-p", "refresh"], capture_output=True, text=True, timeout=600,
                                    env=dict(os.environ, LC_ALL="C", LANGUAGE="C"))
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0 and "Fatal error" not in result.stdout

    def _set_catalog(self, entries, details):
        self._catalog = catalog.Catalog(entries)
        if details:
            self._details = details
        self._loading = False
        self.catalogChanged.emit()
        self._bump()

    def _bump(self):
        self._revision += 1
        self.statesChanged.emit()

    # --- properties ---------------------------------------------------------------

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    @Property(str, constant=True)
    def startPage(self):
        return self._start_page

    @Property(float, constant=True)
    def textScale(self):
        """Settings > Accessibility > Text size (text_scale())."""
        return text_scale()

    @Property(bool, constant=True)
    def darkMode(self):
        return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")

    @Property(str, constant=True)
    def accent(self):
        return accent()

    @Property(bool, notify=catalogChanged)
    def loading(self):
        return self._loading

    @Property(int, notify=catalogChanged)
    def appCount(self):
        return len(self._catalog)

    @Property(int, notify=statesChanged)
    def revision(self):
        """Changes whenever an install state changes (QML bindings use it)."""
        return self._revision

    def _card(self, entry):
        return {"id": entry["id"], "name": entry["name"], "summary": entry.get("summary", ""),
                "pkg": entry["pkg"], "icon": entry.get("icon", ""),
                "category": catalog.category_title(entry["category"], self.lang)}

    def _cards(self, entries):
        return [self._card(e) for e in entries]

    @Property("QVariantMap", notify=catalogChanged)
    def home(self):
        c = self._catalog
        hero = []
        for pkg, start, end in catalog.FEATURED:
            entry = c.package(pkg)
            if entry:
                hero.append(dict(self._card(entry), start=start, end=end))
        t = self._texts
        sections = [
            {"title": t["essentials"], "items": self._cards(c.picked(catalog.ESSENTIALS, 12))},
            {"title": t["top_productivity"], "items": self._cards(c.in_category("productivity", limit=12)),
             "category": "productivity"},
            {"title": t["top_creative"], "items": self._cards(c.picked(catalog.CREATIVE, 12))},
            {"title": t["top_games"], "items": self._cards(c.picked(catalog.GAMES, 12)), "category": "games"},
        ]
        return {"hero": hero, "sections": [s for s in sections if s["items"]]}

    @Property("QVariantList", constant=True)
    def categories(self):
        return [{"id": c[0], "title": catalog.category_title(c[0], self.lang), "icon": c[4]}
                for c in catalog.CATEGORIES if c[0] != "games"]

    @Property(int, notify=updatesChanged)
    def updates(self):
        return self._updates

    @Property(bool, notify=updatesChanged)
    def checkingUpdates(self):
        return self._checking

    @Property("QVariantMap", notify=statesChanged)
    def activeJob(self):
        if not self.jobs.current:
            return {}
        action, pkg = self.jobs.current
        return {"action": action, "pkg": pkg, "percent": self.jobs.percent,
                "status": self._texts.get(self.jobs.state(pkg), "")}

    # --- queries ------------------------------------------------------------------

    @Slot(str, result="QVariantList")
    def browse(self, category):
        """All apps of a category; "" for all apps, "games" for games."""
        if category == "games":
            return self._cards(self._catalog.in_category("games"))
        if category:
            return self._cards(self._catalog.in_category(category))
        return self._cards(self._catalog.in_category(games=False))

    @Slot(str, result="QVariantList")
    def search(self, text):
        return self._cards(self._catalog.search(text))

    @Slot(str, result="QVariantMap")
    def details(self, app_id):
        entry = self._catalog.get(app_id)
        if not entry:
            return {}
        more = self._details(app_id)
        return dict(self._card(entry),
                    description=more.get("description", ""),
                    screenshots=more.get("screenshots", []),
                    developer=entry.get("developer") or self._texts["unknown_developer"],
                    license=entry.get("license", ""),
                    homepage=entry.get("homepage", ""))

    @Slot(str, int, result=str)
    def state(self, pkg, _revision=0):
        """"installed", "" (not installed), or the running job's state key."""
        job = self.jobs.state(pkg)
        if job:
            return job
        if pkg in self._failed:
            return "failed"
        return "installed" if pkg in self._installed else ""

    @Slot(str, int, result=int)
    def percent(self, pkg, _revision=0):
        return self.jobs.percent if self.jobs.current and self.jobs.current[1] == pkg else -1

    @Property("QVariantList", notify=statesChanged)
    def library(self):
        entries = [e for e in self._catalog.entries.values() if e["pkg"] in self._installed]
        entries.sort(key=lambda e: e["name"].lower())
        return self._cards(entries)

    # --- actions ------------------------------------------------------------------

    @Slot(str)
    def install(self, pkg):
        self._failed.discard(pkg)
        self.jobs.add("install", pkg)

    @Slot(str)
    def uninstall(self, pkg):
        """Uninstall, unless that would remove a part of VeltOS (checked in
        the background with apt's simulation)."""
        self._failed.discard(pkg)
        threading.Thread(target=lambda: self.removalChecked.emit(pkg, self._protected_check(pkg)),
                         daemon=True).start()

    def _removal_checked(self, pkg, protected):
        if protected:
            self._protected.add(pkg)
            self._bump()
        else:
            self.jobs.add("remove", pkg)

    @Slot(str, int, result=bool)
    def isProtected(self, pkg, _revision=0):
        return pkg in self._protected

    @Slot(str)
    def open(self, app_id):
        entry = self._catalog.get(app_id)
        if not entry:
            return
        desktop = entry.get("desktop") or app_id
        if desktop.endswith(".desktop"):
            desktop = desktop[:-len(".desktop")]
        self._start(["gtk-launch", desktop])

    @Slot()
    def checkUpdates(self):
        if self._checking:
            return
        self._checking = True
        self.updatesChanged.emit()

        threading.Thread(target=lambda: self.updatesFound.emit(self._update_checker()), daemon=True).start()

    def _set_updates(self, count):
        self._updates = count
        self._checking = False
        self.updatesChanged.emit()

    @Slot()
    def updateAll(self):
        self.jobs.add("update", "")

    @staticmethod
    def _pkcon_updates():
        try:
            result = subprocess.run(["pkcon", "-p", "get-updates"], capture_output=True, text=True,
                                    timeout=600, env=dict(os.environ, LC_ALL="C", LANGUAGE="C"))
        except (OSError, subprocess.SubprocessError):
            return 0
        return packages.count_updates(result.stdout)

    def _jobs_changed(self):
        self._bump()

    def _job_finished(self, action, pkg, ok):
        self._installed = self._installed_source()
        if action == "update":
            self._updates = 0 if ok else self._updates
            self.updatesChanged.emit()
        elif action == "refresh":
            pass                        # a failed refresh is reported by the install that follows
        elif (action == "install") != (pkg in self._installed):
            self._failed.add(pkg)       # nothing changed: refused, failed or cancelled
            self._failure_texts[pkg] = self.jobs.error
        self._bump()

    @Slot(str, int, result=str)
    def failureText(self, pkg, _revision=0):
        """What went wrong with the last job of this app, in plain words
        (PackageKit's message where VeltOS has no better wording)."""
        error = self._failure_texts.get(pkg, "")
        key = packages.failure_key(error)
        if key:
            return self._texts[key]
        if error and error != "pkcon":
            return self._texts["failed_detail"].replace("{detail}", error)
        return self._texts["failed"]


def instance_name():
    return f"veltos-store-{os.getuid()}"


def raise_running():
    """One Store window per user: ask a running one to come to the front."""
    socket = QLocalSocket()
    socket.connectToServer(instance_name())
    if not socket.waitForConnected(500):
        return False
    socket.write(b"raise\n")
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def listen_for_raise(window):
    server = QLocalServer(window)
    QLocalServer.removeServer(instance_name())

    def show():
        connection = server.nextPendingConnection()
        if connection:
            connection.close()
        window.show()
        window.raise_()
        window.requestActivate()

    server.newConnection.connect(show)
    server.listen(instance_name())
    return server


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QGuiApplication(argv)
    if raise_running():
        return 0
    QQuickWindow.setTextRenderType(QQuickWindow.TextRenderType.NativeTextRendering)
    app.setApplicationName("veltos-store")
    app.setDesktopFileName("veltos-store")
    app.setWindowIcon(QIcon.fromTheme("veltos-store"))
    # veltos-store --updates: Library, checking for updates (Settings >
    # VeltOS Update).
    updates = "--updates" in argv
    backend = Backend(start_page="library" if updates else "home")
    if updates:
        backend.checkUpdates()
    app.setApplicationDisplayName(backend.texts["app_title"])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        return 1
    server = listen_for_raise(engine.rootObjects()[0])  # noqa: F841 (kept alive)
    code = app.exec()
    del engine
    return code
