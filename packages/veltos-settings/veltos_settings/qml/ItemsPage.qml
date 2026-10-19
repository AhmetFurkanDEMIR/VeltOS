// A settings page from the catalogue: optional theme picker, then one card
// per setting.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    property var pageData
    signal itemActivated(var item)

    spacing: 6

    Card {
        Layout.fillWidth: true
        Layout.bottomMargin: 18
        visible: page.pageData && page.pageData.themePicker
        ColumnLayout {
            width: parent.width
            spacing: 4
            Label {
                text: backend.text("theme")
                color: Theme.text
                font.pixelSize: Theme.titleSize
                font.weight: Font.DemiBold
            }
            Label {
                text: backend.text("theme_desc")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                Layout.bottomMargin: 10
            }
            ThemePicker {}
        }
    }

    Repeater {
        model: page.pageData ? page.pageData.items : []
        delegate: SettingCard {
            required property var modelData
            Layout.fillWidth: true
            icon: modelData.icon
            title: modelData.title
            description: modelData.description
            external: modelData.kcm !== "" || modelData.action !== ""
            onActivated: page.itemActivated(modelData)
        }
    }
}
