// Outlook's folder pane: Favorites (Inbox, Sent Items, Drafts), then each
// account with its folders (collapsible), unread counts in the brand
// colour, the open folder on a grey background in bold, and "Add account".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: pane

    signal addAccount()

    ListView {
        id: list
        anchors.fill: parent
        anchors.topMargin: 4
        clip: true
        spacing: 1
        boundsBehavior: Flickable.StopAtBounds
        model: backend.folderTree
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        delegate: Item {
            id: row
            required property var modelData
            width: list.width
            height: modelData.kind === "section" ? 36 : 32

            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 8
                radius: Theme.radius
                color: row.modelData.current ? Theme.selectedFolder
                       : (rowHover.hovered ? Theme.hoverCanvas : "transparent")
                Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 80 } }
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12 + (row.modelData.kind === "folder" ? 14 + row.modelData.depth * 14 : 0)
                anchors.rightMargin: 18
                spacing: 8

                Glyph {
                    visible: row.modelData.kind === "section"
                    Layout.preferredWidth: 12
                    Layout.preferredHeight: 12
                    kind: row.modelData.collapsed ? "chevron-right" : "chevron-down"
                    color: Theme.subtext
                }
                Glyph {
                    visible: row.modelData.kind !== "section"
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18
                    kind: row.modelData.kind === "add" ? "add" : (row.modelData.icon || "folder")
                    color: row.modelData.kind === "add" ? Theme.brandText : Theme.text
                }
                Text {
                    Layout.fillWidth: true
                    text: row.modelData.label
                    color: row.modelData.kind === "add" ? Theme.brandText : Theme.text
                    font.pixelSize: row.modelData.kind === "section" ? Theme.fontSize : Theme.fontSize
                    font.weight: row.modelData.kind === "section" || row.modelData.current
                                 || (row.modelData.unread || 0) > 0 ? Font.DemiBold : Font.Normal
                    elide: Text.ElideRight
                }
                // An account's state: signing in / syncing / error.
                Glyph {
                    visible: row.modelData.kind === "section" && (row.modelData.state || "").indexOf("error") === 0
                    Layout.preferredWidth: 14
                    Layout.preferredHeight: 14
                    kind: "warning"
                    color: Theme.danger
                }
                Text {
                    readonly property int count: row.modelData.showTotal ? (row.modelData.total || 0) : (row.modelData.unread || 0)
                    visible: row.modelData.kind === "folder" && count > 0
                    text: count
                    color: row.modelData.showTotal ? Theme.subtext : Theme.brandText
                    font.pixelSize: Theme.smallFont + 1
                    font.weight: Font.DemiBold
                }
            }

            HoverHandler { id: rowHover }
            TapHandler {
                onTapped: {
                    const r = row.modelData;
                    if (r.kind === "section")
                        backend.toggleSection(r.key);
                    else if (r.kind === "add")
                        pane.addAccount();
                    else
                        backend.selectFolder(r.account, r.folder);
                }
            }
            Accessible.role: row.modelData.kind === "folder" ? Accessible.ListItem : Accessible.Button
            Accessible.name: row.modelData.label + (row.modelData.unread ? ", " + row.modelData.unread : "")
        }
    }
}
