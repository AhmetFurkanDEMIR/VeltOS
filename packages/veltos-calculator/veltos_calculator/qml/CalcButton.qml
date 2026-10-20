// A key of the Windows 11 Calculator keypad: digits ("number") are
// lighter than operators and functions ("operator"), "=" is filled with
// the accent colour ("accent"); "toggle" keys (2nd, hyp) are filled when
// on. The label is styled text so that x², ʸ√x and 10ˣ can be written.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

AbstractButton {
    id: key
    property string kind: "operator"
    property string label: ""
    property string glyph: ""
    property bool on: false
    property int labelSize: kind === "number" ? 20 : 16

    readonly property bool filled: kind === "accent" || on
    readonly property color face: filled
        ? (down ? Qt.darker(Theme.accent, 1.12) : (hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent))
        : kind === "number"
          ? (down ? Theme.numberPressed : (hovered ? Theme.numberHover : Theme.number))
          : (down ? Theme.operatorPressed : (hovered ? Theme.operatorHover : Theme.operator))
    readonly property color ink: filled ? Theme.accentText
                                        : (down ? Theme.subtext : (enabled ? Theme.text : Theme.disabledText))

    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumHeight: 32
    implicitWidth: 76
    implicitHeight: 48
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    Accessible.name: text !== "" ? text : label

    background: Rectangle {
        radius: Theme.keyRadius
        color: key.face
        border.width: 1
        border.color: key.filled ? Qt.darker(Theme.accent, 1.1) : Theme.keyBorder
        Behavior on color { ColorAnimation { duration: 83 } }
        // Windows 11 controls are a little darker along the bottom edge.
        Rectangle {
            visible: !key.filled
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: Theme.keyRadius
            anchors.rightMargin: Theme.keyRadius
            height: 1
            color: Theme.keyShade
        }
    }

    contentItem: Item {
        Text {
            anchors.centerIn: parent
            visible: key.glyph === ""
            text: key.label
            textFormat: Text.RichText
            color: key.ink
            font.pixelSize: key.labelSize
            font.weight: key.kind === "number" ? Font.DemiBold : Font.Normal
        }
        Glyph {
            anchors.centerIn: parent
            visible: key.glyph !== ""
            width: 20
            height: 20
            kind: key.glyph
            color: key.ink
        }
    }
}
