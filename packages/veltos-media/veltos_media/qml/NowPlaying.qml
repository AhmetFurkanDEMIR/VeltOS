// "Now playing" of Windows 11 Media Player: a video fills the view (click
// pauses, double click is full screen); a song shows its album picture
// large on a blurred copy of it, with the title, artist and album.
import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import "."

Item {
    id: view

    property var item: ({})
    property bool playing: false
    readonly property alias videoOutput: video
    readonly property bool isVideo: item.kind === "video"
    signal toggle()
    signal fullScreenToggled()
    signal pointerMoved()

    Rectangle {
        anchors.fill: parent
        color: view.isVideo ? "#000000" : Theme.content
    }

    // Song: blurred album picture behind.
    Image {
        id: backdrop
        anchors.fill: parent
        visible: false
        source: !view.isVideo && view.item.cover ? backend.fileUrl(view.item.cover) : ""
        fillMode: Image.PreserveAspectCrop
        sourceSize: Qt.size(400, 400)
    }
    MultiEffect {
        anchors.fill: parent
        visible: !view.isVideo && backdrop.status === Image.Ready
        source: backdrop
        blurEnabled: true
        blur: 1.0
        blurMax: 64
        brightness: Theme.dark ? -0.35 : 0.25
        saturation: 0.2
    }

    ColumnLayout {
        anchors.centerIn: parent
        visible: !view.isVideo
        width: Math.min(parent.width - 80, 420)
        spacing: 12
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: Math.min(320, view.height - 200)
            Layout.preferredHeight: Layout.preferredWidth
            radius: 8
            color: Theme.tile
            clip: true
            Image {
                anchors.fill: parent
                source: view.item.cover ? backend.fileUrl(view.item.cover) : ""
                fillMode: Image.PreserveAspectCrop
                sourceSize: Qt.size(640, 640)
                asynchronous: true
            }
            Glyph {
                anchors.centerIn: parent
                visible: !view.item.cover
                width: 64; height: 64
                kind: "music"
                color: Theme.subtext
            }
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: view.item.title || ""
            color: Theme.text
            font.pixelSize: 24
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: [view.item.artist, view.item.album].filter(t => !!t).join("  ·  ")
            color: Theme.subtext
            font.pixelSize: 14
            elide: Text.ElideRight
        }
    }

    VideoOutput {
        id: video
        anchors.fill: parent
        visible: view.isVideo
        fillMode: VideoOutput.PreserveAspectFit
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        enabled: view.isVideo
        onPositionChanged: view.pointerMoved()
        onClicked: view.toggle()
        onDoubleClicked: view.fullScreenToggled()
        cursorShape: Qt.ArrowCursor
    }
}
