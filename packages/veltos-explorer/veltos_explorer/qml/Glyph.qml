// Thin line glyphs drawn like Windows 11's caption and tab buttons:
// "minimize", "maximize", "restore", "close", "more" (three dots), "pin".
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
        if (kind === "pin") {
            // Push pin tilted to the right, as next to pinned folders in
            // Windows 11 (VeltOS drawing on a 16 px grid, any size).
            const s = Math.min(w, h) / 16;
            ctx.save();
            ctx.scale(s, s);
            ctx.translate(8, 8);
            ctx.rotate(Math.PI / 4);
            ctx.translate(-8, -8);
            ctx.lineWidth = lineWidth / s;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";
            ctx.beginPath();
            ctx.moveTo(5.5, 1.5);           // cap
            ctx.lineTo(10.5, 1.5);
            ctx.lineTo(10.5, 3.5);
            ctx.lineTo(5.5, 3.5);
            ctx.closePath();
            ctx.moveTo(6.5, 3.5);           // body
            ctx.lineTo(6, 8.5);
            ctx.moveTo(9.5, 3.5);
            ctx.lineTo(10, 8.5);
            ctx.moveTo(3.5, 8.5);           // collar
            ctx.lineTo(12.5, 8.5);
            ctx.moveTo(8, 8.5);             // needle
            ctx.lineTo(8, 14.5);
            ctx.stroke();
            ctx.restore();
        }
        if (kind === "more") {
            for (let i = 0; i < 3; ++i) {
                ctx.beginPath();
                ctx.arc(w / 6 + i * w / 3, h / 2, 1.1, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }
}
