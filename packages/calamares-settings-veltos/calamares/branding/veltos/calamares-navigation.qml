/*
    VeltOS installer buttons (Calamares "navigation: qml"): Back, Next (the
    accent-coloured main action, as in Windows 11 Setup) and Cancel, at the
    bottom right.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: navigationBar

    color: "#F3F5FA"
    height: 64

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
        color: primary ? (mouse.pressed ? "#264DC0" : mouse.containsMouse ? "#4570EC" : "#2F5EE6")
                       : (mouse.pressed ? "#EEF1F7" : mouse.containsMouse ? "#F7F8FC" : "#FFFFFF")
        border.width: primary ? 0 : 1
        border.color: "#D5DAE5"
        activeFocusOnTab: active
        Keys.onReturnPressed: if (active) activated()
        Keys.onSpacePressed: if (active) activated()

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 9
            color: "transparent"
            border.width: 2
            border.color: "#1B1D24"
            visible: button.activeFocus
        }
        Text {
            id: caption
            anchors.centerIn: parent
            // Calamares labels carry "&" mnemonics.
            text: button.label.replace("&", "")
            color: button.primary ? "#FFFFFF" : "#1B1D24"
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
            visible: ViewManager.backAndNextVisible
            onActivated: ViewManager.back()
        }
        SetupButton {
            primary: true
            label: ViewManager.nextLabel
            active: ViewManager.nextEnabled
            visible: ViewManager.backAndNextVisible
            onActivated: ViewManager.next()
        }
        SetupButton {
            Layout.leftMargin: 8
            label: ViewManager.quitLabel
            active: ViewManager.quitEnabled
            visible: ViewManager.quitVisible
            onActivated: ViewManager.quit()
        }
    }
}
