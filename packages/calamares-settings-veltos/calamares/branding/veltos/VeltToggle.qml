/*
    A Windows 11 toggle switch with its label for the VeltOS installer
    pages: the knob slides and grows under the pointer, the track takes
    the accent colour when the switch is on.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

RowLayout {
    id: toggle

    property string label
    property string detail: ""
    property bool checked: false
    signal toggled(bool checked)

    spacing: 12

    Rectangle {
        id: track
        Layout.preferredWidth: 40
        Layout.preferredHeight: 20
        Layout.alignment: Qt.AlignTop
        Layout.topMargin: 1
        radius: 10
        color: toggle.checked ? (mouse.containsMouse ? Theme.accentHover : Theme.accent) : (mouse.containsMouse ? Theme.c.fill : Theme.c.card)
        border.width: toggle.checked ? 0 : 1
        border.color: Theme.c.muted
        activeFocusOnTab: true
        Keys.onSpacePressed: toggle.flip()
        Behavior on color { ColorAnimation { duration: 120 } }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 13
            color: "transparent"
            border.width: 2
            border.color: Theme.c.focus
            visible: track.activeFocus
        }
        Rectangle {
            id: knob
            readonly property real size: mouse.pressed ? 14 : (mouse.containsMouse ? 14 : 12)
            width: mouse.pressed ? 17 : size
            height: size
            radius: size / 2
            anchors.verticalCenter: parent.verticalCenter
            x: toggle.checked ? parent.width - width - 4 : 4
            color: toggle.checked ? Theme.onAccent : Theme.c.knob
            Behavior on x { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
            Behavior on width { NumberAnimation { duration: 100 } }
            Behavior on height { NumberAnimation { duration: 100 } }
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            anchors.margins: -4
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: toggle.flip()
        }
    }
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        Text {
            Layout.fillWidth: true
            text: toggle.label
            color: Theme.c.text
            font.family: "Inter"
            font.pixelSize: 14
            wrapMode: Text.WordWrap
        }
        Text {
            Layout.fillWidth: true
            visible: text !== ""
            text: toggle.detail
            color: Theme.c.subtext
            font.family: "Inter"
            font.pixelSize: 12
            wrapMode: Text.WordWrap
        }
    }

    function flip() {
        toggle.checked = !toggle.checked;
        toggle.toggled(toggle.checked);
    }
}
