// System > Storage: used and free space per drive.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)

    spacing: 6

    Repeater {
        model: backend.storage
        delegate: Card {
            required property var modelData
            Layout.fillWidth: true
            RowLayout {
                width: parent.width
                spacing: 16
                Kirigami.Icon {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    Layout.alignment: Qt.AlignTop
                    source: modelData.removable ? "drive-removable-media" : "drive-harddisk"
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Label {
                        Layout.fillWidth: true
                        text: modelData.live ? backend.text("live_drive")
                              : modelData.system ? backend.text("system_drive") + "  (/)"
                              : modelData.removable ? backend.text("removable") + "  (" + modelData.label + ")"
                              : modelData.mount
                        color: Theme.text
                        font.pixelSize: Theme.titleSize
                        wrapMode: Text.WordWrap
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        height: 8
                        radius: 4
                        color: Theme.track
                        Rectangle {
                            width: parent.width * modelData.fraction
                            height: parent.height
                            radius: 4
                            color: modelData.fraction > 0.9 ? "#D13438" : Theme.accent
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: backend.text("used_of").replace("{used}", modelData.used).replace("{total}", modelData.total)
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                        }
                        Label {
                            text: backend.format("free", modelData.free)
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                        }
                    }
                }
            }
        }
    }

    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 12
        icon: "drive-harddisk-symbolic"
        title: backend.text("disk_management")
        description: backend.text("disk_management_desc")
        external: true
        onActivated: page.itemActivated({ action: "disk-management", page: "" })
    }
}
