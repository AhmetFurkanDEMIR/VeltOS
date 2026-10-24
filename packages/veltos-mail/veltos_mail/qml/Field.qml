// A Fluent text field: white box, light border, the accent line under it
// while it has focus.
import QtQuick
import QtQuick.Controls
import "."

Rectangle {
    id: field

    property alias text: input.text
    property alias placeholder: hint.text
    property alias echoMode: input.echoMode
    property alias input: input
    property bool error: false
    signal accepted()

    implicitWidth: 320
    implicitHeight: Math.round(32 * Theme.textScale)
    radius: Theme.radius
    color: Theme.field
    border.width: 1
    border.color: error ? Theme.danger : (input.activeFocus ? Theme.fieldBorder : Theme.fieldBorder)

    function forceActiveFocus() { input.forceActiveFocus(); }

    TextInput {
        id: input
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        verticalAlignment: TextInput.AlignVCenter
        color: Theme.text
        selectionColor: Theme.brand
        selectedTextColor: "#FFFFFF"
        font.pixelSize: Theme.fontSize
        clip: true
        selectByMouse: true
        onAccepted: field.accepted()
    }
    Text {
        id: hint
        anchors.fill: input
        verticalAlignment: Text.AlignVCenter
        visible: input.text === "" && !input.inputMethodComposing
        color: Theme.tertiary
        font.pixelSize: Theme.fontSize
        elide: Text.ElideRight
    }
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 1
        height: input.activeFocus ? 2 : 1
        radius: 1
        color: field.error ? Theme.danger : (input.activeFocus ? Theme.brand : Theme.fieldUnderline)
        Behavior on height { enabled: Theme.anim > 0; NumberAnimation { duration: 90 } }
    }
}
