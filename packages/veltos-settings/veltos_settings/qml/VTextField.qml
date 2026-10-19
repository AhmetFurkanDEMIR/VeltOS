// Windows 11 text box with an accent underline while typing; `password`
// hides the text and adds a "show" button.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: field

    property alias text: input.text
    property string placeholder
    property bool password: false
    property bool revealed: false
    signal accepted()

    function focusInput() {
        input.forceActiveFocus();
    }

    implicitWidth: 280
    implicitHeight: 34
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

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 11
        anchors.rightMargin: 6
        spacing: 6

        TextInput {
            id: input
            Layout.fillWidth: true
            color: Theme.text
            selectionColor: Theme.accent
            selectedTextColor: "#FFFFFF"
            font.pixelSize: 13
            clip: true
            echoMode: field.password && !field.revealed ? TextInput.Password : TextInput.Normal
            Accessible.role: Accessible.EditableText
            Accessible.name: field.placeholder
            Accessible.passwordEdit: field.password
            onAccepted: field.accepted()

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: field.placeholder
                color: Theme.subtext
                font.pixelSize: 13
                visible: input.text.length === 0
            }
        }
        Rectangle {
            visible: field.password && input.text.length > 0
            Layout.preferredWidth: 26
            Layout.preferredHeight: 24
            radius: 4
            color: revealHover.hovered ? Theme.navHover : "transparent"
            Accessible.role: Accessible.Button
            Accessible.name: backend.text("show_key")
            Kirigami.Icon {
                anchors.centerIn: parent
                width: 16
                height: 16
                source: "view-visible"
                color: Theme.subtext
                isMask: true
            }
            HoverHandler { id: revealHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onPressedChanged: field.revealed = pressed }
        }
    }
}
