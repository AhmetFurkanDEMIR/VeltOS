/*
    A text box of the VeltOS installer, like Windows 11's: a label above,
    a white field with the accent line under it while typing, and a short
    message below when what was typed cannot be used (`message`, red) or
    needs a word of advice (`hint`, grey). `search` shows a magnifier.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

ColumnLayout {
    id: field

    property string label
    property string placeholder
    property alias text: input.text
    property bool password: false
    property bool search: false
    property bool enabledState: true
    property string message: ""         // shown in red under the field
    property string hint: ""            // shown in grey under the field when there is no message
    property alias validator: input.validator
    property alias acceptable: input.acceptableInput
    property alias maximumLength: input.maximumLength
    readonly property bool typing: input.activeFocus
    signal edited(string text)
    signal accepted()

    function focusField() {
        input.forceActiveFocus();
    }

    spacing: 6
    Layout.fillWidth: true

    Text {
        visible: field.label !== ""
        text: field.label
        color: Theme.c.text
        font.family: "Inter"
        font.pixelSize: 13
        font.weight: Font.DemiBold
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 36
        radius: 5
        color: field.enabledState ? (input.activeFocus ? Theme.c.card : (fieldHover.hovered ? Theme.c.cardHover : Theme.c.card)) : Theme.c.fill
        border.width: 1
        border.color: field.message !== "" ? Theme.c.error : Theme.c.control
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 1
            height: input.activeFocus ? 2 : 1
            radius: 1
            color: field.message !== "" ? Theme.c.error : (input.activeFocus ? Theme.accent : Theme.c.muted)
        }
        HoverHandler {
            id: fieldHover
            cursorShape: field.enabledState ? Qt.IBeamCursor : Qt.ArrowCursor
        }
        // Windows' search boxes carry a magnifier on the left.
        Canvas {
            id: magnifier
            visible: field.search
            anchors.left: parent.left
            anchors.leftMargin: 11
            anchors.verticalCenter: parent.verticalCenter
            width: 14
            height: 14
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = Theme.c.subtext;
                ctx.lineWidth = 1.4;
                ctx.lineCap = "round";
                ctx.beginPath();
                ctx.arc(6, 6, 4.6, 0, 2 * Math.PI);
                ctx.moveTo(9.4, 9.4);
                ctx.lineTo(13, 13);
                ctx.stroke();
            }
        }
        TextInput {
            id: input
            anchors.fill: parent
            anchors.leftMargin: field.search ? 34 : 12
            anchors.rightMargin: reveal.visible || clear.visible ? 40 : 12
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.c.text
            font.family: "Inter"
            font.pixelSize: 14
            selectByMouse: true
            selectionColor: Theme.accent
            selectedTextColor: Theme.onAccent
            clip: true
            activeFocusOnTab: true
            readOnly: !field.enabledState
            passwordMaskDelay: 300
            echoMode: field.password && !reveal.showing ? TextInput.Password : TextInput.Normal
            inputMethodHints: field.password ? Qt.ImhNoAutoUppercase | Qt.ImhSensitiveData : Qt.ImhNone
            onTextEdited: field.edited(text)
            onAccepted: field.accepted()
            Text {
                visible: input.text === "" && !input.activeFocus
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width
                elide: Text.ElideRight
                text: field.placeholder
                color: Theme.c.muted
                font.family: "Inter"
                font.pixelSize: 14
            }
        }
        // Windows' eye button shows the password while it is pressed.
        Rectangle {
            id: reveal
            property bool showing: false
            visible: field.password && input.text !== ""
            anchors.right: parent.right
            anchors.rightMargin: 4
            anchors.verticalCenter: parent.verticalCenter
            width: 32
            height: 28
            radius: 4
            color: revealTap.pressed ? Theme.c.cardPressed : (revealHover.hovered ? Theme.c.fill : "transparent")
            Image {
                anchors.centerIn: parent
                width: 16
                height: 16
                source: "images/eye.svg"
                sourceSize.width: 32
                sourceSize.height: 32
            }
            HoverHandler {
                id: revealHover
                cursorShape: Qt.ArrowCursor
            }
            TapHandler {
                id: revealTap
                gesturePolicy: TapHandler.WithinBounds
                onPressedChanged: reveal.showing = pressed
            }
        }
        // Search boxes: an "x" that clears the text.
        Rectangle {
            id: clear
            visible: field.search && input.text !== ""
            anchors.right: parent.right
            anchors.rightMargin: 4
            anchors.verticalCenter: parent.verticalCenter
            width: 32
            height: 28
            radius: 4
            color: clearHover.hovered ? Theme.c.fill : "transparent"
            Canvas {
                anchors.centerIn: parent
                width: 10
                height: 10
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = Theme.c.subtext;
                    ctx.lineWidth = 1.3;
                    ctx.lineCap = "round";
                    ctx.beginPath();
                    ctx.moveTo(1, 1);
                    ctx.lineTo(9, 9);
                    ctx.moveTo(9, 1);
                    ctx.lineTo(1, 9);
                    ctx.stroke();
                }
            }
            HoverHandler {
                id: clearHover
                cursorShape: Qt.ArrowCursor
            }
            TapHandler {
                gesturePolicy: TapHandler.WithinBounds
                onTapped: {
                    input.clear();
                    field.edited("");
                    input.forceActiveFocus();
                }
            }
        }
    }
    Text {
        Layout.fillWidth: true
        visible: text !== ""
        text: field.message !== "" ? field.message : field.hint
        color: field.message !== "" ? Theme.c.error : Theme.c.subtext
        font.family: "Inter"
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }
}
