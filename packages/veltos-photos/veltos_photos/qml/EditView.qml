// "Edit image" of Windows 11 Photos: Crop (handles, aspect ratio, rotate
// left/right, flip) and Adjustment (brightness, contrast, saturation,
// warmth) with a live preview, then "Save" or "Save as copy". Python
// (edit.py, Pillow) makes the real picture from the same values.
import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import QtQuick.Layouts
import "."

Item {
    id: editor

    property var item: ({})
    property bool active: false
    property string tool: "crop"
    property int rotation: 0
    property bool flip: false
    property real cropLeft: 0
    property real cropTop: 0
    property real cropRight: 1
    property real cropBottom: 1
    property string aspect: "free"
    property int brightness: 0
    property int contrast: 0
    property int saturation: 0
    property int warmth: 0
    readonly property bool changed: rotation !== 0 || flip || cropLeft > 0 || cropTop > 0 || cropRight < 1
                                    || cropBottom < 1 || brightness !== 0 || contrast !== 0 || saturation !== 0
                                    || warmth !== 0
    signal done()

    function reset() {
        rotation = 0; flip = false;
        cropLeft = 0; cropTop = 0; cropRight = 1; cropBottom = 1; aspect = "free";
        brightness = 0; contrast = 0; saturation = 0; warmth = 0;
    }
    function edits() {
        return { rotation: rotation, flip: flip, crop: [cropLeft, cropTop, cropRight, cropBottom],
                 brightness: brightness, contrast: contrast, saturation: saturation, warmth: warmth };
    }
    function save(asCopy) {
        if (backend.saveEdit(item.path, edits(), asCopy) !== "") {
            reset();
            done();
        }
    }
    function cancel() {
        if (changed) {
            discardQuestion.ask(backend.texts.discard_title, "",
                                [{ text: backend.texts.discard, action: "discard" },
                                 { text: backend.texts.cancel, action: "cancel" }]);
        } else {
            done();
        }
    }
    function setAspect(value) {
        aspect = value;
        const ratio = value === "square" ? 1 : value === "original" ? natural.width / natural.height
                    : value === "16:9" ? 16 / 9 : value === "4:3" ? 4 / 3 : value === "3:2" ? 3 / 2 : 0;
        if (ratio <= 0)
            return;
        // Largest centred box of that ratio in the picture as shown.
        const w = shown.width, h = shown.height;
        let bw = w, bh = w / ratio;
        if (bh > h) { bh = h; bw = h * ratio; }
        cropLeft = (w - bw) / 2 / w; cropRight = 1 - cropLeft;
        cropTop = (h - bh) / 2 / h; cropBottom = 1 - cropTop;
    }
    onActiveChanged: if (active) reset()

    Rectangle { anchors.fill: parent; color: Theme.content }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- Preview -------------------------------------------------------------------
        Item {
            id: area
            Layout.fillWidth: true
            Layout.fillHeight: true

            readonly property bool sideways: editor.rotation % 180 !== 0
            readonly property real srcW: sideways ? natural.height : natural.width
            readonly property real srcH: sideways ? natural.width : natural.height
            readonly property real fit: srcW > 0 ? Math.min((width - 80) / srcW, (height - 80) / srcH) : 1

            Item {
                id: natural
                width: Math.max(1, picture.implicitWidth)
                height: Math.max(1, picture.implicitHeight)
                visible: false
            }

            // The picture as it will look (rotated, flipped, adjusted).
            Item {
                id: shown
                anchors.centerIn: parent
                width: area.srcW * area.fit
                height: area.srcH * area.fit

                Image {
                    id: picture
                    anchors.centerIn: parent
                    width: (area.sideways ? shown.height : shown.width)
                    height: (area.sideways ? shown.width : shown.height)
                    rotation: editor.rotation
                    source: editor.active && editor.item.path ? backend.fileUrl(editor.item.path, editor.item.mtime || 0) : ""
                    sourceSize.width: 2048
                    sourceSize.height: 2048
                    autoTransform: true
                    asynchronous: true
                    smooth: true
                    visible: false
                }
                MultiEffect {
                    anchors.fill: picture
                    rotation: picture.rotation
                    source: picture
                    // Flipped left to right before the rotation, as edit.py does.
                    transform: Scale { origin.x: picture.width / 2; xScale: editor.flip ? -1 : 1 }
                    brightness: editor.brightness / 200
                    contrast: editor.contrast / 100
                    saturation: editor.saturation / 100
                    colorization: Math.abs(editor.warmth) / 400
                    colorizationColor: editor.warmth >= 0 ? "#FF9A2E" : "#2E8BFF"
                }

                // Dimmed outside of the crop box, and the box with its handles.
                Rectangle { color: "#88000000"; x: 0; y: 0; width: parent.width; height: editor.cropTop * parent.height; visible: editor.tool === "crop" }
                Rectangle { color: "#88000000"; x: 0; y: editor.cropBottom * parent.height; width: parent.width
                            height: parent.height - y; visible: editor.tool === "crop" }
                Rectangle { color: "#88000000"; x: 0; y: editor.cropTop * parent.height; width: editor.cropLeft * parent.width
                            height: (editor.cropBottom - editor.cropTop) * parent.height; visible: editor.tool === "crop" }
                Rectangle { color: "#88000000"; x: editor.cropRight * parent.width; y: editor.cropTop * parent.height
                            width: parent.width - x; height: (editor.cropBottom - editor.cropTop) * parent.height
                            visible: editor.tool === "crop" }

                Rectangle {
                    id: box
                    visible: editor.tool === "crop"
                    x: editor.cropLeft * shown.width
                    y: editor.cropTop * shown.height
                    width: (editor.cropRight - editor.cropLeft) * shown.width
                    height: (editor.cropBottom - editor.cropTop) * shown.height
                    color: "transparent"
                    border.width: 1
                    border.color: "#FFFFFF"
                    // Thirds, as in Windows.
                    Repeater {
                        model: 2
                        Rectangle { required property int index; x: box.width * (index + 1) / 3; width: 1; height: box.height; color: "#80FFFFFF" }
                    }
                    Repeater {
                        model: 2
                        Rectangle { required property int index; y: box.height * (index + 1) / 3; height: 1; width: box.width; color: "#80FFFFFF" }
                    }
                    // Moving the box.
                    DragHandler {
                        id: moveDrag
                        target: null
                        property real startL
                        property real startT
                        property real startR
                        property real startB
                        onActiveChanged: if (active) {
                            startL = editor.cropLeft; startT = editor.cropTop;
                            startR = editor.cropRight; startB = editor.cropBottom;
                        }
                        onTranslationChanged: {
                            const dx = Math.max(-startL, Math.min(1 - startR, translation.x / shown.width));
                            const dy = Math.max(-startT, Math.min(1 - startB, translation.y / shown.height));
                            editor.cropLeft = startL + dx; editor.cropRight = startR + dx;
                            editor.cropTop = startT + dy; editor.cropBottom = startB + dy;
                        }
                    }
                }

                // Corner handles.
                Repeater {
                    model: [[0, 0], [1, 0], [0, 1], [1, 1]]
                    delegate: Rectangle {
                        id: handle
                        required property var modelData
                        visible: editor.tool === "crop"
                        width: 18
                        height: 18
                        radius: 9
                        color: "#FFFFFF"
                        border.width: 1
                        border.color: "#40000000"
                        x: (modelData[0] ? editor.cropRight : editor.cropLeft) * shown.width - 9
                        y: (modelData[1] ? editor.cropBottom : editor.cropTop) * shown.height - 9
                        DragHandler {
                            target: null
                            property real startX
                            property real startY
                            onActiveChanged: if (active) {
                                startX = handle.modelData[0] ? editor.cropRight : editor.cropLeft;
                                startY = handle.modelData[1] ? editor.cropBottom : editor.cropTop;
                            }
                            onTranslationChanged: {
                                const min = 0.05;
                                const nx = Math.max(0, Math.min(1, startX + translation.x / shown.width));
                                let ny = Math.max(0, Math.min(1, startY + translation.y / shown.height));
                                if (handle.modelData[0]) editor.cropRight = Math.max(editor.cropLeft + min, nx);
                                else editor.cropLeft = Math.min(editor.cropRight - min, nx);
                                if (handle.modelData[1]) editor.cropBottom = Math.max(editor.cropTop + min, ny);
                                else editor.cropTop = Math.min(editor.cropBottom - min, ny);
                                editor.aspect = "free";
                            }
                        }
                    }
                }
            }
        }

        // --- Tools ----------------------------------------------------------------------
        Rectangle {
            Layout.preferredWidth: 300
            Layout.fillHeight: true
            color: Theme.window
            Rectangle { anchors.left: parent.left; height: parent.height; width: 1; color: Theme.separator }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12

                // Crop | Adjustment
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Repeater {
                        model: [["crop", "crop"], ["adjust", "adjust"]]
                        delegate: Rectangle {
                            required property var modelData
                            readonly property bool chosen: editor.tool === modelData[0]
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            radius: 4
                            color: chosen ? Theme.selected : (tabHover.hovered ? Theme.hover : "transparent")
                            Accessible.role: Accessible.PageTab
                            Accessible.name: backend.texts[modelData[0]]
                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 8
                                Glyph { Layout.preferredWidth: 16; Layout.preferredHeight: 16; kind: modelData[1] }
                                Text { text: backend.texts[modelData[0]]; color: Theme.text; font.pixelSize: Theme.fontSize }
                            }
                            Rectangle {
                                visible: parent.chosen
                                anchors.bottom: parent.bottom
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 20; height: 3; radius: 2
                                color: Theme.accent
                            }
                            HoverHandler { id: tabHover }
                            TapHandler { onTapped: editor.tool = modelData[0] }
                        }
                    }
                }

                // Crop tools.
                ColumnLayout {
                    visible: editor.tool === "crop"
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: backend.texts.aspect; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: [["free", backend.texts.aspect_free], ["original", backend.texts.aspect_original],
                                    ["square", backend.texts.aspect_square], ["16:9", "16:9"], ["4:3", "4:3"], ["3:2", "3:2"]]
                            delegate: Rectangle {
                                required property var modelData
                                width: label.implicitWidth + 22
                                height: 30
                                radius: 15
                                color: editor.aspect === modelData[0] ? Theme.accent : Theme.field
                                border.width: editor.aspect === modelData[0] ? 0 : 1
                                border.color: Theme.fieldBorder
                                Text {
                                    id: label
                                    anchors.centerIn: parent
                                    text: modelData[1]
                                    color: editor.aspect === modelData[0] ? Theme.accentText : Theme.text
                                    font.pixelSize: Theme.smallFont
                                }
                                TapHandler { onTapped: editor.setAspect(modelData[0]) }
                            }
                        }
                    }
                    RowLayout {
                        Layout.topMargin: 6
                        spacing: 6
                        component ToolIcon: Rectangle {
                            id: ti
                            property string glyph
                            property string label
                            signal clicked()
                            width: 40; height: 36; radius: 4
                            color: tiHover.hovered ? Theme.hover : "transparent"
                            Accessible.role: Accessible.Button
                            Accessible.name: label
                            Glyph { anchors.centerIn: parent; width: 16; height: 16; kind: ti.glyph }
                            ToolTip.visible: tiHover.hovered
                            ToolTip.text: label
                            HoverHandler { id: tiHover }
                            TapHandler { onTapped: ti.clicked() }
                        }
                        ToolIcon { glyph: "rotate-left"; label: backend.texts.rotate_left
                                   onClicked: { editor.rotation = (editor.rotation + 270) % 360; editor.setAspect("free"); editor.cropLeft = 0; editor.cropTop = 0; editor.cropRight = 1; editor.cropBottom = 1; } }
                        ToolIcon { glyph: "rotate"; label: backend.texts.rotate_right
                                   onClicked: { editor.rotation = (editor.rotation + 90) % 360; editor.cropLeft = 0; editor.cropTop = 0; editor.cropRight = 1; editor.cropBottom = 1; } }
                        ToolIcon { glyph: "flip"; label: backend.texts.flip; onClicked: editor.flip = !editor.flip }
                    }
                }

                // Adjustments.
                ColumnLayout {
                    visible: editor.tool === "adjust"
                    Layout.fillWidth: true
                    spacing: 4
                    Repeater {
                        model: ["brightness", "contrast", "saturation", "warmth"]
                        delegate: ColumnLayout {
                            required property string modelData
                            Layout.fillWidth: true
                            spacing: 0
                            RowLayout {
                                Layout.fillWidth: true
                                Text { Layout.fillWidth: true; text: backend.texts[modelData]; color: Theme.text; font.pixelSize: Theme.fontSize }
                                Text { text: editor[modelData]; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                            }
                            Slider {
                                Layout.fillWidth: true
                                from: -100
                                to: 100
                                stepSize: 1
                                value: editor[modelData]
                                onMoved: editor[modelData] = Math.round(value)
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Text {
                    Layout.alignment: Qt.AlignRight
                    text: backend.texts.reset
                    color: editor.changed ? Theme.accent : Theme.disabled
                    font.pixelSize: Theme.fontSize
                    TapHandler { enabled: editor.changed; onTapped: editor.reset() }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    component Button2: Rectangle {
                        id: b2
                        property string text
                        property bool primary: false
                        property bool enabledState: true
                        signal clicked()
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        radius: 4
                        opacity: enabledState ? 1 : 0.45
                        color: primary ? (b2Hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                                       : (b2Hover.hovered ? Theme.hover : Theme.field)
                        border.width: primary ? 0 : 1
                        border.color: Theme.fieldBorder
                        Accessible.role: Accessible.Button
                        Accessible.name: text
                        Text { anchors.centerIn: parent; text: b2.text; color: b2.primary ? Theme.accentText : Theme.text; font.pixelSize: Theme.fontSize }
                        HoverHandler { id: b2Hover }
                        TapHandler { enabled: b2.enabledState; onTapped: b2.clicked() }
                    }
                    Button2 { text: backend.texts.save_copy; primary: true; enabledState: editor.changed; onClicked: editor.save(true) }
                    Button2 { text: backend.texts.save; enabledState: editor.changed; onClicked: editor.save(false) }
                }
                Button2 { Layout.fillWidth: true; text: backend.texts.cancel; onClicked: editor.cancel() }
            }
        }
    }

    WinDialog {
        id: discardQuestion
        onChosen: action => {
            if (action === "discard") {
                editor.reset();
                editor.done();
            }
        }
    }
}
