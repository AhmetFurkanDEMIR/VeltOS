// Accounts > Sign-in options: change the password (current, new,
// confirm, like Windows), and whether waking up asks for it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    property bool expanded: false
    property bool busy: false
    property string result: ""        // "", "ok" or an error text key
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    Connections {
        target: backend
        function onAccountResult(operation, error) {
            if (operation !== "password")
                return;
            page.busy = false;
            page.result = error === "" ? "ok" : error;
            if (error === "") {
                current.text = "";
                fresh.text = "";
                confirm.text = "";
                page.expanded = false;
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "dialog-password-symbolic"
        title: backend.text("password")
        description: backend.text("password_desc")
        clickable: true
        onClicked: page.expanded = !page.expanded
        VButton {
            text: backend.text("change")
            onClicked: page.expanded = !page.expanded
        }
    }
    Card {
        Layout.fillWidth: true
        visible: page.expanded
        ColumnLayout {
            width: parent.width
            spacing: 8
            Label { text: backend.text("change_password"); color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
            Label { text: backend.text("current_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: current; Layout.preferredWidth: 320; password: true }
            Label { text: backend.text("new_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: fresh; Layout.preferredWidth: 320; password: true }
            Label { text: backend.text("confirm_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: confirm; Layout.preferredWidth: 320; password: true; onAccepted: change.clicked() }
            RowLayout {
                Layout.topMargin: 6
                spacing: 8
                VButton {
                    id: change
                    primary: true
                    text: page.busy ? backend.text("loading") : backend.text("change")
                    enabledState: !page.busy && current.text.length > 0 && fresh.text.length > 0
                    onClicked: {
                        page.busy = true;
                        page.result = "";
                        backend.changePassword(current.text, fresh.text, confirm.text);
                    }
                }
                VButton {
                    text: backend.text("cancel")
                    onClicked: page.expanded = false
                }
            }
        }
    }
    Label {
        Layout.fillWidth: true
        visible: page.result !== ""
        text: page.result === "ok" ? backend.text("password_changed") : (page.result ? backend.text(page.result) : "")
        color: page.result === "ok" ? Theme.text : Theme.danger
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }
    SettingRow {
        Layout.fillWidth: true
        Layout.topMargin: 14
        icon: "system-lock-screen-symbolic"
        title: backend.text("lock_on_resume")
        ToggleSwitch {
            checked: backend.prefs.lockOnResume !== false
            enabledState: backend.prefs.loaded === true
            accessibleName: backend.text("lock_on_resume")
            onToggled: on => backend.setPref("lockOnResume", on)
        }
    }
}
