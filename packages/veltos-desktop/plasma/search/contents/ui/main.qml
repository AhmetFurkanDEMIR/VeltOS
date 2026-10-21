/*
    VeltOS Search: the search box of the Windows 11 taskbar. Clicking it
    opens Windows 11's search window (not Start): a search field at the
    top, the pinned apps as "Top apps" while it is empty, and while typing
    the results on the left with the best match on the right ("Open").
    Results come from Plasma's runners (apps, settings, documents, the
    calculator), as in Start.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

    switchWidth: 0
    switchHeight: 0
    preferredRepresentation: compactRepresentation
    toolTipMainText: i18n("Search")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    // The pinned apps of Start, shown as "Top apps" like Windows.
    Kicker.RootModel {
        id: rootModel
        appletInterface: root
        autoPopulate: false
        showAllApps: false
        showRecentApps: false
        showRecentDocs: false
        showSeparators: false
        Component.onCompleted: refresh()
    }

    // "Top apps": the most used apps (KActivities' statistics), as Windows
    // lists them while the field is empty.
    Kicker.RecentUsageModel {
        id: topAppsModel
        shownItems: Kicker.RecentUsageModel.OnlyApps
        ordering: Kicker.RecentUsageModel.Popular
    }

    Kicker.RunnerModel {
        id: runnerModel
        appletInterface: root
        favoritesModel: rootModel.favoritesModel
        mergeResults: true
        query: ""
    }

    // --- The taskbar box ---------------------------------------------------
    compactRepresentation: MouseArea {
        id: box

        Layout.minimumWidth: root.vertical ? -1 : (compact ? height : Kirigami.Units.gridUnit * 11)
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.fillHeight: true
        // On a vertical or crowded taskbar only the magnifier, like Windows.
        readonly property bool compact: root.vertical
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Search")

        Rectangle {
            id: pill
            anchors.centerIn: parent
            width: box.compact ? Math.min(parent.width, parent.height) - Kirigami.Units.smallSpacing * 2
                               : parent.width - Kirigami.Units.smallSpacing * 2
            height: Math.min(parent.height - Kirigami.Units.smallSpacing * 3, Kirigami.Units.gridUnit * 2)
            radius: height / 2
            color: Kirigami.Theme.backgroundColor
            opacity: box.containsMouse || root.expanded ? 1 : 0.82
            border.width: 1
            border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                  Kirigami.Theme.textColor.b, box.containsMouse || root.expanded ? 0.18 : 0.1)
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        RowLayout {
            anchors.fill: pill
            anchors.leftMargin: box.compact ? 0 : Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing * 2

            Kirigami.Icon {
                Layout.alignment: box.compact ? Qt.AlignCenter : Qt.AlignVCenter
                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                Layout.preferredHeight: Kirigami.Units.iconSizes.small
                source: "search"
                color: Kirigami.Theme.textColor
                isMask: true
            }
            PC3.Label {
                visible: !box.compact
                Layout.fillWidth: true
                text: i18n("Search")
                opacity: 0.7
                elide: Text.ElideRight
            }
        }
    }

    // --- The search window -----------------------------------------------
    fullRepresentation: FocusScope {
        id: panel

        readonly property bool searching: searchField.text.length > 0
        readonly property var results: runnerModel.count > 0 ? runnerModel.modelForRow(0) : null
        readonly property int bestIndex: resultList.count > 0 ? Math.max(0, resultList.currentIndex) : -1

        Layout.minimumWidth: Kirigami.Units.gridUnit * 40
        Layout.minimumHeight: Kirigami.Units.gridUnit * 32
        Layout.preferredWidth: Kirigami.Units.gridUnit * 46
        Layout.preferredHeight: Kirigami.Units.gridUnit * 36
        focus: true

        function launch(model, index) {
            if (model && index >= 0) {
                model.trigger(index, "", null);
                root.expanded = false;
            }
        }

        Connections {
            target: root
            function onExpandedChanged() {
                if (root.expanded) {
                    searchField.text = "";
                    searchField.forceActiveFocus();
                } else {
                    searchField.text = "";
                }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.gridUnit * 1.5
            spacing: Kirigami.Units.largeSpacing

            // The search field, a rounded pill as in Windows 11.
            PlasmaExtras.SearchField {
                id: searchField
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 2.4
                placeholderText: i18n("Search for apps, settings and documents")
                background: Rectangle {
                    radius: height / 2
                    color: Kirigami.Theme.backgroundColor
                    border.width: searchField.activeFocus ? 2 : 1
                    border.color: searchField.activeFocus ? Kirigami.Theme.highlightColor
                                                          : Qt.alpha(Kirigami.Theme.textColor, 0.15)
                    // The accent line under the field, like Windows' focused fields.
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: parent.width - parent.radius
                        height: 2
                        radius: 1
                        color: Kirigami.Theme.highlightColor
                        visible: searchField.activeFocus
                    }
                }
                onTextChanged: runnerModel.query = text
                onAccepted: panel.launch(panel.results, panel.bestIndex)
                Keys.onDownPressed: {
                    if (resultList.count > 0) {
                        resultList.forceActiveFocus();
                        resultList.currentIndex = 0;
                    }
                }
                Keys.onEscapePressed: {
                    if (text !== "")
                        text = "";
                    else
                        root.expanded = false;
                }
            }

            // Empty field: the pinned apps as "Top apps".
            ColumnLayout {
                visible: !panel.searching
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Kirigami.Units.largeSpacing

                PC3.Label {
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    text: i18n("Top apps")
                    font.weight: Font.DemiBold
                    visible: topApps.count > 0
                }
                PC3.Label {
                    visible: topApps.count === 0
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    text: i18n("Start typing to search for apps, settings and documents.")
                    opacity: 0.7
                }
                GridView {
                    id: topApps
                    Layout.fillWidth: true
                    Layout.preferredHeight: count > 0 ? cellHeight : 0
                    model: topAppsModel
                    cellWidth: Math.floor(width / 6)
                    cellHeight: Kirigami.Units.gridUnit * 5.4
                    interactive: false
                    clip: true
                    delegate: MouseArea {
                        id: topApp
                        required property int index
                        required property var model
                        width: topApps.cellWidth
                        height: topApps.cellHeight
                        hoverEnabled: true
                        Accessible.role: Accessible.Button
                        Accessible.name: model.display
                        onClicked: panel.launch(topApps.model, index)
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.smallSpacing
                            radius: 6
                            color: Kirigami.Theme.textColor
                            opacity: topApp.pressed ? 0.14 : (topApp.containsMouse ? 0.07 : 0)
                        }
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.smallSpacing * 2
                            spacing: Kirigami.Units.smallSpacing
                            Kirigami.Icon {
                                Layout.alignment: Qt.AlignHCenter
                                implicitWidth: Kirigami.Units.iconSizes.medium
                                implicitHeight: Kirigami.Units.iconSizes.medium
                                source: topApp.model.decoration
                            }
                            PC3.Label {
                                Layout.fillWidth: true
                                text: topApp.model.display
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                                maximumLineCount: 2
                                wrapMode: Text.WordWrap
                                font.pointSize: Kirigami.Theme.smallFont.pointSize
                            }
                        }
                    }
                }
                Item { Layout.fillHeight: true }
            }

            // Typing: results on the left, the best match on the right.
            RowLayout {
                visible: panel.searching
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Kirigami.Units.gridUnit

                ColumnLayout {
                    // Fixed share of the width: with only a preferred width the
                    // list took everything and the best-match card got none.
                    Layout.preferredWidth: Math.round(parent.width * 0.56)
                    Layout.maximumWidth: Math.round(parent.width * 0.56)
                    Layout.fillHeight: true
                    spacing: Kirigami.Units.smallSpacing

                    PC3.Label {
                        Layout.leftMargin: Kirigami.Units.largeSpacing
                        text: i18n("Best match")
                        font.weight: Font.DemiBold
                        visible: resultList.count > 0
                    }
                    PC3.ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        ListView {
                            id: resultList
                            model: panel.results
                            currentIndex: 0
                            keyNavigationEnabled: true
                            boundsBehavior: Flickable.StopAtBounds
                            onModelChanged: currentIndex = 0
                            Keys.onReturnPressed: panel.launch(model, currentIndex)
                            Keys.onEnterPressed: panel.launch(model, currentIndex)
                            Keys.onEscapePressed: searchField.forceActiveFocus()
                            Keys.onUpPressed: {
                                if (currentIndex === 0)
                                    searchField.forceActiveFocus();
                                else
                                    decrementCurrentIndex();
                            }
                            delegate: MouseArea {
                                id: row
                                required property int index
                                required property var model
                                width: resultList.width
                                height: Kirigami.Units.gridUnit * (index === 0 ? 3.2 : 2.3)
                                hoverEnabled: true
                                Accessible.role: Accessible.Button
                                Accessible.name: model.display
                                onClicked: panel.launch(resultList.model, index)
                                onContainsMouseChanged: if (containsMouse) resultList.currentIndex = index
                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 1
                                    radius: 6
                                    color: Kirigami.Theme.textColor
                                    opacity: row.pressed ? 0.14 : (resultList.currentIndex === row.index ? 0.1
                                             : (row.containsMouse ? 0.07 : 0))
                                }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: Kirigami.Units.largeSpacing
                                    anchors.rightMargin: Kirigami.Units.largeSpacing
                                    spacing: Kirigami.Units.largeSpacing
                                    Kirigami.Icon {
                                        implicitWidth: row.index === 0 ? Kirigami.Units.iconSizes.medium
                                                                       : Kirigami.Units.iconSizes.smallMedium
                                        implicitHeight: implicitWidth
                                        source: row.model.decoration
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        PC3.Label {
                                            Layout.fillWidth: true
                                            text: row.model.display
                                            elide: Text.ElideRight
                                        }
                                        PC3.Label {
                                            Layout.fillWidth: true
                                            visible: text !== ""
                                            text: row.model.description || ""
                                            opacity: 0.65
                                            elide: Text.ElideRight
                                            font.pointSize: Kirigami.Theme.smallFont.pointSize
                                        }
                                    }
                                }
                            }
                            PlasmaExtras.PlaceholderMessage {
                                anchors.centerIn: parent
                                width: parent.width - Kirigami.Units.gridUnit * 2
                                visible: resultList.count === 0 && panel.searching
                                iconName: "edit-none"
                                text: i18n("No results for “%1”", searchField.text)
                            }
                        }
                    }
                }

                // The best match: big icon, name, kind and "Open".
                Rectangle {
                    Layout.fillWidth: true
                    Layout.minimumWidth: Kirigami.Units.gridUnit * 12
                    Layout.fillHeight: true
                    visible: resultList.count > 0
                    radius: 8
                    color: Qt.alpha(Kirigami.Theme.textColor, 0.04)
                    border.width: 1
                    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.08)
                    readonly property var best: resultList.currentItem ? resultList.currentItem.model : null

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.gridUnit * 1.5
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.topMargin: Kirigami.Units.gridUnit
                            implicitWidth: Kirigami.Units.iconSizes.huge
                            implicitHeight: Kirigami.Units.iconSizes.huge
                            source: parent.parent.best ? parent.parent.best.decoration : ""
                        }
                        PC3.Label {
                            Layout.fillWidth: true
                            text: parent.parent.best ? parent.parent.best.display : ""
                            horizontalAlignment: Text.AlignHCenter
                            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.3
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        PC3.Label {
                            Layout.fillWidth: true
                            text: parent.parent.best ? (parent.parent.best.description || i18n("App")) : ""
                            horizontalAlignment: Text.AlignHCenter
                            opacity: 0.65
                            elide: Text.ElideRight
                        }
                        Item { Layout.fillHeight: true }
                        PC3.Button {
                            Layout.alignment: Qt.AlignHCenter
                            icon.name: "window-new"
                            text: i18n("Open")
                            onClicked: panel.launch(panel.results, panel.bestIndex)
                        }
                    }
                }
            }
        }
    }
}
