/*
    VeltOS Photos: the layout of Windows 11 Photos. Title bar with the app
    name and the search box, the navigation pane (Gallery, Favorites, the
    folders, Settings), the gallery grouped by month, and the viewer over
    it (opened from the gallery, or at once for a file Photos was started
    with).

    The window draws its own frame and shadow (frame.py keeps clicks on the
    shadow going to the windows behind) and resize borders that hand
    resizing to the window manager.

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
    readonly property int shadow: maximized || visibility === Window.FullScreen ? 0 : 12
    readonly property bool viewing: backend.viewerIndex >= 0
    property string pane: "gallery"        // gallery, favorites, folder:<path>, settings
    property bool slideshow: false

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }
    function showPane(id) {
        pane = id;
        if (id !== "settings")
            backend.setPage(id);
    }
    function tell(text) {
        messageBox.ask(backend.texts.app_title, text, [{ text: backend.texts.ok, action: "ok" }]);
    }
    function confirmDelete(path) {
        deleteQuestion.path = path;
        deleteQuestion.ask(backend.texts.delete_title,
                           backend.texts.delete_text.replace("{name}", path.split("/").pop()),
                           [{ text: backend.texts.delete, action: "delete" },
                            { text: backend.texts.cancel, action: "cancel" }]);
    }

    width: 1180
    height: 760
    minimumWidth: 560
    minimumHeight: 400
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: viewing && backend.viewerItem.path ? backend.viewerItem.path.split("/").pop() + " - " + backend.texts.app_title
                                               : backend.texts.app_title

    Connections {
        target: backend
        function onMessage(text) { toast.show(text); }
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
        onPressed: window.startSystemResize(edges)
    }
    readonly property int grip: 6
    Edge { edges: Qt.LeftEdge; cursorShape: Qt.SizeHorCursor; z: 10
           x: window.shadow - grip; y: window.shadow + grip; width: 2 * grip; height: window.height - 2 * window.shadow - 2 * grip }
    Edge { edges: Qt.RightEdge; cursorShape: Qt.SizeHorCursor; z: 10
           x: window.width - window.shadow - grip; y: window.shadow + grip; width: 2 * grip; height: window.height - 2 * window.shadow - 2 * grip }
    Edge { edges: Qt.TopEdge; cursorShape: Qt.SizeVerCursor; z: 10
           x: window.shadow + grip; y: window.shadow - grip; width: window.width - 2 * window.shadow - 2 * grip; height: grip + 2 }
    Edge { edges: Qt.BottomEdge; cursorShape: Qt.SizeVerCursor; z: 10
           x: window.shadow + grip; y: window.height - window.shadow - grip; width: window.width - 2 * window.shadow - 2 * grip; height: 2 * grip }
    Edge { edges: Qt.TopEdge | Qt.LeftEdge; cursorShape: Qt.SizeFDiagCursor; z: 10
           x: window.shadow - grip; y: window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.TopEdge | Qt.RightEdge; cursorShape: Qt.SizeBDiagCursor; z: 10
           x: window.width - window.shadow - grip; y: window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.BottomEdge | Qt.LeftEdge; cursorShape: Qt.SizeBDiagCursor; z: 10
           x: window.shadow - grip; y: window.height - window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor; z: 10
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

            // --- Title bar: app name, search, caption buttons -----------------------------
            Item {
                id: titleBar
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                visible: !window.slideshow

                DragHandler {
                    target: null
                    onActiveChanged: if (active) window.startSystemMove()
                }
                TapHandler { onDoubleTapped: window.toggleMaximized() }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    spacing: 10
                    Rectangle {
                        visible: window.viewing
                        implicitWidth: 36
                        implicitHeight: 32
                        radius: 4
                        color: backHover.hovered ? Theme.hover : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.back
                        Glyph { anchors.centerIn: parent; width: 14; height: 14; kind: "back" }
                        HoverHandler { id: backHover }
                        TapHandler { onTapped: backend.closeViewer() }
                    }
                    Image {
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        source: "image://icon/veltos-photos"
                        sourceSize: Qt.size(36, 36)
                        visible: status === Image.Ready
                    }
                    Text {
                        text: backend.texts.app_title
                        color: Theme.text
                        font.pixelSize: Theme.smallFont
                    }
                    Item { Layout.fillWidth: true }
                }

                // Search, centred like Windows 11 Photos.
                Rectangle {
                    anchors.centerIn: parent
                    width: Math.min(420, parent.width - 420)
                    height: 32
                    visible: !window.viewing && width > 160
                    radius: 4
                    color: Theme.field
                    border.width: 1
                    border.color: searchField.activeFocus ? Theme.accent : Theme.fieldBorder
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 8
                        TextInput {
                            id: searchField
                            // Like a Windows text box: in the Tab order, the text cursor over it and
                            // (in a layout) the full height of its box. A plain TextInput has neither.
                            activeFocusOnTab: true
                            HoverHandler { cursorShape: Qt.IBeamCursor }
                            Layout.fillHeight: true
                            verticalAlignment: TextInput.AlignVCenter
                            Layout.fillWidth: true
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            clip: true
                            selectByMouse: true
                            onTextChanged: searchDelay.restart()
                            Keys.onEscapePressed: text = ""
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                visible: searchField.text === ""
                                text: backend.texts.search
                                color: Theme.subtext
                                font.pixelSize: Theme.fontSize
                            }
                        }
                        Glyph { Layout.preferredWidth: 14; Layout.preferredHeight: 14; kind: "search"; color: Theme.subtext }
                    }
                    Timer {
                        id: searchDelay
                        interval: 250
                        onTriggered: backend.setQuery(searchField.text)
                    }
                }

                RowLayout {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 32
                    spacing: 0
                    component WindowButton: Rectangle {
                        id: wb
                        property string glyph
                        property string label
                        property bool danger: false
                        signal clicked()
                        Layout.preferredWidth: 46
                        Layout.fillHeight: true
                        color: wbHover.hovered ? (danger ? Theme.closeHover : Theme.hover) : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: label
                        Glyph {
                            anchors.centerIn: parent
                            width: 12
                            height: 12
                            lineWidth: 1
                            kind: wb.glyph
                            color: wbHover.hovered && wb.danger ? "#FFFFFF" : Theme.text
                        }
                        HoverHandler { id: wbHover }
                        TapHandler { onTapped: wb.clicked() }
                    }
                    WindowButton { glyph: "minimize"; label: backend.texts.minimize; onClicked: window.showMinimized() }
                    WindowButton {
                        glyph: window.maximized ? "restore" : "maximize"
                        label: window.maximized ? backend.texts.restore_down : backend.texts.maximize
                        onClicked: window.toggleMaximized()
                    }
                    WindowButton { glyph: "close"; label: backend.texts.close; danger: true; onClicked: window.close() }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                RowLayout {
                    anchors.fill: parent
                    spacing: 0
                    visible: !window.viewing

                    NavPane {
                        Layout.preferredWidth: 248
                        Layout.fillHeight: true
                        current: window.pane
                        onActivated: id => window.showPane(id)
                        onAddFolder: folderDialog.open()
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: Theme.content
                        radius: 8
                        Rectangle {           // square lower right corner
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            width: 8
                            height: 8
                            color: Theme.content
                        }
                        GalleryPage {
                            anchors.fill: parent
                            visible: window.pane !== "settings"
                            title: window.pane === "favorites" ? backend.texts.favorites
                                   : window.pane.indexOf("folder:") === 0 ? backend.folderName(window.pane.slice(7))
                                   : backend.texts.gallery
                            onOpen: item => {
                                if (item.kind === "video")
                                    backend.playVideo(item.path);
                                else
                                    backend.openInViewer(item.path);
                            }
                            onContextMenu: (item, target, x, y) => tileMenu.openFor(item, target, x, y)
                            onSlideshow: {
                                const first = backend.galleryRows.rowCount() > 0;
                                if (first) {
                                    window.slideshow = true;
                                    viewer.startSlideshow();
                                }
                            }
                        }
                        SettingsPage {
                            anchors.fill: parent
                            visible: window.pane === "settings"
                            onAddFolder: folderDialog.open()
                        }
                    }
                }

                Viewer {
                    id: viewer
                    anchors.fill: parent
                    visible: window.viewing
                    slideshow: window.slideshow
                    onDeleteRequested: path => window.confirmDelete(path)
                    onSlideshowEnded: {
                        window.slideshow = false;
                        if (window.visibility === Window.FullScreen)
                            window.showNormal();
                    }
                    onFullScreen: on => {
                        if (on)
                            window.showFullScreen();
                        else
                            window.showNormal();
                    }
                }
            }
        }
    }

    // --- Menus, dialogs, notices -------------------------------------------------------------

    WinMenu {
        id: tileMenu
        property var item: ({})
        function openFor(item, target, x, y) {
            tileMenu.item = item;
            const fav = backend.isFavorite(item.path);
            items = item.kind === "video"
                ? [{ text: backend.texts.play_video, action: "open" },
                   { text: fav ? backend.texts.unfavorite : backend.texts.favorite, action: "favorite" },
                   { separator: true },
                   { text: backend.texts.show_in_folder, action: "folder" },
                   { text: backend.texts.delete, action: "delete" }]
                : [{ text: backend.texts.edit, action: "open" },
                   { text: fav ? backend.texts.unfavorite : backend.texts.favorite, action: "favorite" },
                   { text: backend.texts.copy, action: "copy" },
                   { text: backend.texts.set_background, action: "background" },
                   { text: backend.texts.set_lock_screen, action: "lock" },
                   { separator: true },
                   { text: backend.texts.show_in_folder, action: "folder" },
                   { text: backend.texts.delete, action: "delete" }];
            openAt(target, x, y);
        }
        onTriggered: action => {
            const p = tileMenu.item.path;
            if (action === "open") {
                if (tileMenu.item.kind === "video")
                    backend.playVideo(p);
                else
                    backend.openInViewer(p);
            } else if (action === "favorite") backend.toggleFavorite(p);
            else if (action === "copy") backend.copyImage(p);
            else if (action === "background") backend.setBackground(p);
            else if (action === "lock") backend.setLockScreen(p);
            else if (action === "folder") backend.showInFolder(p);
            else if (action === "delete") window.confirmDelete(p);
        }
    }

    FolderDialog {
        id: folderDialog
        onAccepted: backend.addFolder(String(selectedFolder))
    }

    WinDialog {
        id: deleteQuestion
        property string path
        onChosen: action => { if (action === "delete") backend.deleteFile(path); }
    }
    WinDialog { id: messageBox }

    // A short notice at the bottom ("Copied", "Desktop background changed").
    Rectangle {
        id: toast
        function show(text) {
            toastText.text = text;
            opacity = 1;
            toastTimer.restart();
        }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: window.shadow + 40
        width: toastText.implicitWidth + 40
        height: 40
        radius: 8
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        opacity: 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 150 } }
        Text {
            id: toastText
            anchors.centerIn: parent
            color: Theme.text
            font.pixelSize: Theme.fontSize
        }
        Timer {
            id: toastTimer
            interval: 2500
            onTriggered: toast.opacity = 0
        }
    }

    Shortcut {
        sequence: "Escape"
        enabled: window.viewing && !window.slideshow
        onActivated: backend.closeViewer()
    }
    Shortcut {
        sequence: "Ctrl+F"
        enabled: !window.viewing
        onActivated: searchField.forceActiveFocus()
    }
}
