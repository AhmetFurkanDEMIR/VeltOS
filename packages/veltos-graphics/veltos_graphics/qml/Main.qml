// VeltOS Graphics Cards window, in the look of Windows 11 Settings: one
// card per graphics card with its name and driver, an InfoBar that says
// whether the driver is complete and offers the one button that makes it
// so (Install driver, Restart now, Check for updates), the progress of a
// running installation, Secure Boot's key registration for NVIDIA's driver
// and the card's properties in an expander.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window
    width: 900
    height: 700
    minimumWidth: 620
    minimumHeight: 460
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    // slot -> true for cards whose Properties are open.
    property var expanded: ({})
    readonly property bool working: backend.busy !== ""

    function toggle(slot) {
        const next = Object.assign({}, expanded);
        next[slot] = !next[slot];
        expanded = next;
    }
    function severity(state) {
        if (state === "proprietary" || state === "ready" || state === "virtual")
            return "success";
        if (state === "unsupported" || state === "unknown")
            return "warning";
        return "info";
    }
    // The InfoBar's buttons for a card: [{text, action, primary}].
    function buttons(card) {
        const t = backend.texts;
        if (card.state === "available")
            return [{text: t.install_driver, action: "install", primary: true}];
        if (card.state === "missing")
            return [{text: t.install_parts, action: "install", primary: true}];
        if (card.state === "restart")
            return [{text: t.restart_now, action: "restart", primary: true}];
        if (card.state === "proprietary" || card.state === "ready")
            return [{text: t.update_driver, action: "update", primary: false}];
        return [];
    }
    function press(slot, action) {
        if (action === "install")
            backend.installDriver(slot);
        else if (action === "update")
            backend.updateDriver(slot);
        else if (action === "restart")
            backend.restart();
        else if (action === "open")
            backend.useOpenDriver(slot);
    }
    // For tests: the button texts of card `index`, "|"-separated.
    function buttonTexts(index) {
        return buttons(backend.cards[index]).map(b => b.text).join("|");
    }

    Flickable {
        id: flick
        anchors.fill: parent
        contentWidth: width
        contentHeight: page.implicitHeight + 64
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        ColumnLayout {
            id: page
            x: 36
            y: 28
            width: flick.width - 72
            spacing: 8

            // Title, as a Settings page shows it.
            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 10
                spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: backend.texts.app_title
                        color: Theme.text
                        font.pixelSize: Theme.pageTitleSize
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: backend.texts.subtitle
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize + 1
                        wrapMode: Text.Wrap
                    }
                }
                VButton {
                    Layout.alignment: Qt.AlignBottom
                    text: backend.texts.refresh
                    enabledState: !window.working
                    onClicked: backend.refresh()
                }
            }

            // While the cards are read.
            RowLayout {
                visible: !backend.loaded
                spacing: 12
                BusyIndicator {
                    running: !backend.loaded
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                }
                Label {
                    text: backend.texts.loading
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize + 1
                }
            }

            Rectangle {
                Layout.fillWidth: true
                visible: backend.loaded && backend.cards.length === 0
                implicitHeight: 64
                radius: Theme.radius
                color: Theme.card
                border.color: Theme.cardBorder
                Label {
                    anchors.verticalCenter: parent.verticalCenter
                    x: 20
                    text: backend.texts.no_cards
                    color: Theme.text
                    font.pixelSize: Theme.titleSize
                }
            }

            Repeater {
                model: backend.cards
                delegate: Rectangle {
                    id: gpu
                    required property var modelData
                    required property int index
                    readonly property bool open: !!window.expanded[modelData.slot]
                    readonly property bool busyHere: backend.busy === modelData.slot

                    Layout.fillWidth: true
                    Layout.bottomMargin: 8
                    implicitHeight: body.implicitHeight
                    radius: Theme.radius
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder

                    ColumnLayout {
                        id: body
                        width: parent.width
                        spacing: 0

                        // Picture, name and driver.
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.margins: 20
                            spacing: 18
                            Kirigami.Icon {
                                Layout.preferredWidth: 64
                                Layout.preferredHeight: 64
                                source: "veltos-graphics"
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Label {
                                    Layout.fillWidth: true
                                    text: gpu.modelData.name
                                    color: Theme.text
                                    font.pixelSize: Theme.nameSize
                                    font.weight: Font.DemiBold
                                    wrapMode: Text.Wrap
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: backend.texts.driver_in_use.replace("{driver}", gpu.modelData.driverName)
                                    color: Theme.subtext
                                    font.pixelSize: Theme.bodySize + 1
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        // What the driver needs, with its button.
                        InfoBar {
                            Layout.fillWidth: true
                            Layout.leftMargin: 20
                            Layout.rightMargin: 20
                            severity: window.severity(gpu.modelData.state)
                            text: gpu.modelData.stateText
                            Repeater {
                                model: window.buttons(gpu.modelData)
                                delegate: VButton {
                                    required property var modelData
                                    text: modelData.text
                                    primary: modelData.primary
                                    enabledState: !window.working
                                    onClicked: window.press(gpu.modelData.slot, modelData.action)
                                }
                            }
                        }

                        // A running installation.
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.leftMargin: 20
                            Layout.rightMargin: 20
                            Layout.topMargin: 14
                            visible: gpu.busyHere
                            spacing: 8
                            Label {
                                Layout.fillWidth: true
                                text: backend.busyText + (backend.percent >= 0 ? "  " + backend.percent + "%" : "")
                                color: Theme.text
                                font.pixelSize: Theme.bodySize + 1
                            }
                            // Windows 11 progress bar; a sliding segment while the
                            // percentage is not known yet.
                            Rectangle {
                                id: track
                                Layout.fillWidth: true
                                implicitHeight: 4
                                radius: 2
                                color: Theme.track
                                clip: true
                                Rectangle {
                                    visible: backend.percent >= 0
                                    width: track.width * Math.max(0, backend.percent) / 100
                                    height: parent.height
                                    radius: 2
                                    color: Theme.accent
                                    Behavior on width { NumberAnimation { duration: 200 } }
                                }
                                Rectangle {
                                    id: slider
                                    visible: backend.percent < 0
                                    width: track.width * 0.3
                                    height: parent.height
                                    radius: 2
                                    color: Theme.accent
                                    NumberAnimation on x {
                                        running: gpu.busyHere && backend.percent < 0 && window.visible
                                        from: -track.width * 0.3
                                        to: track.width
                                        duration: 1600
                                        loops: Animation.Infinite
                                    }
                                }
                            }
                        }

                        // The result of the last installation or update.
                        InfoBar {
                            Layout.fillWidth: true
                            Layout.leftMargin: 20
                            Layout.rightMargin: 20
                            Layout.topMargin: 10
                            // (After NVIDIA's driver is installed the card's own
                            // InfoBar already says to restart.)
                            visible: gpu.modelData.message !== "" && !gpu.busyHere
                                     && !(gpu.modelData.messageOk && gpu.modelData.state === "restart")
                            severity: gpu.modelData.messageOk ? "success" : "error"
                            text: gpu.modelData.message
                        }

                        // Secure Boot: register DKMS's key with the firmware.
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.leftMargin: 20
                            Layout.rightMargin: 20
                            Layout.topMargin: 14
                            visible: gpu.modelData.needsKey
                            spacing: 8
                            Label {
                                text: backend.texts.sb_title
                                color: Theme.text
                                font.pixelSize: Theme.sectionSize
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: backend.texts.sb_text
                                color: Theme.subtext
                                font.pixelSize: Theme.bodySize + 1
                                wrapMode: Text.Wrap
                            }
                            Flow {
                                Layout.fillWidth: true
                                spacing: 8
                                PasswordField {
                                    id: keyPassword
                                    placeholder: backend.texts.sb_password
                                }
                                PasswordField {
                                    id: keyConfirm
                                    placeholder: backend.texts.sb_confirm
                                    onAccepted: backend.registerKey(keyPassword.text, keyConfirm.text)
                                }
                                VButton {
                                    text: backend.texts.sb_register
                                    primary: true
                                    enabledState: keyPassword.text.length > 0 && keyConfirm.text.length > 0
                                    onClicked: backend.registerKey(keyPassword.text, keyConfirm.text)
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                visible: text !== ""
                                text: backend.keyMessage
                                color: backend.keyMessage === backend.texts.sb_registered ? Theme.successIcon : Theme.errorIcon
                                font.pixelSize: Theme.bodySize + 1
                                wrapMode: Text.Wrap
                            }
                        }

                        // Properties (an expander, as in Windows 11 Settings).
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.topMargin: 16
                            implicitHeight: 1
                            color: Theme.divider
                        }
                        Rectangle {
                            id: expanderHead
                            Layout.fillWidth: true
                            implicitHeight: Math.round(48 * Theme.textScale)
                            color: headTap.pressed ? Theme.cardPressed : headHover.hovered ? Theme.cardHover : "transparent"
                            bottomLeftRadius: gpu.open ? 0 : Theme.radius
                            bottomRightRadius: gpu.open ? 0 : Theme.radius
                            activeFocusOnTab: true
                            Accessible.role: Accessible.Button
                            Accessible.name: backend.texts.show_properties
                            Keys.onReturnPressed: window.toggle(gpu.modelData.slot)
                            Keys.onSpacePressed: window.toggle(gpu.modelData.slot)
                            Label {
                                anchors.verticalCenter: parent.verticalCenter
                                x: 20
                                text: backend.texts.show_properties
                                color: Theme.text
                                font.pixelSize: Theme.titleSize
                            }
                            Kirigami.Icon {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: 20
                                width: 16
                                height: 16
                                source: "go-down-symbolic"
                                isMask: true
                                color: Theme.text
                                rotation: gpu.open ? 180 : 0
                                Behavior on rotation { NumberAnimation { duration: 150 } }
                            }
                            HoverHandler { id: headHover; cursorShape: Qt.PointingHandCursor }
                            TapHandler { id: headTap; onTapped: window.toggle(gpu.modelData.slot) }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.leftMargin: 20
                            Layout.rightMargin: 20
                            Layout.topMargin: 4
                            Layout.bottomMargin: gpu.modelData.openDriver ? 10 : 18
                            visible: gpu.open
                            spacing: 8
                            Repeater {
                                model: gpu.open ? gpu.modelData.properties : []
                                delegate: RowLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: 24
                                    Label {
                                        Layout.preferredWidth: Math.round(170 * Theme.textScale)
                                        Layout.alignment: Qt.AlignTop
                                        text: modelData.label
                                        color: Theme.subtext
                                        font.pixelSize: Theme.bodySize + 1
                                        wrapMode: Text.Wrap
                                    }
                                    // A TextEdit, so the value can be selected and copied.
                                    TextEdit {
                                        Layout.fillWidth: true
                                        text: modelData.value
                                        readOnly: true
                                        selectByMouse: true
                                        wrapMode: TextEdit.Wrap
                                        color: Theme.text
                                        selectionColor: Theme.accent
                                        selectedTextColor: "#FFFFFF"
                                        font.pixelSize: Theme.bodySize + 1
                                    }
                                }
                            }
                        }
                        Label {
                            Layout.leftMargin: 20
                            Layout.bottomMargin: 18
                            visible: gpu.open && gpu.modelData.openDriver
                            text: "<a href=\"#\">" + backend.texts.use_open + "</a>"
                            textFormat: Text.StyledText
                            linkColor: Theme.accent
                            font.pixelSize: Theme.bodySize + 1
                            enabled: !window.working
                            onLinkActivated: window.press(gpu.modelData.slot, "open")
                            HoverHandler { cursorShape: Qt.PointingHandCursor }
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.topMargin: 6
                visible: backend.loaded && backend.cards.length > 0
                text: backend.texts.footer
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.Wrap
            }
        }
    }
}
