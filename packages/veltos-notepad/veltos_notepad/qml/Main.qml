/*
    VeltOS Notepad: the layout of Windows 11 Notepad. Tabs in the title bar,
    the File / Edit / View menus with Settings on the right, the text, the
    find and replace panel and the status bar.

    The window draws its own frame (to put the tabs in the title bar): a
    soft shadow around it, which Python excludes from the input region, and
    resize borders that hand resizing to the window manager.

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

    readonly property bool maximized: visibility === Window.Maximized || visibility === Window.FullScreen
    readonly property int shadow: maximized ? 0 : 12
    readonly property var tab: backend.current
    // `count` makes the binding follow the Repeater creating its editors
    // (at start the current index is set before they exist).
    readonly property var editor: editors.count > 0 ? editors.itemAt(backend.currentIndex) : null
    readonly property var area: editor ? editor.area : null
    property bool settingsOpen: false
    property int pendingClose: -1          // tab to close once it is saved
    property bool quitting: false          // closing the window, asking tab by tab

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }

    function focusText() {
        if (area && !settingsOpen)
            area.forceActiveFocus();
    }

    function updateStatus() {
        if (!area || !tab.tabId)
            return;
        const lc = backend.lineColumn(tab.tabId, area.cursorPosition);
        status.line = lc[0];
        status.column = lc[1];
        status.characters = area.length;
        status.selected = area.selectionEnd - area.selectionStart;
    }

    // --- closing tabs and the window -------------------------------------------------------

    function requestCloseTab(index) {
        if (!backend.needsSaving(index)) {
            backend.closeTab(index);
            return;
        }
        backend.setCurrentIndex(index);
        saveQuestion.tabIndex = index;
        saveQuestion.ask(backend.texts.app_title,
                         backend.texts.save_changes.replace("{name}", editors.itemAt(index) ? backend.current.title : ""),
                         [{ text: backend.texts.save, action: "save" },
                          { text: backend.texts.dont_save, action: "discard" },
                          { text: backend.texts.cancel, action: "cancel" }]);
    }

    function askNextUnsaved() {
        for (let i = 0; i < backend.tabCount; ++i) {
            if (backend.needsSaving(i)) {
                requestCloseTab(i);
                return;
            }
        }
        quitting = false;
        Qt.quit();
    }

    function saveCurrent() {
        backend.save(backend.currentIndex);
    }

    onClosing: close => {
        if (backend.keepsSession && backend.continueSession) {
            backend.saveSession();
            return;
        }
        if (backend.anyModified()) {
            close.accepted = false;
            quitting = true;
            askNextUnsaved();
        }
    }

    width: 1000
    height: 700
    minimumWidth: 480
    minimumHeight: 320
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: (tab.modified ? "*" : "") + (tab.title || "") + " - " + backend.texts.app_title

    Connections {
        target: backend
        function onCurrentChanged() {
            Qt.callLater(window.updateStatus);
            Qt.callLater(window.focusText);
        }
        function onMessage(text) {
            messageBox.ask(backend.texts.app_title, text, [{ text: backend.texts.ok, action: "ok" }]);
        }
        function onSaveAsRequested(index) {
            saveDialog.tabIndex = index;
            saveDialog.selectedFile = "";
            saveDialog.open();
        }
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

    Rectangle {
        id: frame
        anchors.fill: parent
        anchors.margins: window.shadow
        radius: window.maximized ? 0 : 8
        color: Theme.editor
        border.width: window.maximized ? 0 : 1
        border.color: Theme.dark ? "#3A3C4A" : "#C9CDD8"
        clip: true

        DropArea {
            anchors.fill: parent
            onDropped: drop => {
                if (drop.hasUrls) {
                    backend.openPaths(drop.urls.map(String));
                    drop.accept();
                }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: frame.border.width
            spacing: 0

            TitleBar {
                Layout.fillWidth: true
                window: window
                radius: frame.radius
                onCloseTab: index => window.requestCloseTab(index)
                onCloseWindow: window.close()
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: frame.radius
                    color: Theme.tabStrip
                    z: -1
                }
            }

            // Menu row: File, Edit, View; Settings on the right.
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                color: Theme.toolbar
                visible: !window.settingsOpen

                component MenuButton: Rectangle {
                    id: mb
                    property string text
                    property WinMenu menu
                    implicitWidth: label.implicitWidth + 22
                    implicitHeight: 30
                    radius: 4
                    color: mb.menu && mb.menu.opened ? Theme.pressed : (hover.hovered ? Theme.hover : "transparent")
                    Accessible.role: Accessible.MenuItem
                    Accessible.name: text
                    Text {
                        id: label
                        anchors.centerIn: parent
                        text: mb.text
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                    }
                    HoverHandler { id: hover }
                    TapHandler { onTapped: mb.menu.openAt(mb, 0, mb.height + 2) }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 2
                    MenuButton { text: backend.texts.file; menu: fileMenu }
                    MenuButton { text: backend.texts.edit; menu: editMenu }
                    MenuButton { text: backend.texts.view; menu: viewMenu }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        implicitWidth: 34
                        implicitHeight: 30
                        radius: 4
                        color: gearHover.hovered ? Theme.hover : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.settings
                        Glyph {
                            anchors.centerIn: parent
                            width: 15
                            height: 15
                            kind: "gear"
                        }
                        ToolTip.visible: gearHover.hovered
                        ToolTip.delay: 600
                        ToolTip.text: backend.texts.settings
                        HoverHandler { id: gearHover }
                        TapHandler { onTapped: window.settingsOpen = true }
                    }
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: Theme.separator
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                StackLayout {
                    id: stack
                    anchors.fill: parent
                    currentIndex: backend.currentIndex
                    visible: !window.settingsOpen
                    Repeater {
                        id: editors
                        model: backend.tabs
                        delegate: Editor {
                            onCursorMoved: if (index === backend.currentIndex) window.updateStatus()
                            onContextMenu: (x, y) => textMenu.openAt(area, x, y)
                        }
                    }
                }

                FindBar {
                    id: findBar
                    objectName: "findBar"
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.topMargin: 8
                    anchors.rightMargin: 24
                    width: Math.min(440, parent.width - 48)
                    onFindNext: forward => window.find(forward)
                    onReplaceOne: window.replaceOne()
                    onReplaceAll: window.replaceAll()
                    onClosed: window.focusText()
                }

                SettingsPage {
                    anchors.fill: parent
                    visible: window.settingsOpen
                    onBack: {
                        window.settingsOpen = false;
                        window.focusText();
                    }
                }
            }

            StatusBar {
                id: status
                Layout.fillWidth: true
                visible: backend.statusBar && !window.settingsOpen
                onPickEol: item => eolMenu.openAt(item, 0, -eolMenu.height - 4)
                onPickEncoding: item => encodingMenu.openAt(item, 0, -encodingMenu.height - 4)
            }
        }
    }

    // --- Find and replace ----------------------------------------------------------------

    function find(forward) {
        if (!area || findBar.query === "")
            return;
        const from = forward ? area.selectionEnd : area.selectionStart;
        const hit = backend.find(tab.tabId, findBar.query, from, forward, findBar.matchCase, findBar.wrapAround);
        if (hit.length === 2)
            area.select(hit[0], hit[1]);
        else
            messageBox.ask(backend.texts.app_title, backend.texts.not_found.replace("{text}", findBar.query),
                           [{ text: backend.texts.ok, action: "ok" }]);
    }
    function replaceOne() {
        if (!area || findBar.query === "")
            return;
        const selected = area.selectedText;
        const same = findBar.matchCase ? selected === findBar.query
                                       : selected.toLowerCase() === findBar.query.toLowerCase();
        if (same && selected !== "") {
            const start = area.selectionStart;
            area.remove(area.selectionStart, area.selectionEnd);
            area.insert(start, findBar.replacement);
            area.cursorPosition = start + findBar.replacement.length;
        }
        find(true);
    }
    function replaceAll() {
        if (!area || findBar.query === "")
            return;
        backend.replaceAll(tab.tabId, findBar.query, findBar.replacement, findBar.matchCase);
    }

    // --- Menus -----------------------------------------------------------------------------

    function run(action) {
        const a = area;
        switch (action) {
        case "new-tab": backend.newTab(); break;
        case "new-window": backend.newWindow(); break;
        case "open": openDialog.open(); break;
        case "save": saveCurrent(); break;
        case "save-as":
            saveDialog.tabIndex = backend.currentIndex;
            saveDialog.selectedFile = "";
            saveDialog.open();
            break;
        case "save-all": backend.saveAll(); break;
        case "print": backend.printTab(backend.currentIndex); break;
        case "close-tab": requestCloseTab(backend.currentIndex); break;
        case "close-window":
        case "exit": window.close(); break;
        case "undo": if (a) a.undo(); break;
        case "redo": if (a) a.redo(); break;
        case "cut": if (a) a.cut(); break;
        case "copy": if (a) a.copy(); break;
        case "paste": if (a) a.paste(); break;
        case "delete": if (a && a.selectedText !== "") a.remove(a.selectionStart, a.selectionEnd); break;
        case "find": findBar.show(false); break;
        case "replace": findBar.show(true); break;
        case "find-next": if (findBar.query !== "") find(true); else findBar.show(false); break;
        case "find-previous": if (findBar.query !== "") find(false); else findBar.show(false); break;
        case "go-to": goToDialog.open(); break;
        case "select-all": if (a) a.selectAll(); break;
        case "time-date": if (a) a.insert(a.cursorPosition, backend.timeDate()); break;
        case "font": window.settingsOpen = true; break;
        case "zoom-in": backend.stepZoom(1); break;
        case "zoom-out": backend.stepZoom(-1); break;
        case "zoom-reset": backend.stepZoom(0); break;
        case "status-bar": backend.setStatusBar(!backend.statusBar); break;
        case "word-wrap": backend.setWordWrap(!backend.wordWrap); break;
        default:
            if (action.indexOf("recent:") === 0)
                backend.openPaths([action.slice(7)]);
        }
    }

    WinMenu {
        id: fileMenu
        items: [
            { text: backend.texts.new_tab, shortcut: "Ctrl+N", action: "new-tab" },
            { text: backend.texts.new_window, shortcut: "Ctrl+Shift+N", action: "new-window" },
            { text: backend.texts.open, shortcut: "Ctrl+O", action: "open" },
            { text: backend.texts.recent,
              submenu: backend.recentFiles.length > 0
                       ? backend.recentFiles.map(f => ({ text: f, action: "recent:" + f }))
                       : [{ text: backend.texts.no_recent, enabled: false }] },
            { text: backend.texts.save, shortcut: "Ctrl+S", action: "save" },
            { text: backend.texts.save_as, shortcut: "Ctrl+Shift+S", action: "save-as" },
            { text: backend.texts.save_all, shortcut: "Ctrl+Alt+S", action: "save-all" },
            { separator: true },
            { text: backend.texts.print, shortcut: "Ctrl+P", action: "print" },
            { separator: true },
            { text: backend.texts.close_tab, shortcut: "Ctrl+W", action: "close-tab" },
            { text: backend.texts.close_window, shortcut: "Ctrl+Shift+W", action: "close-window" },
            { text: backend.texts.exit, action: "exit" }
        ]
        onTriggered: action => window.run(action)
    }
    WinMenu {
        id: editMenu
        readonly property bool hasSelection: window.area !== null && window.area.selectedText !== ""
        items: [
            { text: backend.texts.undo, shortcut: "Ctrl+Z", action: "undo", enabled: window.area !== null && window.area.canUndo },
            { separator: true },
            { text: backend.texts.cut, shortcut: "Ctrl+X", action: "cut", enabled: hasSelection },
            { text: backend.texts.copy, shortcut: "Ctrl+C", action: "copy", enabled: hasSelection },
            { text: backend.texts.paste, shortcut: "Ctrl+V", action: "paste" },
            { text: backend.texts.delete, shortcut: "Del", action: "delete", enabled: hasSelection },
            { separator: true },
            { text: backend.texts.find, shortcut: "Ctrl+F", action: "find" },
            { text: backend.texts.find_next, shortcut: "F3", action: "find-next" },
            { text: backend.texts.find_previous, shortcut: "Shift+F3", action: "find-previous" },
            { text: backend.texts.replace, shortcut: "Ctrl+H", action: "replace" },
            { text: backend.texts.go_to, shortcut: "Ctrl+G", action: "go-to" },
            { separator: true },
            { text: backend.texts.select_all, shortcut: "Ctrl+A", action: "select-all" },
            { text: backend.texts.time_date, shortcut: "F5", action: "time-date" },
            { separator: true },
            { text: backend.texts.font, action: "font" }
        ]
        onTriggered: action => window.run(action)
    }
    // The right button's menu in the text: Windows' text menu (the edit
    // menu's first part), not the whole Edit menu.
    WinMenu {
        id: textMenu
        readonly property bool hasSelection: editMenu.hasSelection
        items: [
            { text: backend.texts.undo, shortcut: "Ctrl+Z", action: "undo", enabled: window.area !== null && window.area.canUndo },
            { separator: true },
            { text: backend.texts.cut, shortcut: "Ctrl+X", action: "cut", enabled: hasSelection },
            { text: backend.texts.copy, shortcut: "Ctrl+C", action: "copy", enabled: hasSelection },
            { text: backend.texts.paste, shortcut: "Ctrl+V", action: "paste" },
            { text: backend.texts.delete, shortcut: "Del", action: "delete", enabled: hasSelection },
            { separator: true },
            { text: backend.texts.select_all, shortcut: "Ctrl+A", action: "select-all" }
        ]
        onTriggered: action => window.run(action)
    }
    WinMenu {
        id: viewMenu
        items: [
            { text: backend.texts.zoom, submenu: [
                { text: backend.texts.zoom_in, shortcut: "Ctrl+Plus", action: "zoom-in" },
                { text: backend.texts.zoom_out, shortcut: "Ctrl+Minus", action: "zoom-out" },
                { text: backend.texts.zoom_reset, shortcut: "Ctrl+0", action: "zoom-reset" } ] },
            { text: backend.texts.status_bar, checked: backend.statusBar, action: "status-bar" },
            { text: backend.texts.word_wrap, checked: backend.wordWrap, action: "word-wrap" }
        ]
        onTriggered: action => window.run(action)
    }
    WinMenu {
        id: eolMenu
        minimumWidth: 180
        items: ["CRLF", "LF", "CR"].map(e => ({ text: backend.texts["eol_" + e], checked: window.tab.eol === e, action: e }))
        onTriggered: action => backend.setEol(backend.currentIndex, action)
    }
    WinMenu {
        id: encodingMenu
        minimumWidth: 180
        items: backend.encodings.map(e => ({ text: e, checked: window.tab.encoding === e, action: e }))
        onTriggered: action => backend.setEncoding(backend.currentIndex, action)
    }

    // --- Keyboard ------------------------------------------------------------------------
    component Key: Shortcut {
        property string action
        context: Qt.WindowShortcut
        onActivated: window.run(action)
    }
    Key { sequence: "Ctrl+N"; action: "new-tab" }
    Key { sequence: "Ctrl+T"; action: "new-tab" }
    Key { sequence: "Ctrl+Shift+N"; action: "new-window" }
    Key { sequence: "Ctrl+O"; action: "open" }
    Key { sequence: "Ctrl+S"; action: "save" }
    Key { sequence: "Ctrl+Shift+S"; action: "save-as" }
    Key { sequence: "Ctrl+Alt+S"; action: "save-all" }
    Key { sequence: "Ctrl+P"; action: "print" }
    Key { sequence: "Ctrl+W"; action: "close-tab" }
    Key { sequence: "Ctrl+Shift+W"; action: "close-window" }
    Key { sequence: "Ctrl+F"; action: "find" }
    Key { sequence: "F3"; action: "find-next" }
    Key { sequence: "Shift+F3"; action: "find-previous" }
    Key { sequence: "Ctrl+H"; action: "replace" }
    Key { sequence: "Ctrl+G"; action: "go-to" }
    Key { sequence: "F5"; action: "time-date" }
    Key { sequence: "Ctrl++"; action: "zoom-in" }
    Key { sequence: "Ctrl+="; action: "zoom-in" }
    Key { sequence: "Ctrl+-"; action: "zoom-out" }
    Key { sequence: "Ctrl+0"; action: "zoom-reset" }
    Shortcut {
        sequence: "Ctrl+Tab"
        onActivated: backend.setCurrentIndex((backend.currentIndex + 1) % backend.tabCount)
    }
    Shortcut {
        sequence: "Ctrl+Shift+Tab"
        onActivated: backend.setCurrentIndex((backend.currentIndex + backend.tabCount - 1) % backend.tabCount)
    }
    Shortcut {
        sequence: "Escape"
        enabled: findBar.visible || window.settingsOpen
        onActivated: {
            if (findBar.visible)
                findBar.hide();
            else
                window.settingsOpen = false;
        }
    }

    // --- Dialogs ---------------------------------------------------------------------------
    FileDialog {
        id: openDialog
        fileMode: FileDialog.OpenFiles
        nameFilters: [backend.texts.text_files + " (*.txt)", backend.texts.all_files + " (*)"]
        onAccepted: backend.openPaths(selectedFiles.map(String))
    }
    FileDialog {
        id: saveDialog
        property int tabIndex: -1
        fileMode: FileDialog.SaveFile
        defaultSuffix: "txt"
        nameFilters: [backend.texts.text_files + " (*.txt)", backend.texts.all_files + " (*)"]
        onAccepted: {
            const saved = backend.saveAs(tabIndex, String(selectedFile));
            if (saved && window.pendingClose === tabIndex) {
                window.pendingClose = -1;
                backend.closeTab(tabIndex);
                if (window.quitting)
                    window.askNextUnsaved();
            }
        }
        onRejected: {
            window.pendingClose = -1;
            window.quitting = false;
        }
    }

    WinDialog {
        id: saveQuestion
        property int tabIndex: -1
        onChosen: action => {
            if (action === "save") {
                window.pendingClose = tabIndex;
                if (backend.save(tabIndex)) {
                    window.pendingClose = -1;
                    backend.closeTab(tabIndex);
                    if (window.quitting)
                        window.askNextUnsaved();
                }
            } else if (action === "discard") {
                backend.closeTab(tabIndex);
                if (window.quitting)
                    window.askNextUnsaved();
            } else {
                window.quitting = false;
            }
        }
    }
    WinDialog {
        id: messageBox
    }

    Popup {
        id: goToDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 360
        modal: true
        padding: 24
        Overlay.modal: Scrim {}
        onOpened: {
            lineField.text = String(status.line);
            lineField.selectAll();
            lineField.forceActiveFocus();
        }
        function go() {
            const line = parseInt(lineField.text);
            if (!isNaN(line) && window.area) {
                window.area.cursorPosition = backend.positionOfLine(window.tab.tabId, line);
                goToDialog.close();
                window.focusText();
            }
        }
        background: Rectangle {
            radius: 8
            color: Theme.card
            border.width: 1
            border.color: Theme.fieldBorder
        }
        contentItem: ColumnLayout {
            spacing: 12
            Text {
                text: backend.texts.go_to_line
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }
            Text {
                text: backend.texts.line_number
                color: Theme.text
                font.pixelSize: Theme.fontSize
            }
            TextField {
                id: lineField
                Layout.fillWidth: true
                color: Theme.text
                validator: IntValidator { bottom: 1 }
                inputMethodHints: Qt.ImhDigitsOnly
                onAccepted: goToDialog.go()
                background: Rectangle {
                    radius: 4
                    color: Theme.field
                    border.width: 1
                    border.color: lineField.activeFocus ? Theme.accent : Theme.fieldBorder
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button {
                    Layout.fillWidth: true
                    text: backend.texts.go_to
                    highlighted: true
                    onClicked: goToDialog.go()
                }
                Button {
                    Layout.fillWidth: true
                    text: backend.texts.cancel
                    onClicked: goToDialog.close()
                }
            }
        }
    }

    Component.onCompleted: Qt.callLater(function() { window.updateStatus(); window.focusText(); })
}
