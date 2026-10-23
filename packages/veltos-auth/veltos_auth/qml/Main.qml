/*
    VeltOS authentication prompt in the layout of Windows 11's User Account
    Control window: a blue band with the shield, the question, the program
    and its details, the administrator's picture and name, the password
    box, Yes and No. `auth` (dialog.py) holds the request and checks the
    password.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Qt5Compat.GraphicalEffects
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window

    readonly property bool dark: auth.darkMode
    readonly property color windowColour: dark ? "#202129" : "#FFFFFF"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
    readonly property color fieldBorder: dark ? "#4A4D5E" : "#8A90A2"
    readonly property color line: dark ? "#363949" : "#E3E6EE"
    readonly property color accent: auth.accent !== "" ? (dark ? Qt.lighter(auth.accent, 1.35) : auth.accent)
                                                       : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color danger: dark ? "#FF99A4" : "#C42B1C"
    readonly property var user: auth.users.length > 0 ? auth.users[auth.userIndex] : null
    property bool showDetails: false

    width: 456
    height: column.implicitHeight
    minimumWidth: 456
    maximumWidth: 456
    minimumHeight: column.implicitHeight
    maximumHeight: column.implicitHeight
    visible: true
    title: auth.tr("title")
    color: windowColour
    flags: Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint

    onClosing: auth.cancel()
    Component.onCompleted: {
        requestActivate();
        passwordField.forceActiveFocus();
    }

    component DialogButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        Layout.fillWidth: true
        implicitHeight: 32
        radius: 5
        opacity: enabledState ? 1 : 0.5
        color: primary ? (buttonHover.hovered ? Qt.lighter(window.accent, 1.08) : window.accent)
                       : (buttonHover.hovered ? (window.dark ? "#363949" : "#F0F2F8") : (window.dark ? "#2E3140" : "#FBFCFE"))
        border.width: primary ? 0 : 1
        border.color: window.line
        activeFocusOnTab: enabledState
        Accessible.role: Accessible.Button
        Accessible.name: label
        Keys.onReturnPressed: if (enabledState) clicked()
        Keys.onSpacePressed: if (enabledState) clicked()
        Text {
            anchors.centerIn: parent
            text: button.label
            color: button.primary ? "#FFFFFF" : window.text
            font.pixelSize: 13
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 8
            color: "transparent"
            border.width: 2
            border.color: window.text
            visible: button.activeFocus
        }
        HoverHandler { id: buttonHover; enabled: button.enabledState }
        TapHandler { enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 0

        // The band: shield and title, as at the top of Windows' window.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#0E1846" }
                GradientStop { position: 1.0; color: "#1F3B8F" }
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                spacing: 14
                // The VeltOS "V" on a shield with a padlock (veltos-auth.svg).
                Kirigami.Icon {
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
                    source: "veltos-auth"
                    fallback: "security-high"
                }
                Text {
                    Layout.fillWidth: true
                    text: auth.tr("title")
                    color: "#FFFFFF"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 24
            spacing: 10

            Text {
                objectName: "question"
                Layout.fillWidth: true
                text: auth.message
                color: window.text
                font.pixelSize: 16
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            RowLayout {
                visible: auth.program !== "" || auth.icon !== ""
                Layout.fillWidth: true
                spacing: 10
                Kirigami.Icon {
                    visible: auth.icon !== ""
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    source: auth.icon
                    // Policies name icons the icon theme may not have
                    // ("system-users"): the VeltOS shield, not a "?".
                    fallback: "veltos-auth"
                }
                Text {
                    Layout.fillWidth: true
                    text: auth.program !== "" ? auth.tr("program") + ": " + auth.program : ""
                    color: window.subtext
                    font.pixelSize: 13
                    elide: Text.ElideMiddle
                }
            }
            Text {
                visible: auth.description !== ""
                Layout.fillWidth: true
                text: auth.description
                color: window.subtext
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }

            // "Show more details": the action and what polkit knows.
            Text {
                text: window.showDetails ? auth.tr("hide_details") : auth.tr("show_details")
                color: window.accent
                font.pixelSize: 13
                HoverHandler { cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: window.showDetails = !window.showDetails }
            }
            ColumnLayout {
                visible: window.showDetails
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: auth.tr("action") + ": " + auth.action
                    color: window.subtext
                    font.pixelSize: 12
                    wrapMode: Text.WrapAnywhere
                }
                Repeater {
                    model: auth.details
                    delegate: Text {
                        required property var modelData
                        Layout.fillWidth: true
                        text: modelData[0] + ": " + modelData[1]
                        color: window.subtext
                        font.pixelSize: 12
                        wrapMode: Text.WrapAnywhere
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; Layout.topMargin: 6; implicitHeight: 1; color: window.line }

            Text {
                Layout.fillWidth: true
                Layout.topMargin: 4
                text: auth.tr("enter_password")
                color: window.text
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }

            // The administrator (several: pick one, like Windows' account tiles).
            Repeater {
                model: auth.users
                delegate: Rectangle {
                    id: tile
                    required property var modelData
                    required property int index
                    readonly property bool chosen: index === auth.userIndex
                    Layout.fillWidth: true
                    implicitHeight: 60
                    radius: 6
                    color: auth.users.length > 1 && (chosen || tileHover.hovered)
                           ? (window.dark ? "#2C2F3D" : "#EEF1F7") : "transparent"
                    border.width: auth.users.length > 1 && chosen ? 1 : 0
                    border.color: window.accent
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 12
                        // Round account picture, as in Windows.
                        Item {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            Rectangle {
                                anchors.fill: parent
                                radius: width / 2
                                color: window.dark ? "#3A3D4E" : "#DCE0EA"
                                Kirigami.Icon {
                                    anchors.centerIn: parent
                                    width: 24
                                    height: 24
                                    source: "user-identity"
                                    visible: picture.status !== Image.Ready
                                    color: window.subtext
                                    isMask: true
                                }
                            }
                            Image {
                                id: picture
                                anchors.fill: parent
                                source: tile.modelData.icon ? "file://" + tile.modelData.icon : ""
                                fillMode: Image.PreserveAspectCrop
                                sourceSize.width: 88
                                sourceSize.height: 88
                                visible: false
                            }
                            Rectangle {
                                id: mask
                                anchors.fill: parent
                                radius: width / 2
                                visible: false
                            }
                            OpacityMask {
                                anchors.fill: parent
                                source: picture
                                maskSource: mask
                                visible: picture.status === Image.Ready
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text {
                                Layout.fillWidth: true
                                text: tile.modelData.realName || tile.modelData.name
                                color: window.text
                                font.pixelSize: 14
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: tile.modelData.name + " · " + auth.tr("administrator")
                                color: window.subtext
                                font.pixelSize: 12
                                elide: Text.ElideRight
                            }
                        }
                    }
                    HoverHandler { id: tileHover; enabled: auth.users.length > 1 }
                    TapHandler { enabled: auth.users.length > 1; onTapped: { auth.selectUser(tile.index); passwordField.forceActiveFocus(); } }
                }
            }

            // Password box: the accent line under the field, like Windows.
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 34
                radius: 4
                color: window.field
                border.width: 1
                border.color: passwordField.activeFocus ? window.accent : window.fieldBorder
                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 2
                    radius: 1
                    color: window.accent
                    visible: passwordField.activeFocus
                }
                TextInput {
                    id: passwordField
                    // Like a Windows text box: in the Tab order, the text cursor over it and
                    // (in a layout) the full height of its box. A plain TextInput has neither.
                    activeFocusOnTab: true
                    HoverHandler { cursorShape: Qt.IBeamCursor }
                    objectName: "password"
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    passwordCharacter: "●"
                    color: window.text
                    selectionColor: window.accent
                    selectedTextColor: "#FFFFFF"
                    font.pixelSize: 13
                    enabled: !auth.busy
                    Accessible.role: Accessible.EditableText
                    Accessible.name: auth.tr("password")
                    onAccepted: yesButton.clicked()
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: passwordField.text === "" && !passwordField.activeFocus
                        text: auth.tr("password")
                        color: window.subtext
                        font.pixelSize: 13
                    }
                }
            }
            Text {
                objectName: "error"
                visible: auth.error !== "" || auth.busy
                Layout.fillWidth: true
                text: auth.busy ? auth.tr("checking") : auth.error
                color: auth.busy ? window.subtext : window.danger
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            Text {
                visible: auth.info !== ""
                Layout.fillWidth: true
                text: auth.info
                color: window.subtext
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 10
                spacing: 8
                DialogButton {
                    id: yesButton
                    objectName: "yes"
                    primary: true
                    label: auth.tr("yes")
                    enabledState: !auth.busy
                    onClicked: {
                        if (!auth.busy) {
                            auth.submit(passwordField.text);
                            passwordField.text = "";
                        }
                    }
                }
                DialogButton {
                    objectName: "no"
                    label: auth.tr("no")
                    onClicked: auth.cancel()
                }
            }
        }
    }

    Shortcut { sequence: "Escape"; onActivated: auth.cancel() }
}
