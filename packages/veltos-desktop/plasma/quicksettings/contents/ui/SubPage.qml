/*
    A page of Quick Settings that slides in over the tiles, as Windows 11's
    Wi-Fi and Bluetooth lists do: a back button, the title and an on/off
    switch at the top, the page's list in the middle and a link to the
    matching Settings page at the bottom.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: page

    property string title
    property bool switchOn: false
    property bool switchEnabled: true
    property bool showSwitch: true
    property string footerText
    // A line in the middle of the page instead of the list (turned off,
    // nothing found).
    property string placeholder
    default property alias content: body.data
    signal back()
    signal switchToggled(bool on)
    signal footerClicked()

    spacing: 0

    RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing

        PlasmaComponents3.ToolButton {
            icon.name: "go-previous-symbolic"
            display: PlasmaComponents3.AbstractButton.IconOnly
            text: i18n("Back")
            onClicked: page.back()
            PlasmaComponents3.ToolTip.text: text
            PlasmaComponents3.ToolTip.visible: hovered
        }
        PlasmaComponents3.Label {
            Layout.fillWidth: true
            text: page.title
            font.weight: Font.DemiBold
            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.15
            elide: Text.ElideRight
        }
        PlasmaComponents3.Switch {
            id: onOff
            visible: page.showSwitch
            enabled: page.switchEnabled
            checked: page.switchOn
            Accessible.name: page.title
            onToggled: {
                page.switchToggled(checked);
                // Follow the real state again (the click broke the binding).
                checked = Qt.binding(() => page.switchOn);
            }
        }
    }

    Item {
        id: body
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true

        PlasmaComponents3.Label {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 2
            visible: page.placeholder !== ""
            text: page.placeholder
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            opacity: 0.7
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 2.4
        color: Qt.alpha(Kirigami.Theme.textColor, 0.04)
        radius: Kirigami.Units.cornerRadius

        PlasmaComponents3.Label {
            id: link
            anchors.left: parent.left
            anchors.leftMargin: Kirigami.Units.largeSpacing
            anchors.verticalCenter: parent.verticalCenter
            text: page.footerText
            color: Kirigami.Theme.linkColor
            font.underline: linkArea.containsMouse
            Accessible.role: Accessible.Link
            Accessible.name: text

            MouseArea {
                id: linkArea
                anchors.fill: parent
                anchors.margins: -Kirigami.Units.smallSpacing
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: page.footerClicked()
            }
        }
    }
}
