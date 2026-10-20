/*
    VeltOS Snipping Tool window, in the layout of Windows 11's Snipping
    Tool: a command bar with "+ New", the snipping mode and the delay; once
    there is a snip, the markup tools (ballpoint pen, highlighter, eraser,
    image crop, undo, redo) in the middle and Save, Copy and "..." on the
    right; the snip below on a plain canvas. `backend` is app.Editor; the
    strokes live here and go to the backend as JSON (picture pixels).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    readonly property real dpr: Screen.devicePixelRatio > 0 ? Screen.devicePixelRatio : 1
    width: backend.hasImage ? Math.min(Screen.desktopAvailableWidth * 0.85,
                                       Math.max(760, backend.imageWidth / dpr + 64)) : 760
    height: backend.hasImage ? Math.min(Screen.desktopAvailableHeight * 0.85,
                                        Math.max(420, backend.imageHeight / dpr + 140)) : 280
    minimumWidth: 600
    minimumHeight: 220
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    // "pen", "highlighter", "eraser", "crop" or "" (no tool)
    property string tool: ""
    property var strokes: []
    property var history: []          // earlier stroke lists (Undo)
    property var future: []           // (Redo)
    property var current: null        // stroke being drawn
    property color penColor: "#1B1D24"
    property real penWidth: 4
    property color highlighterColor: "#FFE14D"
    property real highlighterWidth: 18
    property rect cropRect: Qt.rect(0, 0, 0, 0)    // picture pixels

    readonly property var penColors: ["#1B1D24", "#FFFFFF", "#E81123", "#FF8C00", "#FFE14D",
                                      "#16C60C", "#2F5EE6", "#8E44AD"]
    readonly property var highlighterColors: ["#FFE14D", "#7CFC00", "#40E0D0", "#FF69B4"]

    function strokesJson() {
        return JSON.stringify(strokes);
    }
    function setStrokes(list) {
        history = history.concat([strokes]);
        future = [];
        strokes = list;
        ink.requestPaint();
    }
    function undo() {
        if (history.length === 0) {
            return;
        }
        future = future.concat([strokes]);
        strokes = history[history.length - 1];
        history = history.slice(0, history.length - 1);
        ink.requestPaint();
    }
    function redo() {
        if (future.length === 0) {
            return;
        }
        history = history.concat([strokes]);
        strokes = future[future.length - 1];
        future = future.slice(0, future.length - 1);
        ink.requestPaint();
    }
    function resetMarkup() {
        strokes = [];
        history = [];
        future = [];
        current = null;
        tool = "";
        ink.requestPaint();
    }
    function chooseTool(name) {
        if (tool === name && (name === "pen" || name === "highlighter")) {
            colours.open();          // second click: colours and size, as on Windows
            return;
        }
        tool = tool === name ? "" : name;
        if (tool === "crop") {
            cropRect = Qt.rect(0, 0, backend.imageWidth, backend.imageHeight);
        }
    }
    function applyCrop() {
        backend.applyCrop(cropRect.x, cropRect.y, cropRect.width, cropRect.height, strokesJson());
    }

    Connections {
        target: backend
        function onHideRequested() {
            window.visible = false;
        }
        function onShowRequested() {
            window.visible = true;
            window.raise();
            window.requestActivate();
        }
        function onChanged() {
            if (page.shownUrl !== backend.imageUrl) {
                page.shownUrl = backend.imageUrl;
                window.resetMarkup();
            }
        }
    }

    Shortcut { sequences: ["Ctrl+N"]; onActivated: backend.newSnip() }
    Shortcut { sequences: [StandardKey.Save]; enabled: backend.hasImage; onActivated: backend.save(window.strokesJson()) }
    Shortcut { sequences: [StandardKey.Copy]; enabled: backend.hasImage; onActivated: backend.copy(window.strokesJson()) }
    Shortcut { sequences: [StandardKey.Undo]; onActivated: window.undo() }
    Shortcut { sequences: [StandardKey.Redo, "Ctrl+Y"]; onActivated: window.redo() }
    Shortcut {
        sequences: ["Escape"]
        enabled: window.tool === "crop"
        onActivated: window.tool = ""
    }

    // --- Command bar --------------------------------------------------------------
    Rectangle {
        id: commandBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 56
        color: Theme.window

        RowLayout {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 12
            spacing: 4

            VButton {
                objectName: "new"
                accent: true
                glyph: "plus"
                text: backend.texts["new"]
                onClicked: backend.newSnip()
            }
            BarButton {
                objectName: "mode"
                glyph: backend.mode
                chevron: true
                tip: backend.texts["mode_" + backend.mode]
                onClicked: modeMenu.open()
                Menu {
                    id: modeMenu
                    y: parent.height
                    Repeater {
                        model: ["rect", "window", "full", "free"]
                        delegate: MenuItem {
                            required property string modelData
                            text: backend.texts["mode_" + modelData]
                            checkable: true
                            checked: backend.mode === modelData
                            onTriggered: backend.setMode(modelData)
                        }
                    }
                }
            }
            BarButton {
                objectName: "delay"
                glyph: "clock"
                chevron: true
                text: backend.delay === 0 ? backend.texts.no_delay : backend.texts["delay_" + backend.delay]
                onClicked: delayMenu.open()
                Menu {
                    id: delayMenu
                    y: parent.height
                    Repeater {
                        model: [0, 3, 5, 10]
                        delegate: MenuItem {
                            required property int modelData
                            text: modelData === 0 ? backend.texts.no_delay : backend.texts["delay_" + modelData]
                            checkable: true
                            checked: backend.delay === modelData
                            onTriggered: backend.setDelay(modelData)
                        }
                    }
                }
            }
        }

        // Markup tools in the middle, like Windows.
        Row {
            id: tools
            visible: backend.hasImage
            anchors.centerIn: parent
            spacing: 2

            BarButton {
                objectName: "pen"
                glyph: "pen"
                tip: backend.texts.pen
                checked: window.tool === "pen"
                showDot: true
                dot: window.penColor
                onClicked: window.chooseTool("pen")
            }
            BarButton {
                objectName: "highlighter"
                glyph: "highlighter"
                tip: backend.texts.highlighter
                checked: window.tool === "highlighter"
                showDot: true
                dot: window.highlighterColor
                onClicked: window.chooseTool("highlighter")
            }
            BarButton {
                objectName: "eraser"
                glyph: "eraser"
                tip: backend.texts.eraser
                checked: window.tool === "eraser"
                onClicked: window.chooseTool("eraser")
            }
            BarButton {
                objectName: "crop"
                glyph: "crop"
                tip: backend.texts.crop
                checked: window.tool === "crop"
                onClicked: window.chooseTool("crop")
            }
            Rectangle {
                width: 1
                height: 24
                anchors.verticalCenter: parent.verticalCenter
                color: Theme.cardBorder
            }
            BarButton {
                objectName: "undo"
                glyph: "undo"
                tip: backend.texts.undo
                enabled: window.history.length > 0
                onClicked: window.undo()
            }
            BarButton {
                objectName: "redo"
                glyph: "redo"
                tip: backend.texts.redo
                enabled: window.future.length > 0
                onClicked: window.redo()
            }
        }

        RowLayout {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 12
            spacing: 2

            // While cropping: Apply / Cancel instead of Save / Copy.
            VButton {
                visible: window.tool === "crop"
                accent: true
                glyph: "check"
                text: backend.texts.apply
                onClicked: window.applyCrop()
            }
            VButton {
                visible: window.tool === "crop"
                text: backend.texts.cancel
                onClicked: window.tool = ""
            }
            BarButton {
                objectName: "save"
                visible: backend.hasImage && window.tool !== "crop"
                glyph: "save"
                tip: backend.texts.save + " (Ctrl+S)"
                onClicked: backend.save(window.strokesJson())
            }
            BarButton {
                objectName: "copy"
                visible: backend.hasImage && window.tool !== "crop"
                glyph: "copy"
                tip: backend.texts.copy + " (Ctrl+C)"
                onClicked: backend.copy(window.strokesJson())
            }
            BarButton {
                objectName: "more"
                glyph: "more"
                onClicked: moreMenu.open()
                Menu {
                    id: moreMenu
                    y: parent.height
                    x: parent.width - width
                    MenuItem {
                        text: backend.texts.auto_save
                        checkable: true
                        checked: backend.autoSave
                        onTriggered: backend.setAutoSave(!backend.autoSave)
                    }
                }
            }
        }
    }

    // Pen colours and sizes (second click on the pen or highlighter).
    Popup {
        id: colours
        x: tools.x + (window.tool === "highlighter" ? 40 : 0)
        y: commandBar.height - 4
        padding: 12
        background: Rectangle {
            radius: Theme.radius
            color: Theme.card
            border.color: Theme.cardBorder
        }
        contentItem: Column {
            spacing: 10
            Grid {
                columns: 4
                spacing: 8
                Repeater {
                    model: window.tool === "highlighter" ? window.highlighterColors : window.penColors
                    delegate: Rectangle {
                        required property string modelData
                        width: 24
                        height: 24
                        radius: 12
                        color: modelData
                        border.width: Qt.colorEqual(window.tool === "highlighter" ? window.highlighterColor
                                                                                  : window.penColor, modelData) ? 3 : 1
                        border.color: border.width > 1 ? Theme.accent : Theme.cardBorder
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (window.tool === "highlighter") {
                                    window.highlighterColor = parent.modelData;
                                } else {
                                    window.penColor = parent.modelData;
                                }
                            }
                        }
                    }
                }
            }
            Slider {
                width: 128
                from: window.tool === "highlighter" ? 8 : 1
                to: window.tool === "highlighter" ? 40 : 24
                stepSize: 1
                value: window.tool === "highlighter" ? window.highlighterWidth : window.penWidth
                onMoved: {
                    if (window.tool === "highlighter") {
                        window.highlighterWidth = value;
                    } else {
                        window.penWidth = value;
                    }
                }
            }
        }
    }

    // --- Empty window ---------------------------------------------------------------
    Column {
        visible: !backend.hasImage
        anchors.centerIn: parent
        anchors.verticalCenterOffset: commandBar.height / 2
        width: Math.min(parent.width - 64, 520)
        spacing: 8
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: backend.texts.empty
            color: Theme.text
            font.pixelSize: 15
            wrapMode: Text.Wrap
        }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: backend.texts.empty_hint
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
            wrapMode: Text.Wrap
        }
    }

    // --- The snip -------------------------------------------------------------------
    Rectangle {
        id: canvasArea
        visible: backend.hasImage
        anchors.top: commandBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: infoBar.visible ? infoBar.top : parent.bottom
        color: Theme.canvas

        Item {
            id: page
            property string shownUrl: ""
            // Picture pixels -> window: 1:1 on the screen it was taken from,
            // smaller when it does not fit.
            readonly property real scale: backend.imageWidth > 0
                ? Math.min(1 / window.dpr, (canvasArea.width - 32) / backend.imageWidth,
                           (canvasArea.height - 32) / backend.imageHeight) : 1
            width: backend.imageWidth * scale
            height: backend.imageHeight * scale
            anchors.centerIn: parent

            Rectangle {      // shadow-like edge
                anchors.fill: parent
                anchors.margins: -1
                color: "transparent"
                border.color: Theme.cardBorder
            }
            Image {
                id: picture
                anchors.fill: parent
                source: backend.imageUrl
                cache: false
                smooth: true
                mipmap: true
            }
            Canvas {
                id: ink
                anchors.fill: parent
                function drawStroke(ctx, s) {
                    const p = s.points;
                    if (!p || p.length < 2) {
                        return;
                    }
                    const k = page.scale;
                    ctx.globalAlpha = s.tool === "highlighter" ? 0.45 : 1;
                    ctx.strokeStyle = s.color;
                    ctx.fillStyle = s.color;
                    ctx.lineWidth = Math.max(1, s.width * k);
                    ctx.lineCap = s.tool === "highlighter" ? "butt" : "round";
                    ctx.lineJoin = "round";
                    ctx.beginPath();
                    ctx.moveTo(p[0] * k, p[1] * k);
                    if (p.length === 2) {
                        ctx.lineTo(p[0] * k + 0.1, p[1] * k);
                    }
                    for (let i = 2; i < p.length - 1; i += 2) {
                        ctx.lineTo(p[i] * k, p[i + 1] * k);
                    }
                    ctx.stroke();
                }
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    for (const s of window.strokes) {
                        drawStroke(ctx, s);
                    }
                    if (window.current) {
                        drawStroke(ctx, window.current);
                    }
                }
            }
            MouseArea {
                anchors.fill: parent
                enabled: window.tool === "pen" || window.tool === "highlighter" || window.tool === "eraser"
                cursorShape: window.tool === "" ? Qt.ArrowCursor : Qt.CrossCursor
                function erase(mouse) {
                    const k = page.scale;
                    const left = backend.eraseAt(window.strokesJson(), mouse.x / k, mouse.y / k, 8 / k);
                    if (left !== window.strokesJson()) {
                        window.setStrokes(JSON.parse(left));
                    }
                }
                onPressed: mouse => {
                    if (window.tool === "eraser") {
                        erase(mouse);
                        return;
                    }
                    const pen = window.tool === "pen";
                    window.current = {"tool": window.tool,
                                      "color": String(pen ? window.penColor : window.highlighterColor),
                                      "width": pen ? window.penWidth : window.highlighterWidth,
                                      "points": [mouse.x / page.scale, mouse.y / page.scale]};
                    ink.requestPaint();
                }
                onPositionChanged: mouse => {
                    if (window.tool === "eraser") {
                        if (pressed) {
                            erase(mouse);
                        }
                        return;
                    }
                    if (window.current) {
                        window.current.points.push(mouse.x / page.scale, mouse.y / page.scale);
                        ink.requestPaint();
                    }
                }
                onReleased: {
                    if (window.current) {
                        const done = window.current;
                        window.current = null;
                        window.setStrokes(window.strokes.concat([done]));
                    }
                }
            }

            // Crop frame with corner handles; outside is dimmed.
            Item {
                id: cropper
                visible: window.tool === "crop"
                anchors.fill: parent
                readonly property real k: page.scale
                readonly property rect r: Qt.rect(window.cropRect.x * k, window.cropRect.y * k,
                                                  window.cropRect.width * k, window.cropRect.height * k)
                Rectangle { x: 0; y: 0; width: parent.width; height: parent.r.y; color: Theme.dim }
                Rectangle { x: 0; y: parent.r.y + parent.r.height; width: parent.width; height: parent.height - y; color: Theme.dim }
                Rectangle { x: 0; y: parent.r.y; width: parent.r.x; height: parent.r.height; color: Theme.dim }
                Rectangle {
                    x: parent.r.x + parent.r.width
                    y: parent.r.y
                    width: parent.width - x
                    height: parent.r.height
                    color: Theme.dim
                }
                Rectangle {
                    x: parent.r.x
                    y: parent.r.y
                    width: parent.r.width
                    height: parent.r.height
                    color: "transparent"
                    border.width: 1
                    border.color: "white"
                }
                Repeater {
                    model: [[0, 0], [1, 0], [0, 1], [1, 1]]
                    delegate: Rectangle {
                        required property var modelData
                        width: 14
                        height: 14
                        radius: 7
                        color: "white"
                        border.color: Theme.accent
                        border.width: 2
                        x: cropper.r.x + modelData[0] * cropper.r.width - width / 2
                        y: cropper.r.y + modelData[1] * cropper.r.height - height / 2
                        MouseArea {
                            anchors.fill: parent
                            anchors.margins: -6
                            cursorShape: (parent.modelData[0] === parent.modelData[1]) ? Qt.SizeFDiagCursor
                                                                                         : Qt.SizeBDiagCursor
                            onPositionChanged: mouse => {
                                if (!pressed) {
                                    return;
                                }
                                const p = mapToItem(cropper, mouse.x, mouse.y);
                                const k = cropper.k;
                                const px = Math.max(0, Math.min(backend.imageWidth, p.x / k));
                                const py = Math.max(0, Math.min(backend.imageHeight, p.y / k));
                                let x1 = window.cropRect.x, y1 = window.cropRect.y;
                                let x2 = x1 + window.cropRect.width, y2 = y1 + window.cropRect.height;
                                if (parent.modelData[0] === 0) { x1 = Math.min(px, x2 - 8); } else { x2 = Math.max(px, x1 + 8); }
                                if (parent.modelData[1] === 0) { y1 = Math.min(py, y2 - 8); } else { y2 = Math.max(py, y1 + 8); }
                                window.cropRect = Qt.rect(x1, y1, x2 - x1, y2 - y1);
                            }
                        }
                    }
                }
            }
        }
    }

    // --- Messages ("Saved to Pictures > Screenshots", "Copied") -------------------
    Rectangle {
        id: infoBar
        visible: backend.message !== ""
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 44
        color: Theme.card
        border.color: Theme.cardBorder
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 8
            spacing: 12
            Text {
                Layout.fillWidth: true
                objectName: "message"
                text: backend.message
                color: Theme.text
                font.pixelSize: Theme.bodySize
                elide: Text.ElideRight
            }
            VButton {
                visible: backend.canShowSaved
                text: backend.texts.show_in_folder
                onClicked: backend.showInFolder()
            }
            BarButton {
                glyph: "close"
                tip: backend.texts.close
                onClicked: backend.dismissMessage()
            }
        }
    }
}
