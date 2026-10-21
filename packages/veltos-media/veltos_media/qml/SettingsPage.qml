// Settings of Windows 11 Media Player: app theme, the music and video
// library locations (add, remove, refresh), about.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    signal addFolder(string kind)

    component Card: Rectangle {
        id: card
        property string title
        property string description
        default property alias controls: controlsRow.data
        Layout.fillWidth: true
        implicitHeight: Math.max(60, cardRow.implicitHeight + 22)
        radius: 6
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        RowLayout {
            id: cardRow
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            spacing: 16
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text { Layout.fillWidth: true; text: card.title; color: Theme.text; font.pixelSize: 14; elide: Text.ElideMiddle }
                Text { Layout.fillWidth: true; visible: text !== ""; text: card.description; color: Theme.subtext
                       font.pixelSize: Theme.smallFont; wrapMode: Text.WordWrap }
            }
            RowLayout { id: controlsRow; spacing: 8 }
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 4
            Text {
                Layout.leftMargin: 32
                Layout.topMargin: 24
                Layout.bottomMargin: 14
                text: backend.texts.settings
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.DemiBold
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                Layout.bottomMargin: 32
                spacing: 4

                Text { text: backend.texts.library; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.bottomMargin: 4 }
                Card {
                    title: backend.texts.music_folders
                    PillButton { text: backend.texts.add_folder; glyph: "add"; onClicked: page.addFolder("music") }
                }
                Repeater {
                    model: backend.musicFolders
                    delegate: Card {
                        required property string modelData
                        Layout.leftMargin: 24
                        title: modelData
                        PillButton { text: backend.texts.remove_folder; onClicked: backend.removeFolder("music", modelData) }
                    }
                }
                Card {
                    Layout.topMargin: 8
                    title: backend.texts.video_folders
                    PillButton { text: backend.texts.add_folder; glyph: "add"; onClicked: page.addFolder("video") }
                }
                Repeater {
                    model: backend.videoFolders
                    delegate: Card {
                        required property string modelData
                        Layout.leftMargin: 24
                        title: modelData
                        PillButton { text: backend.texts.remove_folder; onClicked: backend.removeFolder("video", modelData) }
                    }
                }
                Card {
                    Layout.topMargin: 8
                    title: backend.texts.refresh
                    PillButton { text: backend.texts.refresh; glyph: "rotate"; enabledState: !backend.scanning
                                 onClicked: backend.refresh() }
                }

                Text { text: backend.texts.appearance; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold
                       Layout.topMargin: 14; Layout.bottomMargin: 4 }
                Card {
                    title: backend.texts.app_theme
                    ComboBox {
                        Layout.preferredWidth: 230
                        model: [backend.texts.theme_light, backend.texts.theme_dark, backend.texts.theme_system]
                        currentIndex: ["light", "dark", "system"].indexOf(backend.theme)
                        onActivated: index => backend.setTheme(["light", "dark", "system"][index])
                    }
                }

                Text { text: backend.texts.about; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold
                       Layout.topMargin: 14; Layout.bottomMargin: 4 }
                Card {
                    title: backend.texts.app_title
                    description: backend.texts.about_text.replace("{version}", backend.version)
                }
            }
        }
    }
}
