// A Windows Task Manager graph: values 0..100 over the last 60 seconds,
// a line with a light fill, an optional grid.
import QtQuick

Canvas {
    id: graph

    property var values: []
    property color colour: "#2F5EE6"
    property bool grid: true
    property color gridColour: Qt.rgba(0.5, 0.5, 0.5, 0.25)

    onValuesChanged: requestPaint()
    onColourChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        const w = width, h = height;
        if (grid) {
            ctx.strokeStyle = gridColour;
            ctx.lineWidth = 1;
            for (let i = 1; i < 10; ++i) {
                const y = Math.round(h * i / 10) + 0.5;
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
            }
            for (let i = 1; i < 20; ++i) {
                const x = Math.round(w * i / 20) + 0.5;
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
            }
            ctx.strokeStyle = colour;
            ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
        }
        const n = values.length;
        if (n < 2) {
            return;
        }
        const step = w / (n - 1);
        const yOf = v => h - Math.max(0, Math.min(100, v)) / 100 * (h - 2) - 1;
        ctx.beginPath();
        ctx.moveTo(0, h);
        for (let i = 0; i < n; ++i) {
            ctx.lineTo(i * step, yOf(values[i]));
        }
        ctx.lineTo(w, h);
        ctx.closePath();
        ctx.fillStyle = Qt.rgba(colour.r, colour.g, colour.b, 0.15);
        ctx.fill();
        ctx.beginPath();
        for (let i = 0; i < n; ++i) {
            if (i === 0) {
                ctx.moveTo(0, yOf(values[0]));
            } else {
                ctx.lineTo(i * step, yOf(values[i]));
            }
        }
        ctx.strokeStyle = colour;
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }
}
