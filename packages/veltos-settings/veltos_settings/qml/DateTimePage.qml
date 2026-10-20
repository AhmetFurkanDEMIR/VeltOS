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
        icon: "preferences-system-time-symbolic"
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
        icon: "preferences-desktop-locale-symbolic"
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
        icon: "preferences-system-time-symbolic"
        title: backend.text("set_manually")
        VButton {
            text: backend.text("change")
            enabledState: !page.t.automatic
            onClicked: {
                dateField.text = Qt.formatDate(page.now, "yyyy-MM-dd");
                timeField.text = Qt.formatTime(page.now, "HH:mm");
                dateDialog.failed = false;
                dateDialog.open();
            }
        }
    }

    Popup {
        id: dateDialog
        property bool failed: false
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 380
        padding: 24
        background: Rectangle {
            radius: Theme.radius
            color: Theme.popup
            border.color: Theme.cardBorder
        }
        contentItem: ColumnLayout {
            spacing: 10
            Label {
                text: backend.text("set_date_time")
                color: Theme.text
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }
            Label { text: backend.text("date"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: dateField; Layout.fillWidth: true; placeholder: "2026-10-20" }
            Label { text: backend.text("time"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: timeField; Layout.fillWidth: true; placeholder: "14:30" }
            Label {
                Layout.fillWidth: true
                text: dateDialog.failed ? backend.text("set_time_failed") : backend.text("date_format_hint")
                color: dateDialog.failed ? Theme.danger : Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.topMargin: 8
                spacing: 8
                Item { Layout.fillWidth: true }
                VButton {
                    primary: true
                    text: backend.text("change")
                    onClicked: {
                        if (backend.setDateTime(dateField.text.trim(), timeField.text.trim()))
                            dateDialog.close();
                        else
                            dateDialog.failed = true;
                    }
                }
                VButton {
                    text: backend.text("cancel")
                    onClicked: dateDialog.close()
                }
            }
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
