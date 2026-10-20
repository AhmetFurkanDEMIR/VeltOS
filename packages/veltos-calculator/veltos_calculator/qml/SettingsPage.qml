// Settings of Windows 11 Calculator: Appearance > App theme (Light, Dark,
// Use system setting) and About.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Flickable {
    id: page
    contentHeight: column.implicitHeight + 32
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    ColumnLayout {
        id: column
        x: 16
        y: 8
        width: page.width - 32
        spacing: 6

        Text {
            text: backend.texts.appearance
            color: Theme.text
            font.pixelSize: Theme.bodySize
            font.weight: Font.DemiBold
            Layout.topMargin: 8
            Layout.bottomMargin: 2
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: themeColumn.implicitHeight + 28
            radius: Theme.radius
            color: Theme.card
            border.color: Theme.cardBorder

            ColumnLayout {
                id: themeColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 14
                spacing: 2
                Text {
                    text: backend.texts.app_theme
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.texts.app_theme_hint
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                    wrapMode: Text.Wrap
                    Layout.bottomMargin: 8
                }
                Repeater {
                    model: [{ value: "light", label: backend.texts.theme_light },
                            { value: "dark", label: backend.texts.theme_dark },
                            { value: "system", label: backend.texts.theme_system }]
                    delegate: AbstractButton {
                        id: option
                        required property var modelData
                        readonly property bool selected: backend.theme === modelData.value
                        objectName: "theme_" + modelData.value
                        Layout.fillWidth: true
                        implicitHeight: 32
                        hoverEnabled: true
                        focusPolicy: Qt.NoFocus
                        Accessible.role: Accessible.RadioButton
                        Accessible.name: modelData.label
                        onClicked: backend.setTheme(modelData.value)
                        background: Item {}
                        contentItem: Row {
                            spacing: 10
                            // Windows 11 radio button
                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 20
                                height: 20
                                radius: 10
                                color: option.selected ? Theme.accent : Theme.card
                                border.width: option.selected ? 0 : 1
                                border.color: Theme.subtext
                                Rectangle {
                                    anchors.centerIn: parent
                                    visible: option.selected
                                    width: option.hovered ? 12 : 10
                                    height: width
                                    radius: width / 2
                                    color: Theme.accentText
                                    Behavior on width { NumberAnimation { duration: 83 } }
                                }
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: option.modelData.label
                                color: Theme.text
                                font.pixelSize: Theme.bodySize
                            }
                        }
                    }
                }
            }
        }

        Text {
            text: backend.texts.about
            color: Theme.text
            font.pixelSize: Theme.bodySize
            font.weight: Font.DemiBold
            Layout.topMargin: 18
            Layout.bottomMargin: 2
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: aboutColumn.implicitHeight + 28
            radius: Theme.radius
            color: Theme.card
            border.color: Theme.cardBorder

            ColumnLayout {
                id: aboutColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 14
                spacing: 4
                Text {
                    text: backend.texts.about_name
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    font.weight: Font.DemiBold
                }
                Text {
                    text: backend.texts.copyright
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                }
                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    text: backend.texts.about_text
                    color: Theme.text
                    font.pixelSize: Theme.captionSize
                    wrapMode: Text.Wrap
                }
            }
        }
    }
}
