"""Qt Quick set-up shared by VeltOS' apps (installed by veltos-desktop):

* VeltOS' Qt Quick Controls style: Windows 11 scroll bars over KDE's
  Breeze (qml/org/veltos/controls). KDE's platform theme gives every
  QGuiApplication the org.kde.breeze style whatever QT_QUICK_CONTROLS_STYLE
  says (plasma-integration KdePlatformTheme::setQtQuickControlsTheme), and
  Breeze draws a separator line beside every scroll bar.
* A QML disk cache that is safe with packaged files: the launchers turn
  Qt's cache off (QML_DISABLE_DISK_CACHE) because every package build
  gives its files the same time, so Qt kept old compiled QML after an
  update. Here the cache lives in a folder named after a hash of the app's
  QML files (QML_DISK_CACHE_PATH): new files, new folder; the QML is
  compiled once instead of at every start.

An app calls use() right after creating its QGuiApplication, before
loading QML:

    app = QGuiApplication(argv)
    try:                        # Windows 11 scroll bars (veltos-desktop)
        from veltos_controls import use
        use()
    except ImportError:
        pass

Kirigami chooses its platform plugin (KDE's colours for Kirigami.Theme) by
the style's name: veltos-desktop links org.veltos.controls.so to Breeze's
plugin in PLUGIN_DIR.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

QML_DIR = "/usr/share/veltos/qml"
PLUGIN_DIR = "/usr/share/veltos/qt-plugins"
STYLE = "org.veltos.controls"


def cache_dir():
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "veltos-qml"


def qml_hash(app_qml):
    """A short hash of every file below the app's QML folder (and of Qt's
    version: compiled QML is tied to it)."""
    digest = hashlib.sha1()
    try:
        from PySide6 import __version__ as qt_version
    except ImportError:
        qt_version = ""
    digest.update(qt_version.encode())
    for path in sorted(p for p in Path(app_qml).rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(app_qml)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def use_qml_cache(app_qml, cache=None):
    """Turns Qt's QML disk cache on in a folder for these exact QML files
    and removes this app's folders for older files. Returns the folder,
    or None when there is no QML folder."""
    app_qml = Path(app_qml)
    if not app_qml.is_dir():
        return None
    cache = Path(cache) if cache else cache_dir()
    name = app_qml.parent.name                        # veltos_calculator
    folder = cache / f"{name}-{qml_hash(app_qml)}"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        for old in cache.glob(f"{name}-*"):
            if old != folder:
                shutil.rmtree(old, ignore_errors=True)
    except OSError:
        return None
    os.environ["QML_DISK_CACHE_PATH"] = str(folder) + "/"
    os.environ.pop("QML_DISABLE_DISK_CACHE", None)
    return folder


def use(qml_dir=QML_DIR, plugin_dir=PLUGIN_DIR, app_qml=None):
    """Selects the style when it is installed and no other style was asked
    for (the tests' "Basic"), and the QML cache for the calling app's
    qml/ folder (next to the module that calls); returns whether the style
    was selected."""
    if app_qml is None:
        caller = sys._getframe(1).f_globals.get("__file__")
        app_qml = Path(caller).resolve().parent / "qml" if caller else None
    if os.environ.get("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop") not in ("org.kde.desktop", STYLE):
        return False
    if app_qml is not None:
        use_qml_cache(app_qml)
    if not os.path.isfile(os.path.join(qml_dir, *STYLE.split("."), "qmldir")):
        return False
    try:
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtQuickControls2 import QQuickStyle
    except ImportError:
        return False
    paths = [p for p in os.environ.get("QML_IMPORT_PATH", "").split(os.pathsep) if p]
    if qml_dir not in paths:
        os.environ["QML_IMPORT_PATH"] = os.pathsep.join([qml_dir, *paths])
    QCoreApplication.addLibraryPath(plugin_dir)
    QQuickStyle.setStyle(STYLE)
    return True
