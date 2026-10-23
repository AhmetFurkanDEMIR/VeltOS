/*
    VeltOS: a drive in the "Safely Remove Hardware" flyout as a Windows 11
    row: the drive's icon, its name, "X free of Y" over a usage bar like
    the drives in File Explorer (red when almost full), and a button that
    ejects it (or opens it when it is not mounted). Clicking the row opens
    the drive in File Explorer. While the drive is being prepared or
    removed the button turns into a spinner; messages ("Don't unplug yet",
    errors) show in place of the free space.

    Replaces Plasma's DeviceItem.qml (org.kde.plasma.devicenotifier,
    plasma-workspace 6.3.6) through update-plasma-overrides; the device
    data and actions are still Plasma's (DevicesStateMonitor, the device's
    action model).

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
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.components as PlasmaComponents3
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

    property bool hasMessage: deviceItem.deviceErrorMessage !== ""

    property bool isFree: deviceItem.deviceOperationResult !== DN.DevicesStateMonitor.Working && deviceItem.deviceOperationResult !== DN.DevicesStateMonitor.NotPresent && !(deviceItem.deviceMounted === false && deviceItem.deviceOperationResult === DN.DevicesStateMonitor.Successful)
    readonly property bool busy: deviceItem.deviceOperationResult === DN.DevicesStateMonitor.Working
    readonly property real used: deviceSize > 0 && deviceFreeSpace >= 0 ? Math.min(1, Math.max(0, 1 - deviceFreeSpace / deviceSize)) : -1
    readonly property bool almostFull: used >= 0.95

    // The device's actions by name ("openWithFileManager", ...).
    property var actionNames: []
    Instantiator {
        model: deviceItem.deviceActions
        delegate: QtObject {
            readonly property string actionName: model.Name
        }
        onObjectAdded: (index, object) => deviceItem.actionNames = deviceItem.actionNames.concat([object.actionName])
        onObjectRemoved: (index, object) => deviceItem.actionNames = deviceItem.actionNames.filter(name => name !== object.actionName)
    }
    readonly property string openActionName: actionNames.find(name => /openWithFileManager/i.test(name)) ?? ""

    function open() {
        if (!deviceActions || !isFree)
            return;
        if (openActionName !== "")
            deviceActions.actionTriggered(openActionName);
        else
            deviceActions.actionTriggered(deviceActions.defaultActionName);
    }
    function runDefault() {
        if (!deviceActions || !isFree)
            return;
        if (deviceMounted)
            unmountTimer.restart();
        deviceActions.actionTriggered(deviceActions.defaultActionName);
    }

    onDeviceOperationResultChanged: {
        if (!popupIconTimer.running) {
            if (deviceItem.deviceOperationResult === DN.DevicesStateMonitor.Working) {
                if (deviceMounted) {
                    unmountTimer.restart();
                }
            } else if (deviceItem.deviceOperationResult === DN.DevicesStateMonitor.Successful) {
                devicenotifier.popupIcon = "dialog-ok"
                popupIconTimer.restart()
            } else if (deviceItem.deviceOperationResult === DN.DevicesStateMonitor.Unsuccessful) {
                devicenotifier.popupIcon = "dialog-error"
                popupIconTimer.restart()
            }
        }
    }

    onHasMessageChanged: {
        if (deviceItem.hasMessage) {
            messageHighlight.highlight(this)
        }
    }

    Timer {
        id: unmountTimer
        interval: 1000
        repeat: false
    }

    width: ListView.view ? ListView.view.width - ListView.view.leftMargin - ListView.view.rightMargin : implicitWidth
    implicitHeight: row.implicitHeight + Kirigami.Units.largeSpacing * 2
    hoverEnabled: true
    onClicked: open()
    onContainsMouseChanged: {
        if (containsMouse && ListView.view)
            ListView.view.currentIndex = index;
    }
    Keys.onReturnPressed: open()
    Keys.onEnterPressed: open()
    Accessible.role: Accessible.ListItem
    Accessible.name: deviceDescription
    Accessible.description: status.text

    RowLayout {
        id: row
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: Kirigami.Units.largeSpacing
            rightMargin: Kirigami.Units.smallSpacing
        }
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            Layout.alignment: Qt.AlignVCenter
            source: deviceItem.deviceIcon
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing / 2

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: deviceItem.deviceDescription
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            // Usage bar like File Explorer's drives.
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing / 2
                visible: deviceItem.used >= 0 && !deviceItem.hasMessage && !deviceItem.busy
                implicitHeight: 4
                radius: 2
                color: Qt.alpha(Kirigami.Theme.textColor, 0.14)
                Rectangle {
                    width: Math.max(height, parent.width * Math.max(0, deviceItem.used))
                    height: parent.height
                    radius: 2
                    color: deviceItem.almostFull ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.highlightColor
                }
            }
            PlasmaComponents3.Label {
                id: status
                Layout.fillWidth: true
                font: Kirigami.Theme.smallFont
                opacity: deviceItem.hasMessage ? 1 : 0.75
                wrapMode: Text.WordWrap
                textFormat: Text.PlainText
                color: deviceItem.hasMessage && deviceItem.deviceError !== 0 ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                visible: text !== ""
                text: {
                    if (deviceItem.hasMessage) {
                        return deviceItem.deviceErrorMessage;
                    }
                    if (!deviceItem.busy) {
                        if (deviceItem.deviceFreeSpace > 0 && deviceItem.deviceSize > 0) {
                            return i18nc("@info:status Free disk space", "%1 free of %2", deviceItem.deviceFreeSpaceText, deviceItem.deviceSizeText);
                        }
                        return "";
                    } else if (!deviceItem.deviceMounted) {
                        return i18nc("Accessing is a less technical word for Mounting; translation should be short and mean \'Currently mounting this device\'", "Accessing…");
                    } else if (unmountTimer.running) {
                        return i18nc("Removing is a less technical word for Unmounting; translation should be short and mean \'Currently unmounting this device\'", "Removing…");
                    }
                    return i18n("Don't unplug yet! Files are still being transferred…");
                }
            }
        }

        PlasmaComponents3.BusyIndicator {
            visible: deviceItem.busy
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            running: visible
        }

        // Eject (or open, while not mounted), like Windows' "Eject".
        PlasmaComponents3.ToolButton {
            visible: !deviceItem.busy && deviceItem.deviceActions !== undefined && deviceItem.isFree
            icon.name: deviceItem.deviceActions?.defaultActionIcon ?? "media-eject"
            text: deviceItem.deviceActions?.defaultActionText ?? ""
            display: PlasmaComponents3.AbstractButton.IconOnly
            onClicked: deviceItem.runDefault()
            PlasmaComponents3.ToolTip {
                text: parent.text
            }
        }
    }
}
