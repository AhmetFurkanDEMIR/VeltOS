// Bluetooth & devices > Mouse, or > Touchpad (`touchpad: true`), as in
// Windows 11 (KWin's input devices, see inputs.py).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    property bool touchpad: false
    readonly property var i: backend.inputs
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshInputs()

    Card {
        Layout.fillWidth: true
        visible: page.i.loaded === true && (page.touchpad ? !page.i.hasTouchpad : !page.i.hasMouse)
        Label {
            width: parent.width
            text: backend.text(page.touchpad ? "no_touchpad" : "no_mouse")
            color: Theme.text
            font.pixelSize: Theme.titleSize
            wrapMode: Text.WordWrap
        }
    }

    // --- Mouse ---
    ColumnLayout {
        Layout.fillWidth: true
        visible: !page.touchpad && page.i.hasMouse === true
        spacing: 4
        SettingRow {
            Layout.fillWidth: true
            icon: "input-mouse-symbolic"
            title: backend.text("primary_button")
            VComboBox {
                Layout.preferredWidth: 160
                accessibleName: backend.text("primary_button")
                options: [{ value: false, label: backend.text("left") }, { value: true, label: backend.text("right") }]
                currentValue: page.i.leftHanded === true
                onActivated: value => backend.setInput("leftHanded", value, "all")
            }
        }
        SettingRow {
            Layout.fillWidth: true
            icon: "input-mouse-symbolic"
            title: backend.text("pointer_speed")
            wrapControl: true
            VSlider {
                Layout.fillWidth: true
                from: -100
                to: 100
                value: Math.round((page.i.speed || 0) * 100)
                accessibleName: backend.text("pointer_speed")
                onReleased: v => backend.setInput("pointerAcceleration", v / 100, "mouse")
            }
        }
        SettingRow {
            Layout.fillWidth: true
            icon: "go-down-symbolic"
            title: backend.text("scroll_speed")
            wrapControl: true
            VSlider {
                Layout.fillWidth: true
                from: 10
                to: 300
                stepSize: 10
                value: Math.round((page.i.scrollFactor || 1) * 100)
                accessibleName: backend.text("scroll_speed")
                onReleased: v => backend.setInput("scrollFactor", v / 100, "mouse")
            }
        }
        SettingRow {
            Layout.fillWidth: true
            icon: "view-refresh-symbolic"
            title: backend.text("reverse_scroll")
            ToggleSwitch {
                checked: page.i.mouseNaturalScroll === true
                accessibleName: backend.text("reverse_scroll")
                onToggled: on => backend.setInput("naturalScroll", on, "mouse")
            }
        }
    }

    // --- Touchpad ---
    ColumnLayout {
        Layout.fillWidth: true
        visible: page.touchpad && page.i.hasTouchpad === true
        spacing: 4
        SettingRow {
            Layout.fillWidth: true
            icon: "input-touchpad-symbolic"
            title: backend.text("touchpad_on")
            ToggleSwitch {
                checked: page.i.touchpadOn !== false
                accessibleName: backend.text("touchpad_on")
                onToggled: on => backend.setInput("enabled", on, "touchpad")
            }
        }
        SettingRow {
            Layout.fillWidth: true
            icon: "input-touchpad-symbolic"
            title: backend.text("touchpad_speed")
            wrapControl: true
            VSlider {
                Layout.fillWidth: true
                from: -100
                to: 100
                value: Math.round((page.i.touchpadSpeed || 0) * 100)
                accessibleName: backend.text("touchpad_speed")
                onReleased: v => backend.setInput("pointerAcceleration", v / 100, "touchpad")
            }
        }
        SettingRow {
            Layout.fillWidth: true
            icon: "input-touchpad-symbolic"
            title: backend.text("tap_to_click")
            ToggleSwitch {
                checked: page.i.tapToClick === true
                accessibleName: backend.text("tap_to_click")
                onToggled: on => backend.setInput("tapToClick", on, "touchpad")
            }
        }
        SettingRow {
            Layout.fillWidth: true
            icon: "go-down-symbolic"
            title: backend.text("natural_scroll")
            ToggleSwitch {
                checked: page.i.touchpadNaturalScroll !== true
                accessibleName: backend.text("natural_scroll")
                onToggled: on => backend.setInput("naturalScroll", !on, "touchpad")
            }
        }
    }
}
