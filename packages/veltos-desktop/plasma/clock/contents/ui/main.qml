/*
    VeltOS Clock: the Windows 11 taskbar clock. Time above the date, both in
    the same small size and right-aligned, in the formats of the user's
    region (with a four-digit year, as Windows shows it). Clicking it opens
    the notification centre and the calendar. Unread notifications show as
    a count in an accent-coloured circle right of the clock, and "do not
    disturb" as a muted bell (Windows 11).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.notificationmanager as NotificationManager

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

    // Notifications that arrived since the notification centre was last
    // opened.
    NotificationManager.Notifications {
        id: unread
        showExpired: true
        showDismissed: true
        showJobs: false
        urgencies: NotificationManager.Notifications.CriticalUrgency
                   | NotificationManager.Notifications.NormalUrgency
    }
    readonly property int unreadCount: Math.min(99, unread.unreadNotificationsCount)
    NotificationManager.Settings {
        id: notificationSettings
    }
    readonly property bool doNotDisturb: {
        const until = notificationSettings.notificationsInhibitedUntil;
        return notificationSettings.notificationsInhibitedByApplication
            || (!isNaN(until.getTime()) && until.getTime() > now.getTime());
    }

    preferredRepresentation: compactRepresentation
    toolTipMainText: Qt.formatDate(now, Qt.locale().dateFormat(Locale.LongFormat))
    toolTipSubText: ""
    onExpandedChanged: {
        if (expanded) {
            tick.triggered();
        } else {
            unread.lastRead = undefined; // everything seen: now
        }
    }

    compactRepresentation: MouseArea {
        id: button

        Layout.minimumWidth: row.implicitWidth + Kirigami.Units.largeSpacing * 2
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

        RowLayout {
            id: row
            anchors.right: parent.right
            anchors.rightMargin: Kirigami.Units.largeSpacing
            anchors.verticalCenter: parent.verticalCenter
            spacing: Kirigami.Units.largeSpacing

            ColumnLayout {
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

            // Unread count, Windows 11 style.
            Rectangle {
                visible: root.unreadCount > 0 && !root.doNotDisturb
                Layout.alignment: Qt.AlignVCenter
                implicitWidth: Math.max(implicitHeight, countLabel.implicitWidth + Kirigami.Units.smallSpacing * 2)
                implicitHeight: Math.round(Kirigami.Units.gridUnit * 1.05)
                radius: height / 2
                color: Kirigami.Theme.highlightColor
                PlasmaComponents3.Label {
                    id: countLabel
                    anchors.centerIn: parent
                    text: root.unreadCount
                    color: Kirigami.Theme.highlightedTextColor
                    font.pointSize: 7.5
                    font.weight: Font.DemiBold
                }
            }
            Kirigami.Icon {
                visible: root.doNotDisturb
                Layout.alignment: Qt.AlignVCenter
                implicitWidth: Kirigami.Units.iconSizes.small
                implicitHeight: Kirigami.Units.iconSizes.small
                source: "notifications-disabled-symbolic"
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
