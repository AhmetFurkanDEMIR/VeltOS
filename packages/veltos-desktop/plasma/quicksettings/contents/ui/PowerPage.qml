/*
    Quick Settings > Power mode: choose one of the profiles exposed by
    power-profiles-daemon; unsupported hardware profiles are not shown.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

SubPage {
    id: power

    property var profiles: []
    property string activeProfile: ""
    property string errorMessage: ""
    property bool busy: false
    signal profileSelected(string profile)
    signal openSettings()

    readonly property var names: ({
        "power-saver": i18n("Best power efficiency"),
        "balanced": i18n("Balanced"),
        "performance": i18n("Best performance")
    })

    title: i18n("Power mode")
    footerText: i18n("More power settings")
    placeholder: profiles.length === 0 ? i18n("Power modes aren't available") : ""
    showSwitch: false
    onFooterClicked: power.openSettings()

    Flickable {
        anchors.fill: parent
        anchors.leftMargin: Kirigami.Units.largeSpacing
        anchors.rightMargin: Kirigami.Units.largeSpacing
        visible: power.placeholder === ""
        contentHeight: list.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        PlasmaComponents3.ScrollBar.vertical: PlasmaComponents3.ScrollBar {}

        ColumnLayout {
            id: list
            width: parent.width
            spacing: Kirigami.Units.smallSpacing

            Repeater {
                model: power.profiles
                delegate: QQC2.RadioDelegate {
                    required property string modelData
                    Layout.fillWidth: true
                    text: power.names[modelData]
                    checked: modelData === power.activeProfile
                    enabled: !power.busy
                    onClicked: {
                        power.profileSelected(modelData);
                        checked = Qt.binding(() => modelData === power.activeProfile);
                    }
                }
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: power.profiles.indexOf("performance") < 0
                text: i18n("Best performance is not supported by this device; Balanced will be used on AC power.")
                wrapMode: Text.WordWrap
                opacity: 0.75
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                text: i18n("Automatically switches to best power efficiency on battery and best performance on AC power.")
                wrapMode: Text.WordWrap
                opacity: 0.75
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: power.errorMessage !== ""
                text: power.errorMessage
                wrapMode: Text.WordWrap
            }
            PlasmaComponents3.BusyIndicator {
                Layout.alignment: Qt.AlignHCenter
                visible: power.busy
                running: visible
            }
        }
    }
}
