/*
    VeltOS Start menu popup, in the layout of Windows 11's Start (2025):

      [ search field                                         ]
      ---- one scrolling page --------------------------------
      Pinned                                        Show all >
      [pinned apps, 8 columns, 2 rows until "Show all"]
      Recommended                                   Show all >
      [recent documents, 3 columns, 2 rows]
      All                                     View: Category v
      [categories (4 per row, 2x2 icons each) | grid | list]
      --------------------------------------------------------
      (avatar) User name                                (power)

    A category's first three icons start their apps; the card itself opens
    the category. Categories come from the apps' desktop files
    (/usr/libexec/veltos/start-categories); like Windows, categories with
    fewer than three apps join "Other". Typing searches, Esc steps
    back/closes, arrows and Enter navigate.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.components as KirigamiComponents
import org.kde.coreaddons as KCoreAddons
import org.kde.kcmutils as KCM

FocusScope {
    id: menu

    required property PlasmoidItem plasmoidItem

    // "home", "recommended" or "category"; searching overrides them while
    // the field has text.
    property string page: "home"
    readonly property bool searching: searchField.text.length > 0
    property bool pinnedExpanded: false
    readonly property string allView: ["category", "grid", "list"].includes(Plasmoid.configuration.allAppsView)
                                      ? Plasmoid.configuration.allAppsView : "category"

    readonly property int pinnedColumns: 8
    readonly property int pinnedRows: pinnedExpanded ? Math.max(1, Math.ceil(pinnedGrid.count / pinnedColumns)) : 2
    readonly property int categoryColumns: 4

    readonly property var favoritesModel: plasmoidItem.rootModel.favoritesModel
    property var allAppsModel: null
    readonly property var searchResults: runnerModel.count > 0 ? runnerModel.modelForRow(0) : null

    // All apps as [{row, name, id, icon}] (alphabetical, from allAppsModel)
    // and grouped into categories [{key, title, apps}].
    property var apps: []
    property var groups: []
    property var categoryOf: ({})
    property var openGroup: null

    readonly property var categoryTitles: ({
        "productivity": i18n("Productivity"),
        "office": i18n("Office"),
        "social": i18n("Social"),
        "creativity": i18n("Creativity"),
        "entertainment": i18n("Entertainment"),
        "games": i18n("Games"),
        "education": i18n("Education"),
        "developer": i18n("Developer tools"),
        "utilities": i18n("Utilities & tools"),
        "other": i18n("Other"),
    })
    readonly property var categoryOrder: ["productivity", "office", "social", "creativity", "entertainment", "games",
                                          "education", "developer", "utilities", "other"]

    Layout.minimumWidth: Kirigami.Units.gridUnit * 40
    Layout.minimumHeight: Kirigami.Units.gridUnit * 36
    Layout.preferredWidth: Kirigami.Units.gridUnit * 46
    Layout.preferredHeight: Kirigami.Units.gridUnit * 47

    Kicker.RunnerModel {
        id: runnerModel
        appletInterface: menu.plasmoidItem
        favoritesModel: menu.favoritesModel
        mergeResults: true
        query: searchField.text
        // As the taskbar's search: apps, documents, folders, the calculator,
        // sessions and power; not KDE's settings modules (product owner,
        // 2026-10-22) and not KDE's web shortcuts ("Search DuckDuckGo for
        // ..." as an app): the web is the Google row under the results.
        runners: ["krunner_services", "krunner_recentdocuments", "krunner_placesrunner", "baloosearch",
                  "locations", "calculator", "windows", "krunner_sessions", "krunner_powerdevil"]
    }

    // The Google row under the search results is chosen (keyboard).
    property bool webSelected: false

    function searchWeb() {
        const query = searchField.text.trim();
        if (query !== "") {
            Qt.openUrlExternally("https://www.google.com/search?q=" + encodeURIComponent(query));
            close();
        }
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
        pinnedExpanded = false;
        openGroup = null;
        pinnedGrid.currentIndex = -1;
        homeView.contentItem.contentY = 0;
        searchField.forceActiveFocus();
        loadCategories();
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
            if (webSelected || searchList.count === 0)
                searchWeb();
            else
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
            openGroup = null;
        } else {
            close();
        }
        searchField.forceActiveFocus();
    }

    // --- All apps: list and categories ---------------------------------------

    function loadCategories() {
        categorySource.connectSource("/usr/libexec/veltos/start-categories");
    }

    function rebuildApps() {
        const list = [];
        for (let i = 0; i < appData.count; ++i) {
            const item = appData.itemAt(i);
            if (item && item.name) {
                list.push({ row: i, name: item.name, id: item.appId, icon: item.icon });
            }
        }
        apps = list;
        rebuildGroups();
    }

    function rebuildGroups() {
        const buckets = {};
        for (const app of apps) {
            const key = categoryOf[app.id] || "other";
            (buckets[key] = buckets[key] || []).push(app);
        }
        // Windows needs three apps for a category; VeltOS' catalogue is
        // small, so every category with an app is shown and "Other" holds
        // only apps without one (Media Player alone in Entertainment was
        // landing in Other; product owner, 2026-10-22).
        const result = [];
        let other = buckets["other"] || [];
        for (const key of categoryOrder) {
            if (key === "other" || !buckets[key]) {
                continue;
            }
            result.push({ key: key, title: categoryTitles[key], apps: buckets[key] });
        }
        if (other.length > 0) {
            other.sort((a, b) => a.name.localeCompare(b.name));
            result.push({ key: "other", title: categoryTitles["other"], apps: other });
        }
        groups = result;
    }

    function setAllView(view) {
        Plasmoid.configuration.allAppsView = view;
    }

    function openCategory(group) {
        openGroup = group;
        page = "category";
        searchField.forceActiveFocus();
    }

    function launchApp(row) {
        launch(allAppsModel, row);
    }

    function appContextMenu(visualParent, row) {
        const item = appData.itemAt(row);
        if (item) {
            openActionMenu(visualParent, allAppsModel, row, item.actions(), item.appId);
        }
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

    P5Support.DataSource {
        id: categorySource
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => {
            disconnectSource(source);
            try {
                menu.categoryOf = JSON.parse(data["stdout"] || "{}");
            } catch (error) {
                menu.categoryOf = {};
            }
            menu.rebuildGroups();
        }
    }

    // One invisible item per app: names, ids and icons for the "All"
    // section, read from Plasma's apps model.
    Item {
        visible: false
        Repeater {
            id: appData
            model: menu.allAppsModel
            delegate: Item {
                required property var model
                readonly property string name: model.display || ""
                readonly property string appId: model.favoriteId || ""
                readonly property var icon: model.decoration
                function actions() {
                    return model.actionList;
                }
            }
            onItemAdded: Qt.callLater(menu.rebuildApps)
            onItemRemoved: Qt.callLater(menu.rebuildApps)
        }
    }

    // Users who signed in before VeltOS had its own apps have the KDE apps
    // they replace pinned; swap them once, in the same place (the flags
    // remember it, so a user may pin them again). Calculator is pinned
    // once, as in Windows.
    function replacePinned(oldId, newId, done) {
        if (Plasmoid.configuration[done] || !favoritesModel || !favoritesModel.enabled) {
            return;
        }
        if (favoritesModel.isFavorite(oldId)) {
            const at = favoritesModel.favorites ? favoritesModel.favorites.indexOf(oldId) : -1;
            favoritesModel.removeFavorite(oldId);
            if (!favoritesModel.isFavorite(newId)) {
                favoritesModel.addFavorite(newId, at);
            }
        }
        Plasmoid.configuration[done] = true;
    }

    function pinOnce(id, done) {
        if (Plasmoid.configuration[done] || !favoritesModel || !favoritesModel.enabled) {
            return;
        }
        if (!favoritesModel.isFavorite(id)) {
            favoritesModel.addFavorite(id);
        }
        Plasmoid.configuration[done] = true;
    }

    function pinFileExplorer() {
        replacePinned("org.kde.dolphin.desktop", "veltos-explorer.desktop", "explorerPinned");
        replacePinned("org.kde.discover.desktop", "veltos-store.desktop", "storePinned");
        replacePinned("org.kde.spectacle.desktop", "veltos-snip.desktop", "snipPinned");
        replacePinned("org.kde.ark.desktop", "veltos-archive.desktop", "archivePinned");
        replacePinned("org.kde.kwrite.desktop", "veltos-notepad.desktop", "notepadPinned");
        replacePinned("org.kde.gwenview.desktop", "veltos-photos.desktop", "photosPinned");
        replacePinned("org.kde.okular.desktop", "veltos-pdf.desktop", "pdfPinned");
        pinOnce("veltos-calculator.desktop", "calculatorPinned");
        pinOnce("veltos-clock.desktop", "clockPinned");
        pinOnce("veltos-mail.desktop", "mailPinned");
    }

    // The pinned apps model may not be ready when Start first opens; try
    // again until the swaps are done (VM test: Discover stayed pinned).
    Timer {
        interval: 1000
        repeat: true
        running: !(Plasmoid.configuration.explorerPinned && Plasmoid.configuration.storePinned
                   && Plasmoid.configuration.snipPinned && Plasmoid.configuration.calculatorPinned
                   && Plasmoid.configuration.archivePinned)
        onTriggered: menu.pinFileExplorer()
    }

    Component.onCompleted: {
        plasmoidItem.rootModel.refresh();
        refreshAllApps();
        ensureSystemModel();
        pinFileExplorer();
        loadCategories();
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
    // (Inline components cannot see ids of this file, so no `menu.` in them.)

    // Rounded hover/selection backdrop used by every clickable item.
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

    // Windows 11's small "Show all >" / "< Back" buttons: a light filled
    // rectangle with a hairline border, small text and a chevron.
    component SmallButton: MouseArea {
        id: smallButton
        property string text
        property string iconName: "go-next-symbolic"
        property bool iconFirst: false
        property bool flat: false
        implicitWidth: smallButtonRow.implicitWidth + Kirigami.Units.largeSpacing * 2
        implicitHeight: Math.round(Kirigami.Units.gridUnit * 1.6)
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.name: text
        Accessible.role: Accessible.Button
        Keys.onReturnPressed: clicked(null)
        Keys.onSpacePressed: clicked(null)

        Rectangle {
            anchors.fill: parent
            radius: 4
            color: Qt.alpha(Kirigami.Theme.textColor, smallButton.pressed ? 0.03
                            : (smallButton.containsMouse ? 0.09 : (smallButton.flat ? 0 : 0.06)))
            border.width: smallButton.flat && !smallButton.activeFocus ? 0 : 1
            border.color: Qt.alpha(Kirigami.Theme.textColor, smallButton.activeFocus ? 0.5 : 0.08)
        }
        RowLayout {
            id: smallButtonRow
            anchors.centerIn: parent
            spacing: Kirigami.Units.smallSpacing
            layoutDirection: smallButton.iconFirst ? Qt.RightToLeft : Qt.LeftToRight
            PC3.Label {
                text: smallButton.text
                font: Kirigami.Theme.smallFont
            }
            Kirigami.Icon {
                implicitWidth: Math.round(Kirigami.Units.iconSizes.small * 0.75)
                implicitHeight: implicitWidth
                source: smallButton.iconName
            }
        }
    }

    // An app as Windows shows it in Pinned and in the grid views: icon above
    // a one-line name.
    component AppTile: MouseArea {
        id: appTile
        property string name
        property var icon
        property bool selected: false
        signal launchRequested()
        signal menuRequested()
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        Accessible.name: name
        Accessible.role: Accessible.Button
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton) {
                menuRequested();
            } else {
                launchRequested();
            }
        }

        Highlight {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing / 2
            hovered: appTile.containsMouse
            pressed: appTile.pressed
            selected: appTile.selected
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            Kirigami.Icon {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: Kirigami.Units.smallSpacing * 1.5
                implicitWidth: Kirigami.Units.iconSizes.medium
                implicitHeight: Kirigami.Units.iconSizes.medium
                source: appTile.icon
            }
            PC3.Label {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: appTile.name
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignTop
                maximumLineCount: 1
                elide: Text.ElideRight
                font: Kirigami.Theme.smallFont
            }
        }
    }

    // A category of the "All" section: a rounded card with 2x2 big icons;
    // with more than four apps the fourth place shows four small icons and
    // opens the category, like Windows 11.
    component CategoryTile: ColumnLayout {
        id: categoryTile
        property var group
        property real cardSize: 140
        signal openRequested()
        signal launchRequested(int row)
        signal menuRequested(Item item, int row)
        spacing: Kirigami.Units.smallSpacing

        readonly property var groupApps: group ? group.apps : []
        readonly property int bigCount: groupApps.length > 4 ? 3 : groupApps.length
        readonly property real slot: cardSize * 0.36

        MouseArea {
            id: card
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: categoryTile.cardSize
            Layout.preferredHeight: categoryTile.cardSize
            hoverEnabled: true
            Accessible.name: categoryTile.group ? categoryTile.group.title : ""
            Accessible.role: Accessible.Button
            onClicked: categoryTile.openRequested()

            Rectangle {
                anchors.fill: parent
                radius: 8
                color: Qt.alpha(Kirigami.Theme.textColor, card.containsMouse ? 0.08 : 0.045)
                border.width: 1
                border.color: Qt.alpha(Kirigami.Theme.textColor, 0.06)
                Behavior on color {
                    ColorAnimation { duration: Kirigami.Units.shortDuration }
                }
            }

            Grid {
                anchors.centerIn: parent
                columns: 2
                spacing: categoryTile.cardSize * 0.08

                Repeater {
                    model: categoryTile.bigCount
                    delegate: MouseArea {
                        id: bigIcon
                        required property int index
                        readonly property var app: categoryTile.groupApps[index] || ({ name: "", icon: "", row: -1 })
                        width: categoryTile.slot
                        height: categoryTile.slot
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        Accessible.name: app.name
                        Accessible.role: Accessible.Button
                        PC3.ToolTip.text: app.name
                        PC3.ToolTip.visible: containsMouse
                        PC3.ToolTip.delay: Kirigami.Units.toolTipDelay
                        onClicked: mouse => {
                            if (mouse.button === Qt.RightButton) {
                                categoryTile.menuRequested(bigIcon, app.row);
                            } else {
                                categoryTile.launchRequested(app.row);
                            }
                        }
                        Highlight {
                            anchors.fill: parent
                            anchors.margins: -2
                            hovered: bigIcon.containsMouse
                            pressed: bigIcon.pressed
                        }
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            width: Math.round(categoryTile.slot * 0.78)
                            height: width
                            source: bigIcon.app.icon
                        }
                    }
                }

                // Fourth place: the next four apps, small.
                Item {
                    visible: categoryTile.groupApps.length > 4
                    width: categoryTile.slot
                    height: categoryTile.slot
                    Grid {
                        anchors.centerIn: parent
                        columns: 2
                        spacing: categoryTile.slot * 0.08
                        Repeater {
                            model: Math.min(4, Math.max(0, categoryTile.groupApps.length - 3))
                            delegate: Kirigami.Icon {
                                required property int index
                                width: Math.round(categoryTile.slot * 0.38)
                                height: width
                                source: categoryTile.groupApps[3 + index] ? categoryTile.groupApps[3 + index].icon : ""
                            }
                        }
                    }
                }
            }
        }

        PC3.Label {
            Layout.fillWidth: true
            text: categoryTile.group ? categoryTile.group.title : ""
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            font: Kirigami.Theme.smallFont
        }
    }

    // --- Layout ------------------------------------------------------------

    // A light tint over Plasma's popup background, which is see-through
    // with blur ("acrylic", like Windows 11's Start) and solid without the
    // blur effect (software rendering), so the text stays readable. The
    // tint used to be 94 % opaque and hid the acrylic (product owner,
    // 2026-10-21).
    Rectangle {
        anchors.fill: parent
        radius: Kirigami.Units.cornerRadius !== undefined ? Kirigami.Units.cornerRadius * 2 : 12
        color: Kirigami.Theme.backgroundColor
        opacity: 0.35
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        PlasmaExtras.SearchField {
            id: searchField
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.gridUnit * 1.6
            Layout.bottomMargin: Kirigami.Units.largeSpacing
            implicitHeight: Math.round(Kirigami.Units.gridUnit * 2.2)
            focus: true
            placeholderText: i18n("Search for apps, settings and documents")
            // Rounded "pill" field like Windows 11's Start search.
            background: Rectangle {
                Kirigami.Theme.colorSet: Kirigami.Theme.View
                Kirigami.Theme.inherit: false
                radius: height / 2
                color: Kirigami.Theme.backgroundColor
                border.width: searchField.activeFocus ? 2 : 1
                border.color: searchField.activeFocus ? Kirigami.Theme.highlightColor
                                                      : Qt.alpha(Kirigami.Theme.textColor, 0.14)
            }

            onTextChanged: menu.webSelected = false
            Keys.onDownPressed: event => {
                if (menu.searching) {
                    searchList.forceActiveFocus();
                    searchList.currentIndex = 0;
                    menu.webSelected = searchList.count === 0;
                } else if (menu.page === "home") {
                    pinnedGrid.forceActiveFocus();
                    pinnedGrid.currentIndex = 0;
                }
            }
            Keys.onReturnPressed: menu.launchBestMatch()
            Keys.onEnterPressed: menu.launchBestMatch()
            Keys.onEscapePressed: menu.goBack()
        }

        // Home: Pinned, Recommended and All on one scrolling page
        PC3.ScrollView {
            id: homeView
            visible: !menu.searching && menu.page === "home"
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            PC3.ScrollBar.horizontal.policy: PC3.ScrollBar.AlwaysOff

            ColumnLayout {
                id: home
                width: homeView.availableWidth
                spacing: Kirigami.Units.largeSpacing

                // Pinned
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    SectionTitle {
                        text: i18n("Pinned")
                    }
                    SmallButton {
                        visible: pinnedGrid.count > menu.pinnedColumns * 2
                        flat: true
                        text: menu.pinnedExpanded ? i18n("Show less") : i18n("Show all")
                        iconName: menu.pinnedExpanded ? "go-up-symbolic" : "go-next-symbolic"
                        onClicked: menu.pinnedExpanded = !menu.pinnedExpanded
                    }
                }

                GridView {
                    id: pinnedGrid
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2
                    Layout.preferredHeight: cellHeight * Math.min(menu.pinnedRows, Math.max(1, Math.ceil(count / menu.pinnedColumns)))
                    cellWidth: Math.floor(width / menu.pinnedColumns)
                    cellHeight: Math.round(Kirigami.Units.gridUnit * 4.4)
                    clip: true
                    interactive: false
                    model: menu.favoritesModel
                    currentIndex: -1
                    keyNavigationEnabled: true
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

                    delegate: AppTile {
                        id: pinnedTile
                        required property int index
                        required property var model
                        width: pinnedGrid.cellWidth
                        height: pinnedGrid.cellHeight
                        name: model.display
                        icon: model.decoration
                        selected: pinnedGrid.activeFocus && pinnedGrid.currentIndex === index
                        onLaunchRequested: menu.launch(pinnedGrid.model, index)
                        onMenuRequested: menu.openActionMenu(pinnedTile, pinnedGrid.model, index,
                                                             model.actionList, model.favoriteId)
                    }
                }

                // Recommended
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    SectionTitle {
                        text: i18n("Recommended")
                    }
                    SmallButton {
                        visible: recommendedGrid.count > 0
                        flat: true
                        text: i18n("Show all")
                        onClicked: {
                            menu.page = "recommended";
                            searchField.forceActiveFocus();
                        }
                    }
                }

                GridView {
                    id: recommendedGrid
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2
                    Layout.preferredHeight: count > 0 ? cellHeight * Math.min(2, Math.ceil(count / 3))
                                                      : Kirigami.Units.gridUnit * 3
                    cellWidth: Math.floor(width / 3)
                    cellHeight: Math.round(Kirigami.Units.gridUnit * 2.9)
                    clip: true
                    interactive: false
                    model: menu.plasmoidItem.recentDocsModel

                    delegate: MouseArea {
                        id: doc
                        required property int index
                        required property var model

                        // Two rows, like Windows; the rest is behind "Show all".
                        visible: index < 6
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
                                    font: Kirigami.Theme.smallFont
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

                // All
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    SectionTitle {
                        text: i18n("All")
                    }
                    SmallButton {
                        id: viewButton
                        objectName: "viewButton"
                        flat: true
                        text: i18n("View: %1", menu.allView === "grid" ? i18n("Grid")
                                    : (menu.allView === "list" ? i18n("List") : i18n("Category")))
                        iconName: "go-down-symbolic"
                        onClicked: viewMenu.openRelative()

                        PlasmaExtras.Menu {
                            id: viewMenu
                            visualParent: viewButton
                            placement: PlasmaExtras.Menu.BottomPosedRightAlignedPopup
                            PlasmaExtras.MenuItem {
                                text: i18n("Category")
                                icon: menu.allView === "category" ? "checkmark-symbolic" : ""
                                onClicked: menu.setAllView("category")
                            }
                            PlasmaExtras.MenuItem {
                                text: i18n("Grid")
                                icon: menu.allView === "grid" ? "checkmark-symbolic" : ""
                                onClicked: menu.setAllView("grid")
                            }
                            PlasmaExtras.MenuItem {
                                text: i18n("List")
                                icon: menu.allView === "list" ? "checkmark-symbolic" : ""
                                onClicked: menu.setAllView("list")
                            }
                        }
                    }
                }

                // Category view: four cards a row, left-aligned like Windows
                Grid {
                    id: categoryGrid
                    readonly property real cellWidth: (width - columnSpacing * (columns - 1)) / columns
                    visible: menu.allView === "category"
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2.6
                    Layout.bottomMargin: Kirigami.Units.gridUnit
                    columns: menu.categoryColumns
                    columnSpacing: Kirigami.Units.gridUnit * 1.2
                    rowSpacing: Kirigami.Units.gridUnit

                    Repeater {
                        model: menu.allView === "category" ? menu.groups : []
                        delegate: CategoryTile {
                            required property var modelData
                            width: categoryGrid.cellWidth
                            group: modelData
                            cardSize: Math.min(Kirigami.Units.gridUnit * 8.8, categoryGrid.cellWidth)
                            onOpenRequested: menu.openCategory(modelData)
                            onLaunchRequested: row => menu.launchApp(row)
                            onMenuRequested: (item, row) => menu.appContextMenu(item, row)
                        }
                    }
                }

                // Grid view: every app, alphabetical
                GridLayout {
                    id: allGrid
                    visible: menu.allView === "grid"
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2
                    Layout.bottomMargin: Kirigami.Units.gridUnit
                    columns: menu.pinnedColumns
                    columnSpacing: 0
                    rowSpacing: 0
                    uniformCellWidths: true

                    Repeater {
                        model: menu.allView === "grid" ? menu.apps : []
                        delegate: AppTile {
                            id: gridTile
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.round(Kirigami.Units.gridUnit * 4.4)
                            name: modelData.name
                            icon: modelData.icon
                            onLaunchRequested: menu.launchApp(modelData.row)
                            onMenuRequested: menu.appContextMenu(gridTile, modelData.row)
                        }
                    }
                }

                // List view: every app with letter headers
                ColumnLayout {
                    visible: menu.allView === "list"
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.gridUnit * 2
                    Layout.rightMargin: Kirigami.Units.gridUnit * 2
                    Layout.bottomMargin: Kirigami.Units.gridUnit
                    spacing: 0

                    Repeater {
                        model: menu.allView === "list" ? menu.apps : []
                        delegate: ColumnLayout {
                            id: listEntry
                            required property int index
                            required property var modelData
                            readonly property string letter: modelData.name.charAt(0).toUpperCase()
                            Layout.fillWidth: true
                            spacing: 0

                            PC3.Label {
                                visible: listEntry.index === 0
                                         || menu.apps[listEntry.index - 1].name.charAt(0).toUpperCase() !== listEntry.letter
                                leftPadding: Kirigami.Units.largeSpacing
                                topPadding: Kirigami.Units.largeSpacing
                                bottomPadding: Kirigami.Units.smallSpacing
                                text: listEntry.letter
                                font.weight: Font.DemiBold
                                opacity: 0.8
                            }
                            MouseArea {
                                id: listRow
                                Layout.fillWidth: true
                                Layout.preferredHeight: Kirigami.Units.gridUnit * 2.2
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                Accessible.name: listEntry.modelData.name
                                Accessible.role: Accessible.Button
                                onClicked: mouse => {
                                    if (mouse.button === Qt.RightButton) {
                                        menu.appContextMenu(listRow, listEntry.modelData.row);
                                    } else {
                                        menu.launchApp(listEntry.modelData.row);
                                    }
                                }
                                Highlight {
                                    anchors.fill: parent
                                    hovered: listRow.containsMouse
                                    pressed: listRow.pressed
                                }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: Kirigami.Units.largeSpacing
                                    anchors.rightMargin: Kirigami.Units.largeSpacing
                                    spacing: Kirigami.Units.largeSpacing
                                    Kirigami.Icon {
                                        implicitWidth: Kirigami.Units.iconSizes.smallMedium
                                        implicitHeight: Kirigami.Units.iconSizes.smallMedium
                                        source: listEntry.modelData.icon
                                    }
                                    PC3.Label {
                                        Layout.fillWidth: true
                                        text: listEntry.modelData.name
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // One category, opened from its card
        ColumnLayout {
            visible: !menu.searching && menu.page === "category"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: Kirigami.Units.gridUnit * 2
            Layout.rightMargin: Kirigami.Units.gridUnit * 2
            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.gridUnit * 0.6
                Layout.rightMargin: Kirigami.Units.gridUnit * 0.6
                Layout.topMargin: Kirigami.Units.largeSpacing
                SectionTitle {
                    text: menu.openGroup ? menu.openGroup.title : ""
                }
                SmallButton {
                    text: i18n("Back")
                    iconName: "go-previous-symbolic"
                    iconFirst: true
                    onClicked: menu.goBack()
                }
            }

            PC3.ScrollView {
                id: categoryView
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth

                GridLayout {
                    width: categoryView.availableWidth
                    columns: menu.pinnedColumns
                    columnSpacing: 0
                    rowSpacing: 0
                    uniformCellWidths: true
                    Repeater {
                        model: menu.page === "category" && menu.openGroup ? menu.openGroup.apps : []
                        delegate: AppTile {
                            id: categoryApp
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.round(Kirigami.Units.gridUnit * 4.4)
                            name: modelData.name
                            icon: modelData.icon
                            onLaunchRequested: menu.launchApp(modelData.row)
                            onMenuRequested: menu.appContextMenu(categoryApp, modelData.row)
                        }
                    }
                }
            }
        }

        // "Show all" behind Recommended: every recent document in one list.
        ColumnLayout {
            visible: !menu.searching && menu.page === "recommended"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: Kirigami.Units.gridUnit * 2
            Layout.rightMargin: Kirigami.Units.gridUnit * 2
            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.gridUnit * 0.6
                Layout.rightMargin: Kirigami.Units.gridUnit * 0.6
                Layout.topMargin: Kirigami.Units.largeSpacing
                SectionTitle {
                    text: i18n("Recommended")
                }
                SmallButton {
                    text: i18n("Back")
                    iconName: "go-previous-symbolic"
                    iconFirst: true
                    onClicked: menu.goBack()
                }
            }

            PC3.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ListView {
                    id: recentList
                    model: menu.page === "recommended" ? menu.plasmoidItem.recentDocsModel : null
                    currentIndex: -1
                    keyNavigationEnabled: true
                    boundsBehavior: Flickable.StopAtBounds

                    Keys.onReturnPressed: menu.launch(model, currentIndex)
                    Keys.onEnterPressed: menu.launch(model, currentIndex)
                    Keys.onEscapePressed: menu.goBack()

                    delegate: AppRow {
                        id: recentRow
                        view: recentList
                        showDescription: true
                        onActivated: menu.launch(recentList.model, recentRow.index)
                        onContextMenuRequested: menu.openActionMenu(recentRow, recentList.model, recentRow.index,
                                                                    recentRow.model.actionList, "")
                    }
                }
            }
        }

        // Search results
        ColumnLayout {
            visible: menu.searching
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: Kirigami.Units.gridUnit * 2
            Layout.rightMargin: Kirigami.Units.gridUnit * 2
            spacing: Kirigami.Units.largeSpacing

            SectionTitle {
                Layout.leftMargin: Kirigami.Units.gridUnit * 0.6
                text: i18n("Best match")
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

                    Keys.onReturnPressed: menu.launchBestMatch()
                    Keys.onEnterPressed: menu.launchBestMatch()
                    Keys.onEscapePressed: menu.goBack()
                    Keys.onDownPressed: event => {
                        if (currentIndex >= count - 1)
                            menu.webSelected = true;
                        else
                            incrementCurrentIndex();
                    }
                    Keys.onUpPressed: event => {
                        if (menu.webSelected && count > 0) {
                            menu.webSelected = false;
                        } else if (currentIndex <= 0) {
                            menu.webSelected = false;
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
                        selected: searchList.currentIndex === resultRow.index && !menu.webSelected
                        onActivated: menu.launch(searchList.model, resultRow.index)
                        onContextMenuRequested: menu.openActionMenu(resultRow, searchList.model, resultRow.index,
                                                                    resultRow.model.actionList, resultRow.model.favoriteId)
                    }

                    // Search the web with Google: under the results with its
                    // own heading, the best match when nothing else is found.
                    footer: ColumnLayout {
                        width: searchList.width
                        spacing: Kirigami.Units.smallSpacing
                        SectionTitle {
                            Layout.leftMargin: Kirigami.Units.gridUnit * 0.6
                            Layout.topMargin: Kirigami.Units.largeSpacing
                            visible: searchList.count > 0
                            text: i18n("Search the web")
                        }
                        AppRow {
                            objectName: "webRow"
                            index: -1
                            view: searchList
                            showDescription: true
                            model: ({ display: searchField.text.trim(), description: i18n("Search with Google"),
                                      decoration: Qt.resolvedUrl("../images/web-search.svg") })
                            selected: menu.webSelected || searchList.count === 0
                            onActivated: menu.searchWeb()
                            onContainsMouseChanged: if (containsMouse && searchList.count > 0) menu.webSelected = true
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
                anchors.leftMargin: Kirigami.Units.gridUnit * 2.4
                anchors.rightMargin: Kirigami.Units.gridUnit * 2.4

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

                        // Without a picture: the VeltOS default account
                        // picture (veltos-desktop), not coloured initials.
                        KirigamiComponents.Avatar {
                            implicitWidth: Kirigami.Units.iconSizes.medium
                            implicitHeight: Kirigami.Units.iconSizes.medium
                            name: kuser.fullName
                            source: kuser.faceIconUrl.toString() !== "" ? kuser.faceIconUrl
                                    : "file:///usr/share/veltos/faces/default.png"
                            initialsMode: KirigamiComponents.Avatar.InitialsMode.UseIcon
                            color: Qt.alpha(Kirigami.Theme.textColor, 0.45)
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
                            // Windows' wording: "Sign out", not Plasma's "Log Out".
                            text: model.favoriteId === "logout" ? i18n("Sign out") : model.display
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
