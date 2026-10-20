// Line glyphs of VeltOS Calculator, drawn like Windows 11's (Fluent
// System Icons style, 1.5 px lines on a 20 px grid; VeltOS drawings, not
// Microsoft's).
import QtQuick

Canvas {
    id: glyph
    property string kind: ""
    property color color: Theme.text
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
        case "menu":            // hamburger
            line(ctx, [3, 5.5, 17, 5.5]);
            line(ctx, [3, 10, 17, 10]);
            line(ctx, [3, 14.5, 17, 14.5]);
            break;
        case "history":         // clock with a turning arrow
            ctx.beginPath();
            ctx.arc(10.5, 10, 6.75, Math.PI * 0.95, Math.PI * 2.75, false);
            ctx.stroke();
            line(ctx, [2.5, 6.5, 3.8, 9.6, 6.8, 8.4]);
            line(ctx, [10.5, 6.5, 10.5, 10.25, 13, 11.75]);
            break;
        case "keeptop":         // window with an arrow out of it
            roundRect(ctx, 2.75, 6.75, 10.5, 10.5, 2);
            ctx.stroke();
            line(ctx, [9, 11, 17, 3]);
            line(ctx, [12, 3, 17, 3, 17, 8]);
            break;
        case "fullview":        // window with an arrow into it
            roundRect(ctx, 2.75, 6.75, 10.5, 10.5, 2);
            ctx.stroke();
            line(ctx, [17, 3, 10, 10]);
            line(ctx, [10, 5.5, 10, 10, 14.5, 10]);
            break;
        case "back":            // backspace key
            ctx.beginPath();
            ctx.moveTo(7.25, 4.75);
            ctx.lineTo(16.25, 4.75);
            ctx.arcTo(17.75, 4.75, 17.75, 6.25, 1.5);
            ctx.lineTo(17.75, 13.75);
            ctx.arcTo(17.75, 15.25, 16.25, 15.25, 1.5);
            ctx.lineTo(7.25, 15.25);
            ctx.lineTo(2.25, 10);
            ctx.closePath();
            ctx.stroke();
            line(ctx, [9.75, 7.75, 14.25, 12.25]);
            line(ctx, [14.25, 7.75, 9.75, 12.25]);
            break;
        case "delete":          // waste basket
            line(ctx, [3.5, 5.25, 16.5, 5.25]);
            line(ctx, [7.75, 5.25, 7.75, 3.25, 12.25, 3.25, 12.25, 5.25]);
            line(ctx, [5, 5.25, 6, 16.75, 14, 16.75, 15, 5.25]);
            line(ctx, [8.5, 8.5, 8.75, 13.5]);
            line(ctx, [11.5, 8.5, 11.25, 13.5]);
            break;
        case "chevron":         // down
            line(ctx, [5, 7.5, 10, 12.5, 15, 7.5]);
            break;
        case "chevronup":
            line(ctx, [5, 12.5, 10, 7.5, 15, 12.5]);
            break;
        case "standard":        // calculator
            roundRect(ctx, 4.25, 2.75, 11.5, 14.5, 2);
            ctx.stroke();
            roundRect(ctx, 6.75, 5.25, 6.5, 2.5, 0.75);
            ctx.stroke();
            for (let r = 0; r < 3; ++r) {
                for (let c = 0; c < 3; ++c) {
                    ctx.beginPath();
                    ctx.arc(7.25 + c * 2.75, 10.5 + r * 2.25, 0.8, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
            break;
        case "scientific":      // flask
            line(ctx, [7, 2.75, 13, 2.75]);
            ctx.beginPath();
            ctx.moveTo(8.25, 2.75);
            ctx.lineTo(8.25, 8);
            ctx.lineTo(3.75, 15.25);
            ctx.arcTo(3, 17.25, 5.5, 17.25, 1.5);
            ctx.lineTo(14.5, 17.25);
            ctx.arcTo(17, 17.25, 16.25, 15.25, 1.5);
            ctx.lineTo(11.75, 8);
            ctx.lineTo(11.75, 2.75);
            ctx.stroke();
            line(ctx, [5.5, 12.5, 14.5, 12.5]);
            break;
        case "settings":        // gear
            ctx.beginPath();
            ctx.arc(10, 10, 2.5, 0, Math.PI * 2);
            ctx.stroke();
            ctx.beginPath();
            for (let i = 0; i < 16; ++i) {
                const a = i * Math.PI / 8 - Math.PI / 16;
                const r = (i % 2 === 0) ? 7.25 : 5.5;
                const x = 10 + r * Math.cos(a), y = 10 + r * Math.sin(a);
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            ctx.closePath();
            ctx.stroke();
            break;
        case "check":
            line(ctx, [4.5, 10.5, 8.25, 14, 15.5, 6.25]);
            break;
        }
    }
}
