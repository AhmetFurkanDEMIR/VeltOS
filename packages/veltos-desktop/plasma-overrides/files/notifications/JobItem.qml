/*
    SPDX-FileCopyrightText: 2019 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2024 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 VeltOS Developers

    SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
*/

/*
    VeltOS: a job in a notification toast (a Firefox download through
    Plasma's browser integration, a file copy) the way Windows 11 shows
    progress in a toast: a thin progress bar in the accent colour (amber
    while paused, a travelling segment while the size is unknown), the
    bytes, the speed and the percentage under it, and buttons of equal
    width filling the row: Pause/Resume and Cancel while it runs, Open and
    Open folder when it is done. No Details button and no file menu.
    Replaces Plasma 6.3's JobItem.qml and keeps its interface
    (ModelInterface: percentage, jobState, jobError, jobDetails,
    suspendable, killable and the job signals; menuOpen).
*/

import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQml

import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.coreaddons as KCoreAddons

import org.kde.notificationmanager as NotificationManager

import org.kde.plasma.private.notifications as Notifications

import "../global"

ColumnLayout {
    id: jobItem

    property ModelInterface modelInterface

    readonly property int totalFiles: modelInterface.jobDetails && modelInterface.jobDetails.totalFiles || 0
    // No menu in this toast keeps it open.
    readonly property bool menuOpen: false

    readonly property bool running: modelInterface.jobState === NotificationManager.Notifications.JobStateRunning
    readonly property bool paused: modelInterface.jobState === NotificationManager.Notifications.JobStateSuspended
    readonly property bool stopped: modelInterface.jobState === NotificationManager.Notifications.JobStateStopped
    readonly property string destination: modelInterface.jobDetails && modelInterface.jobDetails.effectiveDestUrl
                                          ? modelInterface.jobDetails.effectiveDestUrl.toString() : ""
    readonly property bool sizeUnknown: running && modelInterface.percentage < 1
        && (modelInterface.jobDetails.processedBytes === 0 || modelInterface.jobDetails.totalBytes === 0)
        && modelInterface.jobDetails.processedFiles === 0
    readonly property bool done: stopped && modelInterface.jobError === 0 && destination !== "" && !fileInfo.error

    spacing: Kirigami.Units.smallSpacing

    Notifications.FileInfo {
        id: fileInfo
        url: jobItem.totalFiles === 1 ? modelInterface.jobDetails.effectiveDestUrl : ""
    }

    // The progress bar of Windows 11: a hairline track, a 3 px bar on it.
    Item {
        id: bar
        visible: !jobItem.stopped
        Layout.fillWidth: true
        Layout.topMargin: Kirigami.Units.smallSpacing
        implicitHeight: 3
        clip: true

        readonly property color fill: jobItem.paused ? Kirigami.Theme.neutralTextColor : Kirigami.Theme.highlightColor

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            height: 1
            color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.35)
        }
        Rectangle {
            visible: !jobItem.sizeUnknown
            width: Math.max(height, parent.width * Math.min(100, Math.max(0, modelInterface.percentage)) / 100)
            height: parent.height
            radius: height / 2
            color: bar.fill
            Behavior on width {
                NumberAnimation { duration: Kirigami.Units.longDuration; easing.type: Easing.OutCubic }
            }
        }
        // Size not known yet: a segment travels along the track.
        Rectangle {
            id: segment
            visible: jobItem.sizeUnknown
            width: parent.width * 0.4
            height: parent.height
            radius: height / 2
            color: bar.fill
            NumberAnimation on x {
                running: segment.visible && jobItem.Window.window && jobItem.Window.window.visible
                loops: Animation.Infinite
                from: -bar.width * 0.4
                to: bar.width
                duration: 1600
                easing.type: Easing.InOutQuad
            }
        }
    }

    // What has been done, how fast, and how much: "4.2 MiB of 12 MiB · 1.1 MiB/s      35%".
    RowLayout {
        visible: !jobItem.stopped
        Layout.fillWidth: true
        spacing: Kirigami.Units.largeSpacing

        PlasmaComponents3.Label {
            Layout.fillWidth: true
            elide: Text.ElideRight
            textFormat: Text.PlainText
            font: Kirigami.Theme.smallFont
            opacity: 0.75
            text: {
                if (jobItem.paused)
                    return i18nd("veltos-desktop", "Paused");
                const details = modelInterface.jobDetails;
                const parts = [];
                if (details.processedBytes > 0 && details.totalBytes > 0 && details.processedBytes <= details.totalBytes) {
                    parts.push(i18ndc("plasma_applet_org.kde.plasma.notifications", "How many bytes have been copied", "%2 of %1",
                                      KCoreAddons.Format.formatByteSize(details.totalBytes),
                                      KCoreAddons.Format.formatByteSize(details.processedBytes)));
                } else if (details.processedBytes > 0) {
                    parts.push(KCoreAddons.Format.formatByteSize(details.processedBytes));
                }
                if (details.speed > 0) {
                    parts.push(i18ndc("plasma_applet_org.kde.plasma.notifications", "Bytes per second", "%1/s",
                                      KCoreAddons.Format.formatByteSize(details.speed)));
                }
                return parts.join(" · ");
            }
        }
        PlasmaComponents3.Label {
            visible: !jobItem.sizeUnknown
            textFormat: Text.PlainText
            font: Kirigami.Theme.smallFont
            opacity: 0.75
            // the || "0" is a workaround for the fact that 0 as number is falsey (KDE bug 451807)
            text: i18ndc("plasma_applet_org.kde.plasma.notifications", "Percentage of a job", "%1%", modelInterface.percentage || "0")
        }
    }

    // Buttons of equal width, as Windows 11 toasts have them.
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing
        uniformCellSizes: true
        visible: pauseButton.visible || cancelButton.visible || openButton.visible || folderButton.visible

        PlasmaComponents3.Button {
            id: pauseButton
            Layout.fillWidth: true
            visible: !jobItem.stopped && modelInterface.suspendable
            text: jobItem.paused ? i18ndc("plasma_applet_org.kde.plasma.notifications", "Resume paused job", "Resume")
                                 : i18ndc("plasma_applet_org.kde.plasma.notifications", "Pause running job", "Pause")
            onClicked: jobItem.paused ? modelInterface.resumeJobClicked() : modelInterface.suspendJobClicked()
        }
        PlasmaComponents3.Button {
            id: cancelButton
            Layout.fillWidth: true
            visible: !jobItem.stopped && modelInterface.killable
            text: i18ndc("plasma_applet_org.kde.plasma.notifications", "Cancel running job", "Cancel")
            onClicked: modelInterface.killJobClicked()
        }
        PlasmaComponents3.Button {
            id: openButton
            Layout.fillWidth: true
            visible: jobItem.done && jobItem.totalFiles === 1 && (fileInfo.openAction === null || fileInfo.openAction.enabled)
            text: i18nd("veltos-desktop", "Open file")
            onClicked: {
                if (fileInfo.openAction !== null) {
                    fileInfo.openAction.trigger();
                    modelInterface.fileActionInvoked(fileInfo.openAction);
                } else {
                    modelInterface.openUrl(jobItem.destination);
                }
            }
        }
        PlasmaComponents3.Button {
            id: folderButton
            Layout.fillWidth: true
            visible: jobItem.done
            text: i18nd("veltos-desktop", "Open folder")
            // A single file: its folder; several files: the destination folder itself.
            onClicked: modelInterface.openUrl(jobItem.totalFiles === 1
                                              ? jobItem.destination.replace(/\/[^\/]*$/, "")
                                              : jobItem.destination)
        }
    }
}
