/*
    VeltOS Settings: navigation pane on the left, the selected page on the
    right, as in Windows 11 Settings. `backend` (Python, app.py) provides
    the pages, texts, facts and actions.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ApplicationWindow {
    id: window

    property string pageId: "home"
    property string subPage: ""     // built-in page opened from a page (about, storage, ...)
    property string query: ""

    readonly property var pages: backend.pages
    readonly property var currentPage: pageById(pageId)
    readonly property string subPageTitle: {
        for (const p of pages) {
            for (const item of p.items) {
                if (item.page === subPage)
                    return item.title;
            }
        }
        return "";
    }

    function pageById(id) {
        for (const p of pages) {
            if (p.id === id)
                return p;
        }
        return null;
    }

    function showPage(id, sub) {
        search.text = "";
        pageId = id;
        subPage = sub || "";
        if (subPage !== "")
            backend.recordVisit(id, subPage);    // Home > Recommended settings
        content.contentItem.contentY = 0;
    }

    function activate(item) {
        if (item.action)
            backend.runAction(item.action);
        else if (item.page)
            showPage(item.pageId || pageId, item.page);
    }

    width: 1120
    height: 740
    minimumWidth: 880
    minimumHeight: 560
    visible: true
    title: backend.text("app_title")
    color: Theme.window

    // Built-in pages (catalog.BUILTIN_PAGES) and their components.
    readonly property var subPages: ({
        "about": aboutComponent, "storage": storageComponent,
        "windows-apps": windowsAppsComponent, "wifi": wifiComponent,
        "bluetooth": bluetoothComponent, "sound": soundComponent,
        "display": displayComponent, "background": backgroundComponent,
        "colours": coloursComponent, "datetime": dateTimeComponent,
        "notifications": notificationsComponent, "power": powerComponent,
        "nightlight": nightLightComponent, "multitasking": multitaskingComponent,
        "mouse": mouseComponent, "touchpad": touchpadComponent, "keyboard": keyboardComponent,
        "lockscreen": lockScreenComponent, "defaultapps": defaultAppsComponent,
        "startup": startupComponent, "yourinfo": yourInfoComponent, "signin": signInComponent,
        "otherusers": otherUsersComponent, "region": regionComponent,
        "accessibility": accessibilityComponent, "searching": searchingComponent,
        "themes": themesComponent, "taskbar": taskbarComponent, "location": locationComponent,
        "hotspot": hotspotComponent, "veltosai": assistantComponent
    })

    // `veltos-settings PAGE`: a navigation page or a built-in page.
    Component.onCompleted: {
        backend.refreshAccounts();
        const start = backend.startPage;
        if (pageById(start)) {
            showPage(start, "");
            return;
        }
        for (const p of pages) {
            for (const item of p.items) {
                if (item.page === start) {
                    showPage(p.id, start);
                    return;
                }
            }
        }
    }

    Shortcut {
        sequences: [StandardKey.Find]
        onActivated: search.forceActiveFocus()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- Navigation pane ---------------------------------------------
        ColumnLayout {
            Layout.preferredWidth: 300
            Layout.fillHeight: true
            Layout.leftMargin: 14
            Layout.topMargin: 18
            Layout.bottomMargin: 14
            spacing: 4

            // The account, as at the top of Windows 11 Settings; opens Your info.
            RowLayout {
                Layout.leftMargin: 6
                Layout.bottomMargin: 14
                spacing: 12
                Avatar {
                    size: 56
                    source: backend.accounts.me.icon || ""
                }
                ColumnLayout {
                    spacing: 0
                    Label {
                        text: backend.accounts.me.realName || backend.userName
                        color: Theme.text
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: backend.text("local_account")
                        color: Theme.subtext
                        font.pixelSize: 12
                    }
                }
                HoverHandler { cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: window.showPage("accounts", "yourinfo") }
            }

            SearchField {
                id: search
                Layout.fillWidth: true
                Layout.rightMargin: 6
                Layout.bottomMargin: 8
                placeholder: backend.text("find_setting")
                onTextChanged: {
                    window.query = text.trim();
                    content.contentItem.contentY = 0;
                }
            }

            ListView {
                id: nav
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 2
                boundsBehavior: Flickable.StopAtBounds
                model: window.pages
                delegate: NavItem {
                    required property var modelData
                    width: nav.width - 6
                    icon: modelData.icon
                    text: modelData.title
                    selected: window.query === "" && window.pageId === modelData.id
                    onClicked: window.showPage(modelData.id, "")
                }
            }

        }

        // --- Page ----------------------------------------------------------
        ScrollView {
            id: content
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: content.availableWidth
                spacing: 0

                // Title, with a breadcrumb for built-in sub pages.
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 36
                    Layout.rightMargin: 36
                    Layout.topMargin: 26
                    Layout.bottomMargin: 22
                    spacing: 10

                    Label {
                        text: window.query !== "" ? backend.text("search_results")
                              : (window.currentPage ? window.currentPage.title : "")
                        color: window.subPage !== "" && window.query === "" ? Theme.subtext : Theme.text
                        font.pixelSize: Theme.pageTitleSize
                        font.weight: Font.DemiBold
                        TapHandler {
                            enabled: window.subPage !== "" && window.query === ""
                            onTapped: window.showPage(window.pageId, "")
                        }
                        HoverHandler {
                            enabled: window.subPage !== "" && window.query === ""
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                    Label {
                        visible: window.subPage !== "" && window.query === ""
                        text: "›"
                        color: Theme.subtext
                        font.pixelSize: Theme.pageTitleSize
                    }
                    Label {
                        visible: window.subPage !== "" && window.query === ""
                        Layout.fillWidth: true
                        text: window.subPageTitle
                        color: Theme.text
                        font.pixelSize: Theme.pageTitleSize
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Item { Layout.fillWidth: window.subPage === "" || window.query !== "" }
                }

                Loader {
                    id: pageLoader
                    Layout.fillWidth: true
                    Layout.leftMargin: 36
                    Layout.rightMargin: 36
                    Layout.bottomMargin: 36
                    sourceComponent: window.query !== "" ? searchComponent
                                     : window.subPage !== "" ? window.subPages[window.subPage]
                                     : window.pageId === "home" ? homeComponent
                                     : itemsComponent
                }
            }
        }
    }

    Component {
        id: searchComponent
        SearchPage {
            query: window.query
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: homeComponent
        HomePage {
            onItemActivated: item => window.activate(item)
            onOpenSubPage: (pageId, sub) => window.showPage(pageId, sub)
        }
    }
    Component {
        id: itemsComponent
        ItemsPage {
            pageData: window.currentPage
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: aboutComponent
        AboutPage {}
    }
    Component {
        id: storageComponent
        StoragePage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: windowsAppsComponent
        WindowsAppsPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: wifiComponent
        WifiPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: assistantComponent
        AssistantPage {}
    }
    Component {
        id: hotspotComponent
        HotspotPage {}
    }
    Component {
        id: bluetoothComponent
        BluetoothPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: soundComponent
        SoundPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: displayComponent
        DisplayPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: backgroundComponent
        BackgroundPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: coloursComponent
        ColoursPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: dateTimeComponent
        DateTimePage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: notificationsComponent
        NotificationsPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: powerComponent
        PowerPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: nightLightComponent
        NightLightPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: multitaskingComponent
        MultitaskingPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: mouseComponent
        MousePage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: touchpadComponent
        MousePage {
            touchpad: true
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: keyboardComponent
        KeyboardPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: lockScreenComponent
        LockScreenPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: taskbarComponent
        TaskbarPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: defaultAppsComponent
        DefaultAppsPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: startupComponent
        StartupPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: yourInfoComponent
        YourInfoPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: signInComponent
        SignInPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: otherUsersComponent
        OtherUsersPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: regionComponent
        RegionPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: accessibilityComponent
        AccessibilityPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: themesComponent
        ThemesPage {
            onItemActivated: item => window.activate(item)
            onOpenSubPage: (pageId, sub) => window.showPage(pageId, sub)
        }
    }
    Component {
        id: searchingComponent
        SearchingPage {
            onItemActivated: item => window.activate(item)
        }
    }
    Component {
        id: locationComponent
        LocationPage {}
    }
}
