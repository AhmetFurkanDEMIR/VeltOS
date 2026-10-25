// Historical weather, as Windows 11 Weather shows it: the months of the
// year with their average high and low (from five years of records), the
// month's details and its precipitation.
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

    readonly property var months: backend.months
    property int selected: -1
    readonly property int shown: selected >= 0 ? selected : months.findIndex(m => m.current)
    readonly property var month: shown >= 0 && shown < months.length ? months[shown] : ({})
    readonly property real lowest: months.length ? Math.min(...months.map(m => m.low)) - 2 : 0
    readonly property real highest: months.length ? Math.max(...months.map(m => m.high)) + 2 : 1
    readonly property real wettest: months.length ? Math.max(1, ...months.map(m => m.precipValue)) : 1

    ColumnLayout {
        id: column
        x: 24
        y: 8
        width: page.width - 48
        spacing: 16

        Text {
            text: backend.text("history_title")
            color: Theme.text
            font.pixelSize: Theme.subtitleSize + 2
            font.weight: Font.DemiBold
        }
        Text {
            Layout.fillWidth: true
            text: backend.text("history_desc")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
            wrapMode: Text.WordWrap
        }

        Text {
            visible: page.months.length === 0
            text: backend.offline ? backend.text("offline") : backend.text("loading")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
        }

        // Temperature: one bar per month from the average low to the average high.
        Card {
            objectName: "temperatureMonths"
            visible: page.months.length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 300
            Row {
                id: bars
                anchors.fill: parent
                anchors.margins: 16
                readonly property real column: width / 12
                Repeater {
                    model: page.months
                    delegate: Item {
                        id: monthItem
                        required property var modelData
                        required property int index
                        readonly property bool chosen: index === page.shown
                        width: bars.column
                        height: bars.height
                        readonly property real barTop: 24
                        readonly property real barBottom: height - 30
                        function yOf(value) {
                            return barBottom - (value - page.lowest) / Math.max(1, page.highest - page.lowest) * (barBottom - barTop);
                        }
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 2
                            radius: Theme.radius
                            color: monthItem.chosen ? Theme.accentSoft : (monthHover.hovered ? Theme.navHover : "transparent")
                        }
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: Math.min(14, parent.width * 0.3)
                            y: monthItem.yOf(monthItem.modelData.high)
                            height: Math.max(4, monthItem.yOf(monthItem.modelData.low) - y)
                            radius: width / 2
                            gradient: Gradient {
                                GradientStop { position: 0; color: "#F08C1A" }
                                GradientStop { position: 1; color: "#3B9BF0" }
                            }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: monthItem.yOf(monthItem.modelData.high) - height - 4
                            text: monthItem.modelData.highText
                            color: Theme.text
                            font.pixelSize: Theme.captionSize
                            font.weight: Font.DemiBold
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: monthItem.yOf(monthItem.modelData.low) + 4
                            text: monthItem.modelData.lowText
                            color: Theme.subtext
                            font.pixelSize: Theme.captionSize
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 6
                            text: monthItem.modelData.name
                            color: monthItem.chosen ? Theme.accent : Theme.subtext
                            font.pixelSize: Theme.captionSize + 1
                            font.weight: monthItem.chosen ? Font.DemiBold : Font.Normal
                        }
                        HoverHandler { id: monthHover }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: page.selected = monthItem.index
                        }
                    }
                }
            }
        }

        // The chosen month.
        GridLayout {
            visible: page.months.length > 0
            Layout.fillWidth: true
            columns: Math.max(2, Math.min(6, Math.floor(column.width / 180)))
            columnSpacing: 12
            rowSpacing: 12
            Repeater {
                model: [
                    [backend.text("avg_high"), page.month.highText || ""],
                    [backend.text("avg_low"), page.month.lowText || ""],
                    [backend.text("record_high"), page.month.highest || ""],
                    [backend.text("record_low"), page.month.lowest || ""],
                    [backend.text("avg_precip"), page.month.precip || ""],
                    [backend.text("rainy_days"), page.month.rainyDays || ""]
                ]
                delegate: Card {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 84
                    Column {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 6
                        Text { text: modelData[0]; color: Theme.subtext; font.pixelSize: Theme.captionSize + 1; width: parent.width; elide: Text.ElideRight }
                        Text { text: modelData[1]; color: Theme.text; font.pixelSize: Theme.headingSize; font.weight: Font.DemiBold }
                    }
                }
            }
        }

        // Precipitation: the average month's total.
        Card {
            visible: page.months.length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 200
            Text {
                x: 16
                y: 12
                text: backend.text("avg_precip")
                color: Theme.subtext
                font.pixelSize: Theme.captionSize + 1
                font.weight: Font.DemiBold
            }
            Row {
                id: rain
                anchors.fill: parent
                anchors.margins: 16
                anchors.topMargin: 36
                readonly property real column: width / 12
                Repeater {
                    model: page.months
                    delegate: Item {
                        required property var modelData
                        required property int index
                        width: rain.column
                        height: rain.height
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 24
                            width: Math.min(18, parent.width * 0.4)
                            height: Math.max(2, (parent.height - 48) * modelData.precipValue / page.wettest)
                            radius: 3
                            color: index === page.shown ? Theme.accent : Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.45)
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            text: modelData.name
                            color: Theme.subtext
                            font.pixelSize: Theme.captionSize
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: backend.text("attribution")
            color: Theme.faint
            font.pixelSize: Theme.captionSize
        }
    }
}
