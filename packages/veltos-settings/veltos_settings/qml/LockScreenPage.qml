// Personalization > Lock screen (also Privacy & security > Screen lock):
// lock automatically after a time, password on wake (kscreenlockerrc).
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
        icon: "system-lock-screen-symbolic"
        title: backend.text("auto_lock")
        ToggleSwitch {
            checked: page.p.autoLock !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("auto_lock")
            onToggled: on => backend.setPref("autoLock", on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-system-time-symbolic"
        title: backend.text("lock_after")
        VComboBox {
            Layout.preferredWidth: 200
            accessibleName: backend.text("lock_after")
            enabledState: page.p.loaded === true
            options: backend.lockOptions
            currentValue: page.p.autoLock === false ? 0 : page.p.lockAfter
            onActivated: value => backend.setPref("lockAfter", value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "dialog-password-symbolic"
        title: backend.text("lock_on_resume")
        ToggleSwitch {
            checked: page.p.lockOnResume !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("lock_on_resume")
            onToggled: on => backend.setPref("lockOnResume", on)
        }
    }
    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 18
        icon: "preferences-desktop-wallpaper-symbolic"
        title: backend.text("lock_picture")
        description: backend.text("lock_picture_desc")
        onActivated: page.itemActivated({ action: "", page: "background", pageId: "personalization" })
    }
}
