// Navigation pane: Home, the pinned folders, This PC (with its drives) and
// the Recycle Bin, as in Windows 11 File Explorer.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: pane

    readonly property var tab: backend.current
    property bool pcExpanded: true
    signal contextMenu(var item, var entry, real x, real y)

    color: Theme.pane

    component NavRow: Rectangle {
        id: row

        property string icon
        property string text
        property string location
        property bool pinned: false
        property bool expandable: false
        property bool expanded: false
        property int indent: 0
        property string device          // drives: opened (and mounted) by device
        readonly property bool current: pane.tab.location === location && pane.tab.query === ""
        signal toggled()
        signal menuRequested(real x, real y)

        Layout.fillWidth: true
        Layout.leftMargin: 6
        Layout.rightMargin: 6
        implicitHeight: 30
        radius: 4
        color: current ? Theme.selected : (rowHover.hovered ? Theme.hover : "transparent")
        Accessible.role: Accessible.Button
        Accessible.name: text

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4 + row.indent
            anchors.rightMargin: 8
            spacing: 6
            Item {
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Kirigami.Icon {
                    anchors.fill: parent
                    anchors.margins: 3
                    visible: row.expandable
                    source: row.expanded ? "arrow-down" : "arrow-right"
                    color: Theme.subtext
                    isMask: true
                }
                TapHandler { enabled: row.expandable; onTapped: row.toggled() }
            }
            Kirigami.Icon {
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
                source: row.icon
            }
            Text {
                Layout.fillWidth: true
                text: row.text
                color: Theme.text
                font.pixelSize: Theme.fontSize
                elide: Text.ElideRight
            }
            Glyph {
                visible: row.pinned
                Layout.preferredWidth: 14
                Layout.preferredHeight: 14
                kind: "pin"
                color: Theme.subtext
            }
        }

        HoverHandler { id: rowHover }
        TapHandler {
            acceptedButtons: Qt.LeftButton
            onTapped: {
                if (row.device !== "")
                    backend.openDrive(row.device);
                else
                    backend.open(row.location);
            }
        }
        TapHandler {
            acceptedButtons: Qt.MiddleButton
            onTapped: backend.openInNewTab(row.location)
        }
        TapHandler {
            acceptedButtons: Qt.RightButton
            onTapped: point => row.menuRequested(point.position.x, point.position.y)
        }
        DropArea {
            anchors.fill: parent
            enabled: row.location.startsWith("/") || row.location === "trash:"
            onDropped: drop => {
                if (drop.hasUrls) {
                    if (row.location === "trash:")
                        backend.dropToTrash(drop.urls);
                    else
                        backend.drop(drop.urls, row.location);
                    drop.accept();
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.topMargin: 6
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: pane.width
            spacing: 1

            NavRow {
                icon: "go-home"
                text: backend.text("home")
                location: "home:"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12
                Layout.topMargin: 6
                Layout.bottomMargin: 6
                height: 1
                color: Theme.separator
            }

            Repeater {
                model: backend.pinned
                delegate: NavRow {
                    id: pinRow
                    required property var modelData
                    icon: modelData.icon
                    text: modelData.name
                    location: modelData.path
                    pinned: true
                    onMenuRequested: (x, y) => pane.contextMenu(pinRow, modelData, x, y)
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12
                Layout.topMargin: 6
                Layout.bottomMargin: 6
                height: 1
                color: Theme.separator
            }

            NavRow {
                icon: "computer"
                text: backend.text("this_pc")
                location: "thispc:"
                expandable: true
                expanded: pane.pcExpanded
                onToggled: pane.pcExpanded = !pane.pcExpanded
            }
            Repeater {
                model: pane.pcExpanded ? backend.drives : []
                delegate: NavRow {
                    required property var modelData
                    indent: 18
                    icon: modelData.icon || (modelData.removable ? "drive-removable-media-usb" : "drive-harddisk")
                    text: modelData.title
                    location: modelData.mount !== "" ? modelData.mount : modelData.device
                    device: modelData.device !== "" ? modelData.device : modelData.mount
                }
            }
            NavRow {
                icon: "user-trash"
                text: backend.text("recycle_bin")
                location: "trash:"
            }
            Item { Layout.preferredHeight: 8 }
        }
    }

    Rectangle {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1
        color: Theme.separator
    }
}
