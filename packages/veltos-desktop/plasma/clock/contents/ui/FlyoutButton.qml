/*
    A Windows 11 standard button as the calendar and notification flyouts
    show it: a light fill with a hairline border and 4 px corners, an
    optional glyph left of the text; "flat" buttons only get a fill under
    the pointer. "accent" fills it with the accent colour (an active
    do-not-disturb, for example).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

MouseArea {
    id: button

    property string text
    property string glyph
    property string toolTip
    property bool flat: false
    property bool accent: false
    property int glyphSize: 12

    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor)
                                 === Kirigami.ColorUtils.Dark
    readonly property color foreground: accent ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor

    implicitHeight: 28
    opacity: enabled ? 1 : 0.4
    implicitWidth: text.length > 0 ? row.implicitWidth + 22 : implicitHeight
    hoverEnabled: true
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: text.length > 0 ? text : toolTip
    Keys.onSpacePressed: clicked(null)
    Keys.onReturnPressed: clicked(null)

    Rectangle {
        anchors.fill: parent
        radius: 4
        color: {
            if (button.accent) {
                return button.pressed ? Qt.darker(Kirigami.Theme.highlightColor, 1.15)
                     : button.containsMouse ? Qt.lighter(Kirigami.Theme.highlightColor, 1.08)
                     : Kirigami.Theme.highlightColor;
            }
            if (button.flat) {
                return Qt.alpha(Kirigami.Theme.textColor, button.pressed ? 0.05 : (button.containsMouse ? 0.08 : 0));
            }
            if (button.dark) {
                return Qt.alpha("white", button.pressed ? 0.03 : (button.containsMouse ? 0.08 : 0.06));
            }
            return Qt.alpha("white", button.pressed ? 0.5 : (button.containsMouse ? 0.85 : 0.7));
        }
        border.width: button.flat || button.accent ? 0 : 1
        border.color: button.dark ? Qt.alpha("white", 0.08) : Qt.alpha("black", 0.09)
    }
    Rectangle {
        visible: button.activeFocus
        anchors.fill: parent
        anchors.margins: -2
        radius: 6
        color: "transparent"
        border.width: 2
        border.color: Kirigami.Theme.textColor
    }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        opacity: button.pressed && !button.accent ? 0.75 : 1

        Glyph {
            visible: button.glyph.length > 0
            Layout.preferredWidth: button.glyphSize
            Layout.preferredHeight: button.glyphSize
            kind: button.glyph
            color: button.foreground
        }
        PlasmaComponents3.Label {
            visible: button.text.length > 0
            text: button.text
            color: button.foreground
        }
    }

    PlasmaComponents3.ToolTip.text: toolTip
    PlasmaComponents3.ToolTip.visible: toolTip.length > 0 && containsMouse
    PlasmaComponents3.ToolTip.delay: Kirigami.Units.toolTipDelay
}
