// Outlook's Settings window: Accounts (email accounts with Remove, Add
// account, the signature), General (appearance) and Mail (layout).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Popup {
    id: dialog

    property string section: "accounts"
    signal addAccount()

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(parent.width - 80, Math.round(860 * Theme.textScale))
    height: Math.min(parent.height - 80, 580)
    modal: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    Overlay.modal: Scrim {}
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 140 * Theme.anim }
        NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 180 * Theme.anim; easing.type: Easing.OutCubic }
    }
    background: Rectangle {
        radius: 8
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
    }

    contentItem: RowLayout {
        spacing: 0

        // Sections
        Rectangle {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            color: Theme.dark ? "#242424" : "#FAFAFA"
            radius: 8
            Rectangle { anchors.right: parent.right; width: 8; height: parent.height; color: parent.color }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 2
                Text {
                    Layout.bottomMargin: 10
                    Layout.leftMargin: 8
                    text: backend.text("settings")
                    color: Theme.text
                    font.pixelSize: Math.round(20 * Theme.textScale)
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: [{ key: "accounts", icon: "person" }, { key: "general", icon: "settings" },
                            { key: "mail", icon: "mail" }]
                    delegate: Rectangle {
                        id: nav
                        required property var modelData
                        readonly property bool current: dialog.section === modelData.key
                        Layout.fillWidth: true
                        implicitHeight: 36
                        radius: Theme.radius
                        color: current ? Theme.selectedFolder : (navHover.hovered ? Theme.hoverCanvas : "transparent")
                        Rectangle {
                            visible: nav.current
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: 3; height: 16; radius: 1.5; color: Theme.brand
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            spacing: 10
                            Glyph { Layout.preferredWidth: 18; Layout.preferredHeight: 18; kind: nav.modelData.icon
                                    color: Theme.text }
                            Text {
                                Layout.fillWidth: true
                                text: backend.text(nav.modelData.key)
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                                font.weight: nav.current ? Font.DemiBold : Font.Normal
                            }
                        }
                        HoverHandler { id: navHover }
                        TapHandler { onTapped: dialog.section = nav.modelData.key }
                    }
                }
                Item { Layout.fillHeight: true }
            }
        }

        // Content
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 24
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: backend.text(dialog.section === "accounts" ? "email_accounts" : dialog.section)
                    color: Theme.text
                    font.pixelSize: Math.round(18 * Theme.textScale)
                    font.weight: Font.DemiBold
                }
                FlatButton { icon: "close"; showText: false; iconSize: 14; tip: backend.text("close"); onClicked: dialog.close() }
            }

            // Accounts
            ColumnLayout {
                visible: dialog.section === "accounts"
                Layout.fillWidth: true
                spacing: 10
                Text {
                    text: backend.text("email_accounts_sub")
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                }
                Repeater {
                    model: backend.accountList
                    delegate: Rectangle {
                        id: acc
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 60
                        radius: Theme.radius
                        color: Theme.dark ? "#2E2E2E" : "#FAFAFA"
                        border.width: 1
                        border.color: Theme.cardBorder
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 10
                            spacing: 12
                            Avatar { size: 36; initials: acc.modelData.initials; tint: acc.modelData.colour }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Text { text: acc.modelData.name; color: Theme.text; font.pixelSize: Theme.fontSize
                                       font.weight: Font.DemiBold }
                                Text { text: acc.modelData.email; color: Theme.subtext; font.pixelSize: Theme.smallFont + 1 }
                            }
                            VButton {
                                text: backend.text("remove")
                                onClicked: { confirm.account = acc.modelData; confirm.open(); }
                            }
                        }
                    }
                }
                VButton {
                    icon: "add"
                    text: backend.text("add_account")
                    onClicked: { dialog.close(); dialog.addAccount(); }
                }
                Text {
                    Layout.topMargin: 10
                    text: backend.text("signature")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize + 1
                    font.weight: Font.DemiBold
                    visible: backend.accountList.length > 0
                }
                Text {
                    text: backend.text("signature_sub")
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont + 1
                    visible: backend.accountList.length > 0
                }
                ComboBox {
                    id: signatureAccount
                    visible: backend.accountList.length > 1
                    Layout.preferredWidth: 300
                    model: backend.accountList
                    textRole: "email"
                    valueRole: "id"
                    onActivated: signature.text = backend.signature(currentValue)
                }
                Rectangle {
                    visible: backend.accountList.length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 110
                    radius: Theme.radius
                    color: Theme.field
                    border.width: 1
                    border.color: Theme.fieldBorder
                    Flickable {
                        anchors.fill: parent
                        anchors.margins: 2
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        TextArea.flickable: TextArea {
                            id: signature
                            wrapMode: TextEdit.Wrap
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            background: null
                            Component.onCompleted: if (backend.accountList.length > 0)
                                                       text = backend.signature(backend.accountList[0].id)
                        }
                    }
                }
                VButton {
                    visible: backend.accountList.length > 0
                    primary: true
                    text: backend.text("save_button")
                    onClicked: backend.setSignature(signatureAccount.visible ? signatureAccount.currentValue
                                                                            : backend.accountList[0].id, signature.text)
                }
            }

            // General
            ColumnLayout {
                visible: dialog.section === "general"
                Layout.fillWidth: true
                spacing: 8
                Text {
                    text: backend.text("appearance")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize + 1
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("appearance_text")
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                }
                Text {
                    Layout.topMargin: 12
                    Layout.fillWidth: true
                    text: backend.text("about_text")
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                }
            }

            // Mail
            ColumnLayout {
                visible: dialog.section === "mail"
                Layout.fillWidth: true
                spacing: 4
                Text {
                    text: backend.text("layout")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize + 1
                    font.weight: Font.DemiBold
                }
                component SettingRow: RowLayout {
                    id: settingRow
                    property string title
                    property string sub
                    property bool on
                    signal toggled(bool on)
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Text { text: settingRow.title; color: Theme.text; font.pixelSize: Theme.fontSize }
                        Text { visible: settingRow.sub !== ""; text: settingRow.sub; color: Theme.subtext
                               font.pixelSize: Theme.smallFont + 1 }
                    }
                    Toggle { on: settingRow.on; onToggled: value => settingRow.toggled(value) }
                }
                SettingRow { title: backend.text("focused_inbox"); sub: backend.text("focused_inbox_sub")
                             on: backend.focusedInbox; onToggled: value => backend.setFocusedInbox(value) }
                SettingRow { title: backend.text("message_preview"); sub: ""
                             on: backend.showPreview; onToggled: value => backend.setShowPreview(value) }
                SettingRow { title: backend.text("sender_images"); sub: ""
                             on: backend.showAvatars; onToggled: value => backend.setShowAvatars(value) }
            }
            Item { Layout.fillHeight: true }
        }
    }

    Popup {
        id: confirm
        property var account: ({})
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        padding: 24
        Overlay.modal: Scrim {}
        background: Rectangle { radius: 8; color: Theme.card; border.width: 1; border.color: Theme.cardBorder }
        contentItem: ColumnLayout {
            spacing: 18
            Text {
                Layout.preferredWidth: 380
                text: backend.textWith("remove_confirm", confirm.account.email || "")
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.Wrap
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                VButton { primary: true; text: backend.text("remove")
                          onClicked: { backend.removeAccount(confirm.account.id); confirm.close(); } }
                VButton { text: backend.text("cancel"); onClicked: confirm.close() }
            }
        }
    }
}
