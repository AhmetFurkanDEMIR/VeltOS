// One of the "Weather details" cards: a small glyph and title, then the
// card's own content.
import QtQuick
import QtQuick.Layouts
import "."

Card {
    id: card
    property string title
    property string glyph
    default property alias content: body.data
    implicitHeight: 212
    Layout.fillWidth: true
    Layout.preferredHeight: implicitHeight

    RowLayout {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 8
        Glyph { name: card.glyph; tint: Theme.subtext }
        Text {
            Layout.fillWidth: true
            text: card.title
            color: Theme.subtext
            font.pixelSize: Theme.captionSize + 1
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
    }
    Item {
        id: body
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: parent.bottom
        anchors.margins: 16
        anchors.topMargin: 10
    }
}
