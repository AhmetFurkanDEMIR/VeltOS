// Windows 11 content dialog over the window: a card with the title and
// content, the buttons on a grey band at the bottom.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: dialog
    property string title: ""
    property alias buttons: buttonRow.data
    default property alias content: body.data

    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    focus: true
    padding: 0
    width: Math.min(520, (parent ? parent.width : 520) - 48)
    closePolicy: Popup.CloseOnEscape

    Overlay.modal: Rectangle { color: Theme.scrim }

    background: Rectangle {
        radius: Theme.radius
        color: Theme.card
        border.color: Theme.cardBorder
    }

    contentItem: ColumnLayout {
        spacing: 0
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 24
            spacing: 14
            Text {
                visible: dialog.title !== ""
                Layout.fillWidth: true
                text: dialog.title
                color: Theme.text
                font.pixelSize: 20
                font.weight: Font.DemiBold
                wrapMode: Text.Wrap
            }
            ColumnLayout {
                id: body
                Layout.fillWidth: true
                spacing: 10
            }
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 80
            color: Theme.window
            radius: Theme.radius
            Rectangle {      // square top corners of the band
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: Theme.radius
                color: Theme.window
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Theme.cardBorder
            }
            RowLayout {
                id: buttonRow
                anchors.fill: parent
                anchors.margins: 24
                spacing: 8
            }
        }
    }
}
