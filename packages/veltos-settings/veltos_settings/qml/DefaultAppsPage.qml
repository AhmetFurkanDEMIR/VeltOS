// Apps > Default apps: which app opens web links, email, music, videos,
// photos, PDF and text files (xdg-mime, ~/.config/mimeapps.list).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshApps()

    Label {
        Layout.fillWidth: true
        Layout.bottomMargin: 10
        text: backend.text("default_apps_desc")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: backend.apps.groups || []
        delegate: SettingRow {
            required property var modelData
            readonly property var chosen: modelData.options.find(o => o.value === modelData.current)
            Layout.fillWidth: true
            icon: chosen ? chosen.icon : "application-x-executable-symbolic"
            title: modelData.title
            description: chosen ? chosen.label
                         : (modelData.options.length > 0 ? backend.text("choose_default") : backend.text("no_choice"))
            VComboBox {
                Layout.preferredWidth: 240
                accessibleName: modelData.title
                enabledState: modelData.options.length > 0
                options: modelData.options
                currentValue: modelData.current
                onActivated: value => backend.setDefaultApp(modelData.id, value)
            }
        }
    }
}
