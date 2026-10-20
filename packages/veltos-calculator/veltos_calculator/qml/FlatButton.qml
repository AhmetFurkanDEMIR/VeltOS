// A flat Windows 11 button: memory keys (MC MR M+ M− MS M˅), DEG and
// F-E, the title bar icons and the list buttons. Text, a glyph or both.
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: button
    property string label: ""
    property string glyph: ""
    property string tip: ""
    property bool on: false
    property bool bold: false
    property bool glyphAfter: false         // "Trigonometry ⌄", "M⌄"
    property int labelSize: Theme.captionSize
    property color ink: !enabled ? Theme.disabledText : (on ? Theme.accent : (down ? Theme.subtext : Theme.text))

    implicitWidth: Math.max(36, content.implicitWidth + 20)
    implicitHeight: 32
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    Accessible.name: tip !== "" ? tip : label

    ToolTip.visible: tip !== "" && hovered
    ToolTip.delay: 600
    ToolTip.text: tip

    background: Rectangle {
        radius: Theme.keyRadius
        color: button.down ? Theme.pressed : (button.hovered && button.enabled ? Theme.hover : "transparent")
        Behavior on color { ColorAnimation { duration: 83 } }
    }
    contentItem: Item {
        implicitWidth: content.implicitWidth
        implicitHeight: content.implicitHeight
        Row {
            id: content
            anchors.centerIn: parent
            spacing: button.glyphAfter ? 2 : 6
            layoutDirection: button.glyphAfter ? Qt.RightToLeft : Qt.LeftToRight
            Glyph {
                visible: button.glyph !== ""
                anchors.verticalCenter: parent.verticalCenter
                width: button.glyphAfter ? 12 : 16
                height: width
                kind: button.glyph
                color: button.ink
            }
            Text {
                visible: button.label !== ""
                anchors.verticalCenter: parent.verticalCenter
                text: button.label
                textFormat: Text.RichText
                color: button.ink
                font.pixelSize: button.labelSize
                font.weight: button.bold ? Font.DemiBold : Font.Normal
            }
        }
    }
}
