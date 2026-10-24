/*
    The filled accent button of Windows 11's flyouts (Connect, Next, Pair).

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
        color: button.down ? Qt.darker(Kirigami.Theme.highlightColor, 1.15)
               : button.hovered ? Qt.lighter(Kirigami.Theme.highlightColor, 1.08)
               : Kirigami.Theme.highlightColor
        opacity: button.enabled ? 1 : 0.45
    }
    contentItem: PlasmaComponents3.Label {
        text: button.text
        color: Kirigami.Theme.highlightedTextColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
