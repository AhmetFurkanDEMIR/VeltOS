// Bluetooth & devices > Bluetooth: turn Bluetooth on or off, add a device,
// connect and disconnect paired devices, and, as the Wi-Fi list shows
// networks, the devices nearby with Pair while the page is open (product
// owner, 2026-10-26).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var bt: backend.bluetooth
    // Found devices that are not among "Your devices" (a device just paired
    // leaves this list at once, before its pairing call has returned).
    readonly property var newDevices: (bt.found || []).filter(
        d => !(bt.devices || []).some(p => p.mac.toUpperCase() === d.mac.toUpperCase()))
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshBluetooth()

    Timer {
        interval: 10000
        repeat: true
        running: page.bt.powered
        onTriggered: backend.refreshBluetooth()
    }
    // New devices: a scan when the page opens and again every 15 seconds
    // (each scan takes about 8), not while a device is being paired.
    Timer {
        interval: 15000
        repeat: true
        triggeredOnStart: true
        running: page.bt.available && page.bt.powered
        onTriggered: if (!page.bt.pairing) backend.discoverBluetooth()
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
            objectName: "pairedDevice"
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

    SectionLabel {
        visible: page.bt.available && page.bt.powered
        text: backend.text("new_devices")
    }
    Repeater {
        model: page.bt.available && page.bt.powered ? page.newDevices : []
        delegate: SettingRow {
            id: newRow
            objectName: "newDevice"
            required property var modelData
            readonly property bool pairing: page.bt.pairing === modelData.mac
            Layout.fillWidth: true
            icon: modelData.icon + "-symbolic"
            title: modelData.name
            description: pairing ? backend.text("pairing")
                         : page.bt.pairFailed === modelData.mac ? backend.text("couldnt_pair")
                         : backend.text("ready_to_pair")
            BusyIndicator {
                visible: newRow.pairing
                running: visible
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
            }
            VButton {
                primary: true
                text: backend.text("pair")
                enabledState: !page.bt.pairing
                onClicked: backend.pairBluetooth(modelData.mac)
            }
        }
    }
    RowLayout {
        visible: page.bt.available && page.bt.powered && !!page.bt.scanning
        Layout.leftMargin: 4
        spacing: 10
        BusyIndicator {
            running: parent.visible
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        Label {
            text: backend.text("searching_devices")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
        }
    }
    Label {
        visible: page.bt.available && page.bt.powered && !page.bt.scanning && page.newDevices.length === 0
        Layout.leftMargin: 4
        text: backend.text("no_devices_found")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize + 1
    }
}
