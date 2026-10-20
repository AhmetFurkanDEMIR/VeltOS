// Store home: the featured banner (changes every few seconds, like the
// Microsoft Store's) and rows of apps.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: page
    signal opened(string appId)
    signal browse(string category)
    contentWidth: availableWidth
    clip: true

    readonly property var home: backend.home
    property int heroIndex: 0

    Timer {
        interval: 7000
        repeat: true
        running: page.visible && page.home.hero.length > 1 && !heroArea.containsMouse
        onTriggered: page.heroIndex = (page.heroIndex + 1) % page.home.hero.length
    }

    ColumnLayout {
        width: page.availableWidth
        spacing: 28

        // Featured banner.
        MouseArea {
            id: heroArea
            Layout.fillWidth: true
            Layout.topMargin: 24
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.preferredHeight: 300
            visible: page.home.hero.length > 0
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            readonly property var app: page.home.hero.length > 0 ? page.home.hero[page.heroIndex % page.home.hero.length] : null
            onClicked: if (app) page.opened(app.id)

            Rectangle {
                id: banner
                anchors.fill: parent
                radius: Theme.radius
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: heroArea.app ? heroArea.app.start : Theme.accent }
                    GradientStop { position: 1; color: heroArea.app ? heroArea.app.end : Theme.accent }
                }
                // Soft light circles, VeltOS style.
                Rectangle {
                    x: parent.width * 0.62
                    y: -parent.height * 0.3
                    width: parent.height * 1.2
                    height: width
                    radius: width / 2
                    color: "#FFFFFF"
                    opacity: 0.08
                }
                Rectangle {
                    x: parent.width * 0.48
                    y: parent.height * 0.45
                    width: parent.height * 0.9
                    height: width
                    radius: width / 2
                    color: "#FFFFFF"
                    opacity: 0.06
                }
            }
            Item {
                anchors.fill: parent
                clip: true
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.leftMargin: 40
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width * 0.5
                    spacing: 10
                    Text {
                        text: backend.texts.featured
                        color: "#FFFFFF"
                        opacity: 0.85
                        font.pixelSize: Theme.captionSize + 1
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: heroArea.app ? heroArea.app.name : ""
                        color: "#FFFFFF"
                        font.pixelSize: 34
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Text {
                        Layout.fillWidth: true
                        text: heroArea.app ? heroArea.app.summary : ""
                        color: "#FFFFFF"
                        opacity: 0.9
                        font.pixelSize: Theme.bodySize + 2
                        wrapMode: Text.Wrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        Layout.topMargin: 10
                        implicitWidth: detailsLabel.implicitWidth + 32
                        implicitHeight: 34
                        radius: Theme.smallRadius
                        color: "#FFFFFF"
                        opacity: heroArea.containsMouse ? 1 : 0.95
                        Text {
                            id: detailsLabel
                            anchors.centerIn: parent
                            text: backend.texts.see_details
                            color: "#1B1D24"
                            font.pixelSize: Theme.bodySize
                            font.weight: Font.DemiBold
                        }
                    }
                }
                AppIcon {
                    anchors.right: parent.right
                    anchors.rightMargin: parent.width * 0.12
                    anchors.verticalCenter: parent.verticalCenter
                    width: 168
                    height: 168
                    icon: heroArea.app ? heroArea.app.icon : ""
                }
                // Page dots.
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 40
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 20
                    spacing: 6
                    Repeater {
                        model: page.home.hero.length
                        Rectangle {
                            required property int index
                            width: index === page.heroIndex ? 18 : 6
                            height: 6
                            radius: 3
                            color: "#FFFFFF"
                            opacity: index === page.heroIndex ? 1 : 0.55
                            Behavior on width { NumberAnimation { duration: 200 } }
                            MouseArea {
                                anchors.fill: parent
                                anchors.margins: -4
                                onClicked: page.heroIndex = parent.index
                            }
                        }
                    }
                }
            }
        }

        Text {
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.fillWidth: true
            text: backend.texts.windows_apps_note
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
            wrapMode: Text.Wrap
        }

        // Rows of apps.
        Repeater {
            model: page.home.sections
            ColumnLayout {
                id: section
                required property var modelData
                Layout.fillWidth: true
                spacing: 12
                RowLayout {
                    Layout.leftMargin: 32
                    Layout.rightMargin: 32
                    Text {
                        Layout.fillWidth: true
                        text: section.modelData.title
                        color: Theme.text
                        font.pixelSize: Theme.sectionSize
                        font.weight: Font.DemiBold
                    }
                    Text {
                        visible: !!section.modelData.category
                        text: backend.texts.see_all + "  ›"
                        color: Theme.accent
                        font.pixelSize: Theme.bodySize
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: page.browse(section.modelData.category)
                        }
                    }
                }
                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 228
                    orientation: ListView.Horizontal
                    spacing: 12
                    leftMargin: 32
                    rightMargin: 32
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    model: section.modelData.items
                    delegate: AppCard {
                        required property var modelData
                        app: modelData
                        y: 4
                        onOpened: appId => page.opened(appId)
                    }
                }
            }
        }

        Item { Layout.preferredHeight: 16 }
    }
}
