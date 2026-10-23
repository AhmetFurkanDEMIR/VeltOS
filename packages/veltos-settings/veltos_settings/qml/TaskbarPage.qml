// Personalization > Taskbar, as in Windows 11: taskbar items (Search, Task
// view), other system tray icons and taskbar behaviours (alignment,
// automatically hide, badges, combining buttons, the far corner shows the
// desktop). The values live in Plasma's taskbar (taskbar.py).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var t: backend.taskbar
    readonly property bool ready: t.loaded === true && t.available === true
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshTaskbar()

    SectionLabel {
        Layout.topMargin: 0
        text: backend.text("taskbar_items")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "search-symbolic"
        title: backend.text("taskbar_search")
        VComboBox {
            Layout.preferredWidth: 220
            accessibleName: backend.text("taskbar_search")
            enabledState: page.ready
            options: [
                { value: 0, label: backend.text("taskbar_search_hide") },
                { value: 1, label: backend.text("taskbar_search_icon") },
                { value: 2, label: backend.text("taskbar_search_label") },
                { value: 3, label: backend.text("taskbar_search_box") }
            ]
            currentValue: page.t.search
            onActivated: value => backend.setTaskbar("search", value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "view-dual-symbolic"
        title: backend.text("taskbar_task_view")
        ToggleSwitch {
            checked: page.t.taskView !== false
            enabledState: page.ready
            accessibleName: backend.text("taskbar_task_view")
            onToggled: on => backend.setTaskbar("taskView", on)
        }
    }

    SectionLabel {
        text: backend.text("taskbar_tray_icons")
    }
    Repeater {
        model: page.t.trayItems || []
        delegate: SettingRow {
            required property var modelData
            Layout.fillWidth: true
            icon: modelData.icon
            title: modelData.title
            ToggleSwitch {
                checked: modelData.shown === true
                enabledState: page.ready
                accessibleName: modelData.title
                onToggled: on => backend.setTrayIcon(modelData.id, on)
            }
        }
    }

    SectionLabel {
        text: backend.text("taskbar_behaviors")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "format-justify-center-symbolic"
        title: backend.text("taskbar_alignment")
        VComboBox {
            Layout.preferredWidth: 220
            accessibleName: backend.text("taskbar_alignment")
            enabledState: page.ready
            options: [
                { value: "center", label: backend.text("taskbar_center") },
                { value: "left", label: backend.text("taskbar_left") }
            ]
            currentValue: page.t.alignment
            onActivated: value => backend.setTaskbar("alignment", value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "go-bottom-symbolic"
        title: backend.text("taskbar_autohide")
        ToggleSwitch {
            checked: page.t.autoHide === true
            enabledState: page.ready
            accessibleName: backend.text("taskbar_autohide")
            onToggled: on => backend.setTaskbar("autoHide", on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "notification-active-symbolic"
        title: backend.text("taskbar_badges")
        ToggleSwitch {
            checked: page.t.badges !== false
            enabledState: page.ready
            accessibleName: backend.text("taskbar_badges")
            onToggled: on => backend.setTaskbar("badges", on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "view-list-icons-symbolic"
        title: backend.text("taskbar_combine")
        VComboBox {
            Layout.preferredWidth: 220
            accessibleName: backend.text("taskbar_combine")
            enabledState: page.ready
            options: [
                { value: "always", label: backend.text("taskbar_combine_always") },
                { value: "full", label: backend.text("taskbar_combine_full") },
                { value: "never", label: backend.text("taskbar_combine_never") }
            ]
            currentValue: page.t.combine
            onActivated: value => backend.setTaskbar("combine", value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "user-desktop-symbolic"
        title: backend.text("taskbar_show_desktop")
        ToggleSwitch {
            checked: page.t.showDesktop !== false
            enabledState: page.ready
            accessibleName: backend.text("taskbar_show_desktop")
            onToggled: on => backend.setTaskbar("showDesktop", on)
        }
    }
}
