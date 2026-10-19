/*
    VeltOS installer side bar (Calamares "sidebar: qml"): the VeltOS logo and
    the steps of the installation, done steps with a check mark and the
    current one highlighted, in the light Windows 11 look of the rest of
    VeltOS.

    Calamares provides `Branding` (io.calamares.ui) and `ViewManager` (the
    list of steps, io.calamares.core).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: sideBar

    readonly property color accent: "#2F5EE6"
    readonly property color text: "#1B1D24"
    readonly property color subtext: "#5D6475"

    color: "#EBEFF7"
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
            id: steps
            model: ViewManager
            delegate: Item {
                id: step

                readonly property bool current: index === ViewManager.currentStepIndex
                readonly property bool done: index < ViewManager.currentStepIndex

                Layout.fillWidth: true
                Layout.preferredHeight: 44

                // Line to the next step.
                Rectangle {
                    x: 11
                    y: 32
                    width: 2
                    height: 24
                    radius: 1
                    color: step.done ? sideBar.accent : "#C9CFDC"
                    visible: index < steps.count - 1
                }
                Rectangle {
                    id: dot
                    x: 0
                    y: 8
                    width: 24
                    height: 24
                    radius: 12
                    color: step.done ? sideBar.accent : "#FFFFFF"
                    border.width: step.done ? 0 : 2
                    border.color: step.current ? sideBar.accent : "#C9CFDC"

                    // Check mark for done steps, a dot for the current one.
                    Canvas {
                        anchors.fill: parent
                        visible: step.done
                        onPaint: {
                            const ctx = getContext("2d");
                            ctx.reset();
                            ctx.strokeStyle = "#FFFFFF";
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
                    anchors.left: dot.right
                    anchors.leftMargin: 14
                    anchors.right: parent.right
                    anchors.verticalCenter: dot.verticalCenter
                    text: display
                    color: step.current || step.done ? sideBar.text : sideBar.subtext
                    font.family: "Inter"
                    font.pixelSize: 14
                    font.weight: step.current ? Font.DemiBold : Font.Normal
                    elide: Text.ElideRight
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
    }
}
