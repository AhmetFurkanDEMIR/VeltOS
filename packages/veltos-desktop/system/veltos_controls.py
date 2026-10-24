"""VeltOS' Qt Quick Controls style for VeltOS' apps: Windows 11 scroll bars
over KDE's Breeze (qml/org/veltos/controls, installed by veltos-desktop).

KDE's platform theme gives every QGuiApplication the org.kde.breeze style
whatever QT_QUICK_CONTROLS_STYLE says (plasma-integration
KdePlatformTheme::setQtQuickControlsTheme), and Breeze draws a separator
line beside every scroll bar. An app calls use() right after creating its
QGuiApplication, before loading QML:

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

import os

QML_DIR = "/usr/share/veltos/qml"
PLUGIN_DIR = "/usr/share/veltos/qt-plugins"
STYLE = "org.veltos.controls"


def use(qml_dir=QML_DIR, plugin_dir=PLUGIN_DIR):
    """Selects the style when it is installed and no other style was asked
    for (the tests' "Basic"); returns whether it did."""
    if os.environ.get("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop") not in ("org.kde.desktop", STYLE):
        return False
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
