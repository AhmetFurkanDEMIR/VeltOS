// Line glyphs of VeltOS Camera, drawn like Windows 11's (Fluent System
// Icons style, 1.5 px lines on a 20 px grid; VeltOS drawings, not
// Microsoft's).
import QtQuick

Canvas {
    id: glyph
    property string kind: ""
    property color color: "#FFFFFF"
    implicitWidth: 20
    implicitHeight: 20
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()

    function roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }
    function line(ctx, points) {
        ctx.beginPath();
        ctx.moveTo(points[0], points[1]);
        for (let i = 2; i < points.length; i += 2) {
            ctx.lineTo(points[i], points[i + 1]);
        }
        ctx.stroke();
    }
    function cameraBody(ctx, lens) {
        ctx.beginPath();
        ctx.moveTo(4, 6);
        ctx.lineTo(6.5, 6);
        ctx.lineTo(8, 4);
        ctx.lineTo(12, 4);
        ctx.lineTo(13.5, 6);
        ctx.lineTo(16, 6);
        ctx.arcTo(17.75, 6, 17.75, 7.75, 1.75);
        ctx.lineTo(17.75, 14.25);
        ctx.arcTo(17.75, 16, 16, 16, 1.75);
        ctx.lineTo(4, 16);
        ctx.arcTo(2.25, 16, 2.25, 14.25, 1.75);
        ctx.lineTo(2.25, 7.75);
        ctx.arcTo(2.25, 6, 4, 6, 1.75);
        ctx.closePath();
        ctx.stroke();
        if (lens) {
            ctx.beginPath();
            ctx.arc(10, 10.75, 3, 0, Math.PI * 2);
            ctx.stroke();
        }
    }

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.scale(width / 20, height / 20);
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 1.5;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        switch (kind) {
        case "camera":
            cameraBody(ctx, true);
            break;
        case "cameraoff":
            cameraBody(ctx, true);
            line(ctx, [2.5, 2.5, 17.5, 17.5]);
            break;
        case "video":
            roundRect(ctx, 2.25, 5.25, 11, 9.5, 2);
            ctx.stroke();
            line(ctx, [13.25, 8.75, 17.75, 6.25, 17.75, 13.75, 13.25, 11.25]);
            break;
        case "settings":        // gear
            ctx.beginPath();
            ctx.arc(10, 10, 2.5, 0, Math.PI * 2);
            ctx.stroke();
            ctx.beginPath();
            for (let i = 0; i < 8; ++i) {
                const a0 = i * Math.PI / 4 - 0.22, a1 = i * Math.PI / 4 + 0.22;
                const b0 = a1 + 0.12, b1 = (i + 1) * Math.PI / 4 - 0.34;
                const outer = 7.5, inner = 5.75;
                if (i === 0) {
                    ctx.moveTo(10 + outer * Math.cos(a0), 10 + outer * Math.sin(a0));
                }
                ctx.lineTo(10 + outer * Math.cos(a1), 10 + outer * Math.sin(a1));
                ctx.lineTo(10 + inner * Math.cos(b0), 10 + inner * Math.sin(b0));
                ctx.lineTo(10 + inner * Math.cos(b1), 10 + inner * Math.sin(b1));
                ctx.lineTo(10 + outer * Math.cos(b1 + 0.12), 10 + outer * Math.sin(b1 + 0.12));
            }
            ctx.closePath();
            ctx.stroke();
            break;
        case "timer":           // stopwatch
            ctx.beginPath();
            ctx.arc(10, 11, 6.5, 0, Math.PI * 2);
            ctx.stroke();
            line(ctx, [8, 2.75, 12, 2.75]);
            line(ctx, [10, 7.5, 10, 11, 12.5, 12.5]);
            line(ctx, [15.25, 5, 16.5, 3.75]);
            break;
        case "switch":          // camera with turning arrows
            cameraBody(ctx, false);
            ctx.beginPath();
            ctx.arc(10, 11, 3, Math.PI * 1.1, Math.PI * 1.9, false);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(10, 11, 3, Math.PI * 0.1, Math.PI * 0.9, false);
            ctx.stroke();
            line(ctx, [12.6, 7.4, 12.8, 9.6, 10.9, 9.0]);
            line(ctx, [7.4, 14.6, 7.2, 12.4, 9.1, 13.0]);
            break;
        case "close":
            line(ctx, [5, 5, 15, 15]);
            line(ctx, [15, 5, 5, 15]);
            break;
        case "folder":
            ctx.beginPath();
            ctx.moveTo(2.75, 5.5);
            ctx.arcTo(2.75, 4, 4.25, 4, 1.5);
            ctx.lineTo(8, 4);
            ctx.lineTo(9.75, 6);
            ctx.lineTo(15.75, 6);
            ctx.arcTo(17.25, 6, 17.25, 7.5, 1.5);
            ctx.lineTo(17.25, 14.5);
            ctx.arcTo(17.25, 16, 15.75, 16, 1.5);
            ctx.lineTo(4.25, 16);
            ctx.arcTo(2.75, 16, 2.75, 14.5, 1.5);
            ctx.closePath();
            ctx.stroke();
            break;
        }
    }
}
