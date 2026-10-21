/*
    VeltOS Archive window, in WinRAR's layout with Windows 11 controls:
    the menu bar (File, Commands, Help), WinRAR's toolbar of large
    pictures (Add, Extract To, Test, View, Delete, Find, Info), the up
    button and the archive path ("photos.zip\2024 - ZIP archive, unpacked
    size ... bytes"), the file list (Name, Size, Packed, Type, Modified,
    CRC32; ".." goes up) and the status bar (lock when encrypted, selection
    or totals). `backend` is app.Backend.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window

    width: 1000
    height: 640
    minimumWidth: 640
    minimumHeight: 400
    visible: true
    title: backend.isOpen ? backend.archiveName + " - " + backend.texts.app_title : backend.texts.app_title
    color: Theme.window

    property var selection: []
    property int anchorIndex: -1
    readonly property var rows: backend.rows
    readonly property bool hasUp: backend.isOpen && (backend.folder !== "" || backend.findQuery !== "")
    readonly property var columns: [
        { key: "name", label: backend.texts.col_name, width: -1 },
        { key: "size", label: backend.texts.col_size, width: 104, right: true },
        { key: "packed", label: backend.texts.col_packed, width: 104, right: true },
        { key: "type", label: backend.texts.col_type, width: 170 },
        { key: "modified", label: backend.texts.col_modified, width: 150 },
        { key: "crc", label: backend.texts.col_crc, width: 92 }
    ]

    function select(index, modifiers) {
        const path = rows[index].path;
        if (modifiers & Qt.ShiftModifier && anchorIndex >= 0) {
            const from = Math.min(anchorIndex, index), to = Math.max(anchorIndex, index);
            selection = rows.slice(from, to + 1).map(r => r.path);
        } else if (modifiers & Qt.ControlModifier) {
            selection = selection.includes(path) ? selection.filter(p => p !== path) : selection.concat([path]);
            anchorIndex = index;
        } else {
            selection = [path];
            anchorIndex = index;
        }
    }
    function selectAll() {
        selection = rows.map(r => r.path);
    }
    function startExtract() {
        extractDialog.prepare();
        extractDialog.open();
    }
    function startDelete() {
        if (selection.length > 0 && backend.canDelete) {
            confirmDelete.open();
        }
    }
    function viewSelected() {
        const files = rows.filter(r => selection.includes(r.path) && !r.isDir);
        if (files.length > 0) {
            backend.viewItem(files[0].path);
        }
    }
    function addFiles() {
        addFileDialog.open();
    }

    Connections {
        target: backend
        function onListingChanged() {
            window.selection = window.selection.filter(p => window.rows.some(r => r.path === p));
        }
        function onPasswordNeeded(reason) {
            passwordDialog.mode = reason;
            passwordDialog.archiveName = backend.archiveName;
            passwordDialog.open();
        }
        function onNotice(title, body) {
            notice.title = title;
            notice.body = body;
            notice.folder = "";
            notice.open();
        }
        function onExtracted(folder) {
            notice.title = backend.texts.app_title;
            notice.body = backend.texts.done_extract.replace("{folder}", folder);
            notice.folder = folder;
            notice.open();
        }
    }

    Shortcut { sequences: [StandardKey.Open]; onActivated: openDialog.open() }
    Shortcut { sequences: ["Alt+E"]; enabled: backend.isOpen; onActivated: window.startExtract() }
    Shortcut { sequences: ["Alt+A"]; onActivated: window.addFiles() }
    Shortcut { sequences: ["Alt+T"]; enabled: backend.isOpen; onActivated: backend.test() }
    Shortcut { sequences: ["Alt+I"]; enabled: backend.isOpen; onActivated: info.open() }
    Shortcut { sequences: [StandardKey.Delete]; enabled: backend.isOpen; onActivated: window.startDelete() }
    Shortcut { sequences: [StandardKey.SelectAll]; enabled: backend.isOpen; onActivated: window.selectAll() }
    Shortcut { sequences: [StandardKey.Find, "F3"]; enabled: backend.isOpen; onActivated: findField.forceActiveFocus() }
    Shortcut { sequences: ["Backspace"]; enabled: window.hasUp && !findField.activeFocus; onActivated: backend.goUp() }

    menuBar: Rectangle {
        implicitHeight: 32
        color: Theme.bar
        Row {
            anchors.left: parent.left
            anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Repeater {
                model: [{ label: backend.texts.menu_file, menu: fileMenu },
                        { label: backend.texts.menu_commands, menu: commandsMenu },
                        { label: backend.texts.menu_help, menu: helpMenu }]
                delegate: AbstractButton {
                    id: menuButton
                    required property var modelData
                    implicitWidth: menuLabel.implicitWidth + 20
                    implicitHeight: 26
                    hoverEnabled: true
                    focusPolicy: Qt.NoFocus
                    onClicked: modelData.menu.popup(menuButton, 0, menuButton.height)
                    background: Rectangle {
                        radius: Theme.smallRadius
                        color: menuButton.down || menuButton.modelData.menu.visible ? Theme.pressed
                                                                                    : (menuButton.hovered ? Theme.hover : "transparent")
                    }
                    contentItem: Text {
                        id: menuLabel
                        text: menuButton.modelData.label
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }

    Menu {
        id: fileMenu
        MenuItem { text: backend.texts.open_archive; onTriggered: openDialog.open() }
        MenuItem { text: backend.texts.new_archive; onTriggered: window.addFiles() }
        MenuSeparator {}
        MenuItem { text: backend.texts.exit; onTriggered: window.close() }
    }
    Menu {
        id: commandsMenu
        MenuItem { text: backend.texts.add; enabled: backend.canAdd; onTriggered: window.addFiles() }
        MenuItem { text: backend.texts.extract_to; enabled: backend.isOpen; onTriggered: window.startExtract() }
        MenuItem { text: backend.texts.test; enabled: backend.isOpen; onTriggered: backend.test() }
        MenuItem { text: backend.texts.view; enabled: window.selection.length > 0; onTriggered: window.viewSelected() }
        MenuItem { text: backend.texts.delete; enabled: backend.canDelete && window.selection.length > 0; onTriggered: window.startDelete() }
        MenuItem { text: backend.texts.find; enabled: backend.isOpen; onTriggered: findField.forceActiveFocus() }
        MenuItem { text: backend.texts.info; enabled: backend.isOpen; onTriggered: info.open() }
    }
    Menu {
        id: helpMenu
        MenuItem { text: backend.texts.about; onTriggered: about.open() }
    }

    FileDialog {
        id: openDialog
        title: backend.texts.open_archive
        nameFilters: ["Archives (*.zip *.rar *.7z *.tar *.gz *.tgz *.bz2 *.xz *.zst *.iso *.cab *.arj *.lzh *.001)",
                      "All files (*)"]
        onAccepted: backend.openArchive(selectedFile.toString())
    }
    FileDialog {
        id: addFileDialog
        title: backend.texts.add
        fileMode: FileDialog.OpenFiles
        onAccepted: {
            const files = selectedFiles.map(f => f.toString());
            if (backend.isOpen && backend.canAdd) {
                backend.addFiles(files);
            } else {
                addDialog.prepare(files);
                addDialog.open();
            }
        }
    }
    FolderDialog {
        id: folderDialog
        onAccepted: destinationField.text = decodeURIComponent(selectedFolder.toString().replace("file://", ""))
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // WinRAR's toolbar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 82
            color: Theme.bar
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 2
                ToolbarButton { objectName: "toolAdd"; picture: "add"; text: backend.texts.add; enabled: backend.canAdd; onClicked: window.addFiles() }
                ToolbarButton { objectName: "toolExtract"; picture: "extract"; text: backend.texts.extract_to; enabled: backend.isOpen; onClicked: window.startExtract() }
                ToolbarButton { objectName: "toolTest"; picture: "test"; text: backend.texts.test; enabled: backend.isOpen; onClicked: backend.test() }
                ToolbarButton { objectName: "toolView"; picture: "view"; text: backend.texts.view; enabled: window.selection.length > 0; onClicked: window.viewSelected() }
                ToolbarButton { objectName: "toolDelete"; picture: "delete"; text: backend.texts.delete; enabled: backend.canDelete && window.selection.length > 0; onClicked: window.startDelete() }
                ToolbarButton { objectName: "toolFind"; picture: "find"; text: backend.texts.find; enabled: backend.isOpen; onClicked: findField.forceActiveFocus() }
                ToolbarButton { objectName: "toolInfo"; picture: "info"; text: backend.texts.info; enabled: backend.isOpen; onClicked: info.open() }
                Item { Layout.fillWidth: true }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.divider
            }
        }

        // Up button, archive path, find
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 8
            spacing: 6
            AbstractButton {
                id: upButton
                objectName: "upButton"
                enabled: window.hasUp
                implicitWidth: 34
                implicitHeight: 32
                hoverEnabled: true
                focusPolicy: Qt.NoFocus
                Accessible.name: backend.texts.up
                ToolTip.visible: hovered
                ToolTip.delay: 600
                ToolTip.text: backend.texts.up
                onClicked: backend.goUp()
                background: Rectangle {
                    radius: Theme.smallRadius
                    color: upButton.down ? Theme.pressed : (upButton.hovered && upButton.enabled ? Theme.hover : "transparent")
                }
                contentItem: Canvas {
                    opacity: upButton.enabled ? 1 : 0.35
                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        ctx.strokeStyle = Theme.text;
                        ctx.lineWidth = 1.4;
                        ctx.lineCap = "round";
                        ctx.lineJoin = "round";
                        const cx = width / 2, cy = height / 2;
                        ctx.beginPath();
                        ctx.moveTo(cx, cy + 6);
                        ctx.lineTo(cx, cy - 6);
                        ctx.moveTo(cx - 5, cy - 1);
                        ctx.lineTo(cx, cy - 6);
                        ctx.lineTo(cx + 5, cy - 1);
                        ctx.stroke();
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 32
                radius: Theme.smallRadius
                color: Theme.card
                border.color: Theme.cardBorder
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 8
                    Kirigami.Icon {
                        visible: backend.isOpen
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        source: "veltos-archive"
                    }
                    Text {
                        objectName: "headerText"
                        Layout.fillWidth: true
                        text: backend.headerText
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideMiddle
                    }
                }
            }
            TextBox {
                id: findField
                objectName: "findField"
                enabled: backend.isOpen
                Layout.preferredWidth: 240
                placeholderText: backend.texts.find_placeholder
                onTextChanged: backend.setFind(text)
                Keys.onEscapePressed: text = ""
            }
        }

        // The file list
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 8
            Layout.rightMargin: 8
            radius: Theme.radius
            color: Theme.list
            border.color: Theme.cardBorder
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 1
                spacing: 0
                visible: backend.isOpen

                // column headers
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 32
                    color: "transparent"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 0
                        Repeater {
                            model: window.columns
                            delegate: AbstractButton {
                                id: header
                                required property var modelData
                                objectName: "sort_" + modelData.key
                                Layout.fillWidth: modelData.width < 0
                                Layout.preferredWidth: modelData.width < 0 ? 200 : modelData.width
                                implicitHeight: 32
                                hoverEnabled: true
                                focusPolicy: Qt.NoFocus
                                onClicked: backend.sortBy(modelData.key)
                                background: Rectangle {
                                    color: header.hovered ? Theme.hover : "transparent"
                                    Rectangle {
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 1
                                        height: 16
                                        color: Theme.divider
                                    }
                                }
                                contentItem: RowLayout {
                                    spacing: 4
                                    layoutDirection: header.modelData.right ? Qt.RightToLeft : Qt.LeftToRight
                                    Text {
                                        text: header.modelData.label
                                        color: Theme.subtext
                                        font.pixelSize: Theme.captionSize
                                        leftPadding: 6
                                        rightPadding: 6
                                    }
                                    Text {
                                        visible: backend.sortKey === header.modelData.key
                                        text: backend.sortAscending ? "▴" : "▾"
                                        color: Theme.subtext
                                        font.pixelSize: Theme.captionSize
                                    }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: Theme.divider
                    }
                }

                ListView {
                    id: list
                    objectName: "fileList"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    model: window.rows
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                    header: window.hasUp ? upRow : null

                    Component {
                        id: upRow
                        Rectangle {
                            width: list.width
                            height: 28
                            color: upHover.hovered ? Theme.hover : "transparent"
                            HoverHandler { id: upHover }
                            TapHandler { onDoubleTapped: backend.goUp() }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 16
                                spacing: 8
                                Kirigami.Icon {
                                    Layout.preferredWidth: 18
                                    Layout.preferredHeight: 18
                                    source: "folder"
                                }
                                Text { text: ".."; color: Theme.text; font.pixelSize: Theme.bodySize }
                            }
                        }
                    }

                    delegate: Rectangle {
                        id: row
                        required property int index
                        required property var modelData
                        readonly property bool isSelected: window.selection.includes(modelData.path)
                        width: ListView.view.width
                        height: 28
                        color: isSelected ? Theme.selected : (rowHover.hovered ? Theme.hover : "transparent")
                        radius: Theme.smallRadius

                        HoverHandler { id: rowHover }
                        TapHandler {
                            acceptedButtons: Qt.LeftButton
                            onTapped: (point, button) => window.select(row.index, point.modifiers)
                            onDoubleTapped: backend.openRow(row.modelData.path)
                        }
                        TapHandler {
                            acceptedButtons: Qt.RightButton
                            onTapped: {
                                if (!row.isSelected) {
                                    window.select(row.index, 0);
                                }
                                rowMenu.popup();
                            }
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 0
                            Item {
                                Layout.fillWidth: true
                                Layout.preferredWidth: 200
                                implicitHeight: 28
                                Kirigami.Icon {
                                    id: fileIcon
                                    x: 6
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 18
                                    height: 18
                                    source: row.modelData.icon
                                    fallback: row.modelData.isDir ? "folder" : "text-x-generic"
                                }
                                Text {
                                    anchors.left: fileIcon.right
                                    anchors.leftMargin: 8
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: row.modelData.name + (row.modelData.encrypted ? " *" : "")
                                    color: Theme.text
                                    font.pixelSize: Theme.bodySize
                                    elide: Text.ElideRight
                                }
                            }
                            Repeater {
                                model: [{ k: "size", w: 104, r: true }, { k: "packed", w: 104, r: true },
                                        { k: "type", w: 170 }, { k: "modified", w: 150 }, { k: "crc", w: 92 }]
                                delegate: Text {
                                    required property var modelData
                                    Layout.preferredWidth: modelData.w
                                    leftPadding: 6
                                    rightPadding: 6
                                    horizontalAlignment: modelData.r ? Text.AlignRight : Text.AlignLeft
                                    text: (row.modelData.isDir && (modelData.k === "crc")) ? "" : row.modelData[modelData.k]
                                    color: Theme.subtext
                                    font.pixelSize: Theme.bodySize
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: backend.findQuery !== "" && list.count === 0
                        text: backend.texts.no_results.replace("{query}", backend.findQuery)
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                    }
                }
            }

            // No archive open yet
            ColumnLayout {
                objectName: "emptyState"
                visible: !backend.isOpen && !backend.busy
                anchors.centerIn: parent
                width: Math.min(parent.width - 64, 460)
                spacing: 12
                Kirigami.Icon {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 96
                    Layout.preferredHeight: 96
                    source: "veltos-archive"
                }
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: backend.texts.empty_title
                    color: Theme.text
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: backend.texts.empty_body
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.Wrap
                }
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 8
                    spacing: 8
                    WinButton { objectName: "openButton"; accent: true; text: backend.texts.open_archive; onClicked: openDialog.open() }
                    WinButton { text: backend.texts.new_archive; onClicked: window.addFiles() }
                }
            }

            // Opening (listing) an archive
            ColumnLayout {
                visible: backend.busy
                anchors.centerIn: parent
                spacing: 10
                BusyIndicator { Layout.alignment: Qt.AlignHCenter; running: backend.busy }
                Text {
                    text: backend.texts.opening.replace("{name}", backend.archiveName)
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                }
            }
        }

        // Status bar
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 14
            Layout.rightMargin: 14
            implicitHeight: 30
            spacing: 8
            Text {
                visible: backend.locked
                text: "🔒"
                font.pixelSize: Theme.captionSize
            }
            Text {
                objectName: "statusText"
                Layout.fillWidth: true
                text: backend.isOpen ? backend.selectionText(window.selection) : ""
                color: Theme.subtext
                font.pixelSize: Theme.captionSize
                elide: Text.ElideRight
            }
        }
    }

    // Files dropped on the window: added to the open archive, or a new
    // archive (an archive dropped alone is opened).
    DropArea {
        anchors.fill: parent
        onDropped: drop => {
            if (!drop.hasUrls) {
                return;
            }
            const urls = drop.urls.map(u => u.toString());
            if (urls.length === 1 && /\.(zip|rar|7z|tar|gz|tgz|bz2|xz|zst|iso|cab|001)$/i.test(urls[0]) && !backend.isOpen) {
                backend.openArchive(urls[0]);
            } else if (backend.isOpen && backend.canAdd) {
                backend.addFiles(urls);
            } else {
                addDialog.prepare(urls);
                addDialog.open();
            }
            drop.accept();
        }
    }

    Menu {
        id: rowMenu
        MenuItem { text: backend.texts.view; onTriggered: window.viewSelected() }
        MenuItem { text: backend.texts.extract_to; onTriggered: window.startExtract() }
        MenuItem { text: backend.texts.delete; enabled: backend.canDelete; onTriggered: window.startDelete() }
        MenuSeparator {}
        MenuItem { text: backend.texts.info; onTriggered: info.open() }
    }

    // --- dialogs ---------------------------------------------------------------------------

    WinDialog {
        id: extractDialog
        objectName: "extractDialog"
        title: backend.texts.extract_title
        width: Math.min(600, window.width - 48)
        property string overwrite: "rename"
        function prepare() {
            destinationField.text = backend.defaultDestination();
            overwrite = "rename";
        }
        Text {
            text: backend.texts.destination
            color: Theme.text
            font.pixelSize: Theme.bodySize
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            TextBox {
                id: destinationField
                objectName: "destinationField"
                Layout.fillWidth: true
                selectByMouse: true
            }
            WinButton { text: backend.texts.browse; onClicked: folderDialog.open() }
        }
        Text {
            Layout.topMargin: 6
            text: backend.texts.overwrite_mode
            color: Theme.text
            font.pixelSize: Theme.bodySize
            font.weight: Font.DemiBold
        }
        Repeater {
            model: [{ k: "rename", l: backend.texts.overwrite_rename }, { k: "overwrite", l: backend.texts.overwrite_all },
                    { k: "skip", l: backend.texts.overwrite_skip }]
            delegate: Choice {
                required property var modelData
                text: modelData.l
                selected: extractDialog.overwrite === modelData.k
                onClicked: extractDialog.overwrite = modelData.k
            }
        }
        buttons: [
            Item { Layout.fillWidth: true },
            WinButton {
                objectName: "extractOk"
                accent: true
                text: backend.texts.ok
                enabled: destinationField.text.trim() !== ""
                onClicked: {
                    extractDialog.close();
                    backend.extract(destinationField.text.trim(), window.selection, extractDialog.overwrite);
                }
            },
            WinButton { text: backend.texts.cancel; onClicked: extractDialog.close() }
        ]
    }

    AddDialog {
        id: addDialog
        onAccepted: (name, format, level, password, names) => backend.createArchive(sources, name, format, level, password, names)
    }

    PasswordDialog {
        id: passwordDialog
        onAccepted: (password, names) => backend.setPassword(password)
        onRejected: backend.cancelPassword()
    }

    WinDialog {
        id: confirmDelete
        title: backend.texts.confirm_delete.replace("{count}", window.selection.length)
        Text {
            text: backend.texts.confirm_delete_body
            color: Theme.text
            font.pixelSize: Theme.bodySize
        }
        buttons: [
            Item { Layout.fillWidth: true },
            WinButton {
                accent: true
                text: backend.texts.delete
                onClicked: {
                    confirmDelete.close();
                    backend.deleteItems(window.selection);
                }
            },
            WinButton { text: backend.texts.cancel; onClicked: confirmDelete.close() }
        ]
    }

    WinDialog {
        id: info
        objectName: "infoDialog"
        title: backend.texts.info_title
        Repeater {
            model: backend.infoRows
            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                Text {
                    Layout.preferredWidth: 160
                    text: modelData.label
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                }
                Text {
                    Layout.fillWidth: true
                    text: modelData.value
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                }
            }
        }
        buttons: [
            Item { Layout.fillWidth: true },
            WinButton { accent: true; text: backend.texts.close; onClicked: info.close() }
        ]
    }

    WinDialog {
        id: notice
        objectName: "noticeDialog"
        property string body: ""
        property string folder: ""
        Text {
            Layout.fillWidth: true
            text: notice.body
            color: Theme.text
            font.pixelSize: Theme.bodySize
            wrapMode: Text.Wrap
        }
        buttons: [
            Item { Layout.fillWidth: true },
            WinButton {
                visible: notice.folder !== ""
                text: backend.texts.show_files
                onClicked: {
                    notice.close();
                    backend.showFolder(notice.folder);
                }
            },
            WinButton { accent: true; text: backend.texts.ok; onClicked: notice.close() }
        ]
    }

    WinDialog {
        id: about
        title: backend.texts.about
        Text {
            Layout.fillWidth: true
            text: backend.texts.about_text
            color: Theme.text
            font.pixelSize: Theme.bodySize
            wrapMode: Text.Wrap
        }
        buttons: [
            Item { Layout.fillWidth: true },
            WinButton { accent: true; text: backend.texts.ok; onClicked: about.close() }
        ]
    }

    // WinRAR's progress window, over the archive window
    Popup {
        id: progress
        objectName: "progressPopup"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(480, window.width - 48)
        modal: true
        closePolicy: Popup.NoAutoClose
        visible: backend.job !== null && backend.job.running && backend.job.title !== ""
        padding: 24
        Overlay.modal: Rectangle { color: Theme.scrim }
        background: Rectangle { radius: Theme.radius; color: Theme.card; border.color: Theme.cardBorder }
        contentItem: ProgressPanel {
            job: backend.job
            onBackgroundRequested: window.showMinimized()
        }
    }
}
