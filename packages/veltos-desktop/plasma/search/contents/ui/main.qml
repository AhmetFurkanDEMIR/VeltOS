/*
    VeltOS Search: the search box of the Windows 11 taskbar. It opens the
    VeltOS Start menu, which searches apps and settings as soon as you type.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

    // Plasma's own D-Bus call for "open the application launcher" (the
    // Meta key does the same).
    function openStart() {
        launcher.connectSource("dbus-send --session --type=method_call --dest=org.kde.plasmashell "
                               + "/PlasmaShell org.kde.PlasmaShell.activateLauncherMenu");
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    preferredRepresentation: fullRepresentation
    toolTipMainText: i18n("Search")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    fullRepresentation: MouseArea {
        id: box

        Layout.minimumWidth: root.vertical ? -1 : (compact ? height : Kirigami.Units.gridUnit * 11)
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.fillHeight: true
        // On a vertical or crowded taskbar only the magnifier, like Windows.
        readonly property bool compact: root.vertical
        hoverEnabled: true
        onClicked: root.openStart()
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Search")

        Rectangle {
            id: pill
            anchors.centerIn: parent
            width: box.compact ? Math.min(parent.width, parent.height) - Kirigami.Units.smallSpacing * 2
                               : parent.width - Kirigami.Units.smallSpacing * 2
            height: Math.min(parent.height - Kirigami.Units.smallSpacing * 3, Kirigami.Units.gridUnit * 2)
            radius: height / 2
            color: Kirigami.Theme.backgroundColor
            opacity: box.containsMouse ? 1 : 0.82
            border.width: 1
            border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                  Kirigami.Theme.textColor.b, box.containsMouse ? 0.18 : 0.1)
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        RowLayout {
            anchors.fill: pill
            anchors.leftMargin: box.compact ? 0 : Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing * 2

            Kirigami.Icon {
                Layout.alignment: box.compact ? Qt.AlignCenter : Qt.AlignVCenter
                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                Layout.preferredHeight: Kirigami.Units.iconSizes.small
                source: "search"
                color: Kirigami.Theme.textColor
                isMask: true
            }
            PlasmaComponents3.Label {
                visible: !box.compact
                Layout.fillWidth: true
                text: i18n("Search")
                opacity: 0.7
                elide: Text.ElideRight
            }
        }
    }
}
