// Line glyphs of the Snipping Tool buttons, drawn like Windows 11's
// (Fluent System Icons style, 1.5 px lines on a 20 px grid; VeltOS
// drawings, not Microsoft's).
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
        case "rect":            // dashed selection
            ctx.setLineDash([2.5, 2]);
            ctx.strokeRect(3, 4.5, 14, 11);
            ctx.setLineDash([]);
            break;
        case "window":          // window with title bar
            roundRect(ctx, 2.75, 3.75, 14.5, 12.5, 2);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(2.75, 7.25);
            ctx.lineTo(17.25, 7.25);
            ctx.stroke();
            break;
        case "full":            // monitor
            roundRect(ctx, 2.75, 3.25, 14.5, 10, 1.5);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(10, 13.25);
            ctx.lineTo(10, 16.25);
            ctx.moveTo(6.5, 16.5);
            ctx.lineTo(13.5, 16.5);
            ctx.stroke();
            break;
        case "free":            // lasso
            ctx.beginPath();
            ctx.ellipse(3, 3.5, 14, 9);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(7, 12);
            ctx.quadraticCurveTo(6, 15, 8.5, 16.5);
            ctx.stroke();
            break;
        case "close":
            ctx.beginPath();
            ctx.moveTo(5, 5);
            ctx.lineTo(15, 15);
            ctx.moveTo(15, 5);
            ctx.lineTo(5, 15);
            ctx.stroke();
            break;
        case "plus":
            ctx.beginPath();
            ctx.moveTo(10, 4);
            ctx.lineTo(10, 16);
            ctx.moveTo(4, 10);
            ctx.lineTo(16, 10);
            ctx.stroke();
            break;
        case "chevron":
            ctx.beginPath();
            ctx.moveTo(6, 8);
            ctx.lineTo(10, 12);
            ctx.lineTo(14, 8);
            ctx.stroke();
            break;
        case "clock":
            ctx.beginPath();
            ctx.arc(10, 10, 7, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(10, 6);
            ctx.lineTo(10, 10);
            ctx.lineTo(13, 11.5);
            ctx.stroke();
            break;
        case "pen":             // ballpoint pen, tip bottom left
            ctx.beginPath();
            ctx.moveTo(13.5, 3.5);
            ctx.lineTo(16.5, 6.5);
            ctx.lineTo(7, 16);
            ctx.lineTo(3.5, 16.5);
            ctx.lineTo(4, 13);
            ctx.closePath();
            ctx.stroke();
            break;
        case "highlighter":     // chisel marker
            ctx.beginPath();
            ctx.moveTo(12, 3);
            ctx.lineTo(17, 8);
            ctx.lineTo(10, 15);
            ctx.lineTo(5, 10);
            ctx.closePath();
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(5, 10);
            ctx.lineTo(3, 16);
            ctx.lineTo(4, 17);
            ctx.lineTo(10, 15);
            ctx.stroke();
            break;
        case "eraser":
            ctx.beginPath();
            ctx.moveTo(11, 3.5);
            ctx.lineTo(17, 9.5);
            ctx.lineTo(10.5, 16);
            ctx.lineTo(6, 16);
            ctx.lineTo(3, 13);
            ctx.closePath();
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(7, 7.5);
            ctx.lineTo(13, 13.5);
            ctx.moveTo(10.5, 16.5);
            ctx.lineTo(17, 16.5);
            ctx.stroke();
            break;
        case "crop":
            ctx.beginPath();
            ctx.moveTo(6, 2.5);
            ctx.lineTo(6, 14);
            ctx.lineTo(17.5, 14);
            ctx.moveTo(2.5, 6);
            ctx.lineTo(14, 6);
            ctx.lineTo(14, 17.5);
            ctx.stroke();
            break;
        case "undo":
        case "redo":
            if (kind === "redo") {
                ctx.translate(20, 0);
                ctx.scale(-1, 1);
            }
            ctx.beginPath();
            ctx.moveTo(4, 8);
            ctx.lineTo(12, 8);
            ctx.arc(12, 12, 4, -Math.PI / 2, Math.PI / 2);
            ctx.lineTo(8, 16);
            ctx.moveTo(7, 5);
            ctx.lineTo(4, 8);
            ctx.lineTo(7, 11);
            ctx.stroke();
            break;
        case "save":            // floppy disk
            roundRect(ctx, 3, 3, 14, 14, 1.5);
            ctx.stroke();
            ctx.strokeRect(6.5, 3, 7, 4.5);
            ctx.strokeRect(6, 11, 8, 6);
            break;
        case "copy":
            roundRect(ctx, 6.5, 6.5, 10, 11, 1.5);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(4, 13.5);
            ctx.lineTo(3.5, 13.5);
            ctx.lineTo(3.5, 4);
            ctx.arcTo(3.5, 2.5, 5, 2.5, 1.5);
            ctx.lineTo(13.5, 2.5);
            ctx.lineTo(13.5, 4);
            ctx.stroke();
            break;
        case "more":
            for (const x of [4.5, 10, 15.5]) {
                ctx.beginPath();
                ctx.arc(x, 10, 1.2, 0, 2 * Math.PI);
                ctx.fill();
            }
            break;
        case "check":
            ctx.beginPath();
            ctx.moveTo(4.5, 10.5);
            ctx.lineTo(8.5, 14.5);
            ctx.lineTo(15.5, 6);
            ctx.stroke();
            break;
        }
    }
}
