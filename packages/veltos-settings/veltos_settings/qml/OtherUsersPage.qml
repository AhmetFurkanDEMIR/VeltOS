// Accounts > Other users: the other people's accounts on this PC, add one
// (name, user name, password, administrator), change the account type or
// remove it. These ask for the administrator password.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    property bool adding: false
    property bool busy: false
    property string error: ""
    property string removing: ""
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshAccounts()

    Connections {
        target: backend
        function onAccountResult(operation, error) {
            if (operation !== "adduser")
                return;
            page.busy = false;
            page.error = error;
            if (error === "") {
                page.adding = false;
                userName.text = "";
                fullName.text = "";
                password.text = "";
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "system-users-symbolic"
        title: backend.text("add_other_user")
        VButton {
            primary: true
            text: backend.text("add_account")
            onClicked: page.adding = !page.adding
        }
    }
    Card {
        Layout.fillWidth: true
        visible: page.adding
        ColumnLayout {
            width: parent.width
            spacing: 8
            Label { text: backend.text("create_user"); color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
            Label { text: backend.text("full_name"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: fullName; Layout.preferredWidth: 320 }
            Label { text: backend.text("user_name"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: userName; Layout.preferredWidth: 320 }
            Label { text: backend.text("password"); color: Theme.text; font.pixelSize: Theme.bodySize }
            VTextField { id: password; Layout.preferredWidth: 320; password: true }
            RowLayout {
                spacing: 8
                ToggleSwitch {
                    id: admin
                    showLabel: false
                    accessibleName: backend.text("make_admin")
                    onToggled: on => checked = on
                }
                Label { text: backend.text("make_admin"); color: Theme.text; font.pixelSize: Theme.bodySize }
            }
            Label {
                Layout.fillWidth: true
                visible: page.error !== ""
                text: page.error ? backend.text(page.error) : ""
                color: Theme.danger
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.topMargin: 6
                spacing: 8
                VButton {
                    primary: true
                    text: page.busy ? backend.text("loading") : backend.text("add_account")
                    enabledState: !page.busy && userName.text.trim().length > 0 && password.text.length > 0
                    onClicked: {
                        page.busy = true;
                        page.error = "";
                        backend.addUser(userName.text.trim(), fullName.text.trim(), password.text, admin.checked);
                    }
                }
                VButton {
                    text: backend.text("cancel")
                    onClicked: page.adding = false
                }
            }
            Label {
                Layout.fillWidth: true
                text: backend.text("admin_note")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }
    }

    SectionLabel {
        text: backend.text("other_users")
    }
    Label {
        Layout.fillWidth: true
        visible: backend.accounts.loaded === true && backend.accounts.others.length === 0
        text: backend.text("no_other_users")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
    }
    Repeater {
        model: backend.accounts.others || []
        delegate: ColumnLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: 4
            SettingRow {
                Layout.fillWidth: true
                icon: "avatar-default-symbolic"
                title: modelData.realName
                description: modelData.name + " · " + (modelData.admin ? backend.text("administrator")
                                                                      : backend.text("standard_user"))
                VButton {
                    text: modelData.admin ? backend.text("standard_user") : backend.text("administrator")
                    onClicked: backend.setAdmin(modelData.name, !modelData.admin)
                }
                VButton {
                    text: backend.text("remove_account")
                    onClicked: page.removing = page.removing === modelData.name ? "" : modelData.name
                }
            }
            Card {
                Layout.fillWidth: true
                visible: page.removing === modelData.name
                ColumnLayout {
                    width: parent.width
                    spacing: 6
                    Label { text: backend.text("remove_account_q"); color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                    Label { Layout.fillWidth: true; text: backend.text("remove_account_desc"); color: Theme.subtext; font.pixelSize: Theme.bodySize; wrapMode: Text.WordWrap }
                    RowLayout {
                        spacing: 8
                        VButton {
                            primary: true
                            text: backend.text("remove_account")
                            onClicked: {
                                backend.removeUser(modelData.name);
                                page.removing = "";
                            }
                        }
                        VButton {
                            text: backend.text("cancel")
                            onClicked: page.removing = ""
                        }
                    }
                }
            }
        }
    }
}
