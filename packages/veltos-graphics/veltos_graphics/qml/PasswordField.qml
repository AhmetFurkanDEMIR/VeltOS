// Windows 11 password box with an accent underline while typing.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: field

    property alias text: input.text
    property string placeholder
    signal accepted()

    implicitWidth: 260
    implicitHeight: Math.round(34 * Theme.textScale)
    radius: 5
    color: input.activeFocus ? Theme.card : Theme.control
    border.width: 1
    border.color: Theme.cardBorder
    clip: true

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: input.activeFocus ? 2 : 1
        color: input.activeFocus ? Theme.accent : Theme.subtext
        opacity: input.activeFocus ? 1 : 0.6
    }

    TextInput {
        id: input
        anchors.fill: parent
        anchors.leftMargin: 11
        anchors.rightMargin: 11
        verticalAlignment: TextInput.AlignVCenter
        activeFocusOnTab: true
        color: Theme.text
        selectionColor: Theme.accent
        selectedTextColor: "#FFFFFF"
        font.pixelSize: Theme.bodySize + 1
        clip: true
        echoMode: TextInput.Password
        Accessible.role: Accessible.EditableText
        Accessible.name: field.placeholder
        Accessible.passwordEdit: true
        onAccepted: field.accepted()
        HoverHandler { cursorShape: Qt.IBeamCursor }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: field.placeholder
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
            visible: input.text.length === 0
        }
    }
}
