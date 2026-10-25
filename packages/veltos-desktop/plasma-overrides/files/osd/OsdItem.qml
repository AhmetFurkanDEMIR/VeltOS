/*
    The flyout of VeltOS' on-screen display (see Osd.qml): a rounded card
    at the bottom centre of the screen with the icon, a slider and the
    value, in the layout of Windows 11's volume flyout; it glides up a
    little and fades in. For an OSD without a value (a keyboard layout,
    a text) the card shows the icon and the text.
    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3

Item {
    id: root

    property int timeout: 1800
    property var osdValue
    property int osdMaxValue: 100
    property string osdAdditionalText: ""
    property string icon
    property bool showingProgress: false
    // Set by Osd.qml from the dialog's screen.
    property int windowScreenHeight: 0

    function formatPercent(number) {
        return i18ndc("plasma_shell_org.kde.plasma.desktop", "Percentage value", "%1%", number);
    }

    function enter() {
        entrance.restart();
    }

    // The flyout shows the icons of the taskbar's quick settings: plasmashell
    // asks for "video-display-brightness" (a monitor picture), quick
    // settings' brightness slider has the sun, "brightness-high-symbolic";
    // volume icons come in their symbolic (outline) form there too.
    function shownIcon(name) {
        if (name === "video-display-brightness") {
            return "brightness-high-symbolic";
        }
        if (name === "input-keyboard-brightness") {
            return "keyboard-brightness-high-symbolic";
        }
        if ((name.startsWith("audio-volume-") || name.startsWith("microphone-sensitivity-"))
                && !name.endsWith("-symbolic")) {
            return name + "-symbolic";
        }
        return name;
    }

    readonly property bool hasValue: showingProgress && osdValue !== undefined && osdValue !== null
    readonly property real fraction: hasValue && osdMaxValue > 0 ? Math.max(0, Math.min(1, osdValue / osdMaxValue)) : 0
    // KWin places an OSD window with its centre at two thirds of the
    // screen's height (Placement::placeOnScreenDisplay). The window is
    // therefore as tall as two thirds of the screen minus twice this band,
    // so that its bottom edge, where the card sits, ends about a band
    // above the taskbar, as Windows 11 shows its flyout.
    readonly property int bottomBand: 40
    readonly property int screenHeight: windowScreenHeight > 0 ? windowScreenHeight
                                        : (Screen.desktopAvailableHeight > 0 ? Screen.desktopAvailableHeight
                                           : (Qt.application.screens.length > 0
                                              ? Qt.application.screens[0].desktopAvailableHeight : 0))

    width: card.width
    height: Math.max(card.height, Math.round(screenHeight * 2 / 3) - bottomBand * 2)

    Rectangle {
        id: card
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.round(Kirigami.Units.gridUnit * 19)
        height: Math.round(Kirigami.Units.gridUnit * 3.1)
        radius: 8
        color: Kirigami.Theme.backgroundColor
        border.width: 1
        border.color: Qt.alpha(Kirigami.Theme.textColor, 0.12)
        opacity: 0
        transform: Translate { id: slide; y: 12 }

        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        Kirigami.Theme.inherit: false

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Kirigami.Units.largeSpacing * 2
            anchors.rightMargin: Kirigami.Units.largeSpacing * 2
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                Layout.alignment: Qt.AlignVCenter
                source: root.shownIcon(root.icon)
                color: Kirigami.Theme.textColor
                isMask: true
                visible: valid
            }

            // The slider: a thin track, the filled part in the accent colour
            // and a round knob, as Windows 11 draws its sliders.
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 20
                Layout.alignment: Qt.AlignVCenter
                visible: root.hasValue

                Rectangle {
                    id: track
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width
                    height: 4
                    radius: 2
                    color: Qt.alpha(Kirigami.Theme.textColor, 0.35)
                }
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: Math.round(track.width * root.fraction)
                    height: 4
                    radius: 2
                    color: Kirigami.Theme.highlightColor
                    Behavior on width { NumberAnimation { duration: Kirigami.Units.shortDuration } }
                }
                Rectangle {
                    id: knob
                    anchors.verticalCenter: parent.verticalCenter
                    x: Math.round((track.width - width) * root.fraction)
                    width: 18
                    height: 18
                    radius: 9
                    color: Kirigami.Theme.backgroundColor
                    border.width: 1
                    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.15)
                    Rectangle {
                        anchors.centerIn: parent
                        width: 10
                        height: 10
                        radius: 5
                        color: Kirigami.Theme.highlightColor
                    }
                    Behavior on x { NumberAnimation { duration: Kirigami.Units.shortDuration } }
                }
            }

            PC3.Label {
                Layout.alignment: Qt.AlignVCenter
                Layout.minimumWidth: root.hasValue ? Kirigami.Units.gridUnit * 2.6 : 0
                horizontalAlignment: root.hasValue ? Text.AlignRight : Text.AlignLeft
                Layout.fillWidth: !root.hasValue
                text: root.hasValue ? root.formatPercent(Math.round(root.osdValue))
                                    : (root.osdAdditionalText !== "" ? root.osdAdditionalText : (root.osdValue !== undefined ? root.osdValue : ""))
                elide: Text.ElideRight
                font.weight: Font.Medium
            }
        }

        ParallelAnimation {
            id: entrance
            NumberAnimation { target: card; property: "opacity"; from: 0; to: 1; duration: 180; easing.type: Easing.OutCubic }
            NumberAnimation { target: slide; property: "y"; from: 12; to: 0; duration: 220; easing.type: Easing.OutCubic }
        }
    }
}
