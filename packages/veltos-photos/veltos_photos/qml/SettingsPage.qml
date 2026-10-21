// Settings of Windows 11 Photos: app theme, the folders the gallery shows
// (add and remove), about.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    signal addFolder()

    component Card: Rectangle {
        id: card
        property string title
        property string description
        default property alias controls: controlsRow.data
        Layout.fillWidth: true
        implicitHeight: Math.max(64, cardRow.implicitHeight + 24)
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
                Text {
                    Layout.fillWidth: true
                    visible: text !== ""
                    text: card.description
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    wrapMode: Text.WordWrap
                }
            }
            RowLayout { id: controlsRow; spacing: 8 }
        }
    }

    component SmallButton: Rectangle {
        id: sb
        property string text
        signal clicked()
        implicitWidth: label.implicitWidth + 28
        implicitHeight: 32
        radius: 4
        color: sbHover.hovered ? Theme.hover : Theme.field
        border.width: 1
        border.color: Theme.fieldBorder
        Accessible.role: Accessible.Button
        Accessible.name: text
        Text { id: label; anchors.centerIn: parent; text: sb.text; color: Theme.text; font.pixelSize: Theme.fontSize }
        HoverHandler { id: sbHover }
        TapHandler { onTapped: sb.clicked() }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 4

            Text {
                Layout.leftMargin: 28
                Layout.topMargin: 18
                Layout.bottomMargin: 14
                text: backend.texts.settings
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.DemiBold
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                Layout.bottomMargin: 28
                spacing: 4

                Text { text: backend.texts.appearance; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.bottomMargin: 4 }
                Card {
                    title: backend.texts.app_theme
                    ComboBox {
                        Layout.preferredWidth: 230
                        model: [backend.texts.theme_light, backend.texts.theme_dark, backend.texts.theme_system]
                        currentIndex: ["light", "dark", "system"].indexOf(backend.theme)
                        onActivated: index => backend.setTheme(["light", "dark", "system"][index])
                    }
                }

                Text { text: backend.texts.folders; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold
                       Layout.topMargin: 14; Layout.bottomMargin: 4 }
                Card {
                    title: backend.texts.folders
                    description: backend.texts.folders_desc
                    SmallButton { text: backend.texts.add_folder; onClicked: page.addFolder() }
                }
                Repeater {
                    model: backend.folders
                    delegate: Card {
                        required property string modelData
                        title: modelData
                        SmallButton { text: backend.texts.remove_folder; onClicked: backend.removeFolder(modelData) }
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
