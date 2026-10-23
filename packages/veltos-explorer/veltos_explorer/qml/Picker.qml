/*
    VeltOS file dialog ("Open", "Save As", "Select Folder") in the layout of
    Windows 11's dialogs: File Explorer's address bar, navigation pane and
    folder views, then the file name box with the file type drop-down and
    the buttons. `picker` (picker.py) holds the request and works out the
    answer; `backend` is File Explorer's.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    readonly property var tab: backend.current
    readonly property bool saving: picker.modeName === "save"
    readonly property bool folders: picker.modeName === "folder"
    readonly property bool renaming: loader.item && loader.item.renameRow !== undefined && loader.item.renameRow >= 0

    width: 940
    height: 620
    minimumWidth: 640
    minimumHeight: 440
    visible: true
    title: picker.title
    color: Theme.content

    onClosing: picker.cancel()

    function accept() { picker.accept(nameField.text); }

    Connections {
        target: backend
        function onMessage(text) { dialog.tell(text); }
    }
    Connections {
        target: picker
        function onMessage(text) { dialog.tell(text); }
        function onConfirmReplace(path, name) {
            dialog.ask(backend.text("confirm_save_as"), backend.format("replace_question", "name", name),
                       backend.text("yes"), backend.text("no"), () => picker.finish([path]));
        }
    }
    // The selection fills the file name box, as in Windows.
    Connections {
        target: window.tab.items
        function onSelectionChanged() {
            const text = picker.selectionText();
            if (text !== "")
                nameField.text = text;
        }
    }

    component DialogButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        implicitWidth: Math.max(96, buttonText.implicitWidth + 32)
        implicitHeight: 32
        radius: 5
        opacity: enabledState ? 1 : 0.5
        color: primary ? (buttonHover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                       : (buttonHover.hovered ? Theme.hover : Theme.field)
        border.width: primary ? 0 : 1
        border.color: Theme.fieldBorder
        activeFocusOnTab: enabledState
        Accessible.role: Accessible.Button
        Accessible.name: label
        Keys.onReturnPressed: if (enabledState) clicked()
        Keys.onSpacePressed: if (enabledState) clicked()
        Text {
            id: buttonText
            anchors.centerIn: parent
            text: button.label
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.fontSize
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 8
            color: "transparent"
            border.width: 2
            border.color: Theme.text
            visible: button.activeFocus
        }
        HoverHandler { id: buttonHover; enabled: button.enabledState }
        TapHandler { enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    // The file type drop-down ("All files", "Pictures", ...).
    component FilterBox: Rectangle {
        id: filterBox
        implicitHeight: 32
        radius: 4
        color: Theme.field
        border.width: 1
        border.color: filterHover.hovered ? Theme.accent : Theme.fieldBorder
        Accessible.role: Accessible.ComboBox
        Accessible.name: picker.filterNames[picker.filterIndex] || ""
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 8
            spacing: 6
            Text {
                Layout.fillWidth: true
                text: picker.filterNames[picker.filterIndex] || ""
                color: Theme.text
                font.pixelSize: Theme.fontSize
                elide: Text.ElideRight
            }
            Kirigami.Icon {
                Layout.preferredWidth: 12
                Layout.preferredHeight: 12
                source: "arrow-down"
                color: Theme.subtext
                isMask: true
            }
        }
        HoverHandler { id: filterHover; cursorShape: Qt.PointingHandCursor }
        TapHandler {
            onTapped: {
                filterMenu.items = picker.filterNames.map((name, index) => ({
                    text: name, action: String(index), checked: index === picker.filterIndex }));
                filterMenu.minimumWidth = filterBox.width;
                filterMenu.openAt(filterBox, 0, filterBox.height + 2);
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AddressBar {
            id: addressBar
            Layout.fillWidth: true
        }

        // Windows' dialogs: "New folder" on the left, the view switch on the right.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: Theme.toolbar
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 2
                IconButton {
                    icon: "folder-new"
                    text: backend.text("new_folder")
                    enabledState: window.tab.kind === "folder"
                    onClicked: backend.createNew("folder")
                }
                Item { Layout.fillWidth: true }
                IconButton {
                    icon: "view-list-details"
                    tooltip: backend.text("details")
                    checked: window.tab.viewMode === "details"
                    onClicked: window.tab.setViewMode("details")
                }
                IconButton {
                    icon: "view-list-icons"
                    tooltip: backend.text("large_icons")
                    checked: window.tab.viewMode === "large"
                    onClicked: window.tab.setViewMode("large")
                }
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.separator }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            NavPane {
                Layout.preferredWidth: 220
                Layout.fillHeight: true
            }
            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: Theme.separator }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Loader {
                    id: loader
                    anchors.fill: parent
                    sourceComponent: window.tab.kind === "home" ? homeComponent
                                     : window.tab.kind === "thispc" ? thisPcComponent : folderComponent
                    onLoaded: if (window.tab.kind !== "home" && window.tab.kind !== "thispc" && !window.saving)
                                  item.forceActiveFocus()
                }
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.separator }

        // File name, file type and the buttons.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: bottom.implicitHeight + 28
            color: Theme.toolbar
            GridLayout {
                id: bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: 14
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                columns: 3
                columnSpacing: 10
                rowSpacing: 10

                Text {
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                    text: window.folders ? backend.text("folder_label") : backend.text("file_name_label")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.columnSpan: window.saving || window.folders ? 2 : 1
                    implicitHeight: 32
                    radius: 4
                    color: Theme.field
                    border.width: 1
                    border.color: nameField.activeFocus ? Theme.accent : Theme.fieldBorder
                    TextInput {
                        id: nameField
                        // Like a Windows text box: in the Tab order, the text cursor over it and
                        // (in a layout) the full height of its box. A plain TextInput has neither.
                        activeFocusOnTab: true
                        HoverHandler { cursorShape: Qt.IBeamCursor }
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        verticalAlignment: TextInput.AlignVCenter
                        color: Theme.text
                        selectionColor: Theme.accent
                        selectedTextColor: "#FFFFFF"
                        font.pixelSize: Theme.fontSize
                        clip: true
                        text: picker.initialName
                        Accessible.role: Accessible.EditableText
                        Accessible.name: backend.text("file_name_label")
                        onAccepted: window.accept()
                        Component.onCompleted: {
                            if (window.saving) {
                                forceActiveFocus();
                                // The name without its extension is selected, as Windows does.
                                const dot = text.lastIndexOf(".");
                                select(0, dot > 0 ? dot : text.length);
                            }
                        }
                    }
                }
                FilterBox {
                    visible: !window.saving && !window.folders
                    Layout.preferredWidth: 230
                }
                Text {
                    visible: window.saving
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                    text: backend.text("save_as_type")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                }
                // As wide as the name box, like Windows' "Save as type": long
                // type names (LibreOffice's) were cut off at 300 px.
                FilterBox {
                    visible: window.saving
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                }
                Item {
                    Layout.columnSpan: 3
                    Layout.fillWidth: true
                    implicitHeight: 32
                    RowLayout {
                        anchors.right: parent.right
                        spacing: 8
                        DialogButton {
                            objectName: "acceptButton"
                            primary: true
                            label: picker.acceptLabel
                            onClicked: window.accept()
                        }
                        DialogButton {
                            objectName: "cancelButton"
                            label: backend.text("cancel")
                            onClicked: picker.cancel()
                        }
                    }
                }
            }
        }
    }

    // --- Views ----------------------------------------------------------------------
    Component {
        id: homeComponent
        HomeView {}
    }
    Component {
        id: thisPcComponent
        ThisPCView {}
    }
    Component {
        id: folderComponent
        FolderView {
            id: folderView
            onItemMenu: (x, y) => window.itemMenu(folderView, x, y)
            onBackgroundMenu: (x, y) => window.backgroundMenu(folderView, x, y)
            onRequestDelete: permanently => backend.deleteSelection(false)
            onShowMessage: text => dialog.tell(text)
        }
    }

    // --- Menus (a short version of File Explorer's) ---------------------------------
    WinMenu {
        id: contextMenu
        onTriggered: action => window.runAction(action)
    }
    WinMenu {
        id: filterMenu
        onTriggered: action => picker.setFilter(parseInt(action))
    }

    function itemMenu(item, x, y) {
        const chosen = window.tab.items.selectedList();
        if (chosen.length === 0)
            return;
        contextMenu.items = [
            { text: backend.text("open"), icon: chosen[0].isDir ? "folder-open" : "document-open", action: "open" },
            { separator: true },
            { text: backend.text("rename"), icon: "edit-rename", action: "rename", enabled: chosen.length === 1 },
            { text: backend.text("delete"), icon: "edit-delete", action: "delete" }
        ];
        contextMenu.openAt(item, x, y);
    }

    function backgroundMenu(item, x, y) {
        const views = [["large", "large_icons"], ["medium", "medium_icons"], ["small", "small_icons"],
                       ["details", "details"], ["tiles", "tiles"]]
            .map(v => ({ text: backend.text(v[1]), action: "view:" + v[0], checked: window.tab.viewMode === v[0] }));
        const sorts = [["name", "name"], ["modified", "date_modified"], ["type", "type"], ["size", "size"]]
            .map(s => ({ text: backend.text(s[1]), action: "sort:" + s[0], checked: window.tab.sortKey === s[0] }));
        contextMenu.items = [
            { text: backend.text("view"), icon: "view-list-icons", submenu: views },
            { text: backend.text("sort"), icon: "view-sort", submenu: sorts },
            { text: backend.text("refresh"), icon: "view-refresh", action: "refresh", shortcut: "F5" },
            { separator: true },
            { text: backend.text("new"), icon: "list-add", enabled: window.tab.kind === "folder", submenu: [
                { text: backend.text("folder"), icon: "folder", action: "new-folder" }
            ] }
        ];
        contextMenu.openAt(item, x, y);
    }

    function runAction(action) {
        const view = loader.item;
        if (action === "open") backend.openSelection();
        else if (action === "rename" && view && view.startRename) view.startRename(window.tab.items.currentRow);
        else if (action === "delete") backend.deleteSelection(false);
        else if (action === "refresh") window.tab.refresh();
        else if (action === "new-folder") backend.createNew("folder");
        else if (action.startsWith("view:")) window.tab.setViewMode(action.slice(5));
        else if (action.startsWith("sort:")) window.tab.setSort(action.slice(5), window.tab.sortDescending);
    }

    WinDialog { id: dialog }

    // --- Keyboard ------------------------------------------------------------------
    Shortcut { sequence: "Escape"; enabled: !window.renaming && !dialog.opened; onActivated: picker.cancel() }
    Shortcut { sequences: ["F5", "Ctrl+R"]; onActivated: window.tab.refresh() }
    Shortcut { sequences: ["Alt+Left", StandardKey.Back]; onActivated: window.tab.back() }
    Shortcut { sequences: ["Alt+Right", StandardKey.Forward]; onActivated: window.tab.forward() }
    Shortcut { sequence: "Alt+Up"; onActivated: window.tab.up() }
    Shortcut { sequences: ["Ctrl+L", "Alt+D", "F4"]; onActivated: addressBar.editAddress() }
    Shortcut { sequences: ["Ctrl+F", "Ctrl+E", "F3"]; onActivated: addressBar.focusSearch() }
    Shortcut { sequence: "Ctrl+Shift+N"; onActivated: backend.createNew("folder") }
    Shortcut { sequence: "Ctrl+H"; onActivated: backend.setShowHidden(!backend.showHidden) }
}
