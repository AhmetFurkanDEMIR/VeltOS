/*
    Quick Settings > Mobile hotspot: the switch, the network's name and
    password to give to a phone, the band, how many devices are connected
    and a link to Settings' Mobile hotspot page (where the name, password,
    band and the shared connection are changed). The state comes from
    VeltOS Settings' helper (/usr/libexec/veltos/hotspot).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

SubPage {
    id: hotspot

    property var info: ({})
    property bool busy: false
    signal toggleHotspot(bool on)
    signal openSettings()

    readonly property bool active: info.active === true
    readonly property string problem: info.error ? info.error : (!active && info.reason ? info.reason : "")
    readonly property var reasons: ({
        "no-wifi": i18n("This PC has no Wi-Fi adapter."),
        "no-ap": i18n("This PC's Wi-Fi adapter can't host a mobile hotspot."),
        "same-adapter": i18n("This PC reaches the internet through its only Wi-Fi adapter, which can't connect and share at the same time."),
        "no-internet": i18n("Connect this PC to the internet first."),
        "start-failed": i18n("Mobile hotspot couldn't be turned on."),
        "save-failed": i18n("Mobile hotspot couldn't be turned on.")
    })
    function bandName(band) {
        return band === "bg" ? i18n("2.4 GHz") : band === "a" ? i18n("5 GHz") : i18n("Any available");
    }

    title: i18n("Mobile hotspot")
    switchOn: active
    switchEnabled: !busy && info.loaded === true && (active || info.reason === "")
    footerText: i18n("More hotspot settings")
    placeholder: info.loaded !== true ? i18n("Loading…") : ""
    onSwitchToggled: on => hotspot.toggleHotspot(on)
    onFooterClicked: hotspot.openSettings()

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.largeSpacing * 2
        anchors.rightMargin: Kirigami.Units.largeSpacing * 2
        visible: hotspot.placeholder === ""
        spacing: Kirigami.Units.largeSpacing

        PlasmaComponents3.Label {
            Layout.fillWidth: true
            visible: hotspot.problem !== ""
            text: hotspot.reasons[hotspot.problem] || ""
            wrapMode: Text.WordWrap
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: Kirigami.Units.largeSpacing * 2
            rowSpacing: Kirigami.Units.smallSpacing
            visible: hotspot.info.available === true

            PlasmaComponents3.Label { text: i18n("Network name"); opacity: 0.7 }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: hotspot.info.ssid || ""
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            PlasmaComponents3.Label { text: i18n("Password"); opacity: 0.7 }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: hotspot.info.password || ""
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            PlasmaComponents3.Label { text: i18n("Band"); opacity: 0.7 }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: hotspot.bandName(hotspot.info.band || "")
            }
            PlasmaComponents3.Label {
                visible: hotspot.active
                text: i18n("Devices")
                opacity: 0.7
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: hotspot.active
                text: i18n("%1 connected", (hotspot.info.clients || []).length)
            }
        }

        PlasmaComponents3.Label {
            Layout.fillWidth: true
            visible: !hotspot.active && (hotspot.info.disconnects || "") !== ""
            text: i18n("Turning on mobile hotspot disconnects this PC from %1.", hotspot.info.disconnects || "")
            wrapMode: Text.WordWrap
            opacity: 0.75
        }
        PlasmaComponents3.BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            visible: hotspot.busy
            running: visible
        }
        Item { Layout.fillHeight: true }
    }
}
