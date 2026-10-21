/*
    Windows 11 notification centre (the upper flyout card): "Notifications"
    with a do-not-disturb button and "Clear all", then the notifications
    grouped by app - the app's icon and name as a heading (on hover: its
    notification settings and a button that clears the app's
    notifications), below it the app's newest notification as a card with
    the time and an expand/collapse chevron, the title, the text and a
    "+N notifications" button that unfolds the app's older ones. Clicking a
    card runs its default action. The notifications come from Plasma's
    notification server (org.kde.notificationmanager), like KDE's own
    history.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.notificationmanager as NotificationManager

ColumnLayout {
    id: centre

    // Most the card may grow to (the screen space above the calendar).
    property real maximumHeight: Kirigami.Units.gridUnit * 30
    property bool doNotDisturb: false
    signal toggleDoNotDisturb()
    signal openSettings()

    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor)
                                 === Kirigami.ColorUtils.Dark
    readonly property color cardColor: dark ? Qt.alpha("white", 0.055) : Qt.alpha("white", 0.75)
    readonly property color cardBorder: dark ? Qt.alpha("black", 0.25) : Qt.alpha("black", 0.07)
    readonly property int count: history.count

    // [{key, name, icon, items: [{id, summary, body, ...}]}], newest app first.
    property var groups: []
    // Apps whose older notifications are unfolded, and notifications whose
    // text is expanded (or folded, for the newest one), by key and id.
    property var unfolded: ({})
    property var toggled: ({})

    NotificationManager.Notifications {
        id: history
        showExpired: true
        showDismissed: true
        showJobs: false
        sortMode: NotificationManager.Notifications.SortByDate
        groupMode: NotificationManager.Notifications.GroupDisabled
        urgencies: NotificationManager.Notifications.CriticalUrgency
                   | NotificationManager.Notifications.NormalUrgency
        onRowsInserted: Qt.callLater(centre.rebuild)
        onRowsRemoved: Qt.callLater(centre.rebuild)
        onModelReset: Qt.callLater(centre.rebuild)
        onDataChanged: Qt.callLater(centre.rebuild)
        onLayoutChanged: Qt.callLater(centre.rebuild)
    }

    function role(row, name) {
        return history.data(history.index(row, 0), NotificationManager.Notifications[name + "Role"]);
    }
    function rebuild() {
        // Newest first (the model keeps the order of arrival); the id
        // breaks ties within a second.
        const rows = [];
        for (let row = 0; row < history.count; ++row) {
            rows.push({row: row, id: role(row, "Id"), time: role(row, "Updated") || role(row, "Created")});
        }
        rows.sort((a, b) => ((b.time ? b.time.getTime() : 0) - (a.time ? a.time.getTime() : 0)) || (b.id - a.id));
        const byKey = {};
        const list = [];
        for (const entry of rows) {
            const row = entry.row;
            const name = role(row, "ApplicationName") || "";
            const key = role(row, "DesktopEntry") || role(row, "NotifyRcName") || name;
            if (!byKey[key]) {
                // Notifications without an app icon (scripts, gdbus) show their own.
                byKey[key] = {key: key, name: name,
                              icon: role(row, "ApplicationIconName") || role(row, "IconName") || "", items: []};
                list.push(byKey[key]);
            }
            byKey[key].items.push({
                id: role(row, "Id"),
                summary: role(row, "Summary") || "",
                body: role(row, "Body") || "",
                image: role(row, "Image"),
                iconName: role(row, "IconName") || "",
                time: role(row, "Updated") || role(row, "Created"),
                hasDefaultAction: !!role(row, "HasDefaultAction"),
                actionNames: role(row, "ActionNames") || [],
                actionLabels: role(row, "ActionLabels") || [],
            });
        }
        groups = list;
    }
    function rowOf(id) {
        for (let row = 0; row < history.count; ++row) {
            if (role(row, "Id") === id) {
                return row;
            }
        }
        return -1;
    }
    function closeIds(ids) {
        ids.forEach(id => {
            const row = rowOf(id);
            if (row >= 0) {
                history.close(history.index(row, 0));
            }
        });
    }
    function clearAll() {
        const ids = [];
        groups.forEach(group => group.items.forEach(item => ids.push(item.id)));
        closeIds(ids);
    }
    function activate(id) {
        const row = rowOf(id);
        if (row >= 0 && role(row, "HasDefaultAction")) {
            history.invokeDefaultAction(history.index(row, 0));
        }
    }
    function invokeAction(id, action) {
        const row = rowOf(id);
        if (row >= 0) {
            history.invokeAction(history.index(row, 0), action);
        }
    }
    function isExpanded(id, newest) {
        return newest !== !!toggled[id];
    }
    function toggle(id) {
        const copy = Object.assign({}, toggled);
        copy[id] = !copy[id];
        toggled = copy;
    }
    function setUnfolded(key, on) {
        const copy = Object.assign({}, unfolded);
        copy[key] = on;
        unfolded = copy;
    }
    // Windows: the time for today's notifications, the weekday within a
    // week, the date before that.
    function timeText(date) {
        if (!date) {
            return "";
        }
        const now = new Date();
        const days = Math.floor((new Date(now.getFullYear(), now.getMonth(), now.getDate()) - date) / 86400000) + 1;
        if (days <= 0) {
            return Qt.formatTime(date, Qt.locale().timeFormat(Locale.ShortFormat));
        }
        if (days < 7) {
            return Qt.locale().standaloneDayName(date.getDay(), Locale.LongFormat);
        }
        return Qt.formatDate(date, Qt.locale().dateFormat(Locale.ShortFormat));
    }

    Component.onCompleted: rebuild()

    spacing: 0

    RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
        Layout.leftMargin: Kirigami.Units.largeSpacing + Kirigami.Units.smallSpacing
        Layout.bottomMargin: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.largeSpacing

        PlasmaComponents3.Label {
            Layout.fillWidth: true
            text: i18n("Notifications")
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        FlyoutButton {
            glyph: "dnd"
            glyphSize: 16
            accent: centre.doNotDisturb
            toolTip: i18n("Do not disturb")
            onClicked: centre.toggleDoNotDisturb()
        }
        FlyoutButton {
            visible: centre.count > 0
            text: i18n("Clear all")
            onClicked: centre.clearAll()
        }
    }

    PlasmaComponents3.Label {
        visible: centre.count === 0
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 4
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        text: i18n("No new notifications")
        opacity: 0.7
    }

    Flickable {
        id: flick
        visible: centre.count > 0
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(column.implicitHeight, Math.max(Kirigami.Units.gridUnit * 6,
                                         centre.maximumHeight - Kirigami.Units.gridUnit * 3))
        contentWidth: width
        contentHeight: column.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {
            id: scrollBar
        }

        ColumnLayout {
            id: column
            // Cards end left of the scroll bar when there is one.
            width: flick.width - (scrollBar.visible && scrollBar.size < 1 ? scrollBar.width : 0)
            spacing: Kirigami.Units.smallSpacing

            Repeater {
                model: centre.groups
                delegate: ColumnLayout {
                    id: group
                    required property var modelData
                    required property int index
                    readonly property bool unfolded: !!centre.unfolded[modelData.key]
                    readonly property var shown: unfolded ? modelData.items : modelData.items.slice(0, 1)

                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.largeSpacing
                    Layout.rightMargin: Kirigami.Units.largeSpacing
                    Layout.bottomMargin: Kirigami.Units.smallSpacing
                    spacing: 2

                    // App heading.
                    MouseArea {
                        id: heading
                        Layout.fillWidth: true
                        Layout.preferredHeight: 36
                        hoverEnabled: true

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Kirigami.Units.smallSpacing
                            spacing: Kirigami.Units.largeSpacing

                            Kirigami.Icon {
                                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                                Layout.preferredHeight: Kirigami.Units.iconSizes.small
                                source: group.modelData.icon || "preferences-desktop-notification"
                            }
                            PlasmaComponents3.Label {
                                Layout.fillWidth: true
                                text: group.modelData.name
                                font: Kirigami.Theme.smallFont
                                elide: Text.ElideRight
                            }
                            FlyoutButton {
                                visible: heading.containsMouse
                                flat: true
                                glyph: "more"
                                toolTip: i18n("Settings")
                                onClicked: centre.openSettings()
                            }
                            FlyoutButton {
                                visible: heading.containsMouse
                                flat: true
                                glyph: "close"
                                glyphSize: 10
                                toolTip: i18n("Clear notifications from %1", group.modelData.name)
                                onClicked: centre.closeIds(group.modelData.items.map(item => item.id))
                            }
                        }
                    }

                    Repeater {
                        model: group.shown
                        delegate: MouseArea {
                            id: card
                            required property var modelData
                            required property int index
                            readonly property var item: modelData
                            readonly property bool newest: index === 0
                            readonly property bool expanded: centre.isExpanded(item.id, newest && group.index === 0)
                            readonly property bool last: index === group.shown.length - 1
                            readonly property int more: group.modelData.items.length - 1
                            readonly property var picture: item.image ? item.image
                                : (item.iconName && item.iconName !== group.modelData.icon ? item.iconName : "")

                            Layout.fillWidth: true
                            implicitHeight: content.implicitHeight + Kirigami.Units.largeSpacing * 2
                            hoverEnabled: true
                            cursorShape: item.hasDefaultAction ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: centre.activate(item.id)

                            Rectangle {
                                anchors.fill: parent
                                radius: 6
                                color: card.containsMouse ? Qt.tint(centre.cardColor, Qt.alpha(Kirigami.Theme.textColor, 0.03))
                                                          : centre.cardColor
                                border.width: 1
                                border.color: centre.cardBorder
                            }

                            ColumnLayout {
                                id: content
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: Kirigami.Units.largeSpacing
                                anchors.topMargin: Kirigami.Units.smallSpacing
                                spacing: Kirigami.Units.smallSpacing

                                // Time and the expand/collapse chevron; close on hover.
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 0
                                    MouseArea {
                                        Layout.preferredHeight: 26
                                        Layout.preferredWidth: timeRow.implicitWidth + Kirigami.Units.smallSpacing * 2
                                        Layout.leftMargin: -Kirigami.Units.smallSpacing
                                        hoverEnabled: true
                                        onClicked: centre.toggle(card.item.id)
                                        Accessible.role: Accessible.Button
                                        Accessible.name: card.expanded ? i18n("Collapse") : i18n("Expand")
                                        Rectangle {
                                            anchors.fill: parent
                                            radius: 4
                                            color: Qt.alpha(Kirigami.Theme.textColor, parent.containsMouse ? 0.07 : 0)
                                        }
                                        RowLayout {
                                            id: timeRow
                                            anchors.centerIn: parent
                                            spacing: Kirigami.Units.smallSpacing
                                            PlasmaComponents3.Label {
                                                text: centre.timeText(card.item.time)
                                                font: Kirigami.Theme.smallFont
                                                opacity: 0.8
                                            }
                                            Glyph {
                                                Layout.preferredWidth: 10
                                                Layout.preferredHeight: 10
                                                kind: card.expanded ? "chevron-up" : "chevron-down"
                                                opacity: 0.8
                                            }
                                        }
                                    }
                                    Item { Layout.fillWidth: true }
                                    FlyoutButton {
                                        opacity: card.containsMouse ? 1 : 0
                                        flat: true
                                        implicitWidth: 26
                                        implicitHeight: 26
                                        glyph: "close"
                                        glyphSize: 10
                                        toolTip: i18n("Close")
                                        onClicked: centre.closeIds([card.item.id])
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: Kirigami.Units.largeSpacing

                                    Kirigami.Icon {
                                        visible: card.picture !== ""
                                        Layout.alignment: Qt.AlignTop
                                        Layout.preferredWidth: Kirigami.Units.iconSizes.large
                                        Layout.preferredHeight: Kirigami.Units.iconSizes.large
                                        source: card.picture
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 2
                                        PlasmaComponents3.Label {
                                            Layout.fillWidth: true
                                            text: card.item.summary
                                            font.weight: Font.DemiBold
                                            wrapMode: Text.Wrap
                                            maximumLineCount: card.expanded ? 3 : 1
                                            elide: Text.ElideRight
                                        }
                                        PlasmaComponents3.Label {
                                            Layout.fillWidth: true
                                            visible: text.length > 0
                                            text: card.item.body
                                            textFormat: Text.StyledText
                                            wrapMode: Text.Wrap
                                            maximumLineCount: card.expanded ? 10 : 2
                                            elide: Text.ElideRight
                                            opacity: 0.85
                                        }
                                    }
                                }

                                // The notification's buttons (expanded cards).
                                Flow {
                                    visible: card.expanded && actions.count > 0
                                    Layout.fillWidth: true
                                    Layout.topMargin: Kirigami.Units.smallSpacing
                                    spacing: Kirigami.Units.smallSpacing
                                    Repeater {
                                        id: actions
                                        model: card.item.actionNames.filter(name => name !== "default")
                                        delegate: FlyoutButton {
                                            required property string modelData
                                            required property int index
                                            text: card.item.actionLabels[card.item.actionNames.indexOf(modelData)] || modelData
                                            onClicked: centre.invokeAction(card.item.id, modelData)
                                        }
                                    }
                                }

                                // "+N notifications" / "Show fewer".
                                FlyoutButton {
                                    visible: card.last && card.more > 0
                                    Layout.topMargin: Kirigami.Units.smallSpacing
                                    text: group.unfolded ? i18n("Show fewer")
                                                         : i18np("+1 notification", "+%1 notifications", card.more)
                                    onClicked: centre.setUnfolded(group.modelData.key, !group.unfolded)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
