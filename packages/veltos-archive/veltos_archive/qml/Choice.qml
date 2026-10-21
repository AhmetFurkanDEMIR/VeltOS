// Windows 11 radio button or check box with its label.
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: choice
    property bool selected: false
    property bool checkbox: false
    implicitHeight: 28
    implicitWidth: row.implicitWidth
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.role: checkbox ? Accessible.CheckBox : Accessible.RadioButton
    Accessible.name: text
    Accessible.checked: selected
    background: Item {}
    contentItem: Row {
        id: row
        spacing: 10
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 20
            height: 20
            radius: choice.checkbox ? 4 : 10
            color: choice.selected ? Theme.accent : (choice.hovered ? Theme.controlHover : Theme.control)
            border.width: choice.selected ? 0 : 1
            border.color: Theme.subtext
            Rectangle {
                visible: choice.selected && !choice.checkbox
                anchors.centerIn: parent
                width: choice.hovered ? 10 : 8
                height: width
                radius: width / 2
                color: Theme.accentText
            }
            Text {
                visible: choice.selected && choice.checkbox
                anchors.centerIn: parent
                text: "✓"
                color: Theme.accentText
                font.pixelSize: 13
                font.weight: Font.Bold
            }
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: choice.text
            color: choice.enabled ? Theme.text : Theme.disabledText
            font.pixelSize: Theme.bodySize
        }
    }
}
