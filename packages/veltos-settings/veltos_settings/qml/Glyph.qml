// Thin line glyphs of the title bar (back, search and the caption
// buttons), drawn on a 16 x 16 grid so they look the same in every icon
// theme, as in VeltOS' other self-drawn windows.
import QtQuick
import "."

Canvas {
    id: glyph

    property string kind: "close"
    property color color: Theme.text
    property real lineWidth: 1.2

    implicitWidth: 16
    implicitHeight: 16
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const c = getContext("2d");
        c.reset();
        const s = Math.min(width, height) / 16;
        c.save();
        c.translate((width - 16 * s) / 2, (height - 16 * s) / 2);
        c.scale(s, s);
        c.strokeStyle = glyph.color;
        c.lineWidth = glyph.lineWidth / s;
        c.lineCap = "round";
        c.lineJoin = "round";
        c.beginPath();
        switch (glyph.kind) {
        case "minimize": c.moveTo(3, 8.5); c.lineTo(13, 8.5); break;
        case "maximize": c.rect(3.5, 3.5, 9, 9); break;
        case "restore":
            c.rect(3.5, 5.5, 7, 7); c.moveTo(5.5, 5.5); c.lineTo(5.5, 3.5); c.lineTo(12.5, 3.5);
            c.lineTo(12.5, 10.5); c.lineTo(10.5, 10.5); break;
        case "close": c.moveTo(4, 4); c.lineTo(12, 12); c.moveTo(12, 4); c.lineTo(4, 12); break;
        case "back": c.moveTo(13, 8); c.lineTo(3, 8); c.moveTo(7.5, 3.5); c.lineTo(3, 8); c.lineTo(7.5, 12.5); break;
        case "search":
            c.arc(6.8, 6.8, 4.3, 0, 2 * Math.PI); c.moveTo(10, 10); c.lineTo(13.5, 13.5); break;
        }
        c.stroke();
        c.restore();
    }
}
