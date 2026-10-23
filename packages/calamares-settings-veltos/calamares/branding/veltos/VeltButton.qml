/*
    A Windows 11 button for the VeltOS installer pages: the accent-coloured
    main action (`primary`) or a standard button, with the hover, press
    and keyboard focus states of Windows 11, light or dark (VeltTheme.js).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick

import "VeltTheme.js" as Theme

Rectangle {
    id: button

    property string label
    property bool primary: false
    property bool active: true
    signal activated()

    implicitWidth: Math.max(120, caption.implicitWidth + 40)
    implicitHeight: 34
    radius: 6
    opacity: active ? 1 : 0.45
    color: primary ? (mouse.pressed ? Theme.accentPressed : mouse.containsMouse ? Theme.accentHover : Theme.accent)
                   : (mouse.pressed ? Theme.c.cardPressed : mouse.containsMouse ? Theme.c.cardHover : Theme.c.card)
    border.width: primary ? 0 : 1
    border.color: Theme.c.control
    activeFocusOnTab: active
    Keys.onReturnPressed: if (active) activated()
    Keys.onEnterPressed: if (active) activated()
    Keys.onSpacePressed: if (active) activated()
    Behavior on color { ColorAnimation { duration: 90 } }

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
        text: button.label
        color: button.primary ? Theme.onAccent : Theme.c.text
        font.family: "Inter"
        font.pixelSize: 13
        font.weight: button.primary ? Font.DemiBold : Font.Normal
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
