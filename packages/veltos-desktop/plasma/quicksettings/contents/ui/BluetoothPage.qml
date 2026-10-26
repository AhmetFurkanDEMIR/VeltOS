/*
    Quick Settings > Bluetooth, as in Windows 11: the paired devices with
    their state (connected, battery) and Connect / Disconnect, and the new
    devices found nearby with Pair while the page is open.

    Devices and calls come from BluezQt and Plasma's Bluetooth model (the
    ones KDE's Bluetooth applet uses); pairing codes are asked by Plasma's
    Bluetooth agent (bluedevil).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.bluezqt as BluezQt
import org.kde.plasma.private.bluetooth as PlasmaBt

SubPage {
    id: bluetooth

    property bool bluetoothOn: false
    property bool available: false
    signal toggleBluetooth(bool on)
    signal openSettings()

    // The device whose row is open (its D-Bus path), and the new devices
    // being paired or that could not be paired ("pairing", "failed"; kept
    // by main.qml, as pairing outlives the page: the flyout closes when the
    // code is confirmed in Plasma's notification).
    property string openUbi: ""
    property var pairing: ({})
    signal pairRequested(var device)

    title: i18n("Bluetooth")
    switchOn: bluetoothOn
    switchEnabled: available
    footerText: i18n("More Bluetooth settings")
    placeholder: !available ? i18n("No Bluetooth adapter found")
                 : !bluetoothOn ? i18n("Bluetooth is turned off") : ""
    onSwitchToggled: on => bluetooth.toggleBluetooth(on)
    onFooterClicked: bluetooth.openSettings()

    // Look for new devices while the page is open, as Windows does.
    property var searching: []
    function search(on) {
        const adapters = BluezQt.Manager.adapters;
        for (let i = 0; i < adapters.length; ++i) {
            const adapter = adapters[i];
            if (on && adapter.powered && !adapter.discovering) {
                adapter.startDiscovery();
                searching.push(adapter);
            }
        }
        if (!on) {
            searching.forEach(adapter => {
                if (adapter.discovering)
                    adapter.stopDiscovery();
            });
            searching = [];
        }
    }
    onBluetoothOnChanged: search(bluetoothOn)
    Component.onCompleted: {
        // Set once: a binding to the shared model looped ("Binding loop
        // detected for property sourceModel").
        pairedDevices.sourceModel = PlasmaBt.SharedDevicesStateProxyModel;
        if (bluetoothOn)
            search(true);
    }
    Component.onDestruction: search(false)

    PlasmaBt.DevicesProxyModel {
        id: pairedDevices
        hideBlockedDevices: true
    }

    Flickable {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.largeSpacing
        anchors.rightMargin: Kirigami.Units.largeSpacing
        visible: bluetooth.placeholder === ""
        contentHeight: list.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {}

        Column {
            id: list
            width: parent.width
            spacing: Kirigami.Units.smallSpacing / 2

            Repeater {
                model: bluetooth.placeholder === "" ? pairedDevices : null
                delegate: ListRow {
                    id: paired

                    required property var model
                    width: list.width
                    iconName: "bluetooth-symbolic"
                    monochromeIcon: true
                    title: model.DeviceFullName
                    busy: model.Connecting
                    expanded: bluetooth.openUbi === model.Ubi
                    status: {
                        if (model.Connecting)
                            return model.Connected ? i18n("Disconnecting…") : i18n("Connecting…");
                        if (model.Connected)
                            return model.Battery ? i18n("Connected · Battery %1%", model.Battery.percentage)
                                                 : i18n("Connected");
                        if (model.ConnectionFailed)
                            return i18n("Couldn't connect");
                        return i18n("Paired");
                    }
                    onClicked: bluetooth.openUbi = expanded ? "" : model.Ubi

                    function toggle() {
                        const device = model.Device;
                        const call = model.Connected ? device.disconnectFromDevice() : device.connectToDevice();
                        PlasmaBt.SharedDevicesStateProxyModel.registerPendingCallForDeviceUbi(call, model.Ubi);
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Item { Layout.fillWidth: true }
                        PlasmaComponents3.Button {
                            Layout.minimumWidth: Kirigami.Units.gridUnit * 6
                            visible: paired.model.Connected
                            enabled: !paired.model.Connecting
                            text: i18n("Disconnect")
                            onClicked: paired.toggle()
                        }
                        AccentButton {
                            Layout.minimumWidth: Kirigami.Units.gridUnit * 6
                            visible: !paired.model.Connected
                            enabled: !paired.model.Connecting
                            text: i18n("Connect")
                            onClicked: paired.toggle()
                        }
                    }
                }
            }

            // New devices nearby.
            PlasmaComponents3.Label {
                width: list.width
                visible: bluetooth.placeholder === ""
                topPadding: Kirigami.Units.largeSpacing
                bottomPadding: Kirigami.Units.smallSpacing
                leftPadding: Kirigami.Units.smallSpacing
                text: i18n("New devices")
                font.weight: Font.DemiBold
            }
            Repeater {
                model: bluetooth.placeholder === "" ? BluezQt.Manager.devices : []
                delegate: ListRow {
                    id: found

                    required property var modelData
                    readonly property string pairState: bluetooth.pairing[modelData.ubi] || ""
                    width: list.width
                    visible: !modelData.paired && !modelData.connected && !modelData.blocked && modelData.name !== ""
                    height: visible ? implicitHeight : 0
                    iconName: "bluetooth-symbolic"
                    monochromeIcon: true
                    title: modelData.name
                    busy: pairState === "pairing"
                    expanded: bluetooth.openUbi === modelData.ubi
                    status: pairState === "pairing" ? i18n("Pairing…")
                            : pairState === "failed" ? i18n("Couldn't pair") : i18n("Ready to pair")
                    onClicked: bluetooth.openUbi = expanded ? "" : modelData.ubi

                    RowLayout {
                        Layout.fillWidth: true
                        Item { Layout.fillWidth: true }
                        AccentButton {
                            Layout.minimumWidth: Kirigami.Units.gridUnit * 6
                            enabled: !found.busy
                            text: i18n("Pair")
                            onClicked: bluetooth.pairRequested(found.modelData)
                        }
                    }
                }
            }
            RowLayout {
                width: list.width
                visible: bluetooth.placeholder === "" && BluezQt.Manager.adapters.some(adapter => adapter.discovering)
                spacing: Kirigami.Units.largeSpacing
                PlasmaComponents3.BusyIndicator {
                    Layout.leftMargin: Kirigami.Units.smallSpacing
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                    running: visible
                }
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: i18n("Searching for devices…")
                    opacity: 0.7
                }
            }
        }
    }
}
