// Windows 11 button: accent (filled) or standard (light with a border).
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: button
    property bool accent: false
    property string iconName: ""
    implicitWidth: Math.max(96, label.implicitWidth + 32)
    implicitHeight: 32
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text

    background: Rectangle {
        radius: Theme.smallRadius
        color: button.accent
               ? (button.down ? Qt.darker(Theme.accent, 1.12) : (button.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent))
               : (button.down ? Theme.window : (button.hovered ? Theme.controlHover : Theme.control))
        border.width: button.accent ? 0 : 1
        border.color: Theme.cardBorder
        opacity: button.enabled ? 1 : 0.5
        Rectangle {
            visible: button.visualFocus
            anchors.fill: parent
            anchors.margins: -3
            radius: Theme.smallRadius + 2
            color: "transparent"
            border.width: 2
            border.color: Theme.text
        }
    }
    contentItem: Text {
        id: label
        text: button.text
        color: button.accent ? Theme.accentText : Theme.text
        font.pixelSize: Theme.bodySize
        font.weight: button.accent ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
