/*
    Settings > Display > Identify: the display's number in a box at its
    bottom left for a moment, as Windows shows it. One window per display
    (project.run_identify), a layer-shell surface that takes no input.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Window
import org.kde.layershell as LayerShell

Window {
    id: badge
    property int number: 1
    width: 180
    height: 180
    visible: false
    color: "transparent"
    flags: Qt.WindowTransparentForInput

    LayerShell.Window.anchors: LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    // 0: placed next to the taskbar, not over it.
    LayerShell.Window.exclusionZone: 0
    LayerShell.Window.scope: "veltos-identify"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 24
        radius: 8
        color: "#E6101218"
        border.width: 1
        border.color: "#40FFFFFF"
        Text {
            anchors.centerIn: parent
            text: badge.number
            color: "#FFFFFF"
            font.pixelSize: 84
            font.weight: Font.DemiBold
        }
    }
}
