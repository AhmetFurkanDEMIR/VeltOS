/*
    One slide of the VeltOS installer slideshow: logo, title and text on the
    VeltOS navy gradient.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick 2.15
import calamares.slideshow 1.0

Slide {
    id: slide

    property string title
    property string body

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#050818" }
            GradientStop { position: 1.0; color: "#0E1846" }
        }
    }

    Image {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: titleText.top
        anchors.bottomMargin: 28
        source: "logo.png"
        width: 96
        height: 96
        fillMode: Image.PreserveAspectFit
    }

    Text {
        id: titleText
        anchors.centerIn: parent
        width: parent.width * 0.8
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        color: "#FFFFFF"
        font.pixelSize: 28
        font.weight: Font.DemiBold
        text: slide.title
    }

    Text {
        anchors.top: titleText.bottom
        anchors.topMargin: 16
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width * 0.7
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        color: "#C9D4F5"
        font.pixelSize: 16
        lineHeight: 1.2
        text: slide.body
    }
}
