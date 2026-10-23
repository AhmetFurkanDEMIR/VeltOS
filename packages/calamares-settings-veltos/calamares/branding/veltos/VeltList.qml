/*
    A list to choose from, as Windows 11's setup shows them (countries,
    keyboard layouts): white card, rows that light up under the pointer,
    the chosen row tinted with the accent and marked by a bar on its left.
    The keyboard's arrows move the choice. `roleName` names the model role
    shown, `detailRole` an optional second role shown in grey on the right;
    `chosen(index)` reports a click or a key press. `empty` is shown when
    the list has no rows (a search without results).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls.Basic

import "VeltTheme.js" as Theme

Rectangle {
    id: box

    property alias model: list.model
    property alias currentIndex: list.currentIndex
    property alias count: list.count
    property string roleName: "label"
    property string detailRole: ""
    property string empty: ""
    signal chosen(int index)

    function show(index) {
        if (index < 0)
            return;
        list.positionViewAtIndex(index, ListView.Center);
        // Again once the page's layout has settled (a page being shown
        // still changes the list's height).
        settle.index = index;
        settle.restart();
    }

    function focusList() {
        list.forceActiveFocus();
    }

    color: Theme.c.card
    radius: 8
    border.width: 1
    border.color: list.activeFocus ? Theme.accent : Theme.c.border
    clip: true
    Behavior on border.color { ColorAnimation { duration: 120 } }

    Timer {
        id: settle
        property int index: -1
        interval: 60
        onTriggered: list.positionViewAtIndex(index, ListView.Center)
    }

    ListView {
        id: list
        anchors.fill: parent
        anchors.margins: 4
        clip: true
        focus: true
        activeFocusOnTab: true
        boundsBehavior: Flickable.StopAtBounds
        highlightMoveDuration: 120
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        Keys.onUpPressed: if (currentIndex > 0) box.chosen(currentIndex - 1)
        Keys.onDownPressed: if (currentIndex < count - 1) box.chosen(currentIndex + 1)

        delegate: Rectangle {
            id: row
            required property int index
            required property var model
            readonly property bool current: ListView.isCurrentItem
            width: ListView.view.width - 12
            height: 40
            radius: 6
            color: current ? Theme.accentSoft : (rowHover.hovered ? Theme.c.fill : "transparent")
            Behavior on color { ColorAnimation { duration: 120 } }

            function value(role) {
                if (role === "")
                    return "";
                const direct = row.model[role];
                if (direct !== undefined)
                    return direct;
                const data = row.model.modelData;
                return data && data[role] !== undefined ? data[role] : "";
            }

            Rectangle {
                x: 0
                anchors.verticalCenter: parent.verticalCenter
                width: 3
                height: row.current ? 18 : 0
                radius: 1.5
                color: Theme.accent
                Behavior on height { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
            }
            Text {
                id: detail
                visible: text !== ""
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 12
                width: Math.min(implicitWidth, parent.width * 0.4)
                // e.g. a language's English name next to its own, unless they are the same
                text: row.value(box.detailRole) !== row.value(box.roleName) ? row.value(box.detailRole) : ""
                color: Theme.c.subtext
                font.family: "Inter"
                font.pixelSize: 12
                elide: Text.ElideRight
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                x: 16
                width: parent.width - 28 - (detail.visible ? detail.width + 12 : 0)
                text: row.value(box.roleName)
                color: Theme.c.text
                font.family: "Inter"
                font.pixelSize: 14
                font.weight: row.current ? Font.DemiBold : Font.Normal
                elide: Text.ElideRight
            }
            HoverHandler { id: rowHover }
            TapHandler { onTapped: box.chosen(row.index) }
        }
    }

    Text {
        visible: list.count === 0 && box.empty !== ""
        anchors.centerIn: parent
        width: parent.width - 32
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        text: box.empty
        color: Theme.c.subtext
        font.family: "Inter"
        font.pixelSize: 13
    }
}
