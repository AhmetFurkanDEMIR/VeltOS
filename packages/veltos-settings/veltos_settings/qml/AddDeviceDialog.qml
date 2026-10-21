// "Add a device" (Windows 11): searches for Bluetooth devices in range and
// connects the one you click. Replaces KDE's Bluetooth wizard.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Popup {
    id: dialog

    readonly property var bt: backend.bluetooth
    readonly property string failedName: {
        for (const d of bt.found || []) {
            if (d.mac === bt.pairFailed)
                return d.name;
        }
        return bt.pairFailed;
    }

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 480
    modal: true
    focus: true
    padding: 24
    onOpened: backend.discoverBluetooth()

    background: Rectangle {
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
    }

    contentItem: ColumnLayout {
        spacing: 12

        Label {
            text: backend.text("add_a_device")
            color: Theme.text
            font.pixelSize: 20
            font.weight: Font.DemiBold
        }
        Label {
            Layout.fillWidth: true
            text: backend.text("add_device_hint")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }

        // Found devices.
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumHeight: 160
            spacing: 4

            Repeater {
                model: dialog.bt.found || []
                delegate: Rectangle {
                    id: row
                    required property var modelData
                    readonly property bool pairing: dialog.bt.pairing === modelData.mac
                    Layout.fillWidth: true
                    implicitHeight: 52
                    radius: 5
                    color: tap.pressed ? Theme.cardPressed : (hover.hovered ? Theme.navHover : "transparent")
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.name
                    Keys.onReturnPressed: backend.pairBluetooth(modelData.mac)

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 14
                        Kirigami.Icon {
                            Layout.preferredWidth: 24
                            Layout.preferredHeight: 24
                            source: row.modelData.icon + "-symbolic"
                            fallback: "bluetooth-symbolic"
                            isMask: true
                            color: Theme.text
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Label {
                                Layout.fillWidth: true
                                text: row.modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.titleSize
                                elide: Text.ElideRight
                            }
                            Label {
                                visible: row.pairing
                                text: backend.text("pairing")
                                color: Theme.subtext
                                font.pixelSize: Theme.bodySize
                            }
                        }
                        BusyIndicator {
                            visible: row.pairing
                            running: visible
                            Layout.preferredWidth: 24
                            Layout.preferredHeight: 24
                        }
                    }
                    HoverHandler { id: hover; enabled: dialog.bt.pairing === ""; cursorShape: Qt.PointingHandCursor }
                    TapHandler { id: tap; enabled: dialog.bt.pairing === ""; onTapped: backend.pairBluetooth(row.modelData.mac) }
                }
            }

            RowLayout {
                visible: dialog.bt.scanning
                spacing: 10
                BusyIndicator {
                    running: dialog.bt.scanning
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                }
                Label {
                    text: backend.text("searching_devices")
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize + 1
                }
            }
            Label {
                Layout.fillWidth: true
                visible: !dialog.bt.scanning && (dialog.bt.found || []).length === 0
                text: backend.text("no_devices_found")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize + 1
                wrapMode: Text.WordWrap
            }
            Item { Layout.fillHeight: true }
        }

        Label {
            Layout.fillWidth: true
            visible: dialog.bt.pairFailed !== ""
            text: backend.text("pair_failed").replace("{name}", dialog.failedName)
            color: Theme.danger
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8
            VButton {
                text: backend.text("search_again")
                enabledState: !dialog.bt.scanning && dialog.bt.pairing === ""
                onClicked: backend.discoverBluetooth()
            }
            VButton {
                primary: true
                text: backend.text("done")
                onClicked: dialog.close()
            }
        }
    }
}
