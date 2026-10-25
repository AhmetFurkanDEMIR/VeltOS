// The Windows 11 File Explorer command bar: New, cut / copy / paste /
// rename / delete, Sort, View and "See more". In the Recycle Bin: Empty
// Recycle Bin and Restore.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: bar

    readonly property var tab: backend.current
    readonly property var model: tab.items
    readonly property bool inFolder: tab.kind === "folder" || tab.kind === "search"
    readonly property bool inTrash: tab.kind === "trash"
    readonly property bool hasSelection: model.selectedCount > 0
    signal action(string name)

    implicitHeight: 48
    color: Theme.toolbar

    function sortItems() {
        const keys = [["name", "name"], ["modified", "date_modified"], ["type", "type"], ["size", "size"]];
        const result = keys.map(k => ({ text: backend.text(k[1]), action: "sort:" + k[0],
                                        checked: bar.tab.sortKey === k[0] }));
        result.push({ separator: true });
        result.push({ text: backend.text("ascending"), action: "order:asc", checked: !bar.tab.sortDescending });
        result.push({ text: backend.text("descending"), action: "order:desc", checked: bar.tab.sortDescending });
        return result;
    }

    function viewItems() {
        const modes = [["xlarge", "extra_large_icons", "view-preview"], ["large", "large_icons", "view-list-icons"],
                       ["medium", "medium_icons", "view-list-icons"], ["small", "small_icons", "view-list-compact"],
                       ["details", "details", "view-list-details"], ["tiles", "tiles", "view-list-tree"]];
        const result = modes.map(m => ({ text: backend.text(m[1]), icon: m[2], action: "view:" + m[0],
                                         checked: bar.tab.viewMode === m[0] }));
        result.push({ separator: true });
        result.push({ text: backend.text("hidden_items"), action: "hidden", checked: backend.showHidden });
        return result;
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 2

        IconButton {
            id: newButton
            visible: !bar.inTrash
            icon: "list-add"
            text: backend.text("new")
            chevron: true
            enabledState: bar.tab.kind === "folder"
            onClicked: newMenu.openAt(newButton, 0, newButton.height + 4)
        }
        Separator { visible: !bar.inTrash }
        IconButton {
            visible: !bar.inTrash
            icon: "edit-cut"
            tooltip: backend.text("cut")
            enabledState: bar.inFolder && bar.hasSelection
            onClicked: backend.cut()
        }
        IconButton {
            visible: !bar.inTrash
            icon: "edit-copy"
            tooltip: backend.text("copy")
            enabledState: bar.inFolder && bar.hasSelection
            onClicked: backend.copy()
        }
        IconButton {
            visible: !bar.inTrash
            icon: "edit-paste"
            tooltip: backend.text("paste")
            enabledState: bar.tab.kind === "folder" && backend.canPaste
            onClicked: backend.paste()
        }
        IconButton {
            visible: !bar.inTrash
            icon: "edit-rename"
            tooltip: backend.text("rename")
            enabledState: bar.inFolder && bar.model.selectedCount === 1
            onClicked: bar.action("rename")
        }
        IconButton {
            icon: "edit-delete"
            tooltip: backend.text("delete")
            enabledState: (bar.inFolder || bar.inTrash) && bar.hasSelection
            onClicked: bar.action("delete")
        }
        IconButton {
            visible: bar.inTrash
            icon: "trash-empty"
            text: backend.text("empty_recycle_bin")
            enabledState: bar.model.count > 0
            onClicked: bar.action("empty-trash")
        }
        IconButton {
            visible: bar.inTrash
            icon: "edit-undo"
            text: backend.text("restore_all")
            enabledState: bar.model.count > 0 && !bar.hasSelection
            onClicked: backend.restoreAll()
        }
        IconButton {
            visible: bar.inTrash
            icon: "edit-undo"
            text: backend.text("restore")
            enabledState: bar.hasSelection
            onClicked: backend.restoreSelection()
        }
        Separator {}
        IconButton {
            id: sortButton
            icon: "view-sort"
            text: backend.text("sort")
            chevron: true
            enabledState: bar.inFolder || bar.inTrash
            onClicked: sortMenu.openAt(sortButton, 0, sortButton.height + 4)
        }
        IconButton {
            id: viewButton
            icon: "view-list-details"
            text: backend.text("view")
            chevron: true
            enabledState: bar.tab.kind !== "home"
            onClicked: viewMenu.openAt(viewButton, 0, viewButton.height + 4)
        }
        Separator {}
        IconButton {
            id: moreButton
            glyph: "more"
            tooltip: backend.text("see_more")
            onClicked: moreMenu.openAt(moreButton, 0, moreButton.height + 4)
        }
        Item { Layout.fillWidth: true }
    }

    component Separator: Rectangle {
        Layout.preferredWidth: 1
        Layout.preferredHeight: 24
        Layout.leftMargin: 6
        Layout.rightMargin: 6
        color: Theme.separator
    }

    WinMenu {
        id: newMenu
        items: backend.newItems(true)
        onTriggered: action => backend.createNew(action.slice(4))
    }
    WinMenu {
        id: sortMenu
        items: bar.sortItems()
        onTriggered: action => {
            if (action.startsWith("sort:"))
                bar.tab.setSort(action.slice(5), bar.tab.sortDescending);
            else
                bar.tab.setSort(bar.tab.sortKey, action === "order:desc");
        }
    }
    WinMenu {
        id: viewMenu
        items: bar.viewItems()
        onTriggered: action => {
            if (action === "hidden")
                backend.setShowHidden(!backend.showHidden);
            else
                bar.tab.setViewMode(action.slice(5));
        }
    }
    WinMenu {
        id: moreMenu
        items: [
            { text: backend.text("select_all"), icon: "edit-select-all", action: "select-all", shortcut: "Ctrl+A",
              enabled: bar.model.count > 0 },
            { text: backend.text("select_none"), icon: "edit-select-none", action: "select-none",
              enabled: bar.hasSelection },
            { text: backend.text("invert_selection"), icon: "edit-select-invert", action: "invert",
              enabled: bar.model.count > 0 },
            { separator: true },
            { text: backend.text("open_in_terminal"), icon: "utilities-terminal", action: "terminal",
              enabled: bar.tab.kind === "folder" },
            { text: backend.text("properties"), icon: "document-properties", action: "properties",
              shortcut: "Alt+Enter", enabled: bar.tab.kind === "folder" }
        ]
        onTriggered: action => bar.action(action)
    }
}
