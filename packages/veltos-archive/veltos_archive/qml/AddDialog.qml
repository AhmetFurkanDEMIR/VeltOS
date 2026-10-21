// WinRAR's "Archive name and parameters": name, format, compression
// method and a password, for new archives.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

WinDialog {
    id: dialog
    property var sources: []
    property string format: "zip"
    property string level: "normal"
    property string password: ""
    property bool encryptNames: false
    signal accepted(string name, string format, string level, string password, bool encryptNames)
    signal rejected()

    title: backend.texts.add_title
    width: Math.min(560, (parent ? parent.width : 560) - 48)

    function prepare(list) {
        sources = list;
        format = "zip";
        level = "normal";
        password = "";
        encryptNames = false;
        nameField.text = backend.defaultArchiveName(list);
    }

    Text {
        text: backend.texts.archive_name
        color: Theme.text
        font.pixelSize: Theme.bodySize
    }
    TextBox {
        id: nameField
        objectName: "archiveName"
        Layout.fillWidth: true
        selectByMouse: true
        onAccepted: okButton.clicked()
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 6
        spacing: 32
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            spacing: 2
            Text {
                text: backend.texts.archive_format
                color: Theme.text
                font.pixelSize: Theme.bodySize
                font.weight: Font.DemiBold
                Layout.bottomMargin: 4
            }
            Repeater {
                model: [{ k: "zip", l: "ZIP" }, { k: "7z", l: "7Z" }, { k: "tar.gz", l: "TAR.GZ" },
                        { k: "tar.xz", l: "TAR.XZ" }]
                delegate: Choice {
                    required property var modelData
                    objectName: "format_" + modelData.k
                    text: modelData.l
                    selected: dialog.format === modelData.k
                    onClicked: {
                        dialog.format = modelData.k;
                        nameField.text = backend.withFormat(nameField.text, modelData.k);
                    }
                }
            }
            Choice {
                enabled: false
                text: "RAR"
            }
        }
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: backend.texts.compression
                color: Theme.text
                font.pixelSize: Theme.bodySize
                font.weight: Font.DemiBold
                Layout.bottomMargin: 4
            }
            Repeater {
                model: ["store", "fastest", "fast", "normal", "good", "best"]
                delegate: Choice {
                    required property string modelData
                    enabled: dialog.format === "zip" || dialog.format === "7z"
                    text: backend.texts["level_" + modelData]
                    selected: dialog.level === modelData
                    onClicked: dialog.level = modelData
                }
            }
        }
    }
    Text {
        Layout.fillWidth: true
        text: backend.texts.rar_note
        color: Theme.subtext
        font.pixelSize: Theme.captionSize
        wrapMode: Text.Wrap
    }
    WinButton {
        enabled: dialog.format === "zip" || dialog.format === "7z"
        text: backend.texts.set_password + (dialog.password !== "" ? "  ✓" : "")
        onClicked: passwordDialog.open()
    }

    PasswordDialog {
        id: passwordDialog
        mode: "new"
        canEncryptNames: dialog.format === "7z"
        onAccepted: (password, names) => {
            dialog.password = password;
            dialog.encryptNames = names;
        }
    }

    buttons: [
        Item { Layout.fillWidth: true },
        WinButton {
            id: okButton
            objectName: "addOk"
            accent: true
            text: backend.texts.ok
            enabled: nameField.text.trim() !== ""
            onClicked: {
                dialog.close();
                dialog.accepted(nameField.text.trim(), dialog.format, dialog.level, dialog.password,
                                dialog.encryptNames);
            }
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
