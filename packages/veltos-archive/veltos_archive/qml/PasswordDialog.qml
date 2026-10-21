// Password for an archive: to open or extract a locked archive ("open",
// "extract", "view", "test", "wrong") or to protect a new one ("new",
// with a second box and "Encrypt file names").
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

WinDialog {
    id: dialog
    property string mode: "open"
    property string archiveName: ""
    property bool canEncryptNames: false
    readonly property bool creating: mode === "new"
    signal accepted(string password, bool encryptNames)
    signal rejected()

    title: backend.texts.password_title
    onOpened: {
        first.text = "";
        second.text = "";
        mismatch.visible = false;
        first.forceActiveFocus();
    }

    function confirm() {
        if (creating && first.text !== second.text) {
            mismatch.visible = true;
            return;
        }
        dialog.close();
        dialog.accepted(first.text, encrypt.selected);
    }

    Text {
        Layout.fillWidth: true
        text: dialog.creating ? backend.texts.password_new
                              : backend.texts.password_for.replace("{name}", dialog.archiveName)
        color: Theme.text
        font.pixelSize: Theme.bodySize
        wrapMode: Text.Wrap
    }
    Text {
        visible: dialog.mode === "wrong"
        Layout.fillWidth: true
        text: backend.texts.wrong_password
        color: Theme.danger
        font.pixelSize: Theme.bodySize
    }
    TextBox {
        id: first
        objectName: "passwordField"
        Layout.fillWidth: true
        placeholderText: backend.texts.password
        echoMode: show.selected ? TextInput.Normal : TextInput.Password
        onAccepted: dialog.creating ? second.forceActiveFocus() : dialog.confirm()
    }
    TextBox {
        id: second
        visible: dialog.creating
        Layout.fillWidth: true
        placeholderText: backend.texts.password_again
        echoMode: show.selected ? TextInput.Normal : TextInput.Password
        onAccepted: dialog.confirm()
    }
    Text {
        id: mismatch
        visible: false
        text: backend.texts.password_mismatch
        color: Theme.danger
        font.pixelSize: Theme.bodySize
    }
    Choice {
        id: show
        checkbox: true
        text: backend.texts.show_password
        onClicked: selected = !selected
    }
    Choice {
        id: encrypt
        visible: dialog.creating && dialog.canEncryptNames
        checkbox: true
        text: backend.texts.encrypt_names
        onClicked: selected = !selected
    }

    buttons: [
        Item { Layout.fillWidth: true },
        WinButton {
            objectName: "passwordOk"
            accent: true
            text: backend.texts.ok
            onClicked: dialog.confirm()
        },
        WinButton {
            text: backend.texts.cancel
            onClicked: {
                dialog.close();
                dialog.rejected();
            }
        }
    ]
}
