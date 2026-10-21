// Thin line glyphs of Windows 11's Notepad: the caption buttons, the tab
// "+", chevrons and arrows of the find panel, the settings gear and the
// "unsaved" dot of a tab.
import QtQuick
import "."

Canvas {
    id: glyph

    property string kind: "close"
    property color color: Theme.text
    property real lineWidth: 1

    implicitWidth: 10
    implicitHeight: 10
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        const w = width, h = height, o = lineWidth / 2;
        ctx.beginPath();
        switch (kind) {
        case "minimize":
            ctx.moveTo(0, Math.round(h / 2) + o);
            ctx.lineTo(w, Math.round(h / 2) + o);
            break;
        case "maximize":
            ctx.rect(o, o, w - lineWidth, h - lineWidth);
            break;
        case "restore":
            ctx.rect(o, 2 + o, w - 2 - lineWidth, h - 2 - lineWidth);
            ctx.moveTo(2 + o, 2);
            ctx.lineTo(2 + o, o);
            ctx.lineTo(w - o, o);
            ctx.lineTo(w - o, h - 2 - o);
            ctx.lineTo(w - 2, h - 2 - o);
            break;
        case "close":
            ctx.moveTo(o, o);
            ctx.lineTo(w - o, h - o);
            ctx.moveTo(w - o, o);
            ctx.lineTo(o, h - o);
            break;
        case "add":
            ctx.moveTo(0, h / 2);
            ctx.lineTo(w, h / 2);
            ctx.moveTo(w / 2, 0);
            ctx.lineTo(w / 2, h);
            break;
        case "chevron-down":
            ctx.moveTo(o, h * 0.3);
            ctx.lineTo(w / 2, h * 0.75);
            ctx.lineTo(w - o, h * 0.3);
            break;
        case "chevron-up":
            ctx.moveTo(o, h * 0.7);
            ctx.lineTo(w / 2, h * 0.25);
            ctx.lineTo(w - o, h * 0.7);
            break;
        case "chevron-right":
            ctx.moveTo(w * 0.3, o);
            ctx.lineTo(w * 0.75, h / 2);
            ctx.lineTo(w * 0.3, h - o);
            break;
        case "arrow-up":
            ctx.moveTo(w / 2, h - o);
            ctx.lineTo(w / 2, o);
            ctx.moveTo(o, h / 2);
            ctx.lineTo(w / 2, o);
            ctx.lineTo(w - o, h / 2);
            break;
        case "arrow-down":
            ctx.moveTo(w / 2, o);
            ctx.lineTo(w / 2, h - o);
            ctx.moveTo(o, h / 2);
            ctx.lineTo(w / 2, h - o);
            ctx.lineTo(w - o, h / 2);
            break;
        case "check":
            ctx.moveTo(o, h * 0.55);
            ctx.lineTo(w * 0.38, h - o);
            ctx.lineTo(w - o, o);
            break;
        case "gear": {
            const cx = w / 2, cy = h / 2, r1 = w * 0.48, r2 = w * 0.36;
            for (let i = 0; i < 8; ++i) {
                const a = i * Math.PI / 4;
                ctx.moveTo(cx + Math.cos(a) * r2, cy + Math.sin(a) * r2);
                ctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1);
            }
            ctx.moveTo(cx + r2, cy);
            ctx.arc(cx, cy, r2, 0, 2 * Math.PI);
            ctx.moveTo(cx + w * 0.15, cy);
            ctx.arc(cx, cy, w * 0.15, 0, 2 * Math.PI);
            break;
        }
        case "dot":
            ctx.arc(w / 2, h / 2, Math.min(w, h) / 2, 0, 2 * Math.PI);
            ctx.fill();
            return;
        case "back":
            ctx.moveTo(w - o, h / 2);
            ctx.lineTo(o, h / 2);
            ctx.moveTo(w * 0.45, o);
            ctx.lineTo(o, h / 2);
            ctx.lineTo(w * 0.45, h - o);
            break;
        }
        ctx.stroke();
    }
}
