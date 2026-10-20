// Accounts > Your info, as in Windows 11: picture, name, account type,
// "Adjust your photo" (AccountsService; see accounts.py).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var me: backend.accounts.me
    property bool saved: false
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshAccounts()

    Card {
        Layout.fillWidth: true
        Layout.bottomMargin: 14
        ColumnLayout {
            width: parent.width
            spacing: 6
            Avatar {
                Layout.alignment: Qt.AlignHCenter
                size: 128
                source: page.me.icon || ""
            }
            Label {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 6
                text: page.me.realName || page.me.name
                color: Theme.text
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }
            Label {
                Layout.alignment: Qt.AlignHCenter
                text: page.me.name + " · " + (page.me.admin ? backend.text("administrator")
                                                             : backend.text("standard_user"))
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "folder-pictures-symbolic"
        title: backend.text("adjust_photo")
        VButton {
            text: backend.text("choose_file")
            onClicked: backend.choosePicture()
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "user-info-symbolic"
        title: backend.text("your_name")
        VTextField {
            id: nameField
            Layout.preferredWidth: 240
            text: page.me.realName || ""
            onTextChanged: page.saved = false
            onAccepted: save.clicked()
        }
        VButton {
            id: save
            primary: true
            text: page.saved ? backend.text("saved") : backend.text("save")
            enabledState: nameField.text.trim().length > 0 && nameField.text.trim() !== (page.me.realName || "")
            onClicked: {
                backend.setRealName(nameField.text.trim());
                page.saved = true;
            }
        }
    }
    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 18
        icon: "dialog-password-symbolic"
        title: backend.text("sign_in_options")
        description: backend.text("password_desc")
        onActivated: page.itemActivated({ action: "", page: "signin", pageId: "accounts" })
    }
}
