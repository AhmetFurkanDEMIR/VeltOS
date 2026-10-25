/*
    Windows 11's media card above Quick Settings: the app that plays (its
    icon and name), the title and artist with the cover on the right, and
    Previous / Play-Pause / Next under them. With several players two
    arrows at the top right go from one to the next, as Windows switches
    between media sessions. A new title and cover fade in.

    `model` is Plasma's Mpris2Model (org.kde.plasma.private.mpris, the
    model of KDE's own media controller); its first row is the
    "multiplexer", which follows whichever player is active.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.mpris as Mpris

ColumnLayout {
    id: card

    required property var model
    readonly property var player: model.currentPlayer
    readonly property string track: player?.track ?? ""
    readonly property string artist: player?.artist ?? ""
    readonly property string art: player?.artUrl ?? ""
    readonly property string app: player?.identity ?? ""
    readonly property string appIcon: player?.iconName ?? ""
    readonly property int status: player?.playbackStatus ?? 0
    readonly property bool playing: status === Mpris.PlaybackStatus.Playing
    // Something to show: a player with a title, or one that plays or waits.
    readonly property bool hasMedia: !!player && (track !== "" || status > Mpris.PlaybackStatus.Stopped)

    // The real players (not the multiplexer row), by row.
    property var players: []
    function updatePlayers() {
        const rows = [];
        for (let i = 0; i < rows_.count; ++i) {
            const item = rows_.itemAt(i);
            if (item && !item.multiplexer)
                rows.push(i);
        }
        players = rows;
    }
    function step(delta) {
        if (players.length < 2)
            return;
        let at = players.indexOf(model.currentIndex);
        if (at < 0) {
            // The multiplexer shows one of them: start from that one.
            at = Math.max(0, players.findIndex(row => rows_.itemAt(row).identity === card.app));
        }
        model.currentIndex = players[(at + delta + players.length) % players.length];
    }

    // Reads the model's rows (identity, multiplexer) for the arrows; an
    // invisible item takes no room in the layout.
    Item {
        visible: false
        Repeater {
            id: rows_
            model: card.model
            delegate: Item {
                required property bool isMultiplexer
                required property string identity
                readonly property bool multiplexer: isMultiplexer
            }
            onCountChanged: Qt.callLater(card.updatePlayers)
            onItemAdded: Qt.callLater(card.updatePlayers)
            onItemRemoved: Qt.callLater(card.updatePlayers)
        }
    }

    spacing: Kirigami.Units.largeSpacing

    component RoundButton: PlasmaComponents3.ToolButton {
        id: control
        property string iconName
        property bool large: false
        implicitWidth: large ? Kirigami.Units.gridUnit * 2.4 : Kirigami.Units.gridUnit * 2
        implicitHeight: implicitWidth
        icon.name: iconName
        readonly property int glyph: large ? Kirigami.Units.iconSizes.smallMedium : Kirigami.Units.iconSizes.small
        icon.width: glyph
        icon.height: glyph
        display: PlasmaComponents3.AbstractButton.IconOnly
        PlasmaComponents3.ToolTip.text: text
        PlasmaComponents3.ToolTip.visible: hovered && text !== ""
        PlasmaComponents3.ToolTip.delay: Kirigami.Units.toolTipDelay
    }

    // App icon and name; the session arrows at the right.
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing * 2
        Kirigami.Icon {
            Layout.preferredWidth: Kirigami.Units.iconSizes.small
            Layout.preferredHeight: Kirigami.Units.iconSizes.small
            source: card.appIcon !== "" ? card.appIcon : "media-playback-start-symbolic"
        }
        PlasmaComponents3.Label {
            Layout.fillWidth: true
            text: card.app
            elide: Text.ElideRight
            font.pointSize: Kirigami.Theme.smallFont.pointSize
            opacity: 0.8
        }
        RoundButton {
            visible: card.players.length > 1
            iconName: "go-previous-symbolic"
            text: i18n("Previous media session")
            onClicked: card.step(-1)
        }
        RoundButton {
            visible: card.players.length > 1
            iconName: "go-next-symbolic"
            text: i18n("Next media session")
            onClicked: card.step(1)
        }
    }

    // Title and artist; the cover on the right.
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.largeSpacing * 2

        ColumnLayout {
            id: texts
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: Kirigami.Units.smallSpacing
            transform: Translate { id: textShift }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: card.track !== "" ? card.track : card.app
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.Wrap
                font.weight: Font.DemiBold
                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.15
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: card.artist !== ""
                text: card.artist
                elide: Text.ElideRight
                opacity: 0.75
            }
        }

        Rectangle {
            id: cover
            Layout.preferredWidth: Kirigami.Units.gridUnit * 4
            Layout.preferredHeight: Layout.preferredWidth
            Layout.alignment: Qt.AlignVCenter
            radius: Kirigami.Units.cornerRadius
            color: Qt.alpha(Kirigami.Theme.textColor, 0.08)
            clip: true
            Kirigami.Icon {
                anchors.centerIn: parent
                width: parent.width * 0.45
                height: width
                visible: picture.status !== Image.Ready
                source: card.appIcon !== "" ? card.appIcon : "media-album-cover"
                opacity: 0.6
            }
            Image {
                id: picture
                anchors.fill: parent
                source: card.art
                asynchronous: true
                fillMode: Image.PreserveAspectCrop
                sourceSize.width: width * 2
                sourceSize.height: height * 2
                visible: status === Image.Ready
            }
        }
    }

    // Previous, Play/Pause, Next in the middle.
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: Kirigami.Units.largeSpacing
        RoundButton {
            iconName: "media-skip-backward-symbolic"
            text: i18n("Previous track")
            enabled: !!card.player && card.player.canGoPrevious
            onClicked: card.player.Previous()
        }
        RoundButton {
            large: true
            iconName: card.playing ? "media-playback-pause-symbolic" : "media-playback-start-symbolic"
            text: card.playing ? i18n("Pause") : i18n("Play")
            enabled: !!card.player && (card.playing ? card.player.canPause : card.player.canPlay)
            onClicked: card.playing ? card.player.Pause() : card.player.Play()
        }
        RoundButton {
            iconName: "media-skip-forward-symbolic"
            text: i18n("Next track")
            enabled: !!card.player && card.player.canGoNext
            onClicked: card.player.Next()
        }
    }

    // A new title (or another player) fades in, as Windows' card does.
    onTrackChanged: changed.restart()
    onAppChanged: changed.restart()
    ParallelAnimation {
        id: changed
        NumberAnimation { target: texts; property: "opacity"; from: 0; to: 1; duration: Kirigami.Units.longDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: cover; property: "opacity"; from: 0; to: 1; duration: Kirigami.Units.longDuration; easing.type: Easing.OutCubic }
        NumberAnimation { target: textShift; property: "x"; from: Kirigami.Units.largeSpacing * 2; to: 0; duration: Kirigami.Units.longDuration; easing.type: Easing.OutCubic }
    }
}
