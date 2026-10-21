/*
    VeltOS: a program's progress (a download in Firefox, a copy in File
    Explorer) on its taskbar button as a thin bar under the icon, as
    Windows 11 draws it, instead of Plasma's filled area behind the icon.
    Replaces Plasma's TaskProgressOverlay.qml (org.kde.plasma.taskmanager,
    plasma-desktop 6.3.6) through update-plasma-overrides.

    SPDX-FileCopyrightText: 2016 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 VeltOS Project

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Templates as T

import org.kde.kirigami as Kirigami

T.ProgressBar {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    hoverEnabled: false
    padding: 0

    from: 0
    to: 100
    value: task.smartLauncherItem.progress

    contentItem: Item {
        // The track sits just above the button's active-window line.
        Rectangle {
            id: track

            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 4
            width: Math.round(parent.width * 0.55)
            height: 3
            radius: 1.5
            color: Qt.alpha(Kirigami.Theme.textColor, 0.16)

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: Math.round(parent.width * control.position)
                radius: 1.5
                color: Kirigami.Theme.highlightColor
                Behavior on width { NumberAnimation { duration: 150 } }
            }
        }
    }

    background: null
}
