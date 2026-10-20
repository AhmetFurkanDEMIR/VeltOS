/*
    VeltOS lock screen in the Windows 11 layout (replaces the Breeze
    LockScreenUi.qml of Plasma's desktop shell, see
    plasma-overrides/org.kde.plasma.desktop.json).

    First the picture with the large time and date. A click or a key slides
    them away: the picture blurs and the account picture, the name and the
    password box appear, with the keyboard layout, battery and power button
    in the bottom-right corner. Esc or a minute without input returns to
    the time.

    Uses the interface of kscreenlocker's greeter like Breeze's version:
    the "authenticator" (startAuthenticating, respond, failed, succeeded,
    hadPrompt, messages), "kscreenlocker_userName",
    "kscreenlocker_userImage", "wallpaper", and LockScreen.qml's root
    (clearPassword, suspendToRam, suspendToRamSupported).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.sessions
import org.kde.plasma.private.keyboardindicator as KeyboardIndicator
import org.kde.plasma.workspace.components as PW
import org.kde.breeze.components

Item {
    id: ui

    readonly property bool turkish: Qt.locale().name.startsWith("tr")
    function tr(en, trText) {
        return turkish ? trText : en;
    }

    property bool signIn: false          // the sign-in view (else the time)
    property bool noPassword: false      // the account needs no password
    property string message: ""
    property date now: new Date()

    function showSignIn(text) {
        if (!signIn) {
            signIn = true;
            message = "";
            authenticator.startAuthenticating();
        }
        idle.restart();
        password.forceActiveFocus();
        if (text) {
            password.insert(password.cursorPosition, text);
        }
    }
    function showClock() {
        signIn = false;
        password.text = "";
        message = "";
    }
    function powerAction(id) {
        powerMenu.visible = false;
        if (id === "sleep") {
            root.suspendToRam();
        } else if (id === "shutdown") {
            sessionManagement.requestShutdown(SessionManagement.Skip);
        } else if (id === "reboot") {
            sessionManagement.requestReboot(SessionManagement.Skip);
        }
    }
    function submit() {
        if (grace.running) {
            return;
        }
        authenticator.respond(password.text);
    }

    Connections {
        target: authenticator
        function onFailed(kind) {
            if (kind != 0) {    // the non-interactive authenticators (fingerprint...)
                return;
            }
            ui.message = ui.tr("The password is incorrect. Try again.", "Parola yanlış. Yeniden deneyin.");
            password.text = "";
            grace.restart();
            shake.start();
        }
        function onSucceeded() {
            if (authenticator.hadPrompt) {
                Qt.quit();
            } else {
                ui.noPassword = true;
            }
        }
        function onInfoMessageChanged() {
            if (authenticator.infoMessage) {
                ui.message = authenticator.infoMessage;
            }
        }
        function onErrorMessageChanged() {
            if (authenticator.errorMessage) {
                ui.message = authenticator.errorMessage;
            }
        }
        function onPromptForSecretChanged() {
            password.forceActiveFocus();
        }
    }
    Connections {
        target: root
        function onClearPassword() {
            password.text = "";
        }
    }

    SessionManagement {
        id: sessionManagement
    }
    KeyboardIndicator.KeyState {
        id: capsLock
        key: Qt.Key_CapsLock
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: ui.now = new Date()
    }
    // Back to the time after a minute without input, as on Windows.
    Timer {
        id: idle
        interval: 60000
        onTriggered: if (password.text === "") ui.showClock()
    }
    // After a wrong password, wait a moment before the next try.
    Timer {
        id: grace
        interval: 2000
        onTriggered: authenticator.startAuthenticating()
    }

    // ---- Background -------------------------------------------------------------

    FastBlur {
        anchors.fill: parent
        source: wallpaper
        radius: 72
        visible: !!wallpaper
        opacity: ui.signIn ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: ui.signIn ? 0.32 : 0.12
        Behavior on opacity { NumberAnimation { duration: 300 } }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onPressed: ui.showSignIn("")
        onPositionChanged: if (ui.signIn) idle.restart()
    }
    focus: true
    Keys.onEscapePressed: ui.showClock()
    Keys.onPressed: event => {
        if (!ui.signIn) {
            ui.showSignIn(event.text.length === 1 && event.text >= " " ? event.text : "");
            event.accepted = true;
        }
    }

    // ---- Time and date --------------------------------------------------------------

    Column {
        id: clock
        anchors.horizontalCenter: parent.horizontalCenter
        y: ui.signIn ? -height : parent.height * 0.11
        opacity: ui.signIn ? 0 : 1
        spacing: 2
        Behavior on y { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
        Behavior on opacity { NumberAnimation { duration: 250 } }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(ui.now, Qt.locale().timeFormat(Locale.ShortFormat)
                                          .replace(/\s*[aA][pP]\s*/, "").replace(/\s*t+\s*/, ""))
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: Math.round(Math.min(ui.height * 0.13, 136))
            font.weight: Font.DemiBold
            layer.enabled: true
            layer.effect: DropShadow { radius: 12; samples: 25; color: "#55000000"; verticalOffset: 2 }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: ui.turkish ? Qt.locale().toString(ui.now, "d MMMM dddd")
                             : Qt.locale().toString(ui.now, "dddd, MMMM d")
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: Math.round(Math.min(ui.height * 0.026, 26))
            layer.enabled: true
            layer.effect: DropShadow { radius: 8; samples: 17; color: "#55000000"; verticalOffset: 1 }
        }
    }

    // ---- Sign in --------------------------------------------------------------------

    ColumnLayout {
        id: signInBox
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: ui.signIn ? -ui.height * 0.04 : ui.height * 0.05
        width: 320
        spacing: 14
        opacity: ui.signIn ? 1 : 0
        visible: opacity > 0
        enabled: ui.signIn
        Behavior on opacity { NumberAnimation { duration: 300 } }
        Behavior on anchors.verticalCenterOffset { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }

        // Account picture (or a person glyph).
        Item {
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 176
            implicitHeight: 176
            Rectangle {
                id: avatarCircle
                anchors.fill: parent
                radius: width / 2
                color: "#C7CDD8"
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: parent.width * 0.55
                    height: width
                    source: "user-symbolic"
                    isMask: true
                    color: "#FFFFFF"
                    visible: avatar.status !== Image.Ready
                }
            }
            Image {
                id: avatar
                anchors.fill: parent
                source: kscreenlocker_userImage !== ""
                        ? "file://" + kscreenlocker_userImage.split("/").map(encodeURIComponent).join("/") : ""
                fillMode: Image.PreserveAspectCrop
                visible: false
            }
            OpacityMask {
                anchors.fill: parent
                source: avatar
                maskSource: avatarCircle
                visible: avatar.status === Image.Ready
            }
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 8
            text: kscreenlocker_userName
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 28
            font.weight: Font.DemiBold
        }

        // Password box with "show" and the arrow, Windows 11 style.
        Rectangle {
            id: field
            visible: !ui.noPassword
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 296
            implicitHeight: 36
            radius: 4
            color: password.activeFocus ? "#FFFFFF" : Qt.rgba(1, 1, 1, 0.82)
            border.width: 1
            border.color: Qt.rgba(0, 0, 0, 0.1)
            transform: Translate { id: shakeOffset; x: 0 }
            Rectangle {
                visible: password.activeFocus
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 1
                height: 2
                color: Kirigami.Theme.highlightColor
            }
            TextInput {
                id: password
                anchors.left: parent.left
                anchors.right: buttons.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 11
                anchors.rightMargin: 4
                echoMode: reveal.checked ? TextInput.Normal : TextInput.Password
                passwordCharacter: "●"
                color: "#1B1B1B"
                font.family: "Inter"
                font.pixelSize: 14
                clip: true
                enabled: !grace.running
                Accessible.name: ui.tr("Password", "Parola")
                onTextChanged: idle.restart()
                Keys.onReturnPressed: ui.submit()
                Keys.onEnterPressed: ui.submit()
                Keys.onEscapePressed: ui.showClock()
                Text {
                    visible: password.text === ""
                    anchors.verticalCenter: parent.verticalCenter
                    text: ui.tr("Password", "Parola")
                    color: "#6B6B6B"
                    font: password.font
                }
            }
            Row {
                id: buttons
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 3
                spacing: 2
                // Show the password while held, like Windows' eye button.
                MouseArea {
                    id: reveal
                    property bool checked: pressed
                    visible: password.text !== ""
                    width: 30
                    height: 28
                    hoverEnabled: true
                    Rectangle {
                        anchors.fill: parent
                        radius: 3
                        color: "#000000"
                        opacity: reveal.containsMouse ? 0.06 : 0
                    }
                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: 16
                        height: 16
                        source: "view-visible-symbolic"
                        isMask: true
                        color: "#3A3A3A"
                    }
                }
                MouseArea {
                    id: go
                    width: 30
                    height: 28
                    hoverEnabled: true
                    onClicked: ui.submit()
                    Accessible.role: Accessible.Button
                    Accessible.name: ui.tr("Sign in", "Oturum aç")
                    Rectangle {
                        anchors.fill: parent
                        radius: 3
                        color: go.containsMouse ? Kirigami.Theme.highlightColor : "#000000"
                        opacity: go.containsMouse ? 1 : 0.06
                    }
                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: 16
                        height: 16
                        source: "go-next-symbolic"
                        isMask: true
                        color: go.containsMouse ? "#FFFFFF" : "#3A3A3A"
                    }
                }
            }
        }

        // Accounts without a password: a Sign in button.
        MouseArea {
            visible: ui.noPassword
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 140
            implicitHeight: 36
            hoverEnabled: true
            onClicked: Qt.quit()
            Accessible.role: Accessible.Button
            Accessible.name: signInText.text
            Rectangle {
                anchors.fill: parent
                radius: 4
                color: "#FFFFFF"
                opacity: parent.containsMouse ? 0.3 : 0.2
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.4)
            }
            Text {
                id: signInText
                anchors.centerIn: parent
                text: ui.tr("Sign in", "Oturum aç")
                color: "#FFFFFF"
                font.family: "Inter"
                font.pixelSize: 14
            }
        }

        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            visible: text !== ""
            text: ui.message !== "" ? ui.message
                  : capsLock.locked ? ui.tr("Caps Lock is on", "Caps Lock açık") : ""
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 14
            wrapMode: Text.Wrap
        }
    }

    SequentialAnimation {
        id: shake
        NumberAnimation { target: shakeOffset; property: "x"; to: -10; duration: 50 }
        NumberAnimation { target: shakeOffset; property: "x"; to: 10; duration: 80 }
        NumberAnimation { target: shakeOffset; property: "x"; to: -6; duration: 70 }
        NumberAnimation { target: shakeOffset; property: "x"; to: 0; duration: 60 }
    }

    // ---- Bottom-right corner: layout, battery, power ------------------------------------

    RowLayout {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        spacing: 8
        opacity: ui.signIn ? 1 : 0.85

        MouseArea {
            visible: layouts.hasMultipleKeyboardLayouts && ui.signIn
            implicitWidth: layoutText.implicitWidth + 16
            implicitHeight: 36
            onClicked: layouts.keyboardLayout.switchToNextLayout()
            PW.KeyboardLayoutSwitcher {
                id: layouts
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
            Text {
                id: layoutText
                anchors.centerIn: parent
                text: layouts.layoutNames.shortName.toUpperCase()
                color: "#FFFFFF"
                font.family: "Inter"
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
        }
        Battery {}
        MouseArea {
            id: power
            visible: ui.signIn
            implicitWidth: 40
            implicitHeight: 36
            hoverEnabled: true
            onClicked: powerMenu.visible = !powerMenu.visible
            Accessible.role: Accessible.Button
            Accessible.name: ui.tr("Power", "Güç")
            Rectangle {
                anchors.fill: parent
                radius: 4
                color: "#FFFFFF"
                opacity: power.containsMouse || powerMenu.visible ? 0.15 : 0
            }
            Kirigami.Icon {
                anchors.centerIn: parent
                width: 20
                height: 20
                source: "system-shutdown-symbolic"
                isMask: true
                color: "#FFFFFF"
            }
        }
    }

    Rectangle {
        id: powerMenu
        visible: false
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 24
        anchors.bottomMargin: 66
        width: 210
        height: menuColumn.implicitHeight + 8
        radius: 8
        color: "#2C2C2C"
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.08)
        Column {
            id: menuColumn
            anchors.fill: parent
            anchors.margins: 4
            Repeater {
                model: [
                    {"id": "sleep", "text": ui.tr("Sleep", "Uyku"), "icon": "system-suspend-symbolic",
                     "shown": root.suspendToRamSupported},
                    {"id": "shutdown", "text": ui.tr("Shut down", "Bilgisayarı kapat"),
                     "icon": "system-shutdown-symbolic", "shown": sessionManagement.canShutdown},
                    {"id": "reboot", "text": ui.tr("Restart", "Yeniden başlat"), "icon": "system-reboot-symbolic",
                     "shown": sessionManagement.canReboot},
                ].filter(item => item.shown)
                MouseArea {
                    id: entry
                    required property var modelData
                    width: menuColumn.width
                    height: 36
                    hoverEnabled: true
                    onClicked: ui.powerAction(modelData.id)
                    Rectangle {
                        anchors.fill: parent
                        radius: 4
                        color: "#FFFFFF"
                        opacity: entry.containsMouse ? 0.08 : 0
                    }
                    Row {
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 12
                        Kirigami.Icon {
                            width: 16
                            height: 16
                            source: entry.modelData.icon
                            isMask: true
                            color: "#FFFFFF"
                        }
                        Text {
                            text: entry.modelData.text
                            color: "#FFFFFF"
                            font.family: "Inter"
                            font.pixelSize: 14
                        }
                    }
                }
            }
        }
    }

    // Fade in, as Windows does when the screen locks.
    opacity: 0
    Component.onCompleted: opacity = 1
    Behavior on opacity { NumberAnimation { duration: 400 } }
}
