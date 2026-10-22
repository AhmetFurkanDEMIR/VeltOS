/*
    VeltOS: the Windows 11 behaviour of the desktop, added to Plasma's
    folder view (FolderView.qml, plasma-desktop 6.3) by
    update-plasma-overrides (org.kde.desktopcontainment.json):

    - the desktop's right-click menu is Windows 11's: View, Sort by,
      Refresh, Paste, New, Display settings, Personalize, Open in Terminal
      (Plasma's containment menu with "Enter Edit Mode", "Add Widgets",
      "Configure Desktop" never opens);
    - New > Folder / Text Document make the item at once and open its name
      for editing, as Windows does (Plasma asked the name in a dialog);
    - Refresh (menu or F5) blinks the icons like Windows;
    - the Recycle Bin, This PC and the VeltOS Store cannot be deleted,
      renamed or cut: their menu has Open (the Bin also Empty Recycle
      Bin), Properties where it makes sense, and nothing else; the Delete
      key, F2 and Ctrl+X skip them.

    Texts come from the veltos-desktop catalog (i18nd), not from the
    containment's, so KDE's own translations stay untouched.

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as Plasma5Support

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
        if (!item || !onDesktop || !isProtectedItem(item))
            return false;
        itemMenuObject.protectedName = fileNameOf(item);
        if (point) {
            itemMenuObject.visualParent = view;
            itemMenuObject.open(Math.round(point.x), Math.round(point.y));
        } else {
            itemMenuObject.visualParent = item;
            itemMenuObject.openRelative();
        }
        return true;
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

    function createNew(kind) {
        const name = kind === "folder" ? tr("New folder") : tr("New Text Document.txt");
        shell.connectSource("/usr/libexec/veltos/desktop-new " + quoted(folderArgument()) + " " + kind + " "
                            + quoted(name));
    }


    Plasma5Support.DataSource {
        id: shell
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => {
            disconnectSource(source);
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
            // Plasma's own Paste action (its text and icon): enabled while
            // the clipboard holds files.
            action: veltos.folderModel ? veltos.folderModel.action("paste") : null
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
                PlasmaExtras.MenuItem {
                    text: veltos.tr("Text Document")
                    icon: "text-plain"
                    onClicked: veltos.createNew("text")
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
            onClicked: veltos.folderModel.openPropertiesDialog()
        }
    }
}
