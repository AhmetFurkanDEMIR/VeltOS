// VeltOS login splash, shown by ksplashqml while Plasma starts.
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Rectangle {
    id: root
    color: "#0B1020"

    // Set by ksplashqml; rises from 1 to 6 as the session starts.
    property int stage

    Image {
        id: logo
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -32
        source: "images/veltos-logo.svg"
        sourceSize.width: 112
        sourceSize.height: 112
        opacity: root.stage >= 1 ? 1 : 0
        Behavior on opacity {
            NumberAnimation { duration: 500; easing.type: Easing.OutCubic }
        }
    }

    Rectangle {
        id: track
        anchors.top: logo.bottom
        anchors.topMargin: 48
        anchors.horizontalCenter: parent.horizontalCenter
        width: 160
        height: 4
        radius: 2
        color: "#26304F"

        Rectangle {
            width: track.width * Math.min(root.stage, 6) / 6
            height: track.height
            radius: track.radius
            color: "#4F7CFF"
            Behavior on width {
                NumberAnimation { duration: 400; easing.type: Easing.OutCubic }
            }
        }
    }
}
