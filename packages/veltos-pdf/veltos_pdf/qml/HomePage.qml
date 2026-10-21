// Home: a welcome with "Open file" and the recent files (name, folder,
// when opened, size), as in modern PDF readers.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: page

    signal openFile()
    signal openRecent(string path)

    color: Theme.content

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: Math.min(parent.width, 1100)
            x: Math.max(0, (parent.width - width) / 2)
            spacing: 14

            // Welcome card.
            Rectangle {
                Layout.fillWidth: true
                Layout.margins: 32
                Layout.bottomMargin: 8
                implicitHeight: 150
                radius: 10
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: Theme.dark ? "#3B1A1E" : "#FDECEA" }
                    GradientStop { position: 1; color: Theme.dark ? "#22232C" : "#F4F6FB" }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 28
                    spacing: 24
                    Image {
                        Layout.preferredWidth: 72
                        Layout.preferredHeight: 72
                        source: "image://icon/veltos-pdf"
                        sourceSize: Qt.size(144, 144)
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text { text: backend.texts.welcome; color: Theme.text; font.pixelSize: 24; font.weight: Font.DemiBold }
                        Text { Layout.fillWidth: true; text: backend.texts.welcome_text; color: Theme.subtext
                               font.pixelSize: Theme.fontSize; wrapMode: Text.WordWrap }
                    }
                    Rectangle {
                        implicitWidth: openLabel.implicitWidth + 40
                        implicitHeight: 36
                        radius: 18
                        color: openHover.hovered ? Qt.lighter("#D93A2B", 1.08) : "#D93A2B"
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.open_file
                        Text { id: openLabel; anchors.centerIn: parent; text: backend.texts.open_file; color: "#FFFFFF"
                               font.pixelSize: Theme.fontSize; font.weight: Font.DemiBold }
                        HoverHandler { id: openHover; cursorShape: Qt.PointingHandCursor }
                        TapHandler { onTapped: page.openFile() }
                    }
                }
            }

            Text {
                Layout.leftMargin: 32
                text: backend.texts.recent
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }

            // Table header.
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                visible: backend.recent.length > 0
                spacing: 12
                Item { Layout.preferredWidth: 28 }
                Text { Layout.fillWidth: true; Layout.preferredWidth: 3; text: backend.texts.name; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                Text { Layout.preferredWidth: 160; text: backend.texts.opened; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                Text { Layout.preferredWidth: 90; text: backend.texts.size; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                Item { Layout.preferredWidth: 28 }
            }
            Text {
                Layout.leftMargin: 32
                visible: backend.recent.length === 0
                text: backend.texts.no_recent
                color: Theme.subtext
                font.pixelSize: Theme.fontSize
            }
            Repeater {
                model: backend.recent
                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.leftMargin: 24
                    Layout.rightMargin: 24
                    implicitHeight: 52
                    radius: 6
                    color: rowHover.hovered ? Theme.hover : "transparent"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 12
                        Glyph { Layout.preferredWidth: 22; Layout.preferredHeight: 22; kind: "document"; color: "#D93A2B" }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.preferredWidth: 3
                            spacing: 0
                            Text { Layout.fillWidth: true; text: modelData.name; color: Theme.text; font.pixelSize: Theme.fontSize; elide: Text.ElideMiddle }
                            Text { Layout.fillWidth: true; text: modelData.folder; color: Theme.subtext; font.pixelSize: Theme.smallFont; elide: Text.ElideMiddle }
                        }
                        Text { Layout.preferredWidth: 160; text: modelData.opened; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                        Text { Layout.preferredWidth: 90; text: modelData.size; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                        Rectangle {
                            Layout.preferredWidth: 28; Layout.preferredHeight: 28; radius: 4
                            opacity: rowHover.hovered ? 1 : 0
                            color: forgetHover.hovered ? Theme.pressed : "transparent"
                            Accessible.role: Accessible.Button
                            Accessible.name: backend.texts.remove_from_recent
                            Glyph { anchors.centerIn: parent; width: 9; height: 9; kind: "close" }
                            ToolTip.visible: forgetHover.hovered
                            ToolTip.text: backend.texts.remove_from_recent
                            HoverHandler { id: forgetHover }
                            TapHandler { onTapped: backend.forget(modelData.path) }
                        }
                    }
                    HoverHandler { id: rowHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: page.openRecent(modelData.path) }
                }
            }
            Item { Layout.preferredHeight: 24 }
        }
    }
}
