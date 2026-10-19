/*
    VeltOS Show desktop: the narrow area at the right end of the Windows 11
    taskbar, after the clock. Clicking it shows the desktop; clicking again
    brings the windows back (KWin's "Show Desktop", the same as Meta+D).

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

    function toggleDesktop() {
        launcher.connectSource("dbus-send --session --type=method_call --dest=org.kde.kglobalaccel "
                               + "/component/kwin org.kde.kglobalaccel.Component.invokeShortcut "
                               + "'string:Show Desktop'");
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    preferredRepresentation: fullRepresentation
    toolTipMainText: i18n("Show desktop")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    fullRepresentation: MouseArea {
        id: area

        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        Layout.minimumWidth: vertical ? -1 : Kirigami.Units.smallSpacing * 3
        Layout.maximumWidth: vertical ? -1 : Kirigami.Units.smallSpacing * 3
        Layout.minimumHeight: vertical ? Kirigami.Units.smallSpacing * 3 : -1
        Layout.maximumHeight: vertical ? Kirigami.Units.smallSpacing * 3 : -1
        Layout.fillHeight: !vertical
        Layout.fillWidth: vertical
        hoverEnabled: true
        onClicked: root.toggleDesktop()
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Show desktop")

        // A thin line on the side facing the clock, as on Windows 11.
        Rectangle {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: area.vertical ? parent.width * 0.6 : 1
            height: area.vertical ? 1 : parent.height * 0.5
            color: Kirigami.Theme.textColor
            opacity: area.containsMouse ? 0.45 : 0.25
        }
        Rectangle {
            anchors.fill: parent
            color: Kirigami.Theme.textColor
            opacity: area.pressed ? 0.12 : (area.containsMouse ? 0.06 : 0)
        }
    }
}
