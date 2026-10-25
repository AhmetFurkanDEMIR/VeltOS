/*
    VeltOS: a drive in the "Safely Remove Hardware" flyout as an entry of
    Windows 11's menu: "Eject USB DISK" with the volume's size (or what
    happens to it) under it, no icon, no buttons. A click closes the flyout
    and removes the drive safely; then, as on Windows, a notification says
    it can be unplugged ("Safe To Remove Hardware"), or why it could not
    (a program still uses it). A drive that is not mounted is safe already:
    the notification comes at once.

    Replaces Plasma's DeviceItem.qml (org.kde.plasma.devicenotifier,
    plasma-workspace 6.3.6) through update-plasma-overrides; the device
    data and actions are still Plasma's (DevicesStateMonitor, the device's
    action model). Texts come from VeltOS' catalog (veltos-desktop).

    SPDX-FileCopyrightText: 2011 Viranch Mehta <viranch.mehta@gmail.com>
    SPDX-FileCopyrightText: 2012 Jacopo De Simoi <wilderkde@gmail.com>
    SPDX-FileCopyrightText: 2016 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2020 Nate Graham <nate@kde.org>
    SPDX-FileCopyrightText: 2022 Harald Sitter <sitter@kde.org>
    SPDX-FileCopyrightText: 2026 VeltOS Project

    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

import org.kde.plasma.private.devicenotifier as DN

MouseArea {
    id: deviceItem

    required property int index

    required property string deviceDescription
    required property string deviceIcon
    required property double deviceFreeSpace
    required property double deviceSize
    required property string deviceFreeSpaceText
    required property string deviceSizeText
    required property bool deviceMounted
    required property int deviceOperationResult
    required property int deviceError
    required property string deviceErrorMessage
    required property var deviceActions
    required property var deviceEmblems

    readonly property string domain: "veltos-desktop"
    readonly property bool busy: deviceOperationResult === DN.DevicesStateMonitor.Working
    readonly property bool hasMessage: deviceErrorMessage !== ""
    // An eject asked for here and not finished yet.
    property bool ejecting: false

    function tr(text, value) {
        return value === undefined ? i18nd(domain, text) : i18nd(domain, text, value);
    }

    // Windows' notifications after an eject, through the desktop's
    // notification service (gdbus: no shell words reach the command).
    function quoted(text) {
        return "'" + String(text).replace(/'/g, "'\\''") + "'";
    }
    function notify(summary, body, icon) {
        notifier.connectSource(["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
                                "--object-path", "/org/freedesktop/Notifications",
                                "--method", "org.freedesktop.Notifications.Notify",
                                quoted(tr("Safely Remove Hardware")), "0", quoted(icon), quoted(summary),
                                quoted(body), "[]", "{}", "7000"].join(" "));
    }
    function notifySafe() {
        notify(tr("Safe To Remove Hardware"),
               tr("The '%1' device can now be safely removed from the computer.", deviceDescription),
               "media-removable");
    }
    function notifyProblem() {
        notify(tr("Problem Ejecting %1", deviceDescription),
               (deviceErrorMessage !== "" ? deviceErrorMessage + "\n" : "")
               + tr("Close any programs or windows that might be using the device, and then try again."),
               "dialog-warning");
    }

    // The menu entry: the flyout closes at once, as Windows' menu does.
    function eject() {
        if (busy)
            return;
        devicenotifier.expanded = false;
        if (deviceMounted && deviceActions) {
            ejecting = true;
            deviceActions.actionTriggered(deviceActions.defaultActionName);
        } else {
            notifySafe();
        }
    }

    onDeviceOperationResultChanged: {
        if (deviceOperationResult === DN.DevicesStateMonitor.Successful) {
            if (ejecting && !deviceMounted)
                notifySafe();
            ejecting = false;
            devicenotifier.popupIcon = "dialog-ok";
            popupIconTimer.restart();
        } else if (deviceOperationResult === DN.DevicesStateMonitor.Unsuccessful) {
            if (ejecting)
                notifyProblem();
            ejecting = false;
            devicenotifier.popupIcon = "dialog-error";
            popupIconTimer.restart();
        }
    }

    P5Support.DataSource {
        id: notifier
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    width: ListView.view ? ListView.view.width - ListView.view.leftMargin - ListView.view.rightMargin : implicitWidth
    implicitHeight: lines.implicitHeight + Kirigami.Units.smallSpacing * 4
    hoverEnabled: true
    onClicked: eject()
    onContainsMouseChanged: {
        if (containsMouse && ListView.view)
            ListView.view.currentIndex = index;
    }
    Keys.onReturnPressed: eject()
    Keys.onEnterPressed: eject()
    Keys.onSpacePressed: eject()
    Accessible.role: Accessible.MenuItem
    Accessible.name: title.text
    Accessible.description: detail.text

    // The entry under the pointer, as Windows 11's menus show it.
    Rectangle {
        anchors.fill: parent
        radius: Kirigami.Units.cornerRadius
        color: Kirigami.Theme.textColor
        opacity: deviceItem.pressed ? 0.12 : (deviceItem.containsMouse ? 0.07 : 0)
        Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
    }

    RowLayout {
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: Kirigami.Units.largeSpacing + Kirigami.Units.smallSpacing
            rightMargin: Kirigami.Units.largeSpacing
        }
        spacing: Kirigami.Units.largeSpacing

        ColumnLayout {
            id: lines
            Layout.fillWidth: true
            spacing: 0

            PlasmaComponents3.Label {
                id: title
                Layout.fillWidth: true
                text: deviceItem.tr("Eject %1", deviceItem.deviceDescription)
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            // Windows lists the drive's volumes under it ("- USB DISK (E:)");
            // here the size, or what is happening to the drive.
            PlasmaComponents3.Label {
                id: detail
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                font: Kirigami.Theme.smallFont
                opacity: deviceItem.hasMessage ? 1 : 0.7
                elide: Text.ElideRight
                textFormat: Text.PlainText
                color: deviceItem.hasMessage && deviceItem.deviceError !== 0 ? Kirigami.Theme.negativeTextColor
                                                                              : Kirigami.Theme.textColor
                visible: text !== ""
                text: {
                    if (deviceItem.hasMessage)
                        return deviceItem.deviceErrorMessage;
                    if (deviceItem.busy)
                        return deviceItem.deviceMounted ? deviceItem.tr("Ejecting…") : deviceItem.tr("Opening…");
                    if (deviceItem.deviceSize > 0)
                        return "- " + deviceItem.deviceSizeText;
                    return "";
                }
            }
        }

        PlasmaComponents3.BusyIndicator {
            visible: deviceItem.busy
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
            running: visible
        }
    }
}
