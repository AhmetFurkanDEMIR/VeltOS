/*
    VeltOS Clock: the Windows 11 taskbar clock. Time above the date, both in
    the same small size and right-aligned, in the formats of the user's
    region (with a four-digit year, as Windows shows it). Unread
    notifications show as a count in an accent-coloured circle right of the
    clock, and "do not disturb" as a muted bell (Windows 11).

    Clicking it opens Windows 11's two flyout cards: the calendar below
    (the date as a heading with a chevron that folds the month away, the
    month, and a focus session timer at the bottom) and the notification
    centre above it. The calendar is the applet's own popup; the
    notification centre is a second Plasma dialog placed above it, of the
    notification type so that clicking it does not take the focus away from
    the calendar (which closes when it loses the focus).

    A focus session turns on "do not disturb" until it ends and announces
    its end with a notification, like Windows' Clock.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasma5support as P5Support
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
    // The calendar's heading: the long date without the year ("21 Ekim
    // Çarşamba", "Wednesday, October 21").
    readonly property string headingText: Qt.locale().toString(now,
        Qt.locale().dateFormat(Locale.LongFormat).replace(/[\s,]*y+[\s,.]*/, " ").trim())

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

    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }
    function run(command) {
        launcher.connectSource(command);
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
    function setDoNotDisturb(on, until) {
        if (on) {
            if (!until) {
                // Plasma's notification applet means "until turned off" by a year.
                until = new Date();
                until.setFullYear(until.getFullYear() + 1);
            }
            notificationSettings.notificationsInhibitedUntil = until;
        } else {
            notificationSettings.notificationsInhibitedUntil = undefined;
            notificationSettings.revokeApplicationInhibitions();
        }
        notificationSettings.save();
        tick.triggered();
    }

    // --- Focus session (Windows 11 Clock) ----------------------------------
    readonly property var focusSteps: [5, 10, 15, 20, 25, 30, 45, 60, 75, 90, 105, 120, 150, 180, 210, 240]
    readonly property int focusMinutes: Plasmoid.configuration.focusMinutes
    readonly property real focusEnd: Number(Plasmoid.configuration.focusEnd) || 0
    property real focusNow: Date.now()
    readonly property bool focusing: focusEnd > 0
    readonly property string focusLeft: {
        const seconds = Math.max(0, Math.round((focusEnd - focusNow) / 1000));
        const h = Math.floor(seconds / 3600);
        const m = Math.floor(seconds / 60) % 60;
        const s = seconds % 60;
        const pad = n => String(n).padStart(2, "0");
        return h > 0 ? h + ":" + pad(m) + ":" + pad(s) : pad(m) + ":" + pad(s);
    }

    function stepFocus(direction) {
        const steps = focusSteps;
        let i = steps.indexOf(focusMinutes);
        if (i < 0) {
            i = steps.indexOf(30);
        }
        Plasmoid.configuration.focusMinutes = steps[Math.max(0, Math.min(steps.length - 1, i + direction))];
    }
    function startFocus() {
        const end = Date.now() + focusMinutes * 60000;
        Plasmoid.configuration.focusEnd = String(end);
        focusNow = Date.now();
        setDoNotDisturb(true, new Date(end));
    }
    function stopFocus() {
        const end = focusEnd;
        Plasmoid.configuration.focusEnd = "";
        // Turn "do not disturb" off only when the session turned it on.
        const until = notificationSettings.notificationsInhibitedUntil.getTime();
        if (!isNaN(until) && Math.abs(until - end) < 5000) {
            setDoNotDisturb(false);
        }
    }
    function finishFocus() {
        stopFocus();
        const quote = text => "'" + text.replace(/'/g, "") + "'";
        run(["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
             "--object-path", "/org/freedesktop/Notifications",
             // "--": gdbus would take the timeout -1 for an option.
             "--method", "org.freedesktop.Notifications.Notify", "--",
             quote(i18n("Clock")), "0", "preferences-system-time",
             quote(i18n("Focus session complete")), quote(i18n("Well done! Time for a break.")),
             "'[]'", "'{\"sound-name\": <\"alarm-clock-elapsed\">}'", "-1"].join(" "));
    }
    Timer {
        running: root.focusing
        interval: 1000
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            root.focusNow = Date.now();
            if (root.focusNow >= root.focusEnd) {
                root.finishFocus();
            }
        }
    }

    preferredRepresentation: compactRepresentation
    toolTipMainText: Qt.formatDate(now, Qt.locale().dateFormat(Locale.LongFormat))
    toolTipSubText: ""
    onExpandedChanged: {
        if (root.expanded) {
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
            Glyph {
                visible: root.doNotDisturb
                Layout.alignment: Qt.AlignVCenter
                implicitWidth: Kirigami.Units.iconSizes.small
                implicitHeight: Kirigami.Units.iconSizes.small
                kind: "dnd"
            }
        }
    }

    // The calendar card (the applet's popup) with the notification centre
    // card above it.
    fullRepresentation: Item {
        id: flyout

        readonly property var popup: Window.window
        readonly property bool collapsed: Plasmoid.configuration.calendarCollapsed
        // Windows leaves 12 px between the two cards.
        readonly property int gap: Kirigami.Units.largeSpacing + Kirigami.Units.smallSpacing
        // Lines and bands reach the card's edges, over the popup's padding.
        readonly property real padLeft: popup ? popup.leftPadding : 0
        readonly property real padRight: popup ? popup.rightPadding : 0

        Layout.preferredWidth: Kirigami.Units.gridUnit * 19
        Layout.minimumWidth: Layout.preferredWidth
        Layout.maximumWidth: Layout.preferredWidth
        Layout.preferredHeight: card.implicitHeight
        Layout.minimumHeight: card.implicitHeight
        Layout.maximumHeight: card.implicitHeight

        Connections {
            target: root
            function onExpandedChanged() {
                if (root.expanded) {
                    calendar.reset();
                }
            }
        }

        ColumnLayout {
            id: card
            anchors.fill: parent
            spacing: 0

            // "21 Ekim Çarşamba" with the chevron that folds the month away.
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.smallSpacing
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: root.headingText
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                FlyoutButton {
                    glyph: flyout.collapsed ? "chevron-up" : "chevron-down"
                    toolTip: flyout.collapsed ? i18n("Show calendar") : i18n("Hide calendar")
                    onClicked: Plasmoid.configuration.calendarCollapsed = !flyout.collapsed
                }
            }
            Kirigami.Separator {
                visible: !flyout.collapsed
                Layout.fillWidth: true
                Layout.leftMargin: -flyout.padLeft
                Layout.rightMargin: -flyout.padRight
            }
            Calendar {
                id: calendar
                visible: !flyout.collapsed
                Layout.fillWidth: true
                Layout.margins: Kirigami.Units.smallSpacing
                Layout.topMargin: Kirigami.Units.largeSpacing
                today: root.now
            }
            Kirigami.Separator {
                Layout.fillWidth: true
                Layout.leftMargin: -flyout.padLeft
                Layout.rightMargin: -flyout.padRight
            }

            // Focus session: "- 30 min +" and "Focus", or the time left and "Stop".
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 52
                Layout.leftMargin: Kirigami.Units.smallSpacing
                Layout.rightMargin: Kirigami.Units.smallSpacing
                spacing: Kirigami.Units.smallSpacing

                FlyoutButton {
                    visible: !root.focusing
                    glyph: "minus"
                    enabled: root.focusMinutes > root.focusSteps[0]
                    toolTip: i18n("Decrease time")
                    onClicked: root.stepFocus(-1)
                }
                RowLayout {
                    visible: !root.focusing
                    Layout.fillWidth: false
                    Layout.preferredWidth: 64
                    spacing: 4
                    Item { Layout.fillWidth: true }
                    PlasmaComponents3.Label {
                        text: root.focusMinutes
                        font.weight: Font.DemiBold
                        font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.15
                    }
                    PlasmaComponents3.Label {
                        Layout.alignment: Qt.AlignBaseline
                        text: i18n("min")
                        font: Kirigami.Theme.smallFont
                    }
                    Item { Layout.fillWidth: true }
                }
                FlyoutButton {
                    visible: !root.focusing
                    glyph: "plus"
                    enabled: root.focusMinutes < root.focusSteps[root.focusSteps.length - 1]
                    toolTip: i18n("Increase time")
                    onClicked: root.stepFocus(1)
                }
                PlasmaComponents3.Label {
                    visible: root.focusing
                    Layout.leftMargin: Kirigami.Units.smallSpacing
                    text: root.focusLeft
                    font.weight: Font.DemiBold
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.15
                    font.features: ({ "tnum": 1 })
                }
                Item { Layout.fillWidth: true }
                FlyoutButton {
                    glyph: root.focusing ? "stop" : "play"
                    glyphSize: 10
                    text: root.focusing ? i18n("Stop") : i18n("Focus")
                    onClicked: root.focusing ? root.stopFocus() : root.startFocus()
                }
            }
        }

        // The notification centre card, 12 px above the calendar card and
        // as wide, growing up to the top of the screen.
        PlasmaCore.Dialog {
            id: notifications

            type: PlasmaCore.Dialog.Notification
            flags: Qt.WindowDoesNotAcceptFocus
            location: PlasmaCore.Types.Floating
            visible: root.expanded && flyout.popup !== null && flyout.popup.visible
            x: flyout.popup ? flyout.popup.x + flyout.popup.width - width : 0
            y: flyout.popup ? flyout.popup.y - flyout.gap - height : 0
            // Wayland applies a new position with the next frame only: draw one.
            onXChanged: Qt.callLater(update)
            onYChanged: Qt.callLater(update)

            mainItem: NotificationCenter {
                width: flyout.width
                height: implicitHeight
                maximumHeight: flyout.popup
                    ? flyout.popup.y - flyout.gap - flyout.Screen.virtualY - flyout.gap
                      - notifications.margins.top - notifications.margins.bottom
                    : Kirigami.Units.gridUnit * 30
                doNotDisturb: root.doNotDisturb
                onToggleDoNotDisturb: root.setDoNotDisturb(!root.doNotDisturb)
                onOpenSettings: {
                    root.expanded = false;
                    root.run("veltos-settings notifications");
                }
            }
        }
    }

    Component.onCompleted: floatPopups()
}
