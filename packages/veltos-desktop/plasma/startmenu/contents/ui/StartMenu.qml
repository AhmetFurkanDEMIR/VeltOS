/*
    VeltOS Start menu popup (Windows 11 layout):

      [ search field                               ]
      Pinned                              All apps >
      [grid of pinned apps, 6 columns]
      Recommended
      [recent documents, 2 columns]
      ---------------------------------------------
      (avatar) User name                       (power)

    Typing searches, Esc steps back/closes, arrows and Enter navigate.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.components as KirigamiComponents
import org.kde.coreaddons as KCoreAddons
import org.kde.kcmutils as KCM

FocusScope {
    id: menu

    required property PlasmoidItem plasmoidItem

    // "home" or "allApps"; searching overrides both while the field has text.
    property string page: "home"
    readonly property bool searching: searchField.text.length > 0

    readonly property int pinnedColumns: 6
    readonly property int pinnedRows: 3

    readonly property var favoritesModel: plasmoidItem.rootModel.favoritesModel
    property var allAppsModel: null
    readonly property var searchResults: runnerModel.count > 0 ? runnerModel.modelForRow(0) : null

    Layout.minimumWidth: Kirigami.Units.gridUnit * 30
    Layout.minimumHeight: Kirigami.Units.gridUnit * 32
    Layout.preferredWidth: Kirigami.Units.gridUnit * 34
    Layout.preferredHeight: Kirigami.Units.gridUnit * 38

    Kicker.RunnerModel {
        id: runnerModel
        appletInterface: menu.plasmoidItem
        favoritesModel: menu.favoritesModel
        mergeResults: true
        query: searchField.text
    }

    KCoreAddons.KUser {
        id: kuser
    }

    // Lock / sign out / sleep / restart / shut down. Created only once the
    // root model has built its system favorites model: Plasma 6.3's
    // SystemModel::refresh() dereferences favoritesModel without a null
    // check, so a SystemModel created earlier crashed plasmashell as soon as
    // the session-management state arrived over D-Bus (found in VM testing).
    property var systemModel: null

    Component {
        id: systemModelComponent
        Kicker.SystemModel {}
    }

    function ensureSystemModel() {
        const favorites = plasmoidItem.rootModel.systemFavoritesModel;
        if (!systemModel && favorites) {
            systemModel = systemModelComponent.createObject(menu, { favoritesModel: favorites });
        }
    }

    function close() {
        plasmoidItem.expanded = false;
    }

    function reset() {
        searchField.text = "";
        page = "home";
        pinnedGrid.currentIndex = -1;
        searchField.forceActiveFocus();
    }

    // Launch row `index` of `model`; Plasma's models start the app/document.
    function launch(model, index) {
        if (model && index >= 0) {
            model.trigger(index, "", null);
            close();
        }
    }

    function launchBestMatch() {
        if (searching) {
            launch(searchResults, Math.max(searchList.currentIndex, 0));
        }
    }

    function refreshAllApps() {
        allAppsModel = plasmoidItem.rootModel.count > 0 ? plasmoidItem.rootModel.modelForRow(0) : null;
    }

    function goBack() {
        if (searching) {
            searchField.text = "";
        } else if (page !== "home") {
            page = "home";
        } else {
            close();
        }
        searchField.forceActiveFocus();
    }

    // Right-click menu for an item: its own actions plus Pin/Unpin to Start.
    function openActionMenu(visualParent, model, index, actionList, favoriteId) {
        let actions = actionList ? Array.from(actionList) : [];
        if (favoriteId && favoritesModel && favoritesModel.enabled) {
            const pinned = favoritesModel.isFavorite(favoriteId);
            if (actions.length > 0) {
                actions.push({ type: "separator" });
            }
            actions.push({
                text: pinned ? i18n("Unpin from Start") : i18n("Pin to Start"),
                icon: pinned ? "window-unpin" : "window-pin",
                actionId: pinned ? "_veltos_unpin" : "_veltos_pin",
                actionArgument: favoriteId,
            });
        }
        if (actions.length === 0) {
            return;
        }
        actionMenu.model = model;
        actionMenu.index = index;
        actionMenu.actionList = actions;
        actionMenu.menu.visualParent = visualParent;
        actionMenu.menu.openRelative();
    }

    Connections {
        target: menu.plasmoidItem
        function onExpandedChanged() {
            if (menu.plasmoidItem.expanded) {
                menu.reset();
            }
        }
    }

    Connections {
        target: menu.plasmoidItem.rootModel
        function onCountChanged() {
            menu.refreshAllApps();
        }
        function onSystemFavoritesModelChanged() {
            menu.ensureSystemModel();
        }
    }

    Component.onCompleted: {
        plasmoidItem.rootModel.refresh();
        refreshAllApps();
        ensureSystemModel();
        searchField.forceActiveFocus();
    }

    ActionMenu {
        id: actionMenu
        onPinRequested: favoriteId => menu.favoritesModel.addFavorite(favoriteId)
        onUnpinRequested: favoriteId => menu.favoritesModel.removeFavorite(favoriteId)
        onCloseRequested: menu.close()
    }

    Keys.onEscapePressed: goBack()

    // --- Reusable item visuals ---------------------------------------------

    // Rounded hover/selection backdrop used by every clickable item.
    // (Inline components cannot see ids of this file, so no `menu.` here.)
    component Highlight: Rectangle {
        property bool hovered: false
        property bool selected: false
        property bool pressed: false
        radius: Kirigami.Units.cornerRadius !== undefined ? Kirigami.Units.cornerRadius : 6
        color: Kirigami.Theme.textColor
        opacity: pressed ? 0.14 : (selected ? 0.11 : (hovered ? 0.07 : 0))
        Behavior on opacity {
            NumberAnimation { duration: Kirigami.Units.shortDuration }
        }
    }

    component SectionTitle: PC3.Label {
        font.weight: Font.DemiBold
        Layout.fillWidth: true
    }

    // --- Layout ------------------------------------------------------------

    // Near-opaque surface: with blur (real GPUs) it reads like Windows'
    // acrylic; without blur (VMs, software rendering) text stays readable.
    Rectangle {
        anchors.fill: parent
        radius: Kirigami.Units.cornerRadius !== undefined ? Kirigami.Units.cornerRadius * 2 : 12
        color: Kirigami.Theme.backgroundColor
        opacity: 0.94
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Kirigami.Units.gridUnit
            Layout.bottomMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing * 2

            PlasmaExtras.SearchField {
                id: searchField
                Layout.fillWidth: true
                focus: true
                placeholderText: i18n("Search for apps, settings and documents")

                Keys.onDownPressed: event => {
                    if (menu.searching) {
                        searchList.forceActiveFocus();
                        searchList.currentIndex = 0;
                    } else if (menu.page === "allApps") {
                        allAppsList.forceActiveFocus();
                        allAppsList.currentIndex = 0;
                    } else {
                        pinnedGrid.forceActiveFocus();
                        pinnedGrid.currentIndex = 0;
                    }
                }
                Keys.onReturnPressed: menu.launchBestMatch()
                Keys.onEnterPressed: menu.launchBestMatch()
                Keys.onEscapePressed: menu.goBack()
            }

            // Home: pinned grid + recommended documents
            ColumnLayout {
                visible: !menu.searching && menu.page === "home"
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Kirigami.Units.largeSpacing

                RowLayout {
                    Layout.fillWidth: true
                    SectionTitle {
                        text: i18n("Pinned")
                    }
                    PC3.ToolButton {
                        id: allAppsButton
                        text: i18n("All apps")
                        // Arrow after the text, like Windows.
                        contentItem: RowLayout {
                            spacing: Kirigami.Units.smallSpacing
                            PC3.Label {
                                text: allAppsButton.text
                            }
                            Kirigami.Icon {
                                implicitWidth: Kirigami.Units.iconSizes.small
                                implicitHeight: Kirigami.Units.iconSizes.small
                                source: "go-next-symbolic"
                            }
                        }
                        onClicked: {
                            menu.page = "allApps";
                            searchField.forceActiveFocus();
                        }
                    }
                }

                GridView {
                    id: pinnedGrid
                    Layout.fillWidth: true
                    Layout.preferredHeight: cellHeight * menu.pinnedRows
                    cellWidth: Math.floor(width / menu.pinnedColumns)
                    cellHeight: Kirigami.Units.gridUnit * 5
                    clip: true
                    model: menu.favoritesModel
                    currentIndex: -1
                    keyNavigationEnabled: true
                    boundsBehavior: Flickable.StopAtBounds
                    highlightFollowsCurrentItem: false

                    Keys.onReturnPressed: menu.launch(model, currentIndex)
                    Keys.onEnterPressed: menu.launch(model, currentIndex)
                    Keys.onEscapePressed: menu.goBack()
                    Keys.onUpPressed: event => {
                        if (currentIndex < menu.pinnedColumns) {
                            searchField.forceActiveFocus();
                        } else {
                            moveCurrentIndexUp();
                        }
                    }

                    delegate: MouseArea {
                        id: tile
                        required property int index
                        required property var model

                        width: pinnedGrid.cellWidth
                        height: pinnedGrid.cellHeight
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        Accessible.name: model.display
                        Accessible.role: Accessible.Button

                        onClicked: mouse => {
                            if (mouse.button === Qt.RightButton) {
                                menu.openActionMenu(tile, pinnedGrid.model, index,
                                                    model.actionList, model.favoriteId);
                            } else {
                                menu.launch(pinnedGrid.model, index);
                            }
                        }

                        Highlight {
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.smallSpacing / 2
                            hovered: tile.containsMouse
                            pressed: tile.pressed
                            selected: pinnedGrid.activeFocus && pinnedGrid.currentIndex === tile.index
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.smallSpacing
                            spacing: Kirigami.Units.smallSpacing

                            Kirigami.Icon {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.topMargin: Kirigami.Units.smallSpacing
                                implicitWidth: Kirigami.Units.iconSizes.medium
                                implicitHeight: Kirigami.Units.iconSizes.medium
                                source: tile.model.decoration
                            }
                            PC3.Label {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: tile.model.display
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignTop
                                wrapMode: Text.Wrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                                font: Kirigami.Theme.smallFont
                            }
                        }
                    }
                }

                SectionTitle {
                    text: i18n("Recommended")
                    Layout.topMargin: Kirigami.Units.largeSpacing
                }

                GridView {
                    id: recommendedGrid
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cellWidth: Math.floor(width / 2)
                    cellHeight: Kirigami.Units.gridUnit * 3
                    clip: true
                    interactive: false
                    model: menu.plasmoidItem.recentDocsModel

                    delegate: MouseArea {
                        id: doc
                        required property int index
                        required property var model

                        // Show only the rows that fit; no scrolling, like Windows.
                        visible: Math.floor(index / 2) < Math.floor(recommendedGrid.height / recommendedGrid.cellHeight)
                        width: recommendedGrid.cellWidth
                        height: recommendedGrid.cellHeight
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: mouse => {
                            if (mouse.button === Qt.RightButton) {
                                menu.openActionMenu(doc, recommendedGrid.model, index,
                                                    model.actionList, "");
                            } else {
                                menu.launch(recommendedGrid.model, index);
                            }
                        }

                        Highlight {
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.smallSpacing / 2
                            hovered: doc.containsMouse
                            pressed: doc.pressed
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Kirigami.Units.largeSpacing
                            anchors.rightMargin: Kirigami.Units.largeSpacing
                            spacing: Kirigami.Units.largeSpacing

                            Kirigami.Icon {
                                implicitWidth: Kirigami.Units.iconSizes.medium
                                implicitHeight: Kirigami.Units.iconSizes.medium
                                source: doc.model.decoration
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                PC3.Label {
                                    Layout.fillWidth: true
                                    text: doc.model.display
                                    elide: Text.ElideMiddle
                                }
                                PC3.Label {
                                    Layout.fillWidth: true
                                    text: doc.model.description || ""
                                    visible: text.length > 0
                                    elide: Text.ElideMiddle
                                    font: Kirigami.Theme.smallFont
                                    opacity: 0.7
                                }
                            }
                        }
                    }

                    PC3.Label {
                        anchors.centerIn: parent
                        width: parent.width - Kirigami.Units.gridUnit * 4
                        visible: recommendedGrid.count === 0
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                        opacity: 0.6
                        text: i18n("Your recently opened files will appear here.")
                    }
                }
            }

            // All apps: alphabetical list with letter headers
            ColumnLayout {
                visible: !menu.searching && menu.page === "allApps"
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Kirigami.Units.largeSpacing

                RowLayout {
                    Layout.fillWidth: true
                    SectionTitle {
                        text: i18n("All apps")
                    }
                    PC3.ToolButton {
                        text: i18n("Back")
                        icon.name: "go-previous-symbolic"
                        onClicked: {
                            menu.page = "home";
                            searchField.forceActiveFocus();
                        }
                    }
                }

                PC3.ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: allAppsList
                        model: menu.allAppsModel
                        currentIndex: -1
                        keyNavigationEnabled: true
                        boundsBehavior: Flickable.StopAtBounds
                        reuseItems: true
                        section.property: "display"
                        section.criteria: ViewSection.FirstCharacter
                        section.delegate: PC3.Label {
                            required property string section
                            width: ListView.view.width
                            leftPadding: Kirigami.Units.largeSpacing
                            topPadding: Kirigami.Units.largeSpacing
                            bottomPadding: Kirigami.Units.smallSpacing
                            text: section.toUpperCase()
                            font.weight: Font.DemiBold
                            opacity: 0.8
                        }

                        Keys.onReturnPressed: menu.launch(model, currentIndex)
                        Keys.onEnterPressed: menu.launch(model, currentIndex)
                        Keys.onEscapePressed: menu.goBack()

                        delegate: AppRow {
                            id: appRow
                            view: allAppsList
                            onActivated: menu.launch(allAppsList.model, appRow.index)
                            onContextMenuRequested: menu.openActionMenu(appRow, allAppsList.model, appRow.index,
                                                                        appRow.model.actionList, appRow.model.favoriteId)
                        }
                    }
                }
            }

            // Search results
            ColumnLayout {
                visible: menu.searching
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Kirigami.Units.largeSpacing

                SectionTitle {
                    text: i18n("Best match")
                    visible: searchList.count > 0
                }

                PC3.ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: searchList
                        model: menu.searchResults
                        currentIndex: 0
                        keyNavigationEnabled: true
                        boundsBehavior: Flickable.StopAtBounds

                        Keys.onReturnPressed: menu.launch(model, currentIndex)
                        Keys.onEnterPressed: menu.launch(model, currentIndex)
                        Keys.onEscapePressed: menu.goBack()
                        Keys.onUpPressed: event => {
                            if (currentIndex === 0) {
                                searchField.forceActiveFocus();
                            } else {
                                decrementCurrentIndex();
                            }
                        }

                        delegate: AppRow {
                            id: resultRow
                            view: searchList
                            showDescription: true
                            // First result is highlighted: Enter in the field launches it.
                            selected: searchList.currentIndex === resultRow.index
                            onActivated: menu.launch(searchList.model, resultRow.index)
                            onContextMenuRequested: menu.openActionMenu(resultRow, searchList.model, resultRow.index,
                                                                        resultRow.model.actionList, resultRow.model.favoriteId)
                        }

                        PlasmaExtras.PlaceholderMessage {
                            anchors.centerIn: parent
                            width: parent.width - Kirigami.Units.gridUnit * 4
                            visible: searchList.count === 0 && menu.searching
                            iconName: "edit-none"
                            text: i18n("No results for “%1”", searchField.text)
                        }
                    }
                }
            }
        }

        // Footer: user on the left, power on the right
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 3.2
            color: Qt.alpha(Kirigami.Theme.textColor, 0.04)

            Kirigami.Separator {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                opacity: 0.6
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.gridUnit * 1.5
                anchors.rightMargin: Kirigami.Units.gridUnit * 1.5

                MouseArea {
                    id: userButton
                    Layout.fillHeight: true
                    Layout.topMargin: Kirigami.Units.smallSpacing
                    Layout.bottomMargin: Kirigami.Units.smallSpacing
                    Layout.preferredWidth: userRow.implicitWidth + Kirigami.Units.largeSpacing * 2
                    hoverEnabled: true
                    Accessible.name: kuser.fullName
                    Accessible.role: Accessible.Button
                    onClicked: accountMenu.openRelative()

                    Highlight {
                        anchors.fill: parent
                        hovered: userButton.containsMouse
                        pressed: userButton.pressed
                    }

                    RowLayout {
                        id: userRow
                        anchors.centerIn: parent
                        spacing: Kirigami.Units.largeSpacing

                        KirigamiComponents.Avatar {
                            implicitWidth: Kirigami.Units.iconSizes.medium
                            implicitHeight: Kirigami.Units.iconSizes.medium
                            name: kuser.fullName
                            source: kuser.faceIconUrl
                        }
                        PC3.Label {
                            text: kuser.fullName || kuser.loginName
                        }
                    }

                    PlasmaExtras.Menu {
                        id: accountMenu
                        visualParent: userButton
                        placement: PlasmaExtras.Menu.TopPosedLeftAlignedPopup

                        PlasmaExtras.MenuItem {
                            text: i18n("Change account settings")
                            icon: "system-users"
                            onClicked: {
                                KCM.KCMLauncher.openSystemSettings("kcm_users");
                                menu.close();
                            }
                        }
                    }

                    // Lock and sign out from Plasma's session model.
                    Instantiator {
                        model: menu.systemModel
                        delegate: PlasmaExtras.MenuItem {
                            required property int index
                            required property var model
                            visible: ["lock-screen", "logout"].includes(model.favoriteId)
                            text: model.display
                            icon: model.decoration
                            onClicked: menu.systemModel.trigger(index, "", null)
                        }
                        onObjectAdded: (index, object) => accountMenu.addMenuItem(object)
                        onObjectRemoved: (index, object) => accountMenu.removeMenuItem(object)
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                PC3.ToolButton {
                    id: powerButton
                    icon.name: "system-shutdown"
                    display: PC3.AbstractButton.IconOnly
                    text: i18n("Power")
                    PC3.ToolTip.text: text
                    PC3.ToolTip.visible: hovered
                    PC3.ToolTip.delay: Kirigami.Units.toolTipDelay
                    onClicked: powerMenu.openRelative()

                    PlasmaExtras.Menu {
                        id: powerMenu
                        visualParent: powerButton
                        placement: PlasmaExtras.Menu.TopPosedRightAlignedPopup
                    }

                    Instantiator {
                        model: menu.systemModel
                        delegate: PlasmaExtras.MenuItem {
                            required property int index
                            required property var model
                            visible: ["suspend", "reboot", "shutdown"].includes(model.favoriteId)
                            text: model.display
                            icon: model.decoration
                            onClicked: menu.systemModel.trigger(index, "", null)
                        }
                        onObjectAdded: (index, object) => powerMenu.addMenuItem(object)
                        onObjectRemoved: (index, object) => powerMenu.removeMenuItem(object)
                    }
                }
            }
        }
    }
}
