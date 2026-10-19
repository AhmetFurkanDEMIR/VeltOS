// Settings matching the text in "Find a setting".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    property string query
    readonly property var results: backend.search(query)
    signal itemActivated(var item)

    spacing: 6

    Label {
        Layout.fillWidth: true
        visible: page.results.length === 0
        text: backend.text("no_results")
        color: Theme.subtext
        font.pixelSize: Theme.titleSize
        wrapMode: Text.WordWrap
    }

    Repeater {
        model: page.results
        delegate: SettingCard {
            required property var modelData
            Layout.fillWidth: true
            icon: modelData.icon
            title: modelData.title
            description: modelData.description
            note: modelData.pageTitle
            external: modelData.kcm !== "" || modelData.action !== ""
            onActivated: page.itemActivated(modelData)
        }
    }
}
