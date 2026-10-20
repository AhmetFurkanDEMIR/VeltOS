// The History or Memory list of Windows 11 Calculator: newest first,
// right-aligned; a history item shows its calculation and result and
// brings both back when chosen; a memory item recalls its number and,
// when pointed at, offers MC, M+ and M− for that item. The waste basket
// at the bottom right clears the list.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: records
    property string kind: "history"     // or "memory"
    signal chosen()

    readonly property var items: kind === "history" ? backend.history : backend.memory
    readonly property bool empty: items.length === 0

    Text {
        visible: records.empty
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        text: records.kind === "history" ? backend.texts.no_history : backend.texts.no_memory
        color: Theme.text
        font.pixelSize: Theme.bodySize
        wrapMode: Text.Wrap
    }

    ListView {
        id: list
        objectName: records.kind + "List"
        anchors.fill: parent
        anchors.bottomMargin: 48
        clip: true
        model: records.items
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        delegate: AbstractButton {
            id: item
            required property int index
            required property var modelData
            width: ListView.view.width
            implicitHeight: column.implicitHeight + 24
            hoverEnabled: true
            focusPolicy: Qt.NoFocus
            Accessible.name: records.kind === "history"
                             ? modelData.expression + " " + modelData.result : modelData
            onClicked: {
                if (records.kind === "history") {
                    backend.useHistory(index);
                } else {
                    backend.memoryItem(index, "recall");
                }
                records.chosen();
            }
            background: Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                radius: Theme.keyRadius
                color: item.down ? Theme.pressed : (item.hovered ? Theme.hover : "transparent")
            }
            contentItem: Item {
                ColumnLayout {
                    id: column
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.topMargin: 12
                    spacing: 2
                    Text {
                        visible: records.kind === "history"
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: records.kind === "history" ? item.modelData.expression : ""
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.WrapAnywhere
                    }
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: records.kind === "history" ? item.modelData.result : item.modelData
                        color: Theme.text
                        font.pixelSize: 20
                        font.weight: Font.DemiBold
                        wrapMode: Text.WrapAnywhere
                    }
                    // Memory: MC M+ M− for this item, shown on hover (Windows).
                    Row {
                        visible: records.kind === "memory"
                        Layout.alignment: Qt.AlignRight
                        opacity: item.hovered ? 1 : 0
                        spacing: 4
                        Repeater {
                            model: [{ label: "MC", action: "clear", tip: backend.texts.memory_clear },
                                    { label: "M+", action: "add", tip: backend.texts.memory_add },
                                    { label: "M−", action: "subtract", tip: backend.texts.memory_subtract }]
                            delegate: FlatButton {
                                required property var modelData
                                label: modelData.label
                                tip: modelData.tip
                                implicitWidth: 40
                                implicitHeight: 26
                                background: Rectangle {
                                    radius: Theme.keyRadius
                                    color: parent.down ? Theme.operatorPressed
                                                       : (parent.hovered ? Theme.operatorHover : Theme.operator)
                                    border.width: 1
                                    border.color: Theme.keyBorder
                                }
                                onClicked: backend.memoryItem(item.index, modelData.action)
                            }
                        }
                    }
                }
            }
        }
    }

    FlatButton {
        objectName: records.kind + "Clear"
        visible: !records.empty
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 8
        implicitWidth: 40
        implicitHeight: 36
        glyph: "delete"
        tip: records.kind === "history" ? backend.texts.clear_history : backend.texts.clear_memory
        onClicked: records.kind === "history" ? backend.clearHistory() : backend.clearMemory()
    }
}
