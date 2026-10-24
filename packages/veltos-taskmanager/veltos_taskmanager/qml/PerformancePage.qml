// Performance: like Windows 11 - a list of devices with small graphs on
// the left, the selected one's large 60-second graph and figures on the right.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: page
    spacing: 0

    property string current: "cpu"
    // CPU, memory, disk, network and every GPU ("GPU 0" ...), from the backend.
    readonly property var devices: backend.devices
    readonly property var info: backend.performance[current] || backend.performance["cpu"]

    Label {
        Layout.margins: 16
        text: backend.texts.performance
        font.pixelSize: Theme.pageTitleSize
        font.weight: Font.DemiBold
        color: Theme.text
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.leftMargin: 8
        Layout.rightMargin: 16
        Layout.bottomMargin: 16
        spacing: 16

        // Devices
        ColumnLayout {
            Layout.preferredWidth: 240
            Layout.maximumWidth: 240
            Layout.fillWidth: false
            Layout.fillHeight: true
            spacing: 4
            Repeater {
                model: page.devices
                MouseArea {
                    id: device
                    required property string modelData
                    readonly property var deviceInfo: backend.performance[modelData]
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    hoverEnabled: true
                    onClicked: page.current = modelData

                    Rectangle {
                        anchors.fill: parent
                        radius: 6
                        color: page.current === device.modelData ? Theme.navSelected
                             : (device.containsMouse ? Theme.navHover : "transparent")
                    }
                    Rectangle {
                        visible: page.current === device.modelData
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: 3
                        height: parent.height * 0.4
                        radius: 1.5
                        color: Theme.accent
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        anchors.leftMargin: 12
                        spacing: 10
                        Graph {
                            Layout.preferredWidth: 70
                            Layout.fillHeight: true
                            values: device.deviceInfo.history
                            colour: Theme.accent
                            grid: false
                            Rectangle {
                                anchors.fill: parent
                                color: "transparent"
                                border.width: 1
                                border.color: Theme.accent
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                text: device.deviceInfo.title
                                font.weight: Font.DemiBold
                                color: Theme.text
                            }
                            Label {
                                Layout.fillWidth: true
                                text: device.deviceInfo.value
                                elide: Text.ElideRight
                                color: Theme.subtext
                            }
                        }
                    }
                }
            }
            Item {
                Layout.fillHeight: true
            }
        }

        // Selected device
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.radius
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: page.info.title
                        font.pixelSize: 24
                        font.weight: Font.DemiBold
                        color: Theme.text
                    }
                    Label {
                        text: page.info.subtitle
                        elide: Text.ElideRight
                        color: Theme.text
                    }
                }
                Label {
                    visible: page.current === "cpu" || page.current.startsWith("gpu")
                    text: backend.texts.over_60
                    color: Theme.subtext
                }
                // A GPU whose driver reports no usage (nouveau, virtual machines).
                Label {
                    Layout.fillWidth: true
                    visible: !!page.info.note
                    text: page.info.note || ""
                    wrapMode: Text.Wrap
                    color: Theme.subtext
                }
                Graph {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 160
                    values: page.info.history
                    colour: Theme.accent
                }
                GridLayout {
                    Layout.topMargin: 8
                    columns: 3
                    columnSpacing: 32
                    rowSpacing: 8
                    Repeater {
                        model: page.info.stats
                        ColumnLayout {
                            required property var modelData
                            spacing: 0
                            Label {
                                text: modelData[0]
                                color: Theme.subtext
                            }
                            Label {
                                text: modelData[1]
                                font.pixelSize: 18
                                color: Theme.text
                            }
                        }
                    }
                }
            }
        }
    }
}
