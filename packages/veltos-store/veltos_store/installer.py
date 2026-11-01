"""The package installer window: double-clicking a .deb file opens it in the
layout of Windows 11's App Installer (product owner, 2026-10-27: ".deb
packages could not be installed; double-clicking one should install it in
a nice Windows 11 window"). `veltos-store --install-file FILE`.

The window reads the package (debfile.py), asks "Install <app>?" with its
publisher, version and size, and installs it with PackageKit
(`pkcon install-local`, which also brings what it needs from Debian's
archive; polkit asks for the administrator's password through VeltOS'
prompt). An installed package of the same name turns the question into
Update, Reinstall or "a newer version is installed". When it is done the
apps it added can be opened."""

import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from . import debfile, packages, strings, themewatch

QML_DIR = Path(__file__).resolve().parent / "qml"


def size_text(size, lang):
    if size >= 1 << 30:
        text = f"{size / (1 << 30):.1f} GB"
    elif size >= 1 << 20:
        text = f"{size / (1 << 20):.1f} MB"
    else:
        text = f"{max(1, round(size / 1024))} KB"
    return text.replace(".", ",") if lang == "tr" else text


class Installer(QObject):
    changed = Signal()
    lookChanged = Signal()
    closeRequested = Signal()

    def __init__(self, path, lang=None, reader=debfile.read, jobs=None, start=None, dark=False, accent="",
                 scale=1.0, desktop_dirs=("/usr/share/applications",), follow=None):
        super().__init__()
        self.lang = lang or strings.language()
        self._texts = strings.texts(self.lang)
        self.path = Path(path)
        self._jobs = jobs or packages.Jobs(parent=self)
        self._jobs.changed.connect(self.changed)
        self._jobs.finished.connect(self._finished)
        self._start = start
        self._scale = scale
        # `follow` reads the system's look again (main()); tests give none.
        self._look = themewatch.ThemeWatch(follow, self, initial=(dark, accent))
        self._look.changed.connect(self.lookChanged)
        self._desktop_dirs = desktop_dirs
        self._icon_dir = tempfile.mkdtemp(prefix="veltos-package-")
        self._icon_url = ""
        self._page = "invalid"
        self._error = ""
        self._show_log = False
        self._launch = True
        self._info = reader(self.path) if self.path.is_file() else None
        if self._info:
            self._page = "ready" if self._info["archOk"] else "wrongarch"
            if self._info["iconData"]:
                icon = Path(self._icon_dir) / self._info["iconName"]
                icon.write_bytes(self._info["iconData"])
                self._icon_url = QUrl.fromLocalFile(str(icon)).toString()

    def cleanup(self):
        shutil.rmtree(self._icon_dir, ignore_errors=True)

    def t(self, key):
        return self._texts[key]

    # --- the theme's properties (Theme.qml reads backend.*) ----------------------------------

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

    @Property("QVariantMap", constant=True)
    def texts(self):
        return self._texts

    # --- what the window shows -------------------------------------------------------------

    @Property(str, notify=changed)
    def page(self):
        """ready, working, done, failed, invalid (not a package dpkg reads)
        or wrongarch (made for another processor)."""
        return self._page

    @Property(str, constant=True)
    def status(self):
        """new, same (installed), newer (the file updates it) or older."""
        return self._info["status"] if self._info else ""

    @Property(str, constant=True)
    def name(self):
        return self._info["displayName"] if self._info else self.path.name

    @Property(str, constant=True)
    def iconUrl(self):
        return self._icon_url

    @Property(str, notify=changed)
    def title(self):
        if not self._info:
            return self.t("pkg_invalid_title")
        name = self.name
        key = {"ready": {"new": "pkg_install_q", "same": "pkg_installed_already", "newer": "pkg_update_q",
                         "older": "pkg_newer_installed"}[self._info["status"]],
               "wrongarch": "pkg_wrong_arch_title",
               "working": "pkg_installing_title", "done": "pkg_done_title", "failed": "pkg_failed_title"}[self._page]
        return self.t(key).replace("{name}", name)

    @Property("QVariantList", constant=True)
    def details(self):
        if not self._info:
            return [self.path.name]
        info, rows = self._info, []
        if info["publisher"]:
            rows.append(self.t("pkg_publisher").replace("{value}", info["publisher"]))
        rows.append(self.t("pkg_version").replace("{value}", info["version"]))
        if info["installed"] and info["installed"] != info["version"]:
            rows.append(self.t("pkg_installed_version").replace("{value}", info["installed"]))
        if info["size"]:
            rows.append(self.t("pkg_size").replace("{value}", size_text(info["size"], self.lang)))
        rows.append(self.t("pkg_package").replace("{value}", f"{info['package']} ({info['arch']})"))
        return rows

    @Property(str, notify=changed)
    def body(self):
        if not self._info:
            return self.t("pkg_invalid")
        if self._page == "wrongarch":
            return self.t("pkg_wrong_arch").replace("{arch}", self._info["arch"]).replace(
                "{native}", self._info["nativeArch"])
        if self._page == "done":
            # A command-line tool or a library has no Start entry (iperf3
            # said "You can find it in Start", VM 2026-11-01).
            return self.t("pkg_done" if self.hasApps else "pkg_done_tool")
        if self._page == "failed":
            key = packages.failure_key(self._error)
            return self.t("pkg_failed") + (" " + self.t("pkg_" + key) if key else "")
        if self._page == "working":
            state = self._jobs.state(str(self.path)) or ("refreshing" if self._jobs.current
                                                          and self._jobs.current[0] == "refresh" else "")
            # A local install has no pkcon status of its own at first (Jobs
            # calls it "updating"): it is installing.
            state = "installing" if state == "updating" else state
            return self.t("pkg_" + state) if state and ("pkg_" + state) in self._texts else self.t("pkg_working")
        return self._info["summary"] + ("\n\n" + self._info["description"] if self._info["description"] else "")

    @Property(int, notify=changed)
    def percent(self):
        return self._jobs.percent if self._page == "working" else -1

    @Property(str, notify=changed)
    def primaryText(self):
        """The ready page's button."""
        if not self._info or self._page != "ready":
            return ""
        return self.t({"new": "install", "same": "pkg_reinstall", "newer": "pkg_update",
                       "older": "pkg_downgrade"}[self._info["status"]])

    @Property("QVariantList", notify=changed)
    def apps(self):
        """The apps the package added, for Open (after the install, or when it
        is installed already)."""
        if not self._info or not (self._page == "done" or (self._page == "ready" and self._info["status"] == "same")):
            return []
        return [app for app in self._info["apps"] if self._desktop_file(app["id"])]

    @Property(bool, notify=changed)
    def hasApps(self):
        """Whether the package brings an app for Start (it has a
        .desktop file that is shown)."""
        return bool(self._info and self._info["apps"])

    @Property(bool, notify=changed)
    def launch(self):
        return self._launch

    @launch.setter
    def launch(self, value):
        if value != self._launch:
            self._launch = value
            self.changed.emit()

    @Property(bool, notify=changed)
    def showLog(self):
        return self._show_log

    @Property(str, notify=changed)
    def log(self):
        return self._jobs.output.strip()

    # --- actions -------------------------------------------------------------------------

    @Slot()
    def install(self):
        if self._page != "ready":
            return
        action = {"new": "install-local", "newer": "install-local", "same": "reinstall-local",
                  "older": "downgrade-local"}[self._info["status"]]
        self._page, self._error = "working", ""
        self._jobs.add(action, str(self.path))
        self.changed.emit()

    def _finished(self, action, package, ok):
        if action == "refresh":
            # A failed refresh is not the end: the install still tries with
            # the old lists (it needs them only for dependencies).
            return
        if ok:
            self._page = "done"
            if self._launch:
                apps = self.apps
                if apps:
                    self.openApp(0)
        else:
            self._page, self._error = "failed", self._jobs.error
        self.changed.emit()

    def _desktop_file(self, desktop_id):
        for folder in self._desktop_dirs:
            path = Path(folder) / desktop_id
            if path.is_file():
                return path
        return None

    @Slot(int)
    def openApp(self, index):
        apps = self.apps
        if 0 <= index < len(apps) and self._start:
            self._start(["gtk-launch", apps[index]["id"].removesuffix(".desktop")])

    @Slot()
    def toggleLog(self):
        self._show_log = not self._show_log
        self.changed.emit()

    @Slot()
    def close(self):
        if self._page != "working":
            self.closeRequested.emit()


def main(path, app, engine_factory, start):
    """Opens the installer window for `path` in the running QGuiApplication."""
    from .app import accent, dark_mode, text_scale
    installer = Installer(path, start=start, dark=dark_mode(), accent=accent(), scale=text_scale(),
                          follow=lambda: (dark_mode(), accent()))
    app.setApplicationDisplayName(installer.t("pkg_window_title"))
    app.setDesktopFileName("veltos-package-installer")
    engine = engine_factory()
    engine.rootContext().setContextProperty("backend", installer)
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "PackageInstaller.qml")))
    if not engine.rootObjects():
        return 1
    installer.closeRequested.connect(app.quit)
    code = app.exec()
    installer.cleanup()
    del engine
    return code
