/*
    A network's key in Windows 11's style (wifikey.py, asked by the VeltOS
    network agent): the network with the Wi-Fi glyph, "Enter the network
    security key" (after a wrong one: "The network security key isn't
    correct"), the key with Windows' reveal button, or user name and
    password for an enterprise network; Next and Cancel in the footer.
    Closing the window is Cancel.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami

Window {
    id: dialog
    objectName: "wifiKey"

    readonly property bool dark: backend.darkMode
    readonly property color accent: backend.accent !== "" ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                                          : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color surface: dark ? "#2B2B2B" : "#FFFFFF"
    readonly property color footer: dark ? "#202020" : "#F3F3F3"
    readonly property color text: dark ? "#FFFFFF" : "#1B1B1B"
    readonly property color subtext: dark ? "#C5C5C5" : "#5D5D5D"
    readonly property color edge: dark ? "#3D3D3D" : "#E5E5E5"
    readonly property color error: dark ? "#FF99A4" : "#C42B1C"
    readonly property bool enterprise: backend.kind === "eap"
    readonly property bool ready: enterprise ? user.text.trim() !== "" && key.text !== ""
                                             : backend.acceptable(key.text)
    property bool answered: false
    // Width and height each follow one value (bound to each other they loop).
    readonly property int fixedHeight: content.implicitHeight + footerBar.height

    function reply(yes) {
        if (answered || (yes && !ready))
            return;
        // Set first: the answer quits the program, which closes this window
        // at once, and its onClosing must not answer "no" after the "yes".
        answered = true;
        backend.answer(yes, user.text, key.text);
    }

    title: backend.text("wifi_key_title")
    color: surface
    flags: Qt.Dialog
    width: 460
    height: fixedHeight
    minimumWidth: 460
    maximumWidth: 460
    minimumHeight: fixedHeight
    maximumHeight: fixedHeight
    onClosing: reply(false)

    component Button: Rectangle {
        id: button
        property string label
        property bool primary: false
        property bool active: true
        signal clicked()
        implicitWidth: Math.max(120, caption.implicitWidth + 40)
        implicitHeight: 32
        radius: 4
        opacity: active ? 1 : 0.45
        color: primary ? (tap.pressed ? Qt.darker(dialog.accent, 1.1) : hover.hovered ? Qt.lighter(dialog.accent, 1.08)
                                                                                     : dialog.accent)
                       : (tap.pressed ? dialog.footer : hover.hovered ? (dialog.dark ? "#3A3A3A" : "#F6F6F6")
                                                                      : dialog.surface)
        border.width: primary ? 0 : 1
        border.color: dialog.edge
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: label
        Keys.onReturnPressed: clicked()
        Keys.onSpacePressed: clicked()
        Text {
            id: caption
            anchors.centerIn: parent
            text: button.label
            color: button.primary ? "#FFFFFF" : dialog.text
            font.pixelSize: 13
        }
        Rectangle {
            visible: button.activeFocus
            anchors.fill: parent
            anchors.margins: -3
            radius: 7
            color: "transparent"
            border.width: 2
            border.color: dialog.text
        }
        HoverHandler { id: hover }
        TapHandler {
            id: tap
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: if (button.active) button.clicked()
        }
    }

    // A Windows 11 text box: grey edge, accent line at the bottom while typing;
    // the key has the reveal (eye) button at its right.
    component Field: Rectangle {
        id: field
        property alias input: entry
        property string placeholder
        property bool secret: false
        property bool revealed: false
        Layout.fillWidth: true
        Layout.leftMargin: 24
        Layout.rightMargin: 24
        implicitHeight: 34
        radius: 4
        color: dialog.dark ? "#323232" : "#FFFFFF"
        border.width: 1
        border.color: entry.activeFocus ? dialog.accent : dialog.edge
        TextInput {
            id: entry
            objectName: field.objectName + "Input"
            anchors.left: parent.left
            anchors.right: eye.visible ? eye.left : parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.leftMargin: 10
            anchors.rightMargin: 6
            verticalAlignment: TextInput.AlignVCenter
            color: dialog.text
            selectionColor: dialog.accent
            selectedTextColor: "#FFFFFF"
            font.pixelSize: 14
            clip: true
            echoMode: field.secret && !field.revealed ? TextInput.Password : TextInput.Normal
            passwordCharacter: "●"
            onAccepted: dialog.reply(true)
            Text {
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                visible: entry.text === ""
                text: field.placeholder
                color: dialog.subtext
                font.pixelSize: 14
            }
        }
        Item {
            id: eye
            visible: field.secret && entry.text !== ""
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 32
            Accessible.role: Accessible.Button
            Accessible.name: backend.text("wifi_key_show")
            Kirigami.Icon {
                anchors.centerIn: parent
                width: 16
                height: 16
                source: field.revealed ? "view-hidden-symbolic" : "view-visible-symbolic"
                isMask: true
                color: dialog.subtext
            }
            // Windows shows the key while the button is held down.
            TapHandler {
                gesturePolicy: TapHandler.WithinBounds
                onPressedChanged: field.revealed = pressed
            }
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 1
            height: entry.activeFocus ? 2 : 0
            color: dialog.accent
        }
    }

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 14

        // The network: the Wi-Fi glyph in an accent circle, its name, "Secured".
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 24
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            spacing: 14
            Rectangle {
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 22
                color: Qt.alpha(dialog.accent, dialog.dark ? 0.25 : 0.12)
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 22
                    height: 22
                    source: "network-wireless-symbolic"
                    isMask: true
                    color: dialog.accent
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    objectName: "networkName"
                    Layout.fillWidth: true
                    text: backend.name
                    color: dialog.text
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Text {
                    text: backend.text("wifi_key_secured")
                    color: dialog.subtext
                    font.pixelSize: 12
                }
            }
        }

        Text {
            objectName: "message"
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            text: backend.text(dialog.enterprise ? "wifi_key_enterprise" : "wifi_key_enter")
            color: dialog.text
            font.pixelSize: 14
            wrapMode: Text.WordWrap
        }

        Field {
            id: userField
            objectName: "userField"
            visible: dialog.enterprise
            placeholder: backend.text("wifi_key_user")
            input.focus: dialog.enterprise
        }
        Field {
            id: keyField
            objectName: "keyField"
            secret: true
            placeholder: backend.text(dialog.enterprise ? "wifi_key_password" : "wifi_key_placeholder")
            input.focus: !dialog.enterprise
        }

        Text {
            objectName: "wrongKey"
            visible: backend.retry
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            text: backend.text(dialog.enterprise ? "wifi_key_wrong_login" : "wifi_key_wrong")
            color: dialog.error
            font.pixelSize: 12
            wrapMode: Text.WordWrap
        }

        Item { Layout.preferredHeight: 8 }
    }

    property alias user: userField.input
    property alias key: keyField.input

    // The footer, in Windows 11 dialogs' grey, with the buttons at the right.
    Rectangle {
        id: footerBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 80
        color: dialog.footer
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: dialog.edge
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 24
            anchors.rightMargin: 24
            spacing: 8
            Item { Layout.fillWidth: true }
            Button {
                objectName: "nextButton"
                Layout.fillWidth: true
                primary: true
                active: dialog.ready
                label: backend.text("next")
                onClicked: dialog.reply(true)
            }
            Button {
                objectName: "cancelButton"
                Layout.fillWidth: true
                label: backend.text("cancel")
                onClicked: dialog.reply(false)
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: dialog.reply(false)
    }
}
