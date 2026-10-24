// Outlook's app bar on the left edge: Mail, Calendar and People, each an
// icon over its name; the open one in the brand colour with a filled icon
// and a bar at its left.
import QtQuick
import QtQuick.Layouts
import "."

ColumnLayout {
    id: rail

    property string current: "mail"
    signal chosen(string page)

    spacing: 2

    Repeater {
        model: [{ page: "mail", icon: "mail", label: "rail_mail" },
                { page: "calendar", icon: "calendar", label: "rail_calendar" },
                { page: "people", icon: "people", label: "rail_people" }]
        delegate: Rectangle {
            id: entry
            required property var modelData
            readonly property bool selected: rail.current === modelData.page
            Layout.preferredWidth: 60
            Layout.preferredHeight: 56
            Layout.alignment: Qt.AlignHCenter
            radius: Theme.radius
            color: entryTap.pressed ? Theme.pressed : (entryHover.hovered ? Theme.hoverCanvas : "transparent")
            Accessible.role: Accessible.Button
            Accessible.name: backend.text(modelData.label)
            Rectangle {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: 3
                height: entry.selected ? 18 : 0
                radius: 1.5
                color: Theme.brand
                Behavior on height { enabled: Theme.anim > 0; NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            }
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 3
                Glyph {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    kind: entry.modelData.icon
                    filled: entry.selected
                    color: entry.selected ? Theme.brandText : Theme.subtext
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: backend.text(entry.modelData.label)
                    color: entry.selected ? Theme.brandText : Theme.subtext
                    font.pixelSize: Theme.captionFont
                    font.weight: entry.selected ? Font.DemiBold : Font.Normal
                }
            }
            HoverHandler { id: entryHover }
            TapHandler { id: entryTap; onTapped: rail.chosen(entry.modelData.page) }
        }
    }
    Item { Layout.fillHeight: true }
}
