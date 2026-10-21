/*
    VeltOS File Explorer: the layout of Windows 11 File Explorer. Tabs in the
    title bar, the command bar, back / forward / up with the address and
    search boxes, the navigation pane, the items, the status bar.

    The window draws its own frame (to put the tabs in the title bar): a
    soft shadow around it, which Python excludes from the input region, and
    resize borders that hand resizing to the window manager.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "."

ApplicationWindow {
    id: window

    readonly property var tab: backend.current
    readonly property bool maximized: visibility === Window.Maximized || visibility === Window.FullScreen
    readonly property int shadow: maximized ? 0 : 12

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }

    width: 1200
    height: 780
    minimumWidth: 640
    minimumHeight: 420
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: (tab.query !== "" ? backend.format("search_results", "name", tab.title) : tab.title)
           + " - " + backend.text("app_title")

    Connections {
        target: backend
        function onMessage(text) { dialog.tell(text); }
        function onCurrentChanged() { content.focusItems(); }
    }
    Connections {
        target: window.tab
        function onChanged() { content.focusItems(); }
    }

    // --- Shadow ----------------------------------------------------------------------
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
        color: Theme.content
        border.width: window.maximized ? 0 : 1
        border.color: Theme.dark ? "#3A3C4A" : "#C9CDD8"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: frame.border.width
            spacing: 0

            TitleBar {
                Layout.fillWidth: true
                window: window
                radius: frame.radius
                onCloseWindow: window.close()
                Rectangle {
                    // Square lower corners.
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: frame.radius
                    color: Theme.titleBar
                    z: -1
                }
            }
            CommandBar {
                Layout.fillWidth: true
                onAction: name => window.runAction(name, null)
            }
            AddressBar {
                id: addressBar
                Layout.fillWidth: true
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Theme.separator
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                NavPane {
                    id: navPane
                    Layout.preferredWidth: 240
                    Layout.fillHeight: true
                    onContextMenu: (item, entry, x, y) => window.folderMenu(item, entry.path, x, y)
                }

                Item {
                    id: content
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    function focusItems() {
                        if (loader.item && window.tab.kind !== "home" && window.tab.kind !== "thispc")
                            loader.item.forceActiveFocus();
                    }

                    Loader {
                        id: loader
                        anchors.fill: parent
                        sourceComponent: window.tab.kind === "home" ? homeComponent
                                         : window.tab.kind === "thispc" ? thisPcComponent : folderComponent
                        onLoaded: content.focusItems()
                    }
                }
            }

            StatusBar {
                Layout.fillWidth: true
                radius: frame.radius
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: frame.radius
                    color: Theme.content
                    z: -1
                }
            }
        }
    }

    // --- Resize borders --------------------------------------------------------------
    component Edge: MouseArea {
        property int edges
        enabled: !window.maximized
        hoverEnabled: true
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

    // --- Views ----------------------------------------------------------------------
    Component {
        id: homeComponent
        HomeView {
            onFolderMenu: (item, entry, x, y) => window.folderMenu(item, entry.path, x, y)
            onFileMenu: (item, entry, x, y) => window.recentMenu(item, entry.path, x, y)
        }
    }
    Component {
        id: thisPcComponent
        ThisPCView {
            onDriveMenu: (item, drive, x, y) => window.driveMenu(item, drive, x, y)
        }
    }
    Component {
        id: folderComponent
        FolderView {
            id: folderView
            onItemMenu: (x, y) => window.itemMenu(folderView, x, y)
            onBackgroundMenu: (x, y) => window.backgroundMenu(folderView, x, y)
            onRequestDelete: permanently => window.runAction(permanently ? "delete-forever" : "delete", null)
            onShowMessage: text => dialog.tell(text)
        }
    }

    // --- Menus ----------------------------------------------------------------------
    WinMenu {
        id: contextMenu
        property var context: null
        onTriggered: action => window.runAction(action, context)
    }

    function showMenu(items, context, item, x, y) {
        contextMenu.items = items;
        contextMenu.context = context;
        contextMenu.openAt(item || window.contentItem, x, y);
    }

    function itemMenu(item, x, y) {
        const chosen = tab.items.selectedList();
        if (chosen.length === 0)
            return;
        const one = chosen.length === 1 ? chosen[0] : null;
        if (tab.kind === "trash") {
            showMenu([
                { text: backend.text("restore"), icon: "edit-undo", action: "restore" },
                { text: backend.text("delete"), icon: "edit-delete", action: "delete", shortcut: "Delete" }
            ], null, item, x, y);
            return;
        }
        const items = [
            { iconRow: [
                { icon: "edit-cut", tooltip: backend.text("cut"), action: "cut" },
                { icon: "edit-copy", tooltip: backend.text("copy"), action: "copy" },
                { icon: "edit-rename", tooltip: backend.text("rename"), action: "rename", enabled: one !== null },
                { icon: "edit-delete", tooltip: backend.text("delete"), action: "delete" }
            ] },
            { separator: true },
            { text: backend.text("open"), icon: one && one.isDir ? "folder-open" : "document-open",
              action: "open", shortcut: "Enter" }
        ];
        if (one && one.isDir)
            items.push({ text: backend.text("open_in_new_tab"), icon: "tab-new", action: "open-tab" });
        if (one && !one.isDir) {
            const apps = backend.appsFor(one.path).map(a => ({ text: a.name, icon: a.icon, action: "with:" + a.path }));
            if (apps.length > 0)
                items.push({ text: backend.text("open_with"), icon: "document-open", submenu: apps });
        }
        items.push({ separator: true });
        if (one && one.isDir)
            items.push(backend.isPinned(one.path)
                       ? { text: backend.text("unpin_from_quick_access"), icon: "window-unpin", action: "unpin" }
                       : { text: backend.text("pin_to_quick_access"), icon: "window-pin", action: "pin" });
        if (tab.kind === "folder") {
            items.push({ text: backend.text("compress_zip"), icon: "archive-insert", action: "compress" });
            items.push({ text: backend.text("add_to_archive"), icon: "veltos-archive", action: "add-archive" });
        }
        if (one && !one.isDir && backend.isArchive(one.path)) {
            items.push({ text: backend.text("extract_all"), icon: "archive-extract", action: "extract" });
            items.push({ text: backend.text("extract_here"), icon: "archive-extract", action: "extract-here" });
        }
        items.push({ text: backend.text("copy_as_path"), icon: "edit-copy-path", action: "copy-path",
                     shortcut: "Ctrl+Shift+C" });
        if (tab.kind === "search" && one)
            items.push({ text: backend.text("open") + " — " + backend.text("location"), icon: "folder-open",
                         action: "open-location" });
        items.push({ separator: true });
        if (one && one.isDir)
            items.push({ text: backend.text("open_in_terminal"), icon: "utilities-terminal", action: "terminal-item" });
        items.push({ text: backend.text("properties"), icon: "document-properties", action: "properties",
                     shortcut: "Alt+Enter" });
        showMenu(items, one ? one.path : null, item, x, y);
    }

    function backgroundMenu(item, x, y) {
        if (tab.kind === "trash") {
            showMenu([{ text: backend.text("empty_recycle_bin"), icon: "trash-empty", action: "empty-trash",
                        enabled: tab.items.count > 0 }], null, item, x, y);
            return;
        }
        const views = [["xlarge", "extra_large_icons"], ["large", "large_icons"], ["medium", "medium_icons"],
                       ["small", "small_icons"], ["details", "details"], ["tiles", "tiles"]]
            .map(v => ({ text: backend.text(v[1]), action: "view:" + v[0], checked: tab.viewMode === v[0] }));
        const sorts = [["name", "name"], ["modified", "date_modified"], ["type", "type"], ["size", "size"]]
            .map(s => ({ text: backend.text(s[1]), action: "sort:" + s[0], checked: tab.sortKey === s[0] }));
        sorts.push({ separator: true });
        sorts.push({ text: backend.text("ascending"), action: "order:asc", checked: !tab.sortDescending });
        sorts.push({ text: backend.text("descending"), action: "order:desc", checked: tab.sortDescending });
        const folder = tab.kind === "folder";
        showMenu([
            { text: backend.text("view"), icon: "view-list-icons", submenu: views },
            { text: backend.text("sort"), icon: "view-sort", submenu: sorts },
            { text: backend.text("refresh"), icon: "view-refresh", action: "refresh", shortcut: "F5" },
            { separator: true },
            { text: backend.text("paste"), icon: "edit-paste", action: "paste", shortcut: "Ctrl+V",
              enabled: folder && backend.canPaste },
            { text: backend.text("new"), icon: "list-add", enabled: folder, submenu: [
                { text: backend.text("folder"), icon: "folder", action: "new-folder" },
                { separator: true },
                { text: backend.text("text_document"), icon: "text-plain", action: "new-text" }
            ] },
            { separator: true },
            { text: backend.text("open_in_terminal"), icon: "utilities-terminal", action: "terminal", enabled: folder },
            { text: backend.text("properties"), icon: "document-properties", action: "properties-folder",
              enabled: folder }
        ], null, item, x, y);
    }

    function folderMenu(item, path, x, y) {
        showMenu([
            { text: backend.text("open"), icon: "folder-open", action: "go" },
            { text: backend.text("open_in_new_tab"), icon: "tab-new", action: "open-tab-path" },
            { separator: true },
            backend.isPinned(path)
                ? { text: backend.text("unpin_from_quick_access"), icon: "window-unpin", action: "unpin-path" }
                : { text: backend.text("pin_to_quick_access"), icon: "window-pin", action: "pin-path" },
            { text: backend.text("copy_as_path"), icon: "edit-copy-path", action: "copy-path-of" },
            { separator: true },
            { text: backend.text("open_in_terminal"), icon: "utilities-terminal", action: "terminal-path" },
            { text: backend.text("properties"), icon: "document-properties", action: "properties-path" }
        ], path, item, x, y);
    }

    function recentMenu(item, path, x, y) {
        showMenu([
            { text: backend.text("open"), icon: "document-open", action: "open-path" },
            { text: backend.text("open") + " — " + backend.text("location"), icon: "folder-open",
              action: "location-path" },
            { separator: true },
            { text: backend.text("copy_as_path"), icon: "edit-copy-path", action: "copy-path-of" },
            { text: backend.text("properties"), icon: "document-properties", action: "properties-path" }
        ], path, item, x, y);
    }

    function driveMenu(item, drive, x, y) {
        const items = [{ text: backend.text("open"), icon: "folder-open", action: "open-drive" }];
        if (drive.removable && drive.mount !== "")
            items.push({ text: backend.text("eject"), icon: "media-eject", action: "eject" });
        if (drive.mount !== "") {
            items.push({ separator: true });
            items.push({ text: backend.text("properties"), icon: "document-properties", action: "properties-drive" });
        }
        showMenu(items, drive, item, x, y);
    }

    function confirmDelete(permanently) {
        const chosen = tab.items.selectedList();
        if (chosen.length === 0)
            return;
        if (!permanently && tab.kind !== "trash") {
            backend.deleteSelection(false);       // to the Recycle Bin, like Windows: no question
            return;
        }
        const question = chosen.length === 1
            ? backend.format("delete_forever_one", "name", chosen[0].name)
            : backend.format("delete_forever", "count", String(chosen.length));
        dialog.ask(chosen.length === 1 ? backend.text("delete") : backend.text("delete_title"), question,
                   backend.text("yes"), backend.text("no"), () => backend.deleteSelection(true));
    }

    function runAction(action, context) {
        const view = loader.item;
        if (action === "cut") backend.cut();
        else if (action === "copy") backend.copy();
        else if (action === "paste") backend.paste();
        else if (action === "rename" && view && view.startRename) view.startRename(tab.items.currentRow);
        else if (action === "delete") confirmDelete(false);
        else if (action === "delete-forever") confirmDelete(true);
        else if (action === "open") backend.openSelection();
        else if (action === "open-tab") backend.openInNewTab(context);
        else if (action.startsWith("with:")) backend.openWith(action.slice(5));
        else if (action === "pin") backend.pin(context);
        else if (action === "unpin") backend.unpin(context);
        else if (action === "compress") backend.compress();
        else if (action === "extract") backend.extract(context);
        else if (action === "extract-here") backend.extractHere(context);
        else if (action === "add-archive") backend.addToArchive();
        else if (action === "copy-path") backend.copyAsPath();
        else if (action === "open-location") backend.openLocation(context);
        else if (action === "properties") backend.properties();
        else if (action === "properties-folder") backend.propertiesOf(tab.location);
        else if (action === "terminal") backend.openTerminal();
        else if (action === "terminal-item") backend.terminalAt(context);
        else if (action === "restore") backend.restoreSelection();
        else if (action === "empty-trash")
            dialog.ask(backend.text("empty_recycle_bin"), backend.text("empty_bin_question"),
                       backend.text("yes"), backend.text("no"), () => backend.emptyTrash());
        else if (action === "refresh") tab.refresh();
        else if (action === "new-folder") backend.createNew("folder");
        else if (action === "new-text") backend.createNew("text");
        else if (action.startsWith("view:")) tab.setViewMode(action.slice(5));
        else if (action.startsWith("sort:")) tab.setSort(action.slice(5), tab.sortDescending);
        else if (action === "order:asc") tab.setSort(tab.sortKey, false);
        else if (action === "order:desc") tab.setSort(tab.sortKey, true);
        else if (action === "select-all") tab.items.selectAll();
        else if (action === "select-none") tab.items.selectNone();
        else if (action === "invert") tab.items.invertSelection();
        else if (action === "go") backend.open(context);
        else if (action === "open-tab-path") backend.openInNewTab(context);
        else if (action === "pin-path") backend.pin(context);
        else if (action === "unpin-path") backend.unpin(context);
        else if (action === "copy-path-of") backend.copyPathText(context);
        else if (action === "terminal-path") backend.terminalAt(context);
        else if (action === "properties-path") backend.propertiesOf(context);
        else if (action === "open-path") backend.open(context);
        else if (action === "location-path") backend.openLocation(context);
        else if (action === "open-drive") backend.openDrive(context.device !== "" ? context.device : context.mount);
        else if (action === "eject") backend.ejectDrive(context.device);
        else if (action === "properties-drive") backend.propertiesOf(context.mount);
    }

    WinDialog { id: dialog }

    // --- Keyboard ------------------------------------------------------------------
    Shortcut { sequences: [StandardKey.Copy]; onActivated: window.runAction("copy", null) }
    Shortcut { sequences: [StandardKey.Cut]; onActivated: window.runAction("cut", null) }
    Shortcut { sequences: [StandardKey.Paste]; onActivated: window.runAction("paste", null) }
    Shortcut { sequences: [StandardKey.SelectAll]; onActivated: window.tab.items.selectAll() }
    Shortcut { sequence: "Ctrl+Shift+N"; onActivated: backend.createNew("folder") }
    Shortcut { sequence: "Ctrl+Shift+C"; onActivated: backend.copyAsPath() }
    Shortcut { sequences: ["F5", "Ctrl+R"]; onActivated: window.tab.refresh() }
    Shortcut { sequences: ["Alt+Left", StandardKey.Back]; onActivated: window.tab.back() }
    Shortcut { sequences: ["Alt+Right", StandardKey.Forward]; onActivated: window.tab.forward() }
    Shortcut { sequence: "Alt+Up"; onActivated: window.tab.up() }
    Shortcut { sequences: ["Ctrl+L", "Alt+D", "F4"]; onActivated: addressBar.editAddress() }
    Shortcut { sequences: ["Ctrl+F", "Ctrl+E", "F3"]; onActivated: addressBar.focusSearch() }
    Shortcut { sequence: "Ctrl+T"; onActivated: backend.newTab("home:") }
    Shortcut { sequence: "Ctrl+W"; onActivated: if (!backend.closeTab(backend.currentIndex)) window.close() }
    Shortcut { sequence: "Ctrl+Tab"; onActivated: backend.setCurrentIndex((backend.currentIndex + 1) % backend.tabs.length) }
    Shortcut { sequence: "Ctrl+Shift+Tab"
               onActivated: backend.setCurrentIndex((backend.currentIndex + backend.tabs.length - 1) % backend.tabs.length) }
    Shortcut { sequence: "Ctrl+N"; onActivated: backend.newWindow() }
    Shortcut { sequence: "Ctrl+H"; onActivated: backend.setShowHidden(!backend.showHidden) }

    // Mouse back / forward buttons.
    TapHandler {
        acceptedButtons: Qt.BackButton | Qt.ForwardButton
        onTapped: (point, button) => {
            if (button === Qt.BackButton)
                window.tab.back();
            else
                window.tab.forward();
        }
    }
}
