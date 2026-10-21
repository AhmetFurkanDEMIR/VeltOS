// Navigation pane of Windows 11 Media Player: search, Home, Music library,
// Video library, Play queue, Playlists (with the playlists), Settings.
import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: pane

    property string current: "home"
    signal activated(string id)

    component NavItem: Rectangle {
        id: item
        property string glyph
        property string text
        property string itemId
        readonly property bool chosen: pane.current === itemId
        Layout.fillWidth: true
        Layout.preferredHeight: 38
        radius: 5
        color: chosen ? Theme.selected : (hover.hovered ? Theme.hover : "transparent")
        Accessible.role: Accessible.PageTab
        Accessible.name: text
        Accessible.selected: chosen
        Rectangle {
            visible: item.chosen
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: 3; height: 16; radius: 2
            color: Theme.accent
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 10
            spacing: 14
            Glyph { Layout.preferredWidth: 16; Layout.preferredHeight: 16; kind: item.glyph }
            Text { Layout.fillWidth: true; text: item.text; color: Theme.text; font.pixelSize: Theme.fontSize; elide: Text.ElideRight }
        }
        HoverHandler { id: hover }
        TapHandler { onTapped: pane.activated(item.itemId) }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        anchors.topMargin: 4
        spacing: 2

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            Layout.bottomMargin: 8
            radius: 4
            color: Theme.field
            border.width: 1
            border.color: searchField.activeFocus ? Theme.accent : Theme.fieldBorder
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                TextInput {
                    id: searchField
                    Layout.fillWidth: true
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    clip: true
                    selectByMouse: true
                    onAccepted: if (text.trim() !== "") pane.activated("search:" + text.trim())
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: searchField.text === ""
                        text: backend.texts.search
                        color: Theme.subtext
                        font.pixelSize: Theme.fontSize
                    }
                }
                Glyph { Layout.preferredWidth: 14; Layout.preferredHeight: 14; kind: "search"; color: Theme.subtext }
            }
        }

        NavItem { glyph: "home"; text: backend.texts.home; itemId: "home" }
        NavItem { glyph: "music"; text: backend.texts.music_library; itemId: "music" }
        NavItem { glyph: "video"; text: backend.texts.video_library; itemId: "videos" }
        Rectangle { Layout.fillWidth: true; Layout.margins: 8; height: 1; color: Theme.separator }
        NavItem { glyph: "queue"; text: backend.texts.play_queue; itemId: "queue" }
        NavItem { glyph: "playlist"; text: backend.texts.playlists; itemId: "playlists" }
        Repeater {
            model: backend.playlists
            delegate: NavItem {
                required property var modelData
                Layout.leftMargin: 16
                glyph: "music"
                text: modelData.name
                itemId: "playlist:" + modelData.name
            }
        }
        Item { Layout.fillHeight: true }
        NavItem { glyph: "gear"; text: backend.texts.settings; itemId: "settings" }
    }
}
