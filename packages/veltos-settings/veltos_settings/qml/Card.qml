// A rounded panel that groups content on a page.
import QtQuick
import "."

Rectangle {
    default property alias content: holder.data
    property int padding: 20

    implicitHeight: holder.childrenRect.height + 2 * padding
    radius: Theme.radius
    color: Theme.card
    border.width: 1
    border.color: Theme.cardBorder

    Item {
        id: holder
        anchors.fill: parent
        anchors.margins: parent.padding
    }
}
