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
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    // Windows 11 flyouts float above the taskbar with all corners rounded.
    // Plasma does that for panel popups only while the panel itself floats
    // (its Panel.qml sets ContainmentPrefersFloatingApplets); the VeltOS
    // taskbar does not float, so the hint is kept set here. Panel.qml
    // clears it whenever its own state changes, hence the Connections.
    function floatPopups() {
        const c = Plasmoid.containment;
        if (c && !(c.containmentDisplayHints & PlasmaCore.Types.ContainmentPrefersFloatingApplets)) {
            c.containmentDisplayHints |= PlasmaCore.Types.ContainmentPrefersFloatingApplets;
        }
    }
    Connections {
        target: Plasmoid.containment
        function onContainmentDisplayHintsChanged() {
            root.floatPopups();
        }
    }

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

    // Windows 11: notifications above the calendar in one flyout.
    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        Layout.minimumWidth: Kirigami.Units.gridUnit * 20
        Layout.preferredHeight: implicitHeight
        spacing: Kirigami.Units.largeSpacing

        NotificationCenter {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            Layout.bottomMargin: 0
        }
        Kirigami.Separator {
            Layout.fillWidth: true
        }
        Calendar {
            id: calendar
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            Layout.topMargin: 0
            today: root.now
            Connections {
                target: root
                function onExpandedChanged() {
                    if (root.expanded) {
                        calendar.reset();
                    }
                }
            }
        }
    }

    Component.onCompleted: floatPopups()
}
