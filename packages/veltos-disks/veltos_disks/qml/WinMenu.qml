// A Windows 11 style context menu: rounded, one list of entries with
// separators; `items` is [{text, action, enabled, separator}] and
// `triggered(action)` reports the choice.
import QtQuick
import QtQuick.Controls
import "."

Popup {
    id: menu

    property var items: []
    signal triggered(string action)

    function showAt(x, y) {
        const w = parent ? parent.width : 0, h = parent ? parent.height : 0;
        menu.x = Math.max(0, Math.min(x, w - width));
        menu.y = Math.max(0, Math.min(y, h - height));
        open();
    }

    parent: Overlay.overlay
    modal: false
    dim: false
    padding: 4
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    width: 240

    background: Rectangle {
        radius: 8
        color: Theme.popup
        border.width: 1
        border.color: Theme.cardBorder
    }

    contentItem: Column {
        spacing: 0
        Repeater {
            model: menu.items
            delegate: Item {
                id: entry
                required property var modelData
                width: menu.width - menu.padding * 2
                height: modelData.separator ? 9 : Theme.rowHeight
                Rectangle {
                    visible: entry.modelData.separator === true
                    anchors.centerIn: parent
                    width: parent.width - 8
                    height: 1
                    color: Theme.cardBorder
                }
                Rectangle {
                    visible: entry.modelData.separator !== true
                    anchors.fill: parent
                    radius: 4
                    color: hover.hovered && entry.modelData.enabled !== false ? Theme.rowHover : "transparent"
                    Text {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        text: entry.modelData.text || ""
                        color: Theme.text
                        opacity: entry.modelData.enabled === false ? 0.45 : 1
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                    HoverHandler { id: hover }
                    TapHandler {
                        enabled: entry.modelData.enabled !== false && entry.modelData.separator !== true
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: {
                            menu.close();
                            menu.triggered(entry.modelData.action);
                        }
                    }
                }
            }
        }
    }
}
