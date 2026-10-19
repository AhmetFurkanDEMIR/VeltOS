/*
    VeltOS power screen (Plasma's logout greeter), shown for the power key
    and Ctrl+Alt+Del. Windows 11 style: the desktop dims and a rounded card
    lists the power options with monochrome glyphs; arrow keys, Enter and
    Esc work as on Windows. Replaces Breeze's full-screen row of big round
    buttons and its countdown.

    The greeter provides the context properties used here (sdtype, maysd,
    canLogout, spdMethods, softwareUpdatePending, screenGeometry) and
    listens to the signals below (interface of Breeze's Logout.qml in
    Plasma 6.3).

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
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

    function tr(en, trText) {
        return turkish ? trText : en;
    }

    // Shown in this order; an entry is left out when the system cannot do it.
    readonly property var actions: [
        { id: "lock", icon: "system-lock-screen-symbolic", text: tr("Lock", "Kilitle"),
          shown: true },
        { id: "logout", icon: "system-log-out-symbolic", text: tr("Sign out", "Oturumu kapat"),
          shown: canLogout },
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

    // The option the request was for (shut down, restart, sign out) is
    // selected; the power key selects "Shut down", as Windows' default.
    function initialIndex() {
        const wanted = sdtype === ShutdownType.ShutdownTypeReboot ? "reboot"
                     : sdtype === ShutdownType.ShutdownTypeNone ? "logout" : "shutdown";
        const i = actions.findIndex(action => action.id === wanted);
        return i >= 0 ? i : 0;
    }

    function run(id) {
        switch (id) {
        case "lock": lockScreenRequested(); break;
        case "logout": logoutRequested(); break;
        case "sleep": suspendRequested(2); break;
        case "shutdown": softwareUpdatePending ? haltUpdateRequested() : haltRequested(); break;
        case "reboot": softwareUpdatePending ? rebootUpdateRequested() : rebootRequested(); break;
        }
    }

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
                focus: true
                model: root.actions
                currentIndex: root.initialIndex()
                keyNavigationWraps: true
                Keys.onReturnPressed: root.run(root.actions[currentIndex].id)
                Keys.onEnterPressed: root.run(root.actions[currentIndex].id)
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

            // Cancel, right-aligned like a Windows dialog button.
            MouseArea {
                id: cancel
                Layout.alignment: Qt.AlignRight
                Layout.topMargin: Kirigami.Units.largeSpacing
                implicitWidth: Math.max(Kirigami.Units.gridUnit * 6, cancelText.implicitWidth + Kirigami.Units.gridUnit * 2)
                implicitHeight: Math.round(Kirigami.Units.gridUnit * 2)
                hoverEnabled: true
                onClicked: root.cancelRequested()
                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: root.dark ? (cancel.containsMouse ? "#3c3c3c" : "#373737")
                                     : (cancel.containsMouse ? "#f6f6f6" : "#fefefe")
                    border.width: 1
                    border.color: root.dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(0, 0, 0, 0.12)
                }
                Text {
                    id: cancelText
                    anchors.centerIn: parent
                    text: root.tr("Cancel", "İptal")
                    color: root.dark ? "#ffffff" : "#1b1b1b"
                    font.family: "Inter"
                    font.pixelSize: 14
                }
            }
        }
    }
}
