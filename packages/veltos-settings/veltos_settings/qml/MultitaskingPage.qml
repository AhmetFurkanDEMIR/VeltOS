// System > Multitasking: snap windows (KWin's screen edges) and desktops
// (VeltOS Task View).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SettingRow {
        Layout.fillWidth: true
        icon: "view-dual-symbolic"
        title: backend.text("snap_windows")
        description: backend.text("snap_windows_desc")
        ToggleSwitch {
            checked: page.p.snapWindows !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("snap_windows")
            onToggled: on => {
                backend.setPref("snapWindows", on);
                backend.setPref("snapMaximize", on);
            }
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "view-grid-symbolic"
        title: backend.text("desktops")
        description: backend.text("desktops_desc")
    }
}
