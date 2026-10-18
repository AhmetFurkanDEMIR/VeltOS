/*
    One row in the All apps and search result lists: icon, name and,
    optionally, a description line.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami

MouseArea {
    id: row

    required property int index
    required property var model
    required property ListView view

    property bool showDescription: false
    property bool selected: view.activeFocus && view.currentIndex === index

    signal activated()
    signal contextMenuRequested()

    width: view.width
    height: Kirigami.Units.gridUnit * (showDescription && model.description ? 2.6 : 2.2)
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    Accessible.name: model.display
    Accessible.role: Accessible.Button

    onClicked: mouse => {
        if (mouse.button === Qt.RightButton) {
            contextMenuRequested();
        } else {
            activated();
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 1
        anchors.bottomMargin: 1
        radius: Kirigami.Units.cornerRadius !== undefined ? Kirigami.Units.cornerRadius : 6
        color: Kirigami.Theme.textColor
        opacity: row.pressed ? 0.14 : (row.selected ? 0.11 : (row.containsMouse ? 0.07 : 0))
        Behavior on opacity {
            NumberAnimation { duration: Kirigami.Units.shortDuration }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.largeSpacing
        anchors.rightMargin: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            implicitWidth: row.showDescription ? Kirigami.Units.iconSizes.medium : Kirigami.Units.iconSizes.smallMedium
            implicitHeight: implicitWidth
            source: row.model.decoration
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0

            PC3.Label {
                Layout.fillWidth: true
                text: row.model.display
                elide: Text.ElideRight
            }
            PC3.Label {
                Layout.fillWidth: true
                visible: row.showDescription && text.length > 0
                text: row.model.description || ""
                elide: Text.ElideRight
                font: Kirigami.Theme.smallFont
                opacity: 0.7
            }
        }
    }
}
