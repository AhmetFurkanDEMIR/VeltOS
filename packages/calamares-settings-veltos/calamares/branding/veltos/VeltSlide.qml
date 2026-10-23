/*
    One slide of the VeltOS installer slideshow (show.qml draws the
    wallpaper behind all slides): a title and a text on the left, and
    either the logo or a picture of the system (Start, File Explorer,
    Settings, the Store, ...) on the right. The words slide in from the
    left, the picture glides in from the right and then floats gently;
    the feature list, if any, appears line by line.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick 2.15
import calamares.slideshow 1.0

import "VeltTheme.js" as Theme

Slide {
    id: slide

    property string title
    property string body
    property string picture: ""          // images/*.png, or "" for the logo
    property var points: []              // short feature lines

    // Calamares loads the slideshow when it starts and its first slide is
    // visible from then on, behind the other pages: the float ran all the
    // time and redrew the installer's window 60 times a second (two cores
    // busy in VirtualBox without 3D, 2026-10-23). It runs only while the
    // slideshow is shown (Presentation.activatedInCalamares), at 20 steps
    // a second when drawn in software (see VeltPage).
    readonly property bool playing: visible && parent !== null && parent.activatedInCalamares === true
    property real ambient: 0
    NumberAnimation on ambient {
        running: slide.playing && !Theme.software
        from: 0
        to: 86400
        duration: 86400000
        loops: Animation.Infinite
    }
    Timer {
        running: slide.playing && Theme.software
        interval: 50
        repeat: true
        onTriggered: slide.ambient += 0.05
    }

    // The animations run each time the slide comes into view (Calamares'
    // Presentation shows one slide at a time by toggling `visible`).
    onVisibleChanged: if (visible) play.restart()

    // Words on the left, above the status line of show.qml.
    Column {
        id: words
        anchors.left: parent.left
        anchors.leftMargin: parent.width * 0.07
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -36
        width: slide.picture !== "" ? parent.width * 0.36 : parent.width * 0.6
        spacing: 14
        opacity: 0.0
        property real shift: 0
        transform: Translate { x: words.shift }

        Image {
            visible: slide.picture === ""
            source: "logo.png"
            width: 72
            height: 72
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }
        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 30
            font.weight: Font.DemiBold
            text: slide.title
        }
        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: "#D5DEF8"
            font.family: "Inter"
            font.pixelSize: 16
            lineHeight: 1.25
            text: slide.body
        }
        Column {
            id: list
            width: parent.width
            spacing: 10
            topPadding: 4
            Repeater {
                model: slide.points
                delegate: Row {
                    id: point
                    required property int index
                    required property var modelData
                    spacing: 12
                    opacity: 0.0
                    property real shift: 16
                    transform: Translate { x: point.shift }
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 22
                        height: 22
                        radius: 11
                        color: Theme.tint(Theme.accent, 0.2)
                        border.width: 1
                        border.color: Theme.tint(Theme.accent, 0.5)
                        Canvas {
                            anchors.fill: parent
                            onPaint: {
                                const ctx = getContext("2d");
                                ctx.reset();
                                ctx.strokeStyle = "#FFFFFF";
                                ctx.lineWidth = 1.6;
                                ctx.lineCap = "round";
                                ctx.lineJoin = "round";
                                ctx.beginPath();
                                ctx.moveTo(6.5, 11.5);
                                ctx.lineTo(9.5, 14.5);
                                ctx.lineTo(15.5, 8);
                                ctx.stroke();
                            }
                        }
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        width: list.width - 34
                        wrapMode: Text.WordWrap
                        color: "#EEF2FC"
                        font.family: "Inter"
                        font.pixelSize: 15
                        text: point.modelData
                    }
                    SequentialAnimation {
                        running: slide.visible
                        PauseAnimation { duration: 650 + point.index * 300 }
                        ParallelAnimation {
                            NumberAnimation { target: point; property: "opacity"; from: 0; to: 1; duration: 400; easing.type: Easing.OutCubic }
                            NumberAnimation { target: point; property: "shift"; from: 16; to: 0; duration: 450; easing.type: Easing.OutCubic }
                        }
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
        anchors.rightMargin: parent.width * 0.04
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -36 + bob
        width: parent.width * 0.52
        height: width * 9 / 16
        opacity: 0.0
        // Floats 6 px up and back in 6 s.
        property real bob: -3 + 3 * Math.cos(2 * Math.PI * slide.ambient / 6)
        property real shift: 60
        transform: Translate { x: shot.shift }

        // Shadow: a few soft layers.
        Repeater {
            model: 4
            delegate: Rectangle {
                required property int index
                anchors.fill: parent
                anchors.margins: -(index * 3 + 2)
                anchors.topMargin: -(index * 3 + 2) + 8
                radius: 12 + index * 3
                color: "#000000"
                opacity: 0.12 - index * 0.025
            }
        }
        Rectangle {
            anchors.fill: parent
            radius: 10
            color: "#1B2560"
            border.width: 1
            border.color: "#5A6BC0"
            clip: true
            Image {
                anchors.fill: parent
                anchors.margins: 1
                source: slide.picture
                fillMode: Image.PreserveAspectCrop
                smooth: true
                mipmap: true
                asynchronous: true
            }
            // A light sheen across the glass.
            Rectangle {
                anchors.fill: parent
                radius: 10
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#18FFFFFF" }
                    GradientStop { position: 0.35; color: "#00FFFFFF" }
                }
            }
        }
    }

    ParallelAnimation {
        id: play
        NumberAnimation { target: words; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
        NumberAnimation { target: words; property: "shift"; from: -30; to: 0; duration: 700; easing.type: Easing.OutCubic }
        SequentialAnimation {
            PauseAnimation { duration: 150 }
            ParallelAnimation {
                NumberAnimation { target: shot; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
                NumberAnimation { target: shot; property: "shift"; from: 60; to: 0; duration: 800; easing.type: Easing.OutCubic }
                NumberAnimation { target: shot; property: "scale"; from: 0.96; to: 1; duration: 800; easing.type: Easing.OutCubic }
            }
        }
    }
}
