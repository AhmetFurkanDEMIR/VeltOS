/*
    VeltOS Windows app runner window: a compact dialog in the style of the
    Windows 11 app installer. `runner` (Python) drives the pages.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window

    width: Kirigami.Units.gridUnit * 30
    height: Kirigami.Units.gridUnit * 19
    minimumWidth: width
    minimumHeight: height
    visible: true
    title: runner.tr("window_title")
    color: Kirigami.Theme.backgroundColor

    readonly property string page: runner.page
    readonly property bool busy: ["preparing", "running", "waiting"].includes(page)

    onClosing: close => {
        if (busy && page !== "running") {
            close.accepted = false; // setup must finish; Cancel stops it explicitly
        } else {
            runner.cancel();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.gridUnit * 1.5
        spacing: Kirigami.Units.largeSpacing * 2

        // Program identity, like the header of the Windows app installer.
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing * 2

            Rectangle {
                implicitWidth: Kirigami.Units.iconSizes.huge + Kirigami.Units.largeSpacing * 2
                implicitHeight: implicitWidth
                radius: Kirigami.Units.cornerRadius !== undefined ? Kirigami.Units.cornerRadius * 2 : 10
                color: Qt.alpha(Kirigami.Theme.textColor, 0.05)

                Image {
                    anchors.centerIn: parent
                    width: Kirigami.Units.iconSizes.huge
                    height: width
                    source: runner.iconUrl
                    visible: runner.iconUrl !== ""
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: Kirigami.Units.iconSizes.huge
                    height: width
                    source: "application-x-ms-dos-executable"
                    visible: runner.iconUrl === ""
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                Label {
                    Layout.fillWidth: true
                    text: runner.appName
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.5
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    text: runner.subtitle
                    opacity: 0.7
                    elide: Text.ElideRight
                }
            }
        }

        // Current step
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing

                BusyIndicator {
                    visible: window.busy
                    running: visible
                    implicitWidth: Kirigami.Units.iconSizes.medium
                    implicitHeight: implicitWidth
                }
                Kirigami.Icon {
                    visible: ["done", "failed", "invalid"].includes(window.page)
                    implicitWidth: Kirigami.Units.iconSizes.medium
                    implicitHeight: implicitWidth
                    source: window.page === "done" ? "emblem-success" : "dialog-error"
                }
                Label {
                    Layout.fillWidth: true
                    text: runner.title
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.2
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
            }

            Label {
                Layout.fillWidth: true
                visible: text !== ""
                text: runner.body
                wrapMode: Text.Wrap
                opacity: 0.85
            }

            CheckBox {
                id: addToStart
                visible: window.page === "confirm" && !runner.isInstaller
                checked: true
                text: runner.tr("add_to_start")
            }

            // Shortcuts the installer created
            Repeater {
                model: window.page === "done" ? runner.newApps : []
                delegate: Button {
                    required property int index
                    required property var modelData
                    text: runner.tr("open_app").replace(runner.appName, modelData.name)
                    icon.name: "media-playback-start"
                    onClicked: runner.openApp(index)
                }
            }

            Item { Layout.fillHeight: true }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: window.page === "confirm"
                type: Kirigami.MessageType.Information
                text: runner.tr("trust_note")
            }
        }

        // Buttons, primary action on the right as in Windows dialogs.
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing

            Button {
                visible: window.page === "failed"
                text: runner.tr("details")
                icon.name: "document-preview"
                onClicked: runner.showDetails()
            }
            Item { Layout.fillWidth: true }
            Button {
                visible: window.page === "waiting"
                text: runner.tr("installer_done")
                onClicked: runner.finishWaiting()
            }
            Button {
                visible: !["done", "waiting"].includes(window.page)
                text: ["failed", "invalid"].includes(window.page) ? runner.tr("close") : runner.tr("cancel")
                onClicked: runner.cancel()
            }
            Button {
                visible: window.page === "confirm" || window.page === "done"
                highlighted: true
                focus: true
                text: window.page === "done" ? runner.tr("done_button")
                    : (runner.isInstaller ? runner.tr("install") : runner.tr("open"))
                icon.name: window.page === "confirm" && runner.isInstaller ? "install" : ""
                onClicked: window.page === "done" ? runner.cancel() : runner.start(addToStart.checked)
            }
        }
    }
}
