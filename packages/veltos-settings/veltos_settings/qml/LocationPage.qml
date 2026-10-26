// Privacy & security > Location, as Windows 11's page: location services
// (shared with VeltOS Maps), the default location Maps uses when the PC
// cannot find its own (set in Maps, as Windows does), and how location is
// found and where it goes.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    readonly property var place: backend.defaultLocation
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: {
        backend.refreshPrefs();
        backend.refreshDefaultLocation();
    }

    // Maps saves the default location while this page is open.
    Timer {
        interval: 3000
        repeat: true
        running: true
        onTriggered: backend.refreshDefaultLocation()
    }

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

    SectionLabel {
        text: backend.text("default_location")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "go-home-symbolic"
        title: backend.text("default_location")
        description: page.place.set === true
                     ? backend.format("default_location_value", page.place.label)
                     : backend.text("default_location_desc")
        VButton {
            text: backend.text("default_location_set")
            onClicked: backend.setDefaultLocation()
        }
        VButton {
            visible: page.place.set === true
            text: backend.text("default_location_clear")
            onClicked: backend.clearDefaultLocation()
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
