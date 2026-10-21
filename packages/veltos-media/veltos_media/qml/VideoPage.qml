// Video library of Windows 11 Media Player: the videos as tiles with their
// first frames, newest first.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    signal contextMenu(var paths, var target, real x, real y)

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.topMargin: 24
            Layout.bottomMargin: 16
            Text { Layout.fillWidth: true; text: backend.texts.videos; color: Theme.text; font.pixelSize: 28; font.weight: Font.DemiBold }
            PillButton {
                text: backend.texts.play_all
                glyph: "play"
                primary: true
                enabledState: backend.videos.length > 0
                onClicked: backend.playPaths(backend.videos.map(v => v.path), 0)
            }
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            visible: !backend.scanning && backend.videos.length === 0
            text: backend.texts.empty_videos
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }
        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 28
            Layout.rightMargin: 12
            clip: true
            cellWidth: 256
            cellHeight: 196
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            model: backend.videos
            delegate: MediaTile {
                id: tile
                required property var modelData
                required property int index
                width: 240
                ratio: 16 / 9
                glyph: "video"
                picture: backend.thumbUrl(modelData.path, modelData.mtime || 0)
                title: modelData.title
                subtitle: modelData.duration ? backend.durationText(modelData.duration) : ""
                onOpen: backend.playPaths(backend.videos.map(v => v.path), index)
                onPlay: backend.playPaths([modelData.path], 0)
                onContextMenu: (x, y) => page.contextMenu([modelData.path], tile, x, y)
            }
        }
    }
}
