// System > Display, as on Windows 11: the displays as numbered boxes in
// their arrangement (Identify shows each one's number on it), Multiple
// displays (duplicate, extend, show only on one; also Windows + P), and for
// the chosen display: main display, scale, resolution (a new resolution is
// reverted after 15 seconds unless kept), orientation and refresh rate;
// night light and the graphics cards (VeltOS Graphics Cards).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var disp: backend.display
    property int selected: 0
    // Display 1 when the chosen one is unplugged.
    readonly property var output: disp.outputs.length > selected ? disp.outputs[selected]
                                                                 : (disp.outputs.length > 0 ? disp.outputs[0] : null)
    readonly property bool several: disp.outputs.length > 1
    property var revertTo: null      // {output, mode} while asking to keep a resolution
    // A rearrangement not applied yet: {id: {x, y}} (logical pixels).
    property var pending: null
    function positionOf(o) {
        return page.pending && page.pending[o.id] ? page.pending[o.id] : { x: o.x, y: o.y };
    }
    function drop(o, x, y) {
        const placed = backend.snapDisplay(o.id, x, y);
        const next = {};
        let moved = false;
        for (const p of placed) {
            next[p.id] = { x: p.x, y: p.y };
            const was = (page.disp.outputs || []).find(out => out.id === p.id);
            if (!was || was.x !== p.x || was.y !== p.y)
                moved = true;
        }
        page.pending = moved ? next : null;
    }
    function applyArrangement() {
        if (!page.pending)
            return;
        const positions = Object.keys(page.pending).map(id => ({ id: parseInt(id), x: page.pending[id].x,
                                                                    y: page.pending[id].y }));
        backend.setDisplayPositions(positions);
        page.pending = null;
    }
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

    // The arrangement: one box per display, to scale, numbered as Windows
    // numbers them; displays not in use sit at the end, dimmed. As on
    // Windows 11 a display in use can be dragged: dropped, it snaps to an
    // edge of another one (devices.snap_position), and Apply moves the
    // screens there (product owner, 2026-10-26).
    Card {
        id: arrangement
        objectName: "arrangement"
        Layout.fillWidth: true
        Layout.bottomMargin: 4
        visible: page.several
        padding: 16
        ColumnLayout {
            width: parent.width
            spacing: 12
            Item {
                id: area
                Layout.fillWidth: true
                Layout.preferredHeight: 170
                readonly property var boxes: {
                    const outs = page.disp.outputs || [];
                    let right = 0;
                    const placed = outs.map(o => {
                        const at = page.positionOf(o);
                        const box = { x: at.x, y: at.y, w: Math.max(1, o.width), h: Math.max(1, o.height), o: o };
                        if (!o.enabled)
                            box.x = -1;
                        else
                            right = Math.max(right, o.x + box.w);
                        return box;
                    });
                    for (const box of placed) {
                        if (box.x < 0) {
                            box.x = right + 160;
                            box.y = 0;
                            right = box.x + box.w;
                        }
                    }
                    return placed;
                }
                readonly property real spanX: Math.max(1, ...boxes.map(b => b.x + b.w))
                readonly property real spanY: Math.max(1, ...boxes.map(b => b.y + b.h))
                // The scale is kept while a display is dragged (the boxes would
                // shrink and grow under the pointer otherwise).
                readonly property real fitFactor: Math.min((width - 24) / spanX, (height - 16) / spanY)
                property real heldFactor: 0
                readonly property real factor: heldFactor > 0 ? heldFactor : fitFactor
                readonly property real originX: (width - spanX * factor) / 2
                readonly property real originY: (height - spanY * factor) / 2
                Repeater {
                    model: area.boxes
                    delegate: Rectangle {
                        id: box
                        required property var modelData
                        required property int index
                        readonly property bool chosen: index === page.selected
                        readonly property bool movable: page.several && modelData.o.enabled
                        // The drag's offset, kept here: DragHandler's own
                        // translation is back at 0 when the drop is handled.
                        property point moved: Qt.point(0, 0)
                        x: area.originX + modelData.x * area.factor + 2 + moved.x
                        y: area.originY + modelData.y * area.factor + 2 + moved.y
                        z: drag.active ? 2 : 1
                        scale: drag.active ? 1.03 : 1
                        Behavior on scale { NumberAnimation { duration: 120 } }
                        width: modelData.w * area.factor - 4
                        height: modelData.h * area.factor - 4
                        radius: 4
                        opacity: modelData.o.enabled ? 1 : 0.5
                        color: chosen ? Theme.accent : (boxHover.hovered ? Theme.cardHover : Theme.control)
                        border.width: chosen ? 0 : 1
                        border.color: Theme.trackStrong
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.o.number + " " + modelData.o.name
                        Label {
                            anchors.centerIn: parent
                            text: box.modelData.o.number
                            color: box.chosen ? "#FFFFFF" : Theme.text
                            font.pixelSize: Math.max(14, Math.min(box.height * 0.45, 40))
                            font.weight: Font.DemiBold
                        }
                        HoverHandler {
                            id: boxHover
                            cursorShape: box.movable ? Qt.OpenHandCursor : Qt.ArrowCursor
                        }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: page.selected = box.index
                        }
                        DragHandler {
                            id: drag
                            target: null
                            enabled: box.movable
                            cursorShape: Qt.ClosedHandCursor
                            onTranslationChanged: if (active) box.moved = Qt.point(translation.x, translation.y)
                            onActiveChanged: {
                                if (active) {
                                    page.selected = box.index;
                                    area.heldFactor = area.factor;
                                    return;
                                }
                                // Plain numbers: a point read from a property stays
                                // tied to it and would read 0 after the reset below.
                                const f = area.factor, dx = box.moved.x, dy = box.moved.y;
                                box.moved = Qt.point(0, 0);
                                page.drop(box.modelData.o, box.modelData.x + dx / f, box.modelData.y + dy / f);
                                area.heldFactor = 0;
                            }
                        }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: backend.text("arrange_desc")
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
                VButton {
                    objectName: "applyArrangement"
                    visible: page.pending !== null
                    primary: true
                    text: backend.text("apply")
                    onClicked: page.applyArrangement()
                }
                VButton {
                    objectName: "cancelArrangement"
                    visible: page.pending !== null
                    text: backend.text("cancel")
                    onClicked: page.pending = null
                }
                VButton {
                    objectName: "identify"
                    text: backend.text("identify")
                    onClicked: backend.identifyDisplays()
                }
            }
        }
    }

    SettingRow {
        objectName: "multipleDisplays"
        Layout.fillWidth: true
        visible: page.several
        icon: "video-display-symbolic"
        title: backend.text("multiple_displays")
        description: backend.text("multiple_displays_desc")
        VComboBox {
            Layout.preferredWidth: 260
            accessibleName: backend.text("multiple_displays")
            options: [
                { label: backend.text("duplicate_displays"), value: "duplicate" },
                { label: backend.text("extend_displays"), value: "extend" },
                { label: backend.format("show_only_on", "1"), value: "pc" },
                { label: backend.format("show_only_on", "2"), value: "second" }
            ]
            currentValue: page.disp.project || "extend"
            onActivated: value => backend.setProject(value)
        }
    }

    SettingRow {
        Layout.fillWidth: true
        visible: page.several && page.output !== null && page.output.enabled
        icon: "favorite-symbolic"
        title: backend.text("main_display")
        description: backend.text("main_display_desc")
        ToggleSwitch {
            showLabel: false
            accessibleName: backend.text("main_display")
            checked: page.output !== null && page.output.primary
            enabledState: page.output !== null && !page.output.primary
            onToggled: checked => { if (checked) backend.setMainDisplay(page.output.id); }
        }
    }

    Card {
        Layout.fillWidth: true
        visible: page.output !== null && !page.output.enabled
        Label {
            width: parent.width
            text: backend.text("display_off")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }
    }

    SectionLabel {
        Layout.topMargin: 0
        visible: page.output !== null && page.output.enabled
        text: backend.text("scale_layout")
    }
    SettingRow {
        Layout.fillWidth: true
        visible: page.output !== null && page.output.enabled
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
        visible: page.output !== null && page.output.enabled
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
    SettingRow {
        objectName: "orientation"
        Layout.fillWidth: true
        visible: page.output !== null && page.output.enabled
        icon: "object-rotate-right-symbolic"
        title: backend.text("orientation")
        VComboBox {
            Layout.preferredWidth: 240
            accessibleName: backend.text("orientation")
            options: [
                { label: backend.text("landscape"), value: "none" },
                { label: backend.text("portrait"), value: "right" },
                { label: backend.text("landscape_flipped"), value: "inverted" },
                { label: backend.text("portrait_flipped"), value: "left" }
            ]
            currentValue: page.output ? page.output.rotation : "none"
            onActivated: value => backend.setRotation(page.output.id, value)
        }
    }
    SettingRow {
        objectName: "refreshRate"
        Layout.fillWidth: true
        visible: page.output !== null && page.output.enabled && page.output.rates.length > 1
        icon: "speedometer-symbolic"
        title: backend.text("refresh_rate")
        description: backend.text("refresh_rate_desc")
        VComboBox {
            Layout.preferredWidth: 240
            accessibleName: backend.text("refresh_rate")
            options: page.output ? page.output.rates.map(r => ({ label: r.label, value: r.id })) : []
            currentValue: page.output ? page.output.currentRate : ""
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
    // The PC's graphics cards, one below the other with the graphics card
    // icon (product owner, 2026-10-26); each opens VeltOS Graphics Cards
    // (drivers and properties, its own window).
    Repeater {
        model: backend.about.gpus || []
        delegate: SettingCard {
            objectName: "graphicsCard"
            required property string modelData
            required property int index
            Layout.fillWidth: true
            icon: "veltos-graphics-symbolic"
            title: modelData
            description: backend.format("graphics_card_number", String(index + 1)) + "  ·  "
                         + backend.text("graphics_cards_desc")
            external: true
            onActivated: page.itemActivated({ action: "graphics", page: "" })
        }
    }
    SettingCard {
        Layout.fillWidth: true
        visible: (backend.about.gpus || []).length === 0
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
