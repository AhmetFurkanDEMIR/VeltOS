/*
    VeltOS sign-in screen (SDDM theme), laid out like Windows 11:
    a lock screen with the time and date; any key or click shows the
    sign-in view (picture, name, password). Power options bottom right,
    other users bottom left. No session or desktop names are shown: Plasma
    on Wayland is started, or Plasma on X11 at a start without a graphics
    driver (sessionIndex).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

Item {
    id: root

    width: 1920
    height: 1080

    // The VeltOS UI font (fonts-inter) for every text; SDDM's own default
    // is Noto Sans.
    readonly property string fontFamily: "Inter"

    readonly property bool turkish: Qt.locale().name.startsWith("tr")
    readonly property var texts: turkish ? {
        password: "Parola", signIn: "Oturum aç", wrong: "Parola yanlış. Yeniden deneyin.",
        caps: "Caps Lock açık", sleep: "Uyku", restart: "Yeniden başlat", shutdown: "Kapat",
        signingIn: "Oturum açılıyor…", power: "Güç",
        locked: "Çok fazla yanlış parola girildi. %1 sonra yeniden deneyin.",
        hint: "İpucu: %1", reset: "Parolayı sıfırla", resetTitle: "Parolanızı sıfırlayın",
        insert: "Bu hesabın parola sıfırlama USB'sini takın ve İleri'yi seçin.",
        next: "İleri", cancel: "İptal", looking: "USB bellek aranıyor…",
        noDrive: "USB bellek bulunamadı. Parola sıfırlama USB'sini takıp yeniden deneyin.",
        noKey: "Bu USB bellek bu hesabın parola sıfırlama USB'si değil.",
        notSetUp: "Bu hesabın parola sıfırlama USB'si yok.",
        newPassword: "Yeni parola", confirm: "Parolayı onaylayın", newHint: "Parola ipucu (isteğe bağlı)",
        apply: "Sıfırla", differ: "Parolalar eşleşmiyor.", empty: "Yeni bir parola girin.",
        resetDone: "Parolanız sıfırlandı. Yeni parolanızla oturum açın.",
        failed: "Parola değiştirilemedi.", noService: "Parola sıfırlama şu anda kullanılamıyor."
    } : {
        password: "Password", signIn: "Sign in", wrong: "The password is incorrect. Try again.",
        caps: "Caps Lock is on", sleep: "Sleep", restart: "Restart", shutdown: "Shut down",
        signingIn: "Signing in…", power: "Power",
        locked: "Too many wrong passwords. Try again in %1.",
        hint: "Hint: %1", reset: "Reset password", resetTitle: "Reset your password",
        insert: "Insert the password reset USB for this account, then select Next.",
        next: "Next", cancel: "Cancel", looking: "Looking for the USB drive…",
        noDrive: "No USB drive was found. Insert the password reset USB and try again.",
        noKey: "This USB drive isn't the password reset USB for this account.",
        notSetUp: "This account has no password reset USB.",
        newPassword: "New password", confirm: "Confirm password", newHint: "Password hint (optional)",
        apply: "Reset", differ: "The passwords don't match.", empty: "Enter a new password.",
        resetDone: "Your password was reset. Sign in with your new password.",
        failed: "The password couldn't be changed.", noService: "Password reset isn't available right now."
    }
    readonly property color accent: "#4F7CFF"

    property bool signInView: false
    property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property string userName: ""
    property string realName: ""
    property string userIcon: ""
    property bool busy: false

    // Three wrong passwords wait 30 seconds, three more a minute, then two
    // minutes after every three; signing in starts the count again (as
    // VeltOS' other password prompts, product owner 2026-11-01).
    property int failures: 0
    property int lockLeft: 0
    function lockText() {
        const minutes = Math.floor(lockLeft / 60), seconds = lockLeft % 60;
        return texts.locked.arg(minutes + ":" + (seconds < 10 ? "0" : "") + seconds);
    }
    Timer {
        id: lockTimer
        interval: 1000
        repeat: true
        onTriggered: {
            root.lockLeft = Math.max(0, root.lockLeft - 1);
            message.text = root.lockLeft > 0 ? root.lockText() : "";
            if (root.lockLeft === 0) {
                stop();
                passwordField.forceActiveFocus();
            }
        }
    }

    // Forgotten passwords (product owner, 2026-11-01): the account's hint
    // after a wrong password, and "Reset password" only for an account with
    // a password reset USB. This screen cannot run programs; veltos-auth's
    // password-recovery service answers it on 127.0.0.1 (only for the sddm
    // user) and changes the password only when the USB's key matches.
    property string recoveryService: "http://127.0.0.1:47824"
    property bool resetAvailable: false
    property string passwordHint: ""
    property string resetStep: ""          // "", "insert", "password"
    property bool resetBusy: false
    property string resetError: ""

    function ask(path, body, done) {
        const request = new XMLHttpRequest();
        request.onreadystatechange = function () {
            if (request.readyState !== XMLHttpRequest.DONE)
                return;
            let answer = null;
            try {
                answer = request.status === 200 ? JSON.parse(request.responseText) : null;
            } catch (error) {
                answer = null;
            }
            done(answer);
        };
        request.open("POST", recoveryService + path);
        request.setRequestHeader("Content-Type", "application/json");
        request.send(JSON.stringify(body));
    }
    function loadAccountHelp() {
        resetAvailable = false;
        passwordHint = "";
        if (userName === "")
            return;
        const asked = userName;
        ask("/status", { user: asked }, function (answer) {
            if (!answer || asked !== root.userName)
                return;
            root.resetAvailable = answer.configured === true;
            root.passwordHint = answer.hint || "";
            // "Reset password" on the lock screen switched to this screen:
            // its reset panel opens at once.
            if (answer.resetRequested === true && root.resetAvailable) {
                root.signInView = true;
                root.startReset();
            }
        });
    }
    onUserNameChanged: loadAccountHelp()

    function resetErrorText(code) {
        return code === "no-drive" ? texts.noDrive : code === "no-key" ? texts.noKey
             : code === "not-set-up" ? texts.notSetUp : code === "bad-password" ? texts.empty
             : code === "unavailable" ? texts.noService : texts.failed;
    }
    function startReset() {
        resetStep = "insert";
        resetError = "";
        message.text = "";
        resetNext.forceActiveFocus();
    }
    function cancelReset() {
        resetStep = "";
        resetBusy = false;
        resetError = "";
        newPassword.text = "";
        confirmPassword.text = "";
        newHint.text = "";
        passwordField.forceActiveFocus();
    }
    function findDrive() {
        if (resetBusy)
            return;
        resetBusy = true;
        resetError = "";
        ask("/find", { user: userName }, function (answer) {
            root.resetBusy = false;
            if (!answer) {
                root.resetError = root.resetErrorText("unavailable");
            } else if (answer.error) {
                root.resetError = root.resetErrorText(answer.error);
            } else {
                root.resetStep = "password";
                newPassword.forceActiveFocus();
            }
        });
    }
    function applyReset() {
        if (resetBusy)
            return;
        if (newPassword.text === "") {
            resetError = texts.empty;
            return;
        }
        if (newPassword.text !== confirmPassword.text) {
            resetError = texts.differ;
            return;
        }
        resetBusy = true;
        resetError = "";
        const body = { user: userName, password: newPassword.text };
        if (newHint.text !== "")
            body.hint = newHint.text;
        ask("/reset", body, function (answer) {
            root.resetBusy = false;
            if (!answer || answer.error) {
                root.resetError = root.resetErrorText(answer ? answer.error : "unavailable");
                return;
            }
            // The count of wrong passwords starts again, as after signing in.
            root.failures = 0;
            root.lockLeft = 0;
            lockTimer.stop();
            root.cancelReset();
            root.loadAccountHelp();
            message.text = root.texts.resetDone;
        });
    }

    function showSignIn() {
        if (!signInView) {
            signInView = true;
            passwordField.forceActiveFocus();
        }
    }

    function signIn() {
        if (busy || userName === "" || lockLeft > 0)
            return;
        busy = true;
        message.text = "";
        sddm.login(userName, passwordField.text, sessionIndex);
    }

    // Which Plasma to start. Without a graphics driver (VeltOS (safe
    // graphics), nomodeset) Linux has no DRM device and Wayland cannot run:
    // veltos-recovery's safe-graphics service then starts this screen on
    // X11 (fbdev), and the X11 Plasma session is the one that works. At
    // every other start Plasma on Wayland, also after a safe start made
    // SDDM remember the X11 session (VM, 2026-10-22).
    property int waylandSession: -1
    property int x11Session: -1
    property bool onX11: Qt.platform.pluginName === "xcb"
    readonly property int sessionIndex: onX11
        ? (x11Session >= 0 ? x11Session : sessionModel.lastIndex)
        : (waylandSession >= 0 ? waylandSession : sessionModel.lastIndex)
    Repeater {
        model: sessionModel
        delegate: Item {
            required property int index
            required property string file
            Component.onCompleted: {
                if (/(^|\/)plasma\.desktop$/.test(file))
                    root.waylandSession = index;
                else if (/(^|\/)plasmax11\.desktop$/.test(file))
                    root.x11Session = index;
            }
        }
    }

    // Users: keep the selected user's details in properties.
    Repeater {
        model: userModel
        delegate: Item {
            required property int index
            required property string name
            required property string realName
            required property string icon
            Component.onCompleted: if (index === root.userIndex) root.pick(index, name, realName, icon)
        }
    }
    function pick(index, name, real, icon) {
        userIndex = index;
        userName = name;
        realName = real || name;
        userIcon = icon || "";
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false;
            passwordField.text = "";
            message.text = root.texts.wrong;
            shake.start();
            passwordField.forceActiveFocus();
            root.failures += 1;
            if (root.failures % 3 === 0) {
                const step = root.failures / 3;
                root.lockLeft = step === 1 ? 30 : step === 2 ? 60 : 120;
                message.text = root.lockText();
                lockTimer.start();
            }
        }
        function onLoginSucceeded() {
            message.text = root.texts.signingIn;
        }
    }

    // --- Background: the wallpaper, blurred and darkened when signing in ---
    Image {
        id: wallpaper
        anchors.fill: parent
        source: config.background
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        smooth: true
    }
    FastBlur {
        anchors.fill: wallpaper
        source: wallpaper
        radius: root.signInView ? 64 : 0
        Behavior on radius { NumberAnimation { duration: 300 } }
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        // Darker than Windows' tint: VeltOS wallpapers are light.
        opacity: root.signInView ? 0.35 : 0.22
        Behavior on opacity { NumberAnimation { duration: 300 } }
    }

    // --- Lock view: time and date -------------------------------------------
    Column {
        id: clock
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.12 - (root.signInView ? 60 : 0)
        opacity: root.signInView ? 0 : 1
        visible: opacity > 0
        spacing: 2
        Behavior on opacity { NumberAnimation { duration: 250 } }
        Behavior on y { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }

        property date now: new Date()
        Timer {
            interval: 1000
            running: true
            repeat: true
            onTriggered: clock.now = new Date()
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(clock.now, "h:mm")
            color: "#FFFFFF"
            font.pixelSize: 112
            font.family: root.fontFamily
            font.weight: Font.DemiBold
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: clock.now.toLocaleDateString(Qt.locale(), "dddd, d MMMM")
            color: "#FFFFFF"
            font.pixelSize: 26
            font.family: root.fontFamily
        }
    }

    // A text box and a button in the sign-in box's look (the reset steps).
    component PanelField: Item {
        id: plain
        property alias text: input.text
        property string placeholder
        property bool secret: true
        signal accepted()
        function focusField() {
            input.forceActiveFocus();
        }
        Layout.fillWidth: true
        Layout.preferredHeight: 40
        Rectangle {
            anchors.fill: parent
            radius: 6
            color: "#F2FFFFFF"
            border.width: 1
            border.color: "#33000000"
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 1
                height: 2
                color: root.accent
                visible: input.activeFocus
            }
        }
        TextInput {
            id: input
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            echoMode: plain.secret ? TextInput.Password : TextInput.Normal
            passwordCharacter: "●"
            maximumLength: plain.secret ? 512 : 100
            font.pixelSize: 15
            font.family: root.fontFamily
            color: "#1B1D24"
            clip: true
            enabled: !root.resetBusy
            // Tab goes to the next field and the buttons (product owner,
            // 2026-11-02: Tab did not move down in the reset fields).
            activeFocusOnTab: true
            Accessible.role: Accessible.EditableText
            Accessible.name: plain.placeholder
            Keys.onReturnPressed: plain.accepted()
            Keys.onEnterPressed: plain.accepted()
            Keys.onEscapePressed: root.cancelReset()
            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: input.text.length === 0
                text: plain.placeholder
                color: "#6B7080"
                font.pixelSize: 15
                font.family: root.fontFamily
            }
        }
    }
    component PanelButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        property bool active: true
        signal clicked()
        implicitWidth: Math.max(104, caption.implicitWidth + 32)
        implicitHeight: 36
        radius: 6
        opacity: active ? 1 : 0.6
        color: primary ? (area.containsMouse ? Qt.lighter(root.accent, 1.1) : root.accent)
                       : (area.containsMouse ? "#40FFFFFF" : "#26FFFFFF")
        border.width: activeFocus ? 2 : primary ? 0 : 1
        border.color: activeFocus ? "#FFFFFF" : "#59FFFFFF"
        activeFocusOnTab: true
        Keys.onReturnPressed: if (active) clicked()
        Keys.onEnterPressed: if (active) clicked()
        Keys.onSpacePressed: if (active) clicked()
        Keys.onEscapePressed: root.cancelReset()
        Accessible.role: Accessible.Button
        Accessible.name: label
        Text {
            id: caption
            anchors.centerIn: parent
            text: button.label
            color: "#FFFFFF"
            font.pixelSize: 14
            font.family: root.fontFamily
            font.weight: Font.DemiBold
        }
        MouseArea {
            id: area
            anchors.fill: parent
            hoverEnabled: true
            enabled: button.active
            cursorShape: Qt.PointingHandCursor
            onClicked: button.clicked()
        }
    }

    // --- Sign-in view ---------------------------------------------------------
    ColumnLayout {
        id: signInPanel
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -40
        width: 360
        spacing: 14
        opacity: root.signInView ? 1 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 250 } }

        Item {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 176
            Layout.preferredHeight: 176
            Rectangle {
                id: avatarBase
                anchors.fill: parent
                radius: width / 2
                color: "#E8ECF6"
                Text {
                    anchors.centerIn: parent
                    visible: avatar.status !== Image.Ready
                    text: root.realName.charAt(0).toUpperCase()
                    color: "#2F5EE6"
                    font.pixelSize: 72
                    font.family: root.fontFamily
                    font.weight: Font.DemiBold
                }
            }
            Image {
                id: avatar
                anchors.fill: parent
                source: root.userIcon
                fillMode: Image.PreserveAspectCrop
                visible: false
                sourceSize: Qt.size(352, 352)
            }
            OpacityMask {
                anchors.fill: parent
                source: avatar
                maskSource: avatarBase
                visible: avatar.status === Image.Ready
            }
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: root.realName
            color: "#FFFFFF"
            font.pixelSize: 30
            font.family: root.fontFamily
            font.weight: Font.DemiBold
        }

        Item {
            id: fieldBox
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            Layout.topMargin: 10
            visible: root.resetStep === ""

            SequentialAnimation {
                id: shake
                loops: 2
                NumberAnimation { target: fieldBox; property: "x"; to: fieldBox.x - 10; duration: 50 }
                NumberAnimation { target: fieldBox; property: "x"; to: fieldBox.x + 10; duration: 100 }
                NumberAnimation { target: fieldBox; property: "x"; to: fieldBox.x; duration: 50 }
            }

            Rectangle {
                anchors.fill: parent
                radius: 6
                color: "#F2FFFFFF"
                border.width: 1
                border.color: "#33000000"
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 1
                    height: 2
                    color: root.accent
                    visible: passwordField.activeFocus
                }
            }
            TextInput {
                id: passwordField
                objectName: "passwordField"
                anchors.left: parent.left
                anchors.right: submit.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                echoMode: TextInput.Password
                passwordCharacter: "●"
                font.pixelSize: 15
                font.family: root.fontFamily
                color: "#1B1D24"
                clip: true
                enabled: !root.busy && root.lockLeft === 0
                Accessible.role: Accessible.EditableText
                Accessible.name: root.texts.password
                Keys.onReturnPressed: root.signIn()
                Keys.onEnterPressed: root.signIn()
                Keys.onEscapePressed: {
                    text = "";
                    root.signInView = false;
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    visible: passwordField.text.length === 0
                    text: root.texts.password
                    color: "#6B7080"
                    font.pixelSize: 15
                    font.family: root.fontFamily
                }
            }
            Rectangle {
                id: submit
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: 4
                width: 32
                height: 32
                radius: 4
                color: submitArea.containsMouse ? root.accent : "#E6EAF5"
                Accessible.role: Accessible.Button
                Accessible.name: root.texts.signIn
                Text {
                    anchors.centerIn: parent
                    text: "→"
                    color: submitArea.containsMouse ? "#FFFFFF" : "#2F5EE6"
                    font.pixelSize: 18
                    font.family: root.fontFamily
                }
                MouseArea {
                    id: submitArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.signIn()
                }
            }
        }

        Text {
            id: message
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#FFFFFF"
            font.pixelSize: 14
            font.family: root.fontFamily
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            visible: keyboard.capsLock
            text: root.texts.caps
            color: "#FFE08A"
            font.pixelSize: 13
            font.family: root.fontFamily
        }
        // After a wrong password, as Windows does: the hint, and the way
        // to a new password when the account has a reset USB.
        Text {
            id: hintLine
            objectName: "hintLine"
            Layout.fillWidth: true
            visible: root.resetStep === "" && root.failures > 0 && root.passwordHint !== ""
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: root.texts.hint.arg(root.passwordHint)
            color: "#E6FFFFFF"
            font.pixelSize: 13
            font.family: root.fontFamily
            textFormat: Text.PlainText
        }
        Text {
            id: resetLink
            objectName: "resetLink"
            Layout.alignment: Qt.AlignHCenter
            // Only after a wrong password, as Windows does (product owner,
            // 2026-11-02).
            visible: root.resetStep === "" && root.resetAvailable && root.failures > 0
            text: root.texts.reset
            color: "#CFE0FF"
            font.pixelSize: 14
            font.family: root.fontFamily
            font.underline: linkArea.containsMouse || activeFocus
            activeFocusOnTab: true
            Keys.onReturnPressed: root.startReset()
            Keys.onEnterPressed: root.startReset()
            Keys.onSpacePressed: root.startReset()
            Accessible.role: Accessible.Link
            Accessible.name: text
            MouseArea {
                id: linkArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.startReset()
            }
        }

        // Reset password: insert the USB, then the new password.
        ColumnLayout {
            id: resetPanel
            objectName: "resetPanel"
            Layout.fillWidth: true
            Layout.topMargin: 6
            visible: root.resetStep !== ""
            spacing: 12
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: root.texts.resetTitle
                color: "#FFFFFF"
                font.pixelSize: 18
                font.family: root.fontFamily
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                visible: root.resetStep === "insert"
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: root.resetBusy ? root.texts.looking : root.texts.insert
                color: "#FFFFFF"
                font.pixelSize: 14
                font.family: root.fontFamily
            }
            PanelField {
                id: newPassword
                objectName: "newPassword"
                visible: root.resetStep === "password"
                placeholder: root.texts.newPassword
                onAccepted: confirmPassword.focusField()
            }
            PanelField {
                id: confirmPassword
                objectName: "confirmPassword"
                visible: root.resetStep === "password"
                placeholder: root.texts.confirm
                onAccepted: newHint.focusField()
            }
            PanelField {
                id: newHint
                objectName: "newHint"
                visible: root.resetStep === "password"
                secret: false
                placeholder: root.texts.newHint
                onAccepted: root.applyReset()
            }
            Text {
                id: resetErrorLine
                objectName: "resetError"
                Layout.fillWidth: true
                visible: text !== ""
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: root.resetError
                color: "#FFD2D2"
                font.pixelSize: 13
                font.family: root.fontFamily
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                PanelButton {
                    id: resetNext
                    objectName: "resetNext"
                    label: root.resetStep === "insert" ? root.texts.next : root.texts.apply
                    primary: true
                    active: !root.resetBusy
                    onClicked: root.resetStep === "insert" ? root.findDrive() : root.applyReset()
                }
                PanelButton {
                    objectName: "resetCancel"
                    label: root.texts.cancel
                    onClicked: root.cancelReset()
                }
            }
        }
    }

    // Other users (bottom left), as on Windows.
    Column {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 28
        spacing: 6
        visible: root.signInView && userModel.count > 1
        Repeater {
            model: userModel
            delegate: Rectangle {
                required property int index
                required property string name
                required property string realName
                required property string icon
                width: 240
                height: 52
                radius: 6
                color: index === root.userIndex ? "#40FFFFFF" : (userArea.containsMouse ? "#26FFFFFF" : "transparent")
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    spacing: 12
                    // The account picture in a circle, as Windows lists the
                    // other users; the initial while there is none.
                    Item {
                        width: 36
                        height: 36
                        Rectangle {
                            id: faceBase
                            anchors.fill: parent
                            radius: width / 2
                            color: "#E8ECF6"
                            Text {
                                anchors.centerIn: parent
                                visible: face.status !== Image.Ready
                                text: (realName || name).charAt(0).toUpperCase()
                                color: "#2F5EE6"
                                font.pixelSize: 16
                                font.family: root.fontFamily
                                font.weight: Font.DemiBold
                            }
                        }
                        Image {
                            id: face
                            objectName: "userListPicture"
                            anchors.fill: parent
                            source: icon || ""
                            fillMode: Image.PreserveAspectCrop
                            sourceSize: Qt.size(72, 72)
                            visible: false
                        }
                        OpacityMask {
                            anchors.fill: parent
                            source: face
                            maskSource: faceBase
                            visible: face.status === Image.Ready
                        }
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: realName || name
                        color: "#FFFFFF"
                        font.pixelSize: 14
                        font.family: root.fontFamily
                    }
                }
                MouseArea {
                    id: userArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        root.pick(index, name, realName, icon);
                        passwordField.text = "";
                        message.text = "";
                        passwordField.forceActiveFocus();
                    }
                }
            }
        }
    }

    // Power (bottom right).
    Rectangle {
        id: powerButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 28
        width: 44
        height: 44
        radius: 6
        color: powerArea.containsMouse || powerMenu.visible ? "#33FFFFFF" : "transparent"
        Accessible.role: Accessible.Button
        Accessible.name: root.texts.power
        // Power symbol: an open ring with a bar.
        Canvas {
            anchors.centerIn: parent
            width: 22
            height: 22
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = "#FFFFFF";
                ctx.lineWidth = 2;
                ctx.lineCap = "round";
                ctx.beginPath();
                ctx.arc(11, 12, 8, -Math.PI / 2 + 0.7, 3 * Math.PI / 2 - 0.7);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(11, 2);
                ctx.lineTo(11, 11);
                ctx.stroke();
            }
        }
        MouseArea {
            id: powerArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: powerMenu.visible = !powerMenu.visible
        }
    }
    Rectangle {
        id: powerMenu
        visible: false
        anchors.right: powerButton.right
        anchors.bottom: powerButton.top
        anchors.bottomMargin: 8
        width: 200
        height: menuColumn.implicitHeight + 12
        radius: 8
        color: "#F7F8FB"
        border.width: 1
        border.color: "#22000000"
        Column {
            id: menuColumn
            anchors.fill: parent
            anchors.margins: 6
            Repeater {
                model: [
                    { label: root.texts.sleep, action: "suspend", enabled: sddm.canSuspend },
                    { label: root.texts.restart, action: "reboot", enabled: sddm.canReboot },
                    { label: root.texts.shutdown, action: "powerOff", enabled: sddm.canPowerOff }
                ]
                delegate: Rectangle {
                    required property var modelData
                    visible: modelData.enabled
                    width: menuColumn.width
                    height: 38
                    radius: 5
                    color: itemArea.containsMouse ? "#E6EAF5" : "transparent"
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        text: modelData.label
                        color: "#1B1D24"
                        font.pixelSize: 14
                        font.family: root.fontFamily
                    }
                    MouseArea {
                        id: itemArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            powerMenu.visible = false;
                            if (modelData.action === "suspend") sddm.suspend();
                            else if (modelData.action === "reboot") sddm.reboot();
                            else sddm.powerOff();
                        }
                    }
                }
            }
        }
    }

    // Any key or click on the lock view shows the sign-in view.
    MouseArea {
        anchors.fill: parent
        z: -1
        onClicked: {
            powerMenu.visible = false;
            root.showSignIn();
        }
    }
    Keys.onPressed: event => {
        if (!root.signInView) {
            root.showSignIn();
            if (event.text.length > 0 && event.key !== Qt.Key_Return && event.key !== Qt.Key_Enter
                    && event.key !== Qt.Key_Space)
                passwordField.text += event.text;
            event.accepted = true;
        }
    }
    focus: true
}
