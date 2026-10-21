// A song in Windows 11 Media Player's lists: play button under the
// pointer, title, artist, album, year, genre and length; the playing song
// in the accent colour; zebra rows.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: row

    property var song: ({})
    property int rowIndex: 0
    property bool showRemove: false
    readonly property bool playing: backend.current.path === song.path
    signal play()
    signal remove()
    signal contextMenu(real x, real y)

    implicitHeight: 48
    radius: 4
    color: hover.hovered ? Theme.hover : (rowIndex % 2 === 0 ? Theme.zebra : "transparent")
    Accessible.role: Accessible.ListItem
    Accessible.name: song.title || ""

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 12
        Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            Glyph { anchors.centerIn: parent; width: 14; height: 14; kind: row.playing ? "volume" : "play"
                    visible: hover.hovered || row.playing; color: row.playing ? Theme.accent : Theme.text
                    TapHandler { onTapped: row.play() } }
        }
        Text { Layout.fillWidth: true; Layout.preferredWidth: 3; text: row.song.title || ""; elide: Text.ElideRight
               color: row.playing ? Theme.accent : Theme.text; font.pixelSize: Theme.fontSize }
        Text { Layout.fillWidth: true; Layout.preferredWidth: 2; text: row.song.artist || backend.texts.unknown_artist
               elide: Text.ElideRight; color: row.playing ? Theme.accent : Theme.subtext; font.pixelSize: Theme.fontSize }
        Text { Layout.fillWidth: true; Layout.preferredWidth: 2; text: row.song.album || backend.texts.unknown_album
               elide: Text.ElideRight; color: row.playing ? Theme.accent : Theme.subtext; font.pixelSize: Theme.fontSize
               visible: row.width > 640 }
        Text { Layout.preferredWidth: 48; text: row.song.year || ""; color: Theme.subtext; font.pixelSize: Theme.fontSize
               visible: row.width > 760 }
        Text { Layout.preferredWidth: 90; text: row.song.genre || ""; elide: Text.ElideRight; color: Theme.subtext
               font.pixelSize: Theme.fontSize; visible: row.width > 880 }
        Text { Layout.preferredWidth: 48; horizontalAlignment: Text.AlignRight
               text: row.song.duration ? backend.durationText(row.song.duration) : ""
               color: Theme.subtext; font.pixelSize: Theme.fontSize }
        Rectangle {
            visible: row.showRemove
            Layout.preferredWidth: 28; Layout.preferredHeight: 28; radius: 4
            color: removeHover.hovered ? Theme.hover : "transparent"
            Accessible.role: Accessible.Button
            Accessible.name: backend.texts.remove
            Glyph { anchors.centerIn: parent; width: 10; height: 10; kind: "close" }
            HoverHandler { id: removeHover }
            TapHandler { onTapped: row.remove() }
        }
    }
    HoverHandler { id: hover }
    TapHandler { onDoubleTapped: row.play() }
    TapHandler { acceptedButtons: Qt.RightButton; onTapped: point => row.contextMenu(point.position.x, point.position.y) }
}
