// Windows 11 button: accent (filled) or standard (light with a border),
// with an optional glyph before the text ("+ New").
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: button
    property bool accent: false
    property string glyph: ""
    implicitWidth: Math.max(80, content.implicitWidth + 28)
    implicitHeight: 32
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text
    Keys.onReturnPressed: clicked()
    Keys.onEnterPressed: clicked()

    background: Rectangle {
        radius: Theme.smallRadius
        color: button.accent
               ? (button.down ? Qt.darker(Theme.accent, 1.12) : (button.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent))
               : (button.down ? Theme.window : (button.hovered ? Theme.controlHover : Theme.control))
        border.width: button.accent ? 0 : 1
        border.color: Theme.cardBorder
        opacity: button.enabled ? 1 : 0.5
        Behavior on color { ColorAnimation { duration: 83 } }
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
    contentItem: Item {
        implicitWidth: content.implicitWidth
        implicitHeight: content.implicitHeight
        Row {
            id: content
            anchors.centerIn: parent
            spacing: 6
            Glyph {
                visible: button.glyph !== ""
                anchors.verticalCenter: parent.verticalCenter
                width: 16
                height: 16
                kind: button.glyph
                color: button.accent ? Theme.accentText : Theme.text
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: button.text
                color: button.accent ? Theme.accentText : Theme.text
                font.pixelSize: Theme.bodySize
                font.weight: button.accent ? Font.DemiBold : Font.Normal
            }
        }
    }
}
