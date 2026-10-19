/*
    VeltOS Task View: the Windows 11 taskbar button that shows every open
    window and the virtual desktops. It starts KWin's Overview effect (the
    same as Meta+W).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    function showOverview() {
        launcher.connectSource("dbus-send --session --type=method_call --dest=org.kde.kglobalaccel "
                               + "/component/kwin org.kde.kglobalaccel.Component.invokeShortcut "
                               + "string:Overview");
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    preferredRepresentation: fullRepresentation
    toolTipMainText: i18n("Task View")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    fullRepresentation: MouseArea {
        id: button

        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        Layout.minimumWidth: vertical ? -1 : height
        Layout.minimumHeight: vertical ? width : -1
        Layout.maximumWidth: Layout.minimumWidth
        Layout.maximumHeight: Layout.minimumHeight
        hoverEnabled: true
        onClicked: root.showOverview()
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Task View")

        Rectangle {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            radius: Kirigami.Units.cornerRadius
            color: Kirigami.Theme.textColor
            opacity: button.pressed ? 0.12 : (button.containsMouse ? 0.07 : 0)
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        // Two overlapping windows, drawn so they follow the text colour.
        Item {
            anchors.centerIn: parent
            width: Kirigami.Units.iconSizes.smallMedium
            height: width

            Rectangle {
                x: width * 0.32
                y: 0
                width: parent.width * 0.68
                height: parent.height * 0.6
                radius: 2
                color: "transparent"
                border.width: 1.5
                border.color: Kirigami.Theme.textColor
                opacity: 0.55
            }
            Rectangle {
                x: 0
                y: parent.height * 0.32
                width: parent.width * 0.74
                height: parent.height * 0.62
                radius: 2
                color: Kirigami.Theme.backgroundColor
                border.width: 1.5
                border.color: Kirigami.Theme.textColor
            }
        }
    }
}
