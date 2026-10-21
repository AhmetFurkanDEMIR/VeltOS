// Home of Windows 11 Media Player: "Open file(s)" and the recent media.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    signal play(var paths, int index)
    signal openFiles()

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                Layout.topMargin: 24
                Text { Layout.fillWidth: true; text: backend.texts.home; color: Theme.text; font.pixelSize: 28; font.weight: Font.DemiBold }
                PillButton { text: backend.texts.open_files; glyph: "folder"; onClicked: page.openFiles() }
            }
            Text {
                Layout.leftMargin: 32
                Layout.topMargin: 8
                text: backend.texts.recent_media
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }
            Text {
                Layout.leftMargin: 32
                visible: backend.recent.length === 0
                text: backend.texts.no_recent
                color: Theme.subtext
                font.pixelSize: Theme.fontSize
            }
            Flow {
                Layout.fillWidth: true
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                Layout.bottomMargin: 32
                spacing: 18
                Repeater {
                    model: backend.recent
                    delegate: MediaTile {
                        required property var modelData
                        required property int index
                        width: modelData.kind === "video" ? 240 : 160
                        ratio: modelData.kind === "video" ? 16 / 9 : 1
                        picture: modelData.cover ? backend.fileUrl(modelData.cover)
                                 : modelData.kind === "video" ? backend.thumbUrl(modelData.path, modelData.mtime || 0) : ""
                        glyph: modelData.kind === "video" ? "video" : "music"
                        title: modelData.title
                        subtitle: modelData.artist || ""
                        onOpen: page.play([modelData.path], 0)
                        onPlay: page.play([modelData.path], 0)
                    }
                }
            }
        }
    }
}
