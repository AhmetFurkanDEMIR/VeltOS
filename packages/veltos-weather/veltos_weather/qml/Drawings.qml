// Small drawings of the detail cards, as inline components: the sun's
// path between sunrise and sunset, the moon's phase, a compass with the
// wind and a coloured scale with a marker (UV index, air quality).
import QtQuick
import "."

QtObject {
    component SunArc: Canvas {
        id: arc
        property real position: -1       // 0..1 between sunrise and sunset, -1 at night
        onPositionChanged: requestPaint()
        onWidthChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const cx = width / 2, base = height - 4, r = Math.min(width / 2 - 8, height - 10);
            ctx.setLineDash([4, 4]);
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = Theme.faint;
            ctx.beginPath();
            ctx.arc(cx, base, r, Math.PI, 2 * Math.PI);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.strokeStyle = Theme.track;
            ctx.beginPath();
            ctx.moveTo(4, base);
            ctx.lineTo(width - 4, base);
            ctx.stroke();
            if (position >= 0) {
                const angle = Math.PI + position * Math.PI;
                ctx.strokeStyle = "#FFB020";
                ctx.lineWidth = 2.5;
                ctx.beginPath();
                ctx.arc(cx, base, r, Math.PI, angle);
                ctx.stroke();
                const sx = cx + r * Math.cos(angle), sy = base + r * Math.sin(angle);
                const glow = ctx.createRadialGradient(sx, sy, 2, sx, sy, 14);
                glow.addColorStop(0, "rgba(255, 196, 64, 0.55)");
                glow.addColorStop(1, "rgba(255, 196, 64, 0)");
                ctx.fillStyle = glow;
                ctx.beginPath();
                ctx.arc(sx, sy, 14, 0, 2 * Math.PI);
                ctx.fill();
                ctx.fillStyle = "#FFB020";
                ctx.beginPath();
                ctx.arc(sx, sy, 7, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }

    component MoonDisc: Canvas {
        // phase: 0 new, 0.25 first quarter, 0.5 full, 0.75 last quarter.
        property real phase: 0
        onPhaseChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const r = Math.min(width, height) / 2 - 2, cx = width / 2, cy = height / 2;
            ctx.fillStyle = Theme.dark ? "#3A3E50" : "#D9DEE8";
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, 2 * Math.PI);
            ctx.fill();
            // The lit part: a half disc on the lit side and an ellipse that
            // grows (gibbous) or cuts it (crescent).
            const waxing = phase < 0.5;
            const k = Math.cos(phase * 2 * Math.PI);     // 1 new .. -1 full
            const lit = "#F6E7B5", unlit = Theme.dark ? "#3A3E50" : "#D9DEE8";
            ctx.fillStyle = lit;
            ctx.beginPath();
            ctx.moveTo(cx, cy - r);
            ctx.arc(cx, cy, r, -Math.PI / 2, Math.PI / 2, !waxing);    // the lit half (right while waxing)
            ctx.closePath();
            ctx.fill();
            if (Math.abs(k) > 0.01) {
                ctx.fillStyle = k > 0 ? unlit : lit;                   // crescent cuts, gibbous adds
                ctx.beginPath();
                ctx.ellipse(cx - Math.abs(k) * r, cy - r, 2 * Math.abs(k) * r, 2 * r);
                ctx.fill();
            }
        }
    }

    component Compass: Canvas {
        property real angle: 0            // the direction the wind comes from, degrees
        property var names: ["N", "E", "S", "W"]
        onAngleChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const r = Math.min(width, height) / 2 - 12, cx = width / 2, cy = height / 2;
            ctx.strokeStyle = Theme.track;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, 2 * Math.PI);
            ctx.stroke();
            for (let i = 0; i < 36; ++i) {
                const a = i * Math.PI / 18;
                const inner = i % 9 === 0 ? r - 8 : r - 4;
                ctx.beginPath();
                ctx.moveTo(cx + inner * Math.sin(a), cy - inner * Math.cos(a));
                ctx.lineTo(cx + r * Math.sin(a), cy - r * Math.cos(a));
                ctx.strokeStyle = Theme.faint;
                ctx.lineWidth = 1;
                ctx.stroke();
            }
            ctx.fillStyle = Theme.subtext;
            ctx.font = Math.round(10 * Theme.textScale) + "px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            const labels = [[0, -1], [1, 0], [0, 1], [-1, 0]];
            for (let i = 0; i < 4; ++i)
                ctx.fillText(names[i], cx + labels[i][0] * (r + 8), cy + labels[i][1] * (r + 8));
            // The arrow points where the wind blows to.
            const a = (angle + 180) * Math.PI / 180;
            const tipX = cx + (r - 12) * Math.sin(a), tipY = cy - (r - 12) * Math.cos(a);
            const tailX = cx - (r - 12) * Math.sin(a), tailY = cy + (r - 12) * Math.cos(a);
            ctx.strokeStyle = Theme.accent;
            ctx.lineWidth = 3;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(tailX, tailY);
            ctx.lineTo(tipX, tipY);
            ctx.stroke();
            ctx.fillStyle = Theme.accent;
            ctx.beginPath();
            const side = 7, back = 12;
            ctx.moveTo(tipX + 4 * Math.sin(a), tipY - 4 * Math.cos(a));
            ctx.lineTo(tipX - back * Math.sin(a) + side * Math.cos(a), tipY + back * Math.cos(a) + side * Math.sin(a));
            ctx.lineTo(tipX - back * Math.sin(a) - side * Math.cos(a), tipY + back * Math.cos(a) - side * Math.sin(a));
            ctx.closePath();
            ctx.fill();
            ctx.beginPath();
            ctx.arc(tailX, tailY, 4, 0, 2 * Math.PI);
            ctx.fill();
        }
    }

    component Scale: Item {
        // A coloured scale with a marker at `value` (0..1).
        property real value: 0
        property var stops: ["#3FB950", "#9ACD32", "#F2C200", "#F08C1A", "#E5484D", "#8E3BB8"]
        implicitHeight: 14
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            height: 6
            radius: 3
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: stops[0] }
                GradientStop { position: 0.2; color: stops[1] }
                GradientStop { position: 0.4; color: stops[2] }
                GradientStop { position: 0.6; color: stops[3] }
                GradientStop { position: 0.8; color: stops[4] }
                GradientStop { position: 1.0; color: stops[5] }
            }
        }
        Rectangle {
            width: 14
            height: 14
            radius: 7
            color: Theme.card
            border.width: 3
            border.color: Theme.text
            x: Math.max(0, Math.min(parent.width - width, parent.value * parent.width - width / 2))
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
