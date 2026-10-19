// Time & language > Date & time: the time now, automatic time and the
// time zone. Changing them goes through polkit (it may ask for the
// password).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var t: backend.time
    property date now: new Date()
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshTime()

    Timer {
        interval: 1000
        repeat: true
        running: true
        onTriggered: page.now = new Date()
    }

    ColumnLayout {
        Layout.bottomMargin: 18
        spacing: 0
        Label {
            text: page.now.toLocaleTimeString(Qt.locale(), Locale.ShortFormat)
            color: Theme.text
            font.pixelSize: 40
            font.weight: Font.DemiBold
        }
        Label {
            text: page.now.toLocaleDateString(Qt.locale(), Locale.LongFormat)
            color: Theme.subtext
            font.pixelSize: Theme.titleSize
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-system-time"
        title: backend.text("set_time_automatically")
        ToggleSwitch {
            checked: page.t.automatic
            enabledState: page.t.loaded && page.t.canAutomatic
            accessibleName: backend.text("set_time_automatically")
            onToggled: on => backend.setAutomaticTime(on)
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-desktop-locale"
        title: backend.text("time_zone")
        VComboBox {
            Layout.preferredWidth: 340
            accessibleName: backend.text("time_zone")
            enabledState: page.t.zones.length > 0
            options: page.t.zones
            currentValue: page.t.timezone
            onActivated: value => backend.setTimezone(value)
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "view-calendar"
        title: backend.text("set_manually")
        VButton {
            text: backend.text("change")
            enabledState: !page.t.automatic
            onClicked: page.itemActivated({ kcm: "kcm_clock", action: "", page: "" })
        }
    }

    Label {
        Layout.fillWidth: true
        Layout.topMargin: 10
        text: backend.text("admin_note")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
}
