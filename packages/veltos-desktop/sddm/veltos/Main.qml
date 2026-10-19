/*
    VeltOS sign-in screen (SDDM theme), laid out like Windows 11:
    a lock screen with the time and date; any key or click shows the
    sign-in view (picture, name, password). Power options bottom right,
    other users bottom left. No session or desktop names are shown: the
    session SDDM used last (Plasma) is started.

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
        signingIn: "Oturum açılıyor…", power: "Güç"
    } : {
        password: "Password", signIn: "Sign in", wrong: "The password is incorrect. Try again.",
        caps: "Caps Lock is on", sleep: "Sleep", restart: "Restart", shutdown: "Shut down",
        signingIn: "Signing in…", power: "Power"
    }
    readonly property color accent: "#4F7CFF"

    property bool signInView: false
    property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property string userName: ""
    property string realName: ""
    property string userIcon: ""
    property bool busy: false

    function showSignIn() {
        if (!signInView) {
            signInView = true;
            passwordField.forceActiveFocus();
        }
    }

    function signIn() {
        if (busy || userName === "")
            return;
        busy = true;
        message.text = "";
        sddm.login(userName, passwordField.text, sessionModel.lastIndex);
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
                enabled: !root.busy
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
                    Rectangle {
                        width: 36
                        height: 36
                        radius: 18
                        color: "#E8ECF6"
                        Text {
                            anchors.centerIn: parent
                            text: (realName || name).charAt(0).toUpperCase()
                            color: "#2F5EE6"
                            font.pixelSize: 16
                            font.family: root.fontFamily
                            font.weight: Font.DemiBold
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
