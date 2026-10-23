// The player bar of Windows 11 Media Player: the item's picture, title and
// artist on the left (opens "now playing"); shuffle, previous, play/pause,
// next and repeat with the seek bar and times in the middle; volume, full
// screen on the right.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import "."

Rectangle {
    id: bar

    property var player
    property bool fullScreen: false
    readonly property var current: backend.current
    readonly property bool hasMedia: current.path !== undefined
    readonly property bool playing: player && player.playbackState === MediaPlayer.PlayingState
    signal togglePlay()
    signal previous()
    signal openNowPlaying()
    signal toggleFullScreen()

    // The sides are equally wide, so the buttons and the seek bar sit in
    // the middle of the window at every size, also in full screen
    // (product owner, 2026-10-22: they stayed left of the middle there,
    // because the volume side grew as well).
    readonly property real sideWidth: Math.round(Math.min(320, bar.width * 0.26))

    implicitHeight: 96
    color: Theme.player
    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; height: 1; color: Theme.separator }

    function time(ms) {
        return backend.durationText(Math.floor((ms || 0) / 1000));
    }

    component IconButton: Rectangle {
        id: ib
        property string glyph
        property string label
        property bool active: false
        property bool enabledState: true
        property int size: 16
        signal clicked()
        implicitWidth: 40
        implicitHeight: 40
        radius: 4
        opacity: enabledState ? 1 : 0.35
        color: enabledState && ibTap.pressed ? Theme.pressed : (enabledState && ibHover.hovered ? Theme.hover : "transparent")
        Accessible.role: Accessible.Button
        Accessible.name: label
        Glyph { anchors.centerIn: parent; width: ib.size; height: ib.size; kind: ib.glyph
                color: ib.active ? Theme.accent : Theme.text }
        ToolTip.visible: ibHover.hovered
        ToolTip.delay: 600
        ToolTip.text: label
        HoverHandler { id: ibHover }
        TapHandler { id: ibTap; enabled: ib.enabledState; onTapped: ib.clicked() }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 16

        // Now playing.
        RowLayout {
            Layout.preferredWidth: bar.sideWidth
            Layout.minimumWidth: bar.sideWidth
            Layout.maximumWidth: bar.sideWidth
            spacing: 12
            Rectangle {
                implicitWidth: 56
                implicitHeight: 56
                radius: 4
                color: Theme.tile
                clip: true
                Image {
                    anchors.fill: parent
                    visible: status === Image.Ready
                    source: bar.current.cover ? backend.fileUrl(bar.current.cover)
                          : bar.current.kind === "video" ? backend.thumbUrl(bar.current.path, bar.current.mtime || 0) : ""
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    sourceSize: Qt.size(112, 112)
                }
                Glyph {
                    anchors.centerIn: parent
                    visible: !bar.current.cover && bar.current.kind !== "video"
                    width: 22; height: 22
                    kind: "music"
                    color: Theme.subtext
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: bar.hasMedia ? bar.current.title : backend.texts.nothing_playing
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    visible: text !== ""
                    text: bar.current.artist || ""
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    elide: Text.ElideRight
                }
            }
            HoverHandler { cursorShape: bar.hasMedia ? Qt.PointingHandCursor : Qt.ArrowCursor }
            TapHandler { onTapped: bar.openNowPlaying() }
        }

        // Transport and seek bar.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 6
                IconButton {
                    glyph: "shuffle"
                    active: backend.shuffle
                    label: backend.shuffle ? backend.texts.shuffle_on : backend.texts.shuffle_off
                    onClicked: backend.setShuffle(!backend.shuffle)
                }
                IconButton { glyph: "previous"; label: backend.texts.previous; size: 14; enabledState: bar.hasMedia
                             onClicked: bar.previous() }
                Rectangle {
                    implicitWidth: 44
                    implicitHeight: 44
                    radius: 22
                    color: playHover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent
                    opacity: bar.hasMedia ? 1 : 0.4
                    Accessible.role: Accessible.Button
                    Accessible.name: bar.playing ? backend.texts.pause : backend.texts.play
                    Glyph { anchors.centerIn: parent; anchors.horizontalCenterOffset: bar.playing ? 0 : 1
                            width: 16; height: 16; kind: bar.playing ? "pause" : "play"; color: Theme.accentText }
                    HoverHandler { id: playHover }
                    TapHandler { onTapped: bar.togglePlay() }
                }
                IconButton { glyph: "next"; label: backend.texts.next; size: 14; enabledState: bar.hasMedia
                             onClicked: backend.next() }
                IconButton {
                    glyph: backend.repeat === "one" ? "repeat-one" : "repeat"
                    active: backend.repeat !== "off"
                    label: backend.texts["repeat_" + backend.repeat]
                    onClicked: backend.cycleRepeat()
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Text {
                    text: bar.time(bar.player ? bar.player.position : 0)
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    font.features: ({ "tnum": 1 })
                }
                Slider {
                    id: seek
                    Layout.fillWidth: true
                    from: 0
                    to: Math.max(1, bar.player ? bar.player.duration : 1)
                    value: pressed ? value : (bar.player ? bar.player.position : 0)
                    enabled: bar.hasMedia && bar.player && bar.player.seekable
                    onMoved: bar.player.position = value
                    Accessible.name: backend.texts.now_playing
                }
                Text {
                    text: bar.time(bar.player ? bar.player.duration : 0)
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    font.features: ({ "tnum": 1 })
                }
            }
        }

        // Volume and full screen.
        RowLayout {
            Layout.preferredWidth: bar.sideWidth
            Layout.minimumWidth: bar.sideWidth
            Layout.maximumWidth: bar.sideWidth
            Layout.fillWidth: false
            spacing: 4
            Item { Layout.fillWidth: true }
            IconButton {
                glyph: backend.muted || backend.volume === 0 ? "mute" : "volume"
                label: backend.muted ? backend.texts.unmute : backend.texts.mute
                onClicked: backend.setMuted(!backend.muted)
            }
            Slider {
                Layout.preferredWidth: 110
                from: 0
                to: 100
                stepSize: 1
                value: backend.volume
                onMoved: {
                    backend.setVolume(Math.round(value));
                    if (backend.muted)
                        backend.setMuted(false);
                }
                Accessible.name: backend.texts.volume
            }
            IconButton {
                glyph: bar.fullScreen ? "exit-fullscreen" : "fullscreen"
                label: bar.fullScreen ? backend.texts.exit_full_screen : backend.texts.full_screen
                enabledState: bar.hasMedia
                onClicked: bar.toggleFullScreen()
            }
        }
    }
}
