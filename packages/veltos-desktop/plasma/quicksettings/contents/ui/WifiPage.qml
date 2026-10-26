/*
    Quick Settings > Wi-Fi, as in Windows 11: the networks in range with
    their signal and security, the connected one first with Properties and
    Disconnect; another network opens with "Connect automatically" and
    Connect, and secured networks ask for their key in place.

    The list and the actions are Plasma's network management (the same
    NetworkModel, AppletProxyModel and Handler calls KDE's network applet
    makes); networks of other kinds (wired, VPN) are left out.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.kitemmodels as KItemModels
import org.kde.plasma.networkmanagement as PlasmaNM

SubPage {
    id: wifi

    required property PlasmaNM.Handler nmHandler
    property bool wifiOn: false
    property bool airplane: false
    signal toggleWifi(bool on)
    signal openSettings()

    // The network whose row is open (its unique name), and the network
    // whose new profile must not connect by itself ("Connect automatically"
    // was cleared).
    property string openName: ""
    property string noAutoConnect: ""

    title: i18n("Wi-Fi")
    switchOn: wifiOn
    switchEnabled: !airplane
    footerText: i18n("More Wi-Fi settings")
    placeholder: airplane ? i18n("Airplane mode is on")
                 : !wifiOn ? i18n("Wi-Fi is turned off")
                 : networks.count === 0 ? i18n("No Wi-Fi networks found") : ""
    onSwitchToggled: on => wifi.toggleWifi(on)
    onFooterClicked: wifi.openSettings()

    PlasmaNM.NetworkModel { id: networkModel }
    PlasmaNM.AppletProxyModel {
        id: sorted
        sourceModel: networkModel
    }
    KItemModels.KSortFilterProxyModel {
        id: networks
        sourceModel: sorted
        filterRowCallback: (row, parent) => sorted.data(sorted.index(row, 0, parent), PlasmaNM.NetworkModel.TypeRole)
                                            === PlasmaNM.Enums.Wireless
    }
    P5Support.DataSource {
        id: shell
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    // Look for networks while the page is open, as Windows does.
    Timer {
        interval: 10000
        repeat: true
        triggeredOnStart: true
        running: wifi.wifiOn && !wifi.airplane
        onTriggered: wifi.nmHandler.requestScan()
    }

    Flickable {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.largeSpacing
        anchors.rightMargin: Kirigami.Units.largeSpacing
        visible: wifi.placeholder === ""
        contentHeight: list.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {}

        Column {
            id: list
            width: parent.width
            spacing: Kirigami.Units.smallSpacing / 2

            Repeater {
                model: networks
                delegate: ListRow {
                    id: network

                    required property var model
                    required property int index
                    readonly property int connectionState: model.ConnectionState
                    readonly property bool connected: connectionState === PlasmaNM.Enums.Activated
                    readonly property bool secured: model.SecurityType > PlasmaNM.Enums.NoneSecurity
                    readonly property bool asksKey: [PlasmaNM.Enums.StaticWep, PlasmaNM.Enums.WpaPsk,
                                                     PlasmaNM.Enums.Wpa2Psk, PlasmaNM.Enums.SAE]
                                                    .indexOf(model.SecurityType) !== -1
                    property bool askingKey: false

                    width: list.width
                    iconName: model.ConnectionIcon
                    title: model.ItemUniqueName
                    busy: connectionState === PlasmaNM.Enums.Activating || connectionState === PlasmaNM.Enums.Deactivating
                    expanded: wifi.openName === model.ItemUniqueName || (wifi.openName === "" && connected)
                    status: {
                        if (connectionState === PlasmaNM.Enums.Activating)
                            return i18n("Connecting…");
                        if (connectionState === PlasmaNM.Enums.Deactivating)
                            return i18n("Disconnecting…");
                        if (connected)
                            return secured ? i18n("Connected, secured") : i18n("Connected, open");
                        return secured ? i18n("Secured") : i18n("Open");
                    }
                    onClicked: {
                        wifi.openName = expanded ? "-" : model.ItemUniqueName;
                        askingKey = false;
                    }
                    // Keep the row as it is while its key is typed (the list
                    // is sorted by signal and would move under the pointer);
                    // a held row also stops showing its connection state, so
                    // only while typing, as KDE's applet does.
                    onAskingKeyChanged: networks.setData(networks.index(index, 0), askingKey,
                                                         PlasmaNM.NetworkModel.DelayModelUpdatesRole)
                    Component.onDestruction: if (askingKey)
                        networks.setData(networks.index(index, 0), false, PlasmaNM.NetworkModel.DelayModelUpdatesRole)
                    onConnectedChanged: {
                        if (connected && model.Ssid === wifi.noAutoConnect && /^[0-9a-fA-F-]{36}$/.test(model.Uuid)) {
                            shell.connectSource("nmcli connection modify uuid " + model.Uuid
                                                + " connection.autoconnect no");
                            wifi.noAutoConnect = "";
                        }
                    }

                    function join() {
                        if (model.Uuid !== "") {
                            // A saved network: its profile follows the box
                            // (changed only when it differs, so no password
                            // prompt for profiles the user may not change).
                            if (/^[0-9a-fA-F-]{36}$/.test(model.Uuid)) {
                                const want = autoConnect.checked ? "yes" : "no";
                                shell.connectSource("[ \"$(nmcli -g connection.autoconnect connection show uuid "
                                                    + model.Uuid + ")\" = " + want + " ] || nmcli connection modify uuid "
                                                    + model.Uuid + " connection.autoconnect " + want);
                            }
                            wifi.nmHandler.activateConnection(model.ConnectionPath, model.DevicePath, model.SpecificPath);
                            return;
                        }
                        if (!autoConnect.checked)
                            wifi.noAutoConnect = model.Ssid;
                        if (asksKey)
                            askingKey = true;
                        else
                            // Open networks; enterprise ones ask through
                            // Plasma's network password dialog.
                            wifi.nmHandler.addAndActivateConnection(model.DevicePath, model.SpecificPath);
                    }
                    function sendKey() {
                        if (!key.acceptableInput)
                            return;
                        wifi.nmHandler.addAndActivateConnection(model.DevicePath, model.SpecificPath, key.text);
                        askingKey = false;
                        key.text = "";
                    }

                    PlasmaComponents3.CheckBox {
                        id: autoConnect
                        visible: !network.connected && !network.askingKey
                        checked: true
                        text: i18n("Connect automatically")
                    }
                    PlasmaComponents3.Label {
                        visible: network.askingKey
                        Layout.fillWidth: true
                        text: i18n("Enter the network security key")
                        wrapMode: Text.WordWrap
                    }
                    PlasmaExtras.PasswordField {
                        id: key
                        visible: network.askingKey
                        Layout.fillWidth: true
                        validator: RegularExpressionValidator {
                            regularExpression: network.model.SecurityType === PlasmaNM.Enums.StaticWep
                                ? /^(?:.{5}|[0-9a-fA-F]{10}|.{13}|[0-9a-fA-F]{26})$/
                                : /^(?:.{8,64})$/
                        }
                        onVisibleChanged: if (visible) forceActiveFocus()
                        onAccepted: network.sendKey()
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: Kirigami.Units.smallSpacing
                        spacing: Kirigami.Units.smallSpacing

                        // Properties: a link in the accent colour, as in Windows 11.
                        PlasmaComponents3.Label {
                            visible: network.connected
                            text: i18n("Properties")
                            color: Kirigami.Theme.highlightColor
                            font.underline: propertiesArea.containsMouse
                            MouseArea {
                                id: propertiesArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: wifi.openSettings()
                            }
                        }
                        Item {
                            visible: !network.askingKey
                            Layout.fillWidth: true
                        }
                        // While the key is asked, Next and Cancel share the row
                        // equally, as in Windows 11.
                        OutlineButton {
                            visible: network.askingKey
                            Layout.fillWidth: true
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 6
                            text: i18n("Cancel")
                            onClicked: network.askingKey = false
                        }
                        OutlineButton {
                            Layout.minimumWidth: Kirigami.Units.gridUnit * 6
                            visible: network.connected && !network.busy
                            text: i18n("Disconnect")
                            onClicked: wifi.nmHandler.deactivateConnection(network.model.ConnectionPath,
                                                                           network.model.DevicePath)
                        }
                        AccentButton {
                            Layout.minimumWidth: Kirigami.Units.gridUnit * 6
                            Layout.fillWidth: network.askingKey
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 6
                            visible: network.askingKey || (!network.connected && !network.busy)
                            enabled: !network.askingKey || key.acceptableInput
                            text: network.askingKey ? i18n("Next") : i18n("Connect")
                            onClicked: network.askingKey ? network.sendKey() : network.join()
                        }
                    }
                }
            }
        }
    }
}
