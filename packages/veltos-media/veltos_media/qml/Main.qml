/*
    VeltOS Media Player: the layout of Windows 11 Media Player. Title bar,
    navigation pane (search, Home, Music library, Video library, Play
    queue, Playlists, Settings), the pages, the player bar at the bottom
    and the "now playing" view over the pages (the video, or the album
    picture of a song). Qt Multimedia (FFmpeg backend) plays.

    The window draws its own frame and shadow (frame.py keeps clicks on the
    shadow going to the windows behind).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import QtMultimedia
import "."

ApplicationWindow {
    id: window

    readonly property bool fullScreen: visibility === Window.FullScreen
    readonly property bool maximized: visibility === Window.Maximized || fullScreen
    readonly property int shadow: maximized ? 0 : 12
    readonly property var current: backend.current
    readonly property bool hasMedia: current.path !== undefined
    readonly property bool isVideo: current.kind === "video"
    property string page: "home"
    property bool nowPlaying: false
    property bool controlsShown: true      // full screen video: shown while the mouse moves

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }
    function toggleFullScreen() {
        if (fullScreen) {
            showNormal();
        } else {
            nowPlaying = true;
            showFullScreen();
        }
    }
    function showPage(id) {
        page = id;
        nowPlaying = false;
    }
    function togglePlay() {
        if (!hasMedia)
            return;
        if (player.playbackState === MediaPlayer.PlayingState)
            player.pause();
        else
            player.play();
    }
    function previous() {
        // Windows: back to the start first, the previous item within 3 s.
        if (player.position > 3000)
            player.position = 0;
        else
            backend.previous();
    }
    function tell(text) {
        toast.show(text);
    }

    width: 1180
    height: 760
    minimumWidth: 600
    minimumHeight: 420
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: hasMedia ? current.title + " - " + backend.texts.app_title : backend.texts.app_title

    // --- Playing ---------------------------------------------------------------------------
    MediaPlayer {
        id: player
        objectName: "player"            // found by the MPRIS service (mpris.py)
        // The state as a plain number for Python: PySide has no converter
        // for QMediaPlayer::PlaybackState read through property().
        readonly property int stateNumber: playbackState
        audioOutput: AudioOutput {
            // The slider is the loudness people hear (logarithmic), as in
            // Windows: Qt's QAudio::convertVolume(Logarithmic -> Linear),
            // written out because Qt 6.8 does not offer it to QML (the old
            // QtAudio.convertVolume call failed and the volume stayed at 100 %).
            volume: backend.volume >= 100 ? 1 : -Math.log(1 - backend.volume / 100) / Math.log(100)
            muted: backend.muted
        }
        videoOutput: nowPlayingView.videoOutput
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.EndOfMedia && !backend.ended())
                window.nowPlaying = window.nowPlaying && window.isVideo;
        }
        onErrorOccurred: (error, text) => window.tell(backend.texts.cant_play)
    }
    Connections {
        target: backend
        function onCurrentChanged() {
            const url = backend.current.path ? backend.fileUrl(backend.current.path) : "";
            if (String(player.source) === url) {
                player.position = 0;
            } else {
                player.stop();
                player.source = url;
            }
            if (url !== "") {
                player.play();
                if (backend.current.kind === "video")
                    window.nowPlaying = true;
            }
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
        color: window.fullScreen ? "#000000" : Theme.window
        border.width: window.maximized ? 0 : 1
        border.color: Theme.dark ? "#3A3C4A" : "#C9CDD8"
        clip: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: frame.border.width
            spacing: 0

            // --- Title bar -----------------------------------------------------------------
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                visible: !window.fullScreen
                DragHandler { target: null; onActiveChanged: if (active) window.startSystemMove() }
                TapHandler { onDoubleTapped: window.toggleMaximized() }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    spacing: 10
                    Rectangle {
                        visible: window.nowPlaying
                        implicitWidth: 36
                        implicitHeight: 30
                        radius: 4
                        color: backHover.hovered ? Theme.hover : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.back
                        Glyph { anchors.centerIn: parent; width: 14; height: 14; kind: "back" }
                        HoverHandler { id: backHover }
                        TapHandler { onTapped: window.nowPlaying = false }
                    }
                    Text { text: backend.texts.app_title; color: Theme.text; font.pixelSize: Theme.smallFont }
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

            // --- Navigation and pages ---------------------------------------------------------
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                RowLayout {
                    anchors.fill: parent
                    spacing: 0
                    visible: !window.nowPlaying

                    NavPane {
                        Layout.preferredWidth: 280
                        Layout.fillHeight: true
                        current: window.page
                        onActivated: id => window.showPage(id)
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: Theme.content
                        radius: 8
                        Rectangle { anchors.right: parent.right; anchors.bottom: parent.bottom; width: 8; height: 8; color: Theme.content }
                        Rectangle { anchors.left: parent.left; anchors.bottom: parent.bottom; width: 8; height: 8; color: Theme.content }
                        Loader {
                            anchors.fill: parent
                            sourceComponent: window.page === "music" ? musicPage
                                             : window.page === "videos" ? videoPage
                                             : window.page === "queue" ? queuePage
                                             : window.page.indexOf("playlist") === 0 ? playlistsPage
                                             : window.page === "settings" ? settingsPage
                                             : window.page.indexOf("search:") === 0 ? searchPage
                                             : homePage
                        }
                    }
                }

                NowPlaying {
                    id: nowPlayingView
                    anchors.fill: parent
                    visible: window.nowPlaying
                    item: window.current
                    playing: player.playbackState === MediaPlayer.PlayingState
                    onToggle: window.togglePlay()
                    onFullScreenToggled: window.toggleFullScreen()
                    onPointerMoved: {
                        window.controlsShown = true;
                        hideControls.restart();
                    }
                }
            }

            PlayerBar {
                Layout.fillWidth: true
                visible: !window.fullScreen || window.controlsShown
                player: player
                fullScreen: window.fullScreen
                onTogglePlay: window.togglePlay()
                onPrevious: window.previous()
                onOpenNowPlaying: window.nowPlaying = window.hasMedia && !window.nowPlaying
                onToggleFullScreen: window.toggleFullScreen()
            }
        }
    }

    Timer {
        id: hideControls
        interval: 2500
        onTriggered: if (window.fullScreen) window.controlsShown = false
    }

    Component { id: homePage; HomePage { onPlay: (paths, i) => backend.playPaths(paths, i); onOpenFiles: openDialog.open() } }
    Component { id: musicPage; MusicPage { onContextMenu: (paths, target, x, y) => itemMenu.openFor(paths, target, x, y) } }
    Component { id: videoPage; VideoPage { onContextMenu: (paths, target, x, y) => itemMenu.openFor(paths, target, x, y) } }
    Component { id: queuePage; QueuePage {} }
    Component { id: playlistsPage; PlaylistsPage { selected: window.page.indexOf("playlist:") === 0 ? window.page.slice(9) : ""
                                                   onOpenPlaylist: name => window.showPage("playlist:" + name) } }
    Component { id: settingsPage; SettingsPage { onAddFolder: kind => { folderDialog.kind = kind; folderDialog.open(); } } }
    Component { id: searchPage; SearchPage { query: window.page.slice(7)
                                             onContextMenu: (paths, target, x, y) => itemMenu.openFor(paths, target, x, y) } }

    // Song / video menu: Play, Play next, Add to play queue or a playlist, Show in folder.
    WinMenu {
        id: itemMenu
        property var paths: []
        function openFor(paths, target, x, y) {
            itemMenu.paths = paths;
            const lists = backend.playlists.map(p => ({ text: p.name, action: "list:" + p.name }));
            items = [
                { text: backend.texts.play, action: "play" },
                { text: backend.texts.play_next, action: "next" },
                { text: backend.texts.add_to, submenu: [{ text: backend.texts.play_queue, action: "queue" },
                                                        { separator: true },
                                                        { text: backend.texts.new_playlist, action: "new-list" }].concat(lists) },
                { separator: true },
                { text: backend.texts.show_in_folder, action: "folder" }
            ];
            openAt(target, x, y);
        }
        onTriggered: action => {
            if (action === "play") backend.playPaths(itemMenu.paths, 0);
            else if (action === "next") backend.playNext(itemMenu.paths);
            else if (action === "queue") backend.addToQueue(itemMenu.paths);
            else if (action === "folder") backend.showInFolder(itemMenu.paths[0]);
            else if (action === "new-list") backend.addToPlaylist(backend.createPlaylist(""), itemMenu.paths);
            else if (action.indexOf("list:") === 0) backend.addToPlaylist(action.slice(5), itemMenu.paths);
        }
    }

    FileDialog {
        id: openDialog
        fileMode: FileDialog.OpenFiles
        nameFilters: [backend.texts.media_files + " (*.mp3 *.flac *.ogg *.opus *.m4a *.aac *.wav *.wma *.mp4 *.m4v *.mkv *.webm *.avi *.mov *.wmv *.mpg *.mpeg)"]
        onAccepted: backend.playPaths(selectedFiles.map(String), 0)
    }
    FolderDialog {
        id: folderDialog
        property string kind: "music"
        onAccepted: backend.addFolder(kind, String(selectedFolder))
    }

    Rectangle {
        id: toast
        function show(text) {
            toastText.text = text;
            opacity = 1;
            toastTimer.restart();
        }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: window.shadow + 120
        width: toastText.implicitWidth + 40
        height: 40
        radius: 8
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        opacity: 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 150 } }
        Text { id: toastText; anchors.centerIn: parent; color: Theme.text; font.pixelSize: Theme.fontSize }
        Timer { id: toastTimer; interval: 2500; onTriggered: toast.opacity = 0 }
    }

    // Keyboard, as in Windows Media Player.
    Shortcut { sequence: "Space"; enabled: window.hasMedia; onActivated: window.togglePlay() }
    Shortcut { sequence: "Ctrl+P"; enabled: window.hasMedia; onActivated: window.togglePlay() }
    Shortcut { sequence: "Ctrl+F"; onActivated: backend.next() }
    Shortcut { sequence: "Ctrl+B"; onActivated: window.previous() }
    Shortcut { sequence: "Ctrl+H"; onActivated: backend.setShuffle(!backend.shuffle) }
    Shortcut { sequence: "Ctrl+T"; onActivated: backend.cycleRepeat() }
    Shortcut { sequence: "Ctrl+O"; onActivated: openDialog.open() }
    Shortcut { sequence: "F11"; onActivated: window.toggleFullScreen() }
    Shortcut { sequence: "Escape"; enabled: window.fullScreen; onActivated: window.showNormal() }
    Shortcut { sequence: "Right"; enabled: window.hasMedia && window.nowPlaying; onActivated: player.position = Math.min(player.duration, player.position + 10000) }
    Shortcut { sequence: "Left"; enabled: window.hasMedia && window.nowPlaying; onActivated: player.position = Math.max(0, player.position - 10000) }
    Shortcut { sequence: "F9"; onActivated: backend.setVolume(backend.volume - 5) }
    Shortcut { sequence: "F10"; onActivated: backend.setVolume(backend.volume + 5) }
    Shortcut { sequence: "F8"; onActivated: backend.setMuted(!backend.muted) }
}
