// Accessibility: text size (KDE fonts) and animation effects, as in
// Windows 11's Text size and Visual effects pages.
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

    Card {
        Layout.fillWidth: true
        Layout.bottomMargin: 10
        Label {
            width: parent.width
            text: backend.text("text_size_desc")
            color: Theme.text
            font.pixelSize: Math.round(14 * (preview.value || 100) / 100)
            wrapMode: Text.WordWrap
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-desktop-font-symbolic"
        title: backend.text("text_size")
        wrapControl: true
        VSlider {
            id: preview
            Layout.fillWidth: true
            from: 100
            to: 225
            stepSize: 5
            value: page.p.textSize || 100
            enabledState: page.p.loaded === true
            accessibleName: backend.text("text_size")
            onReleased: v => backend.setTextSize(Math.round(v))
        }
        Label {
            text: Math.round(preview.value) + " %"
            color: Theme.text
            font.pixelSize: Theme.titleSize
        }
    }

    SectionLabel {
        text: backend.text("visual_effects")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "applications-graphics-symbolic"
        title: backend.text("animations")
        description: backend.text("animations_desc")
        ToggleSwitch {
            checked: page.p.animations !== false
            enabledState: page.p.loaded === true
            accessibleName: backend.text("animations")
            onToggled: on => backend.setAnimations(on)
        }
    }
}
