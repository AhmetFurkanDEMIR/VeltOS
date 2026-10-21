// Playlists of Windows 11 Media Player: the playlists as tiles with "New
// playlist"; a chosen playlist shows its songs (play all, remove a song,
// delete the playlist).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    property string selected: ""
    signal openPlaylist(string name)
    readonly property var playlist: {
        for (const p of backend.playlists) {
            if (p.name === selected)
                return p;
        }
        return null;
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.topMargin: 24
            Layout.bottomMargin: 16
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: page.playlist ? page.playlist.name : backend.texts.playlists
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            PillButton {
                visible: page.playlist !== null
                text: backend.texts.play_all
                glyph: "play"
                primary: true
                enabledState: page.playlist !== null && page.playlist.items.length > 0
                onClicked: backend.playPaths(page.playlist.items.map(i => i.path), 0)
            }
            PillButton {
                visible: page.playlist !== null
                text: backend.texts.delete_playlist
                onClicked: {
                    backend.deletePlaylist(page.playlist.name);
                    page.openPlaylist("");
                }
            }
            PillButton {
                visible: page.playlist === null
                text: backend.texts.new_playlist
                glyph: "add"
                onClicked: nameDialog.open()
            }
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            visible: page.playlist ? page.playlist.items.length === 0 : backend.playlists.length === 0
            text: page.playlist ? backend.texts.empty_playlist : backend.texts.empty_playlists
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }
        ListView {
            id: songs
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            visible: page.playlist !== null
            clip: true
            model: page.playlist ? page.playlist.items : []
            ScrollBar.vertical: ScrollBar {}
            delegate: SongRow {
                required property var modelData
                required property int index
                width: songs.width - 12
                song: modelData
                rowIndex: index
                showRemove: true
                onPlay: backend.playPaths(page.playlist.items.map(i => i.path), index)
                onRemove: backend.removeFromPlaylist(page.playlist.name, index)
            }
        }
        GridView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 28
            visible: page.playlist === null
            clip: true
            cellWidth: 184
            cellHeight: 240
            model: backend.playlists
            delegate: MediaTile {
                required property var modelData
                width: 168
                glyph: "playlist"
                picture: modelData.cover ? backend.fileUrl(modelData.cover) : ""
                title: modelData.name
                subtitle: backend.songCount(modelData.items.length)
                onOpen: page.openPlaylist(modelData.name)
                onPlay: backend.playPaths(modelData.items.map(i => i.path), 0)
            }
        }
    }

    Popup {
        id: nameDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 380
        modal: true
        padding: 24
        Overlay.modal: Rectangle { color: "#40000000" }
        onOpened: {
            nameField.text = "";
            nameField.forceActiveFocus();
        }
        function create() {
            const name = backend.createPlaylist(nameField.text);
            nameDialog.close();
            page.openPlaylist(name);
        }
        background: Rectangle { radius: 8; color: Theme.card; border.width: 1; border.color: Theme.fieldBorder }
        contentItem: ColumnLayout {
            spacing: 14
            Text { text: backend.texts.playlist_name; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
            TextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: backend.texts.untitled_playlist
                color: Theme.text
                onAccepted: nameDialog.create()
                background: Rectangle { radius: 4; color: Theme.field; border.width: 1
                                        border.color: nameField.activeFocus ? Theme.accent : Theme.fieldBorder }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                PillButton { Layout.fillWidth: true; text: backend.texts.create; primary: true; onClicked: nameDialog.create() }
                PillButton { Layout.fillWidth: true; text: backend.texts.cancel; onClicked: nameDialog.close() }
            }
        }
    }
}
