// "Find a setting" box of the navigation pane.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: box

    property alias text: input.text
    property string placeholder

    implicitHeight: 38
    radius: 6
    color: Theme.card
    border.width: 1
    border.color: input.activeFocus ? Theme.accent : Theme.cardBorder

    Rectangle {
        // Windows-style accent underline while typing.
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: 2
        radius: 1
        color: Theme.accent
        visible: input.activeFocus
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 8
        spacing: 8

        TextInput {
            id: input
            // Like a Windows text box: in the Tab order, the text cursor over it and
            // (in a layout) the full height of its box. A plain TextInput has neither.
            activeFocusOnTab: true
            HoverHandler { cursorShape: Qt.IBeamCursor }
            Layout.fillHeight: true
            verticalAlignment: TextInput.AlignVCenter
            Layout.fillWidth: true
            color: Theme.text
            selectionColor: Theme.accent
            selectedTextColor: "#FFFFFF"
            font.pixelSize: 14
            clip: true
            Accessible.role: Accessible.EditableText
            Accessible.name: box.placeholder
            Keys.onEscapePressed: text = ""

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: box.placeholder
                color: Theme.subtext
                font.pixelSize: 14
                visible: input.text.length === 0
            }
        }
        Kirigami.Icon {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            source: input.text.length > 0 ? "edit-clear" : "search"
            color: Theme.subtext
            isMask: true
            TapHandler { onTapped: input.text = "" }
        }
    }
}
