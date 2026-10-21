/*
    VeltOS Windows app runner window, in the layout of the Windows 11 App
    Installer: what happens ("Installing 7-Zip") with publisher and version
    on the left, the program's icon on the right, a thin progress bar while
    it works and the buttons at the bottom right. There is no question
    first: opening the file starts it, as in Windows. `runner` (Python)
    drives the pages.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window

    width: 600
    height: 400
    minimumWidth: width
    minimumHeight: height
    maximumWidth: width
    maximumHeight: height
    visible: true
    title: runner.tr("window_title")
    color: Theme.window

    readonly property string page: runner.page
    readonly property bool busy: ["preparing", "running", "waiting"].includes(page)
    readonly property bool choosing: page === "choose"
    readonly property bool problem: ["failed", "invalid", "nospace"].includes(page)

    onClosing: close => {
        if (busy && page !== "running") {
            close.accepted = false; // setup must finish; Cancel stops it explicitly
        } else {
            runner.cancel();
        }
    }

    // Header: question and program details left, icon right.
    RowLayout {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 28
        anchors.leftMargin: 32
        anchors.rightMargin: 32
        spacing: 24

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 4

            Text {
                objectName: "title"
                Layout.fillWidth: true
                Layout.bottomMargin: 8
                text: runner.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
                font.weight: Font.DemiBold
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            Repeater {
                model: runner.details
                delegate: Text {
                    required property string modelData
                    Layout.fillWidth: true
                    text: modelData
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    elide: Text.ElideRight
                }
            }
        }

        Item {
            Layout.alignment: Qt.AlignTop
            implicitWidth: 88
            implicitHeight: 88

            Image {
                anchors.fill: parent
                source: runner.iconUrl
                visible: runner.iconUrl !== ""
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
            Kirigami.Icon {
                anchors.fill: parent
                source: runner.fallbackIcon
                visible: runner.iconUrl === ""
            }
        }
    }

    // What happens: explanation, result, programs the installer added.
    ColumnLayout {
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        anchors.topMargin: 20
        anchors.leftMargin: 32
        anchors.rightMargin: 32
        anchors.bottomMargin: 12
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: body.text !== ""

            // Result mark, as in Windows' status messages.
            Rectangle {
                visible: window.page === "done" || window.problem
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 1
                implicitWidth: 18
                implicitHeight: 18
                radius: 9
                color: window.page === "done" ? Theme.success : Theme.danger
                Text {
                    anchors.centerIn: parent
                    text: window.page === "done" ? "✓" : "!"
                    color: Theme.dark ? "#000000" : "#FFFFFF"
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }
            Text {
                id: body
                objectName: "body"
                Layout.fillWidth: true
                text: runner.body
                color: Theme.text
                font.pixelSize: Theme.bodySize
                wrapMode: Text.Wrap
                lineHeight: 1.15
            }
        }

        // Programs the installer created, each with an Open button. A long
        // list scrolls inside the window instead of pushing the buttons up.
        ScrollView {
            visible: window.page === "done" && runner.newApps.length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(appsColumn.implicitHeight, 160)
            Layout.maximumHeight: 160
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ColumnLayout {
                id: appsColumn
                width: parent.width
                spacing: 8
                Repeater {
                    model: window.page === "done" ? runner.newApps : []
                    delegate: Rectangle {
                        required property int index
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 48
                        radius: Theme.radius
                        color: Theme.card
                        border.color: Theme.cardBorder
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 8
                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.bodySize
                                elide: Text.ElideRight
                            }
                            VButton {
                                text: runner.tr("open")
                                implicitWidth: 96
                                onClicked: runner.openApp(index)
                            }
                        }
                    }
                }
            }
        }

        // "How do you want to open this?" when Bottles or Lutris are
        // installed next to VeltOS' own Wine environment.
        ColumnLayout {
            visible: window.page === "choose"
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: window.page === "choose" ? runner.alternatives : []
                delegate: Rectangle {
                    id: option
                    required property int index
                    required property var modelData
                    readonly property bool chosen: runner.chosenRunner === modelData.id
                    Layout.fillWidth: true
                    implicitHeight: 56
                    radius: Theme.radius
                    color: chosen ? Theme.controlHover : (optionHover.hovered ? Theme.controlHover : Theme.card)
                    border.width: chosen ? 2 : 1
                    border.color: chosen ? Theme.accent : Theme.cardBorder
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 12
                        Kirigami.Icon {
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 28
                            source: option.modelData.icon
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text {
                                Layout.fillWidth: true
                                text: option.modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.bodySize
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: option.modelData.description
                                color: Theme.subtext
                                font.pixelSize: Theme.captionSize
                                elide: Text.ElideRight
                            }
                        }
                    }
                    HoverHandler { id: optionHover }
                    TapHandler { onTapped: runner.chosenRunner = option.modelData.id }
                }
            }
        }

        Item { Layout.fillHeight: true }

        // Information bar (Windows 11 InfoBar): Wine is not a sandbox.
        Rectangle {
            Layout.fillWidth: true
            visible: window.page === "preparing" || window.page === "running" || window.page === "choose"
            implicitHeight: note.implicitHeight + 24
            radius: Theme.smallRadius
            color: Theme.card
            border.color: Theme.cardBorder
            Rectangle {
                id: infoMark
                x: 14
                y: 13
                width: 16
                height: 16
                radius: 8
                color: Theme.accent
                Text {
                    anchors.centerIn: parent
                    text: "i"
                    color: Theme.accentText
                    font.pixelSize: 11
                    font.weight: Font.Bold
                }
            }
            Text {
                id: note
                anchors.left: infoMark.right
                anchors.right: parent.right
                anchors.leftMargin: 10
                anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                text: runner.tr("trust_note")
                color: Theme.text
                font.pixelSize: Theme.captionSize
                wrapMode: Text.Wrap
            }
        }
    }

    // Footer: progress while busy; option on the left, buttons on the right.
    ColumnLayout {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 32
        anchors.rightMargin: 32
        anchors.bottomMargin: 24
        spacing: 16

        // Windows 11 indeterminate progress bar: a short accent bar running
        // along a thin track.
        Item {
            objectName: "progress"
            Layout.fillWidth: true
            visible: window.busy
            implicitHeight: 3
            clip: true
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width
                height: 1
                color: Theme.track
            }
            Rectangle {
                id: runningBar
                height: 3
                radius: 1.5
                width: parent.width * 0.35
                color: Theme.accent
                NumberAnimation on x {
                    running: window.busy && window.visible
                    loops: Animation.Infinite
                    from: -runningBar.width
                    to: footer.width
                    duration: 1600
                    easing.type: Easing.InOutQuad
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            VButton {
                visible: window.page === "failed"
                text: runner.tr("details")
                onClicked: runner.showDetails()
            }
            Item { Layout.fillWidth: true }
            VButton {
                visible: window.page === "waiting"
                text: runner.tr("installer_done")
                onClicked: runner.finishWaiting()
            }
            VButton {
                visible: window.page === "choose"
                accent: true
                focus: true
                text: runner.tr("open")
                onClicked: runner.chooseRunner(runner.chosenRunner)
            }
            VButton {
                visible: !["done", "waiting"].includes(window.page)
                text: window.problem ? runner.tr("close") : runner.tr("cancel")
                onClicked: runner.cancel()
            }
            VButton {
                objectName: "primary"
                visible: window.page === "done"
                accent: true
                focus: true
                text: runner.tr("done_button")
                onClicked: runner.cancel()
            }
        }
    }
}
