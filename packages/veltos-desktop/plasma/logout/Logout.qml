/*
    VeltOS logout greeter (Plasma's "logout screen"), in two Windows 11
    forms:

    - Ctrl+Alt+Del (and "Show Logout Screen"): Windows' security options
      screen. The sign-in wallpaper, blurred and dimmed, fills the screen;
      a column offers Lock, Switch user, Sign out, Change a password and
      Task Manager, with Cancel below and the power button (Sleep, Shut
      down, Restart) in the bottom-right corner.
    - A program asking to shut down or restart: a small card listing the
      power options, like Windows' "Shut Down Windows" dialog.

    The power key shuts down directly, as on Windows (powerdevilrc), so it
    does not open this screen.

    The greeter provides the context properties used here (sdtype, maysd,
    canLogout, spdMethods, softwareUpdatePending, screenGeometry) and
    listens to the signals below (interface of Breeze's Logout.qml in
    Plasma 6.3). Arrow keys, Enter and Esc work as on Windows.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.sessions

Item {
    id: root
    height: screenGeometry.height
    width: screenGeometry.width

    signal logoutRequested()
    signal haltRequested()
    signal haltUpdateRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal rebootUpdateRequested()
    signal cancelRequested()
    signal lockScreenRequested()
    signal cancelSoftwareUpdateRequested()

    readonly property bool turkish: Qt.locale().name.startsWith("tr")
    readonly property bool dark: Kirigami.Theme.backgroundColor.hslLightness < 0.5
    // A program asked to shut down or restart: the small dialog; otherwise
    // (Ctrl+Alt+Del) the security options screen.
    readonly property bool powerRequest: sdtype === ShutdownType.ShutdownTypeHalt
                                         || sdtype === ShutdownType.ShutdownTypeReboot

    function tr(en, trText) {
        return turkish ? trText : en;
    }

    readonly property var powerActions: [
        { id: "sleep", icon: "system-suspend-symbolic", text: tr("Sleep", "Uyku"),
          shown: spdMethods.SuspendState },
        { id: "shutdown", icon: "system-shutdown-symbolic",
          text: softwareUpdatePending ? tr("Update and shut down", "Güncelleştir ve kapat")
                                      : tr("Shut down", "Bilgisayarı kapat"),
          shown: maysd },
        { id: "reboot", icon: "system-reboot-symbolic",
          text: softwareUpdatePending ? tr("Update and restart", "Güncelleştir ve yeniden başlat")
                                      : tr("Restart", "Yeniden başlat"),
          shown: maysd },
    ].filter(action => action.shown)

    readonly property var securityActions: [
        { id: "lock", text: tr("Lock", "Kilitle"), shown: true },
        { id: "switchuser", text: tr("Switch user", "Kullanıcı değiştir"), shown: session.canSwitchUser },
        { id: "logout", text: tr("Sign out", "Oturumu kapat"), shown: canLogout },
        { id: "password", text: tr("Change a password", "Parola değiştir"), shown: true },
        { id: "taskmanager", text: tr("Task Manager", "Görev Yöneticisi"), shown: true },
    ].filter(action => action.shown)

    readonly property var cardActions: [
        { id: "lock", icon: "system-lock-screen-symbolic", text: tr("Lock", "Kilitle") },
        { id: "logout", icon: "system-log-out-symbolic", text: tr("Sign out", "Oturumu kapat") },
    ].filter(action => action.id !== "logout" || canLogout).concat(powerActions)

    function cardIndex() {
        const wanted = sdtype === ShutdownType.ShutdownTypeReboot ? "reboot" : "shutdown";
        const i = cardActions.findIndex(action => action.id === wanted);
        return i >= 0 ? i : 0;
    }

    function run(id) {
        switch (id) {
        case "lock": lockScreenRequested(); break;
        case "switchuser": session.switchUser(); cancelRequested(); break;
        case "logout": logoutRequested(); break;
        case "password": launch("kcmshell6 kcm_users"); break;
        case "taskmanager": launch("veltos-taskmanager"); break;
        case "sleep": suspendRequested(2); break;
        case "shutdown": softwareUpdatePending ? haltUpdateRequested() : haltRequested(); break;
        case "reboot": softwareUpdatePending ? rebootUpdateRequested() : rebootRequested(); break;
        }
    }

    // Programs are started in their own session so that they outlive this
    // greeter, which closes once the command has been handed over.
    function launch(command) {
        runner.connectSource("setsid -f " + command + " </dev/null >/dev/null 2>&1");
    }

    SessionManagement {
        id: session
    }

    P5Support.DataSource {
        id: runner
        engine: "executable"
        onNewData: (sourceName, data) => {
            disconnectSource(sourceName);
            root.cancelRequested();
        }
    }

    // Fade in, as Windows does.
    opacity: 0
    Component.onCompleted: opacity = 1
    Behavior on opacity {
        NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
    }

    // ---- Ctrl+Alt+Del: security options -----------------------------------

    Item {
        id: security
        anchors.fill: parent
        visible: !root.powerRequest

        Image {
            id: wallpaper
            anchors.fill: parent
            // Replaced at package build time (tools/build-assets.py).
            source: "@LOGIN_IMAGE@"
            fillMode: Image.PreserveAspectCrop
            visible: false
        }
        Rectangle {
            anchors.fill: parent
            color: "#0B1020"
        }
        FastBlur {
            anchors.fill: parent
            source: wallpaper
            radius: 64
            visible: wallpaper.status === Image.Ready
        }
        Rectangle {
            anchors.fill: parent
            color: "#000000"
            opacity: 0.45
        }
        // Clicks on the background close the power menu.
        MouseArea {
            anchors.fill: parent
            onClicked: powerMenu.visible = false
        }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: Kirigami.Units.smallSpacing

            ListView {
                id: options
                Layout.preferredWidth: Math.round(Kirigami.Units.gridUnit * 18)
                Layout.preferredHeight: contentHeight
                interactive: false
                focus: !root.powerRequest
                spacing: 2
                model: root.securityActions
                keyNavigationWraps: true
                Keys.onReturnPressed: root.run(root.securityActions[currentIndex].id)
                Keys.onEnterPressed: root.run(root.securityActions[currentIndex].id)
                Keys.onEscapePressed: root.cancelRequested()
                Keys.onTabPressed: cancelButton.forceActiveFocus()

                delegate: MouseArea {
                    id: option
                    required property int index
                    required property var modelData
                    width: ListView.view.width
                    height: Math.round(Kirigami.Units.gridUnit * 2.6)
                    hoverEnabled: true
                    onClicked: root.run(modelData.id)
                    onContainsMouseChanged: if (containsMouse) options.currentIndex = index

                    Rectangle {
                        anchors.fill: parent
                        radius: 4
                        color: "#ffffff"
                        opacity: option.pressed ? 0.06
                               : (options.activeFocus && options.currentIndex === option.index) || option.containsMouse ? 0.12 : 0
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: Kirigami.Units.largeSpacing * 2
                        text: option.modelData.text
                        color: "#ffffff"
                        font.family: "Inter"
                        font.pixelSize: 20
                    }
                }
            }

            WinButton {
                id: cancelButton
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: Kirigami.Units.gridUnit * 2
                text: root.tr("Cancel", "İptal")
                onActivated: root.cancelRequested()
                Keys.onTabPressed: powerButton.forceActiveFocus()
                Keys.onUpPressed: options.forceActiveFocus()
            }
        }

        // Bottom-right corner: power button, as on Windows.
        MouseArea {
            id: powerButton
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: Kirigami.Units.gridUnit * 2
            width: Math.round(Kirigami.Units.gridUnit * 2.4)
            height: width
            hoverEnabled: true
            activeFocusOnTab: true
            visible: root.powerActions.length > 0
            onClicked: powerMenu.visible = !powerMenu.visible
            Keys.onReturnPressed: powerMenu.visible = !powerMenu.visible
            Keys.onEnterPressed: powerMenu.visible = !powerMenu.visible
            Keys.onSpacePressed: powerMenu.visible = !powerMenu.visible
            Keys.onEscapePressed: powerMenu.visible ? powerMenu.visible = false : root.cancelRequested()
            Keys.onTabPressed: options.forceActiveFocus()

            Rectangle {
                anchors.fill: parent
                radius: 4
                color: "#ffffff"
                opacity: powerButton.pressed ? 0.06 : (powerButton.containsMouse || powerButton.activeFocus || powerMenu.visible ? 0.12 : 0)
            }
            Kirigami.Icon {
                anchors.centerIn: parent
                implicitWidth: Kirigami.Units.iconSizes.smallMedium
                implicitHeight: Kirigami.Units.iconSizes.smallMedium
                source: "system-shutdown-symbolic"
                isMask: true
                color: "#ffffff"
            }
        }

        // Power menu above the button (Windows' dark flyout menu).
        Rectangle {
            id: powerMenu
            visible: false
            anchors.right: powerButton.right
            anchors.bottom: powerButton.top
            anchors.bottomMargin: Kirigami.Units.smallSpacing
            width: Math.round(Kirigami.Units.gridUnit * 13)
            height: menuColumn.implicitHeight + 8
            radius: 8
            color: "#2c2c2c"
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.08)

            Column {
                id: menuColumn
                anchors.fill: parent
                anchors.margins: 4
                Repeater {
                    model: root.powerActions
                    delegate: MouseArea {
                        id: menuItem
                        required property var modelData
                        width: menuColumn.width
                        height: Math.round(Kirigami.Units.gridUnit * 2)
                        hoverEnabled: true
                        onClicked: root.run(modelData.id)
                        Rectangle {
                            anchors.fill: parent
                            radius: 4
                            color: "#ffffff"
                            opacity: menuItem.pressed ? 0.04 : (menuItem.containsMouse ? 0.08 : 0)
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Kirigami.Units.largeSpacing * 2
                            spacing: Kirigami.Units.largeSpacing * 2
                            Kirigami.Icon {
                                implicitWidth: Kirigami.Units.iconSizes.small
                                implicitHeight: Kirigami.Units.iconSizes.small
                                source: menuItem.modelData.icon
                                isMask: true
                                color: "#ffffff"
                            }
                            Text {
                                Layout.fillWidth: true
                                text: menuItem.modelData.text
                                color: "#ffffff"
                                font.family: "Inter"
                                font.pixelSize: 14
                            }
                        }
                    }
                }
            }
        }
    }

    // ---- A program asked to shut down or restart: small dialog -------------

    Item {
        anchors.fill: parent
        visible: root.powerRequest

        // Dimmed desktop; clicking outside the card cancels, like Windows.
        Rectangle {
            anchors.fill: parent
            color: "#000000"
            opacity: 0.45
        }
        MouseArea {
            anchors.fill: parent
            onClicked: root.cancelRequested()
        }

        Rectangle {
            id: card
            anchors.centerIn: parent
            width: Math.round(Kirigami.Units.gridUnit * 20)
            height: content.implicitHeight + Kirigami.Units.gridUnit * 2
            radius: 8
            color: root.dark ? "#2b2b2b" : "#f9f9f9"
            border.width: 1
            border.color: root.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.08)

            // Swallow clicks so they do not reach the cancel area behind.
            MouseArea {
                anchors.fill: parent
            }

            ColumnLayout {
                id: content
                anchors.fill: parent
                anchors.margins: Kirigami.Units.gridUnit
                spacing: Kirigami.Units.smallSpacing

                Text {
                    Layout.fillWidth: true
                    Layout.bottomMargin: Kirigami.Units.largeSpacing
                    text: root.tr("What do you want the computer to do?", "Bilgisayarın ne yapmasını istiyorsunuz?")
                    color: root.dark ? "#ffffff" : "#1b1b1b"
                    font.family: "Inter"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }

                ListView {
                    id: list
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentHeight
                    interactive: false
                    focus: root.powerRequest
                    model: root.cardActions
                    currentIndex: root.cardIndex()
                    keyNavigationWraps: true
                    Keys.onReturnPressed: root.run(root.cardActions[currentIndex].id)
                    Keys.onEnterPressed: root.run(root.cardActions[currentIndex].id)
                    Keys.onEscapePressed: root.cancelRequested()

                    delegate: MouseArea {
                        id: row
                        required property int index
                        required property var modelData
                        width: ListView.view.width
                        height: Math.round(Kirigami.Units.gridUnit * 2.2)
                        hoverEnabled: true
                        onClicked: root.run(modelData.id)
                        onContainsMouseChanged: if (containsMouse) list.currentIndex = index

                        Rectangle {
                            anchors.fill: parent
                            radius: 4
                            color: root.dark ? "#ffffff" : "#000000"
                            opacity: row.pressed ? 0.04 : (list.currentIndex === row.index ? 0.07 : 0)
                        }
                        // Windows' selection pill on the left of the current row.
                        Rectangle {
                            visible: list.currentIndex === row.index
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: 3
                            height: parent.height * 0.45
                            radius: 1.5
                            color: Kirigami.Theme.highlightColor
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Kirigami.Units.largeSpacing * 2
                            spacing: Kirigami.Units.largeSpacing * 2
                            Kirigami.Icon {
                                implicitWidth: Kirigami.Units.iconSizes.small
                                implicitHeight: Kirigami.Units.iconSizes.small
                                source: row.modelData.icon
                                isMask: true
                                color: root.dark ? "#ffffff" : "#1b1b1b"
                            }
                            Text {
                                Layout.fillWidth: true
                                text: row.modelData.text
                                color: root.dark ? "#ffffff" : "#1b1b1b"
                                font.family: "Inter"
                                font.pixelSize: 14
                            }
                        }
                    }
                }

                WinButton {
                    Layout.alignment: Qt.AlignRight
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    light: !root.dark
                    text: root.tr("Cancel", "İptal")
                    onActivated: root.cancelRequested()
                }
            }
        }
    }

    // Windows 11 standard button.
    component WinButton: MouseArea {
        id: button
        property string text
        property bool light: false
        signal activated()
        implicitWidth: Math.max(Kirigami.Units.gridUnit * 7, label.implicitWidth + Kirigami.Units.gridUnit * 2)
        implicitHeight: Math.round(Kirigami.Units.gridUnit * 2)
        hoverEnabled: true
        activeFocusOnTab: true
        onClicked: activated()
        Keys.onReturnPressed: activated()
        Keys.onEnterPressed: activated()
        Keys.onSpacePressed: activated()
        Keys.onEscapePressed: root.cancelRequested()
        Rectangle {
            anchors.fill: parent
            radius: 4
            color: button.light ? (button.containsMouse ? "#f6f6f6" : "#fefefe")
                                : Qt.rgba(1, 1, 1, button.pressed ? 0.06 : (button.containsMouse ? 0.15 : 0.1))
            border.width: button.activeFocus ? 2 : 1
            border.color: button.activeFocus ? (button.light ? "#1b1b1b" : "#ffffff")
                        : button.light ? Qt.rgba(0, 0, 0, 0.12) : Qt.rgba(1, 1, 1, 0.09)
        }
        Text {
            id: label
            anchors.centerIn: parent
            text: button.text
            color: button.light ? "#1b1b1b" : "#ffffff"
            font.family: "Inter"
            font.pixelSize: 14
        }
    }
}
