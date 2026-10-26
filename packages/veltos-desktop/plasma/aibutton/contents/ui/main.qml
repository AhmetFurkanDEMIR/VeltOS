/*
    VeltOS AI button: Windows 11's Copilot button at the right end of the
    taskbar (product owner, 2026-10-26). A click opens or closes the VeltOS
    AI pane (veltos-ai toggles a running pane, the same as Windows + C).
    The right-click menu hides the button (Settings > Personalization >
    Taskbar > VeltOS AI shows it again) or opens VeltOS AI's settings.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    function run(command) {
        launcher.connectSource(command + " #" + Date.now());
    }

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    preferredRepresentation: fullRepresentation
    toolTipMainText: i18n("VeltOS AI")
    toolTipSubText: i18n("Ask VeltOS AI (Windows + C)")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    fullRepresentation: MouseArea {
        id: button

        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        // Settings > Personalization > Taskbar > VeltOS AI. Hidden by zero
        // size, clipped and disabled: Plasma makes a panel applet visible
        // again whenever it places it (AGENTS.md).
        readonly property bool shown: Plasmoid.configuration.shown
        Layout.minimumWidth: !shown ? 0 : vertical ? -1 : height
        Layout.minimumHeight: !shown ? 0 : vertical ? width : -1
        Layout.maximumWidth: Layout.minimumWidth
        Layout.maximumHeight: Layout.minimumHeight
        clip: true
        opacity: shown ? 1 : 0
        enabled: shown
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton)
                menu.openRelative();
            else
                root.run("veltos-ai");
        }
        Accessible.role: Accessible.Button
        Accessible.name: i18n("VeltOS AI")

        Rectangle {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            radius: Kirigami.Units.cornerRadius
            // The taskbar's see-through highlight (as Task View and Quick
            // Settings).
            readonly property bool darkTheme: Kirigami.ColorUtils.brightnessForColor(
                Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
            color: darkTheme ? Qt.rgba(1, 1, 1, button.pressed ? 0.05 : 0.09)
                             : Qt.rgba(1, 1, 1, button.pressed ? 0.38 : 0.62)
            border.width: 1
            border.color: darkTheme ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(0, 0, 0, 0.05)
            opacity: button.pressed || button.containsMouse ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        Kirigami.Icon {
            anchors.centerIn: parent
            width: Kirigami.Units.iconSizes.smallMedium
            height: width
            source: "veltos-ai"
            active: button.containsMouse
            // A small press, like Windows 11's taskbar icons.
            scale: button.pressed ? 0.88 : 1
            Behavior on scale { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        PlasmaExtras.Menu {
            id: menu
            visualParent: button
            placement: PlasmaExtras.Menu.TopPosedRightAlignedPopup

            PlasmaExtras.MenuItem {
                text: i18n("VeltOS AI settings")
                icon: "configure"
                onClicked: root.run("veltos-settings veltosai")
            }
            PlasmaExtras.MenuItem {
                text: i18n("Hide from taskbar")
                icon: "view-hidden"
                onClicked: Plasmoid.configuration.shown = false
            }
        }
    }
}
