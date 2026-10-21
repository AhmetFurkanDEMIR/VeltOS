// Search results: songs and videos whose title, artist, album or file name
// match.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    property string query
    readonly property var results: backend.search(query)
    signal contextMenu(var paths, var target, real x, real y)

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.topMargin: 24
            Layout.bottomMargin: 16
            text: "“" + page.query + "”"
            color: Theme.text
            font.pixelSize: 28
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            clip: true
            model: page.results
            ScrollBar.vertical: ScrollBar {}
            delegate: SongRow {
                id: row
                required property var modelData
                required property int index
                width: list.width - 12
                song: modelData
                rowIndex: index
                onPlay: backend.playPaths(page.results.map(r => r.path), index)
                onContextMenu: (x, y) => page.contextMenu([modelData.path], row, x, y)
            }
        }
    }
}
