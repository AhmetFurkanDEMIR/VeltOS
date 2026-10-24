// VeltOS controls style: the scroll bar of Windows 11 for VeltOS' apps.
// A thin rounded bar at the edge that widens (and gets a faint track)
// while the pointer is over it or it is dragged. KDE's Breeze style, which
// the apps get otherwise, draws a separator line beside the bar (the
// "extra line" next to scroll bars, product owner 2026-10-23). Every
// other control falls back to Breeze (qmldir).
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Templates as T
import org.kde.kirigami as Kirigami

T.ScrollBar {
    id: control

    readonly property bool wide: control.hovered || control.pressed
    readonly property int thickness: 12

    implicitWidth: vertical ? thickness : implicitContentWidth + leftPadding + rightPadding
    implicitHeight: horizontal ? thickness : implicitContentHeight + topPadding + bottomPadding

    hoverEnabled: true
    minimumSize: 0.08
    visible: control.size < 1 && control.policy !== T.ScrollBar.AlwaysOff

    // The bar runs along the outer edge: 2 px thin, 6 px while wide.
    topPadding: vertical ? 2 : (wide ? 4 : 8)
    bottomPadding: vertical ? 2 : 2
    leftPadding: horizontal ? 2 : (control.mirrored ? 2 : (wide ? 4 : 8))
    rightPadding: horizontal ? 2 : (control.mirrored ? (wide ? 4 : 8) : 2)
    Behavior on topPadding { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    Behavior on leftPadding { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    Behavior on rightPadding { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }

    contentItem: Rectangle {
        implicitWidth: 2
        implicitHeight: 2
        radius: Math.min(width, height) / 2
        color: Kirigami.Theme.textColor
        opacity: control.pressed ? 0.62 : control.wide ? 0.5 : 0.38
        Behavior on opacity { NumberAnimation { duration: 120 } }
    }

    background: Rectangle {
        radius: control.thickness / 2
        color: Kirigami.Theme.textColor
        opacity: control.wide ? 0.06 : 0
        Behavior on opacity { NumberAnimation { duration: 120 } }
    }
}
