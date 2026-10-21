// Windows 11 text box: a thin border with an accent line under it when
// focused.
import QtQuick
import QtQuick.Controls

TextField {
    id: field
    implicitHeight: 32
    leftPadding: 10
    rightPadding: 10
    color: Theme.text
    placeholderTextColor: Theme.subtext
    selectionColor: Theme.accent
    selectedTextColor: Theme.accentText
    font.pixelSize: Theme.bodySize
    background: Rectangle {
        radius: Theme.smallRadius
        color: field.activeFocus ? Theme.card : Theme.control
        border.color: Theme.cardBorder
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            height: field.activeFocus ? 2 : 1
            radius: 1
            color: field.activeFocus ? Theme.accent : Theme.subtext
            opacity: field.activeFocus ? 1 : 0.5
        }
    }
}
