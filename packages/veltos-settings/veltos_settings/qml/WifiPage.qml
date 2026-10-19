// Network & internet > Wi-Fi: turn Wi-Fi on or off, see the networks
// around, connect with the security key, disconnect, forget.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var net: backend.network
    property string expanded: ""
    signal itemActivated(var item)

    function signalIcon(strength) {
        const level = strength >= 80 ? "excellent" : strength >= 55 ? "good"
                      : strength >= 30 ? "ok" : strength >= 5 ? "weak" : "none";
        return "network-wireless-signal-" + level;
    }

    spacing: 4
    Component.onCompleted: backend.refreshNetwork(false)

    Timer {
        // Keep the list current while the page is open, like Windows.
        interval: 15000
        repeat: true
        running: page.net.enabled && page.net.connecting === ""
        onTriggered: backend.refreshNetwork(false)
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "network-wireless"
        title: "Wi-Fi"
        description: page.net.connection.type === "wifi"
                     ? backend.format("connected_to", page.net.connection.name)
                     : backend.text("wifi_desc")
        ToggleSwitch {
            checked: page.net.enabled
            enabledState: page.net.available
            accessibleName: "Wi-Fi"
            onToggled: on => backend.setWifi(on)
        }
    }

    Card {
        Layout.fillWidth: true
        visible: page.net.loaded && !page.net.available
        Label {
            width: parent.width
            text: backend.text("no_wifi")
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }
    }

    RowLayout {
        Layout.fillWidth: true
        visible: page.net.enabled
        SectionLabel {
            text: backend.text("available_networks")
        }
        Label {
            Layout.topMargin: 18
            visible: page.net.scanning
            text: backend.text("searching")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
        }
        VButton {
            Layout.topMargin: 14
            text: backend.text("refresh")
            enabledState: !page.net.scanning
            onClicked: backend.refreshNetwork(true)
        }
    }

    Label {
        visible: page.net.enabled && page.net.loaded && !page.net.scanning && page.net.networks.length === 0
        text: backend.text("no_networks")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize + 1
    }

    Repeater {
        model: page.net.enabled ? page.net.networks : []
        delegate: Rectangle {
            id: entry

            required property var modelData
            readonly property bool open: page.expanded === modelData.ssid
            readonly property bool busy: page.net.connecting === modelData.ssid
            readonly property bool failed: page.net.failed === modelData.ssid
            readonly property bool needsKey: modelData.secure && !modelData.saved && !modelData.enterprise

            Layout.fillWidth: true
            implicitHeight: column.implicitHeight + 24
            radius: Theme.radius
            color: entry.open ? Theme.card : (hover.hovered ? Theme.cardHover : Theme.card)
            border.width: 1
            border.color: Theme.cardBorder

            ColumnLayout {
                id: column
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 12
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Item {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        Kirigami.Icon {
                            anchors.fill: parent
                            source: page.signalIcon(entry.modelData.signal)
                            fallback: "network-wireless"
                        }
                        Kirigami.Icon {
                            visible: entry.modelData.secure
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.margins: -2
                            width: 12
                            height: 12
                            source: "object-locked"
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            Layout.fillWidth: true
                            text: entry.modelData.ssid
                            color: Theme.text
                            font.pixelSize: Theme.titleSize
                            font.weight: entry.modelData.active ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: entry.busy ? backend.text("connecting")
                                  : entry.modelData.active
                                    ? backend.text(entry.modelData.secure ? "connected_secured" : "connected_open")
                                    : backend.text(entry.modelData.secure ? "secured" : "open_network")
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                        }
                    }
                    Kirigami.Icon {
                        Layout.preferredWidth: 14
                        Layout.preferredHeight: 14
                        source: entry.open ? "arrow-up" : "arrow-down"
                        color: Theme.subtext
                        isMask: true
                    }
                }

                // Expanded: what can be done with this network.
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 40
                    visible: entry.open
                    spacing: 10

                    Label {
                        Layout.fillWidth: true
                        visible: entry.modelData.enterprise && !entry.modelData.active
                        text: backend.text("enterprise_hint")
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.WordWrap
                    }
                    VTextField {
                        id: key
                        Layout.preferredWidth: 320
                        visible: entry.needsKey && !entry.modelData.active
                        password: true
                        placeholder: backend.text("security_key")
                        onAccepted: if (text.length >= 8) backend.connectWifi(entry.modelData.ssid, text, entry.modelData.security)
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: entry.failed
                        text: backend.text("connect_failed")
                        color: Theme.danger
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        spacing: 8
                        VButton {
                            visible: !entry.modelData.active && !entry.modelData.enterprise
                            primary: true
                            text: entry.busy ? backend.text("connecting") : backend.text("connect")
                            enabledState: !entry.busy && (!entry.needsKey || key.text.length >= 8)
                            onClicked: backend.connectWifi(entry.modelData.ssid, key.text, entry.modelData.security)
                        }
                        VButton {
                            visible: entry.modelData.enterprise && !entry.modelData.active
                            primary: true
                            text: backend.text("advanced_network")
                            onClicked: backend.openModule("kcm_networkmanagement")
                        }
                        VButton {
                            visible: entry.modelData.active
                            text: backend.text("disconnect")
                            onClicked: backend.disconnectWifi()
                        }
                        VButton {
                            visible: entry.modelData.saved
                            text: backend.text("forget")
                            onClicked: {
                                page.expanded = "";
                                backend.forgetWifi(entry.modelData.ssid);
                            }
                        }
                    }
                }
            }

            HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
            TapHandler {
                // Only the header row toggles; the controls handle their own taps.
                onTapped: point => {
                    if (point.position.y < 64) {
                        page.expanded = entry.open ? "" : entry.modelData.ssid;
                        if (!entry.open)
                            return;
                        if (entry.needsKey)
                            key.focusInput();
                    }
                }
            }
        }
    }

    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 18
        icon: "network-wired"
        title: backend.text("advanced_network")
        description: backend.text("advanced_network_desc")
        external: true
        onActivated: page.itemActivated({ kcm: "kcm_networkmanagement", action: "", page: "" })
    }
}
