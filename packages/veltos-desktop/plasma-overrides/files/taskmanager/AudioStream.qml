/*
    VeltOS: the sign that an app is playing sound (music in Media Player,
    a video in Firefox) as a small round badge on the corner of its
    taskbar icon, with a Fluent-style speaker glyph whose sound waves pulse
    gently while it plays, and a cross when the app is muted. Clicking the
    badge mutes or unmutes the app, as before. Replaces Plasma's
    AudioStream.qml (org.kde.plasma.taskmanager, plasma-desktop 6.3.6)
    through update-plasma-overrides; the properties and functions it uses
    (task.playingAudio, task.muted, toggleMuted...) are Task.qml's.

    SPDX-FileCopyrightText: 2017 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 VeltOS Project

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Shapes

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

Item {
    id: audioStreamIconBox

    // A badge on the icon's top-right corner, partly outside it, like
    // Windows' badges.
    width: Math.round(Math.max(16, Math.min(20, Math.min(iconBox.width, iconBox.height) * 0.56)))
    height: width
    x: iconBox.x + iconBox.width - width * 0.68
    y: iconBox.y - height * 0.3
    z: 10

    readonly property bool hovered: hoverHandler.hovered
    readonly property real unit: glyph.width / 16

    activeFocusOnTab: true

    // Using States rather than a simple Behavior we can apply different transitions,
    // which allows us to delay showing the icon but hide it instantly still.
    states: [
        State {
            name: "playing"
            when: task.playingAudio && !task.muted
            PropertyChanges {
                target: audioStreamIconBox
                opacity: 1
            }
        },
        State {
            name: "muted"
            when: task.muted
            PropertyChanges {
                target: audioStreamIconBox
                opacity: 1
            }
        }
    ]

    transitions: [
        Transition {
             from: ""
             to: "playing"
             SequentialAnimation {
                 // Delay showing the play indicator so we don't flash it for brief sounds.
                 PauseAnimation {
                     duration: !task.delayAudioStreamIndicator || inPopup ? 0 : 2000
                 }
                 NumberAnimation {
                     property: "opacity"
                     duration: Kirigami.Units.longDuration
                 }
             }
        },
        Transition {
             from: ""
             to: "muted"
             NumberAnimation {
                 property: "opacity"
                 duration: Kirigami.Units.longDuration
             }
        },
        Transition {
             to: ""
             NumberAnimation {
                 property: "opacity"
                 duration: Kirigami.Units.longDuration
             }
        }
    ]

    opacity: 0
    visible: opacity > 0

    Keys.onReturnPressed: event => toggleMuted()
    Keys.onEnterPressed: event => Keys.returnPressed(event);
    Keys.onSpacePressed: event => Keys.returnPressed(event);

    Accessible.checkable: true
    Accessible.checked: task.muted
    Accessible.name: task.muted ? i18nc("@action:button", "Unmute") : i18nc("@action:button", "Mute")
    Accessible.description: task.muted ? i18nc("@info:tooltip %1 is the window title", "Unmute %1", model.display) : i18nc("@info:tooltip %1 is the window title", "Mute %1", model.display)
    Accessible.role: Accessible.Button

    HoverHandler {
        id: hoverHandler
        enabled: Plasmoid.configuration.interactiveMute
    }

    TapHandler {
        id: tapHandler
        gesturePolicy: TapHandler.ReleaseWithinBounds // Exclusive grab
        enabled: Plasmoid.configuration.interactiveMute
        onTapped: (eventPoint, button) => toggleMuted()
    }

    // The badge: the taskbar's own colour with a thin outline, so it reads
    // on every icon; pointed at, it lights up like a button.
    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: Kirigami.Theme.backgroundColor
        border.width: 1
        border.color: Qt.alpha(Kirigami.Theme.textColor, 0.18)
    }
    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: width / 2
        color: tapHandler.pressed ? Qt.alpha(Kirigami.Theme.textColor, 0.16)
             : (audioStreamIconBox.hovered || audioStreamIconBox.activeFocus) ? Qt.alpha(Kirigami.Theme.highlightColor, 0.22)
             : "transparent"
    }

    // Speaker, sound waves and the mute cross on a 16 x 16 grid.
    Shape {
        id: glyph
        anchors.centerIn: parent
        width: Math.round(parent.width * 0.7)
        height: width
        preferredRendererType: Shape.CurveRenderer

        readonly property color ink: task.muted ? Qt.alpha(Kirigami.Theme.textColor, 0.75) : Kirigami.Theme.textColor

        ShapePath {
            scale: Qt.size(audioStreamIconBox.unit, audioStreamIconBox.unit)
            strokeColor: "transparent"
            fillColor: glyph.ink
            PathSvg { path: "M 1.5 6 Q 1.5 5.4 2.1 5.4 L 4.4 5.4 L 7.6 2.6 Q 8.4 2 8.4 3 L 8.4 13 Q 8.4 14 7.6 13.4 L 4.4 10.6 L 2.1 10.6 Q 1.5 10.6 1.5 10 Z" }
        }
        ShapePath {
            id: innerWave
            property real level: 1
            scale: Qt.size(audioStreamIconBox.unit, audioStreamIconBox.unit)
            strokeColor: Qt.alpha(glyph.ink, level)
            strokeWidth: 1.4
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathSvg { path: task.muted ? "" : "M 10.4 5.9 A 3 3 0 0 1 10.4 10.1" }
        }
        ShapePath {
            id: outerWave
            property real level: 1
            scale: Qt.size(audioStreamIconBox.unit, audioStreamIconBox.unit)
            strokeColor: Qt.alpha(glyph.ink, level)
            strokeWidth: 1.4
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathSvg { path: task.muted ? "" : "M 12.2 3.9 A 5.8 5.8 0 0 1 12.2 12.1" }
        }
        ShapePath {
            scale: Qt.size(audioStreamIconBox.unit, audioStreamIconBox.unit)
            strokeColor: task.muted ? glyph.ink : "transparent"
            strokeWidth: 1.4
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathSvg { path: "M 10.6 6 L 14.6 10 M 14.6 6 L 10.6 10" }
        }
    }

    // The waves pulse one after the other while sound plays.
    SequentialAnimation {
        running: audioStreamIconBox.visible && task.playingAudio && !task.muted
        loops: Animation.Infinite
        onRunningChanged: {
            if (!running) {
                innerWave.level = 1;
                outerWave.level = 1;
            }
        }
        NumberAnimation { target: outerWave; property: "level"; to: 0.3; duration: 420; easing.type: Easing.InOutSine }
        NumberAnimation { target: innerWave; property: "level"; to: 0.45; duration: 380; easing.type: Easing.InOutSine }
        ParallelAnimation {
            NumberAnimation { target: innerWave; property: "level"; to: 1; duration: 380; easing.type: Easing.InOutSine }
            NumberAnimation { target: outerWave; property: "level"; to: 1; duration: 520; easing.type: Easing.InOutSine }
        }
        PauseAnimation { duration: 500 }
    }
}
