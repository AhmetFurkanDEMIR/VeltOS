/*
    The second button of a flyout row (Disconnect, Cancel, Remove device):
    the accent colour as outline and text, filled lightly while pointed at,
    next to AccentButton's filled one. Plasma's grey button looked unrelated
    to the row and to the accent colour (product owner, 2026-10-26).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

PlasmaComponents3.Button {
    id: button

    background: Rectangle {
        implicitWidth: Kirigami.Units.gridUnit * 6
        implicitHeight: Kirigami.Units.gridUnit * 1.8
        radius: Kirigami.Units.cornerRadius
        color: button.down ? Qt.alpha(Kirigami.Theme.highlightColor, 0.22)
               : button.hovered ? Qt.alpha(Kirigami.Theme.highlightColor, 0.12)
               : Qt.alpha(Kirigami.Theme.backgroundColor, 0.6)
        border.width: 1
        border.color: Kirigami.Theme.highlightColor
        opacity: button.enabled ? 1 : 0.45
    }
    contentItem: PlasmaComponents3.Label {
        text: button.text
        color: Kirigami.Theme.highlightColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
