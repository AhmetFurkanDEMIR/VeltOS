// Windows 11 style menu: rounded, with icons, check marks, shortcuts and
// sub-menus. `items` is a list of
//   {text, icon, shortcut, enabled, checked, action}   a command
//   {separator: true}
//   {text, icon, submenu: [items]}                       a sub-menu
//   {iconRow: [{icon, tooltip, action, enabled}]}       the icon row at the
//                                                        top of File Explorer's
//                                                        context menu
// `triggered(action)` reports the chosen command.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Popup {
    id: menu

    property var items: []
    property int minimumWidth: 220
    signal triggered(string action)

    // Where the menu was asked to open, and the top of what it opens from
    // (it flips above when the space below is too small). The position
    // follows the menu's size: on the first opening the size is only known
    // once the new items are laid out, and a position computed from the
    // old size put drop-downs in the wrong place (product owner,
    // 2026-10-22: the file dialog's type list on its first opening).
    property point anchorPoint: Qt.point(0, 0)
    property real anchorTop: 0
    x: Math.max(4, Math.min(anchorPoint.x, Overlay.overlay.width - width - 4))
    y: anchorPoint.y + height > Overlay.overlay.height - 4 ? Math.max(4, anchorTop - height) : anchorPoint.y

    function openAt(item, x, y) {
        const point = item.mapToItem(Overlay.overlay, x, y);
        menu.anchorPoint = point;
        // Below a box (a drop-down): above the box when flipped; at a
        // clicked point: ending at the point.
        menu.anchorTop = y >= item.height ? item.mapToItem(Overlay.overlay, 0, 0).y - 2 : point.y;
        menu.open();
    }

    parent: Overlay.overlay
    padding: 4
    // Never wider than the window: long entries (file types) are shortened.
    width: Math.min(Overlay.overlay.width - 8, Math.max(minimumWidth, column.implicitWidth + 2 * padding))
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 90 } }

    background: Rectangle {
        radius: 8
        color: Theme.menu
        border.width: 1
        border.color: Theme.fieldBorder
        // Soft shadow.
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
                sourceComponent: modelData.separator ? separatorComponent
                                 : modelData.iconRow ? iconRowComponent : entryComponent
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
        id: iconRowComponent
        RowLayout {
            property var entry
            spacing: 2
            Repeater {
                model: entry ? entry.iconRow : []
                delegate: IconButton {
                    required property var modelData
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 36
                    icon: modelData.icon
                    tooltip: modelData.tooltip
                    enabledState: modelData.enabled !== false
                    onClicked: {
                        menu.close();
                        menu.triggered(modelData.action);
                    }
                }
            }
            Item { Layout.fillWidth: true }
        }
    }

    Component {
        id: entryComponent
        Rectangle {
            id: entryItem

            property var entry
            readonly property bool active: entry && entry.enabled !== false
            readonly property bool hasSubmenu: entry && entry.submenu !== undefined

            implicitWidth: entryRow.implicitWidth + 24
            implicitHeight: 32
            radius: 4
            color: hover.hovered && active ? Theme.hover : "transparent"

            RowLayout {
                id: entryRow
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 12
                Item {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    Kirigami.Icon {
                        anchors.fill: parent
                        visible: entryItem.entry && !!entryItem.entry.icon && !entryItem.entry.checked
                        source: entryItem.entry && entryItem.entry.icon ? entryItem.entry.icon : ""
                        opacity: entryItem.active ? 1 : 0.35
                    }
                    Kirigami.Icon {
                        anchors.fill: parent
                        visible: entryItem.entry && entryItem.entry.checked === true
                        source: "checkmark"
                        color: Theme.text
                        isMask: true
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: entryItem.entry ? entryItem.entry.text : ""
                    color: entryItem.active ? Theme.text : Theme.disabled
                    font.pixelSize: Theme.fontSize
                    elide: Text.ElideRight
                }
                Text {
                    visible: text !== ""
                    text: entryItem.entry && entryItem.entry.shortcut ? entryItem.entry.shortcut : ""
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                }
                Kirigami.Icon {
                    visible: entryItem.hasSubmenu
                    Layout.preferredWidth: 10
                    Layout.preferredHeight: 10
                    source: "arrow-right"
                    color: Theme.subtext
                    isMask: true
                }
            }

            HoverHandler {
                id: hover
                onHoveredChanged: {
                    if (hovered && entryItem.hasSubmenu && entryItem.active) {
                        submenu.items = entryItem.entry.submenu;
                        submenu.openAt(entryItem, entryItem.width - 2, -4);
                    }
                }
            }
            TapHandler {
                enabled: entryItem.active
                onTapped: {
                    if (entryItem.hasSubmenu) {
                        submenu.items = entryItem.entry.submenu;
                        submenu.openAt(entryItem, entryItem.width - 2, -4);
                        return;
                    }
                    menu.close();
                    menu.triggered(entryItem.entry.action);
                }
            }
        }
    }

    // One level of sub-menus is enough for File Explorer (New, Sort, View,
    // Open with).
    property var submenu: Popup {
        id: submenuPopup

        property var items: []

        function openAt(item, x, y) {
            const point = item.mapToItem(Overlay.overlay, x, y);
            submenuPopup.x = point.x + submenuPopup.width > Overlay.overlay.width
                             ? point.x - item.width - submenuPopup.width + 4 : point.x;
            submenuPopup.y = Math.min(point.y, Overlay.overlay.height - submenuPopup.height - 4);
            submenuPopup.open();
        }

        parent: Overlay.overlay
        padding: 4
        width: Math.max(200, subColumn.implicitWidth + 2 * padding)
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: Rectangle {
            radius: 8
            color: Theme.menu
            border.width: 1
            border.color: Theme.fieldBorder
        }
        contentItem: ColumnLayout {
            id: subColumn
            spacing: 0
            Repeater {
                model: submenuPopup.items
                delegate: Loader {
                    required property var modelData
                    Layout.fillWidth: true
                    sourceComponent: modelData.separator ? separatorComponent : subEntryComponent
                    onLoaded: item.entry = modelData
                }
            }
        }
    }

    Component {
        id: subEntryComponent
        Rectangle {
            id: subItem
            property var entry
            readonly property bool active: entry && entry.enabled !== false
            implicitWidth: subRow.implicitWidth + 24
            implicitHeight: 32
            radius: 4
            color: subHover.hovered && active ? Theme.hover : "transparent"
            RowLayout {
                id: subRow
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 12
                Item {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    Kirigami.Icon {
                        anchors.fill: parent
                        visible: subItem.entry && !!subItem.entry.icon && !subItem.entry.checked
                        source: subItem.entry && subItem.entry.icon ? subItem.entry.icon : ""
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        visible: subItem.entry && subItem.entry.checked === true
                        width: 6
                        height: 6
                        radius: 3
                        color: Theme.text
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: subItem.entry ? subItem.entry.text : ""
                    color: subItem.active ? Theme.text : Theme.disabled
                    font.pixelSize: Theme.fontSize
                }
            }
            HoverHandler { id: subHover }
            TapHandler {
                enabled: subItem.active
                onTapped: {
                    menu.submenu.close();
                    menu.close();
                    menu.triggered(subItem.entry.action);
                }
            }
        }
    }

    onClosed: submenu.close()
}
