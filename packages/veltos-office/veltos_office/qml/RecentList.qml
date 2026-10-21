// The recent files list of Microsoft 365's Home and Open pages: Recent /
// Pinned tabs with a search box, "Name" and "Date modified" columns,
// rows grouped by Pinned / Today / Yesterday / This week / Last week /
// Older, a pin on hover, a right-click menu.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Column {
    id: list

    property string mode: "recent"      // "recent" or "pinned"
    property string query: ""
    property bool showTabs: true

    spacing: 0

    // Reading backend.recent makes the binding follow the list's changes.
    readonly property var items: {
        const all = backend.recent.length >= 0 ? backend.searchRecent(query) : [];
        return mode === "pinned" ? all.filter(i => i.pinned) : all;
    }
    // Rows with group headers in front of them.
    readonly property var rows: {
        const result = [];
        let lastGroup = "";
        const pinnedFirst = mode === "recent";
        const ordered = pinnedFirst ? items.filter(i => i.pinned).concat(items.filter(i => !i.pinned)) : items;
        for (const item of ordered) {
            const group = (pinnedFirst && item.pinned) ? "pinned" : item.group;
            if (group !== lastGroup) {
                result.push({ header: true, group: group });
                lastGroup = group;
            }
            result.push({ header: false, item: item });
        }
        return result;
    }

    // --- Tabs and search ----------------------------------------------------------------
    RowLayout {
        width: parent.width
        spacing: 0
        visible: list.showTabs

        component Tab: Item {
            id: tab
            property string name
            property string label
            readonly property bool selected: list.mode === name
            Layout.preferredWidth: tabLabel.implicitWidth + 24
            Layout.preferredHeight: Math.round(36 * Theme.textScale)
            Accessible.role: Accessible.PageTab
            Accessible.name: label
            Text {
                id: tabLabel
                anchors.centerIn: parent
                text: tab.label
                color: tab.selected ? Theme.text : (tabHover.hovered ? Theme.text : Theme.subtext)
                font.pixelSize: Theme.fontSize
                font.weight: tab.selected ? Font.DemiBold : Font.Normal
                renderType: Text.NativeRendering
            }
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: tab.selected ? tabLabel.implicitWidth : 0
                height: 3
                radius: 1.5
                color: Theme.accent
                Behavior on width { enabled: Theme.anim > 0; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            }
            HoverHandler { id: tabHover }
            TapHandler {
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: list.mode = tab.name
            }
        }

        Tab { name: "recent"; label: backend.text("recent") }
        Tab { name: "pinned"; label: backend.text("pinned") }
        Item { Layout.fillWidth: true }
        SearchBox {
            Layout.preferredWidth: Math.round(240 * Theme.textScale)
            onTextChanged: list.query = text
        }
    }

    Rectangle {
        width: parent.width
        height: 1
        color: Theme.separator
        visible: list.showTabs
    }

    // --- Column headers --------------------------------------------------------------------
    Item {
        width: parent.width
        height: Math.round(32 * Theme.textScale)
        visible: list.rows.length > 0
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 44
            anchors.verticalCenter: parent.verticalCenter
            text: backend.text("name")
            color: Theme.subtext
            font.pixelSize: Theme.smallFont
            renderType: Text.NativeRendering
        }
        Text {
            anchors.right: parent.right
            anchors.rightMargin: 48
            anchors.verticalCenter: parent.verticalCenter
            text: backend.text("date_modified")
            color: Theme.subtext
            font.pixelSize: Theme.smallFont
            renderType: Text.NativeRendering
        }
    }

    // --- Empty states ------------------------------------------------------------------------
    Item {
        width: parent.width
        height: Math.round(120 * Theme.textScale)
        visible: list.rows.length === 0
        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            Glyph {
                width: 28
                height: 28
                kind: list.query !== "" ? "search" : (list.mode === "pinned" ? "pin" : "open")
                color: Theme.disabled
                lineWidth: 1.4
            }
            Text {
                width: Math.min(parent.width, 520)
                text: list.query !== "" ? backend.format("no_results", "query", list.query)
                      : (list.mode === "pinned" ? backend.text("no_pinned") : backend.noRecentText)
                color: Theme.subtext
                font.pixelSize: Theme.fontSize
                wrapMode: Text.Wrap
                renderType: Text.NativeRendering
            }
        }
    }

    // --- Rows ------------------------------------------------------------------------------------
    Repeater {
        model: list.rows
        delegate: Loader {
            id: loader
            required property var modelData
            required property int index
            width: list.width
            sourceComponent: modelData.header ? header : row
            Component {
                id: header
                Item {
                    width: list.width
                    height: Math.round(34 * Theme.textScale)
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 6
                        text: backend.text(loader.modelData.group)
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont
                        font.weight: Font.DemiBold
                        renderType: Text.NativeRendering
                    }
                }
            }
            Component {
                id: row
                Rectangle {
                    id: rowItem
                    readonly property var item: loader.modelData.item
                    width: list.width
                    height: Theme.rowHeight
                    radius: 4
                    color: rowTap.pressed ? Theme.pressed : (rowHover.hovered ? Theme.hover : "transparent")
                    Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 100 } }
                    Accessible.role: Accessible.Button
                    Accessible.name: item.name

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 12
                        Kirigami.Icon {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            source: rowItem.item.icon
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text {
                                Layout.fillWidth: true
                                text: rowItem.item.name
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                                elide: Text.ElideMiddle
                                renderType: Text.NativeRendering
                            }
                            Text {
                                Layout.fillWidth: true
                                text: rowItem.item.folder
                                color: Theme.subtext
                                font.pixelSize: Theme.smallFont
                                elide: Text.ElideMiddle
                                renderType: Text.NativeRendering
                            }
                        }
                        Text {
                            Layout.preferredWidth: Math.round(170 * Theme.textScale)
                            text: rowItem.item.modifiedText
                            color: Theme.subtext
                            font.pixelSize: Theme.smallFont
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideRight
                            renderType: Text.NativeRendering
                        }
                        Rectangle {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 28
                            radius: 4
                            color: pinHover.hovered ? Theme.pressed : "transparent"
                            opacity: rowItem.item.pinned || rowHover.hovered ? 1 : 0
                            Behavior on opacity { enabled: Theme.anim > 0; NumberAnimation { duration: 120 } }
                            Accessible.role: Accessible.Button
                            Accessible.name: backend.text(rowItem.item.pinned ? "unpin" : "pin")
                            Glyph {
                                anchors.centerIn: parent
                                width: 16
                                height: 16
                                kind: rowItem.item.pinned ? "pinned" : "pin"
                                color: rowItem.item.pinned ? Theme.accent : Theme.subtext
                            }
                            HoverHandler { id: pinHover }
                            TapHandler {
                                gesturePolicy: TapHandler.ReleaseWithinBounds
                                onTapped: backend.pin(rowItem.item.path, !rowItem.item.pinned)
                            }
                        }
                    }
                    HoverHandler { id: rowHover }
                    TapHandler {
                        id: rowTap
                        acceptedButtons: Qt.LeftButton
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: backend.openFile(rowItem.item.path)
                    }
                    TapHandler {
                        acceptedButtons: Qt.RightButton
                        onTapped: point => {
                            menu.entries = [
                                { text: backend.text("open"), glyph: "open", action: () => backend.openFile(rowItem.item.path) },
                                { text: backend.text(rowItem.item.pinned ? "unpin" : "pin"), glyph: rowItem.item.pinned ? "pinned" : "pin",
                                  action: () => backend.pin(rowItem.item.path, !rowItem.item.pinned) },
                                { text: backend.text("open_file_location"), glyph: "folder", action: () => backend.openFileLocation(rowItem.item.path) },
                                { text: backend.text("copy_path"), glyph: "more", action: () => backend.copyPath(rowItem.item.path) },
                                { text: backend.text("remove_from_list"), glyph: "close", action: () => backend.remove(rowItem.item.path) },
                            ];
                            menu.show(rowItem, point.position.x, point.position.y);
                        }
                    }
                }
            }
        }
    }

    ContextMenu { id: menu }
}
