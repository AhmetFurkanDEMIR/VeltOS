/*
    VeltOS installer side bar (Calamares "sidebar: qml"): the VeltOS logo and
    the steps of the installation, done steps with a check mark and the
    current one highlighted, in the light or dark Windows 11 look of the
    rest of VeltOS (VeltTheme.js), and the VeltOS website.

    Calamares provides `Branding` (io.calamares.ui) and `ViewManager` (the
    list of steps, io.calamares.core).

    Step names: Calamares' own names (the model's `display`) are read once
    and never retranslated in a QML side bar, so they stayed English after
    Turkish was chosen (VirtualBox, 2026-10-23). VeltOS names its steps
    itself, in the order of settings.conf (tests/test_config.py checks it),
    and reads the installer's language again when it changes.

    The website: Calamares runs as root, and a browser must not; a click
    asks install-veltos' helper, which runs as the signed-in user
    (open-website, 127.0.0.1 only), to open the page in their browser.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

Rectangle {
    id: sideBar

    readonly property color accent: Theme.accent
    readonly property color text: Theme.c.text
    readonly property color subtext: Theme.c.subtext
    readonly property string website: "veltos.ahmetfurkandemir.com"
    readonly property string helper: "http://127.0.0.1:47823/website"

    // The steps of settings.conf: welcomeq, localeq, keyboardq, partition,
    // usersq, the installation, finishedq.
    readonly property var steps: [
        ["Welcome", "Hoş geldiniz"], ["Location", "Konum"], ["Keyboard", "Klavye"],
        ["Disk", "Disk"], ["Account", "Hesap"], ["Install", "Yükleme"], ["Finish", "Bitiş"]
    ]
    // The installer's language (Calamares sets Qt's default locale when the
    // language is chosen on the first page; nothing announces it here).
    property string language: Qt.locale().name.substring(0, 2)
    Timer {
        interval: 400
        repeat: true
        running: true
        onTriggered: {
            const now = Qt.locale().name.substring(0, 2);
            if (now !== sideBar.language)
                sideBar.language = now;
        }
    }
    function stepName(index, fallback) {
        if (index < 0 || index >= steps.length)
            return fallback;
        return steps[index][language === "tr" ? 1 : 0];
    }

    color: Theme.c.sidebar
    anchors.fill: parent

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 0

        RowLayout {
            Layout.bottomMargin: 34
            spacing: 12
            Image {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                source: "file:/" + Branding.imagePath(Branding.ProductLogo)
                sourceSize.width: 72
                sourceSize.height: 72
                fillMode: Image.PreserveAspectFit
            }
            ColumnLayout {
                spacing: 0
                Text {
                    text: Branding.string(Branding.ProductName)
                    color: sideBar.text
                    font.family: "Inter"
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Text {
                    text: Branding.string(Branding.Version)
                    color: sideBar.subtext
                    font.family: "Inter"
                    font.pixelSize: 12
                }
            }
        }

        Repeater {
            id: stepList
            model: ViewManager
            delegate: Item {
                id: step

                readonly property bool current: index === ViewManager.currentStepIndex
                readonly property bool done: index < ViewManager.currentStepIndex

                Layout.fillWidth: true
                // Long step names wrap onto a second line instead of being cut.
                Layout.preferredHeight: Math.max(44, stepName.implicitHeight + 22)

                // Line to the next step.
                Rectangle {
                    x: 11
                    y: 32
                    width: 2
                    height: step.height - 24
                    radius: 1
                    color: step.done ? sideBar.accent : Theme.c.line
                    visible: index < stepList.count - 1
                }
                Rectangle {
                    id: dot
                    x: 0
                    y: 8
                    width: 24
                    height: 24
                    radius: 12
                    color: step.done ? sideBar.accent : Theme.c.card
                    border.width: step.done ? 0 : 2
                    border.color: step.current ? sideBar.accent : Theme.c.line

                    // Check mark for done steps, a dot for the current one.
                    Canvas {
                        anchors.fill: parent
                        visible: step.done
                        onPaint: {
                            const ctx = getContext("2d");
                            ctx.reset();
                            ctx.strokeStyle = Theme.onAccent;
                            ctx.lineWidth = 2;
                            ctx.lineCap = "round";
                            ctx.lineJoin = "round";
                            ctx.beginPath();
                            ctx.moveTo(7, 12.5);
                            ctx.lineTo(10.5, 16);
                            ctx.lineTo(17, 9);
                            ctx.stroke();
                        }
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: 10
                        height: 10
                        radius: 5
                        color: sideBar.accent
                        visible: step.current
                    }
                }
                Text {
                    id: stepName
                    anchors.left: dot.right
                    anchors.leftMargin: 12
                    anchors.right: parent.right
                    y: lineCount > 1 ? dot.y - 1 : dot.y + (dot.height - height) / 2
                    text: sideBar.stepName(index, display)
                    color: step.current || step.done ? sideBar.text : sideBar.subtext
                    font.family: "Inter"
                    font.pixelSize: 13
                    font.weight: step.current ? Font.DemiBold : Font.Normal
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                    lineHeight: 1.05
                }
            }
        }

        Item { Layout.fillHeight: true }

        Text {
            Layout.fillWidth: true
            text: "Your PC. No Limits."
            color: sideBar.subtext
            font.family: "Inter"
            font.pixelSize: 12
        }
        // The operating system's website (product owner, 2026-10-22): whole,
        // on two lines when the bar is narrow (after "veltos."), and a link
        // (product owner, 2026-10-23).
        Text {
            id: link
            Layout.fillWidth: true
            Layout.topMargin: 2
            text: "veltos.​ahmetfurkandemir.com"
            color: Theme.accentText
            font.family: "Inter"
            font.pixelSize: 12
            font.underline: linkMouse.containsMouse
            wrapMode: Text.Wrap
            MouseArea {
                id: linkMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    const request = new XMLHttpRequest();
                    request.open("GET", sideBar.helper);
                    request.send();
                }
            }
        }
    }
}
