// System > Notifications, as in Windows 11: do not disturb, sounds, and
// banners per app (Plasma's notification settings, plasmanotifyrc).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: {
        backend.refreshPrefs();
        backend.refreshApps();
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "notification-symbolic"
        title: backend.text("dnd")
        description: backend.text("dnd_desc")
        ToggleSwitch {
            checked: page.p.doNotDisturb === true
            enabledState: page.p.loaded === true
            accessibleName: backend.text("dnd")
            onToggled: on => backend.setDoNotDisturb(on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "audio-volume-high-symbolic"
        title: backend.text("notification_sounds")
        ToggleSwitch {
            checked: page.p.notificationSoundsMuted !== true
            enabledState: page.p.loaded === true
            accessibleName: backend.text("notification_sounds")
            onToggled: on => backend.setPref("notificationSoundsMuted", !on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "dialog-warning-symbolic"
        title: backend.text("critical_in_dnd")
        ToggleSwitch {
            checked: page.p.criticalInDnd !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("critical_in_dnd")
            onToggled: on => backend.setPref("criticalInDnd", on)
        }
    }

    SectionLabel {
        text: backend.text("from_apps")
    }
    Label {
        Layout.fillWidth: true
        visible: backend.apps.loaded === true && backend.apps.notificationApps.length === 0
        text: backend.text("no_notification_apps")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: backend.apps.notificationApps || []
        delegate: SettingRow {
            required property var modelData
            Layout.fillWidth: true
            icon: modelData.icon
            title: modelData.name
            description: backend.text("banners") + ": " + (modelData.banners ? backend.text("on") : backend.text("off"))
            ToggleSwitch {
                checked: modelData.banners
                accessibleName: modelData.name
                onToggled: on => backend.setAppBanners(modelData.id, on)
            }
        }
    }
}
