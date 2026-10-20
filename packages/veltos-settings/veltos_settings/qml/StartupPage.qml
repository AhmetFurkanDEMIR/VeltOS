// Apps > Startup: apps that start when you sign in, each with an on/off
// switch (autostart entries; see apps.py).
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
        text: backend.text("startup_desc")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
    Label {
        Layout.fillWidth: true
        visible: backend.apps.loaded === true && backend.apps.startup.length === 0
        text: backend.text("no_startup")
        color: Theme.text
        font.pixelSize: Theme.titleSize
    }
    Repeater {
        model: backend.apps.startup || []
        delegate: SettingRow {
            required property var modelData
            Layout.fillWidth: true
            icon: modelData.icon
            title: modelData.name
            ToggleSwitch {
                checked: modelData.enabled
                accessibleName: modelData.name
                onToggled: on => backend.setStartupEnabled(modelData.id, on)
            }
        }
    }
}
