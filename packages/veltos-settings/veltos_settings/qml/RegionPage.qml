// Time & language > Language & region: display language and regional
// format (Plasma starts the session with them: plasma-localerc).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    property bool changed: false
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-desktop-locale-symbolic"
        title: backend.text("display_language")
        description: backend.text("display_language_desc")
        VComboBox {
            Layout.preferredWidth: 240
            accessibleName: backend.text("display_language")
            enabledState: page.p.loaded === true
            options: backend.languageOptions
            currentValue: page.p.language
            onActivated: value => {
                backend.setLanguage(value);
                page.changed = true;
            }
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-system-time-symbolic"
        title: backend.text("regional_format")
        description: backend.text("regional_format_desc")
        VComboBox {
            Layout.preferredWidth: 240
            accessibleName: backend.text("regional_format")
            enabledState: page.p.loaded === true
            options: page.p.formatOptions || []
            currentValue: page.p.formats
            onActivated: value => {
                backend.setFormats(value);
                page.changed = true;
            }
        }
    }
    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 18
        icon: "input-keyboard-symbolic"
        title: backend.text("keyboard_layouts")
        description: backend.text("keyboard_layouts_desc")
        onActivated: page.itemActivated({ action: "", page: "keyboard", pageId: "time" })
    }
    Label {
        Layout.fillWidth: true
        Layout.topMargin: 10
        visible: page.changed
        text: backend.text("sign_out_note")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
}
