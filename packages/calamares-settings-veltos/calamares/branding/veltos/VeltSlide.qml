/*
    One slide of the VeltOS installer slideshow on the VeltOS navy
    gradient: a title and a text, and either the logo or a picture of the
    system (a screenshot of the desktop, Start, Settings, File Explorer,
    the Store) that glides in from the right while the words fade in from
    the left. The feature list, if any, appears line by line.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick 2.15
import calamares.slideshow 1.0

Slide {
    id: slide

    property string title
    property string body
    property string picture: ""          // images/*.png, or "" for the logo
    property var points: []              // short feature lines

    // The animations run each time the slide comes into view (Calamares'
    // Presentation shows one slide at a time by toggling `visible`).
    onVisibleChanged: if (visible) play.restart()

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#050818" }
            GradientStop { position: 1.0; color: "#0E1846" }
        }
    }
    // A soft glow behind the picture, like the sunrise of the VeltOS wallpaper.
    Rectangle {
        id: glow
        width: parent.width * 0.9
        height: width
        radius: width / 2
        x: parent.width * 0.45
        y: -height * 0.25
        opacity: 0.0
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#2FA8F0" }
            GradientStop { position: 0.6; color: "#1A2E8C" }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    // Words on the left.
    Column {
        id: words
        anchors.left: parent.left
        anchors.leftMargin: parent.width * 0.07
        anchors.verticalCenter: parent.verticalCenter
        width: slide.picture !== "" ? parent.width * 0.40 : parent.width * 0.86
        spacing: 14
        opacity: 0.0

        Image {
            visible: slide.picture === ""
            anchors.horizontalCenter: parent.horizontalCenter
            source: "logo.png"
            width: 96
            height: 96
            fillMode: Image.PreserveAspectFit
        }
        Text {
            width: parent.width
            horizontalAlignment: slide.picture !== "" ? Text.AlignLeft : Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#FFFFFF"
            font.pixelSize: 28
            font.weight: Font.DemiBold
            text: slide.title
        }
        Text {
            width: parent.width
            horizontalAlignment: slide.picture !== "" ? Text.AlignLeft : Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#C9D4F5"
            font.pixelSize: 16
            lineHeight: 1.25
            text: slide.body
        }
        Column {
            id: list
            width: parent.width
            spacing: 8
            Repeater {
                model: slide.points
                delegate: Row {
                    id: point
                    required property int index
                    required property var modelData
                    spacing: 10
                    opacity: 0.0
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 8
                        height: 8
                        radius: 4
                        color: "#2FA8F0"
                    }
                    Text {
                        width: list.width - 18
                        wrapMode: Text.WordWrap
                        color: "#E7ECFA"
                        font.pixelSize: 15
                        text: point.modelData
                    }
                    SequentialAnimation {
                        running: slide.visible
                        PauseAnimation { duration: 700 + point.index * 350 }
                        NumberAnimation { target: point; property: "opacity"; from: 0; to: 1; duration: 400 }
                    }
                }
            }
        }
    }

    // The picture on the right, in a rounded frame with a soft shadow.
    Item {
        id: shot
        visible: slide.picture !== ""
        anchors.right: parent.right
        anchors.rightMargin: parent.width * 0.05
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width * 0.47
        height: width * 9 / 16
        opacity: 0.0
        transform: Translate { id: shotShift; x: 60 }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            radius: 12
            color: "#000000"
            opacity: 0.35
            anchors.topMargin: 6
        }
        Rectangle {
            anchors.fill: parent
            radius: 10
            color: "#1B2560"
            border.width: 1
            border.color: "#3C4C9C"
            clip: true
            Image {
                anchors.fill: parent
                anchors.margins: 1
                source: slide.picture
                fillMode: Image.PreserveAspectCrop
                smooth: true
                mipmap: true
            }
        }
    }

    ParallelAnimation {
        id: play
        NumberAnimation { target: words; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
        NumberAnimation { target: glow; property: "opacity"; from: 0; to: 0.55; duration: 1200; easing.type: Easing.OutCubic }
        SequentialAnimation {
            PauseAnimation { duration: 150 }
            ParallelAnimation {
                NumberAnimation { target: shot; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
                NumberAnimation { target: shotShift; property: "x"; from: 60; to: 0; duration: 700; easing.type: Easing.OutCubic }
            }
        }
    }
}
