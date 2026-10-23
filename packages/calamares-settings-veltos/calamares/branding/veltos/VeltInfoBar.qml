/*
    A Windows 11 InfoBar for the VeltOS installer pages: a tinted card with
    a round severity icon, a bold title and a few lines of text.
    `severity`: "error" (red), "warning" (yellow), "info" (blue) or
    "success" (green). The lines come from `lines` (a list of texts) or
    from a model (`model`, the role named by `role`).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

Rectangle {
    id: bar

    property string severity: "info"
    property string title
    property var lines: []
    property var model: null
    property string role: "display"
    readonly property int count: repeater.count

    readonly property color tint: severity === "error" ? Theme.c.errorBack : severity === "warning" ? Theme.c.warningBack
                                : severity === "success" ? Theme.c.successBack : Theme.accentSoft
    readonly property color mark: severity === "error" ? Theme.c.error : severity === "warning" ? Theme.c.warning
                                : severity === "success" ? Theme.c.success : Theme.accent

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + 24
    radius: 8
    color: tint
    border.width: 1
    border.color: Qt.darker(tint, 1.08)

    Rectangle {
        id: icon
        x: 14
        y: 13
        width: 18
        height: 18
        radius: 9
        color: bar.mark
        Canvas {
            anchors.fill: parent
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = Theme.dark ? "#1C1E24" : "#FFFFFF";
                ctx.fillStyle = Theme.dark ? "#1C1E24" : "#FFFFFF";
                ctx.lineWidth = 1.6;
                ctx.lineCap = "round";
                ctx.beginPath();
                if (bar.severity === "success") {
                    ctx.moveTo(5, 9.5);
                    ctx.lineTo(8, 12.5);
                    ctx.lineTo(13, 6.5);
                    ctx.stroke();
                } else if (bar.severity === "error") {
                    ctx.moveTo(6, 6);
                    ctx.lineTo(12, 12);
                    ctx.moveTo(12, 6);
                    ctx.lineTo(6, 12);
                    ctx.stroke();
                } else if (bar.severity === "warning") {
                    ctx.moveTo(9, 4.8);
                    ctx.lineTo(9, 10.2);
                    ctx.stroke();
                    ctx.beginPath();
                    ctx.arc(9, 13.2, 1.1, 0, 2 * Math.PI);
                    ctx.fill();
                } else {
                    ctx.moveTo(9, 8.2);
                    ctx.lineTo(9, 13.2);
                    ctx.stroke();
                    ctx.beginPath();
                    ctx.arc(9, 5.2, 1.1, 0, 2 * Math.PI);
                    ctx.fill();
                }
            }
        }
    }
    ColumnLayout {
        id: column
        anchors.left: icon.right
        anchors.leftMargin: 12
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.top: parent.top
        anchors.topMargin: 12
        spacing: 4
        Text {
            Layout.fillWidth: true
            text: bar.title
            color: Theme.c.text
            font.family: "Inter"
            font.pixelSize: 14
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }
        Repeater {
            id: repeater
            model: bar.model !== null ? bar.model : bar.lines
            delegate: Text {
                required property var model
                Layout.fillWidth: true
                text: bar.model !== null ? model[bar.role] : model.modelData
                color: Theme.c.text
                font.family: "Inter"
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
        }
    }
}
