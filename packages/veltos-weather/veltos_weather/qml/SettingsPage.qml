// Settings of Windows 11 Weather: temperature unit, launch location, about.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: page
    contentWidth: width
    contentHeight: column.implicitHeight + 48
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}

    component Choice: Rectangle {
        id: choice
        property string text
        property bool chosen: false
        signal picked()
        Layout.fillWidth: true
        implicitHeight: 40
        radius: 5
        color: hover.hovered ? Theme.navHover : "transparent"
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            spacing: 12
            Rectangle {
                width: 20
                height: 20
                radius: 10
                color: choice.chosen ? Theme.accent : "transparent"
                border.width: choice.chosen ? 0 : 1.5
                border.color: Theme.faint
                Rectangle {
                    visible: choice.chosen
                    anchors.centerIn: parent
                    width: 8
                    height: 8
                    radius: 4
                    color: "#FFFFFF"
                }
            }
            Text { Layout.fillWidth: true; text: choice.text; color: Theme.text; font.pixelSize: Theme.bodySize }
        }
        HoverHandler { id: hover }
        TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: choice.picked() }
        Accessible.role: Accessible.RadioButton
        Accessible.name: text
        Accessible.checked: chosen
    }

    ColumnLayout {
        id: column
        x: 24
        y: 8
        width: Math.min(page.width - 48, 860)
        spacing: 12

        Text {
            text: backend.text("settings")
            color: Theme.text
            font.pixelSize: Theme.titleSize
            font.weight: Font.DemiBold
        }

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: unitColumn.implicitHeight + 32
            ColumnLayout {
                id: unitColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                spacing: 4
                Text { text: backend.text("temperature_unit"); color: Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold }
                Choice {
                    objectName: "fahrenheit"
                    text: backend.text("fahrenheit") + " (°F)"
                    chosen: backend.unitName === "F"
                    onPicked: backend.setUnit("F")
                }
                Choice {
                    objectName: "celsius"
                    text: backend.text("celsius") + " (°C)"
                    chosen: backend.unitName === "C"
                    onPicked: backend.setUnit("C")
                }
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: homeColumn.implicitHeight + 32
            ColumnLayout {
                id: homeColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                spacing: 8
                Text { text: backend.text("launch_location"); color: Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("launch_location_desc")
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    spacing: 12
                    Glyph { name: "home"; tint: Theme.subtext }
                    Text {
                        Layout.fillWidth: true
                        text: backend.homeName !== "" ? backend.homeName : "—"
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                    }
                    VButton {
                        visible: backend.hasPlace && !backend.isHome
                        text: backend.text("set_home") + ": " + backend.placeName
                        onClicked: backend.setHome()
                    }
                }
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: aboutColumn.implicitHeight + 32
            ColumnLayout {
                id: aboutColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                spacing: 8
                Text { text: backend.text("about"); color: Theme.text; font.pixelSize: Theme.subtitleSize; font.weight: Font.DemiBold }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("about_text")
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
