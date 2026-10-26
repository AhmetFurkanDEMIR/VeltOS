// Time & language > Typing: keyboard layouts (kxkbrc), switched with
// Windows key + Space as on Windows.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    readonly property var layouts: p.layouts || ["us"]
    signal itemActivated(var item)

    function label(value) {
        for (const o of backend.layoutOptions) {
            if (o.value === value)
                return o.label;
        }
        return value;
    }

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SectionLabel {
        Layout.topMargin: 0
        text: backend.text("keyboard_layouts")
    }
    Label {
        Layout.fillWidth: true
        Layout.bottomMargin: 6
        text: backend.text("keyboard_layouts_desc")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
    }
    Repeater {
        model: page.layouts
        delegate: SettingRow {
            required property string modelData
            required property int index
            Layout.fillWidth: true
            icon: "input-keyboard-symbolic"
            title: page.label(modelData)
            VButton {
                visible: index > 0
                text: backend.text("move_up")
                onClicked: {
                    const list = page.layouts.slice();
                    list.splice(index, 1);
                    list.splice(index - 1, 0, modelData);
                    backend.setLayouts(list);
                }
            }
            VButton {
                text: backend.text("remove")
                enabledState: page.layouts.length > 1
                onClicked: backend.setLayouts(page.layouts.filter(l => l !== modelData))
            }
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "list-add-symbolic"
        title: backend.text("add_keyboard")
        VComboBox {
            objectName: "addKeyboard"
            Layout.preferredWidth: 240
            accessibleName: backend.text("add_keyboard")
            options: backend.layoutOptions.filter(o => !page.layouts.includes(o.value))
            // Turkish is offered first (the top of the list), as the product
            // owner asked (2026-10-22); choosing an entry adds it. Nothing is
            // preselected: a preselected Turkish Q could not be added, as
            // choosing the current entry does nothing (product owner,
            // 2026-10-26).
            currentValue: ""
            placeholder: backend.text("choose_keyboard")
            onActivated: value => backend.setLayouts(page.layouts.concat([value]))
        }
    }
}
