// Windows 11 style menu (Outlook's ribbon drop-downs and the message
// list's context menu): rounded, with icons, check marks, shortcuts and one
// level of sub-menus. `items` is a list of
//   {text, icon, shortcut, enabled, checked, action}   a command
//   {separator: true}
//   {text, submenu: [items]}                      a sub-menu
// `triggered(action)` reports the chosen command.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Popup {
    id: menu

    property var items: []
    property int minimumWidth: 240
    signal triggered(string action)

    function openAt(item, x, y) {
        const point = item.mapToItem(Overlay.overlay, x, y);
        menu.x = Math.max(4, Math.min(point.x, Overlay.overlay.width - menu.width - 4));
        menu.y = point.y + menu.height > Overlay.overlay.height - 4 ? Math.max(4, point.y - menu.height) : point.y;
        menu.open();
    }

    parent: Overlay.overlay
    padding: 4
    width: Math.max(minimumWidth, column.implicitWidth + 2 * padding)
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 90 } }
    background: MenuBackground {}

    component MenuBackground: Rectangle {
        radius: 8
        color: Theme.menu
        border.width: 1
        border.color: Theme.fieldBorder
        Rectangle {
            z: -1
            anchors.fill: parent
            anchors.margins: -3
            anchors.topMargin: -1
            anchors.bottomMargin: -5
            radius: 11
            color: "#000000"
            opacity: Theme.dark ? 0.35 : 0.08
        }
    }

    contentItem: ColumnLayout {
        id: column
        spacing: 0
        Repeater {
            model: menu.items
            delegate: Loader {
                required property var modelData
                Layout.fillWidth: true
                sourceComponent: modelData.separator ? separatorComponent : entryComponent
                onLoaded: item.entry = modelData
            }
        }
    }

    Component {
        id: separatorComponent
        Item {
            property var entry
            implicitHeight: 9
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 8
                height: 1
                color: Theme.separator
            }
        }
    }

    Component {
        id: entryComponent
        Rectangle {
            id: entryItem
            property var entry
            property Popup owner: menu
            readonly property bool active: entry && entry.enabled !== false
            readonly property bool hasSubmenu: entry && entry.submenu !== undefined

            implicitWidth: entryRow.implicitWidth + 24
            implicitHeight: 32
            radius: 4
            color: hover.hovered && active ? Theme.hover : "transparent"
            Accessible.role: Accessible.MenuItem
            Accessible.name: entry ? entry.text : ""

            RowLayout {
                id: entryRow
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 12
                Item {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    Glyph {
                        anchors.fill: parent
                        visible: !!entryItem.entry && (entryItem.entry.checked === true || !!entryItem.entry.icon)
                        kind: entryItem.entry && entryItem.entry.icon ? entryItem.entry.icon : "check"
                        color: entryItem.active ? Theme.text : Theme.disabled
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: entryItem.entry ? entryItem.entry.text : ""
                    color: entryItem.active ? Theme.text : Theme.disabled
                    font.pixelSize: Theme.fontSize
                    elide: Text.ElideMiddle
                    Layout.maximumWidth: 360
                }
                Text {
                    visible: text !== ""
                    text: entryItem.entry && entryItem.entry.shortcut ? entryItem.entry.shortcut : ""
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                }
                Glyph {
                    visible: entryItem.hasSubmenu
                    Layout.preferredWidth: 8
                    Layout.preferredHeight: 8
                    kind: "chevron-right"
                    color: Theme.subtext
                }
            }

            HoverHandler {
                id: hover
                onHoveredChanged: {
                    if (hovered && entryItem.hasSubmenu && entryItem.active) {
                        submenu.items = entryItem.entry.submenu;
                        submenu.openAt(entryItem);
                    } else if (hovered && entryItem.owner === menu && !entryItem.hasSubmenu) {
                        submenu.close();
                    }
                }
            }
            TapHandler {
                enabled: entryItem.active
                // Exclusive: a passive grab let the tap through to the item
                // under the menu too (File Explorer, VM 2026-10-25).
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: {
                    if (entryItem.hasSubmenu) {
                        submenu.items = entryItem.entry.submenu;
                        submenu.openAt(entryItem);
                        return;
                    }
                    submenu.close();
                    menu.close();
                    menu.triggered(entryItem.entry.action);
                }
            }
        }
    }

    property Popup submenu: Popup {
        id: submenuPopup
        property var items: []
        function openAt(item) {
            const point = item.mapToItem(Overlay.overlay, item.width - 2, -4);
            submenuPopup.x = point.x + submenuPopup.width > Overlay.overlay.width
                             ? point.x - item.width - submenuPopup.width + 4 : point.x;
            submenuPopup.y = Math.min(point.y, Overlay.overlay.height - submenuPopup.height - 4);
            submenuPopup.open();
        }
        parent: Overlay.overlay
        padding: 4
        width: Math.max(220, subColumn.implicitWidth + 2 * padding)
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: MenuBackground {}
        contentItem: ColumnLayout {
            id: subColumn
            spacing: 0
            Repeater {
                model: submenuPopup.items
                delegate: Loader {
                    required property var modelData
                    Layout.fillWidth: true
                    sourceComponent: modelData.separator ? separatorComponent : entryComponent
                    onLoaded: {
                        item.entry = modelData;
                        item.owner = submenuPopup;
                    }
                }
            }
        }
    }

    onClosed: submenu.close()
}
