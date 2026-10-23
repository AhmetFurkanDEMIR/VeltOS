/*
    VeltOS installer buttons (Calamares "navigation: qml"): Back, Next (the
    accent-coloured main action, as in Windows 11 Setup) and Cancel, at the
    bottom right. While VeltOS is being installed there are none (Windows
    Setup shows none either; settings.conf hides Back/Next and disables
    Cancel then), and the last page has buttons of its own (finishedq.qml).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

Rectangle {
    id: navigationBar

    color: Theme.c.window
    height: 64

    // Calamares marks the very last page by its Done button's icon.
    readonly property bool atEnd: ViewManager.quitIcon === "dialog-ok-apply"
    readonly property bool installing: !ViewManager.backAndNextVisible && !atEnd

    component SetupButton: Rectangle {
        id: button

        property string label
        property bool primary: false
        property bool active: true
        signal activated()

        implicitWidth: Math.max(112, caption.implicitWidth + 40)
        implicitHeight: 34
        radius: 6
        opacity: active ? 1 : 0.45
        color: primary ? (mouse.pressed ? Theme.accentPressed : mouse.containsMouse ? Theme.accentHover : Theme.accent)
                       : (mouse.pressed ? Theme.c.cardPressed : mouse.containsMouse ? Theme.c.cardHover : Theme.c.card)
        border.width: primary ? 0 : 1
        border.color: Theme.c.control
        activeFocusOnTab: active
        Keys.onReturnPressed: if (active) activated()
        Keys.onSpacePressed: if (active) activated()

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 9
            color: "transparent"
            border.width: 2
            border.color: Theme.c.focus
            visible: button.activeFocus
        }
        Text {
            id: caption
            anchors.centerIn: parent
            // Calamares labels carry "&" mnemonics.
            text: button.label.replace("&", "")
            color: button.primary ? Theme.onAccent : Theme.c.text
            font.family: "Inter"
            font.pixelSize: 13
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            enabled: button.active
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: button.activated()
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.rightMargin: 24
        spacing: 8

        Item { Layout.fillWidth: true }

        SetupButton {
            label: ViewManager.backLabel
            active: ViewManager.backEnabled
            visible: ViewManager.backAndNextVisible && !navigationBar.atEnd
            onActivated: ViewManager.back()
        }
        SetupButton {
            primary: true
            label: ViewManager.nextLabel
            active: ViewManager.nextEnabled
            visible: ViewManager.backAndNextVisible && !navigationBar.atEnd
            onActivated: ViewManager.next()
        }
        SetupButton {
            Layout.leftMargin: 8
            label: ViewManager.quitLabel
            active: ViewManager.quitEnabled
            visible: ViewManager.quitVisible && !navigationBar.atEnd && !navigationBar.installing
            onActivated: ViewManager.quit()
        }
    }
}
