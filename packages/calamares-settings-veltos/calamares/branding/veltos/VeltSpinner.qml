/*
    Windows 11's progress ring (WinUI ProgressRing, indeterminate): an
    accent arc on a faint track that grows to three quarters of the circle,
    shrinks again from its tail and keeps turning. Used while the first
    page loads, while the PC is being checked and while VeltOS installs.

    It runs only while visible and `running`; drawn in software the ring
    is small, so only its own square is redrawn.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick

import "VeltTheme.js" as Theme

Item {
    id: ring

    property color color: Theme.accent
    property color trackColor: Theme.tint(Theme.dark ? "#FFFFFF" : "#1B1D24", 0.10)
    property real thickness: Math.max(2, Math.round(width / 11))
    property bool running: true

    implicitWidth: 32
    implicitHeight: 32

    // One grow-and-shrink takes `cycle` ms; the arc's head runs ahead while
    // it grows, its tail catches up while it shrinks, and the whole ring
    // turns on meanwhile.
    readonly property int cycle: 1500
    readonly property real minSweep: 0.06       // of a turn
    readonly property real maxSweep: 0.74
    property real phase: 0                      // cycles

    NumberAnimation on phase {
        running: ring.running && ring.visible
        from: 0
        to: 3600
        duration: ring.cycle * 3600
        loops: Animation.Infinite
    }

    function ease(x) {
        x = Math.max(0, Math.min(1, x));
        return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        renderStrategy: Canvas.Immediate
        property real head: 0
        property real tail: 0
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const r = (Math.min(width, height) - ring.thickness) / 2;
            ctx.lineWidth = ring.thickness;
            ctx.lineCap = "round";
            ctx.strokeStyle = ring.trackColor;
            ctx.beginPath();
            ctx.arc(width / 2, height / 2, r, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.strokeStyle = ring.color;
            ctx.beginPath();
            ctx.arc(width / 2, height / 2, r, 2 * Math.PI * tail - Math.PI / 2, 2 * Math.PI * head - Math.PI / 2);
            ctx.stroke();
        }
    }

    onPhaseChanged: {
        const turn = Math.floor(phase);
        const p = phase - turn;
        const grow = ring.maxSweep - ring.minSweep;
        // Each cycle starts where the last one's tail stopped, plus a third
        // of a turn of steady rotation per cycle.
        const base = turn * (grow + 0.33) + p * 0.33;
        canvas.head = base + ring.minSweep + grow * ease(p * 2);
        canvas.tail = base + grow * ease(p * 2 - 1);
        canvas.requestPaint();
    }
    Component.onCompleted: phaseChanged()
}
