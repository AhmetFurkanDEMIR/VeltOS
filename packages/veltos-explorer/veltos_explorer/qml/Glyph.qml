// Thin line glyphs drawn like Windows 11's caption and tab buttons:
// "minimize", "maximize", "restore", "close", "more" (three dots).
import QtQuick
import "."

Canvas {
    id: glyph

    property string kind: "close"
    property color color: Theme.text
    property real lineWidth: 1

    width: 10
    height: 10
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()
    // A layout may resize the glyph after its first paint (the navigation
    // pane's pins were drawn at 10 px and stretched).
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = lineWidth;
        const w = width, h = height, o = lineWidth / 2;
        ctx.beginPath();
        if (kind === "minimize") {
            ctx.moveTo(0, Math.round(h / 2) + o);
            ctx.lineTo(w, Math.round(h / 2) + o);
        } else if (kind === "maximize") {
            ctx.rect(o, o, w - lineWidth, h - lineWidth);
        } else if (kind === "restore") {
            ctx.rect(o, 2 + o, w - 2 - lineWidth, h - 2 - lineWidth);
            ctx.moveTo(2 + o, 2);
            ctx.lineTo(2 + o, o);
            ctx.lineTo(w - o, o);
            ctx.lineTo(w - o, h - 2 - o);
            ctx.lineTo(w - 2, h - 2 - o);
        } else if (kind === "close") {
            ctx.moveTo(0, 0);
            ctx.lineTo(w, h);
            ctx.moveTo(w, 0);
            ctx.lineTo(0, h);
        }
        ctx.stroke();
        if (kind === "more") {
            for (let i = 0; i < 3; ++i) {
                ctx.beginPath();
                ctx.arc(w / 6 + i * w / 3, h / 2, 1.1, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }
}
