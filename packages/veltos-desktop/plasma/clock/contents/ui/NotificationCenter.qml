/*
    Windows 11 notification centre (above the calendar): "Notifications"
    with "Clear all", then one card per notification - app icon and name,
    title, text, a close button on hover. Clicking a card runs its default
    action. The notifications come from Plasma's notification server
    (org.kde.notificationmanager), like KDE's own history.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.notificationmanager as NotificationManager

ColumnLayout {
    id: centre

    spacing: Kirigami.Units.largeSpacing

    NotificationManager.Notifications {
        id: history
        showExpired: true
        showDismissed: true
        showJobs: false
        sortMode: NotificationManager.Notifications.SortByDate
        groupMode: NotificationManager.Notifications.GroupDisabled
        urgencies: NotificationManager.Notifications.CriticalUrgency
                   | NotificationManager.Notifications.NormalUrgency
    }

    readonly property int count: list.count

    function relativeTime(date) {
        if (!date) {
            return "";
        }
        const minutes = Math.floor((Date.now() - date.getTime()) / 60000);
        if (minutes < 1) {
            return i18n("Now");
        }
        if (minutes < 60) {
            return i18np("1 min ago", "%1 min ago", minutes);
        }
        return Qt.formatTime(date, Qt.locale().timeFormat(Locale.ShortFormat));
    }

    RowLayout {
        Layout.fillWidth: true
        PlasmaComponents3.Label {
            Layout.fillWidth: true
            text: i18n("Notifications")
            font.weight: Font.DemiBold
        }
        PlasmaComponents3.ToolButton {
            visible: list.count > 0
            text: i18n("Clear all")
            onClicked: history.clear(NotificationManager.Notifications.ClearExpired)
        }
    }

    ListView {
        id: list
        Layout.fillWidth: true
        Layout.preferredHeight: count === 0 ? emptyLabel.implicitHeight + Kirigami.Units.gridUnit * 2
                                            : Math.min(contentHeight, Kirigami.Units.gridUnit * 18)
        clip: true
        spacing: Kirigami.Units.smallSpacing
        model: history
        boundsBehavior: Flickable.StopAtBounds

        delegate: MouseArea {
            id: card
            required property int index
            required property var model
            width: ListView.view.width
            height: cardContent.implicitHeight + Kirigami.Units.largeSpacing * 2
            hoverEnabled: true
            onClicked: {
                if (model.hasDefaultAction) {
                    history.invokeDefaultAction(history.index(index, 0));
                }
            }

            Rectangle {
                anchors.fill: parent
                radius: 6
                color: Qt.alpha(Kirigami.Theme.textColor, card.containsMouse ? 0.08 : 0.05)
                border.width: 1
                border.color: Qt.alpha(Kirigami.Theme.textColor, 0.06)
            }

            ColumnLayout {
                id: cardContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: Kirigami.Units.largeSpacing
                spacing: Kirigami.Units.smallSpacing

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing
                    Kirigami.Icon {
                        implicitWidth: Kirigami.Units.iconSizes.small
                        implicitHeight: Kirigami.Units.iconSizes.small
                        source: card.model.applicationIconName || card.model.iconName || "preferences-desktop-notification"
                    }
                    PlasmaComponents3.Label {
                        Layout.fillWidth: true
                        text: card.model.applicationName || ""
                        font: Kirigami.Theme.smallFont
                        opacity: 0.8
                        elide: Text.ElideRight
                    }
                    PlasmaComponents3.Label {
                        visible: !card.containsMouse
                        text: centre.relativeTime(card.model.updated || card.model.created)
                        font: Kirigami.Theme.smallFont
                        opacity: 0.7
                    }
                    PlasmaComponents3.ToolButton {
                        visible: card.containsMouse
                        implicitWidth: Kirigami.Units.iconSizes.small + Kirigami.Units.smallSpacing * 2
                        implicitHeight: implicitWidth
                        icon.name: "window-close-symbolic"
                        display: PlasmaComponents3.AbstractButton.IconOnly
                        text: i18n("Close")
                        onClicked: history.close(history.index(card.index, 0))
                    }
                }
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: card.model.summary || ""
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: card.model.body || ""
                    textFormat: Text.StyledText
                    wrapMode: Text.Wrap
                    maximumLineCount: 4
                    elide: Text.ElideRight
                    opacity: 0.85
                }
            }
        }

        PlasmaComponents3.Label {
            id: emptyLabel
            anchors.centerIn: parent
            visible: list.count === 0
            text: i18n("No new notifications")
            opacity: 0.7
        }
    }
}
