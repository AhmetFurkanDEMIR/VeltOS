/*
    Windows 11 calendar flyout: the full date as a heading, then the month
    with up/down arrows, two-letter weekday names and the days of six
    weeks; today in a filled accent circle, a clicked day ringed. The mouse
    wheel changes the month. No week numbers, no Days/Months/Years tabs.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: calendar

    property date today: new Date()
    // First day of the month that is shown.
    property date month: new Date(today.getFullYear(), today.getMonth(), 1)
    property date selected: today

    readonly property int firstDay: Qt.locale().firstDayOfWeek  // 0 = Sunday ... 6
    readonly property int offset: (month.getDay() - firstDay + 7) % 7

    function sameDay(a, b) {
        return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
            && a.getDate() === b.getDate();
    }
    function step(months) {
        month = new Date(month.getFullYear(), month.getMonth() + months, 1);
    }
    function reset() {
        month = new Date(today.getFullYear(), today.getMonth(), 1);
        selected = today;
    }

    spacing: Kirigami.Units.smallSpacing

    PlasmaComponents3.Label {
        Layout.fillWidth: true
        Layout.bottomMargin: Kirigami.Units.largeSpacing
        text: Qt.locale().toString(calendar.today, "dddd, d MMMM")
        font.weight: Font.DemiBold
        elide: Text.ElideRight
    }

    RowLayout {
        Layout.fillWidth: true
        PlasmaComponents3.Label {
            Layout.fillWidth: true
            text: Qt.locale().standaloneMonthName(calendar.month.getMonth(), Locale.LongFormat)
                  + " " + calendar.month.getFullYear()
            font.weight: Font.DemiBold
        }
        PlasmaComponents3.ToolButton {
            icon.name: "go-up-symbolic"
            display: PlasmaComponents3.AbstractButton.IconOnly
            text: i18n("Previous month")
            onClicked: calendar.step(-1)
        }
        PlasmaComponents3.ToolButton {
            icon.name: "go-down-symbolic"
            display: PlasmaComponents3.AbstractButton.IconOnly
            text: i18n("Next month")
            onClicked: calendar.step(1)
        }
    }

    GridLayout {
        id: grid
        Layout.fillWidth: true
        columns: 7
        rowSpacing: 2
        columnSpacing: 2

        Repeater {
            model: 7
            PlasmaComponents3.Label {
                required property int index
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: Qt.locale().dayName((calendar.firstDay + index) % 7, Locale.ShortFormat).slice(0, 2)
                font: Kirigami.Theme.smallFont
                opacity: 0.8
            }
        }

        Repeater {
            model: 42
            MouseArea {
                id: cell
                required property int index
                readonly property date day: new Date(calendar.month.getFullYear(), calendar.month.getMonth(),
                                                      index - calendar.offset + 1)
                readonly property bool inMonth: day.getMonth() === calendar.month.getMonth()
                readonly property bool isToday: calendar.sameDay(day, calendar.today)
                readonly property bool isSelected: calendar.sameDay(day, calendar.selected)

                Layout.fillWidth: true
                Layout.preferredHeight: Math.round(Kirigami.Units.gridUnit * 2)
                hoverEnabled: true
                onClicked: calendar.selected = day
                Accessible.name: Qt.formatDate(day, Locale.LongFormat)
                Accessible.role: Accessible.Button

                Rectangle {
                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height) - 2
                    height: width
                    radius: width / 2
                    color: cell.isToday ? Kirigami.Theme.highlightColor
                         : Qt.alpha(Kirigami.Theme.textColor, cell.pressed ? 0.05 : (cell.containsMouse ? 0.08 : 0))
                    border.width: cell.isSelected && !cell.isToday ? 1.5 : 0
                    border.color: Kirigami.Theme.highlightColor
                }
                PlasmaComponents3.Label {
                    anchors.centerIn: parent
                    text: cell.day.getDate()
                    color: cell.isToday ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                    opacity: cell.inMonth || cell.isToday ? 1 : 0.45
                }
            }
        }
    }

    WheelHandler {
        target: null
        onWheel: event => calendar.step(event.angleDelta.y > 0 ? -1 : 1)
    }
}
