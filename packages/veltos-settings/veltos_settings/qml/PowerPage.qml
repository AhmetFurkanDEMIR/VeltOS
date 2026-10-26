// System > Power & battery: the power mode for plugged in and on battery
// (veltos-desktop's power-mode helper), when the screen turns off and the
// PC sleeps, what the power button and the lid do (PowerDevil, powerdevilrc).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    readonly property bool hasBattery: backend.prefs.hasBattery === true
    // Windows 11's three power modes; one the PC does not offer stays in the
    // list, greyed (power-profiles-daemon reports what the hardware has).
    readonly property var modeNames: ({
        "power-saver": "power_saver",
        "balanced": "power_balanced",
        "performance": "power_performance"
    })
    readonly property var modeIcons: ({
        "power-saver": "power-profile-power-saver-symbolic",
        "balanced": "power-profile-balanced-symbolic",
        "performance": "power-profile-performance-symbolic"
    })
    readonly property var modeOptions: ["power-saver", "balanced", "performance"].map(mode => {
        const offered = (page.p.powerModes || []).indexOf(mode) >= 0;
        return {
            value: mode,
            enabled: offered,
            label: offered ? backend.text(page.modeNames[mode])
                           : backend.format("power_mode_not_supported", backend.text(page.modeNames[mode]))
        };
    })
    readonly property string activeMode: page.p.powerMode || ""
    // The mode a source really gets: the chosen one, or Balanced (then the
    // first one offered) when this PC does not have it (the helper's rule).
    function effective(mode) {
        const offered = page.p.powerModes || [];
        if (offered.indexOf(mode) >= 0)
            return mode;
        return offered.indexOf("balanced") >= 0 ? "balanced" : (offered[0] || "");
    }
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SectionLabel {
        Layout.topMargin: 0
        text: backend.text("power_section")
    }

    // Power mode: one card like Windows 11's expander, the mode for each
    // power source beneath its heading.
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: modeColumn.implicitHeight
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder

        ColumnLayout {
            id: modeColumn
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 18
                Layout.topMargin: 16
                Layout.bottomMargin: 16
                spacing: 16
                Rectangle {
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    radius: 18
                    color: Qt.alpha(Theme.accent, 0.14)
                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: 20
                        height: 20
                        source: page.modeIcons[page.activeMode] || "power-profile-balanced-symbolic"
                        color: Theme.accent
                        isMask: true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: backend.text("power_mode")
                        color: Theme.text
                        font.pixelSize: Theme.titleSize
                    }
                    Label {
                        Layout.fillWidth: true
                        text: backend.text("power_mode_desc")
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.WordWrap
                    }
                }
                // A PC without a battery has one mode: chosen right here.
                VComboBox {
                    visible: !page.hasBattery
                    Layout.preferredWidth: 260
                    accessibleName: backend.text("power_mode")
                    enabledState: page.p.loaded === true && page.p.powerModesAvailable === true
                    options: page.modeOptions
                    currentValue: page.effective(page.p.powerModeAC || "")
                    onActivated: value => backend.setPowerMode("ac", value)
                }
                // "Now: Balanced", as a small accent chip.
                Rectangle {
                    visible: page.activeMode !== "" && page.hasBattery
                    Layout.preferredHeight: 26
                    Layout.preferredWidth: nowLabel.implicitWidth + 20
                    radius: 13
                    color: Qt.alpha(Theme.accent, 0.12)
                    Label {
                        id: nowLabel
                        anchors.centerIn: parent
                        text: page.activeMode ? backend.format("power_mode_now", backend.text(page.modeNames[page.activeMode])) : ""
                        color: Theme.accent
                        font.pixelSize: Theme.bodySize
                        font.weight: Font.DemiBold
                    }
                }
            }

            Repeater {
                // Plugged in and On battery, on PCs with a battery.
                model: page.hasBattery ? ["ac", "battery"] : []
                delegate: ColumnLayout {
                    required property string modelData
                    readonly property bool current: page.p.powerSource === modelData
                    Layout.fillWidth: true
                    spacing: 0
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: Theme.cardBorder
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 70
                        Layout.rightMargin: 18
                        Layout.topMargin: 10
                        Layout.bottomMargin: 10
                        spacing: 12
                        Kirigami.Icon {
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                            source: modelData === "ac" ? "ac-adapter-symbolic" : "battery-good-symbolic"
                            color: Theme.subtext
                            isMask: true
                        }
                        Label {
                            Layout.fillWidth: true
                            text: backend.text(modelData === "ac" ? "plugged_in" : "on_battery")
                                  + (current ? "  ·  " + backend.text("power_source_now") : "")
                            color: Theme.text
                            font.pixelSize: Theme.bodySize + 1
                            elide: Text.ElideRight
                        }
                        VComboBox {
                            Layout.preferredWidth: 260
                            accessibleName: backend.text(modelData === "ac" ? "plugged_in" : "on_battery")
                            enabledState: page.p.loaded === true && page.p.powerModesAvailable === true
                            options: page.modeOptions
                            currentValue: page.effective((modelData === "ac" ? page.p.powerModeAC : page.p.powerModeBattery) || "")
                            onActivated: value => backend.setPowerMode(modelData, value)
                        }
                    }
                }
            }
        }
    }
    Label {
        Layout.fillWidth: true
        Layout.topMargin: 4
        visible: page.hasBattery
        wrapMode: Text.WordWrap
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
        text: backend.text("power_mode_auto_note")
    }
    Label {
        Layout.fillWidth: true
        visible: page.p.loaded === true && page.p.powerModesAvailable !== true
        wrapMode: Text.WordWrap
        color: Theme.danger
        font.pixelSize: Theme.bodySize
        text: backend.text("power_modes_unavailable")
    }
    Label {
        Layout.fillWidth: true
        visible: page.p.powerModeError === true
        wrapMode: Text.WordWrap
        color: Theme.danger
        font.pixelSize: Theme.bodySize
        text: backend.text("power_mode_change_failed")
    }

    SectionLabel {
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
