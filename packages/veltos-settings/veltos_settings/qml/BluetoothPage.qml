// Bluetooth & devices > Bluetooth: turn Bluetooth on or off, add a device,
// connect and disconnect paired devices.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var bt: backend.bluetooth
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshBluetooth()

    Timer {
        interval: 10000
        repeat: true
        running: page.bt.powered
        onTriggered: backend.refreshBluetooth()
    }

    Card {
        Layout.fillWidth: true
        visible: page.bt.loaded && !page.bt.available
        Label {
            width: parent.width
            text: backend.text("no_bluetooth")
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }
    }

    SettingRow {
        Layout.fillWidth: true
        visible: page.bt.available
        icon: "bluetooth-symbolic"
        title: "Bluetooth"
        description: backend.text("bluetooth_desc")
        ToggleSwitch {
            checked: page.bt.powered
            accessibleName: "Bluetooth"
            onToggled: on => backend.setBluetooth(on)
        }
    }

    SettingRow {
        Layout.fillWidth: true
        visible: page.bt.available
        icon: "list-add-symbolic"
        title: backend.text("add_device")
        description: backend.text("add_device_desc")
        VButton {
            text: backend.text("add_device")
            enabledState: page.bt.powered
            onClicked: addDialog.open()
        }
    }

    SectionLabel {
        visible: page.bt.available
        text: backend.text("your_devices")
    }

    Label {
        visible: page.bt.available && page.bt.loaded && page.bt.devices.length === 0
        text: backend.text("no_devices")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize + 1
    }

    AddDeviceDialog {
        id: addDialog
    }

    Repeater {
        model: page.bt.available ? page.bt.devices : []
        delegate: SettingRow {
            required property var modelData
            readonly property bool busy: page.bt.busy === modelData.mac
            Layout.fillWidth: true
            icon: modelData.icon
            title: modelData.name
            description: [modelData.connected ? backend.text("connected") : backend.text("paired"),
                          modelData.battery >= 0 ? backend.format("battery_percent", String(modelData.battery)) : ""]
                         .filter(part => part.length > 0).join("  ·  ")
            VButton {
                text: modelData.connected ? backend.text("disconnect") : backend.text("connect")
                enabledState: page.bt.powered && !busy
                onClicked: backend.connectBluetooth(modelData.mac, !modelData.connected)
            }
            VButton {
                text: backend.text("remove_device")
                enabledState: !busy
                onClicked: backend.removeBluetooth(modelData.mac)
            }
        }
    }

}
