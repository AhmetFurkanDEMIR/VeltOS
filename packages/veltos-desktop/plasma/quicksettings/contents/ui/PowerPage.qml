/*
    Quick Settings > Power mode, in the spirit of Windows 11: three modes as
    cards (Best power efficiency, Balanced, Best performance), one chosen
    for "Plugged in" and one for "On battery" (the tabs, on PCs with a
    battery), switched with the power source by veltos-desktop's power-mode
    helper. A mode the PC does not offer is shown, greyed.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

SubPage {
    id: power

    property var profiles: []           // offered by this PC
    property string activeProfile: ""
    property string source: "ac"        // the current power source
    property bool hasBattery: false
    property var modes: ({})            // {"ac": profile, "battery": profile}
    property string errorMessage: ""
    property bool busy: false
    // The source whose mode the cards show; the current one at first.
    property string editing: source
    signal profileSelected(string source, string profile)
    signal openSettings()

    readonly property var choices: [
        { profile: "power-saver", icon: "power-profile-power-saver-symbolic",
          name: i18n("Best power efficiency"), text: i18n("Saves energy; apps may run a little slower") },
        { profile: "balanced", icon: "power-profile-balanced-symbolic",
          name: i18n("Balanced"), text: i18n("Speed when you need it, energy saved when you don't") },
        { profile: "performance", icon: "power-profile-performance-symbolic",
          name: i18n("Best performance"), text: i18n("As fast as this PC can go; uses more power") }
    ]
    // The chosen mode, or what the PC uses instead when it lacks it.
    readonly property string chosen: {
        const mode = modes[editing] || "";
        if (profiles.indexOf(mode) >= 0)
            return mode;
        return profiles.indexOf("balanced") >= 0 ? "balanced" : (profiles[0] || "");
    }

    title: i18n("Power mode")
    footerText: i18n("More power settings")
    placeholder: profiles.length === 0 ? i18n("Power modes aren't available") : ""
    showSwitch: false
    onFooterClicked: power.openSettings()
    onSourceChanged: editing = source

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
            spacing: Kirigami.Units.smallSpacing * 1.5

            // Plugged in | On battery, a segmented control.
            Rectangle {
                visible: power.hasBattery
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 1.9
                radius: height / 2
                color: Qt.alpha(Kirigami.Theme.textColor, 0.06)

                Rectangle {
                    // The sliding highlight under the chosen tab.
                    width: parent.width / 2 - 4
                    height: parent.height - 4
                    y: 2
                    x: power.editing === "ac" ? 2 : parent.width / 2 + 2
                    radius: height / 2
                    color: Kirigami.Theme.backgroundColor
                    border.width: 1
                    border.color: Qt.alpha(Kirigami.Theme.textColor, 0.12)
                    Behavior on x { NumberAnimation { duration: Kirigami.Units.shortDuration; easing.type: Easing.OutCubic } }
                }
                Row {
                    anchors.fill: parent
                    Repeater {
                        model: [["ac", i18n("Plugged in"), "ac-adapter-symbolic"],
                                ["battery", i18n("On battery"), "battery-good-symbolic"]]
                        delegate: MouseArea {
                            required property var modelData
                            width: parent.width / 2
                            height: parent.height
                            cursorShape: Qt.PointingHandCursor
                            Accessible.role: Accessible.PageTab
                            Accessible.name: modelData[1]
                            onClicked: power.editing = modelData[0]
                            RowLayout {
                                anchors.centerIn: parent
                                spacing: Kirigami.Units.smallSpacing
                                Kirigami.Icon {
                                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                                    source: modelData[2]
                                    isMask: true
                                    color: Kirigami.Theme.textColor
                                }
                                PlasmaComponents3.Label {
                                    text: modelData[1]
                                    font.weight: power.editing === modelData[0] ? Font.DemiBold : Font.Normal
                                }
                            }
                        }
                    }
                }
            }

            Repeater {
                model: power.choices
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    readonly property bool offered: power.profiles.indexOf(modelData.profile) >= 0
                    readonly property bool selected: power.chosen === modelData.profile

                    Layout.fillWidth: true
                    implicitHeight: cardRow.implicitHeight + Kirigami.Units.largeSpacing * 2
                    radius: Kirigami.Units.cornerRadius + 2
                    opacity: offered ? 1 : 0.5
                    color: selected ? Qt.alpha(Kirigami.Theme.highlightColor, 0.12)
                                    : Qt.alpha(Kirigami.Theme.textColor, cardArea.containsMouse && offered ? 0.08 : 0.04)
                    border.width: selected ? 2 : 1
                    border.color: selected ? Kirigami.Theme.highlightColor : Qt.alpha(Kirigami.Theme.textColor, 0.1)
                    Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
                    Accessible.role: Accessible.RadioButton
                    Accessible.name: modelData.name
                    Accessible.checked: selected

                    RowLayout {
                        id: cardRow
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: Kirigami.Units.largeSpacing
                        anchors.rightMargin: Kirigami.Units.largeSpacing
                        spacing: Kirigami.Units.largeSpacing

                        Rectangle {
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 2
                            Layout.preferredHeight: Kirigami.Units.gridUnit * 2
                            radius: width / 2
                            color: card.selected ? Kirigami.Theme.highlightColor : Qt.alpha(Kirigami.Theme.textColor, 0.08)
                            Kirigami.Icon {
                                anchors.centerIn: parent
                                width: Kirigami.Units.iconSizes.smallMedium
                                height: width
                                source: card.modelData.icon
                                isMask: true
                                color: card.selected ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            PlasmaComponents3.Label {
                                Layout.fillWidth: true
                                text: card.modelData.name
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            PlasmaComponents3.Label {
                                Layout.fillWidth: true
                                text: card.offered ? card.modelData.text : i18n("Not available on this PC")
                                font: Kirigami.Theme.smallFont
                                opacity: 0.75
                                wrapMode: Text.WordWrap
                            }
                        }
                        Kirigami.Icon {
                            visible: card.selected
                            Layout.preferredWidth: Kirigami.Units.iconSizes.small
                            Layout.preferredHeight: Kirigami.Units.iconSizes.small
                            source: "checkmark-symbolic"
                            isMask: true
                            color: Kirigami.Theme.highlightColor
                        }
                    }
                    MouseArea {
                        id: cardArea
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: card.offered && !power.busy
                        cursorShape: Qt.PointingHandCursor
                        onClicked: power.profileSelected(power.editing, card.modelData.profile)
                    }
                }
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                text: power.hasBattery
                      ? i18n("VeltOS switches modes when you plug in or unplug the PC.")
                      : ""
                visible: text !== ""
                wrapMode: Text.WordWrap
                font: Kirigami.Theme.smallFont
                opacity: 0.7
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: power.errorMessage !== ""
                text: power.errorMessage
                wrapMode: Text.WordWrap
            }
        }
    }
}
