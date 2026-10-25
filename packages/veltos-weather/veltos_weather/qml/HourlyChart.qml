// The hourly chart of Windows 11 Weather: 24 hours side by side, a smooth
// line (bars for the chance of precipitation) with the value over each
// hour, the weather pictures above (Overview), the chance of precipitation
// or the wind's direction under it and the hours at the bottom. Scrolls
// sideways when the window is narrow.
import QtQuick
import "."

Item {
    id: view
    property var chart: ({})
    readonly property int count: chart.values ? chart.values.length : 0
    readonly property real minStep: 58
    readonly property bool bars: chart.kind === "precipitation"
    implicitHeight: 250

    onChartChanged: canvas.requestPaint()

    Flickable {
        id: flick
        anchors.fill: parent
        contentWidth: Math.max(width, view.count * view.minStep)
        contentHeight: height
        flickableDirection: Flickable.HorizontalFlick
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        onWidthChanged: canvas.requestPaint()

        Item {
            id: plot
            width: flick.contentWidth
            height: flick.height
            readonly property real column: width / Math.max(1, view.count)
            readonly property real plotTop: (view.chart.showIcons ? 44 : 8) + 26
            readonly property real plotBottom: height - 62
            function px(index) { return (index + 0.5) * column; }
            function py(value) {
                const low = view.chart.min, high = view.chart.max;
                const share = high > low ? (value - low) / (high - low) : 0.5;
                return plotBottom - Math.max(0, Math.min(1, share)) * (plotBottom - plotTop);
            }

            Canvas {
                id: canvas
                anchors.fill: parent
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    const values = view.chart.values || [];
                    if (values.length === 0)
                        return;
                    const accent = Theme.accent;
                    if (view.bars) {
                        for (let i = 0; i < values.length; ++i) {
                            const x = plot.px(i), y = plot.py(values[i]);
                            const w = Math.min(18, plot.column * 0.42);
                            ctx.fillStyle = Qt.rgba(accent.r, accent.g, accent.b, 0.85);
                            const h = Math.max(2, plot.plotBottom - y);
                            ctx.beginPath();
                            ctx.roundedRect(x - w / 2, plot.plotBottom - h, w, h, 3, 3);
                            ctx.fill();
                        }
                        return;
                    }
                    // A smooth line through the hours (midpoint curves).
                    ctx.beginPath();
                    ctx.moveTo(plot.px(0), plot.py(values[0]));
                    for (let i = 1; i < values.length; ++i) {
                        const mx = (plot.px(i - 1) + plot.px(i)) / 2;
                        ctx.bezierCurveTo(mx, plot.py(values[i - 1]), mx, plot.py(values[i]), plot.px(i), plot.py(values[i]));
                    }
                    ctx.lineWidth = 2.5;
                    ctx.strokeStyle = accent;
                    ctx.stroke();
                    ctx.lineTo(plot.px(values.length - 1), plot.plotBottom);
                    ctx.lineTo(plot.px(0), plot.plotBottom);
                    ctx.closePath();
                    const fill = ctx.createLinearGradient(0, plot.plotTop, 0, plot.plotBottom);
                    fill.addColorStop(0, Qt.rgba(accent.r, accent.g, accent.b, Theme.dark ? 0.32 : 0.22));
                    fill.addColorStop(1, Qt.rgba(accent.r, accent.g, accent.b, 0.0));
                    ctx.fillStyle = fill;
                    ctx.fill();
                    for (let i = 0; i < values.length; ++i) {
                        ctx.beginPath();
                        ctx.arc(plot.px(i), plot.py(values[i]), i === 0 ? 4.5 : 3, 0, 2 * Math.PI);
                        ctx.fillStyle = i === 0 ? accent : Theme.card;
                        ctx.fill();
                        ctx.lineWidth = 2;
                        ctx.strokeStyle = accent;
                        ctx.stroke();
                    }
                }
            }

            Repeater {
                model: view.count
                delegate: Item {
                    id: hour
                    required property int index
                    x: index * plot.column
                    width: plot.column
                    height: plot.height
                    readonly property real value: view.chart.values[index]

                    WeatherIcon {
                        visible: !!view.chart.showIcons
                        name: view.chart.icons ? view.chart.icons[hour.index] : ""
                        width: 34
                        height: 34
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: 6
                    }
                    Text {
                        text: view.chart.texts ? view.chart.texts[hour.index] : ""
                        color: hour.index === 0 ? Theme.text : Theme.subtext
                        font.pixelSize: Theme.captionSize + 1
                        font.weight: hour.index === 0 ? Font.DemiBold : Font.Normal
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: plot.py(hour.value) - height - 8
                    }
                    // Under the line: the chance of precipitation, or where the wind blows.
                    Row {
                        visible: view.chart.kind === "overview" && !!view.chart.extras
                                 && view.chart.extras[hour.index].chance !== ""
                        spacing: 2
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: plot.plotBottom + 10
                        Glyph { name: "drop"; tint: "#3B9BF0"; width: 12; height: 12; anchors.verticalCenter: parent.verticalCenter }
                        Text {
                            text: view.chart.extras ? view.chart.extras[hour.index].chance : ""
                            color: Theme.subtext
                            font.pixelSize: Theme.captionSize
                        }
                    }
                    Glyph {
                        visible: !!view.chart.arrows
                        name: "arrow"
                        tint: Theme.subtext
                        width: 16
                        height: 16
                        rotation: view.chart.extras ? view.chart.extras[hour.index].angle : 0
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: plot.plotBottom + 8
                    }
                    Text {
                        text: view.chart.labels ? view.chart.labels[hour.index] : ""
                        color: hour.index === 0 && view.chart.labels[0] !== undefined ? Theme.text : Theme.subtext
                        font.pixelSize: Theme.captionSize
                        font.weight: hour.index === 0 ? Font.DemiBold : Font.Normal
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 6
                    }
                }
            }
        }
    }
}
