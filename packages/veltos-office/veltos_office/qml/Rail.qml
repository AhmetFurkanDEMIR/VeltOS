// The navigation rail of Microsoft 365's start screen: Home, New, Open at
// the top; Account and Options at the bottom; a white indicator that
// glides to the selected entry.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: rail

    property string current: backend.page
    signal chosen(string page)

    color: Theme.chrome
    implicitWidth: Theme.railWidth

    readonly property var topPages: ["home", "new", "open"]
    readonly property var bottomPages: ["account", "options"]

    function itemAt(page) {
        for (let i = 0; i < topRepeater.count; ++i)
            if (topRepeater.itemAt(i).page === page)
                return topRepeater.itemAt(i);
        for (let i = 0; i < bottomRepeater.count; ++i)
            if (bottomRepeater.itemAt(i).page === page)
                return bottomRepeater.itemAt(i);
        return null;
    }

    component RailItem: Rectangle {
        id: item
        property string page
        property string glyph
        readonly property bool selected: rail.current === page
        Layout.fillWidth: true
        Layout.preferredHeight: Math.round(40 * Theme.textScale)
        Layout.leftMargin: 8
        Layout.rightMargin: 8
        radius: 4
        color: selected ? Theme.chromeSelected : (hover.hovered ? Theme.chromeHover : "transparent")
        Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 100 } }
        Accessible.role: Accessible.Button
        Accessible.name: backend.text(page)
        activeFocusOnTab: true
        Keys.onReturnPressed: rail.chosen(page)
        Keys.onSpacePressed: rail.chosen(page)
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            spacing: 12
            Glyph {
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
                width: 18
                height: 18
                kind: item.glyph
                color: Theme.chromeText
            }
            Text {
                Layout.fillWidth: true
                text: backend.text(item.page)
                color: Theme.chromeText
                font.pixelSize: Theme.fontSize
                font.weight: item.selected ? Font.DemiBold : Font.Normal
                elide: Text.ElideRight
                renderType: Text.NativeRendering
            }
        }
        HoverHandler { id: hover }
        TapHandler {
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: rail.chosen(item.page)
        }
    }

    ColumnLayout {
        id: column
        anchors.fill: parent
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 2

        Repeater {
            id: topRepeater
            model: rail.topPages
            delegate: RailItem {
                required property string modelData
                page: modelData
                glyph: modelData
            }
        }
        Item { Layout.fillHeight: true }
        Repeater {
            id: bottomRepeater
            model: rail.bottomPages
            delegate: RailItem {
                required property string modelData
                page: modelData
                glyph: modelData
            }
        }
    }

    // The selection indicator glides between entries.
    Rectangle {
        id: indicator
        // Depends on the repeaters' counts: itemAt() alone is not re-evaluated
        // when the delegates are created later.
        readonly property Item target: (topRepeater.count + bottomRepeater.count) >= 0 ? rail.itemAt(rail.current) : null
        readonly property int targetY: target ? column.y + target.y + Math.round((target.height - height) / 2) : -height
        width: 3
        height: 16
        radius: 1.5
        x: 8
        y: targetY
        color: Theme.chromeText
        visible: target !== null
        Behavior on y { enabled: Theme.anim > 0; NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    }
}
