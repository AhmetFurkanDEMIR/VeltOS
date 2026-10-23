/*
    VeltOS Automatic Repair, in the layout of Windows 11's recovery screens:
    "Automatic Repair" with Restart and Advanced options at the bottom
    right, "Choose an option" with large tiles (Startup Repair, Safe mode,
    Command Prompt, Problem details, Continue, Turn off), the repair's
    progress step by step, and the last start's errors in a terminal-style
    box. Full screen on the console (linuxfb), keyboard and mouse.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Window

Window {
    id: root

    visible: true
    visibility: Window.FullScreen
    color: "#0A1236"
    title: "VeltOS Automatic Repair"

    property string page: "home"          // home, options, repair, details
    property var stepStates: []
    property var stepOutputs: []
    property bool repairDone: false
    property bool repairOk: false
    property string problemText: ""
    // Chosen from the boot menu rather than started after failed starts.
    readonly property bool manual: Qt.application.arguments.indexOf("--manual") >= 0

    readonly property real unit: Math.max(1, Math.min(width / 1280, height / 800))
    readonly property bool inputBlocked: backend.terminalOpen || (backend.busy && page !== "repair")

    function show(name) {
        page = name;
        pageIn.restart();
        Qt.callLater(focusFirst);
    }

    // The keyboard always starts on a button of the page shown. (The
    // finished repair page used to focus the options page's hidden Back
    // button: Enter went to the start page; VM, 2026-10-22.)
    function focusFirst() {
        let first = pages;                     // no button while the repair runs
        if (page === "options")
            first = tiles.itemAt(0);
        else if (page === "home")
            first = homeAdvanced;
        else if (page === "repair" && repairDone)
            first = repairRestart;
        else if (page === "details")
            first = detailsBack;
        if (first)
            first.forceActiveFocus();
    }

    function startRepair() {
        const states = [];
        const outputs = [];
        for (let i = 0; i < backend.steps.length; i++) {
            states.push("waiting");
            outputs.push("");
        }
        stepStates = states;
        stepOutputs = outputs;
        repairDone = false;
        show("repair");
        backend.startRepair();
    }

    Connections {
        target: backend
        function onStepChanged(index, state, output) {
            const states = root.stepStates.slice();
            const outputs = root.stepOutputs.slice();
            states[index] = state;
            outputs[index] = output;
            root.stepStates = states;
            root.stepOutputs = outputs;
        }
        function onRepairFinished(ok) {
            root.repairOk = ok;
            root.repairDone = true;
            Qt.callLater(root.focusFirst);
        }
        function onTerminalOpenChanged() {
            // The console drew over the screen: draw everything again.
            if (!backend.terminalOpen)
                repaint.restart();
        }
    }

    // The VeltOS navy with a soft glow, like the start-up screen.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0A1236" }
            GradientStop { position: 1.0; color: "#13235E" }
        }
    }
    Rectangle {
        width: parent.width * 0.8
        height: width
        radius: width / 2
        x: parent.width * 0.55
        y: -height * 0.35
        opacity: 0.35
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#2F5EE6" }
            GradientStop { position: 1.0; color: "#002F5EE6" }
        }
    }

    // Brand, top left.
    Row {
        x: 48 * root.unit
        y: 36 * root.unit
        spacing: 12 * root.unit
        Image {
            source: backend.logo
            width: 32 * root.unit
            height: width
            sourceSize.width: width * 2
            sourceSize.height: height * 2
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "VeltOS"
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 18 * root.unit
            font.weight: Font.DemiBold
        }
    }

    // ---- Shared pieces ----

    component Heading: Column {
        property string title
        property string body
        spacing: 14 * root.unit
        width: Math.min(root.width * 0.62, 900 * root.unit)
        Text {
            width: parent.width
            text: parent.title
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 40 * root.unit
            font.weight: Font.Light
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width
            visible: text !== ""
            text: parent.body
            color: "#D5DEF8"
            font.family: "Inter"
            font.pixelSize: 18 * root.unit
            lineHeight: 1.3
            wrapMode: Text.WordWrap
        }
    }

    component ActionButton: Rectangle {
        id: action
        property string label
        property bool primary: false
        signal activated()
        implicitWidth: Math.max(180 * root.unit, caption.implicitWidth + 48 * root.unit)
        implicitHeight: 44 * root.unit
        radius: 6 * root.unit
        color: primary ? (mouse.pressed ? "#264DC0" : mouse.containsMouse || activeFocus ? "#4570EC" : "#2F5EE6")
                       : (mouse.pressed ? "#33FFFFFF" : mouse.containsMouse || activeFocus ? "#26FFFFFF" : "#14FFFFFF")
        border.width: activeFocus ? 2 : 1
        border.color: activeFocus ? "#FFFFFF" : (primary ? "transparent" : "#40FFFFFF")
        activeFocusOnTab: true
        Keys.onReturnPressed: activated()
        Keys.onEnterPressed: activated()
        Keys.onSpacePressed: activated()
        Text {
            id: caption
            anchors.centerIn: parent
            text: action.label
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 16 * root.unit
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: action.activated()
        }
    }

    // A white line glyph drawn on a canvas.
    component Glyph: Canvas {
        property string kind
        width: 30 * root.unit
        height: width
        onKindChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d");
            const s = width / 30;
            ctx.reset();
            ctx.scale(s, s);
            ctx.strokeStyle = "#FFFFFF";
            ctx.fillStyle = "#FFFFFF";
            ctx.lineWidth = 2;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";
            ctx.beginPath();
            if (kind === "repair") {            // a wrench
                ctx.arc(19, 11, 6, Math.PI * 0.75, Math.PI * 2.25);
                ctx.moveTo(15, 15);
                ctx.lineTo(6, 24);
            } else if (kind === "safe") {        // a shield
                ctx.moveTo(15, 4);
                ctx.lineTo(24, 8);
                ctx.lineTo(24, 15);
                ctx.quadraticCurveTo(24, 23, 15, 27);
                ctx.quadraticCurveTo(6, 23, 6, 15);
                ctx.lineTo(6, 8);
                ctx.closePath();
            } else if (kind === "terminal") {    // >_ in a window
                ctx.rect(4, 6, 22, 18);
                ctx.moveTo(9, 12);
                ctx.lineTo(13, 15);
                ctx.lineTo(9, 18);
                ctx.moveTo(15, 19);
                ctx.lineTo(21, 19);
            } else if (kind === "details") {     // a page with lines
                ctx.moveTo(8, 4);
                ctx.lineTo(19, 4);
                ctx.lineTo(23, 8);
                ctx.lineTo(23, 26);
                ctx.lineTo(8, 26);
                ctx.closePath();
                ctx.moveTo(12, 13);
                ctx.lineTo(19, 13);
                ctx.moveTo(12, 17);
                ctx.lineTo(19, 17);
                ctx.moveTo(12, 21);
                ctx.lineTo(17, 21);
            } else if (kind === "continue") {    // an arrow
                ctx.moveTo(5, 15);
                ctx.lineTo(24, 15);
                ctx.moveTo(17, 8);
                ctx.lineTo(24, 15);
                ctx.lineTo(17, 22);
            } else if (kind === "off") {         // the power symbol
                ctx.arc(15, 16, 9, -Math.PI * 0.3, Math.PI * 1.3);
                ctx.moveTo(15, 4);
                ctx.lineTo(15, 14);
            } else if (kind === "restart") {     // a circular arrow
                ctx.arc(15, 15, 9, -Math.PI * 0.4, Math.PI * 1.5);
                ctx.moveTo(15, 3);
                ctx.lineTo(19, 6);
                ctx.lineTo(15, 9);
            }
            ctx.stroke();
        }
    }

    component Terminal: Rectangle {
        id: term
        property string content
        radius: 8 * root.unit
        color: "#0C0C0C"
        border.width: 1
        border.color: "#2B2B2B"
        clip: true
        Flickable {
            id: flick
            anchors.fill: parent
            anchors.margins: 14 * root.unit
            contentHeight: body.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            clip: true
            TextEdit {
                id: body
                width: flick.width
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.WrapAnywhere
                textFormat: TextEdit.PlainText
                text: term.content
                color: "#CCCCCC"
                font.family: "Cascadia Mono"
                font.pixelSize: 13 * root.unit
            }
        }
    }

    // ---- Pages ----

    Item {
        id: pages
        anchors.fill: parent
        // The firmware's frame buffer is often only 1024x768 or 800x600
        // (the recovery start has no graphics driver): narrower margins
        // there, so every page fits (VM, 2026-10-22).
        anchors.leftMargin: (root.width < 1000 ? 48 : 96) * root.unit
        anchors.rightMargin: (root.width < 1000 ? 48 : 96) * root.unit
        anchors.topMargin: (root.height < 700 ? 84 : 130) * root.unit
        anchors.bottomMargin: (root.height < 700 ? 40 : 72) * root.unit
        enabled: !root.inputBlocked
        property real shift: 0
        transform: Translate { x: pages.shift }

        // Automatic Repair.
        Item {
            anchors.fill: parent
            visible: root.page === "home"
            Heading {
                title: backend.text(root.manual ? "manual_title" : "title")
                body: backend.text(root.manual ? "manual_body" : "body")
            }
            Row {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                spacing: 12 * root.unit
                ActionButton {
                    id: homeAdvanced
                    label: backend.text("advanced")
                    KeyNavigation.right: homeRestart
                    onActivated: root.show("options")
                }
                ActionButton {
                    id: homeRestart
                    primary: true
                    label: backend.text("restart")
                    KeyNavigation.left: homeAdvanced
                    onActivated: backend.restart()
                }
            }
        }

        // Choose an option.
        Item {
            anchors.fill: parent
            visible: root.page === "options"
            Heading {
                id: optionsHeading
                title: backend.text("choose")
                body: ""
            }
            // Two columns as in Windows' "Advanced options" whenever two
            // tiles fit side by side: in one column the six tiles did not
            // fit on a 1024x768 screen (VM, 2026-10-22).
            Grid {
                id: tileGrid
                objectName: "tileGrid"
                anchors.top: optionsHeading.bottom
                anchors.topMargin: 32 * root.unit
                columns: parent.width >= 700 * root.unit ? 2 : 1
                columnSpacing: 24 * root.unit
                rowSpacing: 16 * root.unit
                readonly property real tileWidth: Math.min(440 * root.unit,
                                                           (parent.width - (columns - 1) * columnSpacing) / columns)
                Repeater {
                    id: tiles
                    model: [
                        { kind: "repair", title: "repair", desc: "repair_desc" },
                        { kind: "safe", title: "safe", desc: "safe_desc" },
                        { kind: "terminal", title: "terminal", desc: "terminal_desc" },
                        { kind: "details", title: "details", desc: "details_desc" },
                        { kind: "continue", title: "continue", desc: "continue_desc" },
                        { kind: "off", title: "off", desc: "off_desc" }
                    ]
                    delegate: Rectangle {
                        id: tile
                        required property var modelData
                        required property int index
                        width: tileGrid.tileWidth
                        height: 84 * root.unit
                        radius: 8 * root.unit
                        color: tileMouse.pressed ? "#33FFFFFF" : (tileMouse.containsMouse || activeFocus ? "#24FFFFFF" : "#12FFFFFF")
                        border.width: activeFocus ? 2 : 1
                        border.color: activeFocus ? "#FFFFFF" : "#26FFFFFF"
                        activeFocusOnTab: true
                        Keys.onReturnPressed: activate()
                        Keys.onEnterPressed: activate()
                        Keys.onSpacePressed: activate()
                        Keys.onDownPressed: focusTile(index + tileGrid.columns)
                        Keys.onUpPressed: focusTile(index - tileGrid.columns)
                        Keys.onRightPressed: focusTile(index + 1)
                        Keys.onLeftPressed: focusTile(index - 1)

                        function focusTile(i) {
                            const other = tiles.itemAt(i);
                            if (other)
                                other.forceActiveFocus();
                        }
                        Behavior on color { ColorAnimation { duration: 100 } }

                        function activate() {
                            switch (modelData.kind) {
                            case "repair": root.startRepair(); break;
                            case "safe": backend.safeMode(); break;
                            case "terminal": backend.openTerminal(); break;
                            case "details": root.problemText = backend.problems(); root.show("details"); break;
                            case "continue": backend.restart(); break;
                            case "off": backend.powerOff(); break;
                            }
                        }

                        Rectangle {
                            id: badge
                            x: 18 * root.unit
                            anchors.verticalCenter: parent.verticalCenter
                            width: 48 * root.unit
                            height: width
                            radius: width / 2
                            color: "#2F5EE6"
                            Glyph {
                                anchors.centerIn: parent
                                kind: tile.modelData.kind
                            }
                        }
                        Column {
                            anchors.left: badge.right
                            anchors.leftMargin: 18 * root.unit
                            anchors.right: parent.right
                            anchors.rightMargin: 16 * root.unit
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 4 * root.unit
                            Text {
                                width: parent.width
                                text: backend.text(tile.modelData.title)
                                color: "#FFFFFF"
                                font.family: "Inter"
                                font.pixelSize: 19 * root.unit
                                elide: Text.ElideRight
                            }
                            Text {
                                width: parent.width
                                text: backend.text(tile.modelData.desc)
                                color: "#C9D4F5"
                                font.family: "Inter"
                                font.pixelSize: 13 * root.unit
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }
                        }
                        MouseArea {
                            id: tileMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: tile.activate()
                        }
                    }
                }
            }
            ActionButton {
                id: backButton
                objectName: "backButton"
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                visible: root.page === "options"
                label: "←  " + backend.text("back")
                onActivated: root.show("home")
            }
        }

        // Startup Repair.
        Item {
            anchors.fill: parent
            visible: root.page === "repair"
            Heading {
                id: repairHeading
                title: !root.repairDone ? backend.text("repairing")
                                        : backend.text(root.repairOk ? "repair_done" : "repair_failed")
                body: !root.repairDone ? backend.text("repairing_body")
                                       : backend.text(root.repairOk ? "repair_done_body" : "repair_failed_body")
            }
            Column {
                id: stepList
                anchors.top: repairHeading.bottom
                anchors.topMargin: 32 * root.unit
                spacing: 12 * root.unit
                Repeater {
                    model: backend.steps
                    delegate: Row {
                        required property string modelData
                        required property int index
                        id: stepRow
                        readonly property string stepState: root.stepStates[index] || "waiting"
                        spacing: 14 * root.unit
                        Item {
                            width: 22 * root.unit
                            height: width
                            // Running: a turning arc; done: a mark.
                            Canvas {
                                anchors.fill: parent
                                visible: stepRow.stepState === "running"
                                onPaint: {
                                    const ctx = getContext("2d");
                                    ctx.reset();
                                    ctx.strokeStyle = "#7FA2FF";
                                    ctx.lineWidth = 2.5;
                                    ctx.lineCap = "round";
                                    ctx.beginPath();
                                    ctx.arc(width / 2, height / 2, width / 2 - 2, 0, Math.PI * 1.3);
                                    ctx.stroke();
                                }
                                RotationAnimation on rotation {
                                    from: 0; to: 360; duration: 1000; loops: Animation.Infinite
                                    running: parent.visible
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                visible: stepRow.stepState !== "running"
                                text: stepRow.stepState === "ok" ? "✓" : (stepRow.stepState === "failed" ? "✕" : "•")
                                color: stepRow.stepState === "ok" ? "#6CCB5F" : (stepRow.stepState === "failed" ? "#FF99A4" : "#8FA3D9")
                                font.pixelSize: 18 * root.unit
                            }
                        }
                        Text {
                            text: modelData
                            color: stepRow.stepState === "waiting" ? "#8FA3D9" : "#FFFFFF"
                            font.family: "Inter"
                            font.pixelSize: 17 * root.unit
                        }
                    }
                }
            }
            Terminal {
                anchors.top: stepList.bottom
                anchors.topMargin: 24 * root.unit
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: repairButtons.top
                anchors.bottomMargin: 20 * root.unit
                visible: root.repairDone && !root.repairOk
                content: {
                    const lines = [];
                    for (let i = 0; i < backend.steps.length; i++) {
                        if (root.stepStates[i] === "failed")
                            lines.push("== " + backend.steps[i] + "\n" + (root.stepOutputs[i] || ""));
                    }
                    return lines.join("\n\n");
                }
            }
            Row {
                id: repairButtons
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                spacing: 12 * root.unit
                visible: root.repairDone
                ActionButton {
                    id: repairAdvanced
                    label: backend.text("advanced")
                    KeyNavigation.right: repairRestart
                    onActivated: root.show("options")
                }
                ActionButton {
                    id: repairRestart
                    primary: true
                    label: backend.text("restart")
                    KeyNavigation.left: repairAdvanced
                    onActivated: backend.restart()
                }
            }
        }

        // Problem details.
        Item {
            anchors.fill: parent
            visible: root.page === "details"
            Heading {
                id: detailsHeading
                title: backend.text("details_title")
                body: root.problemText !== "" ? backend.text("details_body") : backend.text("details_none")
            }
            Terminal {
                anchors.top: detailsHeading.bottom
                anchors.topMargin: 28 * root.unit
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: detailsBack.top
                anchors.bottomMargin: 20 * root.unit
                visible: root.problemText !== ""
                content: root.problemText
            }
            ActionButton {
                id: detailsBack
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                label: "←  " + backend.text("back")
                onActivated: root.show("options")
            }
        }
    }

    NumberAnimation {
        id: pageIn
        target: pages
        property: "shift"
        from: 40 * root.unit
        to: 0
        duration: 280
        easing.type: Easing.OutCubic
    }

    // While the text console is open or a restart is on its way.
    Rectangle {
        anchors.fill: parent
        visible: root.inputBlocked
        color: "#CC0A1236"
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
        }
        Text {
            anchors.centerIn: parent
            width: parent.width * 0.6
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: backend.terminalOpen ? backend.text("terminal_open") : backend.text("working")
            color: "#FFFFFF"
            font.family: "Inter"
            font.pixelSize: 22 * root.unit
        }
    }

    // A full-screen change forces every pixel to be drawn again.
    Rectangle {
        id: flash
        anchors.fill: parent
        color: "#0A1236"
        opacity: 0
    }
    SequentialAnimation {
        id: repaint
        PropertyAction { target: flash; property: "opacity"; value: 0.01 }
        PauseAnimation { duration: 50 }
        PropertyAction { target: flash; property: "opacity"; value: 0 }
    }

    Component.onCompleted: {
        // Started by hand from the boot menu (not after failed starts):
        // straight to the options, as Windows' "Troubleshoot". Back from
        // Command Prompt (run-recovery): the options again.
        if (root.manual || Qt.application.arguments.indexOf("--options") >= 0)
            page = "options";
        Qt.callLater(focusFirst);
    }
}
