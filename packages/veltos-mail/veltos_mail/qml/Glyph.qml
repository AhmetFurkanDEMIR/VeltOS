// Line icons in the style of the Fluent System Icons Outlook uses (20 px
// regular), drawn on a canvas on a 20 x 20 grid; "filled" variants for the
// selected app bar entry. The caption buttons follow Windows 11 (10 x 10).
import QtQuick
import "."

Canvas {
    id: glyph

    property string kind: "mail"
    property color color: Theme.text
    property bool filled: false
    property real lineWidth: 1.25

    width: 20
    height: 20
    onKindChanged: requestPaint()
    onColorChanged: requestPaint()
    onFilledChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    function line(ctx, pts) {
        ctx.moveTo(pts[0], pts[1]);
        for (let i = 2; i < pts.length; i += 2)
            ctx.lineTo(pts[i], pts[i + 1]);
    }
    function roundRect(ctx, x, y, w, h, r) {
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y); ctx.arcTo(x + w, y, x + w, y + r, r);
        ctx.lineTo(x + w, y + h - r); ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
        ctx.lineTo(x + r, y + h); ctx.arcTo(x, y + h, x, y + h - r, r);
        ctx.lineTo(x, y + r); ctx.arcTo(x, y, x + r, y, r);
        ctx.closePath();
    }
    function envelope(ctx) {
        roundRect(ctx, 2.5, 4.5, 15, 11, 2);
        line(ctx, [3.2, 6, 10, 10.6, 16.8, 6]);
    }

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        if (["minimize", "maximize", "restore", "close-caption"].indexOf(kind) >= 0) {
            paintCaption(ctx);
            return;
        }
        const s = Math.min(width, height) / 20;
        ctx.translate((width - 20 * s) / 2, (height - 20 * s) / 2);
        ctx.scale(s, s);
        ctx.lineWidth = lineWidth / s;
        ctx.beginPath();
        switch (kind) {
        case "mail":
            envelope(ctx);
            if (filled) { ctx.globalAlpha = 0.18; ctx.fill(); ctx.globalAlpha = 1; }
            break;
        case "mail-read":
            line(ctx, [2.5, 8.5, 10, 3.5, 17.5, 8.5, 17.5, 16, 2.5, 16, 2.5, 8.5]);
            line(ctx, [3.2, 9.2, 10, 13.2, 16.8, 9.2]);
            break;
        case "new-mail":
            roundRect(ctx, 2.5, 4.5, 11.5, 10, 2);
            line(ctx, [3.2, 6, 8.2, 9.6, 13.2, 6]);
            line(ctx, [15.5, 11, 15.5, 17]);
            line(ctx, [12.5, 14, 18.5, 14]);
            break;
        case "calendar":
            roundRect(ctx, 2.5, 3.5, 15, 14, 2.5);
            line(ctx, [2.5, 7.5, 17.5, 7.5]);
            if (filled) { ctx.globalAlpha = 0.18; ctx.fill(); ctx.globalAlpha = 1; }
            for (let r = 0; r < 2; ++r)
                for (let c = 0; c < 3; ++c) {
                    ctx.moveTo(6.6 + c * 3.4, 11 + r * 3.2);
                    ctx.arc(6 + c * 3.4, 11 + r * 3.2, 0.6, 0, 2 * Math.PI);
                }
            break;
        case "people":
            ctx.arc(7.5, 6.5, 2.8, 0, 2 * Math.PI);
            ctx.moveTo(2.5, 16.5); ctx.bezierCurveTo(2.5, 11, 12.5, 11, 12.5, 16.5);
            ctx.moveTo(15.8, 7.5); ctx.arc(13.8, 7.5, 2, 0, 2 * Math.PI);
            ctx.moveTo(14, 12); ctx.bezierCurveTo(16.5, 12, 17.5, 13.5, 17.5, 16.5);
            break;
        case "person":
            ctx.arc(10, 6.5, 3.4, 0, 2 * Math.PI);
            ctx.moveTo(3.5, 17.5); ctx.bezierCurveTo(3.5, 11.5, 16.5, 11.5, 16.5, 17.5);
            break;
        case "delete":
            line(ctx, [3, 5, 17, 5]);
            line(ctx, [8, 5, 8, 3.2, 12, 3.2, 12, 5]);
            line(ctx, [4.5, 5, 5.5, 16.5, 14.5, 16.5, 15.5, 5]);
            line(ctx, [8.5, 8, 8.5, 13.5]); line(ctx, [11.5, 8, 11.5, 13.5]);
            break;
        case "archive":
            roundRect(ctx, 2.5, 3.5, 15, 4, 1.2);
            line(ctx, [3.5, 7.5, 3.5, 15.5, 16.5, 15.5, 16.5, 7.5]);
            line(ctx, [8, 10.5, 12, 10.5]);
            break;
        case "report":
            line(ctx, [10, 2.5, 16.5, 5, 16.5, 9.5]);
            ctx.bezierCurveTo(16.5, 13.5, 13.5, 16.3, 10, 17.5);
            ctx.bezierCurveTo(6.5, 16.3, 3.5, 13.5, 3.5, 9.5);
            line(ctx, [3.5, 9.5, 3.5, 5, 10, 2.5]);
            line(ctx, [10, 6.5, 10, 10.5]);
            ctx.moveTo(10.6, 13.2); ctx.arc(10, 13.2, 0.6, 0, 2 * Math.PI);
            break;
        case "junk":
            ctx.arc(10, 10, 7, 0, 2 * Math.PI);
            line(ctx, [5.1, 5.1, 14.9, 14.9]);
            break;
        case "move":
            line(ctx, [2.5, 15.5, 2.5, 4.5, 7.5, 4.5, 9.5, 6.5, 17.5, 6.5, 17.5, 9]);
            line(ctx, [2.5, 15.5, 9.5, 15.5]);
            line(ctx, [11.5, 13.5, 17.5, 13.5]); line(ctx, [15, 11, 17.5, 13.5, 15, 16]);
            break;
        case "folder":
            line(ctx, [2.5, 15.5, 2.5, 4.5, 7.5, 4.5, 9.5, 6.5, 17.5, 6.5, 17.5, 15.5, 2.5, 15.5]);
            break;
        case "inbox":
            roundRect(ctx, 2.5, 3.5, 15, 13, 2);
            line(ctx, [2.5, 11, 6.5, 11, 7.5, 13, 12.5, 13, 13.5, 11, 17.5, 11]);
            break;
        case "drafts":
            line(ctx, [11, 3, 4.5, 3, 4.5, 17, 15.5, 17, 15.5, 7.5]);
            line(ctx, [9, 13.5, 9.5, 11, 16, 4.5, 18, 6.5, 11.5, 13, 9, 13.5]);
            break;
        case "sent":
            line(ctx, [2.5, 3.5, 17.5, 10, 2.5, 16.5, 4.8, 10, 2.5, 3.5]);
            line(ctx, [4.8, 10, 10.5, 10]);
            break;
        case "reply":
            line(ctx, [7.5, 4.5, 2.5, 9.5, 7.5, 14.5]);
            ctx.moveTo(2.8, 9.5); ctx.lineTo(11, 9.5);
            ctx.bezierCurveTo(15, 9.5, 17.5, 12, 17.5, 16);
            break;
        case "reply-all":
            line(ctx, [6, 4.5, 1.5, 9.5, 6, 14.5]);
            line(ctx, [10, 4.5, 5.5, 9.5, 10, 14.5]);
            ctx.moveTo(5.8, 9.5); ctx.lineTo(12, 9.5);
            ctx.bezierCurveTo(15.5, 9.5, 18, 12, 18, 16);
            break;
        case "forward":
            line(ctx, [12.5, 4.5, 17.5, 9.5, 12.5, 14.5]);
            ctx.moveTo(17.2, 9.5); ctx.lineTo(9, 9.5);
            ctx.bezierCurveTo(5, 9.5, 2.5, 12, 2.5, 16);
            break;
        case "flag":
            line(ctx, [4.5, 17.5, 4.5, 3]);
            line(ctx, [4.5, 3.5, 16, 3.5, 13, 7.5, 16, 11.5, 4.5, 11.5]);
            if (filled) { ctx.closePath(); ctx.fill(); }
            break;
        case "pin":
            line(ctx, [11.5, 2.5, 17.5, 8.5, 14.2, 9.2, 11.3, 13.7, 6.3, 8.7, 10.8, 5.8, 11.5, 2.5]);
            if (filled) ctx.fill();
            line(ctx, [8.5, 11.5, 3, 17]);
            break;
        case "star":
            for (let i = 0; i < 10; ++i) {
                const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 === 0 ? 7.5 : 3.3;
                if (i === 0) ctx.moveTo(10 + r * Math.cos(a), 10.5 + r * Math.sin(a));
                else ctx.lineTo(10 + r * Math.cos(a), 10.5 + r * Math.sin(a));
            }
            ctx.closePath();
            if (filled) ctx.fill();
            break;
        case "more":
            for (let i = 0; i < 3; ++i) {
                ctx.moveTo(5 + i * 5 + 1.2, 10);
                ctx.arc(5 + i * 5, 10, 1.2, 0, 2 * Math.PI);
            }
            ctx.fill();
            return;
        case "more-vertical":
            for (let i = 0; i < 3; ++i) {
                ctx.moveTo(11.2, 5 + i * 5);
                ctx.arc(10, 5 + i * 5, 1.2, 0, 2 * Math.PI);
            }
            ctx.fill();
            return;
        case "search":
            ctx.arc(8.5, 8.5, 5.5, 0, 2 * Math.PI);
            line(ctx, [12.5, 12.5, 17.5, 17.5]);
            break;
        case "settings":
            ctx.arc(10, 10, 2.6, 0, 2 * Math.PI);
            for (let i = 0; i < 8; ++i) {
                const a = i * Math.PI / 4;
                ctx.moveTo(10 + 5.4 * Math.cos(a - 0.22), 10 + 5.4 * Math.sin(a - 0.22));
                ctx.lineTo(10 + 7.2 * Math.cos(a - 0.12), 10 + 7.2 * Math.sin(a - 0.12));
                ctx.lineTo(10 + 7.2 * Math.cos(a + 0.12), 10 + 7.2 * Math.sin(a + 0.12));
                ctx.lineTo(10 + 5.4 * Math.cos(a + 0.22), 10 + 5.4 * Math.sin(a + 0.22));
                ctx.arc(10, 10, 5.4, a + 0.22, a + Math.PI / 4 - 0.22);
            }
            break;
        case "sync":
            ctx.arc(10, 10, 6.5, -Math.PI * 0.85, -Math.PI * 0.05);
            line(ctx, [16.3, 6, 16.7, 9.6, 13.2, 9]);
            ctx.moveTo(10 + 6.5 * Math.cos(Math.PI * 0.15), 10 + 6.5 * Math.sin(Math.PI * 0.15));
            ctx.arc(10, 10, 6.5, Math.PI * 0.15, Math.PI * 0.95);
            line(ctx, [3.7, 14, 3.3, 10.4, 6.8, 11]);
            break;
        case "help":
            ctx.arc(10, 10, 7.5, 0, 2 * Math.PI);
            ctx.moveTo(7.6, 7.8);
            ctx.bezierCurveTo(7.6, 4.8, 12.6, 4.8, 12.6, 7.8);
            ctx.bezierCurveTo(12.6, 9.6, 10, 9.8, 10, 11.6);
            ctx.moveTo(10.6, 14.2); ctx.arc(10, 14.2, 0.6, 0, 2 * Math.PI);
            break;
        case "info":
            ctx.arc(10, 10, 7.5, 0, 2 * Math.PI);
            line(ctx, [10, 9, 10, 14]);
            ctx.moveTo(10.6, 6.3); ctx.arc(10, 6.3, 0.6, 0, 2 * Math.PI);
            break;
        case "attach":
            ctx.moveTo(13.5, 7);
            ctx.lineTo(8, 12.5);
            ctx.bezierCurveTo(6.5, 14, 8.5, 16, 10, 14.5);
            ctx.lineTo(16, 8.5);
            ctx.bezierCurveTo(18.5, 6, 15, 2.5, 12.5, 5);
            ctx.lineTo(5.5, 12);
            ctx.bezierCurveTo(2, 15.5, 7, 20.5, 10.5, 17);
            ctx.lineTo(15, 12.5);
            break;
        case "image":
            roundRect(ctx, 2.5, 3.5, 15, 13, 2);
            ctx.moveTo(14, 7.5); ctx.arc(12.8, 7.5, 1.2, 0, 2 * Math.PI);
            line(ctx, [2.8, 14.5, 7.5, 10, 12, 14.5]);
            line(ctx, [11, 13.5, 13, 11.5, 17.2, 15.5]);
            break;
        case "chevron-down":
            line(ctx, [5, 7.5, 10, 12.5, 15, 7.5]);
            break;
        case "chevron-up":
            line(ctx, [5, 12.5, 10, 7.5, 15, 12.5]);
            break;
        case "chevron-right":
            line(ctx, [7.5, 5, 12.5, 10, 7.5, 15]);
            break;
        case "chevron-left":
            line(ctx, [12.5, 5, 7.5, 10, 12.5, 15]);
            break;
        case "filter":
            line(ctx, [3, 5.5, 17, 5.5]); line(ctx, [5.5, 10, 14.5, 10]); line(ctx, [8, 14.5, 12, 14.5]);
            break;
        case "hamburger":
            line(ctx, [3, 5.5, 17, 5.5]); line(ctx, [3, 10, 17, 10]); line(ctx, [3, 14.5, 17, 14.5]);
            break;
        case "add":
            line(ctx, [10, 3.5, 10, 16.5]); line(ctx, [3.5, 10, 16.5, 10]);
            break;
        case "close":
            line(ctx, [5, 5, 15, 15]); line(ctx, [15, 5, 5, 15]);
            break;
        case "check":
            line(ctx, [3.5, 10.5, 8, 15, 16.5, 5.5]);
            break;
        case "back":
            line(ctx, [16.5, 10, 3.5, 10]); line(ctx, [8.5, 5, 3.5, 10, 8.5, 15]);
            break;
        case "bullets":
            for (let i = 0; i < 3; ++i) {
                ctx.moveTo(4.7, 5 + i * 5); ctx.arc(4, 5 + i * 5, 0.7, 0, 2 * Math.PI);
                line(ctx, [8, 5 + i * 5, 17, 5 + i * 5]);
            }
            break;
        case "numbering":
            line(ctx, [3.5, 3.8, 4.5, 3.2, 4.5, 7]);
            line(ctx, [3.3, 9.3, 5.6, 9.3, 3.3, 12.8, 5.6, 12.8]);
            line(ctx, [8, 5, 17, 5]); line(ctx, [8, 10.5, 17, 10.5]); line(ctx, [8, 16, 17, 16]);
            break;
        case "link":
            ctx.moveTo(8.5, 11.5); ctx.lineTo(11.5, 8.5);
            ctx.moveTo(9.5, 6.2); ctx.lineTo(11.3, 4.4); ctx.bezierCurveTo(13, 2.7, 17.3, 7, 15.6, 8.7);
            ctx.lineTo(13.8, 10.5);
            ctx.moveTo(10.5, 13.8); ctx.lineTo(8.7, 15.6); ctx.bezierCurveTo(7, 17.3, 2.7, 13, 4.4, 11.3);
            ctx.lineTo(6.2, 9.5);
            break;
        case "bold":
        case "italic":
        case "underline": {
            ctx.font = (kind === "bold" ? "bold " : kind === "italic" ? "italic " : "") + "13px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(kind === "bold" ? "B" : kind === "italic" ? "I" : "U", 10, 9.5);
            if (kind === "underline")
                line(ctx, [5.5, 16.5, 14.5, 16.5]);
            break;
        }
        case "download":
            line(ctx, [10, 3, 10, 13]); line(ctx, [6, 9, 10, 13, 14, 9]);
            line(ctx, [4, 16.5, 16, 16.5]);
            break;
        case "open-external":
            line(ctx, [11, 3.5, 16.5, 3.5, 16.5, 9]); line(ctx, [16.5, 3.5, 9.5, 10.5]);
            line(ctx, [14.5, 12, 14.5, 16.5, 3.5, 16.5, 3.5, 5.5, 8, 5.5]);
            break;
        case "globe":
            ctx.arc(10, 10, 7.5, 0, 2 * Math.PI);
            ctx.moveTo(10, 2.5); ctx.bezierCurveTo(6, 6, 6, 14, 10, 17.5);
            ctx.moveTo(10, 2.5); ctx.bezierCurveTo(14, 6, 14, 14, 10, 17.5);
            line(ctx, [2.8, 10, 17.2, 10]);
            break;
        case "lock":
            roundRect(ctx, 4, 9, 12, 8.5, 2);
            ctx.moveTo(6.8, 9); ctx.lineTo(6.8, 6.5); ctx.bezierCurveTo(6.8, 2.2, 13.2, 2.2, 13.2, 6.5);
            ctx.lineTo(13.2, 9);
            break;
        case "warning":
            line(ctx, [10, 3, 17.5, 16.5, 2.5, 16.5, 10, 3]);
            line(ctx, [10, 8, 10, 11.5]);
            ctx.moveTo(10.6, 14); ctx.arc(10, 14, 0.6, 0, 2 * Math.PI);
            break;
        }
        ctx.stroke();
    }

    function paintCaption(ctx) {
        ctx.lineWidth = 1;
        const w = width, h = height, o = 0.5;
        ctx.beginPath();
        if (kind === "minimize") {
            ctx.moveTo(0, Math.round(h / 2) + o); ctx.lineTo(w, Math.round(h / 2) + o);
        } else if (kind === "maximize") {
            ctx.rect(o, o, w - 1, h - 1);
        } else if (kind === "restore") {
            ctx.rect(o, 2 + o, w - 3, h - 3);
            ctx.moveTo(2 + o, 2); ctx.lineTo(2 + o, o); ctx.lineTo(w - o, o); ctx.lineTo(w - o, h - 2 - o);
            ctx.lineTo(w - 2, h - 2 - o);
        } else {
            ctx.moveTo(0, 0); ctx.lineTo(w, h); ctx.moveTo(w, 0); ctx.lineTo(0, h);
        }
        ctx.stroke();
    }
}
