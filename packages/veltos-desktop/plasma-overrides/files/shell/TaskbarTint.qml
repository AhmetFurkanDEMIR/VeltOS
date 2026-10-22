/*
    VeltOS: the taskbar takes on the theme and the accent colour, as the
    product owner asked for Windows 11's taskbar (2026-10-22): a soft glow
    of the accent colour behind the centred Start button and apps, over the
    theme's light or dark background, and a wave of the colour sweeping
    across the bar once when the accent or the light/dark mode changes.
    Nothing moves at rest, so the taskbar costs no extra drawing while
    nothing changes (software rendering in VMs repaints every frame of an
    animation).

    Added to Plasma's desktop shell package by update-plasma-overrides
    (org.kde.plasma.desktop.json); Panel.qml places it over the panel's
    background and under the applets.

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: tint

    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false

    // The accent the user chose (Settings > Personalization > Colours):
    // Plasma's colours follow the system scheme since the VeltOS Plasma
    // theme has no colours of its own (tools/fluent.py). plasmashell's
    // application palette (SystemPalette) stays VeltOS blue (VM, 2026-10-22).
    readonly property color accent: Kirigami.Theme.highlightColor
    readonly property color background: Kirigami.Theme.backgroundColor
    readonly property bool dark: (0.299 * background.r + 0.587 * background.g + 0.114 * background.b) < 0.5
    // How strongly the accent shows in the middle of the bar.
    readonly property real strength: dark ? 0.18 : 0.11
    // The colour shown: follows the accent with a cross-fade.
    property color shown: accent
    Behavior on shown {
        ColorAnimation { duration: 600; easing.type: Easing.InOutQuad }
    }

    function sweep() {
        wave.restart();
    }

    onAccentChanged: {
        shown = accent;
        sweep();
    }
    onDarkChanged: sweep()

    clip: true

    // The glow: the accent fading in towards the middle of the bar.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.alpha(tint.shown, 0) }
            GradientStop { position: 0.3; color: Qt.alpha(tint.shown, tint.strength * 0.35) }
            GradientStop { position: 0.5; color: Qt.alpha(tint.shown, tint.strength) }
            GradientStop { position: 0.7; color: Qt.alpha(tint.shown, tint.strength * 0.35) }
            GradientStop { position: 1.0; color: Qt.alpha(tint.shown, 0) }
        }
    }

    // The wave: a band of the colour crossing the bar from left to right.
    Rectangle {
        id: band
        width: Math.round(tint.width * 0.3)
        height: tint.height
        x: -width
        visible: wave.running
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.alpha(tint.shown, 0) }
            GradientStop { position: 0.5; color: Qt.alpha(tint.shown, tint.dark ? 0.34 : 0.26) }
            GradientStop { position: 1.0; color: Qt.alpha(tint.shown, 0) }
        }
    }
    NumberAnimation {
        id: wave
        target: band
        property: "x"
        from: -band.width
        to: tint.width
        duration: 1100
        easing.type: Easing.InOutCubic
    }
}
