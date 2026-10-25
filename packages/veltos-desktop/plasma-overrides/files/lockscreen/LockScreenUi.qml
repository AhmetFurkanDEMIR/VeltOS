/*
    VeltOS lock screen in the Windows 11 layout (replaces the Breeze
    LockScreenUi.qml of Plasma's desktop shell, see
    plasma-overrides/org.kde.plasma.desktop.json).

    First the picture with the large time and date. A click or a key lifts
    it like a curtain, as Windows 11 does: under it the picture is blurred
    and the account picture, the name and the password box come up, with
    the keyboard layout, battery and power button in the bottom-right
    corner. Esc or a minute without input lets the curtain down again (Esc
    also turns the screen off: kscreenlocker's own key handling). The
    right password shows "Welcome" with Windows' turning dots before the
    desktop; after the PC wakes from sleep the screen comes up from black
    with the time again.

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
    property bool welcome: false         // signed in: "Welcome", then the desktop
    property bool instant: false         // no curtain animation (waking up)
    property string message: ""
    property date now: new Date()
    property double lastTick: Date.now()

    function showSignIn(text) {
        if (welcome) {
            return;
        }
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
        if (welcome) {
            return;
        }
        signIn = false;
        password.text = "";
        message = "";
        // The hidden password box would keep the keys: a key press must
        // lift the curtain again.
        ui.forceActiveFocus();
    }
    // Signed in: Windows shows "Welcome" with its dots for a moment.
    function finish() {
        welcome = true;
        powerMenu.visible = false;
        leave.start();
    }
    // The PC woke from sleep: the time again, coming up from black.
    function woke() {
        instant = true;
        showClock();
        instant = false;
        wake.restart();
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
                ui.finish();
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

    // Windows' turning dots (LogonUI's "Welcome"): five dots chase one
    // another round a circle, fast at the bottom and slow at the top, and
    // go out one after another before the next round (5.5 s, 240 ms apart).
    component WindowsDots: Item {
        id: dots
        property bool running: false
        property color color: "#FFFFFF"
        implicitWidth: 32
        implicitHeight: 32
        Repeater {
            model: 5
            Item {
                id: orbit
                required property int index
                anchors.fill: parent
                opacity: 0
                rotation: 225
                Rectangle {
                    x: (parent.width - width) / 2
                    width: Math.max(3, Math.round(dots.width / 6))
                    height: width
                    radius: width / 2
                    color: dots.color
                }
                SequentialAnimation {
                    running: dots.running
                    PauseAnimation { duration: orbit.index * 240 }
                    SequentialAnimation {
                        loops: Animation.Infinite
                        PropertyAction { target: orbit; property: "opacity"; value: 1 }
                        NumberAnimation { target: orbit; property: "rotation"; from: 225; to: 345; duration: 385; easing.type: Easing.OutQuad }
                        NumberAnimation { target: orbit; property: "rotation"; to: 455; duration: 1265 }
                        NumberAnimation { target: orbit; property: "rotation"; to: 690; duration: 495; easing.type: Easing.InOutQuad }
                        NumberAnimation { target: orbit; property: "rotation"; to: 815; duration: 1705 }
                        NumberAnimation { target: orbit; property: "rotation"; to: 945; duration: 275; easing.type: Easing.OutQuad }
                        PropertyAction { target: orbit; property: "opacity"; value: 0 }
                        PauseAnimation { duration: 1375 }
                    }
                }
            }
        }
    }

    SessionManagement {
        id: sessionManagement
    }
    KeyboardIndicator.KeyState {
        id: capsLock
        key: Qt.Key_CapsLock
    }

    // The clock. Timers stand still while the PC sleeps, the date does not:
    // a jump of more than 20 seconds between two ticks means it woke up.
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            const tick = Date.now();
            if (tick - ui.lastTick > 20000) {
                ui.woke();
            }
            ui.lastTick = tick;
            ui.now = new Date(tick);
        }
    }
    // "Welcome" stays a moment, then the desktop.
    Timer {
        id: leave
        interval: 1300
        onTriggered: Qt.quit()
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

    // ---- Sign-in background: the picture blurred and darkened ----------------------
    // Drawn only while the curtain is (partly) lifted.

    FastBlur {
        anchors.fill: parent
        source: wallpaper
        radius: 72
        visible: !!wallpaper && curtain.y < 0
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.32
        visible: curtain.y < 0
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
            // A letter goes into the password box; Space or Enter only lifts the curtain.
            ui.showSignIn(event.text.length === 1 && event.text > " " ? event.text : "");
            event.accepted = true;
        }
    }

    // ---- The lock screen: a curtain with the picture, time and date -----------------
    // It goes up quickly, gathering speed, and comes down the same way.

    // Above the sign-in box, which it uncovers; under the corner buttons.
    Item {
        id: curtain
        z: 1
        width: parent.width
        height: parent.height
        y: ui.signIn ? -height : 0
        visible: y > -height
        Behavior on y {
            enabled: !ui.instant
            NumberAnimation { duration: 420; easing.type: Easing.InOutCubic }
        }

        ShaderEffectSource {
            anchors.fill: parent
            sourceItem: wallpaper
            visible: !!wallpaper
        }
        Rectangle {
            anchors.fill: parent
            color: "#000000"
            opacity: 0.12
        }

        Column {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            y: parent.height * 0.11
            spacing: 2

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
        visible: opacity > 0 || ui.signIn       // visible at once: the password box takes the focus
        enabled: ui.signIn && !ui.welcome
        // Comes up while the curtain is still going away (and goes while
        // the curtain comes down over it).
        Behavior on opacity {
            enabled: !ui.instant
            SequentialAnimation {
                PauseAnimation { duration: 160 }
                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
            }
        }
        Behavior on anchors.verticalCenterOffset {
            enabled: !ui.instant
            SequentialAnimation {
                PauseAnimation { duration: 160 }
                NumberAnimation { duration: 380; easing.type: Easing.OutCubic }
            }
        }

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
            visible: !ui.noPassword && !ui.welcome
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
            visible: ui.noPassword && !ui.welcome
            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 140
            implicitHeight: 36
            hoverEnabled: true
            onClicked: ui.finish()
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

        // Signed in: Windows' turning dots and "Welcome" under the name.
        Row {
            id: welcomeRow
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredHeight: 36
            visible: ui.welcome
            opacity: ui.welcome ? 1 : 0
            spacing: 12
            Behavior on opacity { NumberAnimation { duration: 250 } }
            WindowsDots {
                anchors.verticalCenter: parent.verticalCenter
                running: ui.welcome
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: ui.tr("Welcome", "Hoş geldiniz")
                color: "#FFFFFF"
                font.family: "Inter"
                font.pixelSize: 20
            }
        }

        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            visible: text !== "" && !ui.welcome
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
        z: 2
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
            visible: ui.signIn && !ui.welcome
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
        z: 3
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

    // Waking from sleep: the lock screen comes up from black.
    Rectangle {
        id: wakeCover
        z: 4
        anchors.fill: parent
        color: "#000000"
        opacity: 0
        visible: opacity > 0
    }
    NumberAnimation {
        id: wake
        target: wakeCover
        property: "opacity"
        from: 1
        to: 0
        duration: 700
        easing.type: Easing.OutCubic
    }

    // Fade in, as Windows does when the screen locks.
    opacity: 0
    Component.onCompleted: opacity = 1
    Behavior on opacity { NumberAnimation { duration: 400 } }
}
