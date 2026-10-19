/*
    VeltOS Clock: the Windows 11 taskbar clock. Time above the date, both in
    the same small size and right-aligned, in the formats of the user's
    region (with a four-digit year, as Windows shows it). Clicking it opens
    the calendar.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property date now: new Date()
    readonly property string timeText: Qt.formatTime(now, Qt.locale().timeFormat(Locale.ShortFormat))
    readonly property string dateText: Qt.formatDate(now, fullYear(Qt.locale().dateFormat(Locale.ShortFormat)))

    function fullYear(format) {
        return format.indexOf("yyyy") >= 0 ? format : format.replace("yy", "yyyy");
    }

    // Wake up at each new minute only.
    Timer {
        id: tick
        running: true
        triggeredOnStart: true
        onTriggered: {
            root.now = new Date();
            interval = 60000 - root.now.getSeconds() * 1000 - root.now.getMilliseconds() + 20;
            restart();
        }
    }

    preferredRepresentation: compactRepresentation
    toolTipMainText: Qt.formatDate(now, Qt.locale().dateFormat(Locale.LongFormat))
    toolTipSubText: ""
    onExpandedChanged: if (expanded) tick.triggered()

    compactRepresentation: MouseArea {
        id: button

        Layout.minimumWidth: lines.implicitWidth + Kirigami.Units.largeSpacing * 2
        Layout.preferredWidth: Layout.minimumWidth
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded
        Accessible.role: Accessible.Button
        Accessible.name: root.timeText + ", " + root.dateText

        Rectangle {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            radius: Kirigami.Units.cornerRadius
            color: Kirigami.Theme.textColor
            opacity: root.expanded ? 0.12 : (button.containsMouse ? 0.07 : 0)
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        ColumnLayout {
            id: lines
            anchors.right: parent.right
            anchors.rightMargin: Kirigami.Units.largeSpacing
            anchors.verticalCenter: parent.verticalCenter
            spacing: 0

            PlasmaComponents3.Label {
                Layout.alignment: Qt.AlignRight
                text: root.timeText
                font.pointSize: 9
            }
            PlasmaComponents3.Label {
                Layout.alignment: Qt.AlignRight
                text: root.dateText
                font.pointSize: 9
            }
        }
    }

    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        Layout.preferredHeight: Kirigami.Units.gridUnit * 21
        spacing: Kirigami.Units.largeSpacing

        PlasmaComponents3.Label {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            text: Qt.formatDate(root.now, Qt.locale().dateFormat(Locale.LongFormat))
            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.15
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        PlasmaCalendar.MonthView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            today: root.now
            firstDayOfWeek: Qt.locale().firstDayOfWeek
            showWeekNumbers: false
            borderOpacity: 0
        }
    }
}
