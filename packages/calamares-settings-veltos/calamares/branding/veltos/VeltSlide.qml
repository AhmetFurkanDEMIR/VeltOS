/*
    One slide of the VeltOS installer slideshow (show.qml draws the
    wallpaper behind all slides): a title and a text on the left, and on
    the right a picture of the system (Start, File Explorer, Settings, the
    Store, ...), a panel of app icons, or VeltOS AI's pane answering a
    question (the logo above the words when there is none). The words slide
    in from the left, the picture glides in from the right and then floats
    gently; app icons pop in one after another and bob; the assistant's
    pane shows a question, "typing" dots and then its answer; the feature
    list, if any, appears line by line.

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
    // App icons on the right: [{icon: "veltos-mail", label: "Mail"}, ...]
    // (the installed system's icons, /usr/share/icons).
    property var icons: []
    // "assistant": VeltOS AI's pane on the right, with these texts.
    property string art: ""
    property string question: ""
    property string answer: ""
    property string allow: ""
    readonly property bool hasVisual: picture !== "" || icons.length > 0 || art !== ""

    function iconSource(name) {
        return "file:///usr/share/icons/.Fluent-base/scalable/apps/" + name + ".svg";
    }

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
        width: slide.hasVisual ? parent.width * 0.36 : parent.width * 0.6
        spacing: 14
        opacity: 0.0
        property real shift: 0
        transform: Translate { x: words.shift }

        Image {
            visible: !slide.hasVisual
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


    // App icons on the right, in a glass panel: they pop in one after
    // another and then bob gently, each a little out of step.
    Item {
        id: iconPanel
        visible: slide.icons.length > 0
        anchors.right: parent.right
        anchors.rightMargin: parent.width * 0.06
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -36
        width: Math.min(parent.width * 0.46, grid.implicitWidth + 72)
        height: grid.implicitHeight + 64
        opacity: 0.0
        property real shift: 60
        transform: Translate { x: iconPanel.shift }

        Rectangle {
            anchors.fill: parent
            radius: 18
            color: "#8C141B4A"
            border.width: 1
            border.color: "#40AFC2FF"
            Rectangle {
                anchors.fill: parent
                radius: 18
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#1CFFFFFF" }
                    GradientStop { position: 0.45; color: "#00FFFFFF" }
                }
            }
        }
        Grid {
            id: grid
            anchors.centerIn: parent
            columns: Math.min(4, slide.icons.length)
            columnSpacing: 22
            rowSpacing: 18
            Repeater {
                model: slide.icons
                delegate: Column {
                    id: tile
                    required property int index
                    required property var modelData
                    spacing: 8
                    opacity: 0.0
                    scale: 0.6
                    property real lift: -3 * Math.sin(2 * Math.PI * (slide.ambient / 5 + tile.index * 0.17))
                    transform: Translate { y: tile.lift }
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 76
                        height: 76
                        radius: 18
                        color: "#24FFFFFF"
                        border.width: 1
                        border.color: "#30FFFFFF"
                        Image {
                            anchors.centerIn: parent
                            width: 52
                            height: 52
                            sourceSize.width: 104
                            sourceSize.height: 104
                            source: slide.iconSource(tile.modelData.icon)
                            // Some apps install their icon in hicolor only.
                            onStatusChanged: {
                                if (status === Image.Error && source.toString().indexOf("hicolor") < 0)
                                    source = "file:///usr/share/icons/hicolor/scalable/apps/" + tile.modelData.icon + ".svg";
                            }
                            smooth: true
                            asynchronous: true
                        }
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 96
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                        color: "#E3E9FB"
                        font.family: "Inter"
                        font.pixelSize: 13
                        text: tile.modelData.label
                    }
                    SequentialAnimation {
                        running: slide.visible
                        PauseAnimation { duration: 450 + tile.index * 110 }
                        ParallelAnimation {
                            NumberAnimation { target: tile; property: "opacity"; from: 0; to: 1; duration: 350; easing.type: Easing.OutCubic }
                            NumberAnimation { target: tile; property: "scale"; from: 0.6; to: 1; duration: 520; easing.type: Easing.OutBack }
                        }
                    }
                }
            }
        }
    }

    // VeltOS AI's pane: a question, the assistant "typing", then its answer
    // with an Allow button, as VeltOS AI asks before it changes anything.
    Item {
        id: assistant
        visible: slide.art === "assistant"
        anchors.right: parent.right
        anchors.rightMargin: parent.width * 0.07
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -36 + bob
        width: Math.min(parent.width * 0.40, 460)
        height: chat.implicitHeight + 40
        opacity: 0.0
        property real shift: 60
        property real bob: -3 + 3 * Math.cos(2 * Math.PI * slide.ambient / 6)
        transform: Translate { x: assistant.shift }

        Repeater {
            model: 4
            delegate: Rectangle {
                required property int index
                anchors.fill: parent
                anchors.margins: -(index * 3 + 2)
                anchors.topMargin: -(index * 3 + 2) + 8
                radius: 18 + index * 3
                color: "#000000"
                opacity: 0.12 - index * 0.025
            }
        }
        Rectangle {
            anchors.fill: parent
            radius: 16
            color: "#E6121A44"
            border.width: 1
            border.color: "#505A6BC0"
        }
        Column {
            id: chat
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 20
            spacing: 14

            Row {
                spacing: 10
                Image {
                    width: 28
                    height: 28
                    sourceSize.width: 56
                    sourceSize.height: 56
                    source: slide.iconSource("veltos-ai")
                    smooth: true
                    // The sparkle breathes while the assistant thinks.
                    scale: dots.visible ? 1 + 0.08 * Math.sin(2 * Math.PI * slide.ambient * 1.4) : 1
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: "VeltOS AI"
                    color: "#FFFFFF"
                    font.family: "Inter"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
            }
            // The question, on the right in the accent colour.
            Item {
                id: asked
                width: parent.width
                height: askBubble.height
                opacity: 0.0
                property real rise: 10
                transform: Translate { y: asked.rise }
                Rectangle {
                    id: askBubble
                    anchors.right: parent.right
                    width: Math.min(parent.width * 0.82, askText.implicitWidth + 28)
                    height: askText.implicitHeight + 20
                    radius: 14
                    color: Theme.accent
                    Text {
                        id: askText
                        anchors.fill: parent
                        anchors.margins: 10
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        wrapMode: Text.WordWrap
                        color: "#FFFFFF"
                        font.family: "Inter"
                        font.pixelSize: 14
                        text: slide.question
                    }
                }
            }
            // "Typing", then the answer.
            Item {
                width: parent.width
                height: Math.max(dots.height, answered.implicitHeight)
                Row {
                    id: dots
                    visible: false
                    spacing: 6
                    height: 34
                    leftPadding: 14
                    Repeater {
                        model: 3
                        delegate: Rectangle {
                            required property int index
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.verticalCenterOffset: -4 * Math.max(0, Math.sin(2 * Math.PI * (slide.ambient * 1.6 - index * 0.18)))
                            width: 8
                            height: 8
                            radius: 4
                            color: "#C9D4F5"
                        }
                    }
                }
                Column {
                    id: answered
                    width: parent.width * 0.86
                    spacing: 12
                    opacity: 0.0
                    Rectangle {
                        width: parent.width
                        height: answerText.implicitHeight + 20
                        radius: 14
                        color: "#2A3470"
                        border.width: 1
                        border.color: "#3D4A94"
                        Text {
                            id: answerText
                            anchors.fill: parent
                            anchors.margins: 10
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            wrapMode: Text.WordWrap
                            color: "#EEF2FC"
                            font.family: "Inter"
                            font.pixelSize: 14
                            text: slide.answer
                        }
                    }
                    Rectangle {
                        width: allowText.implicitWidth + 36
                        height: 32
                        radius: 6
                        color: Theme.accent
                        // A soft pulse: VeltOS AI waits for this click.
                        scale: answered.opacity > 0.99 ? 1 + 0.03 * Math.sin(2 * Math.PI * slide.ambient / 1.6) : 1
                        Text {
                            id: allowText
                            anchors.centerIn: parent
                            color: "#FFFFFF"
                            font.family: "Inter"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            text: slide.allow
                        }
                    }
                }
            }
        }
        SequentialAnimation {
            running: slide.visible && slide.art === "assistant"
            ScriptAction { script: { asked.opacity = 0; answered.opacity = 0; dots.visible = false; } }
            PauseAnimation { duration: 700 }
            ParallelAnimation {
                NumberAnimation { target: asked; property: "opacity"; from: 0; to: 1; duration: 350; easing.type: Easing.OutCubic }
                NumberAnimation { target: asked; property: "rise"; from: 10; to: 0; duration: 450; easing.type: Easing.OutCubic }
            }
            PauseAnimation { duration: 350 }
            ScriptAction { script: dots.visible = true }
            PauseAnimation { duration: 1500 }
            ScriptAction { script: dots.visible = false }
            NumberAnimation { target: answered; property: "opacity"; from: 0; to: 1; duration: 450; easing.type: Easing.OutCubic }
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
                NumberAnimation { target: iconPanel; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
                NumberAnimation { target: iconPanel; property: "shift"; from: 60; to: 0; duration: 800; easing.type: Easing.OutCubic }
                NumberAnimation { target: assistant; property: "opacity"; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
                NumberAnimation { target: assistant; property: "shift"; from: 60; to: 0; duration: 800; easing.type: Easing.OutCubic }
            }
        }
    }
}
