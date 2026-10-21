// One picture or video in the gallery: the thumbnail cropped to a square,
// a play mark on videos, the heart on favorites; a light border and a
// slight lift under the pointer, as in Windows 11 Photos.
import QtQuick
import "."

Rectangle {
    id: tile

    property var item: ({})
    signal open()
    signal contextMenu(real x, real y)

    radius: 4
    color: Theme.tile
    clip: true
    Accessible.role: Accessible.Graphic
    Accessible.name: item.path ? item.path.split("/").pop() : ""

    Image {
        anchors.fill: parent
        source: tile.item.path ? backend.thumbUrl(tile.item.path, tile.item.kind, tile.item.mtime || 0) : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: true
        smooth: true
        opacity: status === Image.Ready ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 120 } }
    }

    // Video: a round play mark in the corner.
    Rectangle {
        visible: tile.item.kind === "video"
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 8
        width: 28
        height: 28
        radius: 14
        color: "#99000000"
        Glyph { anchors.centerIn: parent; anchors.horizontalCenterOffset: 1; width: 12; height: 12; kind: "play"; color: "#FFFFFF" }
    }
    Glyph {
        visible: backend.favorites.indexOf(tile.item.path) >= 0
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 8
        width: 16
        height: 16
        kind: "heart-filled"
        color: "#FFFFFF"
    }

    Rectangle {
        anchors.fill: parent
        radius: tile.radius
        color: hover.hovered ? Qt.rgba(1, 1, 1, Theme.dark ? 0.06 : 0.12) : "transparent"
        border.width: hover.hovered ? 2 : 0
        border.color: Theme.accent
    }

    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: tile.open() }
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: point => tile.contextMenu(point.position.x, point.position.y)
    }
}
