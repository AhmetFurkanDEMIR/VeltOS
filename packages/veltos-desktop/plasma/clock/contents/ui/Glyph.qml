/*
    Small line glyphs of the Windows 11 calendar and notification flyouts
    (chevrons, the month arrows, minus/plus, play/stop, close, "more", the
    do-not-disturb bell), drawn so they match Windows' thin Fluent glyphs in
    every icon theme.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import org.kde.kirigami as Kirigami

Canvas {
    id: glyph

    property string kind: "close"
    property color color: Kirigami.Theme.textColor

    implicitWidth: 16
    implicitHeight: 16
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const c = getContext("2d");
        c.reset();
        const s = Math.min(width, height) / 16;   // drawn on a 16 x 16 grid
        c.save();
        c.translate((width - 16 * s) / 2, (height - 16 * s) / 2);
        c.scale(s, s);
        c.strokeStyle = glyph.color;
        c.fillStyle = glyph.color;
        c.lineWidth = 1.25;
        c.lineCap = "round";
        c.lineJoin = "round";
        c.beginPath();
        switch (glyph.kind) {
        case "chevron-up":
            c.moveTo(3.5, 10.5); c.lineTo(8, 6); c.lineTo(12.5, 10.5);
            c.stroke();
            break;
        case "chevron-down":
            c.moveTo(3.5, 6); c.lineTo(8, 10.5); c.lineTo(12.5, 6);
            c.stroke();
            break;
        case "triangle-up":
            c.moveTo(4, 10.5); c.lineTo(8, 5.5); c.lineTo(12, 10.5); c.closePath();
            c.fill();
            break;
        case "triangle-down":
            c.moveTo(4, 5.5); c.lineTo(8, 10.5); c.lineTo(12, 5.5); c.closePath();
            c.fill();
            break;
        case "minus":
            c.moveTo(3, 8); c.lineTo(13, 8);
            c.stroke();
            break;
        case "plus":
            c.moveTo(3, 8); c.lineTo(13, 8); c.moveTo(8, 3); c.lineTo(8, 13);
            c.stroke();
            break;
        case "play":
            c.moveTo(4.5, 2.5); c.lineTo(13, 8); c.lineTo(4.5, 13.5); c.closePath();
            c.fill();
            break;
        case "stop":
            c.roundedRect(3.5, 3.5, 9, 9, 1.5, 1.5);
            c.fill();
            break;
        case "close":
            c.moveTo(4, 4); c.lineTo(12, 12); c.moveTo(12, 4); c.lineTo(4, 12);
            c.stroke();
            break;
        case "more":
            for (const x of [3, 8, 13]) {
                c.moveTo(x + 1, 8);
                c.arc(x, 8, 1, 0, 2 * Math.PI);
            }
            c.fill();
            break;
        case "dnd":
            // A bell with a small "z" (Windows' do-not-disturb glyph).
            c.moveTo(2.5, 12); c.lineTo(10.5, 12);
            c.moveTo(3.5, 12);
            c.lineTo(3.5, 7.5);
            c.bezierCurveTo(3.5, 4.8, 5, 3.5, 6.5, 3.5);
            c.bezierCurveTo(8, 3.5, 9.5, 4.8, 9.5, 7.5);
            c.lineTo(9.5, 12);
            c.moveTo(5.2, 14); c.lineTo(7.8, 14);
            c.moveTo(10.5, 1.5); c.lineTo(14, 1.5); c.lineTo(10.5, 5.5); c.lineTo(14, 5.5);
            c.stroke();
            break;
        }
        c.restore();
    }
}
