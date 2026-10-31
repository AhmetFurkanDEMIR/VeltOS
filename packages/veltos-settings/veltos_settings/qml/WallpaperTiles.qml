// The picture tiles of Personalization > Background and > Lock screen:
// VeltOS' wallpapers and any other picture in use, the chosen one framed.
import QtQuick
import QtQuick.Controls
import "."

Flow {
    id: tiles

    // [{name, path, preview, previewDark}] (Personalization.wallpapers()).
    property var wallpapers: []
    property string currentPath: ""
    // Pictures outside the list that are in use (a photo picked with
    // Browse): shown after the wallpapers so they can be chosen again.
    property var extraPaths: []
    signal chosen(string path)

    readonly property var entries: {
        const list = (wallpapers || []).slice();
        const known = list.map(w => w.path);
        for (const path of extraPaths) {
            if (path && known.indexOf(path) < 0) {
                list.push({ name: path.split("/").pop(), path: path, preview: path, previewDark: path });
                known.push(path);
            }
        }
        return list;
    }

    spacing: 8

    Repeater {
        model: tiles.entries
        delegate: Rectangle {
            id: tile
            required property var modelData
            readonly property bool chosen: modelData.path === tiles.currentPath
            width: 112
            height: 72
            radius: 6
            color: "transparent"
            border.width: chosen || activeFocus ? 3 : 0
            border.color: Theme.accent
            activeFocusOnTab: true
            Accessible.role: Accessible.RadioButton
            Accessible.name: modelData.name
            Accessible.checked: chosen
            Keys.onSpacePressed: tiles.chosen(modelData.path)
            Keys.onReturnPressed: tiles.chosen(modelData.path)

            Image {
                anchors.fill: parent
                anchors.margins: tile.chosen ? 4 : 0
                source: "file://" + (Theme.dark ? tile.modelData.previewDark : tile.modelData.preview)
                sourceSize.width: 224
                sourceSize.height: 144
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                opacity: hover.hovered ? 0.85 : 1
            }
            HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: tiles.chosen(tile.modelData.path) }
        }
    }
}
