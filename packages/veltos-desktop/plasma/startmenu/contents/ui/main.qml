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
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

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

        onPressed: wasExpanded = root.expanded
        onClicked: root.expanded = !wasExpanded

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

    Kicker.ProcessRunner {
        id: processRunner
    }

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18n("Edit Applications…")
            icon.name: "kmenuedit"
            visible: Plasmoid.immutability !== PlasmaCore.Types.SystemImmutable
            onTriggered: processRunner.runMenuEditor()
        }
    ]

    Component.onCompleted: {
        if (Plasmoid.hasOwnProperty("activationTogglesExpanded")) {
            Plasmoid.activationTogglesExpanded = true;
        }
    }
}
