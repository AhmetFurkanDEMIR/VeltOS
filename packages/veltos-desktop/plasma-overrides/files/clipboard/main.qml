/*
    VeltOS: the clipboard flyout as Windows 11's clipboard history (Win+V):
    "Clipboard history" with "Clear all" at the top, then everything that
    was copied as cards, the newest first: up to three lines of text or a
    picture. Clicking a card puts it back on the clipboard; its "..."
    button deletes it. With nothing copied yet, a short message instead.
    KDE's search field, barcode and edit pages and its settings dialog are
    not offered.

    Replaces Plasma's main.qml of the clipboard applet
    (org.kde.plasma.clipboard, plasma-workspace 6.3.6) through
    update-plasma-overrides; the history is still Klipper's
    (org.kde.plasma.private.clipboard HistoryModel). Texts come from the
    veltos-desktop catalog (i18nd).

    SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2014 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 VeltOS Project

    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

import org.kde.plasma.private.clipboard as Private

PlasmoidItem {
    id: main

    readonly property bool isClipboardEmpty: historyModel.count === 0
    readonly property string domain: "veltos-desktop"
    function tr(text) {
        return i18nd(domain, text);
    }

    switchWidth: Kirigami.Units.gridUnit * 5
    switchHeight: Kirigami.Units.gridUnit * 5
    Plasmoid.status: isClipboardEmpty ? PlasmaCore.Types.PassiveStatus : PlasmaCore.Types.ActiveStatus
    toolTipMainText: tr("Clipboard history")
    toolTipSubText: isClipboardEmpty ? tr("Nothing copied yet") : historyModel.currentText
    toolTipTextFormat: Text.PlainText
    Plasmoid.icon: "klipper-symbolic"

    function action_clearHistory() {
        historyModel.clearHistory();
    }

    onIsClipboardEmptyChanged: {
        if (isClipboardEmpty) {
            // We need to hide the applet before changing its status to passive
            // because only the active applet can hide itself
            if (main.hideOnWindowDeactivate)
                main.expanded = false;
            Plasmoid.status = PlasmaCore.Types.HiddenStatus;
        } else {
            Plasmoid.status = PlasmaCore.Types.ActiveStatus
        }
    }

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: main.tr("Clear all")
            icon.name: "edit-clear-history"
            visible: !main.isClipboardEmpty
            onTriggered: historyModel.clearHistory()
        }
    ]

    Private.HistoryModel {
        id: historyModel
    }

    fullRepresentation: PlasmaExtras.Representation {
        id: dialogItem

        Layout.minimumWidth: Kirigami.Units.gridUnit * 20
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        Layout.maximumWidth: Kirigami.Units.gridUnit * 24
        Layout.minimumHeight: Kirigami.Units.gridUnit * 24
        Layout.maximumHeight: Kirigami.Units.gridUnit * 30
        collapseMarginsHint: true
        focus: true

        readonly property var appletInterface: main

        Connections {
            target: main
            function onExpandedChanged(expanded) {
                if (expanded) {
                    list.currentIndex = -1;
                    list.positionViewAtBeginning();
                    list.forceActiveFocus();
                }
            }
        }

        Keys.forwardTo: [list]

        // "Clipboard history" and "Clear all", as at the top of Windows 11's
        // clipboard history.
        RowLayout {
            id: titleRow
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                leftMargin: Kirigami.Units.largeSpacing * 2
                rightMargin: Kirigami.Units.largeSpacing
                topMargin: Kirigami.Units.largeSpacing
            }
            height: Kirigami.Units.gridUnit * 2
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: main.tr("Clipboard history")
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            PlasmaComponents3.ToolButton {
                visible: !main.isClipboardEmpty
                text: main.tr("Clear all")
                onClicked: historyModel.clearHistory()
            }
        }

        ListView {
            id: list
            anchors {
                left: parent.left
                right: parent.right
                top: titleRow.bottom
                bottom: parent.bottom
                margins: Kirigami.Units.largeSpacing
            }
            clip: true
            spacing: Kirigami.Units.smallSpacing * 2
            model: historyModel
            currentIndex: -1
            keyNavigationEnabled: true
            highlightFollowsCurrentItem: false
            boundsBehavior: Flickable.StopAtBounds
            focus: true

            Keys.onReturnPressed: {
                if (currentItem !== null)
                    currentItem.choose();
            }
            Keys.onEnterPressed: event => Keys.returnPressed(event)
            Keys.onDeletePressed: {
                if (currentItem !== null)
                    historyModel.remove(currentItem.uuid);
            }

            delegate: Card {}

            // Nothing copied yet.
            ColumnLayout {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 2
                visible: list.count === 0
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    Layout.alignment: Qt.AlignHCenter
                    implicitWidth: Kirigami.Units.iconSizes.large
                    implicitHeight: implicitWidth
                    source: "edit-paste-symbolic"
                    color: Kirigami.Theme.textColor
                    opacity: 0.6
                }
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.weight: Font.DemiBold
                    text: main.tr("Nothing copied yet")
                }
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                    text: main.tr("Text and pictures you copy appear here, so you can use them again.")
                }
            }
        }
    }

    // One copied item: up to three lines of text, or a picture.
    component Card: MouseArea {
        id: card

        required property int index
        required property var model
        required property var decoration
        required property size imageSize
        required property var uuid
        required property int type

        readonly property bool isImage: type === 4
        readonly property bool highlighted: containsMouse || ListView.isCurrentItem

        function choose() {
            historyModel.moveToTop(uuid);
            if (main.hideOnWindowDeactivate)
                main.expanded = false;
        }

        width: ListView.view.width
        height: content.implicitHeight + Kirigami.Units.largeSpacing * 2 + Kirigami.Units.smallSpacing
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        onClicked: choose()
        Accessible.role: Accessible.ListItem
        Accessible.name: isImage ? main.tr("Picture") : (model.display ?? "")

        Rectangle {
            anchors.fill: parent
            radius: Kirigami.Units.cornerRadius * 2
            color: Qt.alpha(Kirigami.Theme.textColor, card.pressed ? 0.05 : (card.highlighted ? 0.09 : 0.045))
            border.width: 1
            border.color: Qt.alpha(Kirigami.Theme.textColor, 0.08)
        }

        Item {
            id: content
            x: Kirigami.Units.largeSpacing + Kirigami.Units.smallSpacing
            y: Kirigami.Units.largeSpacing
            width: parent.width - x - more.width - Kirigami.Units.smallSpacing * 2
            implicitHeight: card.isImage ? picture.height : text.implicitHeight

            PlasmaComponents3.Label {
                id: text
                visible: !card.isImage
                width: parent.width
                maximumLineCount: 3
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                elide: Text.ElideRight
                textFormat: Text.PlainText
                text: (card.model.display ?? "").slice(0, 400).trim()
            }
            Image {
                id: picture
                visible: card.isImage
                anchors.left: parent.left
                width: Math.min(parent.width, Math.round(height * card.imageSize.width / Math.max(1, card.imageSize.height)))
                height: card.isImage ? sourceSize.height : 0
                cache: false
                source: card.isImage ? card.decoration : ""
                sourceSize.height: Math.min(card.imageSize.height, Kirigami.Units.gridUnit * 6)
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
        }

        // Windows 11's "..." on each card.
        PlasmaComponents3.ToolButton {
            id: more
            anchors {
                right: parent.right
                top: parent.top
                rightMargin: Kirigami.Units.smallSpacing
                topMargin: Kirigami.Units.smallSpacing
            }
            opacity: card.highlighted || menu.status === PlasmaExtras.Menu.Open ? 1 : 0
            icon.name: "view-more-symbolic"
            display: PlasmaComponents3.AbstractButton.IconOnly
            text: main.tr("More options")
            onClicked: menu.open(0, height)

            PlasmaExtras.Menu {
                id: menu
                visualParent: more
                PlasmaExtras.MenuItem {
                    text: main.tr("Delete")
                    icon: "edit-delete"
                    onClicked: historyModel.remove(card.uuid)
                }
                PlasmaExtras.MenuItem {
                    text: main.tr("Clear all")
                    icon: "edit-clear-history"
                    onClicked: historyModel.clearHistory()
                }
            }
        }
    }
}
