// Thin line glyphs of Windows 11 Photos, drawn on a 16 x 16 grid so they
// look the same in every icon theme: caption buttons, navigation, the
// viewer's toolbar (zoom, rotate, edit, delete, heart, information, more),
// the editor's tools and the gallery's filter, sort and view buttons.
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
        c.fillStyle = glyph.color;
        c.lineWidth = glyph.lineWidth / s;
        c.lineCap = "round";
        c.lineJoin = "round";
        c.beginPath();
        let fill = false;
        switch (glyph.kind) {
        case "minimize": c.moveTo(3, 8.5); c.lineTo(13, 8.5); break;
        case "maximize": c.rect(3.5, 3.5, 9, 9); break;
        case "restore":
            c.rect(3.5, 5.5, 7, 7); c.moveTo(5.5, 5.5); c.lineTo(5.5, 3.5); c.lineTo(12.5, 3.5);
            c.lineTo(12.5, 10.5); c.lineTo(10.5, 10.5); break;
        case "close": c.moveTo(4, 4); c.lineTo(12, 12); c.moveTo(12, 4); c.lineTo(4, 12); break;
        case "back": c.moveTo(13, 8); c.lineTo(3, 8); c.moveTo(7.5, 3.5); c.lineTo(3, 8); c.lineTo(7.5, 12.5); break;
        case "chevron-left": c.moveTo(10, 3); c.lineTo(5, 8); c.lineTo(10, 13); break;
        case "chevron-right": c.moveTo(6, 3); c.lineTo(11, 8); c.lineTo(6, 13); break;
        case "chevron-down": c.moveTo(3.5, 6); c.lineTo(8, 10.5); c.lineTo(12.5, 6); break;
        case "chevron-up": c.moveTo(3.5, 10); c.lineTo(8, 5.5); c.lineTo(12.5, 10); break;
        case "check": c.moveTo(3, 8.5); c.lineTo(6.5, 12); c.lineTo(13, 4.5); break;
        case "add": c.moveTo(8, 3); c.lineTo(8, 13); c.moveTo(3, 8); c.lineTo(13, 8); break;
        case "search":
            c.arc(6.8, 6.8, 4.3, 0, 2 * Math.PI); c.moveTo(10, 10); c.lineTo(13.5, 13.5); break;
        case "zoom-in":
            c.arc(6.8, 6.8, 4.3, 0, 2 * Math.PI); c.moveTo(10, 10); c.lineTo(13.5, 13.5);
            c.moveTo(4.8, 6.8); c.lineTo(8.8, 6.8); c.moveTo(6.8, 4.8); c.lineTo(6.8, 8.8); break;
        case "zoom-out":
            c.arc(6.8, 6.8, 4.3, 0, 2 * Math.PI); c.moveTo(10, 10); c.lineTo(13.5, 13.5);
            c.moveTo(4.8, 6.8); c.lineTo(8.8, 6.8); break;
        case "fit":
            c.moveTo(2.5, 6); c.lineTo(2.5, 2.5); c.lineTo(6, 2.5); c.moveTo(10, 2.5); c.lineTo(13.5, 2.5);
            c.lineTo(13.5, 6); c.moveTo(13.5, 10); c.lineTo(13.5, 13.5); c.lineTo(10, 13.5);
            c.moveTo(6, 13.5); c.lineTo(2.5, 13.5); c.lineTo(2.5, 10); break;
        case "rotate":
            c.arc(8, 8.5, 5, Math.PI * 1.55, Math.PI * 1.2, false);
            c.moveTo(8.8, 1.2); c.lineTo(11, 3.4); c.lineTo(8.6, 5.4); break;
        case "rotate-left":       // "rotate" mirrored
            c.translate(16, 0);
            c.scale(-1, 1);
            c.arc(8, 8.5, 5, Math.PI * 1.55, Math.PI * 1.2, false);
            c.moveTo(8.8, 1.2); c.lineTo(11, 3.4); c.lineTo(8.6, 5.4); break;
        case "edit":
            c.moveTo(3, 13); c.lineTo(3.6, 10.2); c.lineTo(10.8, 3); c.lineTo(13, 5.2); c.lineTo(5.8, 12.4);
            c.closePath(); c.moveTo(9.4, 4.4); c.lineTo(11.6, 6.6); break;
        case "delete":
            c.moveTo(2.5, 4); c.lineTo(13.5, 4); c.moveTo(6, 4); c.lineTo(6.5, 2.5); c.lineTo(9.5, 2.5);
            c.lineTo(10, 4); c.moveTo(4, 4); c.lineTo(4.8, 13.5); c.lineTo(11.2, 13.5); c.lineTo(12, 4);
            c.moveTo(6.8, 6.5); c.lineTo(6.8, 11); c.moveTo(9.2, 6.5); c.lineTo(9.2, 11); break;
        case "heart":
        case "heart-filled":
            c.moveTo(8, 13.5);
            c.bezierCurveTo(1, 9, 1.5, 3, 5, 3); c.bezierCurveTo(6.6, 3, 7.5, 4, 8, 5);
            c.bezierCurveTo(8.5, 4, 9.4, 3, 11, 3); c.bezierCurveTo(14.5, 3, 15, 9, 8, 13.5);
            fill = glyph.kind === "heart-filled";
            break;
        case "info":
            c.arc(8, 8, 6, 0, 2 * Math.PI); c.moveTo(8, 7.2); c.lineTo(8, 11.5); c.moveTo(8.6, 4.9);
            c.arc(8, 4.9, 0.6, 0, 2 * Math.PI); break;
        case "more":
            for (const x of [3, 8, 13]) { c.moveTo(x + 1, 8); c.arc(x, 8, 1, 0, 2 * Math.PI); }
            fill = true;
            break;
        case "gallery":
            c.rect(2.5, 3.5, 11, 9); c.moveTo(2.5, 10.5); c.lineTo(6, 7); c.lineTo(9, 10); c.lineTo(10.5, 8.5);
            c.lineTo(13.5, 11.5); c.moveTo(11.3, 6); c.arc(10.5, 6, 0.8, 0, 2 * Math.PI); break;
        case "folder":
            c.moveTo(2.5, 12.5); c.lineTo(2.5, 3.5); c.lineTo(6.5, 3.5); c.lineTo(8, 5); c.lineTo(13.5, 5);
            c.lineTo(13.5, 12.5); c.closePath(); c.moveTo(2.5, 7); c.lineTo(13.5, 7); break;
        case "gear": {
            for (let i = 0; i < 8; ++i) {
                const a = i * Math.PI / 4;
                c.moveTo(8 + Math.cos(a) * 4.6, 8 + Math.sin(a) * 4.6);
                c.lineTo(8 + Math.cos(a) * 6.4, 8 + Math.sin(a) * 6.4);
            }
            c.moveTo(12.6, 8); c.arc(8, 8, 4.6, 0, 2 * Math.PI); c.moveTo(10.2, 8); c.arc(8, 8, 2.2, 0, 2 * Math.PI);
            break;
        }
        case "filter": c.moveTo(2.5, 3.5); c.lineTo(13.5, 3.5); c.lineTo(9.5, 8.5); c.lineTo(9.5, 13);
            c.lineTo(6.5, 11.5); c.lineTo(6.5, 8.5); c.closePath(); break;
        case "sort": c.moveTo(5, 13); c.lineTo(5, 3); c.moveTo(2.5, 5.5); c.lineTo(5, 3); c.lineTo(7.5, 5.5);
            c.moveTo(11, 3); c.lineTo(11, 13); c.moveTo(8.5, 10.5); c.lineTo(11, 13); c.lineTo(13.5, 10.5); break;
        case "grid": c.rect(2.5, 2.5, 4.5, 4.5); c.rect(9, 2.5, 4.5, 4.5); c.rect(2.5, 9, 4.5, 4.5);
            c.rect(9, 9, 4.5, 4.5); break;
        case "play": c.moveTo(4.5, 2.5); c.lineTo(13, 8); c.lineTo(4.5, 13.5); c.closePath(); fill = true; break;
        case "play-outline": c.moveTo(4.5, 2.5); c.lineTo(13, 8); c.lineTo(4.5, 13.5); c.closePath(); break;
        case "pause": c.rect(4, 3, 2.5, 10); c.rect(9.5, 3, 2.5, 10); fill = true; break;
        case "crop": c.moveTo(4.5, 1.5); c.lineTo(4.5, 11.5); c.lineTo(14.5, 11.5); c.moveTo(1.5, 4.5);
            c.lineTo(11.5, 4.5); c.lineTo(11.5, 14.5); break;
        case "adjust":
            c.arc(8, 8, 3, 0, 2 * Math.PI);
            for (let i = 0; i < 8; ++i) {
                const a = i * Math.PI / 4;
                c.moveTo(8 + Math.cos(a) * 4.8, 8 + Math.sin(a) * 4.8);
                c.lineTo(8 + Math.cos(a) * 6.5, 8 + Math.sin(a) * 6.5);
            }
            break;
        case "flip": c.moveTo(8, 1.5); c.lineTo(8, 14.5); c.moveTo(6, 3.5); c.lineTo(2, 12.5); c.lineTo(6, 12.5);
            c.closePath(); c.moveTo(10, 3.5); c.lineTo(14, 12.5); c.lineTo(10, 12.5); c.closePath(); break;
        case "video":
            c.rect(1.5, 4, 9.5, 8); c.moveTo(11, 7); c.lineTo(14.5, 5); c.lineTo(14.5, 11); c.lineTo(11, 9); break;
        case "copy": c.rect(5.5, 5.5, 8, 8); c.moveTo(3.5, 10.5); c.lineTo(2.5, 10.5); c.lineTo(2.5, 2.5);
            c.lineTo(10.5, 2.5); c.lineTo(10.5, 3.5); break;
        case "dot": c.arc(8, 8, 3, 0, 2 * Math.PI); fill = true; break;
        case "home":
            c.moveTo(2.5, 7.5); c.lineTo(8, 2.5); c.lineTo(13.5, 7.5); c.moveTo(4, 6.2); c.lineTo(4, 13.5);
            c.lineTo(12, 13.5); c.lineTo(12, 6.2); c.moveTo(6.8, 13.5); c.lineTo(6.8, 9.5); c.lineTo(9.2, 9.5);
            c.lineTo(9.2, 13.5); break;
        case "music":
            c.moveTo(6, 12); c.lineTo(6, 3); c.lineTo(13, 1.8); c.lineTo(13, 10.5);
            c.moveTo(6, 5.5); c.lineTo(13, 4.3);
            c.moveTo(6, 12); c.arc(4.3, 12, 1.7, 0, 2 * Math.PI); c.moveTo(13, 10.5); c.arc(11.3, 10.5, 1.7, 0, 2 * Math.PI);
            break;
        case "queue":
            c.moveTo(2, 4); c.lineTo(12, 4); c.moveTo(2, 7.5); c.lineTo(12, 7.5); c.moveTo(2, 11); c.lineTo(7, 11);
            c.moveTo(9.5, 9.5); c.lineTo(14, 12); c.lineTo(9.5, 14.5); c.closePath(); break;
        case "playlist":
            c.moveTo(2, 4); c.lineTo(10, 4); c.moveTo(2, 7.5); c.lineTo(10, 7.5); c.moveTo(2, 11); c.lineTo(7, 11);
            c.moveTo(12, 13); c.lineTo(12, 6); c.lineTo(14.5, 6.8); c.moveTo(12, 13); c.arc(10.8, 13, 1.2, 0, 2 * Math.PI);
            break;
        case "previous":
            c.moveTo(3.5, 3); c.lineTo(3.5, 13); c.moveTo(13, 3); c.lineTo(5.5, 8); c.lineTo(13, 13); c.closePath();
            fill = true; c.fill(); fill = false; break;
        case "next":
            c.moveTo(12.5, 3); c.lineTo(12.5, 13); c.moveTo(3, 3); c.lineTo(10.5, 8); c.lineTo(3, 13); c.closePath();
            fill = true; c.fill(); fill = false; break;
        case "shuffle":
            c.moveTo(2, 4.5); c.lineTo(5, 4.5); c.lineTo(10.5, 11.5); c.lineTo(14, 11.5);
            c.moveTo(2, 11.5); c.lineTo(5, 11.5); c.lineTo(10.5, 4.5); c.lineTo(14, 4.5);
            c.moveTo(12, 2.5); c.lineTo(14, 4.5); c.lineTo(12, 6.5); c.moveTo(12, 9.5); c.lineTo(14, 11.5); c.lineTo(12, 13.5);
            break;
        case "repeat":
        case "repeat-one":
            c.moveTo(2.5, 8); c.lineTo(2.5, 6.5); c.quadraticCurveTo(2.5, 4.5, 4.5, 4.5); c.lineTo(13, 4.5);
            c.moveTo(11, 2.5); c.lineTo(13, 4.5); c.lineTo(11, 6.5);
            c.moveTo(13.5, 8); c.lineTo(13.5, 9.5); c.quadraticCurveTo(13.5, 11.5, 11.5, 11.5); c.lineTo(3, 11.5);
            c.moveTo(5, 9.5); c.lineTo(3, 11.5); c.lineTo(5, 13.5);
            if (glyph.kind === "repeat-one") { c.moveTo(7.5, 7); c.lineTo(8.5, 6.3); c.lineTo(8.5, 10); }
            break;
        case "volume":
        case "mute":
            c.moveTo(2, 6); c.lineTo(4.5, 6); c.lineTo(8, 3); c.lineTo(8, 13); c.lineTo(4.5, 10); c.lineTo(2, 10); c.closePath();
            if (glyph.kind === "volume") {
                c.moveTo(10.5, 5.5); c.quadraticCurveTo(12, 8, 10.5, 10.5);
                c.moveTo(12.3, 3.8); c.quadraticCurveTo(15, 8, 12.3, 12.2);
            } else {
                c.moveTo(10.5, 6); c.lineTo(14.5, 10); c.moveTo(14.5, 6); c.lineTo(10.5, 10);
            }
            break;
        case "fullscreen":
            c.moveTo(2.5, 6); c.lineTo(2.5, 2.5); c.lineTo(6, 2.5); c.moveTo(10, 2.5); c.lineTo(13.5, 2.5);
            c.lineTo(13.5, 6); c.moveTo(13.5, 10); c.lineTo(13.5, 13.5); c.lineTo(10, 13.5);
            c.moveTo(6, 13.5); c.lineTo(2.5, 13.5); c.lineTo(2.5, 10); break;
        case "exit-fullscreen":
            c.moveTo(2.5, 6); c.lineTo(6, 6); c.lineTo(6, 2.5); c.moveTo(10, 2.5); c.lineTo(10, 6);
            c.lineTo(13.5, 6); c.moveTo(13.5, 10); c.lineTo(10, 10); c.lineTo(10, 13.5);
            c.moveTo(6, 13.5); c.lineTo(6, 10); c.lineTo(2.5, 10); break;
        case "album":
            c.arc(8, 8, 6, 0, 2 * Math.PI); c.moveTo(9.5, 8); c.arc(8, 8, 1.5, 0, 2 * Math.PI); break;
        case "person":
            c.arc(8, 5.5, 3, 0, 2 * Math.PI); c.moveTo(2.5, 14); c.quadraticCurveTo(8, 6.5, 13.5, 14); break;
        }
        if (fill)
            c.fill();
        else
            c.stroke();
        c.restore();
    }
}
