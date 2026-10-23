// VeltOS Store window, Microsoft Store layout: a navigation rail on the
// left (Home, Apps, Gaming, Library at the bottom), the search box at the
// top, the page in a rounded pane; an app's page opens over it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 860
    minimumHeight: 560
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    property string page: backend.startPage   // home | apps | games | library | search
    property string query: ""
    property var history: []         // app ids, for Back
    property string openApp: ""

    function showPage(id) {
        page = id;
        history = [];
        openApp = "";
    }
    function showApp(appId) {
        if (openApp !== "") {
            history = history.concat([openApp]);
        }
        openApp = appId;
    }
    function goBack() {
        if (history.length > 0) {
            openApp = history[history.length - 1];
            history = history.slice(0, history.length - 1);
        } else {
            openApp = "";
        }
    }

    readonly property var navItems: [
        {"id": "home", "icon": "go-home-symbolic", "text": backend.texts.home},
        {"id": "apps", "icon": "view-app-grid-symbolic", "text": backend.texts.apps},
        {"id": "games", "icon": "input-gaming-symbolic", "text": backend.texts.games},
    ]

    component NavButton: MouseArea {
        id: nav
        property string pageId
        property string iconName
        property string label
        readonly property bool selected: window.page === pageId && window.openApp === ""
        // Wide enough for "Uygulamalar" in bold beside the selection bar
        // (product owner, 2026-10-22: the bar covered its first letter).
        Layout.preferredWidth: 84
        Layout.preferredHeight: 60
        Layout.alignment: Qt.AlignHCenter
        hoverEnabled: true
        onClicked: window.showPage(pageId)
        Accessible.role: Accessible.PageTab
        Accessible.name: label

        Rectangle {
            anchors.fill: parent
            radius: Theme.radius
            color: nav.selected ? Theme.navSelected : (nav.containsMouse ? Theme.navHover : "transparent")
        }
        // The selection bar, as the Microsoft Store draws it: a short pill
        // at the left edge, level with the icon; the label keeps clear of it.
        Rectangle {
            visible: nav.selected
            x: 2
            y: navContent.y + navIcon.y + (navIcon.height - height) / 2
            width: 3
            height: 16
            radius: 1.5
            color: Theme.accent
        }
        ColumnLayout {
            id: navContent
            anchors.centerIn: parent
            width: nav.width - 16
            spacing: 4
            Kirigami.Icon {
                id: navIcon
                Layout.alignment: Qt.AlignHCenter
                implicitWidth: 20
                implicitHeight: 20
                source: nav.iconName
                isMask: true
                color: nav.selected ? Theme.accent : Theme.text
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: nav.label
                color: Theme.text
                font.pixelSize: 11
                font.weight: nav.selected ? Font.DemiBold : Font.Normal
                elide: Text.ElideRight
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Navigation rail.
        ColumnLayout {
            Layout.preferredWidth: 96
            Layout.fillHeight: true
            Layout.topMargin: 12
            Layout.bottomMargin: 12
            spacing: 6
            Repeater {
                model: window.navItems
                NavButton {
                    required property var modelData
                    pageId: modelData.id
                    iconName: modelData.icon
                    label: modelData.text
                }
            }
            Item { Layout.fillHeight: true }
            NavButton {
                pageId: "library"
                iconName: "library-symbolic"
                label: backend.texts.library
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Search box, centred above the page.
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                Rectangle {
                    id: searchBox
                    anchors.centerIn: parent
                    width: Math.min(560, parent.width - 48)
                    height: 36
                    radius: Theme.smallRadius
                    color: search.activeFocus ? Theme.card : Theme.control
                    border.width: 1
                    border.color: Theme.cardBorder
                    Rectangle {
                        visible: search.activeFocus
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 1
                        height: 2
                        color: Theme.accent
                    }
                    TextInput {
                        id: search
                        // Like a Windows text box: in the Tab order, the text cursor over it and
                        // (in a layout) the full height of its box. A plain TextInput has neither.
                        activeFocusOnTab: true
                        HoverHandler { cursorShape: Qt.IBeamCursor }
                        anchors.left: parent.left
                        anchors.right: searchIcon.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        verticalAlignment: TextInput.AlignVCenter
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        color: Theme.text
                        font.pixelSize: Theme.bodySize + 1
                        clip: true
                        selectByMouse: true
                        Accessible.name: backend.texts.search
                        onTextChanged: searchTimer.restart()
                        Keys.onReturnPressed: searchTimer.triggered()
                        Keys.onEscapePressed: text = ""
                        Text {
                            visible: search.text === ""
                            anchors.verticalCenter: parent.verticalCenter
                            text: backend.texts.search
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize + 1
                        }
                    }
                    Kirigami.Icon {
                        id: searchIcon
                        anchors.right: parent.right
                        anchors.rightMargin: 12
                        anchors.verticalCenter: parent.verticalCenter
                        implicitWidth: 16
                        implicitHeight: 16
                        source: "edit-find-symbolic"
                        isMask: true
                        color: Theme.subtext
                    }
                    Timer {
                        id: searchTimer
                        interval: 250
                        onTriggered: {
                            const text = search.text.trim();
                            if (text === "") {
                                if (window.page === "search") {
                                    window.showPage("home");
                                }
                                return;
                            }
                            window.query = text;
                            window.page = "search";
                            window.history = [];
                            window.openApp = "";
                        }
                    }
                }
            }

            // The page, in a pane with a rounded top-left corner.
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                Rectangle {
                    anchors.fill: parent
                    anchors.rightMargin: -Theme.radius
                    anchors.bottomMargin: -Theme.radius
                    radius: Theme.radius
                    color: Theme.pane
                    border.width: 1
                    border.color: Theme.cardBorder
                }

                BusyIndicator {
                    anchors.centerIn: parent
                    running: backend.loading
                    visible: running
                }
                Text {
                    anchors.centerIn: parent
                    width: Math.min(480, parent.width - 48)
                    visible: !backend.loading && backend.appCount === 0
                    text: backend.texts.no_catalog
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize + 1
                    wrapMode: Text.Wrap
                    horizontalAlignment: Text.AlignHCenter
                }

                StackLayout {
                    anchors.fill: parent
                    visible: !backend.loading && backend.appCount > 0 && window.openApp === ""
                    currentIndex: ["home", "apps", "games", "library", "search"].indexOf(window.page)
                    HomePage {
                        onOpened: appId => window.showApp(appId)
                        onBrowse: category => window.showPage(category === "games" ? "games" : "apps")
                    }
                    GridPage {
                        title: backend.texts.apps
                        showCategories: true
                        source: ""
                        onOpened: appId => window.showApp(appId)
                    }
                    GridPage {
                        title: backend.texts.games
                        source: "games"
                        onOpened: appId => window.showApp(appId)
                    }
                    LibraryPage {
                        onOpened: appId => window.showApp(appId)
                    }
                    GridPage {
                        title: backend.texts.results_for.replace("%1", window.query)
                        searchText: window.query
                        onOpened: appId => window.showApp(appId)
                    }
                }

                Loader {
                    anchors.fill: parent
                    active: window.openApp !== ""
                    sourceComponent: AppPage {
                        appId: window.openApp
                        onBack: window.goBack()
                        onOpened: appId => window.showApp(appId)
                    }
                }
            }
        }
    }
}
