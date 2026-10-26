// This PC: drives with a capacity bar, as in Windows 11 File Explorer.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ScrollView {
    id: view

    signal driveMenu(var item, var drive, real x, real y)

    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    Component.onCompleted: backend.refreshDrives()

    ColumnLayout {
        width: view.availableWidth
        spacing: 4

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 18
            Layout.rightMargin: 12
            Layout.topMargin: 10
            spacing: 8
            Kirigami.Icon {
                Layout.preferredWidth: 10
                Layout.preferredHeight: 10
                source: "arrow-down"
                color: Theme.subtext
                isMask: true
            }
            Text {
                text: backend.text("devices_and_drives")
                color: Theme.text
                font.pixelSize: 14
                font.weight: Font.DemiBold
            }
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.separator
            }
        }

        Flow {
            Layout.fillWidth: true
            Layout.leftMargin: 34
            Layout.rightMargin: 12
            Layout.topMargin: 6
            spacing: 6

            Repeater {
                model: backend.drives
                delegate: Rectangle {
                    id: tile
                    required property var modelData
                    width: 270
                    height: 70
                    radius: 4
                    color: tileHover.hovered ? Theme.hover : "transparent"
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.title

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 10
                        spacing: 12
                        // 48 px as in Windows 11's tiles: the Windows logo on a
                        // Windows drive reads at this size.
                        Kirigami.Icon {
                            Layout.preferredWidth: 48
                            Layout.preferredHeight: 48
                            source: tile.modelData.icon || (tile.modelData.usb ? "drive-removable-media-usb"
                                    : tile.modelData.removable ? "drive-removable-media"
                                    : tile.modelData.windows ? "drive-harddisk-windows" : "drive-harddisk")
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                Layout.fillWidth: true
                                text: tile.modelData.title
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                                elide: Text.ElideRight
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                visible: tile.modelData.mount !== ""
                                height: 14
                                color: Theme.dark ? "#3A3D4E" : "#E6E6E6"
                                border.width: 1
                                border.color: Theme.dark ? "#4A4E62" : "#BCBCBC"
                                Rectangle {
                                    x: 1
                                    y: 1
                                    width: (parent.width - 2) * tile.modelData.fraction
                                    height: parent.height - 2
                                    color: tile.modelData.fraction > 0.9 ? "#DA2626" : "#26A0DA"
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: tile.modelData.freeText
                                color: Theme.subtext
                                font.pixelSize: Theme.smallFont
                                elide: Text.ElideRight
                            }
                        }
                    }
                    HoverHandler { id: tileHover }
                    TapHandler {
                        acceptedButtons: Qt.LeftButton
                        onDoubleTapped: backend.openDrive(tile.modelData.device !== "" ? tile.modelData.device
                                                                                         : tile.modelData.mount)
                    }
                    TapHandler {
                        acceptedButtons: Qt.RightButton
                        onTapped: point => view.driveMenu(tile, tile.modelData, point.position.x, point.position.y)
                    }
                }
            }
        }
    }
}
