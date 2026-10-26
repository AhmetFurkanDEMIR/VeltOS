/*
    A row of the Wi-Fi or Bluetooth page: icon, name and state; clicking it
    opens the row with its buttons underneath, as in Windows 11.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

Rectangle {
    id: row

    property string iconName
    property bool monochromeIcon: false
    property string title
    property string status
    property bool busy: false
    property bool expanded: false
    default property alias details: detailsColumn.data
    signal clicked()

    implicitHeight: layout.implicitHeight + Kirigami.Units.smallSpacing * 2
    radius: Kirigami.Units.cornerRadius
    // The open row in a light tint of the accent colour with an accent
    // edge, so it goes with the accent buttons in it (product owner,
    // 2026-10-26: grey row, white buttons, unrelated colours).
    color: row.expanded ? Qt.alpha(Kirigami.Theme.highlightColor, 0.10)
                        : headerArea.containsMouse ? Qt.alpha(Kirigami.Theme.textColor, 0.05) : "transparent"
    border.width: row.expanded ? 1 : 0
    border.color: Qt.alpha(Kirigami.Theme.highlightColor, 0.35)
    Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
    Accessible.role: Accessible.ListItem
    Accessible.name: row.title
    Accessible.description: row.status

    ColumnLayout {
        id: layout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        Item {
            Layout.fillWidth: true
            implicitHeight: header.implicitHeight + Kirigami.Units.smallSpacing * 2

            RowLayout {
                id: header
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.smallSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing
                spacing: Kirigami.Units.largeSpacing

                Kirigami.Icon {
                    id: icon
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                    source: row.iconName
                    color: row.monochromeIcon ? Kirigami.Theme.textColor : "transparent"
                    isMask: row.monochromeIcon
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    PlasmaComponents3.Label {
                        Layout.fillWidth: true
                        text: row.title
                        elide: Text.ElideRight
                    }
                    PlasmaComponents3.Label {
                        Layout.fillWidth: true
                        visible: text !== ""
                        text: row.status
                        elide: Text.ElideRight
                        font: Kirigami.Theme.smallFont
                        opacity: 0.7
                    }
                }
                PlasmaComponents3.BusyIndicator {
                    visible: row.busy
                    running: visible
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                }
            }
            MouseArea {
                id: headerArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: row.clicked()
            }
        }

        ColumnLayout {
            id: detailsColumn
            visible: row.expanded
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing
                               + Kirigami.Units.smallSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing
            Layout.bottomMargin: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing
        }
    }
}
