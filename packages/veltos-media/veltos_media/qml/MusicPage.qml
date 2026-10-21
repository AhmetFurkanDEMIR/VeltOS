// Music library of Windows 11 Media Player: Songs, Albums and Artists, with
// "Shuffle and play". An album or artist opens its songs below the tabs.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    property string tab: "songs"
    property var opened: null            // album or artist shown
    signal contextMenu(var paths, var target, real x, real y)

    readonly property var songPaths: backend.songs.map(s => s.path)

    function songsOf(paths) {
        const wanted = {};
        paths.forEach(p => wanted[p] = true);
        return backend.songs.filter(s => wanted[s.path]);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.topMargin: 24
            spacing: 10
            Rectangle {
                visible: page.opened !== null
                implicitWidth: 34; implicitHeight: 32; radius: 4
                color: backHover.hovered ? Theme.hover : "transparent"
                Accessible.role: Accessible.Button
                Accessible.name: backend.texts.back
                Glyph { anchors.centerIn: parent; width: 13; height: 13; kind: "back" }
                HoverHandler { id: backHover }
                TapHandler { onTapped: page.opened = null }
            }
            Text {
                Layout.fillWidth: true
                text: page.opened ? (page.opened.title || page.opened.name || backend.texts.unknown_album) : backend.texts.music
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            PillButton {
                text: page.opened ? backend.texts.play_all : backend.texts.shuffle_and_play
                glyph: page.opened ? "play" : "shuffle"
                primary: true
                enabledState: backend.songs.length > 0
                onClicked: page.opened ? backend.playPaths(page.opened.songs, 0) : backend.shuffleAll()
            }
        }

        // Songs | Albums | Artists
        RowLayout {
            Layout.leftMargin: 28
            Layout.topMargin: 12
            Layout.bottomMargin: 8
            visible: page.opened === null
            spacing: 4
            Repeater {
                model: ["songs", "albums", "artists"]
                delegate: Item {
                    required property string modelData
                    implicitWidth: label.implicitWidth + 24
                    implicitHeight: 36
                    Text {
                        id: label
                        anchors.centerIn: parent
                        text: backend.texts[modelData]
                        color: page.tab === modelData ? Theme.text : Theme.subtext
                        font.pixelSize: 14
                        font.weight: page.tab === modelData ? Font.DemiBold : Font.Normal
                    }
                    Rectangle {
                        visible: page.tab === modelData
                        anchors.bottom: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 16; height: 3; radius: 2
                        color: Theme.accent
                    }
                    TapHandler { onTapped: page.tab = modelData }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.margins: 32
            visible: !backend.scanning && backend.songs.length === 0
            text: backend.texts.empty_music
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }

        // Songs (all, or of an album or artist).
        ListView {
            id: songList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            visible: page.opened !== null || page.tab === "songs"
            clip: true
            spacing: 0
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            model: page.opened ? page.songsOf(page.opened.songs) : backend.songs
            delegate: SongRow {
                id: songRow
                required property var modelData
                required property int index
                width: songList.width - 12
                song: modelData
                rowIndex: index
                onPlay: {
                    const list = songList.model.map(s => s.path);
                    backend.playPaths(list, index);
                }
                onContextMenu: (x, y) => page.contextMenu([modelData.path], songRow, x, y)
            }
        }

        // Albums or artists.
        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 28
            Layout.rightMargin: 12
            visible: page.opened === null && page.tab !== "songs"
            clip: true
            cellWidth: 184
            cellHeight: 240
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            model: page.tab === "albums" ? backend.albums : backend.artists
            delegate: MediaTile {
                required property var modelData
                width: 168
                round: page.tab === "artists"
                glyph: page.tab === "artists" ? "person" : "album"
                picture: modelData.cover ? backend.fileUrl(modelData.cover) : ""
                title: page.tab === "albums" ? (modelData.title || backend.texts.unknown_album)
                                             : (modelData.name || backend.texts.unknown_artist)
                subtitle: page.tab === "albums" ? (modelData.artist || backend.texts.unknown_artist)
                                                : backend.songCount(modelData.songs.length)
                onOpen: page.opened = modelData
                onPlay: backend.playPaths(modelData.songs, 0)
            }
        }
    }
}
