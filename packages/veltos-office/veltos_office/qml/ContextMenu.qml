// A Windows 11 context menu: a rounded card with a shadow, entries with
// a glyph, opened at the pointer.
import QtQuick
import QtQuick.Controls
import "."

Popup {
    id: menu

    // [{text, glyph, action: function}]
    property var entries: []

    function show(item, x, y) {
        parent = Overlay.overlay;
        const point = item.mapToItem(Overlay.overlay, x, y);
        menu.x = Math.min(point.x, Overlay.overlay.width - width - 8);
        menu.y = Math.min(point.y, Overlay.overlay.height - height - 8);
        open();
    }

    modal: true
    dim: false
    padding: 4
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 120 * Theme.anim }
        NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 140 * Theme.anim; easing.type: Easing.OutCubic }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 80 * Theme.anim }
    }
    background: Item {
        Repeater {
            model: 8
            delegate: Rectangle {
                required property int index
                anchors.fill: card
                anchors.margins: -(index + 1)
                radius: card.radius + index + 1
                color: "transparent"
                border.width: 1
                border.color: Qt.rgba(0, 0, 0, (Theme.dark ? 0.22 : 0.07) * Math.pow(1 - index / 8, 2))
            }
        }
        Rectangle {
            id: card
            anchors.fill: parent
            radius: 8
            color: Theme.menu
            border.width: 1
            border.color: Theme.cardBorder
        }
    }
    contentItem: Column {
        spacing: 2
        Repeater {
            model: menu.entries
            delegate: Rectangle {
                id: entry
                required property var modelData
                width: Math.max(220, label.implicitWidth + 64)
                height: Math.round(32 * Theme.textScale)
                radius: 4
                color: entryHover.hovered ? Theme.hover : "transparent"
                Glyph {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    width: 16
                    height: 16
                    visible: entry.modelData.glyph !== undefined
                    kind: entry.modelData.glyph || "more"
                    color: Theme.text
                }
                Text {
                    id: label
                    anchors.left: parent.left
                    anchors.leftMargin: 36
                    anchors.verticalCenter: parent.verticalCenter
                    text: entry.modelData.text
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    renderType: Text.NativeRendering
                }
                HoverHandler { id: entryHover }
                TapHandler {
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: {
                        menu.close();
                        entry.modelData.action();
                    }
                }
            }
        }
    }
}
