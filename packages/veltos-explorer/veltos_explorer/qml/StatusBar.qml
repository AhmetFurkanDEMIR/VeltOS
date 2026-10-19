// Status bar: number of items, the selection and its size on the left,
// Details / Large icons switches on the right (Windows 11 File Explorer).
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: bar

    readonly property var tab: backend.current
    readonly property var model: tab.items

    implicitHeight: 28
    color: Theme.content

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 10
        spacing: 16

        Text {
            visible: bar.tab.kind !== "home"
            text: {
                const count = bar.tab.kind === "thispc" ? backend.drives.length : bar.model.count;
                return count === 1 ? backend.text("item") : backend.format("items", "count", String(count));
            }
            color: Theme.text
            font.pixelSize: Theme.smallFont
        }
        Rectangle {
            visible: bar.model.selectedCount > 0
            Layout.preferredWidth: 1
            Layout.preferredHeight: 14
            color: Theme.separator
        }
        Text {
            visible: bar.model.selectedCount > 0
            text: (bar.model.selectedCount === 1 ? backend.text("one_selected")
                   : backend.format("selected", "count", String(bar.model.selectedCount)))
                  + (bar.model.selectedSize !== "" ? "   " + bar.model.selectedSize : "")
            color: Theme.text
            font.pixelSize: Theme.smallFont
        }
        Item { Layout.fillWidth: true }
        IconButton {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 24
            icon: "view-list-details"
            tooltip: backend.text("details")
            checked: bar.tab.viewMode === "details"
            enabledState: bar.tab.kind !== "home"
            onClicked: bar.tab.setViewMode("details")
        }
        IconButton {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 24
            icon: "view-list-icons"
            tooltip: backend.text("large_icons")
            checked: bar.tab.viewMode === "large"
            enabledState: bar.tab.kind !== "home"
            onClicked: bar.tab.setViewMode("large")
        }
    }
}
