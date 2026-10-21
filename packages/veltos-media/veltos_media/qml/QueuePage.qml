// Play queue of Windows 11 Media Player: what plays, in order, the current
// item in the accent colour; remove items, clear the queue.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.topMargin: 24
            Layout.bottomMargin: 16
            Text { Layout.fillWidth: true; text: backend.texts.play_queue; color: Theme.text; font.pixelSize: 28; font.weight: Font.DemiBold }
            PillButton { text: backend.texts.clear; enabledState: backend.queueItems.length > 0; onClicked: backend.clearQueue() }
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            visible: backend.queueItems.length === 0
            text: backend.texts.empty_queue
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }
        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            model: backend.queueItems
            delegate: SongRow {
                required property var modelData
                required property int index
                width: list.width - 12
                song: modelData
                rowIndex: index
                showRemove: true
                onPlay: backend.goQueue(index)
                onRemove: backend.removeFromQueue(index)
            }
        }
    }
}
