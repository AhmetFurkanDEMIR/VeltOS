/*
    VeltOS Show desktop: the narrow area at the right end of the Windows 11
    taskbar, after the clock, reaching the screen's edge (the panel
    containment override drops Plasma's margin there). Clicking it shows
    the desktop; clicking again brings the windows back (KWin's "Show
    Desktop", the same as Meta+D). Settings > Personalization > Taskbar can
    switch it off ("Select the far corner of the taskbar to show the
    desktop"): a narrow empty end remains.

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
    toolTipMainText: Plasmoid.configuration.enabled ? i18n("Show desktop") : ""
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    fullRepresentation: MouseArea {
        id: area

        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        readonly property bool active: Plasmoid.configuration.enabled
        // A little wider than before (product owner, 2026-10-22), as easy
        // to hit as Windows 11's corner.
        readonly property int size: active ? Kirigami.Units.smallSpacing * 4 : Kirigami.Units.smallSpacing * 2
        Layout.minimumWidth: vertical ? -1 : size
        Layout.maximumWidth: vertical ? -1 : size
        Layout.minimumHeight: vertical ? size : -1
        Layout.maximumHeight: vertical ? size : -1
        Layout.fillHeight: !vertical
        Layout.fillWidth: vertical
        hoverEnabled: active
        onClicked: {
            if (active) {
                root.toggleDesktop();
            }
        }
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Show desktop")

        // A thin line on the side facing the clock, as on Windows 11.
        Rectangle {
            visible: area.active
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
            opacity: !area.active ? 0 : area.pressed ? 0.12 : (area.containsMouse ? 0.06 : 0)
        }
    }
}
