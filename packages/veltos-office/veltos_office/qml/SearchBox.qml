// A Windows 11 search box: rounded field, magnifier, placeholder, an
// accent line under it while it has focus.
import QtQuick
import "."

Rectangle {
    id: box

    property string placeholder: backend.text("search")
    property alias text: input.text
    signal accepted()

    implicitWidth: 240
    implicitHeight: Math.round(32 * Theme.textScale)
    radius: Theme.radius
    color: Theme.field
    border.width: 1
    border.color: input.activeFocus ? Theme.accent : Theme.fieldBorder

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: 2
        radius: 1
        color: Theme.accent
        opacity: input.activeFocus ? 1 : 0
        Behavior on opacity { enabled: Theme.anim > 0; NumberAnimation { duration: 120 } }
    }

    Glyph {
        id: icon
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        width: 15
        height: 15
        kind: "search"
        color: Theme.subtext
    }

    TextInput {
        id: input
        anchors.left: icon.right
        anchors.right: clear.visible ? clear.left : parent.right
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        color: Theme.text
        font.pixelSize: Theme.fontSize
        selectByMouse: true
        selectionColor: Theme.accent
        clip: true
        onAccepted: box.accepted()
        Text {
            anchors.fill: parent
            text: box.placeholder
            color: Theme.subtext
            font: input.font
            visible: !input.text && !input.activeFocus
            verticalAlignment: Text.AlignVCenter
        }
    }

    Rectangle {
        id: clear
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        width: 24
        height: 24
        radius: 4
        visible: input.text !== ""
        color: clearHover.hovered ? Theme.hover : "transparent"
        Glyph {
            anchors.centerIn: parent
            width: 8
            height: 8
            kind: "close"
            color: Theme.subtext
        }
        HoverHandler { id: clearHover }
        TapHandler { onTapped: { input.text = ""; input.forceActiveFocus(); } }
    }

    TapHandler {
        onTapped: input.forceActiveFocus()
    }
}
