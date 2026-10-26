/*
    Bluetooth pairing in Windows 11's "Add a device" style (btpair.py): the
    device with the Bluetooth glyph, what to do, the PIN large ("123 456")
    or a box to type it, and a footer with the accent button (Connect,
    Allow) and Cancel. Closing the window is Cancel.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami

Window {
    id: dialog
    objectName: "bluetoothPair"

    readonly property bool dark: backend.darkMode
    readonly property color accent: backend.accent !== "" ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                                          : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color surface: dark ? "#2B2B2B" : "#FFFFFF"
    readonly property color footer: dark ? "#202020" : "#F3F3F3"
    readonly property color text: dark ? "#FFFFFF" : "#1B1B1B"
    readonly property color subtext: dark ? "#C5C5C5" : "#5D5D5D"
    readonly property color edge: dark ? "#3D3D3D" : "#E5E5E5"
    readonly property bool asks: ["pin", "passkey"].includes(backend.kind)
    readonly property bool shows: ["confirm", "display"].includes(backend.kind)
    readonly property bool canAnswer: backend.kind !== "display"
    property bool answered: false
    // Width and height each follow one value (bound to each other they loop).
    readonly property int fixedHeight: content.implicitHeight + footerBar.height

    function reply(yes) {
        if (answered || (yes && asks && entry.text.trim() === ""))
            return;
        // Set first: the answer quits the program, which closes this window
        // at once, and its onClosing must not answer "no" after the "yes".
        answered = true;
        backend.answer(yes, entry.text);
    }

    title: backend.text("pair_title")
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
        signal clicked()
        implicitWidth: Math.max(120, caption.implicitWidth + 40)
        implicitHeight: 32
        radius: 4
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
            onTapped: button.clicked()
        }
    }

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 16

        Text {
            Layout.fillWidth: true
            Layout.topMargin: 24
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            text: backend.text("pair_title")
            color: dialog.text
            font.pixelSize: 20
            font.weight: Font.DemiBold
        }

        // The device: the Bluetooth glyph in an accent circle, its name.
        RowLayout {
            Layout.fillWidth: true
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
                    source: "bluetooth-symbolic"
                    isMask: true
                    color: dialog.accent
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    objectName: "deviceName"
                    Layout.fillWidth: true
                    text: backend.name
                    color: dialog.text
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Text {
                    text: "Bluetooth"
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
            text: backend.message
            color: dialog.text
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            lineHeight: 1.15
        }

        // The PIN, large, as Windows shows it.
        Rectangle {
            visible: dialog.shows
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            implicitHeight: 64
            radius: 6
            color: dialog.dark ? "#323232" : "#F9F9F9"
            border.width: 1
            border.color: dialog.edge
            Text {
                objectName: "code"
                anchors.centerIn: parent
                text: backend.code
                color: dialog.text
                font.pixelSize: 30
                font.weight: Font.DemiBold
                font.letterSpacing: 3
            }
        }

        // Typing the device's PIN.
        Rectangle {
            visible: dialog.asks
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
                objectName: "entry"
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                verticalAlignment: TextInput.AlignVCenter
                color: dialog.text
                selectionColor: dialog.accent
                selectedTextColor: "#FFFFFF"
                font.pixelSize: 14
                maximumLength: backend.kind === "passkey" ? 6 : 16
                inputMethodHints: backend.kind === "passkey" ? Qt.ImhDigitsOnly : Qt.ImhNone
                validator: RegularExpressionValidator {
                    regularExpression: backend.kind === "passkey" ? /[0-9]{0,6}/ : /.{0,16}/
                }
                focus: dialog.asks
                onAccepted: dialog.reply(true)
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

        Item { Layout.preferredHeight: 8 }
    }

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
                objectName: "yesButton"
                visible: dialog.canAnswer
                Layout.fillWidth: true
                primary: true
                label: ["authorize", "service"].includes(backend.kind) ? backend.text("allow")
                                                                     : backend.text("connect")
                onClicked: dialog.reply(true)
            }
            Button {
                objectName: "noButton"
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
