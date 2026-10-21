// Home, as in Windows 11 File Explorer: Quick access (pinned folders as
// tiles) and Recent files.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ScrollView {
    id: view

    property bool quickOpen: true
    property bool recentOpen: true
    signal folderMenu(var item, var entry, real x, real y)
    signal fileMenu(var item, var entry, real x, real y)

    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    Component.onCompleted: backend.refreshRecent()

    component SectionHeader: Rectangle {
        id: header
        property string text
        property bool open: true
        signal toggled()
        Layout.fillWidth: true
        Layout.leftMargin: 12
        Layout.rightMargin: 12
        implicitHeight: 30
        radius: 4
        color: headerHover.hovered ? Theme.hover : "transparent"
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 6
            spacing: 8
            Kirigami.Icon {
                Layout.preferredWidth: 10
                Layout.preferredHeight: 10
                source: header.open ? "arrow-down" : "arrow-right"
                color: Theme.subtext
                isMask: true
            }
            Text {
                text: header.text
                color: Theme.text
                font.pixelSize: 14
                font.weight: Font.DemiBold
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.rightMargin: 8
                height: 1
                color: Theme.separator
            }
        }
        HoverHandler { id: headerHover }
        TapHandler { onTapped: header.toggled() }
    }

    ColumnLayout {
        width: view.availableWidth
        spacing: 4

        Item { Layout.preferredHeight: 6 }

        SectionHeader {
            text: backend.text("quick_access")
            open: view.quickOpen
            onToggled: view.quickOpen = !view.quickOpen
        }

        Flow {
            Layout.fillWidth: true
            Layout.leftMargin: 34
            Layout.rightMargin: 12
            Layout.bottomMargin: 10
            visible: view.quickOpen
            spacing: 4

            Repeater {
                model: backend.pinned
                delegate: Rectangle {
                    id: tile
                    required property var modelData
                    width: Math.round(230 * Theme.textScale)
                    height: 64
                    radius: 4
                    color: tileHover.hovered ? Theme.hover : "transparent"
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.name

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        spacing: 12
                        Kirigami.Icon {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            source: tile.modelData.icon
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text {
                                Layout.fillWidth: true
                                text: tile.modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: backend.text("stored_locally")
                                color: Theme.subtext
                                font.pixelSize: Theme.smallFont
                                elide: Text.ElideRight
                            }
                            Item {
                                Layout.preferredWidth: 14
                                Layout.minimumWidth: 14
                                Layout.preferredHeight: 14
                                Kirigami.Icon {
                                    anchors.centerIn: parent
                                    width: 14
                                    height: 14
                                    source: Qt.resolvedUrl("pin.svg")
                                    isMask: true
                                    color: Theme.subtext
                                }
                            }
                        }
                    }
                    HoverHandler { id: tileHover }
                    TapHandler {
                        acceptedButtons: Qt.LeftButton
                        onDoubleTapped: backend.open(tile.modelData.path)
                    }
                    TapHandler {
                        acceptedButtons: Qt.MiddleButton
                        onTapped: backend.openInNewTab(tile.modelData.path)
                    }
                    TapHandler {
                        acceptedButtons: Qt.RightButton
                        onTapped: point => view.folderMenu(tile, tile.modelData, point.position.x, point.position.y)
                    }
                }
            }
        }

        SectionHeader {
            text: backend.text("recent")
            open: view.recentOpen
            onToggled: view.recentOpen = !view.recentOpen
        }

        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 40
            Layout.topMargin: 4
            visible: view.recentOpen && backend.recent.length === 0
            text: backend.text("no_recent")
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }

        Repeater {
            model: view.recentOpen ? backend.recent : []
            delegate: Rectangle {
                id: recentRow
                required property var modelData
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 12
                implicitHeight: Theme.rowHeight
                radius: 4
                color: recentHover.hovered ? Theme.hover : "transparent"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 10
                    Kirigami.Icon {
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        source: recentRow.modelData.icon
                    }
                    Text {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 4
                        text: recentRow.modelData.name
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                        elide: Text.ElideRight
                    }
                    Text {
                        Layout.preferredWidth: Math.round(160 * Theme.textScale)
                        text: recentRow.modelData.modifiedText
                        color: Theme.subtext
                        font.pixelSize: Theme.fontSize
                    }
                    Text {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 3
                        text: recentRow.modelData.folder
                        color: Theme.subtext
                        font.pixelSize: Theme.fontSize
                        elide: Text.ElideMiddle
                    }
                }
                HoverHandler { id: recentHover }
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onDoubleTapped: backend.open(recentRow.modelData.path)
                }
                TapHandler {
                    acceptedButtons: Qt.RightButton
                    onTapped: point => view.fileMenu(recentRow, recentRow.modelData, point.position.x, point.position.y)
                }
            }
        }
        Item { Layout.preferredHeight: 12 }
    }
}
