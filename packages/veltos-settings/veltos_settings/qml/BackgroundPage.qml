// Personalization > Background: pick a desktop picture.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var personal: backend.personal
    readonly property string currentPath: personal.wallpaper !== "" ? personal.wallpaper
                                          : (personal.wallpapers.length ? personal.wallpapers[0].path : "")
    readonly property string previewSource: {
        for (const w of personal.wallpapers) {
            if (w.path === currentPath)
                return "file://" + w.preview;
        }
        return currentPath !== "" ? "file://" + currentPath : "";
    }
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPersonal()

    // Preview: the desktop with the chosen picture.
    Rectangle {
        Layout.alignment: Qt.AlignHCenter
        Layout.bottomMargin: 18
        Layout.preferredWidth: 360
        Layout.preferredHeight: 214
        radius: 10
        color: Theme.dark ? "#101118" : "#1B1D24"
        Rectangle {
            id: screen
            anchors.fill: parent
            anchors.margins: 8
            radius: 4
            clip: true
            color: "#0E1846"
            Image {
                anchors.fill: parent
                source: page.previewSource
                sourceSize.width: 720
                sourceSize.height: 400
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }
            Rectangle {
                // Taskbar of the miniature desktop.
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 14
                color: Theme.dark ? "#CC1C1D26" : "#CCF3F5FA"
                Row {
                    anchors.centerIn: parent
                    spacing: 4
                    Repeater {
                        model: 5
                        Rectangle { width: 8; height: 8; radius: 2; color: index === 0 ? Theme.accent : "#8A90A2" }
                    }
                }
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-desktop-wallpaper"
        title: backend.text("personalize_background")
        description: backend.text("choose_photo")
        wrapControl: true

        Flow {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: page.personal.wallpapers
                delegate: Rectangle {
                    id: tile
                    required property var modelData
                    readonly property bool chosen: modelData.path === page.currentPath
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
                    Keys.onSpacePressed: backend.setWallpaper(modelData.path)
                    Keys.onReturnPressed: backend.setWallpaper(modelData.path)

                    Image {
                        anchors.fill: parent
                        anchors.margins: tile.chosen ? 4 : 0
                        source: "file://" + tile.modelData.preview
                        sourceSize.width: 224
                        sourceSize.height: 144
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        opacity: hover.hovered ? 0.85 : 1
                    }
                    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: backend.setWallpaper(tile.modelData.path) }
                }
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "folder-pictures"
        title: backend.text("choose_photo")
        VButton {
            text: backend.text("browse_photos")
            onClicked: backend.browseWallpaper()
        }
    }

    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 18
        icon: "preferences-desktop-wallpaper"
        title: backend.text("more_background")
        description: backend.text("more_background_desc")
        external: true
        onActivated: page.itemActivated({ kcm: "kcm_wallpaper", action: "", page: "" })
    }
}
