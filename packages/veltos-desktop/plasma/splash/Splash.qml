// VeltOS splash after signing in, shown by ksplashqml while Plasma starts.
// Like Windows 11's "Welcome" screen: the sign-in wallpaper, blurred and
// dimmed, with the dot spinner Windows uses (the same motion as the VeltOS
// boot splash, veltos-boot) and "Welcome". No progress bar.
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import Qt5Compat.GraphicalEffects

Rectangle {
    id: root
    color: "#0B1020"

    // Set by ksplashqml; rises from 1 to 6 as the session starts (unused:
    // Windows shows no progress either).
    property int stage

    readonly property bool turkish: Qt.locale().name.startsWith("tr")

    Image {
        id: wallpaper
        anchors.fill: parent
        // Replaced at package build time (tools/build-assets.py).
        source: "@LOGIN_IMAGE@"
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        visible: false
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
        opacity: 0.35
    }

    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 40
        spacing: 28

        // Six dots chasing each other around a circle, fast at the bottom
        // and slow at the top.
        Item {
            id: spinner
            anchors.horizontalCenter: parent.horizontalCenter
            width: 56
            height: 56

            property real t: 0
            NumberAnimation on t {
                from: 0
                to: 1
                duration: 1800
                loops: Animation.Infinite
            }

            Repeater {
                model: 6
                Rectangle {
                    required property int index
                    readonly property real phase: ((spinner.t - index * 0.055) % 1 + 1) % 1
                    readonly property real eased: phase - Math.sin(2 * Math.PI * phase) / (2 * Math.PI) * 0.75
                    readonly property real angle: 2 * Math.PI * eased - Math.PI / 2
                    width: 5
                    height: 5
                    radius: 2.5
                    color: "white"
                    x: spinner.width / 2 + spinner.width * 0.4 * Math.cos(angle) - width / 2
                    y: spinner.height / 2 + spinner.height * 0.4 * Math.sin(angle) - height / 2
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.turkish ? "Hoş geldiniz" : "Welcome"
            color: "white"
            font.family: "Inter"
            font.pixelSize: 26
            font.weight: Font.Normal
        }
    }
}
