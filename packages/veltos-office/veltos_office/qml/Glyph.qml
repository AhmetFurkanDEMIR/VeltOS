// Thin line glyphs in the style of Windows 11's Segoe Fluent icons, drawn
// on a canvas: the caption buttons ("minimize", "maximize", "restore",
// "close"), the navigation rail ("home", "new", "open", "account",
// "options"), and "pin", "pinned", "search", "back", "forward", "plus",
// "more", "check", "folder".
import QtQuick
import "."

Canvas {
    id: glyph

    property string kind: "close"
    property color color: Theme.text
    property real lineWidth: 1.2

    width: 20
    height: 20
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        const caption = ["minimize", "maximize", "restore", "close"].indexOf(kind) >= 0;
        if (caption) {
            paintCaption(ctx);
            return;
        }
        // Everything else is designed on a 20 x 20 grid.
        const s = Math.min(width, height) / 20;
        ctx.scale(s, s);
        ctx.lineWidth = lineWidth / s;
        ctx.beginPath();
        if (kind === "home") {
            ctx.moveTo(2.5, 10); ctx.lineTo(10, 3); ctx.lineTo(17.5, 10);
            ctx.moveTo(4.5, 8.5); ctx.lineTo(4.5, 17); ctx.lineTo(15.5, 17); ctx.lineTo(15.5, 8.5);
            ctx.moveTo(8, 17); ctx.lineTo(8, 12); ctx.lineTo(12, 12); ctx.lineTo(12, 17);
        } else if (kind === "new") {
            ctx.moveTo(4.5, 2.5); ctx.lineTo(11.5, 2.5); ctx.lineTo(15.5, 6.5); ctx.lineTo(15.5, 17.5);
            ctx.lineTo(4.5, 17.5); ctx.closePath();
            ctx.moveTo(11.5, 2.5); ctx.lineTo(11.5, 6.5); ctx.lineTo(15.5, 6.5);
            ctx.moveTo(10, 9.5); ctx.lineTo(10, 14.5);
            ctx.moveTo(7.5, 12); ctx.lineTo(12.5, 12);
        } else if (kind === "open" || kind === "folder") {
            ctx.moveTo(2.5, 4.5); ctx.lineTo(7.5, 4.5); ctx.lineTo(9.5, 6.5); ctx.lineTo(17.5, 6.5);
            ctx.lineTo(17.5, 16); ctx.lineTo(2.5, 16); ctx.closePath();
            ctx.moveTo(2.5, 9); ctx.lineTo(17.5, 9);
        } else if (kind === "account") {
            ctx.arc(10, 7, 3.6, 0, 2 * Math.PI);
            ctx.moveTo(3.5, 17.5);
            ctx.bezierCurveTo(3.5, 12.5, 16.5, 12.5, 16.5, 17.5);
        } else if (kind === "options") {
            ctx.arc(10, 10, 5.8, 0, 2 * Math.PI);
            ctx.moveTo(12.6, 10); ctx.arc(10, 10, 2.6, 0, 2 * Math.PI);
            for (let i = 0; i < 8; ++i) {
                const a = i * Math.PI / 4;
                ctx.moveTo(10 + 5.8 * Math.cos(a), 10 + 5.8 * Math.sin(a));
                ctx.lineTo(10 + 8.3 * Math.cos(a), 10 + 8.3 * Math.sin(a));
            }
        } else if (kind === "pin" || kind === "pinned") {
            ctx.moveTo(11.5, 2.5); ctx.lineTo(17.5, 8.5); ctx.lineTo(14.2, 9.2); ctx.lineTo(11.3, 13.7);
            ctx.lineTo(6.3, 8.7); ctx.lineTo(10.8, 5.8); ctx.closePath();
            if (kind === "pinned")
                ctx.fill();
            ctx.moveTo(8.5, 11.5); ctx.lineTo(3, 17);
        } else if (kind === "search") {
            ctx.arc(8.5, 8.5, 5.5, 0, 2 * Math.PI);
            ctx.moveTo(12.5, 12.5); ctx.lineTo(17.5, 17.5);
        } else if (kind === "back") {
            ctx.moveTo(16.5, 10); ctx.lineTo(3.5, 10);
            ctx.moveTo(8.5, 5); ctx.lineTo(3.5, 10); ctx.lineTo(8.5, 15);
        } else if (kind === "forward") {
            ctx.moveTo(3.5, 10); ctx.lineTo(16.5, 10);
            ctx.moveTo(11.5, 5); ctx.lineTo(16.5, 10); ctx.lineTo(11.5, 15);
        } else if (kind === "plus") {
            ctx.moveTo(10, 3.5); ctx.lineTo(10, 16.5);
            ctx.moveTo(3.5, 10); ctx.lineTo(16.5, 10);
        } else if (kind === "check") {
            ctx.moveTo(3.5, 10.5); ctx.lineTo(8, 15); ctx.lineTo(16.5, 5.5);
        } else if (kind === "chevron-down") {
            ctx.moveTo(5, 8); ctx.lineTo(10, 13); ctx.lineTo(15, 8);
        } else if (kind === "more") {
            for (let i = 0; i < 3; ++i) {
                ctx.moveTo(5 + i * 5 + 1.3, 10);
                ctx.arc(5 + i * 5, 10, 1.3, 0, 2 * Math.PI);
            }
            ctx.fill();
            return;
        }
        ctx.stroke();
    }

    function paintCaption(ctx) {
        // Windows 11 caption glyphs: 10 x 10, 1 px lines.
        ctx.lineWidth = 1;
        const w = width, h = height, o = 0.5;
        ctx.beginPath();
        if (kind === "minimize") {
            ctx.moveTo(0, Math.round(h / 2) + o);
            ctx.lineTo(w, Math.round(h / 2) + o);
        } else if (kind === "maximize") {
            ctx.rect(o, o, w - 1, h - 1);
        } else if (kind === "restore") {
            ctx.rect(o, 2 + o, w - 3, h - 3);
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
    }
}
