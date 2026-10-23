/*
    A page of the VeltOS installer in the layout of Windows 11's setup:
    a picture on a soft card on the left, the question, a few words and the
    answers on the right. The picture floats in and the words slide in
    each time the page is shown.

    `activated()` is emitted whenever the page comes into view: Calamares
    shows a step's widget when the step becomes current (the QQuickWidget's
    window becomes visible). Not every Calamares QML step calls the
    page's onActivate() (keyboardq does not), so the pages use this.

    Texts: `t(english, turkish)` follows the installer's language.
    Calamares does not retranslate the QML of its pages when the language
    changes (only the slideshow's), so t() reads two values that change
    afterwards: the current step (bindings are evaluated again when the
    user goes to the next page) and `languageTick`, which a page binds to
    whatever announces a language change on that page (the welcome page:
    the chosen language).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Layouts
import QtQuick.Window

import "VeltTheme.js" as Theme

Rectangle {
    id: page

    property string title
    property string subtitle
    property string picture             // file in images/
    property bool showLogo: false       // the VeltOS logo above the title (first page)
    property bool celebrate: false      // rings pulse out of the picture (installation done)
    property int languageTick: 0
    default property alias content: answers.data
    readonly property bool shown: Window.window !== null && Window.window.visible
    signal activated()

    onShownChanged: {
        if (shown) {
            enter();
            activated();
        }
    }

    readonly property color accent: Theme.accent
    readonly property color text: Theme.c.text
    readonly property color subtext: Theme.c.subtext
    readonly property color card: Theme.c.card
    readonly property color border: Theme.c.border

    // The slow ambient motion (the glow breathing, the picture floating),
    // in seconds. Only while the page is shown: Calamares keeps every
    // page's QML running, and a running animation redraws the whole
    // window each frame (in VMs without 3D, drawn in software, that kept
    // two cores busy, VirtualBox 2026-10-23). Drawn in software the motion
    // advances 20 times a second, which looks the same for motion this
    // slow and costs a third.
    property real ambient: 0
    NumberAnimation on ambient {
        running: page.shown && !Theme.software
        from: 0
        to: 86400
        duration: 86400000
        loops: Animation.Infinite
    }
    Timer {
        running: page.shown && Theme.software
        interval: 50
        repeat: true
        onTriggered: page.ambient += 0.05
    }

    function t(english, turkish) {
        void page.languageTick;
        void ViewManager.currentStepIndex;
        return Qt.locale().name.substring(0, 2) === "tr" ? turkish : english;
    }

    function enter() {
        appear.restart();
    }

    color: Theme.c.window

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 36
        anchors.rightMargin: 36
        anchors.topMargin: 28
        anchors.bottomMargin: 12
        spacing: 40

        // The picture.
        Item {
            id: pictureBox
            visible: page.picture !== ""
            Layout.preferredWidth: Math.round(page.width * 0.32)
            Layout.fillHeight: true

            Rectangle {
                id: pictureCard
                anchors.centerIn: parent
                width: parent.width
                height: Math.min(parent.height, width * 1.12)
                radius: 18
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Theme.c.pictureTop }
                    GradientStop { position: 1.0; color: Theme.c.pictureBottom }
                }
                // A glow like the VeltOS wallpaper's light, breathing slowly
                // (0.92 to 1.04 and back in 6.4 s).
                Rectangle {
                    id: glow
                    width: parent.width * 0.9
                    height: width
                    radius: width / 2
                    anchors.centerIn: parent
                    opacity: 0.55
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Theme.c.glow }
                        GradientStop { position: 1.0; color: "transparent" }
                    }
                    scale: 0.98 - 0.06 * Math.cos(2 * Math.PI * page.ambient / 6.4)
                }
                // Rings that pulse out of the picture when there is something to celebrate.
                Repeater {
                    model: page.celebrate ? 3 : 0
                    delegate: Rectangle {
                        id: ring
                        required property int index
                        anchors.centerIn: parent
                        width: pictureImage.width * 0.72
                        height: width
                        radius: width / 2
                        color: "transparent"
                        border.width: 2
                        border.color: Theme.c.celebrate
                        opacity: 0
                        SequentialAnimation {
                            running: page.shown
                            loops: Animation.Infinite
                            PauseAnimation { duration: ring.index * 700 }
                            ParallelAnimation {
                                NumberAnimation { target: ring; property: "scale"; from: 0.9; to: 1.7; duration: 2100; easing.type: Easing.OutCubic }
                                NumberAnimation { target: ring; property: "opacity"; from: 0.55; to: 0; duration: 2100; easing.type: Easing.OutCubic }
                            }
                            PauseAnimation { duration: (2 - ring.index) * 700 }
                        }
                    }
                }
                // A shadow under the floating picture.
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: pictureImage.y + pictureImage.height * 0.98
                    width: pictureImage.width * (0.55 - pictureImage.lift / 120)
                    height: 10
                    radius: 5
                    color: Theme.dark ? Theme.c.shadow : Theme.accent
                    opacity: (Theme.dark ? 0.35 : 0.10) - pictureImage.lift / 200
                }
                Image {
                    id: pictureImage
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: lift - 6
                    width: Math.round(parent.width * 0.62)
                    height: width
                    source: page.picture !== "" ? "images/" + page.picture : ""
                    sourceSize.width: width * 2
                    sourceSize.height: height * 2
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    // A slow float, as Windows' setup pictures breathe (6 px
                    // up and down in 5.2 s).
                    property real lift: -6 * Math.cos(2 * Math.PI * page.ambient / 5.2)
                }
            }
        }

        // The question and its answers.
        ColumnLayout {
            id: words
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10
            property real shift: 0

            transform: Translate { x: words.shift }

            Image {
                visible: page.showLogo
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                Layout.bottomMargin: 4
                source: "file:/" + Branding.imagePath(Branding.ProductLogo)
                sourceSize.width: 88
                sourceSize.height: 88
                fillMode: Image.PreserveAspectFit
            }
            Text {
                Layout.fillWidth: true
                text: page.title
                color: page.text
                font.family: "Inter"
                font.pixelSize: 28
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                Layout.bottomMargin: 8
                visible: text !== ""
                text: page.subtitle
                color: page.subtext
                font.family: "Inter"
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                lineHeight: 1.15
            }
            ColumnLayout {
                id: answers
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10
                opacity: 1
                property real rise: 0
                transform: Translate { y: answers.rise }
            }
        }
    }

    ParallelAnimation {
        id: appear
        NumberAnimation { target: words; property: "opacity"; from: 0; to: 1; duration: 320; easing.type: Easing.OutCubic }
        NumberAnimation { target: words; property: "shift"; from: 36; to: 0; duration: 420; easing.type: Easing.OutCubic }
        SequentialAnimation {
            PropertyAction { target: answers; property: "opacity"; value: 0 }
            PauseAnimation { duration: 120 }
            ParallelAnimation {
                NumberAnimation { target: answers; property: "opacity"; from: 0; to: 1; duration: 360; easing.type: Easing.OutCubic }
                NumberAnimation { target: answers; property: "rise"; from: 14; to: 0; duration: 420; easing.type: Easing.OutCubic }
            }
        }
        NumberAnimation { target: pictureCard; property: "opacity"; from: 0; to: 1; duration: 420; easing.type: Easing.OutCubic }
        NumberAnimation { target: pictureCard; property: "scale"; from: 0.94; to: 1; duration: 520; easing.type: Easing.OutBack }
    }
}
