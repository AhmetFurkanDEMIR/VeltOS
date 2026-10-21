// A tile of the media pages (album, artist, video, recent item): the
// picture (album cover or video frame) with a play button under the
// pointer, the title and a second line.
import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: tile

    property string picture             // URL
    property string glyph: "music"      // shown without a picture
    property string title
    property string subtitle
    property real ratio: 1              // width / height of the picture
    property bool round: false          // artists
    signal open()
    signal play()
    signal contextMenu(real x, real y)

    implicitWidth: 168
    implicitHeight: art.height + 52

    Rectangle {
        id: art
        width: parent.width
        height: Math.round(width / tile.ratio)
        radius: tile.round ? width / 2 : 6
        color: Theme.tile
        clip: true
        Image {
            anchors.fill: parent
            source: tile.picture
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            sourceSize: Qt.size(320, 320)
            visible: status === Image.Ready && implicitWidth > 1
        }
        Glyph {
            anchors.centerIn: parent
            visible: tile.picture === ""
            width: 36; height: 36
            kind: tile.glyph
            color: Theme.subtext
        }
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: hover.hovered ? Qt.rgba(0, 0, 0, 0.18) : "transparent"
        }
        Rectangle {
            visible: hover.hovered
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.margins: 10
            width: 36; height: 36; radius: 18
            color: Theme.accent
            Accessible.role: Accessible.Button
            Accessible.name: backend.texts.play
            Glyph { anchors.centerIn: parent; anchors.horizontalCenterOffset: 1; width: 13; height: 13; kind: "play"; color: Theme.accentText }
            TapHandler { onTapped: tile.play() }
        }
    }
    ColumnLayout {
        anchors.top: art.bottom
        anchors.topMargin: 8
        width: parent.width
        spacing: 1
        Text { Layout.fillWidth: true; text: tile.title; color: Theme.text; font.pixelSize: Theme.fontSize; elide: Text.ElideRight
               horizontalAlignment: tile.round ? Text.AlignHCenter : Text.AlignLeft }
        Text { Layout.fillWidth: true; text: tile.subtitle; color: Theme.subtext; font.pixelSize: Theme.smallFont
               elide: Text.ElideRight; visible: text !== ""; horizontalAlignment: tile.round ? Text.AlignHCenter : Text.AlignLeft }
    }
    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: tile.open() }
    TapHandler { acceptedButtons: Qt.RightButton; onTapped: point => tile.contextMenu(point.position.x, point.position.y) }
}
