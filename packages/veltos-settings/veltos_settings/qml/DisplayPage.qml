// System > Display: scale and resolution of each display (a new
// resolution is reverted after 15 seconds unless kept, as in Windows),
// night light and the graphics cards (VeltOS Graphics Cards).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var disp: backend.display
    property int selected: 0
    readonly property var output: disp.outputs.length > selected ? disp.outputs[selected] : null
    property var revertTo: null      // {output, mode} while asking to keep a resolution
    property int secondsLeft: 15
    signal itemActivated(var item)

    function percent(scale) {
        return Math.round(scale * 100) + "%";
    }

    function changeResolution(modeId) {
        revertTo = { output: output.id, mode: output.currentMode };
        backend.setResolution(output.id, modeId);
        secondsLeft = 15;
        keepDialog.open();
    }

    spacing: 4
    Component.onCompleted: backend.refreshDisplay()

    Card {
        Layout.fillWidth: true
        visible: page.disp.loaded && page.disp.outputs.length === 0
        Label {
            width: parent.width
            text: backend.text("no_display")
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
        }
    }

    // Display picker when several are connected.
    Flow {
        Layout.fillWidth: true
        Layout.bottomMargin: 8
        visible: page.disp.outputs.length > 1
        spacing: 8
        Repeater {
            model: page.disp.outputs
            delegate: VButton {
                required property var modelData
                required property int index
                text: (index + 1) + "  " + modelData.name
                primary: index === page.selected
                onClicked: page.selected = index
            }
        }
    }

    SectionLabel {
        Layout.topMargin: 0
        visible: page.output !== null
        text: backend.text("scale_layout")
    }
    SettingRow {
        Layout.fillWidth: true
        visible: page.output !== null
        icon: "zoom-in-symbolic"
        title: backend.text("scale")
        description: backend.text("scale_desc")
        VComboBox {
            Layout.preferredWidth: 240
            accessibleName: backend.text("scale")
            options: page.output ? page.output.scales.map(s => ({ label: page.percent(s), value: s })) : []
            currentValue: page.output ? page.output.scale : 1
            onActivated: value => backend.setScale(page.output.id, value)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        visible: page.output !== null
        icon: "video-display-symbolic"
        title: backend.text("resolution")
        description: backend.text("resolution_desc")
        VComboBox {
            Layout.preferredWidth: 240
            accessibleName: backend.text("resolution")
            options: page.output ? page.output.modes.map(m => ({
                label: m.recommended ? backend.format("recommended_value", m.label) : m.label,
                value: m.id
            })) : []
            currentValue: page.output ? page.output.currentMode : ""
            onActivated: value => page.changeResolution(value)
        }
    }

    SectionLabel {
        text: backend.text("brightness_colour")
    }
    SettingCard {
        Layout.fillWidth: true
        icon: "night-light-symbolic"
        title: backend.pages.find(p => p.id === "system").items.find(i => i.id === "nightlight").title
        description: backend.pages.find(p => p.id === "system").items.find(i => i.id === "nightlight").description
        onActivated: page.itemActivated({ action: "", page: "nightlight", pageId: "system" })
    }

    SectionLabel {
        text: backend.text("related_settings")
    }
    // VeltOS Graphics Cards: the cards' drivers and properties (its own window).
    SettingCard {
        Layout.fillWidth: true
        icon: "veltos-graphics-symbolic"
        title: backend.text("graphics_cards")
        description: backend.text("graphics_cards_desc")
        external: true
        onActivated: page.itemActivated({ action: "graphics", page: "" })
    }


    Popup {
        id: keepDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 440
        modal: true
        closePolicy: Popup.NoAutoClose
        padding: 24

        function keep() {
            countdown.stop();
            page.revertTo = null;
            close();
        }
        function revert() {
            countdown.stop();
            if (page.revertTo && page.revertTo.mode !== "")
                backend.setResolution(page.revertTo.output, page.revertTo.mode);
            page.revertTo = null;
            close();
        }

        onOpened: countdown.restart()

        Timer {
            id: countdown
            interval: 1000
            repeat: true
            onTriggered: {
                page.secondsLeft -= 1;
                if (page.secondsLeft <= 0)
                    keepDialog.revert();
            }
        }

        background: Rectangle {
            radius: 8
            color: Theme.popup
            border.width: 1
            border.color: Theme.cardBorder
        }
        Overlay.modal: Rectangle { color: "#66000000" }

        contentItem: ColumnLayout {
            spacing: 16
            Label {
                Layout.fillWidth: true
                text: backend.text("keep_title")
                color: Theme.text
                font.pixelSize: 20
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                text: backend.format("keep_countdown", String(page.secondsLeft))
                color: Theme.text
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                spacing: 8
                VButton {
                    Layout.fillWidth: true
                    primary: true
                    text: backend.text("keep")
                    onClicked: keepDialog.keep()
                }
                VButton {
                    Layout.fillWidth: true
                    text: backend.text("revert")
                    onClicked: keepDialog.revert()
                }
            }
        }
    }
}
