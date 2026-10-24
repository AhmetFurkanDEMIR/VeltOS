// People: everyone you got mail from, most frequent first, with "Send
// email" (Outlook's People app in its simplest form).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: page

    color: Theme.card
    radius: Theme.cardRadius
    border.width: Theme.dark ? 0 : 1
    border.color: Theme.cardBorder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12
        Text {
            text: backend.text("people_title")
            color: Theme.text
            font.pixelSize: Math.round(20 * Theme.textScale)
            font.weight: Font.DemiBold
        }
        Text {
            visible: backend.people.length === 0
            text: backend.text("people_empty")
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
        }
        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            cellWidth: Math.max(240, Math.floor(width / Math.max(1, Math.floor(width / 260))))
            cellHeight: 76
            model: backend.people
            ScrollBar.vertical: ScrollBar {}
            delegate: Item {
                id: cell
                required property var modelData
                width: grid.cellWidth
                height: grid.cellHeight
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 4
                    radius: Theme.radius
                    color: cellHover.hovered ? Theme.hover : "transparent"
                    border.width: 1
                    border.color: Theme.cardBorder
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 12
                        Avatar { size: 40; initials: cell.modelData.initials; tint: cell.modelData.colour }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Text { Layout.fillWidth: true; text: cell.modelData.name; color: Theme.text
                                   font.pixelSize: Theme.fontSize; font.weight: Font.DemiBold; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: cell.modelData.address; color: Theme.subtext
                                   font.pixelSize: Theme.smallFont + 1; elide: Text.ElideRight }
                        }
                        FlatButton {
                            icon: "new-mail"; showText: false; tip: backend.text("send_email"); iconColour: Theme.brandText
                            onClicked: backend.newMail({ to: cell.modelData.address })
                        }
                    }
                    HoverHandler { id: cellHover }
                }
            }
        }
    }
}
