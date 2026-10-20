// System > Display > Night light: on/off, strength, and a sunset-to-sunrise
// schedule (KWin's night colour, kwinrc [NightColor]).
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
        icon: "night-light-symbolic"
        title: backend.text("night_light")
        description: backend.text("night_light_desc")
        ToggleSwitch {
            checked: page.p.nightLight === true
            enabledState: page.p.loaded === true
            accessibleName: backend.text("night_light")
            onToggled: on => backend.setPref("nightLight", on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "weather-clear-night-symbolic"
        title: backend.text("strength")
        wrapControl: true
        VSlider {
            Layout.fillWidth: true
            // 0 % = 6500 K (no change) .. 100 % = 2500 K, like Windows' slider.
            from: 0
            to: 100
            value: page.p.loaded ? Math.round((6500 - page.p.nightTemperature) / 40) : 50
            enabledState: page.p.loaded === true
            accessibleName: backend.text("strength")
            onReleased: v => backend.setPref("nightTemperature", Math.round(6500 - v * 40))
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-system-time-symbolic"
        title: backend.text("schedule_night")
        description: backend.text("schedule_desc")
        ToggleSwitch {
            checked: page.p.nightMode === "Automatic"
            enabledState: page.p.loaded === true && page.p.nightLight === true
            accessibleName: backend.text("schedule_night")
            onToggled: on => backend.setPref("nightMode", on ? "Automatic" : "Constant")
        }
    }
}
