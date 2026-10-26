/*
    VeltOS: the Windows 11 behaviour of the desktop, added to Plasma's
    folder view (FolderView.qml, plasma-desktop 6.3) by
    update-plasma-overrides (org.kde.desktopcontainment.json):

    - the desktop's right-click menu is Windows 11's: View, Sort by,
      Refresh, Paste, New, Display settings, Personalize, Open in Terminal
      (Plasma's containment menu with "Enter Edit Mode", "Add Widgets",
      "Configure Desktop" never opens);
    - New > Folder / Word Document / PowerPoint Presentation / Text
      Document / Excel Worksheet make the item at once and open its name
      for editing, as Windows does (Plasma asked the name in a dialog);
    - Refresh (menu or F5) blinks the icons like Windows;
    - the Recycle Bin, This PC and the VeltOS Store cannot be deleted,
      renamed or cut: their menu has Open (the Bin also Empty Recycle
      Bin), Properties where it makes sense, and nothing else; the Delete
      key, F2 and Ctrl+X skip them;
    - every other file and folder gets Windows 11's menu (Open, Open with,
      Cut, Copy, Rename, Delete, Compress to ZIP file, Properties); its
      Properties is VeltOS' window (veltos-explorer --properties), never
      KDE's dialog.

    Texts come from the veltos-desktop catalog (i18nd), not from the
    containment's, so KDE's own translations stay untouched.

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.private.desktopcontainment.folder as Folder
import org.kde.kquickcontrolsaddons as KQuickAddons

Item {
    id: veltos

    // The folder view's parts, handed over by FolderView.qml.
    property Item view            // the view (FolderView's root: rename(), url)
    property var folderModel      // Folder.FolderModel
    property var grid             // the GridView of icons
    property var mapper           // Folder.Positioner (view index -> model index)

    readonly property bool onDesktop: folderModel ? folderModel.usedByContainment : false
    // Launchers every user gets (veltos-session.sh); they cannot go.
    readonly property var protectedNames: ["recycle-bin.desktop", "this-pc.desktop", "veltos-store.desktop"]
    readonly property string domain: "veltos-desktop"

    function tr(text) {
        return i18nd(domain, text);
    }

    // --- The Recycle Bin's fill -------------------------------------------

    // Whether the bin holds anything: the desktop's Recycle Bin icon shows
    // it (FolderItemDelegate.qml reads trashFull), as on Windows. KIO's
    // own way (EmptyIcon in the launcher, trashrc) was not re-read by the
    // desktop when files went in or out (product owner, 2026-10-22). The
    // trash is watched like a folder; only its count is used.
    property bool trashFull: false
    Folder.FolderModel {
        id: trashModel
        url: veltos.onDesktop ? "trash:/" : ""
        onRowsInserted: veltos.trashFull = rowCount() > 0
        onRowsRemoved: veltos.trashFull = rowCount() > 0
        onModelReset: veltos.trashFull = rowCount() > 0
        onListingCompleted: veltos.trashFull = rowCount() > 0
    }

    // --- Protected icons --------------------------------------------------

    // The file name of an item, from its delegate: the override gives
    // FolderItemDelegate.qml a `veltosFileName` (the model's roles). The
    // model's own urlForIndex() is not callable from QML (VM, 2026-10-22).
    function fileNameOf(item) {
        const text = item && item.veltosFileName !== undefined ? String(item.veltosFileName) : "";
        return decodeURIComponent(text.substring(text.lastIndexOf("/") + 1));
    }

    function isProtectedItem(item) {
        return onDesktop && protectedNames.indexOf(fileNameOf(item)) >= 0;
    }

    // True when a protected icon is among the selected ones.
    function selectionProtected() {
        if (!onDesktop || !grid || !mapper)
            return false;
        for (let i = 0; i < grid.count; ++i) {
            const modelIndex = mapper.map(i);
            if (modelIndex >= 0 && folderModel.isSelected(modelIndex) && isProtectedItem(grid.itemAtIndex(i)))
                return true;
        }
        return false;
    }

    // The menu of a right-clicked (or Menu-key) item; `point` is where
    // the pointer is, in the view's coordinates, or null for the keyboard.
    // Returns false when Plasma's own menu is the right one (every
    // ordinary file).
    function itemMenu(item, point) {
        if (!item || !onDesktop)
            return false;
        let menu = itemMenuObject;
        if (isProtectedItem(item)) {
            itemMenuObject.protectedName = fileNameOf(item);
        } else {
            // Every other file and folder: Windows 11's menu, whose
            // Properties is VeltOS' window, not KDE's dialog.
            fileMenuObject.names = selectedNames(fileNameOf(item));
            fileMenuObject.isDir = item.isDir === true;
            menu = fileMenuObject;
        }
        if (point) {
            menu.visualParent = view;
            menu.open(Math.round(point.x), Math.round(point.y));
        } else {
            menu.visualParent = item;
            menu.openRelative();
        }
        return true;
    }

    // The names of the selected icons; `clicked` first, and alone when it
    // is not selected (a right-click on an unselected icon).
    function selectedNames(clicked) {
        const names = [];
        if (grid && mapper) {
            for (let i = 0; i < grid.count; ++i) {
                const modelIndex = mapper.map(i);
                const item = grid.itemAtIndex(i);
                if (modelIndex >= 0 && item && folderModel.isSelected(modelIndex)) {
                    const name = fileNameOf(item);
                    if (name !== "" && protectedNames.indexOf(name) < 0)
                        names.push(name);
                }
            }
        }
        if (names.indexOf(clicked) < 0)
            return [clicked];
        return [clicked].concat(names.filter(name => name !== clicked));
    }

    // Shift+Delete: Windows 11's "Delete File" question from File Explorer
    // (veltos-explorer --delete-permanently) instead of KDE's dialog, which
    // belonged to plasmashell and showed as "plasmashell" on the taskbar
    // (product owner, 2026-10-26).
    function deletePermanently() {
        const names = [];
        if (grid && mapper) {
            for (let i = 0; i < grid.count; ++i) {
                const modelIndex = mapper.map(i);
                const item = grid.itemAtIndex(i);
                if (modelIndex >= 0 && item && folderModel.isSelected(modelIndex)) {
                    const name = fileNameOf(item);
                    if (name !== "" && protectedNames.indexOf(name) < 0)
                        names.push(name);
                }
            }
        }
        if (names.length > 0)
            shell.connectSource("veltos-explorer --delete-permanently " + itemArguments(names));
    }

    // Paste (Ctrl+V and the menu): files go through File Explorer's
    // Windows 11 copy window (veltos-explorer --transfer), with Windows'
    // "name - Copy" for a copy into the same folder; KDE's "File Already
    // Exists" dialog belonged to plasmashell (product owner, 2026-10-26).
    // Anything else on the clipboard (a picture, text) is Plasma's paste.
    KQuickAddons.Clipboard { id: clipboard }

    function paste() {
        const formats = clipboard.formats || [];
        if (formats.indexOf("text/uri-list") < 0) {
            folderModel.paste();
            return;
        }
        const urls = clipboard.contentFormat("text/uri-list") || [];
        const paths = [];
        for (let i = 0; i < urls.length; ++i) {
            const path = localPath(String(urls[i]));
            if (!path) {
                folderModel.paste();       // network files: KIO
                return;
            }
            paths.push(path);
        }
        if (paths.length === 0)
            return;
        // KDE marks cut files with "1" in application/x-kde-cutselection.
        let cut = false;
        if (formats.indexOf("application/x-kde-cutselection") >= 0) {
            const mark = clipboard.contentFormat("application/x-kde-cutselection");
            cut = mark && mark.byteLength > 0 && new Uint8Array(mark)[0] === 49;
        }
        const folder = "\"$(/usr/libexec/veltos/desktop-new " + quoted(folderArgument()) + " path)\"";
        shell.connectSource("veltos-explorer --transfer " + (cut ? "move " : "copy ") + folder + " "
                            + paths.map(quoted).join(" "));
        if (cut)
            clipboard.clear();
    }

    // The items as shell words: "$(desktop folder)/name" (the desktop is
    // desktop:/ to Plasma; desktop-new knows its real path).
    function itemArguments(names) {
        const folder = "\"$(/usr/libexec/veltos/desktop-new " + quoted(folderArgument()) + " path)\"/";
        return names.map(name => folder + quoted(name)).join(" ");
    }

    // --- The desktop's menu ----------------------------------------------

    function desktopMenu(point) {
        desktopMenuObject.visualParent = view;
        if (point)
            desktopMenuObject.open(Math.round(point.x), Math.round(point.y));
        else
            desktopMenuObject.open(Math.round(view.width / 3), Math.round(view.height / 3));
    }

    function refresh() {
        if (folderModel)
            folderModel.refresh();
        blink.restart();
    }

    // Windows blinks the icons on Refresh.
    SequentialAnimation {
        id: blink
        NumberAnimation { target: veltos.grid; property: "opacity"; to: 0; duration: 70 }
        NumberAnimation { target: veltos.grid; property: "opacity"; to: 1; duration: 180; easing.type: Easing.OutCubic }
    }

    // --- New folder / text document ---------------------------------------

    function localPath(url) {
        const text = String(url);
        return text.startsWith("file://") ? decodeURIComponent(text.substring(7)) : "";
    }

    function quoted(text) {
        return "'" + text.replace(/'/g, "'\\''") + "'";
    }

    // The folder as the helper takes it: Plasma keeps the desktop as
    // "desktop:/" (resolvedUrl stays desktop:/ too, VM 2026-10-22), which
    // desktop-new resolves from user-dirs.dirs; any other folder by path.
    function folderArgument() {
        const resolved = String(folderModel.resolvedUrl !== undefined ? folderModel.resolvedUrl : folderModel.url);
        return localPath(resolved) || String(folderModel.url);
    }

    // New file names, as Windows names them.
    readonly property var newNames: ({
        "folder": tr("New folder"),
        "text": tr("New Text Document.txt"),
        "word": tr("New Word Document.docx"),
        "slides": tr("New PowerPoint Presentation.pptx"),
        "sheet": tr("New Excel Worksheet.xlsx")
    })

    function createNew(kind) {
        shell.connectSource("/usr/libexec/veltos/desktop-new " + quoted(folderArgument()) + " " + kind + " "
                            + quoted(newNames[kind]));
    }

    // Word, PowerPoint and Excel documents need veltos-office.
    property bool officeNew: false
    readonly property string officeCheck: "test -x /usr/libexec/veltos-office/blank-document && echo office"
    Component.onCompleted: shell.connectSource(officeCheck)


    Plasma5Support.DataSource {
        id: shell
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => {
            disconnectSource(source);
            if (source === veltos.officeCheck)
                veltos.officeNew = String(data["stdout"] || "").trim() === "office";
            if (source.indexOf("/desktop-new ") < 0)
                return;
            const path = String(data["stdout"] || "").trim();
            if (path !== "") {
                renameWhenListed.name = path.substring(path.lastIndexOf("/") + 1);
                renameWhenListed.tries = 0;
                renameWhenListed.restart();
            }
        }
    }

    // The folder view lists the new item a moment later (KDirLister);
    // then it is made current and selected, and once the view's current
    // item is really that delegate, its name is opened for editing. (The
    // model's indexForUrl and an immediate rename() edited the item that
    // was current before, VM 2026-10-22.)
    Timer {
        id: renameWhenListed
        property string name
        property int tries: 0
        interval: 80
        repeat: true
        onTriggered: {
            let target = null;
            for (let i = 0; i < grid.count; ++i) {
                const item = grid.itemAtIndex(i);
                if (item && !item.blank && fileNameOf(item) === name) {
                    target = item;
                    break;
                }
            }
            if (target) {
                if (grid.currentIndex !== target.index) {
                    folderModel.clearSelection();
                    grid.currentIndex = target.index;
                    folderModel.setSelected(mapper.map(target.index));
                } else if (grid.currentItem === target) {
                    stop();
                    view.rename();
                    return;
                }
            }
            if (++tries > 50)
                stop();
        }
    }

    function openSettings(page) {
        shell.connectSource("veltos-settings " + page);
    }

    // --- Menus -------------------------------------------------------------

    PlasmaExtras.Menu {
        id: desktopMenuObject
        placement: PlasmaExtras.Menu.BottomPosedRightAlignedPopup

        // Submenus are declared as a property of their item, as Plasma's
        // task manager menu does (a MenuItem has no default property).
        PlasmaExtras.MenuItem {
            id: viewItem
            text: veltos.tr("View")
            icon: "view-list-icons"
            readonly property PlasmaExtras.Menu submenu: PlasmaExtras.Menu {
                visualParent: viewItem.action
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Large icons")
                    checkable: true
                    checked: Plasmoid.configuration.iconSize >= 4
                    onClicked: Plasmoid.configuration.iconSize = 4
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Medium icons")
                    checkable: true
                    checked: Plasmoid.configuration.iconSize >= 2 && Plasmoid.configuration.iconSize < 4
                    onClicked: Plasmoid.configuration.iconSize = 2
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Small icons")
                    checkable: true
                    checked: Plasmoid.configuration.iconSize < 2
                    onClicked: Plasmoid.configuration.iconSize = 1
                }
                PlasmaExtras.MenuItem { separator: true }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Auto arrange icons")
                    checkable: true
                    checked: Plasmoid.configuration.sortMode !== -1
                    onClicked: Plasmoid.configuration.sortMode = Plasmoid.configuration.sortMode === -1 ? 2 : -1
                }
            }
        }
        PlasmaExtras.MenuItem {
            id: sortItem
            text: veltos.tr("Sort by")
            icon: "view-sort"
            readonly property PlasmaExtras.Menu submenu: PlasmaExtras.Menu {
                visualParent: sortItem.action
                // KDirModel's columns: 0 name, 1 size, 2 modified, 6 type.
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Name")
                    checkable: true
                    checked: Plasmoid.configuration.sortMode === 0
                    onClicked: Plasmoid.configuration.sortMode = 0
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Size")
                    checkable: true
                    checked: Plasmoid.configuration.sortMode === 1
                    onClicked: Plasmoid.configuration.sortMode = 1
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Item type")
                    checkable: true
                    checked: Plasmoid.configuration.sortMode === 6
                    onClicked: Plasmoid.configuration.sortMode = 6
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Date modified")
                    checkable: true
                    checked: Plasmoid.configuration.sortMode === 2
                    onClicked: Plasmoid.configuration.sortMode = 2
                }
            }
        }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Refresh")
            icon: "view-refresh"
            onClicked: veltos.refresh()
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            // Plasma's Paste text, icon and state (enabled while the
            // clipboard holds files); the paste itself is veltos.paste().
            readonly property var plasmaPaste: veltos.folderModel ? veltos.folderModel.action("paste") : null
            text: plasmaPaste ? plasmaPaste.text : veltos.tr("Paste")
            icon: "edit-paste"
            enabled: !!plasmaPaste && plasmaPaste.enabled
            onClicked: veltos.paste()
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            id: newItem
            text: veltos.tr("New")
            icon: "list-add"
            readonly property PlasmaExtras.Menu submenu: PlasmaExtras.Menu {
                visualParent: newItem.action
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Folder")
                    icon: "folder"
                    onClicked: veltos.createNew("folder")
                }
                PlasmaExtras.MenuItem { separator: true }
                // Windows 11's order with Office (by extension): Word,
                // PowerPoint, Text, Excel.
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Word Document")
                    icon: "x-office-document"
                    visible: veltos.officeNew
                    onClicked: veltos.createNew("word")
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("PowerPoint Presentation")
                    icon: "x-office-presentation"
                    visible: veltos.officeNew
                    onClicked: veltos.createNew("slides")
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Text Document")
                    icon: "text-plain"
                    onClicked: veltos.createNew("text")
                }
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Excel Worksheet")
                    icon: "x-office-spreadsheet"
                    visible: veltos.officeNew
                    onClicked: veltos.createNew("sheet")
                }
            }
        }
        PlasmaExtras.MenuItem { separator: true }
        // Line icons like the other entries (Fluent's 16 px monitor and
        // brush; the preferences-* names are coloured app icons).
        PlasmaExtras.MenuItem {
            text: veltos.tr("Display settings")
            icon: "monitor"
            onClicked: veltos.openSettings("display")
        }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Personalize")
            icon: "draw-brush"
            onClicked: veltos.openSettings("personalization")
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Open in Terminal")
            icon: "utilities-terminal"
            onClicked: shell.connectSource("konsole --notransparency --workdir \"$(/usr/libexec/veltos/desktop-new "
                                           + veltos.quoted(veltos.folderArgument()) + " path)\"")
        }
    }

    // Windows 11's menu of a file or folder on the desktop.
    PlasmaExtras.Menu {
        id: fileMenuObject
        property var names: []
        property bool isDir: false
        readonly property bool single: names.length === 1
        placement: PlasmaExtras.Menu.BottomPosedRightAlignedPopup

        PlasmaExtras.MenuItem {
            text: veltos.tr("Open")
            icon: fileMenuObject.isDir ? "folder-open" : "document-open"
            onClicked: veltos.folderModel.runSelected()
        }
        PlasmaExtras.MenuItem {
            visible: fileMenuObject.single && !fileMenuObject.isDir
            text: veltos.tr("Open with")
            icon: "document-open"
            // Windows 11's "Select an app" window (File Explorer).
            onClicked: shell.connectSource("veltos-explorer --open-with " + veltos.itemArguments(fileMenuObject.names))
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Cut")
            icon: "edit-cut"
            onClicked: veltos.folderModel.cut()
        }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Copy")
            icon: "edit-copy"
            onClicked: veltos.folderModel.copy()
        }
        PlasmaExtras.MenuItem {
            visible: fileMenuObject.single
            text: veltos.tr("Rename")
            icon: "edit-rename"
            onClicked: veltos.view.rename()
        }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Delete")
            icon: "edit-delete"
            onClicked: {
                const action = veltos.folderModel.action("trash");
                if (action && action.enabled)
                    action.trigger();
            }
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Compress to ZIP file")
            icon: "archive-insert"
            onClicked: shell.connectSource("veltos-explorer --compress " + veltos.itemArguments(fileMenuObject.names))
        }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            text: veltos.tr("Properties")
            icon: "document-properties"
            onClicked: shell.connectSource("veltos-explorer --properties " + veltos.itemArguments(fileMenuObject.names))
        }
    }

    // The menu of the Recycle Bin, This PC and the Store: no Delete, no
    // Rename, no Cut.
    PlasmaExtras.Menu {
        id: itemMenuObject
        property string protectedName
        placement: PlasmaExtras.Menu.BottomPosedRightAlignedPopup

        PlasmaExtras.MenuItem {
            text: veltos.tr("Open")
            icon: "document-open"
            onClicked: veltos.folderModel.runSelected()
        }
        PlasmaExtras.MenuItem {
            visible: itemMenuObject.protectedName === "recycle-bin.desktop"
            text: veltos.tr("Empty Recycle Bin")
            icon: "trash-empty"
            // File Explorer asks in a Windows 11 dialog, then empties the bin.
            onClicked: shell.connectSource("veltos-explorer --empty-recycle-bin")
        }
        PlasmaExtras.MenuItem {
            visible: itemMenuObject.protectedName !== "veltos-store.desktop"
            separator: true
        }
        PlasmaExtras.MenuItem {
            visible: itemMenuObject.protectedName === "this-pc.desktop"
            text: veltos.tr("Properties")
            icon: "document-properties"
            // "System > About", as Windows opens it for This PC.
            onClicked: veltos.openSettings("about")
        }
        PlasmaExtras.MenuItem {
            visible: itemMenuObject.protectedName === "recycle-bin.desktop"
            text: veltos.tr("Properties")
            icon: "document-properties"
            // VeltOS' Properties window for the bin (what is in it), not KDE's dialog.
            onClicked: shell.connectSource("veltos-explorer --properties \"${XDG_DATA_HOME:-$HOME/.local/share}/Trash/files\"")
        }
    }
}
