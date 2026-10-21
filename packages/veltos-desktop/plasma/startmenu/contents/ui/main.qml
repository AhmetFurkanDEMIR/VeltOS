/*
    VeltOS Start: a Windows 11 style application launcher for Plasma 6.

    Uses the same Plasma application, search and session models as KDE's
    Kickoff launcher (org.kde.plasma.private.kicker); only the layout is new.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.private.kicker as Kicker
import org.kde.plasma.private.sessions as Sessions
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    // Windows 11 flyouts float above the taskbar with all corners rounded.
    // Plasma does that for panel popups only while the panel itself floats
    // (its Panel.qml sets ContainmentPrefersFloatingApplets); the VeltOS
    // taskbar does not float, so the hint is kept set here. Panel.qml
    // clears it whenever its own state changes, hence the Connections.
    function floatPopups() {
        const c = Plasmoid.containment;
        if (c && !(c.containmentDisplayHints & PlasmaCore.Types.ContainmentPrefersFloatingApplets)) {
            c.containmentDisplayHints |= PlasmaCore.Types.ContainmentPrefersFloatingApplets;
        }
    }
    Connections {
        target: Plasmoid.containment
        function onContainmentDisplayHintsChanged() {
            root.floatPopups();
        }
    }

    readonly property Kicker.RootModel rootModel: Kicker.RootModel {
        autoPopulate: false
        appletInterface: root

        appNameFormat: 0 // name only
        flat: true
        sorted: true
        showSeparators: false
        showTopLevelItems: true

        // Row 0 is then always "All Applications".
        showAllApps: true
        showAllAppsCategorized: false
        showRecentApps: false
        showRecentDocs: false
        showPowerSession: false
        showFavoritesPlaceholder: false

        Component.onCompleted: {
            favoritesModel.initForClient("org.veltos.startmenu.favorites.instance-" + Plasmoid.id);
            if (!Plasmoid.configuration.favoritesPortedToKAstats) {
                if (favoritesModel.count < 1) {
                    favoritesModel.portOldFavorites(Plasmoid.configuration.favorites);
                }
                Plasmoid.configuration.favoritesPortedToKAstats = true;
            }
        }
    }

    readonly property Kicker.RecentUsageModel recentDocsModel: Kicker.RecentUsageModel {
        shownItems: Kicker.RecentUsageModel.OnlyDocs
        ordering: Kicker.RecentUsageModel.Recent
        favoritesModel: root.rootModel.favoritesModel
    }

    // The session/power model (Kicker.SystemModel) is created in StartMenu.qml
    // only after rootModel.refresh(): see the comment there.

    Plasmoid.icon: Plasmoid.configuration.icon
    preferredRepresentation: compactRepresentation
    fullRepresentation: StartMenu {
        plasmoidItem: root
        focus: true
    }

    // Taskbar button: the logo, with a rounded hover/pressed backdrop.
    compactRepresentation: MouseArea {
        id: button

        property bool wasExpanded: false

        Layout.minimumWidth: Plasmoid.formFactor === PlasmaCore.Types.Vertical ? -1 : height
        Layout.preferredWidth: Layout.minimumWidth
        Layout.minimumHeight: Plasmoid.formFactor === PlasmaCore.Types.Vertical ? width : -1
        Layout.preferredHeight: Layout.minimumHeight

        hoverEnabled: true
        Accessible.name: Plasmoid.title
        Accessible.role: Accessible.Button

        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: wasExpanded = root.expanded
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton) {
                root.expanded = false;
                quickLinks.openRelative();
            } else {
                root.expanded = !wasExpanded;
            }
        }

        // Right-clicking Start opens Windows 11's quick link menu (Windows +
        // X) with the VeltOS equivalents; nothing in it opens a KDE settings
        // window. The button opens it itself: the locked taskbar has no
        // menu of its own, and Plasma shows applet menus only through it.
        PlasmaExtras.Menu {
            id: quickLinks
            visualParent: button
            placement: PlasmaExtras.Menu.TopPosedLeftAlignedPopup

            PlasmaExtras.MenuItem {
                text: i18n("Installed apps")
                onClicked: root.run("veltos-settings apps")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Power Options")
                onClicked: root.run("veltos-settings power")
            }
            PlasmaExtras.MenuItem {
                text: i18n("System")
                onClicked: root.run("veltos-settings about")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Network Connections")
                onClicked: root.run("veltos-settings network")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Disk Management")
                onClicked: root.run("partitionmanager")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Terminal")
                onClicked: root.run("konsole --notransparency")
            }
            PlasmaExtras.MenuItem { separator: true }
            PlasmaExtras.MenuItem {
                text: i18n("Task Manager")
                onClicked: root.run("veltos-taskmanager")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Settings")
                onClicked: root.run("veltos-settings")
            }
            PlasmaExtras.MenuItem {
                text: i18n("File Explorer")
                onClicked: root.run("veltos-explorer")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Search")
                onClicked: root.expanded = true
            }
            PlasmaExtras.MenuItem { separator: true }
            PlasmaExtras.MenuItem {
                text: i18n("Sign out")
                visible: session.canLogout
                onClicked: session.requestLogout()
            }
            PlasmaExtras.MenuItem {
                text: i18n("Sleep")
                visible: session.canSuspend
                onClicked: session.suspend()
            }
            PlasmaExtras.MenuItem {
                text: i18n("Shut down")
                visible: session.canShutdown
                onClicked: session.requestShutdown()
            }
            PlasmaExtras.MenuItem {
                text: i18n("Restart")
                visible: session.canReboot
                onClicked: session.requestReboot()
            }
            PlasmaExtras.MenuItem { separator: true }
            PlasmaExtras.MenuItem {
                text: i18n("Desktop")
                onClicked: root.run("dbus-send --session --type=method_call --dest=org.kde.kglobalaccel "
                                      + "/component/kwin org.kde.kglobalaccel.Component.invokeShortcut "
                                      + "'string:Show Desktop'")
            }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: Math.round(Kirigami.Units.smallSpacing / 2)
            radius: Kirigami.Units.cornerRadius
            color: Kirigami.Theme.textColor
            opacity: button.pressed ? 0.16 : (button.containsMouse || root.expanded ? 0.09 : 0)
            Behavior on opacity {
                NumberAnimation { duration: Kirigami.Units.shortDuration }
            }
        }

        Kirigami.Icon {
            anchors.centerIn: parent
            width: Math.round(Math.min(parent.width, parent.height) * 0.74)
            height: width
            source: Plasmoid.icon
            scale: button.pressed ? 0.88 : 1
            Behavior on scale {
                NumberAnimation { duration: Kirigami.Units.shortDuration }
            }
        }
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }
    function run(command) {
        launcher.connectSource(command);
    }
    Sessions.SessionManagement {
        id: session
    }


    Component.onCompleted: {
        floatPopups();
        if (Plasmoid.hasOwnProperty("activationTogglesExpanded")) {
            Plasmoid.activationTogglesExpanded = true;
        }
    }
}
