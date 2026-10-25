// The Forecast page of Windows 11 Weather: the current weather over the
// sky of its condition, the 10-day forecast, the hourly chart of the
// chosen day and the weather details.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: page
    contentWidth: width
    contentHeight: column.implicitHeight + 48
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}

    readonly property var current: backend.current
    readonly property var details: backend.details
    readonly property int detailColumns: Math.max(1, Math.min(4, Math.floor((width - 48) / 280)))

    ColumnLayout {
        id: column
        x: 24
        y: 8
        width: page.width - 48
        spacing: 20

        // --- the current weather ------------------------------------------------------------------
        Rectangle {
            id: hero
            objectName: "hero"
            Layout.fillWidth: true
            Layout.preferredHeight: heroContent.implicitHeight + 48
            radius: Theme.bigRadius
            gradient: Gradient {
                GradientStop { position: 0; color: page.current.skyTop || "#4A7FC8" }
                GradientStop { position: 1; color: page.current.skyBottom || "#9DBFE6" }
            }
            Behavior on Layout.preferredHeight { NumberAnimation { duration: 150 } }

            // Soft light from the top right, as on a photo of the sky.
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "transparent" }
                    GradientStop { position: 1; color: Qt.rgba(1, 1, 1, page.current.isDay ? 0.16 : 0.05) }
                }
            }

            ColumnLayout {
                id: heroContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 24
                spacing: 14

                RowLayout {
                    spacing: 6
                    Text {
                        text: backend.text("current_weather")
                        color: "#FFFFFF"
                        font.pixelSize: Theme.bodySize
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: page.current.time || ""
                        color: Qt.rgba(1, 1, 1, 0.8)
                        font.pixelSize: Theme.bodySize
                    }
                }

                RowLayout {
                    spacing: 18
                    WeatherIcon {
                        name: page.current.icon || ""
                        Layout.preferredWidth: 112
                        Layout.preferredHeight: 112
                    }
                    Row {
                        Layout.alignment: Qt.AlignVCenter
                        Text {
                            objectName: "temperature"
                            text: page.current.temperature || "--"
                            color: "#FFFFFF"
                            font.pixelSize: Theme.heroSize
                            font.weight: Font.Light
                        }
                        Text {
                            text: page.current.unit || ""
                            color: "#FFFFFF"
                            font.pixelSize: Theme.headingSize + 4
                            topPadding: 14
                        }
                    }
                    ColumnLayout {
                        Layout.alignment: Qt.AlignVCenter
                        Layout.leftMargin: 8
                        spacing: 4
                        Text {
                            text: page.current.condition || ""
                            color: "#FFFFFF"
                            font.pixelSize: Theme.headingSize
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: backend.text("feels_like") + " " + (page.current.feels || "--")
                            color: Qt.rgba(1, 1, 1, 0.85)
                            font.pixelSize: Theme.bodySize
                        }
                    }
                    Item { Layout.fillWidth: true }
                }

                Text {
                    Layout.fillWidth: true
                    text: page.current.summary || ""
                    color: "#FFFFFF"
                    font.pixelSize: Theme.subtitleSize
                    wrapMode: Text.WordWrap
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 28
                    Repeater {
                        model: page.current.details || []
                        delegate: Column {
                            id: chip
                            required property var modelData
                            spacing: 3
                            Text {
                                text: chip.modelData.label
                                color: Qt.rgba(1, 1, 1, 0.82)
                                font.pixelSize: Theme.captionSize
                            }
                            Row {
                                spacing: 6
                                Rectangle {
                                    visible: chip.modelData.colour !== ""
                                    width: 10
                                    height: 10
                                    radius: 5
                                    color: chip.modelData.colour || "transparent"
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Glyph {
                                    visible: chip.modelData.key === "wind"
                                    name: "arrow"
                                    tint: "#FFFFFF"
                                    width: 14
                                    height: 14
                                    rotation: chip.modelData.angle || 0
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: chip.modelData.value
                                    color: "#FFFFFF"
                                    font.pixelSize: Theme.subtitleSize
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                    }
                }
            }
        }

        // --- 10-day forecast -------------------------------------------------------------------------
        Text {
            text: backend.text("daily_forecast")
            color: Theme.text
            font.pixelSize: Theme.subtitleSize + 2
            font.weight: Font.DemiBold
        }
        ListView {
            id: dayList
            objectName: "days"
            Layout.fillWidth: true
            Layout.preferredHeight: 168
            orientation: ListView.Horizontal
            spacing: 8
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: backend.days
            delegate: Rectangle {
                id: dayCard
                required property var modelData
                required property int index
                width: Math.max(112, (dayList.width - 9 * 8) / 10)
                height: dayList.height
                radius: Theme.radius
                color: modelData.selected ? Theme.accentSoft : (dayHover.hovered ? Theme.cardHover : Theme.card)
                border.width: modelData.selected ? 2 : 1
                border.color: modelData.selected ? Theme.accent : Theme.cardBorder
                Accessible.role: Accessible.Button
                Accessible.name: modelData.name + " " + modelData.condition + " " + modelData.high + " " + modelData.low

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 4
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: dayCard.modelData.name + (dayCard.index === 0 ? "" : " " + dayCard.modelData.date)
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        font.weight: Font.DemiBold
                    }
                    WeatherIcon {
                        Layout.alignment: Qt.AlignHCenter
                        name: dayCard.modelData.icon
                        Layout.preferredWidth: 52
                        Layout.preferredHeight: 52
                    }
                    Row {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8
                        Text {
                            text: dayCard.modelData.high
                            color: Theme.text
                            font.pixelSize: Theme.subtitleSize
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: dayCard.modelData.low
                            color: Theme.subtext
                            font.pixelSize: Theme.subtitleSize
                        }
                    }
                    Row {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 3
                        visible: dayCard.modelData.chance !== ""
                        Glyph { name: "drop"; tint: "#3B9BF0"; width: 12; height: 12; anchors.verticalCenter: parent.verticalCenter }
                        Text {
                            text: dayCard.modelData.chance
                            color: Theme.subtext
                            font.pixelSize: Theme.captionSize
                        }
                    }
                }
                HoverHandler { id: dayHover }
                ToolTip.visible: dayHover.hovered
                ToolTip.delay: 600
                ToolTip.text: modelData.condition
                TapHandler {
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: backend.selectDay(dayCard.index)
                }
            }
        }

        // --- hourly chart ------------------------------------------------------------------------------
        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: chartColumn.implicitHeight + 32
            ColumnLayout {
                id: chartColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                spacing: 8
                Flickable {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    contentWidth: tabs.implicitWidth
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    flickableDirection: Flickable.HorizontalFlick
                    Row {
                        id: tabs
                        spacing: 4
                        Repeater {
                            model: backend.chartKinds
                            delegate: Rectangle {
                                id: tab
                                required property var modelData
                                readonly property bool active: backend.chartKind === modelData.key
                                width: tabText.implicitWidth + 24
                                height: 32
                                radius: 16
                                color: active ? Theme.accent : (tabHover.hovered ? Theme.navHover : "transparent")
                                border.width: active ? 0 : 1
                                border.color: Theme.cardBorder
                                Text {
                                    id: tabText
                                    anchors.centerIn: parent
                                    text: tab.modelData.label
                                    color: tab.active ? "#FFFFFF" : Theme.text
                                    font.pixelSize: Theme.captionSize + 1
                                }
                                HoverHandler { id: tabHover }
                                TapHandler {
                                    gesturePolicy: TapHandler.ReleaseWithinBounds
                                    onTapped: backend.setChartKind(tab.modelData.key)
                                }
                            }
                        }
                    }
                }
                HourlyChart {
                    objectName: "hourlyChart"
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    chart: backend.chart
                }
            }
        }

        // --- weather details ---------------------------------------------------------------------------
        Text {
            text: backend.text("weather_details")
            color: Theme.text
            font.pixelSize: Theme.subtitleSize + 2
            font.weight: Font.DemiBold
        }
        GridLayout {
            id: detailGrid
            objectName: "details"
            Layout.fillWidth: true
            columns: page.detailColumns
            columnSpacing: 12
            rowSpacing: 12
            visible: !!page.details.sunrise

            DetailCard {
                title: backend.text("sun")
                glyph: "sunrise"
                Drawings.SunArc {
                    id: sunArc
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 74
                    position: page.details.sunPosition !== undefined ? page.details.sunPosition : -1
                }
                RowLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: sunArc.bottom
                    anchors.topMargin: 8
                    ColumnLayout {
                        spacing: 0
                        Text { text: backend.text("sunrise"); color: Theme.subtext; font.pixelSize: Theme.captionSize }
                        Text { text: page.details.sunrise || ""; color: Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold }
                    }
                    Item { Layout.fillWidth: true }
                    ColumnLayout {
                        spacing: 0
                        Text { Layout.alignment: Qt.AlignRight; text: backend.text("sunset"); color: Theme.subtext; font.pixelSize: Theme.captionSize }
                        Text { Layout.alignment: Qt.AlignRight; text: page.details.sunset || ""; color: Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold }
                    }
                }
                Text {
                    anchors.bottom: parent.bottom
                    text: page.details.daylight || ""
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                }
            }

            DetailCard {
                title: backend.text("moon")
                glyph: "moon"
                Drawings.MoonDisc {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 84
                    height: 84
                    phase: page.details.moonPhase || 0
                }
                Column {
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 2
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: page.details.moonName || ""; color: Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: page.details.moonLight || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize }
                }
            }

            DetailCard {
                title: backend.text("wind")
                glyph: "wind"
                Drawings.Compass {
                    id: compass
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    width: 120
                    height: 120
                    angle: page.details.windAngle || 0
                    names: backend.compassNames
                }
                Column {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4
                    Text { text: page.details.windSpeed || ""; color: Theme.text; font.pixelSize: Theme.headingSize + 2; font.weight: Font.DemiBold }
                    Text { text: page.details.windFrom || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1 }
                    Text { text: page.details.windGusts || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1 }
                }
            }

            DetailCard {
                title: backend.text("humidity")
                glyph: "humidity"
                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 10
                    Text { text: page.details.humidity || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                    Rectangle {
                        width: parent.width
                        height: 6
                        radius: 3
                        color: Theme.track
                        Rectangle {
                            width: parent.width * Math.max(0, Math.min(1, (page.details.humidityValue || 0) / 100))
                            height: parent.height
                            radius: 3
                            color: "#3B9BF0"
                        }
                    }
                    Text { text: page.details.humidityText || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1; width: parent.width; wrapMode: Text.WordWrap }
                }
                Text {
                    anchors.bottom: parent.bottom
                    text: backend.text("dew_point") + " " + (page.details.dewPoint || "")
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize + 1
                }
            }

            DetailCard {
                title: backend.text("uv_index")
                glyph: "uv"
                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 8
                    Row {
                        spacing: 10
                        Text { id: uvValue; text: page.details.uv || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                        Text { text: page.details.uvBand || ""; color: page.details.uvColour || Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold; anchors.baseline: uvValue.baseline }
                    }
                    Drawings.Scale {
                        width: parent.width
                        value: Math.min(1, (page.details.uvValue || 0) / 11)
                        stops: ["#3FB950", "#F2C200", "#F08C1A", "#E5484D", "#E5484D", "#8E3BB8"]
                    }
                    Text { text: page.details.uvText || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1; width: parent.width; wrapMode: Text.WordWrap }
                }
            }

            DetailCard {
                title: backend.text("air_quality")
                glyph: "air"
                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 8
                    Row {
                        spacing: 10
                        Text { id: aqiValue; text: page.details.aqi || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                        Text { text: page.details.aqiBand || ""; color: page.details.aqiColour || Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold; anchors.baseline: aqiValue.baseline }
                    }
                    Drawings.Scale {
                        width: parent.width
                        value: page.details.aqiFraction || 0
                    }
                    Text { text: page.details.aqiText || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1; width: parent.width; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight }
                }
                Flow {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    spacing: 10
                    Repeater {
                        model: (page.details.pollutants || []).slice(0, 4)
                        delegate: Text {
                            required property var modelData
                            text: modelData.label + " " + modelData.value
                            color: Theme.faint
                            font.pixelSize: Theme.captionSize
                        }
                    }
                }
            }

            DetailCard {
                title: backend.text("visibility")
                glyph: "visibility"
                Column {
                    spacing: 8
                    Text { text: page.details.visibility || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                    Text { text: page.details.visibilityText || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1 }
                }
            }

            DetailCard {
                title: backend.text("pressure")
                glyph: "pressure"
                Column {
                    spacing: 8
                    Text { text: page.details.pressure || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                    Text { text: page.details.pressureTrend || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1 }
                }
            }

            DetailCard {
                title: backend.text("feels_like")
                glyph: "feels"
                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 8
                    Text { text: page.details.feels || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                    Text { text: page.details.feelsText || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1; width: parent.width; wrapMode: Text.WordWrap }
                }
            }

            DetailCard {
                title: backend.text("precipitation")
                glyph: "precipitation"
                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: 8
                    Text { text: page.details.precip || ""; color: Theme.text; font.pixelSize: Theme.titleSize; font.weight: Font.DemiBold }
                    Text { text: page.details.precipText || ""; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1; width: parent.width; wrapMode: Text.WordWrap }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: 4
            text: backend.text("attribution") + (backend.updatedText !== "" ? "  ·  " + backend.updatedText : "")
            color: Theme.faint
            font.pixelSize: Theme.captionSize
            wrapMode: Text.WordWrap
        }
    }
}
