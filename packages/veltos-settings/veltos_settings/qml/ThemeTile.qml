// A theme as Windows 11 shows it: the wallpaper with a small window in the
// lower right corner (light or dark) that carries an accent-coloured bar.
// Clicking applies the theme (wallpaper, mode and accent colour).
import QtQuick
import QtQuick.Controls
import "."

Rectangle {
    id: tile

    required property var theme
    readonly property bool chosen: backend.currentTheme === theme.id

    implicitWidth: 112
    implicitHeight: 90
    radius: 6
    color: "transparent"
    border.width: chosen || activeFocus ? 3 : (hover.hovered ? 1 : 0)
    border.color: chosen || activeFocus ? Theme.accent : Theme.cardBorder
    activeFocusOnTab: true
    Accessible.role: Accessible.RadioButton
    Accessible.name: theme.title
    Accessible.checked: chosen
    Accessible.onPressAction: backend.applyTheme(theme.id)
    Keys.onReturnPressed: backend.applyTheme(theme.id)
    Keys.onSpacePressed: backend.applyTheme(theme.id)

    Rectangle {
        id: frame
        anchors.fill: parent
        anchors.margins: tile.chosen || tile.activeFocus ? 4 : 0
        radius: 4
        clip: true
        color: tile.theme.dark ? "#0E1846" : "#CFE0FF"

        Image {
            anchors.fill: parent
            source: tile.theme.preview
            fillMode: Image.PreserveAspectCrop
            sourceSize.width: 240
            asynchronous: true
        }
        // The window: light or dark, with the accent colour.
        Rectangle {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: parent.width * 0.07
            anchors.bottomMargin: parent.height * 0.1
            width: parent.width * 0.36
            height: parent.height * 0.44
            radius: 3
            color: tile.theme.dark ? "#202230" : "#F7F8FB"
            opacity: 0.94
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.2
                width: parent.width * 0.5
                height: Math.max(4, parent.height * 0.16)
                radius: 2
                color: tile.theme.accent
            }
        }
    }

    ToolTip.visible: hover.hovered
    ToolTip.delay: 600
    ToolTip.text: theme.title

    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: backend.applyTheme(tile.theme.id) }
}
