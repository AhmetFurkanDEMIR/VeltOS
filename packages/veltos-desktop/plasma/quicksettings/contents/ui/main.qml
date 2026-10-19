/*
    VeltOS Quick Settings: one taskbar button (network, sound and battery
    icons) that opens a Windows 11 style panel: toggle tiles (Wi-Fi,
    Bluetooth, airplane mode, night light), brightness and volume sliders,
    battery level and a Settings button.

    State and actions come from the same Plasma components KDE's own tray
    applets use (network, Bluetooth, volume, brightness, battery), so this
    applet only replaces their look.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.plasma.networkmanagement as PlasmaNM
import org.kde.plasma.private.volume
import org.kde.bluezqt as BluezQt
import org.kde.plasma.private.brightnesscontrolplugin
import org.kde.plasma.private.battery

PlasmoidItem {
    id: root

    PlasmaNM.EnabledConnections { id: enabledConnections }
    PlasmaNM.AvailableDevices { id: availableDevices }
    PlasmaNM.NetworkStatus { id: networkStatus }
    PlasmaNM.ConnectionIcon {
        id: connectionIcon
        connectivity: networkStatus.connectivity
    }
    PlasmaNM.Handler { id: handler }
    ScreenBrightnessControl {
        id: brightnessControl
        isSilent: root.expanded
    }
    NightLightControl { id: nightLight }
    BatteryControlModel { id: battery }
    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: source => disconnectSource(source)
    }

    readonly property var sink: PreferredDevice.sink
    readonly property int volumePercent: sink ? Math.round(sink.volume / PulseAudio.NormalVolume * 100) : 0
    readonly property bool muted: !sink || sink.muted
    readonly property bool wifiAvailable: availableDevices.wirelessDeviceAvailable
    readonly property bool wifiOn: enabledConnections.wirelessEnabled && !airplane
    readonly property bool bluetoothAvailable: BluezQt.Manager.adapters.length > 0
    readonly property bool bluetoothOn: BluezQt.Manager.bluetoothOperational
    readonly property bool airplane: PlasmaNM.Configuration.airplaneModeEnabled
    readonly property bool nightLightOn: nightLight.enabled && nightLight.running && !nightLight.inhibited
    readonly property string batteryIcon: {
        const level = Math.min(100, Math.round(battery.percent / 10) * 10);
        const name = "battery-" + String(level).padStart(3, "0");
        return battery.pluggedIn ? name + "-charging" : name;
    }

    function run(command) {
        launcher.connectSource(command);
        root.expanded = false;
    }
    function setVolume(percent) {
        if (!sink)
            return;
        sink.volume = Math.round(PulseAudio.NormalVolume * percent / 100);
        if (sink.muted && percent > 0)
            sink.muted = false;
    }
    function setBluetooth(enable) {
        BluezQt.Manager.bluetoothBlocked = !enable;
        BluezQt.Manager.adapters.forEach(adapter => {
            adapter.powered = enable;
        });
    }
    function setAirplane(enable) {
        handler.enableAirplaneMode(enable);
        PlasmaNM.Configuration.airplaneModeEnabled = enable;
    }

    preferredRepresentation: compactRepresentation
    toolTipMainText: i18n("Quick Settings")
    toolTipSubText: {
        const parts = [networkStatus.activeConnections || i18n("Not connected"),
                       muted ? i18n("Sound off") : i18n("Volume %1%", volumePercent)];
        if (battery.hasInternalBatteries)
            parts.push(i18n("Battery %1%", battery.percent));
        return parts.join("\n");
    }

    // --- Taskbar button: network, sound, battery in one hover area ----------
    compactRepresentation: MouseArea {
        id: button

        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

        Layout.minimumWidth: vertical ? -1 : icons.implicitWidth + Kirigami.Units.largeSpacing * 2
        Layout.minimumHeight: vertical ? icons.implicitHeight + Kirigami.Units.largeSpacing * 2 : -1
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded

        Rectangle {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            radius: Kirigami.Units.cornerRadius
            color: Kirigami.Theme.textColor
            opacity: root.expanded ? 0.12 : (button.containsMouse ? 0.07 : 0)
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }

        GridLayout {
            id: icons
            anchors.centerIn: parent
            flow: button.vertical ? GridLayout.TopToBottom : GridLayout.LeftToRight
            columnSpacing: Kirigami.Units.largeSpacing
            rowSpacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                source: root.airplane ? "network-flightmode-on" : connectionIcon.connectionIcon + "-symbolic"
                active: button.containsMouse
            }
            Kirigami.Icon {
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                source: AudioIcon.forVolume(root.volumePercent, root.muted, "") + "-symbolic"
                active: button.containsMouse
            }
            Kirigami.Icon {
                visible: battery.hasInternalBatteries
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                source: root.batteryIcon + "-symbolic"
                active: button.containsMouse
            }
        }
    }

    // --- Panel ------------------------------------------------------------------
    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 22
        Layout.minimumWidth: Kirigami.Units.gridUnit * 22
        spacing: Kirigami.Units.largeSpacing * 2

        component Tile: ColumnLayout {
            id: tile

            property string iconName
            property string label
            property bool active: false
            property bool available: true
            property bool hasMore: false
            signal toggled()
            signal more()

            Layout.fillWidth: true
            Layout.preferredWidth: 1
            spacing: Kirigami.Units.smallSpacing
            opacity: available ? 1 : 0.45

            Rectangle {
                id: face
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 2.6
                radius: Kirigami.Units.cornerRadius + 2
                color: tile.active ? Kirigami.Theme.highlightColor
                                   : Qt.alpha(Kirigami.Theme.textColor, mainArea.containsMouse ? 0.12 : 0.07)
                border.width: tile.active ? 0 : 1
                border.color: Qt.alpha(Kirigami.Theme.textColor, 0.12)
                Accessible.role: Accessible.CheckBox
                Accessible.name: tile.label
                Accessible.checked: tile.active

                MouseArea {
                    id: mainArea
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: tile.hasMore ? moreArea.left : parent.right
                    hoverEnabled: true
                    enabled: tile.available
                    onClicked: tile.toggled()

                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: Kirigami.Units.iconSizes.smallMedium
                        height: width
                        source: tile.iconName
                        color: tile.active ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                        isMask: true
                    }
                }
                Rectangle {
                    visible: tile.hasMore
                    anchors.right: moreArea.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 1
                    height: parent.height * 0.5
                    color: tile.active ? Qt.alpha(Kirigami.Theme.highlightedTextColor, 0.4)
                                       : Qt.alpha(Kirigami.Theme.textColor, 0.2)
                }
                MouseArea {
                    id: moreArea
                    visible: tile.hasMore
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: tile.hasMore ? parent.width * 0.3 : 0
                    hoverEnabled: true
                    onClicked: tile.more()

                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: Kirigami.Units.iconSizes.small
                        height: width
                        source: "go-next-symbolic"
                        color: tile.active ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                        isMask: true
                    }
                }
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: tile.label
                elide: Text.ElideRight
                font: Kirigami.Theme.smallFont
            }
        }

        component SliderRow: RowLayout {
            id: row

            property string iconName
            property string label
            property int value
            property bool available: true
            signal moved(int value)
            signal iconClicked()

            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
            visible: available

            PlasmaComponents3.ToolButton {
                icon.name: row.iconName
                display: PlasmaComponents3.AbstractButton.IconOnly
                text: row.label
                onClicked: row.iconClicked()
                PlasmaComponents3.ToolTip.text: row.label
                PlasmaComponents3.ToolTip.visible: hovered
            }
            PlasmaComponents3.Slider {
                id: slider
                Layout.fillWidth: true
                from: 0
                to: 100
                stepSize: 1
                value: row.value
                Accessible.name: row.label
                onMoved: row.moved(Math.round(value))
            }
            PlasmaComponents3.Label {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 2
                horizontalAlignment: Text.AlignRight
                text: i18n("%1%", Math.round(slider.value))
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            columns: 3
            columnSpacing: Kirigami.Units.largeSpacing
            rowSpacing: Kirigami.Units.largeSpacing

            Tile {
                iconName: root.wifiOn ? "network-wireless-symbolic" : "network-wireless-disconnected-symbolic"
                label: i18n("Wi-Fi")
                available: root.wifiAvailable && !root.airplane
                active: root.wifiOn && available
                hasMore: true
                onToggled: handler.enableWireless(!root.wifiOn)
                onMore: root.run("veltos-settings network")
            }
            Tile {
                iconName: "network-bluetooth-symbolic"
                label: i18n("Bluetooth")
                available: root.bluetoothAvailable && !root.airplane
                active: root.bluetoothOn && available
                hasMore: true
                onToggled: root.setBluetooth(!root.bluetoothOn)
                onMore: root.run("veltos-settings devices")
            }
            Tile {
                iconName: "network-flightmode-on-symbolic"
                label: i18n("Airplane mode")
                available: root.wifiAvailable || root.bluetoothAvailable
                active: root.airplane && available
                onToggled: root.setAirplane(!root.airplane)
            }
            Tile {
                iconName: "redshift-status-on-symbolic"
                label: i18n("Night light")
                available: nightLight.available
                active: root.nightLightOn && available
                hasMore: true
                onToggled: {
                    if (nightLight.enabled)
                        nightLight.toggleInhibition();
                    else
                        root.run("kcmshell6 kcm_nightlight");
                }
                onMore: root.run("kcmshell6 kcm_nightlight")
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.largeSpacing
            Layout.rightMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing

            Repeater {
                model: brightnessControl.isBrightnessAvailable ? brightnessControl.displays : []
                delegate: SliderRow {
                    required property string displayName
                    required property int brightness
                    required property int maxBrightness
                    iconName: "brightness-high-symbolic"
                    label: i18n("Brightness")
                    value: maxBrightness > 0 ? Math.round(100 * brightness / maxBrightness) : 0
                    onMoved: v => brightnessControl.setBrightness(displayName, Math.round(maxBrightness * v / 100))
                }
            }
            SliderRow {
                available: root.sink !== null
                iconName: AudioIcon.forVolume(root.volumePercent, root.muted, "") + "-symbolic"
                label: root.muted ? i18n("Unmute") : i18n("Mute")
                value: root.muted ? 0 : root.volumePercent
                onMoved: v => root.setVolume(v)
                onIconClicked: if (root.sink) root.sink.muted = !root.sink.muted
            }
        }

        // Footer: battery on the left, Settings on the right.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 2.4
            color: Qt.alpha(Kirigami.Theme.textColor, 0.04)
            radius: Kirigami.Units.cornerRadius

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.largeSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing

                Kirigami.Icon {
                    visible: battery.hasInternalBatteries
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                    source: root.batteryIcon
                }
                PlasmaComponents3.Label {
                    visible: battery.hasInternalBatteries
                    text: battery.pluggedIn ? i18n("%1% · Charging", battery.percent) : i18n("%1%", battery.percent)
                }
                Item { Layout.fillWidth: true }
                PlasmaComponents3.ToolButton {
                    icon.name: "configure-symbolic"
                    display: PlasmaComponents3.AbstractButton.IconOnly
                    text: i18n("Settings")
                    onClicked: root.run("veltos-settings")
                    PlasmaComponents3.ToolTip.text: text
                    PlasmaComponents3.ToolTip.visible: hovered
                }
            }
        }
    }
}
