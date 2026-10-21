// Navigation pane of Windows 11 Photos: Gallery and Favorites, the folders
// (with "Add a folder"), Settings at the bottom.
import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: pane

    property string current: "gallery"
    signal activated(string id)
    signal addFolder()

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
            width: 3
            height: 16
            radius: 2
            color: Theme.accent
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 10
            spacing: 14
            Glyph { Layout.preferredWidth: 16; Layout.preferredHeight: 16; kind: item.glyph }
            Text {
                Layout.fillWidth: true
                text: item.text
                color: Theme.text
                font.pixelSize: Theme.fontSize
                elide: Text.ElideRight
            }
        }
        HoverHandler { id: hover }
        TapHandler { onTapped: item.itemId === "add-folder" ? pane.addFolder() : pane.activated(item.itemId) }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        anchors.topMargin: 4
        spacing: 2

        NavItem { glyph: "gallery"; text: backend.texts.gallery; itemId: "gallery" }
        NavItem { glyph: "heart"; text: backend.texts.favorites; itemId: "favorites" }

        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: 8
            Layout.bottomMargin: 8
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            height: 1
            color: Theme.separator
        }
        Text {
            Layout.leftMargin: 14
            Layout.bottomMargin: 4
            text: backend.texts.folders
            color: Theme.subtext
            font.pixelSize: Theme.smallFont
        }
        Repeater {
            model: backend.folders
            delegate: NavItem {
                required property string modelData
                glyph: "folder"
                text: backend.folderName(modelData)
                itemId: "folder:" + modelData
            }
        }
        NavItem {
            glyph: "add"
            text: backend.texts.add_folder
            itemId: "add-folder"
        }

        Item { Layout.fillHeight: true }

        NavItem { glyph: "gear"; text: backend.texts.settings; itemId: "settings" }
    }
}
