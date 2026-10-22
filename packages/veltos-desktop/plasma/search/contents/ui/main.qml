/*
    VeltOS Search: the search box of the Windows 11 taskbar. Clicking it
    opens Windows 11's search window (not Start): a search field at the
    top, the most used apps as "Top apps" while it is empty, and while
    typing the results on the left with the best match on the right
    ("Open"). Results come from Plasma's runners (apps, documents, the
    calculator, ...; not KDE's settings modules), as in Start.

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
        // What Windows' search finds: apps, documents, folders, the web, a
        // calculation, sessions and power. Not KDE's System Settings modules
        // (krunner_systemsettings: the product owner must never see KDE's
        // settings, 2026-10-22), nor shell commands, process killing, KWin
        // commands or activities. KF6 runner ids are the plugin file names.
        runners: ["krunner_services", "krunner_recentdocuments", "krunner_placesrunner", "baloosearch",
                  "locations", "krunner_webshortcuts", "calculator", "windows", "krunner_sessions",
                  "krunner_powerdevil"]
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

        // Windows 11's taskbar search box: it looks the same while its
        // window is open; only the pointer over it brightens it a little.
        Rectangle {
            id: pill
            anchors.centerIn: parent
            width: box.compact ? Math.min(parent.width, parent.height) - Kirigami.Units.smallSpacing * 2
                               : parent.width - Kirigami.Units.smallSpacing * 2
            height: Math.min(parent.height - Kirigami.Units.smallSpacing * 3, Kirigami.Units.gridUnit * 2)
            radius: height / 2
            color: Kirigami.Theme.backgroundColor
            opacity: box.containsMouse ? 1 : 0.85
            border.width: 1
            border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g,
                                  Kirigami.Theme.textColor.b, 0.1)
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
        // Windows lists a handful of results; the rest would need scrolling.
        readonly property int maxResults: 12
        readonly property int resultCount: results ? Math.min(results.count, maxResults) : 0
        // The highlighted result (keyboard or pointer); 0 is the best match.
        property int current: 0
        // Counts every row the Repeater makes or drops: the model is reset
        // on every keystroke and its rows are made anew with the same
        // count, so `best` must be re-read then (it held a dead row and the
        // card stayed empty, VM 2026-10-22).
        property int rowsGeneration: 0
        readonly property var best: {
            const generation = rowsGeneration;
            if (resultCount <= 0 || resultRows.count <= 0)
                return null;
            return resultRows.itemAt(Math.min(current, resultCount - 1, resultRows.count - 1));
        }

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
        function launchCurrent() {
            if (panel.resultCount > 0)
                launch(panel.results, Math.min(panel.current, panel.resultCount - 1));
        }

        onResultsChanged: current = 0
        onResultCountChanged: current = Math.min(current, Math.max(0, resultCount - 1))

        Connections {
            target: root
            function onExpandedChanged() {
                searchField.text = "";
                panel.current = 0;
                if (root.expanded)
                    searchField.forceActiveFocus();
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.gridUnit * 1.5
            spacing: Kirigami.Units.largeSpacing

            // The search field of Windows 11's search window: a plain
            // rounded box with the accent line along its bottom edge while
            // it has the focus (no frame around it).
            PlasmaExtras.SearchField {
                id: searchField
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 2.4
                placeholderText: i18n("Search for apps, settings and documents")
                background: Rectangle {
                    radius: 4
                    color: Kirigami.Theme.backgroundColor
                    border.width: 1
                    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.12)
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.margins: 1
                        height: searchField.activeFocus ? 2 : 1
                        color: searchField.activeFocus ? Kirigami.Theme.highlightColor
                                                       : Qt.alpha(Kirigami.Theme.textColor, 0.3)
                    }
                }
                onTextChanged: runnerModel.query = text
                onAccepted: panel.launchCurrent()
                Keys.onDownPressed: {
                    if (panel.resultCount > 0)
                        panel.current = Math.min(panel.current + 1, panel.resultCount - 1);
                }
                Keys.onUpPressed: panel.current = Math.max(0, panel.current - 1)
                Keys.onEscapePressed: {
                    if (text !== "")
                        text = "";
                    else
                        root.expanded = false;
                }
            }

            // Empty field: the most used apps as "Top apps".
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
                        visible: panel.resultCount > 0
                    }
                    // One row under the other (a Column: rows cannot overlap,
                    // as they did in a list view whose rows changed height,
                    // 2026-10-22). The first row, the best match, is taller.
                    Column {
                        Layout.fillWidth: true
                        spacing: 2
                        Repeater {
                            id: resultRows
                            model: panel.results
                            onItemAdded: (index, item) => panel.rowsGeneration++
                            onItemRemoved: (index, item) => panel.rowsGeneration++
                            delegate: MouseArea {
                                id: row
                                required property int index
                                required property var model
                                readonly property bool shown: index < panel.maxResults
                                readonly property bool first: index === 0
                                readonly property string title: model.display || ""
                                readonly property string subtitle: model.description || ""
                                readonly property var decoration: model.decoration
                                visible: shown
                                width: parent.width
                                height: shown ? Kirigami.Units.gridUnit * (first ? 3.2 : 2.3) : 0
                                hoverEnabled: true
                                Accessible.role: Accessible.Button
                                Accessible.name: title
                                onClicked: panel.launch(panel.results, index)
                                onContainsMouseChanged: if (containsMouse) panel.current = index
                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 1
                                    radius: 6
                                    color: Kirigami.Theme.textColor
                                    opacity: row.pressed ? 0.14 : (panel.current === row.index ? 0.1
                                             : (row.containsMouse ? 0.07 : 0))
                                }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: Kirigami.Units.largeSpacing
                                    anchors.rightMargin: Kirigami.Units.largeSpacing
                                    spacing: Kirigami.Units.largeSpacing
                                    Kirigami.Icon {
                                        implicitWidth: row.first ? Kirigami.Units.iconSizes.medium
                                                                 : Kirigami.Units.iconSizes.smallMedium
                                        implicitHeight: implicitWidth
                                        source: row.decoration
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        PC3.Label {
                                            Layout.fillWidth: true
                                            text: row.title
                                            elide: Text.ElideRight
                                        }
                                        PC3.Label {
                                            Layout.fillWidth: true
                                            visible: text !== ""
                                            text: row.subtitle
                                            opacity: 0.65
                                            elide: Text.ElideRight
                                            font.pointSize: Kirigami.Theme.smallFont.pointSize
                                        }
                                    }
                                }
                            }
                        }
                    }
                    PlasmaExtras.PlaceholderMessage {
                        Layout.fillWidth: true
                        Layout.topMargin: Kirigami.Units.gridUnit * 4
                        visible: panel.resultCount === 0 && panel.searching
                        iconName: "edit-none"
                        text: i18n("No results for “%1”", searchField.text)
                    }
                    Item { Layout.fillHeight: true }
                }

                // The best match: big icon, name, kind and "Open".
                Rectangle {
                    Layout.fillWidth: true
                    Layout.minimumWidth: Kirigami.Units.gridUnit * 12
                    Layout.fillHeight: true
                    visible: panel.resultCount > 0
                    radius: 8
                    color: Qt.alpha(Kirigami.Theme.textColor, 0.04)
                    border.width: 1
                    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.08)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.gridUnit * 1.5
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.topMargin: Kirigami.Units.gridUnit
                            implicitWidth: Kirigami.Units.iconSizes.huge
                            implicitHeight: Kirigami.Units.iconSizes.huge
                            source: panel.best ? panel.best.decoration : ""
                        }
                        PC3.Label {
                            Layout.fillWidth: true
                            text: panel.best ? panel.best.title : ""
                            horizontalAlignment: Text.AlignHCenter
                            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.3
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        PC3.Label {
                            Layout.fillWidth: true
                            text: panel.best ? (panel.best.subtitle || i18n("App")) : ""
                            horizontalAlignment: Text.AlignHCenter
                            opacity: 0.65
                            elide: Text.ElideRight
                        }
                        Item { Layout.fillHeight: true }
                        PC3.Button {
                            Layout.alignment: Qt.AlignHCenter
                            icon.name: "window-new"
                            text: i18n("Open")
                            onClicked: panel.launchCurrent()
                        }
                    }
                }
            }
        }
    }
}
