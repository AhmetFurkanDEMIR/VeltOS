// System > Power & battery: when the screen turns off and the PC sleeps,
// what the power button and the lid do (PowerDevil, powerdevilrc).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    readonly property bool hasBattery: backend.prefs.hasBattery === true
    readonly property var powerModeNames: ({
        "power-saver": "power_saver",
        "balanced": "power_balanced",
        "performance": "power_performance"
    })
    readonly property var powerModeOptions: (page.p.powerModes || []).map(
        mode => ({value: mode, label: backend.text(page.powerModeNames[mode])}))
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SectionLabel {
        Layout.topMargin: 0
        text: backend.text("power_mode")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "battery-symbolic"
        title: backend.text("power_mode")
        VComboBox {
            Layout.preferredWidth: 200
            accessibleName: backend.text("power_mode")
            enabledState: page.p.loaded === true && page.p.powerModesAvailable === true
            options: page.powerModeOptions
            currentValue: page.p.powerMode || ""
            onActivated: value => backend.setPowerMode(value)
        }
    }
    Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        opacity: 0.75
        text: backend.text("power_mode_auto_note")
    }
    Label {
        Layout.fillWidth: true
        visible: page.p.powerModesAvailable === true && (page.p.powerModes || []).indexOf("performance") < 0
        wrapMode: Text.WordWrap
        opacity: 0.75
        text: backend.text("power_mode_performance_unavailable")
    }
    Label {
        Layout.fillWidth: true
        visible: page.p.loaded === true && page.p.powerModesAvailable !== true
        wrapMode: Text.WordWrap
        color: palette.brightText
        text: backend.text("power_modes_unavailable")
    }
    Label {
        Layout.fillWidth: true
        visible: page.p.powerModeError === true
        wrapMode: Text.WordWrap
        color: palette.brightText
        text: backend.text("power_mode_change_failed")
    }

    SectionLabel {
        Layout.topMargin: 0
        text: backend.text("screen_sleep")
    }
    Repeater {
        model: [
            ["screenOffAC", "screen_off_ac", "video-display-symbolic", true],
            ["sleepAC", "sleep_ac", "weather-clear-night-symbolic", true],
            ["screenOffBattery", "screen_off_battery", "video-display-symbolic", page.hasBattery],
            ["sleepBattery", "sleep_battery", "weather-clear-night-symbolic", page.hasBattery]
        ]
        delegate: SettingRow {
            required property var modelData
            Layout.fillWidth: true
            visible: modelData[3]
            icon: modelData[2]
            title: backend.text(modelData[1])
            VComboBox {
                Layout.preferredWidth: 200
                accessibleName: backend.text(modelData[1])
                enabledState: page.p.loaded === true
                options: backend.timeoutOptions
                currentValue: page.p[modelData[0]]
                onActivated: value => backend.setPref(modelData[0], value)
            }
        }
    }

    SectionLabel {
        text: backend.text("power_button")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "system-shutdown-symbolic"
        title: backend.text("power_button")
        VComboBox {
            Layout.preferredWidth: 200
            accessibleName: backend.text("power_button")
            enabledState: page.p.loaded === true
            options: backend.powerActionOptions
            currentValue: page.p.powerButton
            onActivated: value => backend.setPref("powerButton", value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        visible: page.hasBattery
        icon: "computer-symbolic"
        title: backend.text("lid_action")
        VComboBox {
            Layout.preferredWidth: 200
            accessibleName: backend.text("lid_action")
            enabledState: page.p.loaded === true
            options: backend.powerActionOptions
            currentValue: page.p.lidAction
            onActivated: value => backend.setPref("lidAction", value)
        }
    }
}
