// Network & internet > Mobile hotspot, in Windows 11's layout: the switch,
// which connection is shared and over what, the network's properties with
// Edit (name, password, band) and the devices that are connected.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var hs: backend.hotspot
    property bool editing: false
    signal itemActivated(var item)

    function bandLabel(band) {
        return backend.text(band === "bg" ? "band_24" : band === "a" ? "band_5" : "band_any");
    }
    readonly property var sourceOptions: (hs.sources || []).map(s => ({
        value: s.uuid, label: s.name + " (" + backend.text("source_" + s.kind) + ")"
    }))
    readonly property var bandOptions: (hs.bands || []).map(b => ({ value: b, label: page.bandLabel(b) }))
    readonly property string problem: hs.error ? hs.error : (!hs.active && hs.reason ? hs.reason : "")

    spacing: 4
    Component.onCompleted: backend.refreshHotspot()

    Timer {
        // The connected devices change while the page is open.
        interval: 5000
        repeat: true
        running: true
        onTriggered: backend.refreshHotspot()
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "network-wireless-hotspot-symbolic"
        title: backend.text("mobile_hotspot")
        description: page.hs.busy && page.hs.active ? backend.text("turning_on") : backend.text("hotspot_desc")
        ToggleSwitch {
            checked: page.hs.active === true
            enabledState: page.hs.loaded === true && page.hs.busy !== true
                          && (page.hs.active === true || page.hs.reason === "")
            accessibleName: backend.text("mobile_hotspot")
            onToggled: on => backend.setHotspot(on)
        }
    }

    Card {
        Layout.fillWidth: true
        visible: page.hs.loaded === true && page.problem !== ""
        Label {
            width: parent.width
            text: page.problem ? backend.text("hotspot_" + page.problem) : ""
            color: page.hs.error ? Theme.danger : Theme.text
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }
    }

    SettingRow {
        Layout.fillWidth: true
        visible: page.hs.available === true
        icon: "network-wired-symbolic"
        title: backend.text("share_from")
        description: page.sourceOptions.length > 1 ? backend.text("share_from_note") : ""
        VComboBox {
            Layout.preferredWidth: 260
            accessibleName: backend.text("share_from")
            enabledState: page.sourceOptions.length > 1 && page.hs.busy !== true
            options: page.sourceOptions
            currentValue: page.hs.source || ""
            onActivated: value => backend.setHotspotSource(value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        visible: page.hs.available === true
        icon: "network-wireless-symbolic"
        title: backend.text("share_over")
        VComboBox {
            Layout.preferredWidth: 260
            accessibleName: backend.text("share_over")
            enabledState: false
            options: [{ value: "wifi", label: "Wi-Fi" }]
            currentValue: "wifi"
        }
    }

    // Properties, as Windows lists them, with Edit.
    Rectangle {
        Layout.fillWidth: true
        Layout.topMargin: 14
        visible: page.hs.available === true
        implicitHeight: properties.implicitHeight + 32
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder

        ColumnLayout {
            id: properties
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 16
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: backend.text("hotspot_properties")
                    color: Theme.text
                    font.pixelSize: Theme.titleSize
                    font.weight: Font.DemiBold
                }
                VButton {
                    text: backend.text("edit")
                    enabledState: page.hs.busy !== true
                    onClicked: {
                        nameField.text = page.hs.ssid || "";
                        passwordField.text = page.hs.password || "";
                        bandBox.currentValue = page.hs.band || "";
                        page.editing = true;
                        nameField.focusInput();
                    }
                }
            }
            GridLayout {
                visible: !page.editing
                columns: 2
                columnSpacing: 32
                rowSpacing: 6
                Repeater {
                    model: [
                        ["network_name", page.hs.ssid || ""],
                        ["network_password", page.hs.password || ""],
                        ["network_band", page.bandLabel(page.hs.band || "")],
                        ["security_type", page.hs.security || ""]
                    ]
                    delegate: Label {
                        required property var modelData
                        required property int index
                        Layout.row: index
                        Layout.column: 0
                        text: backend.text(modelData[0]) + ":"
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize + 1
                    }
                }
                Repeater {
                    model: [page.hs.ssid || "", page.hs.password || "",
                            page.bandLabel(page.hs.band || ""), page.hs.security || ""]
                    delegate: Label {
                        required property var modelData
                        required property int index
                        Layout.row: index
                        Layout.column: 1
                        text: modelData
                        color: Theme.text
                        font.pixelSize: Theme.bodySize + 1
                    }
                }
            }

            // Edit network info.
            ColumnLayout {
                Layout.fillWidth: true
                visible: page.editing
                spacing: 6
                Label { text: backend.text("edit_network_info"); color: Theme.text; font.pixelSize: Theme.bodySize + 1; font.weight: Font.DemiBold }
                Label { Layout.topMargin: 4; text: backend.text("network_name"); color: Theme.text; font.pixelSize: Theme.bodySize }
                VTextField { id: nameField; Layout.preferredWidth: 320 }
                Label { text: backend.text("network_password"); color: Theme.text; font.pixelSize: Theme.bodySize }
                VTextField { id: passwordField; Layout.preferredWidth: 320; password: true }
                Label { text: backend.text("network_band"); color: Theme.text; font.pixelSize: Theme.bodySize }
                VComboBox {
                    id: bandBox
                    Layout.preferredWidth: 320
                    accessibleName: backend.text("network_band")
                    options: page.bandOptions
                    currentValue: ""
                    onActivated: value => currentValue = value
                }
                Label {
                    Layout.fillWidth: true
                    readonly property bool nameOk: nameField.text.length > 0 && nameField.text.trim() === nameField.text
                    readonly property bool passwordOk: /^[ -~]{8,63}$/.test(passwordField.text)
                    visible: page.editing && (!nameOk || !passwordOk)
                    text: !nameOk ? backend.text("hotspot_invalid-name") : backend.text("hotspot_invalid-password")
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.topMargin: 6
                    spacing: 8
                    VButton {
                        primary: true
                        text: backend.text("save")
                        enabledState: nameField.text.length > 0 && nameField.text.trim() === nameField.text
                                      && /^[ -~]{8,63}$/.test(passwordField.text)
                        onClicked: {
                            backend.configureHotspot(nameField.text, passwordField.text, bandBox.currentValue);
                            page.editing = false;
                        }
                    }
                    VButton {
                        text: backend.text("cancel")
                        onClicked: page.editing = false
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                visible: page.hs.disconnects !== undefined && page.hs.disconnects !== ""
                text: page.hs.disconnects ? backend.format("hotspot_disconnects", page.hs.disconnects) : ""
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                text: backend.text("hotspot_trust_note")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }
    }

    SectionLabel {
        visible: page.hs.active === true
        text: backend.format("devices_connected", String((page.hs.clients || []).length))
    }
    Label {
        visible: page.hs.active === true && (page.hs.clients || []).length === 0
        text: backend.text("no_hotspot_devices")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize + 1
    }
    Repeater {
        model: page.hs.active === true ? page.hs.clients || [] : []
        delegate: SettingRow {
            required property var modelData
            Layout.fillWidth: true
            icon: "phone-symbolic"
            title: modelData.name || backend.text("unknown_device")
            description: backend.text("ip_address") + ": " + (modelData.ip || "—") + "   "
                         + backend.text("physical_address") + ": " + modelData.mac
        }
    }
}
