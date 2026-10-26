// Privacy & security > Location: VeltOS Maps' access to browser geolocation.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SettingRow {
        Layout.fillWidth: true
        icon: Qt.resolvedUrl("icons/location.svg")
        title: backend.text("location_services")
        description: backend.text("location_services_desc")
        ToggleSwitch {
            checked: page.p.locationEnabled === true
            enabledState: page.p.loaded === true
            accessibleName: backend.text("location_services")
            onToggled: on => backend.setPref("locationEnabled", on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        Layout.topMargin: 14
        icon: "preferences-system-privacy-symbolic"
        title: backend.text("location_provider_title")
        description: backend.text("location_provider_note")
    }
}
