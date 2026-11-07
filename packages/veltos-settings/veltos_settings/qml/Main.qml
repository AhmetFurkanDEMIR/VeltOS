/*
    VeltOS Settings: navigation pane on the left, the selected page on the
    right, as in Windows 11 Settings. `backend` (Python, app.py) provides
    the pages, texts, facts and actions.

    The window draws its own frame, as Windows 11 Settings does: the title
    bar holds the back button and the search box, and the background is
    Mica, the desktop picture blurred under the window colour (product
    owner, 2026-11-07). frame.py keeps clicks on the shadow going to the
    windows behind.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    property string pageId: "home"
    property string subPage: ""     // built-in page opened from a page (about, storage, ...)
    property string query: ""
    // Pages shown before this one, for the back button: {page, sub}.
    property var history: []

    readonly property bool maximized: visibility === Window.Maximized || visibility === Window.FullScreen
    readonly property int shadow: maximized ? 0 : 12
    readonly property bool canGoBack: history.length > 0 || query !== ""

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
        sub = sub || "";
        if (id !== pageId || sub !== subPage)
            history = history.concat([{ page: pageId, sub: subPage }]).slice(-50);
        search.text = "";
        pageId = id;
        subPage = sub;
        if (subPage !== "")
            backend.recordVisit(id, subPage);    // Home > Recommended settings
        content.contentItem.contentY = 0;
    }

    // The back button, Alt+Left and the mouse's back button: out of the
    // search results first, then to the pages shown before.
    function goBack() {
        if (query !== "") {
            search.text = "";
            return;
        }
        if (history.length === 0)
            return;
        const last = history[history.length - 1];
        history = history.slice(0, -1);
        pageId = last.page;
        subPage = last.sub;
        content.contentItem.contentY = 0;
    }

    function activate(item) {
        if (item.action)
            backend.runAction(item.action);
        else if (item.page)
            showPage(item.pageId || pageId, item.page);
    }

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }

    // 1120 x 740 inside the shadow.
    width: 1144
    height: 764
    minimumWidth: 904
    minimumHeight: 584
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: backend.text("app_title")

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
        "accessibility": accessibilityComponent, "pointer": pointerComponent,
        "searching": searchingComponent,
        "themes": themesComponent, "taskbar": taskbarComponent, "location": locationComponent,
        "hotspot": hotspotComponent, "veltosai": assistantComponent, "update": updateComponent
    })

    // `veltos-settings PAGE`: a navigation page or a built-in page.
    function showStartPage(start) {
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
    Component.onCompleted: {
        backend.refreshAccounts();
        showStartPage(backend.startPage);
        history = [];       // nothing to go back to when the window opens
    }

    Shortcut {
        sequences: [StandardKey.Find]
        onActivated: search.forceInputFocus()
    }
    Shortcut {
        sequences: [StandardKey.Back]
        onActivated: window.goBack()
    }

    // --- Shadow and resize borders -----------------------------------------------------
    Repeater {
        model: window.shadow
        delegate: Rectangle {
            required property int index
            anchors.fill: frame
            anchors.margins: -(index + 1)
            radius: frame.radius + index + 1
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(0, 0, 0, (Theme.dark ? 0.1 : 0.06) * Math.pow(1 - index / window.shadow, 2))
        }
    }
    component Edge: MouseArea {
        property int edges
        enabled: !window.maximized
        hoverEnabled: true
        z: 10
        onPressed: window.startSystemResize(edges)
    }
    readonly property int grip: 6
    Edge { edges: Qt.LeftEdge; cursorShape: Qt.SizeHorCursor
           x: window.shadow - grip; y: window.shadow + grip; width: 2 * grip; height: window.height - 2 * window.shadow - 2 * grip }
    Edge { edges: Qt.RightEdge; cursorShape: Qt.SizeHorCursor
           x: window.width - window.shadow - grip; y: window.shadow + grip; width: 2 * grip; height: window.height - 2 * window.shadow - 2 * grip }
    Edge { edges: Qt.TopEdge; cursorShape: Qt.SizeVerCursor
           x: window.shadow + grip; y: window.shadow - grip; width: window.width - 2 * window.shadow - 2 * grip; height: grip + 2 }
    Edge { edges: Qt.BottomEdge; cursorShape: Qt.SizeVerCursor
           x: window.shadow + grip; y: window.height - window.shadow - grip; width: window.width - 2 * window.shadow - 2 * grip; height: 2 * grip }
    Edge { edges: Qt.TopEdge | Qt.LeftEdge; cursorShape: Qt.SizeFDiagCursor
           x: window.shadow - grip; y: window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.TopEdge | Qt.RightEdge; cursorShape: Qt.SizeBDiagCursor
           x: window.width - window.shadow - grip; y: window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.BottomEdge | Qt.LeftEdge; cursorShape: Qt.SizeBDiagCursor
           x: window.shadow - grip; y: window.height - window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor
           x: window.width - window.shadow - grip; y: window.height - window.shadow - grip; width: 2 * grip; height: 2 * grip }

    Rectangle {
        id: frame
        objectName: "frame"
        anchors.fill: parent
        anchors.margins: window.shadow
        radius: window.maximized ? 0 : 8
        // Acrylic: KWin blurs the windows and desktop behind the frame
        // (acrylic.py); the colour comes from the layer below.
        color: backend.acrylic ? "transparent" : Theme.window
        clip: true

        // --- Mica, where KWin cannot blur behind the window -------------------------------
        // The desktop picture, blurred, under the window colour (Theme.micaTint).
        // Drawn larger than the window so the blur has picture at the edges, and
        // masked to the window's rounded shape.
        Item {
            id: mica
            readonly property int bleed: 48
            x: -bleed
            y: -bleed
            width: frame.width + 2 * bleed
            height: frame.height + 2 * bleed
            // Off with Personalization > Colours > Transparency effects, as on Windows.
            visible: !backend.acrylic && backend.transparency && picture.status === Image.Ready

            Image {
                id: picture
                anchors.fill: parent
                source: backend.acrylic ? "" : backend.micaImage
                sourceSize: Qt.size(480, 300)
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                visible: false
            }
            Item {
                id: micaMask
                anchors.fill: parent
                layer.enabled: true
                visible: false
                Rectangle {
                    x: mica.bleed
                    y: mica.bleed
                    width: frame.width
                    height: frame.height
                    radius: frame.radius
                }
            }
            MultiEffect {
                anchors.fill: parent
                source: picture
                autoPaddingEnabled: false
                blurEnabled: true
                blur: 1.0
                blurMax: 64
                saturation: 0.25
                maskEnabled: true
                maskSource: micaMask
                maskThresholdMin: 0.5
                maskSpreadAtMin: 1.0
            }
        }
        Rectangle {
            anchors.fill: parent
            radius: frame.radius
            color: backend.acrylic ? Theme.acrylicTint : (mica.visible ? Theme.micaTint : Theme.window)
        }

        TapHandler {
            acceptedButtons: Qt.BackButton
            onTapped: window.goBack()
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // --- Title bar ---------------------------------------------------------------
            Item {
                id: titleBar
                Layout.fillWidth: true
                Layout.preferredHeight: 48

                DragHandler { target: null; onActiveChanged: if (active) window.startSystemMove() }
                TapHandler { onDoubleTapped: window.toggleMaximized() }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    spacing: 6

                    Rectangle {
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 36
                        radius: 5
                        color: window.canGoBack && backHover.hovered ? Theme.hover : "transparent"
                        opacity: window.canGoBack ? 1 : 0.4
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.text("back")
                        Glyph { anchors.centerIn: parent; width: 16; height: 16; kind: "back"; lineWidth: 1.3 }
                        HoverHandler { id: backHover }
                        TapHandler {
                            enabled: window.canGoBack
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: window.goBack()
                        }
                    }
                    Kirigami.Icon {
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                        source: "veltos-settings"
                    }
                    Text {
                        Layout.leftMargin: 4
                        text: backend.text("app_title")
                        color: Theme.text
                        font.pixelSize: 12
                    }
                    Item { Layout.fillWidth: true }

                    component WindowButton: Rectangle {
                        id: wb
                        property string glyph
                        property string label
                        property bool danger: false
                        signal clicked()
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignTop
                        // The close button rounds the window's top right corner.
                        topRightRadius: danger && !window.maximized ? 8 : 0
                        color: wbHover.hovered ? (danger ? Theme.closeHover : Theme.hover) : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: label
                        Glyph { anchors.centerIn: parent; width: 12; height: 12; lineWidth: 1; kind: wb.glyph
                                color: wbHover.hovered && wb.danger ? "#FFFFFF" : Theme.text }
                        HoverHandler { id: wbHover }
                        TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: wb.clicked() }
                    }
                    WindowButton { glyph: "minimize"; label: backend.text("minimize"); onClicked: window.showMinimized() }
                    WindowButton { glyph: window.maximized ? "restore" : "maximize"
                                   label: window.maximized ? backend.text("restore_down") : backend.text("maximize")
                                   onClicked: window.toggleMaximized() }
                    WindowButton { glyph: "close"; label: backend.text("close"); danger: true; onClicked: window.close() }
                }

                // "Find a setting" in the middle of the title bar.
                SearchField {
                    id: search
                    anchors.centerIn: parent
                    width: Math.max(220, Math.min(520, titleBar.width - 2 * 190))
                    placeholder: backend.text("find_setting")
                    onTextChanged: {
                        window.query = text.trim();
                        content.contentItem.contentY = 0;
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                // --- Navigation pane -----------------------------------------------------
                ColumnLayout {
                    Layout.preferredWidth: 300
                    Layout.fillWidth: false
                    Layout.fillHeight: true
                    Layout.leftMargin: 10
                    Layout.topMargin: 6
                    Layout.bottomMargin: 12
                    spacing: 4

                    // The account, as at the top of Windows 11 Settings; opens Your info.
                    RowLayout {
                        Layout.leftMargin: 10
                        Layout.bottomMargin: 16
                        spacing: 14
                        Avatar {
                            size: 64
                            source: backend.accounts.me.icon || ""
                        }
                        ColumnLayout {
                            spacing: 1
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
                            // VeltOS' colour icons, as in Windows 11 Settings (catalog.py).
                            icon: Qt.resolvedUrl("icons/nav-" + modelData.id + ".svg")
                            text: modelData.title
                            selected: window.query === "" && window.pageId === modelData.id
                            onClicked: window.showPage(modelData.id, "")
                        }
                    }
                }

                // --- Page --------------------------------------------------------------------
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
                            Layout.leftMargin: 32
                            Layout.rightMargin: 36
                            Layout.topMargin: 10
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
                            Layout.leftMargin: 32
                            Layout.rightMargin: 36
                            Layout.bottomMargin: 36
                            sourceComponent: window.query !== "" ? searchComponent
                                             : window.subPage !== "" ? window.subPages[window.subPage]
                                             : window.pageId === "home" ? homeComponent
                                             : window.pageId === "update" ? updateComponent
                                             : itemsComponent
                        }
                    }
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
        id: updateComponent
        UpdatePage {
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
        id: pointerComponent
        MousePointerPage {
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
