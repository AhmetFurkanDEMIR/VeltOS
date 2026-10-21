/*
    VeltOS PDF Reader: a modern PDF reader layout. Title bar with the menu,
    the Home tab and one tab per open document; Home lists the recent
    files; a document shows its pages with the side panels, the quick tool
    rail and the floating page and zoom bar (DocumentView.qml).

    The window draws its own frame and shadow (frame.py keeps clicks on the
    shadow going to the windows behind).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "."

ApplicationWindow {
    id: window

    readonly property bool fullScreen: visibility === Window.FullScreen
    readonly property bool maximized: visibility === Window.Maximized || fullScreen
    readonly property int shadow: maximized ? 0 : 12
    // `count`: follow the Repeater creating the views (see AGENTS.md).
    readonly property var currentView: backend.currentIndex > 0 && docs.count >= backend.currentIndex
                                       ? docs.itemAt(backend.currentIndex - 1) : null
    property bool readMode: false

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }
    function run(action) {
        const v = currentView;
        if (action === "open") openDialog.open();
        else if (action === "print" && v) backend.printDocument(v.path, v.password);
        else if (action === "properties" && v) properties.showFor(v);
        else if (action === "folder" && v) backend.showInFolder(v.path);
        else if (action === "close-tab" && backend.currentIndex > 0) backend.closeTab(backend.currentIndex);
        else if (action === "read-mode") readMode = !readMode;
        else if (action === "full-screen") fullScreen ? showNormal() : showFullScreen();
        else if (action === "exit") Qt.quit();
        else if (action.indexOf("recent:") === 0) backend.openPath(action.slice(7), "");
    }

    width: 1200
    height: 800
    minimumWidth: 640
    minimumHeight: 420
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: currentView ? currentView.path.split("/").pop() + " - " + backend.texts.app_title : backend.texts.app_title

    Connections {
        target: backend
        function onMessage(text) { messageBox.ask(backend.texts.app_title, text, [{ text: backend.texts.ok, action: "ok" }]); }
        function onPasswordNeeded(path, wrong) { passwordDialog.ask(path, wrong); }
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
            border.color: Qt.rgba(0, 0, 0, (Theme.dark ? 0.22 : 0.075) * Math.pow(1 - index / window.shadow, 2))
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
        anchors.fill: parent
        anchors.margins: window.shadow
        radius: window.maximized ? 0 : 8
        color: Theme.window
        border.width: window.maximized ? 0 : 1
        border.color: Theme.dark ? "#3A3C4A" : "#C9CDD8"
        clip: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: frame.border.width
            spacing: 0

            // --- Title bar: menu, Home, document tabs, caption buttons ------------------------
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                visible: !window.fullScreen

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    spacing: 2

                    Rectangle {
                        id: menuButton
                        implicitWidth: 40; implicitHeight: 34; radius: 4
                        color: menuHover.hovered ? Theme.hover : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.menu
                        Glyph { anchors.centerIn: parent; width: 16; height: 16; kind: "menu" }
                        HoverHandler { id: menuHover }
                        TapHandler { onTapped: appMenu.openAt(menuButton, 0, menuButton.height + 4) }
                    }

                    component Tab: Item {
                        id: tab
                        property string title
                        property string glyph
                        property bool current: false
                        property bool closable: true
                        signal activated()
                        signal closed()
                        Layout.alignment: Qt.AlignBottom
                        Layout.preferredHeight: 36
                        Layout.preferredWidth: closable ? Math.min(220, Math.max(140, label.implicitWidth + 70))
                                                        : label.implicitWidth + 56
                        Accessible.role: Accessible.PageTab
                        Accessible.name: title
                        Rectangle {
                            anchors.fill: parent
                            anchors.bottomMargin: tab.current ? -1 : 4
                            radius: 8
                            color: tab.current ? Theme.content : (tabHover.hovered ? Theme.hover : "transparent")
                            Rectangle { visible: tab.current; anchors.left: parent.left; anchors.right: parent.right
                                        anchors.bottom: parent.bottom; height: 8; color: Theme.content }
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 6
                            anchors.bottomMargin: tab.current ? 0 : 4
                            spacing: 8
                            Glyph { Layout.preferredWidth: 14; Layout.preferredHeight: 14; kind: tab.glyph
                                    color: tab.glyph === "document" ? "#D93A2B" : Theme.text }
                            Text { id: label; Layout.fillWidth: true; text: tab.title; color: Theme.text
                                   font.pixelSize: Theme.smallFont; elide: Text.ElideRight }
                            Rectangle {
                                visible: tab.closable && (tab.current || tabHover.hovered)
                                Layout.preferredWidth: 24; Layout.preferredHeight: 22; radius: 4
                                color: xHover.hovered ? Theme.pressed : "transparent"
                                Accessible.role: Accessible.Button
                                Accessible.name: backend.texts.close_tab
                                Glyph { anchors.centerIn: parent; width: 9; height: 9; kind: "close" }
                                HoverHandler { id: xHover }
                                TapHandler { onTapped: tab.closed() }
                            }
                        }
                        HoverHandler { id: tabHover }
                        TapHandler { onTapped: tab.activated() }
                        TapHandler { acceptedButtons: Qt.MiddleButton; onTapped: if (tab.closable) tab.closed() }
                    }

                    Tab {
                        title: backend.texts.home
                        glyph: "home"
                        closable: false
                        current: backend.currentIndex === 0
                        onActivated: backend.setCurrentIndex(0)
                    }
                    Repeater {
                        model: backend.tabs
                        delegate: Tab {
                            required property var modelData
                            required property int index
                            title: modelData.title
                            glyph: "document"
                            current: backend.currentIndex === index + 1
                            onActivated: backend.setCurrentIndex(index + 1)
                            onClosed: backend.closeTab(index + 1)
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        DragHandler { target: null; onActiveChanged: if (active) window.startSystemMove() }
                        TapHandler { onDoubleTapped: window.toggleMaximized() }
                    }

                    component WindowButton: Rectangle {
                        id: wb
                        property string glyph
                        property string label
                        property bool danger: false
                        signal clicked()
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignTop
                        color: wbHover.hovered ? (danger ? Theme.closeHover : Theme.hover) : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: label
                        Glyph { anchors.centerIn: parent; width: 12; height: 12; lineWidth: 1; kind: wb.glyph
                                color: wbHover.hovered && wb.danger ? "#FFFFFF" : Theme.text }
                        HoverHandler { id: wbHover }
                        TapHandler { onTapped: wb.clicked() }
                    }
                    WindowButton { glyph: "minimize"; label: backend.texts.minimize; onClicked: window.showMinimized() }
                    WindowButton { glyph: window.maximized ? "restore" : "maximize"
                                   label: window.maximized ? backend.texts.restore_down : backend.texts.maximize
                                   onClicked: window.toggleMaximized() }
                    WindowButton { glyph: "close"; label: backend.texts.close; danger: true; onClicked: window.close() }
                }
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: backend.currentIndex

                HomePage {
                    onOpenFile: openDialog.open()
                    onOpenRecent: path => backend.openPath(path, "")
                }
                Repeater {
                    id: docs
                    model: backend.tabs
                    delegate: DocumentView {
                        id: docView
                        required property var modelData
                        path: modelData.path
                        url: modelData.url
                        password: modelData.password
                        readMode: window.readMode
                        onPrintRequested: backend.printDocument(path, password)
                        onPropertiesRequested: properties.showFor(docView)
                    }
                }
            }
        }
    }

    WinMenu {
        id: appMenu
        minimumWidth: 260
        items: [
            { text: backend.texts.open, shortcut: "Ctrl+O", action: "open" },
            { text: backend.texts.open_recent, submenu: backend.recent.length > 0
                  ? backend.recent.slice(0, 10).map(r => ({ text: r.name, action: "recent:" + r.path }))
                  : [{ text: backend.texts.no_recent, enabled: false }] },
            { separator: true },
            { text: backend.texts.print, shortcut: "Ctrl+P", action: "print", enabled: window.currentView !== null },
            { text: backend.texts.properties, shortcut: "Ctrl+D", action: "properties", enabled: window.currentView !== null },
            { text: backend.texts.show_in_folder, action: "folder", enabled: window.currentView !== null },
            { separator: true },
            { text: backend.texts.read_mode, shortcut: "Ctrl+H", checked: window.readMode, action: "read-mode" },
            { text: backend.texts.full_screen, shortcut: "F11", checked: window.fullScreen, action: "full-screen" },
            { separator: true },
            { text: backend.texts.close_tab, shortcut: "Ctrl+W", action: "close-tab", enabled: window.currentView !== null },
            { text: backend.texts.exit, shortcut: "Ctrl+Q", action: "exit" }
        ]
        onTriggered: action => window.run(action)
    }

    FileDialog {
        id: openDialog
        fileMode: FileDialog.OpenFiles
        nameFilters: [backend.texts.pdf_files + " (*.pdf *.PDF)"]
        onAccepted: backend.openPaths(selectedFiles.map(String))
    }

    WinDialog { id: messageBox }

    // Password of a protected document.
    Popup {
        id: passwordDialog
        property string path
        property bool wrong
        function ask(path, wrong) {
            passwordDialog.path = path;
            passwordDialog.wrong = wrong;
            open();
        }
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 420
        modal: true
        padding: 24
        Overlay.modal: Scrim {}
        onOpened: { passwordField.text = ""; passwordField.forceActiveFocus(); }
        function accept() {
            close();
            backend.openPath(path, passwordField.text);
        }
        background: Rectangle { radius: 8; color: Theme.card; border.width: 1; border.color: Theme.fieldBorder }
        contentItem: ColumnLayout {
            spacing: 12
            Text { text: backend.texts.password_title; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
            Text {
                Layout.fillWidth: true
                text: backend.texts.password_text.replace("{name}", passwordDialog.path.split("/").pop())
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
            }
            TextField {
                id: passwordField
                Layout.fillWidth: true
                echoMode: TextInput.Password
                color: Theme.text
                onAccepted: passwordDialog.accept()
                background: Rectangle { radius: 4; color: Theme.field; border.width: 1
                                        border.color: passwordField.activeFocus ? Theme.accent : Theme.fieldBorder }
            }
            Text { visible: passwordDialog.wrong; text: backend.texts.wrong_password; color: "#C42B1C"; font.pixelSize: Theme.smallFont }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button { Layout.fillWidth: true; text: backend.texts.ok; highlighted: true; onClicked: passwordDialog.accept() }
                Button { Layout.fillWidth: true; text: backend.texts.cancel; onClicked: passwordDialog.close() }
            }
        }
    }

    // Document properties.
    Popup {
        id: properties
        property var facts: []
        function showFor(view) {
            const d = view.document;
            const file = backend.fileFacts(view.path);
            const size = d.pageCount > 0 ? d.pagePointSize(0) : Qt.size(0, 0);
            const date = value => value && !isNaN(value.getTime()) ? value.toLocaleString(Qt.locale(), Locale.ShortFormat) : "";
            properties.facts = [
                [backend.texts.file, file.name], [backend.texts.title, d.title], [backend.texts.author, d.author],
                [backend.texts.subject, d.subject], [backend.texts.keywords, d.keywords],
                [backend.texts.created, date(d.creationDate)], [backend.texts.modified, date(d.modificationDate)],
                [backend.texts.application, d.creator], [backend.texts.producer, d.producer],
                [backend.texts.pages, String(d.pageCount)],
                [backend.texts.page_size, d.pageCount > 0 ? backend.pageSizeText(size.width, size.height) : ""],
                [backend.texts.file_size, file.size], [backend.texts.location, file.folder]
            ].filter(f => f[1]);
            open();
        }
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(560, parent.width - 40)
        modal: true
        padding: 24
        Overlay.modal: Scrim {}
        background: Rectangle { radius: 8; color: Theme.card; border.width: 1; border.color: Theme.fieldBorder }
        contentItem: ColumnLayout {
            spacing: 14
            Text { text: backend.texts.properties; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 18
                rowSpacing: 8
                Repeater {
                    model: properties.facts.length * 2
                    delegate: Text {
                        required property int index
                        readonly property var fact: properties.facts[Math.floor(index / 2)]
                        Layout.fillWidth: index % 2 === 1
                        Layout.maximumWidth: index % 2 === 1 ? 360 : 180
                        text: fact ? fact[index % 2] : ""
                        color: index % 2 === 0 ? Theme.subtext : Theme.text
                        font.pixelSize: Theme.fontSize
                        wrapMode: Text.WrapAnywhere
                    }
                }
            }
            Button { Layout.alignment: Qt.AlignRight; text: backend.texts.ok; highlighted: true; onClicked: properties.close() }
        }
    }

    Shortcut { sequences: [StandardKey.Open]; onActivated: window.run("open") }
    Shortcut { sequence: "Ctrl+P"; onActivated: window.run("print") }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.run("properties") }
    Shortcut { sequence: "Ctrl+W"; onActivated: window.run("close-tab") }
    Shortcut { sequence: "Ctrl+H"; onActivated: window.run("read-mode") }
    Shortcut { sequence: "F11"; onActivated: window.run("full-screen") }
    Shortcut { sequence: "Ctrl+Q"; onActivated: window.run("exit") }
    Shortcut { sequence: "Escape"; enabled: window.fullScreen || window.readMode
               onActivated: { window.readMode = false; if (window.fullScreen) window.showNormal(); } }
    Shortcut { sequence: "Ctrl+Tab"; onActivated: backend.setCurrentIndex((backend.currentIndex + 1) % (backend.tabs.length + 1)) }
}
