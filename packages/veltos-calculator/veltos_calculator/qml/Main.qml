/*
    VeltOS Calculator window, in the layout of Windows 11's Calculator:
    the navigation button and the mode name at the top ("Standard",
    "Scientific", with "Keep on top" in Standard), the calculation and the
    number right-aligned below, the memory row (MC MR M+ M− MS M⌄), in
    Scientific DEG / F-E and the Trigonometry and Function flyouts, then
    the keypad. A wide window shows History and Memory beside the keypad;
    a narrow one shows them over the keypad (History button, M⌄).
    `backend` is app.Backend; keys go to it by name (engine.py).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    width: 340
    height: 560
    minimumWidth: 320
    minimumHeight: compact ? 340 : 480
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    property string page: "calc"            // or "settings"
    property bool navOpen: false
    property string sheet: ""               // "history" / "memory" over the keypad (narrow)
    property string panelTab: "history"     // side panel (wide)
    property string flyout: ""              // "trig" / "func"
    property bool second: false             // 2nd
    property bool trigSecond: false         // 2nd in the Trigonometry flyout
    property bool hyperbolic: false         // hyp
    property size fullSize: Qt.size(340, 560)
    property real flyoutY: 0
    readonly property bool compact: backend.keepOnTop
    readonly property bool scientific: backend.mode === "scientific"
    readonly property bool wide: !compact && page === "calc" && width >= 640
    readonly property string point: backend.language === "tr" ? "," : "."

    function press(key) {
        backend.press(key);
    }
    function setMode(mode) {
        backend.setMode(mode);
        page = "calc";
        navOpen = false;
        sheet = "";
        flyout = "";
    }
    function setCompact(on) {
        if (on) {
            fullSize = Qt.size(width, height);
            sheet = "";
            backend.setKeepOnTop(true);
            width = 322;
            height = 400;
        } else {
            backend.setKeepOnTop(false);
            width = fullSize.width;
            height = fullSize.height;
        }
    }
    function toggleSheet(kind) {
        if (wide) {
            panelTab = kind;
        } else {
            sheet = sheet === kind ? "" : kind;
        }
    }
    function trigKey(base) {
        return (trigSecond ? "a" : "") + base + (hyperbolic ? "h" : "");
    }
    function trigLabel(base) {
        return base + (hyperbolic ? "h" : "") + (trigSecond ? "<sup>-1</sup>" : "");
    }

    // Windows Calculator keyboard keys.
    function handleKey(event) {
        const ctrl = event.modifiers & Qt.ControlModifier;
        const alt = event.modifiers & Qt.AltModifier;
        if (event.key === Qt.Key_Escape) {
            if (navOpen) {
                navOpen = false;
            } else if (flyout !== "") {
                flyout = "";
            } else if (sheet !== "") {
                sheet = "";
            } else {
                press("C");
            }
            event.accepted = true;
            return;
        }
        if (page !== "calc") {
            return;
        }
        if (ctrl) {
            const ctrlKeys = {};
            ctrlKeys[Qt.Key_M] = "MS";
            ctrlKeys[Qt.Key_R] = "MR";
            ctrlKeys[Qt.Key_P] = "M+";
            ctrlKeys[Qt.Key_Q] = "M-";
            ctrlKeys[Qt.Key_L] = "MC";
            if (event.key === Qt.Key_C) {
                backend.copy();
            } else if (event.key === Qt.Key_V) {
                backend.paste();
            } else if (event.key === Qt.Key_H) {
                toggleSheet("history");
            } else if (ctrlKeys[event.key] !== undefined) {
                press(ctrlKeys[event.key]);
            } else {
                return;
            }
            event.accepted = true;
            return;
        }
        if (alt) {
            if (event.key === Qt.Key_1) {
                setMode("standard");
                event.accepted = true;
            } else if (event.key === Qt.Key_2) {
                setMode("scientific");
                event.accepted = true;
            }
            return;
        }
        const named = {};
        named[Qt.Key_Return] = "=";
        named[Qt.Key_Enter] = "=";
        named[Qt.Key_Backspace] = "back";
        named[Qt.Key_Delete] = "CE";
        named[Qt.Key_F9] = "negate";
        if (named[event.key] !== undefined) {
            press(named[event.key]);
            event.accepted = true;
            return;
        }
        const t = event.text;
        if (t.length !== 1) {
            return;
        }
        if (t >= "0" && t <= "9") {
            press(t);
            event.accepted = true;
            return;
        }
        const keys = { "+": "+", "-": "-", "*": "*", "/": "/", "=": "=", ".": ".", ",": ".",
                       "%": scientific ? "mod" : "%", "r": "inv", "@": "sqrt", "q": "sqr" };
        const scientificKeys = { "(": "(", ")": ")", "^": "pow", "y": "pow", "!": "fact", "p": "pi",
                                 "s": "sin", "o": "cos", "t": "tan", "l": "log", "n": "ln",
                                 "#": "cube", "x": "exp" };
        const key = keys[t] !== undefined ? keys[t] : (scientific ? scientificKeys[t] : undefined);
        if (key !== undefined) {
            press(key);
            event.accepted = true;
        }
    }

    readonly property var standardKeys: [
        { k: "%", l: "%" }, { k: "CE", l: "CE" }, { k: "C", l: "C" }, { k: "back", g: "back" },
        { k: "inv", l: "<sup>1</sup>/<i>x</i>" }, { k: "sqr", l: "<i>x</i><sup>2</sup>" },
        { k: "sqrt", l: "<sup>2</sup>√<i>x</i>" }, { k: "/", l: "÷", s: 22 },
        { k: "7", n: true }, { k: "8", n: true }, { k: "9", n: true }, { k: "*", l: "×", s: 22 },
        { k: "4", n: true }, { k: "5", n: true }, { k: "6", n: true }, { k: "-", l: "−", s: 22 },
        { k: "1", n: true }, { k: "2", n: true }, { k: "3", n: true }, { k: "+", l: "+", s: 22 },
        { k: "negate", l: "+/−", n: true }, { k: "0", n: true }, { k: ".", l: window.point, n: true },
        { k: "=", l: "=", a: true, s: 22 }
    ]
    // Keys whose meaning changes are resolved per delegate (resolve()), so
    // the keypad is not rebuilt on every key press.
    readonly property var scientificKeys: [
        { k: "2nd", l: "2<sup>nd</sup>", t: true }, { k: "pi", l: "π" }, { k: "e", l: "<i>e</i>" },
        { dyn: "clear" }, { k: "back", g: "back" },
        { k: "sqr", l: "<i>x</i><sup>2</sup>", alt: { k: "cube", l: "<i>x</i><sup>3</sup>" } },
        { k: "inv", l: "<sup>1</sup>/<i>x</i>" }, { k: "abs", l: "|<i>x</i>|" }, { k: "exp", l: "exp" },
        { k: "mod", l: "mod" },
        { k: "sqrt", l: "<sup>2</sup>√<i>x</i>", alt: { k: "cuberoot", l: "<sup>3</sup>√<i>x</i>" } },
        { dyn: "paren" }, { k: ")", l: ")" }, { k: "fact", l: "<i>n</i>!" }, { k: "/", l: "÷", s: 22 },
        { k: "pow", l: "<i>x</i><sup><i>y</i></sup>", alt: { k: "root", l: "<sup><i>y</i></sup>√<i>x</i>" } },
        { k: "7", n: true }, { k: "8", n: true }, { k: "9", n: true }, { k: "*", l: "×", s: 22 },
        { k: "pow10", l: "10<sup><i>x</i></sup>", alt: { k: "pow2", l: "2<sup><i>x</i></sup>" } },
        { k: "4", n: true }, { k: "5", n: true }, { k: "6", n: true }, { k: "-", l: "−", s: 22 },
        { k: "log", l: "log", alt: { k: "logbase", l: "log<sub><i>y</i></sub><i>x</i>" } },
        { k: "1", n: true }, { k: "2", n: true }, { k: "3", n: true }, { k: "+", l: "+", s: 22 },
        { k: "ln", l: "ln", alt: { k: "powe", l: "<i>e</i><sup><i>x</i></sup>" } },
        { k: "negate", l: "+/−", n: true }, { k: "0", n: true }, { k: ".", l: window.point, n: true },
        { k: "=", l: "=", a: true, s: 22 }
    ]

    function resolve(d) {
        if (d.dyn === "clear") {
            return backend.canClearEntry ? { k: "CE", l: "CE" } : { k: "C", l: "C" };
        }
        if (d.dyn === "paren") {
            return { k: "(", l: backend.openParens > 0 ? "(<sub>" + backend.openParens + "</sub>" : "(" };
        }
        return d.alt !== undefined && window.second ? d.alt : d;
    }
    // The compact (keep on top) window: CE, C, backspace and ÷ above the
    // digits, without % and the functions row.
    readonly property var compactKeys: standardKeys.slice(1, 4).concat([standardKeys[7]], standardKeys.slice(8))

    Item {
        id: root
        anchors.fill: parent
        focus: true
        Keys.onPressed: event => window.handleKey(event)

        RowLayout {
            anchors.fill: parent
            spacing: 0

            // ---- the calculator ----------------------------------------------------------------
            Item {
                id: calculator
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    id: column
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 4
                    anchors.bottomMargin: 4
                    spacing: 0

                    // Title row
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 4
                        Layout.preferredHeight: 44
                        spacing: 2
                        FlatButton {
                            objectName: "navButton"
                            visible: !window.compact
                            implicitWidth: 40
                            implicitHeight: 36
                            glyph: "menu"
                            tip: backend.texts.open_navigation
                            onClicked: window.navOpen = true
                        }
                        FlatButton {
                            objectName: "fullViewButton"
                            visible: window.compact
                            implicitWidth: 40
                            implicitHeight: 36
                            glyph: "fullview"
                            tip: backend.texts.back_to_full
                            onClicked: window.setCompact(false)
                        }
                        Text {
                            objectName: "modeTitle"
                            visible: !window.compact
                            Layout.leftMargin: 6
                            text: window.page === "settings" ? backend.texts.settings
                                  : (window.scientific ? backend.texts.scientific : backend.texts.standard)
                            color: Theme.text
                            font.pixelSize: 20
                            font.weight: Font.DemiBold
                        }
                        FlatButton {
                            objectName: "keepOnTopButton"
                            visible: !window.compact && window.page === "calc" && !window.scientific
                            Layout.leftMargin: 4
                            implicitWidth: 36
                            implicitHeight: 32
                            glyph: "keeptop"
                            tip: backend.texts.keep_on_top
                            onClicked: window.setCompact(true)
                        }
                        Item { Layout.fillWidth: true }
                        FlatButton {
                            objectName: "historyButton"
                            visible: window.page === "calc" && !window.wide && !window.compact
                            implicitWidth: 40
                            implicitHeight: 36
                            glyph: "history"
                            on: window.sheet === "history"
                            tip: backend.texts.history
                            onClicked: window.toggleSheet("history")
                        }
                    }

                    // Calculation and number
                    Item {
                        id: displayArea
                        visible: window.page === "calc"
                        Layout.fillWidth: true
                        Layout.preferredHeight: window.compact ? 76 : 104
                        Text {
                            id: expressionText
                            objectName: "expression"
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            anchors.topMargin: window.compact ? 0 : 8
                            height: 20
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideLeft
                            text: backend.expression
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                        }
                        Text {
                            id: displayText
                            objectName: "display"
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: expressionText.bottom
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            horizontalAlignment: Text.AlignRight
                            verticalAlignment: Text.AlignVCenter
                            text: backend.display
                            color: Theme.text
                            font.pixelSize: window.compact ? 40 : 46
                            font.weight: Font.DemiBold
                            fontSizeMode: Text.HorizontalFit
                            minimumPixelSize: 16
                        }
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onClicked: mouse => {
                                contextMenu.x = Math.min(mouse.x, window.width - contextMenu.width - 8);
                                contextMenu.y = mouse.y;
                                contextMenu.open();
                            }
                        }
                        Popup {
                            id: contextMenu
                            padding: 4
                            background: Rectangle {
                                radius: Theme.radius
                                color: Theme.pane
                                border.color: Theme.paneBorder
                            }
                            contentItem: Column {
                                spacing: 2
                                Repeater {
                                    model: [{ label: backend.texts.copy, act: "copy" },
                                            { label: backend.texts.paste, act: "paste" }]
                                    delegate: FlatButton {
                                        required property var modelData
                                        width: 140
                                        label: modelData.label
                                        labelSize: Theme.bodySize
                                        contentItem: Text {
                                            text: parent.label
                                            color: Theme.text
                                            font.pixelSize: Theme.bodySize
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 8
                                        }
                                        onClicked: {
                                            contextMenu.close();
                                            if (modelData.act === "copy") {
                                                backend.copy();
                                            } else {
                                                backend.paste();
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Scientific: angle unit and F-E
                    RowLayout {
                        visible: window.page === "calc" && window.scientific
                        Layout.fillWidth: true
                        spacing: 2
                        FlatButton {
                            objectName: "angleButton"
                            label: backend.angle
                            bold: true
                            implicitWidth: 56
                            onClicked: backend.nextAngle()
                        }
                        FlatButton {
                            objectName: "feButton"
                            label: "F-E"
                            bold: true
                            implicitWidth: 56
                            on: backend.fixedExponent
                            onClicked: backend.toggleFixedExponent()
                        }
                        Item { Layout.fillWidth: true }
                    }

                    // Memory row
                    RowLayout {
                        id: memoryRow
                        visible: window.page === "calc" && !window.compact
                        Layout.fillWidth: true
                        spacing: 0
                        Repeater {
                            model: [{ k: "MC", l: "MC", needs: true }, { k: "MR", l: "MR", needs: true },
                                    { k: "M+", l: "M+" }, { k: "M-", l: "M−" }, { k: "MS", l: "MS" }]
                            delegate: FlatButton {
                                required property var modelData
                                Layout.fillWidth: true
                                label: modelData.l
                                bold: true
                                enabled: !backend.isError && (!modelData.needs || backend.memory.length > 0)
                                onClicked: window.press(modelData.k)
                            }
                        }
                        FlatButton {
                            objectName: "memoryButton"
                            visible: !window.wide
                            Layout.fillWidth: true
                            label: "M"
                            bold: true
                            glyph: "chevron"
                            glyphAfter: true
                            on: window.sheet === "memory"
                            enabled: backend.memory.length > 0 || window.sheet === "memory"
                            tip: backend.texts.memory
                            onClicked: window.toggleSheet("memory")
                        }
                    }

                    // Scientific: Trigonometry and Function flyouts
                    RowLayout {
                        visible: window.page === "calc" && window.scientific
                        Layout.fillWidth: true
                        Layout.topMargin: 2
                        Layout.bottomMargin: 2
                        spacing: 2
                        FlatButton {
                            id: trigButton
                            objectName: "trigButton"
                            label: backend.texts.trigonometry
                            labelSize: Theme.bodySize
                            glyph: "chevron"
                            glyphAfter: true
                            on: window.flyout === "trig"
                            onClicked: {
                                window.flyoutY = mapToItem(calculator, 0, height).y + 4;
                                window.flyout = window.flyout === "trig" ? "" : "trig";
                            }
                        }
                        FlatButton {
                            id: funcButton
                            objectName: "funcButton"
                            label: backend.texts.function
                            labelSize: Theme.bodySize
                            glyph: "chevron"
                            glyphAfter: true
                            on: window.flyout === "func"
                            onClicked: {
                                window.flyoutY = mapToItem(calculator, 0, height).y + 4;
                                window.flyout = window.flyout === "func" ? "" : "func";
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }

                    // Keypad
                    GridLayout {
                        id: keypad
                        objectName: "keypad"
                        visible: window.page === "calc"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.topMargin: 2
                        columns: window.scientific && !window.compact ? 5 : 4
                        rowSpacing: 2
                        columnSpacing: 2
                        uniformCellWidths: true
                        uniformCellHeights: true
                        Repeater {
                            model: window.compact ? window.compactKeys
                                   : (window.scientific ? window.scientificKeys : window.standardKeys)
                            delegate: CalcButton {
                                required property var modelData
                                readonly property var key: window.resolve(modelData)
                                objectName: "key_" + (modelData.dyn !== undefined ? modelData.dyn : modelData.k)
                                kind: key.a ? "accent" : (key.n ? "number" : "operator")
                                label: key.l !== undefined ? key.l : key.k
                                glyph: key.g !== undefined ? key.g : ""
                                labelSize: key.s !== undefined ? key.s : (key.n ? 20 : 16)
                                on: key.t === true && window.second
                                enabled: !backend.isError || ["C", "CE", "back", "="].includes(key.k)
                                         || /^[0-9.]$/.test(key.k)
                                onClicked: {
                                    if (key.k === "2nd") {
                                        window.second = !window.second;
                                    } else {
                                        window.press(key.k);
                                    }
                                }
                            }
                        }
                    }

                    SettingsPage {
                        objectName: "settingsPage"
                        visible: window.page === "settings"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                }

                // History or Memory over the keypad (narrow window)
                MouseArea {
                    visible: window.sheet !== ""
                    anchors.fill: parent
                    onClicked: window.sheet = ""
                }
                Rectangle {
                    objectName: "sheet"
                    visible: window.sheet !== "" && !window.wide
                    anchors.left: parent.left
                    anchors.right: parent.right
                    y: column.y + displayArea.y + displayArea.height
                    height: parent.height - y
                    radius: Theme.radius
                    color: Theme.pane
                    border.color: Theme.paneBorder
                    MouseArea { anchors.fill: parent }       // keep clicks inside
                    Records {
                        anchors.fill: parent
                        anchors.topMargin: 6
                        kind: window.sheet === "memory" ? "memory" : "history"
                        onChosen: window.sheet = ""
                    }
                }

                // Trigonometry / Function flyout
                MouseArea {
                    visible: window.flyout !== ""
                    anchors.fill: parent
                    onClicked: window.flyout = ""
                }
                Rectangle {
                    objectName: "flyout"
                    visible: window.flyout !== ""
                    x: 8
                    y: window.flyoutY
                    width: Math.min(calculator.width - 16, 360)
                    height: flyoutGrid.implicitHeight + 16
                    radius: Theme.radius
                    color: Theme.pane
                    border.color: Theme.paneBorder
                    MouseArea { anchors.fill: parent }
                    GridLayout {
                        id: flyoutGrid
                        anchors.fill: parent
                        anchors.margins: 8
                        columns: window.flyout === "trig" ? 4 : 3
                        rowSpacing: 2
                        columnSpacing: 2
                        uniformCellWidths: true
                        Repeater {
                            model: window.flyout === "trig"
                                   ? [{ k: "2nd", l: "2<sup>nd</sup>" }, { b: "sin" }, { b: "cos" }, { b: "tan" },
                                      { k: "hyp", l: "hyp" }, { b: "sec" }, { b: "csc" }, { b: "cot" }]
                                   : [{ k: "abs", l: "|<i>x</i>|" }, { k: "floor", l: "⌊<i>x</i>⌋" },
                                      { k: "ceil", l: "⌈<i>x</i>⌉" }, { k: "rand", l: "rand" },
                                      { k: "todms", l: "→dms" }, { k: "fromdms", l: "dms" }]
                            delegate: CalcButton {
                                required property var modelData
                                objectName: "flyout_" + (modelData.b !== undefined ? modelData.b : modelData.k)
                                Layout.preferredHeight: 44
                                Layout.fillHeight: false
                                label: modelData.b !== undefined ? window.trigLabel(modelData.b) : modelData.l
                                on: (modelData.k === "2nd" && window.trigSecond) || (modelData.k === "hyp" && window.hyperbolic)
                                onClicked: {
                                    if (modelData.k === "2nd") {
                                        window.trigSecond = !window.trigSecond;
                                    } else if (modelData.k === "hyp") {
                                        window.hyperbolic = !window.hyperbolic;
                                    } else {
                                        window.press(modelData.b !== undefined ? window.trigKey(modelData.b) : modelData.k);
                                        window.flyout = "";
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ---- History and Memory beside the keypad (wide window) -----------------------------
            Rectangle {
                objectName: "sidePanel"
                visible: window.wide
                Layout.preferredWidth: 320
                Layout.fillHeight: true
                color: Theme.window
                Rectangle {
                    anchors.fill: parent
                    anchors.topMargin: 8
                    anchors.rightMargin: 8
                    anchors.bottomMargin: 8
                    radius: Theme.radius
                    color: Theme.pane
                    border.color: Theme.paneBorder

                    Row {
                        id: tabs
                        x: 12
                        y: 8
                        spacing: 4
                        Repeater {
                            model: [{ k: "history", l: backend.texts.history }, { k: "memory", l: backend.texts.memory }]
                            delegate: AbstractButton {
                                id: tab
                                required property var modelData
                                objectName: "tab_" + modelData.k
                                implicitWidth: tabText.implicitWidth + 20
                                implicitHeight: 40
                                hoverEnabled: true
                                focusPolicy: Qt.NoFocus
                                onClicked: window.panelTab = modelData.k
                                background: Item {}
                                contentItem: Item {
                                    Text {
                                        id: tabText
                                        anchors.centerIn: parent
                                        text: tab.modelData.l
                                        color: window.panelTab === tab.modelData.k || tab.hovered ? Theme.text : Theme.subtext
                                        font.pixelSize: Theme.bodySize
                                        font.weight: window.panelTab === tab.modelData.k ? Font.DemiBold : Font.Normal
                                    }
                                    Rectangle {
                                        visible: window.panelTab === tab.modelData.k
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        anchors.bottom: parent.bottom
                                        anchors.bottomMargin: 4
                                        width: 16
                                        height: 3
                                        radius: 1.5
                                        color: Theme.accent
                                    }
                                }
                            }
                        }
                    }
                    Records {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: tabs.bottom
                        anchors.bottom: parent.bottom
                        anchors.topMargin: 4
                        kind: window.panelTab
                    }
                }
            }
        }

        // ---- navigation pane ----------------------------------------------------------------
        Rectangle {
            visible: nav.x > -nav.width
            anchors.fill: parent
            color: Theme.scrim
            opacity: window.navOpen ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 167 } }
            MouseArea {
                anchors.fill: parent
                onClicked: window.navOpen = false
            }
        }
        Rectangle {
            id: nav
            objectName: "navPane"
            width: Math.min(280, window.width - 40)
            height: parent.height
            x: window.navOpen ? 0 : -width - 2
            visible: x > -width - 2
            color: Theme.pane
            border.color: Theme.paneBorder
            Behavior on x { NumberAnimation { duration: 167; easing.type: Easing.OutCubic } }
            MouseArea { anchors.fill: parent }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 2
                FlatButton {
                    Layout.topMargin: 4
                    implicitWidth: 40
                    implicitHeight: 36
                    glyph: "menu"
                    tip: backend.texts.close_navigation
                    onClicked: window.navOpen = false
                }
                Text {
                    Layout.leftMargin: 12
                    Layout.topMargin: 10
                    Layout.bottomMargin: 4
                    text: backend.texts.calculator
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: [{ k: "standard", g: "standard" }, { k: "scientific", g: "scientific" }]
                    delegate: NavItem {
                        required property var modelData
                        objectName: "nav_" + modelData.k
                        Layout.fillWidth: true
                        glyph: modelData.g
                        label: backend.texts[modelData.k]
                        current: window.page === "calc" && backend.mode === modelData.k
                        onClicked: window.setMode(modelData.k)
                    }
                }
                Item { Layout.fillHeight: true }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: Theme.paneBorder
                }
                NavItem {
                    objectName: "nav_settings"
                    Layout.fillWidth: true
                    glyph: "settings"
                    label: backend.texts.settings
                    current: window.page === "settings"
                    onClicked: {
                        window.page = "settings";
                        window.navOpen = false;
                        window.sheet = "";
                        window.flyout = "";
                    }
                }
            }
        }
    }

    component NavItem: AbstractButton {
        id: navItem
        property string glyph: ""
        property string label: ""
        property bool current: false
        implicitHeight: 40
        hoverEnabled: true
        focusPolicy: Qt.NoFocus
        Accessible.name: label
        background: Rectangle {
            radius: Theme.keyRadius
            color: navItem.down ? Theme.pressed
                   : (navItem.current ? Theme.selected : (navItem.hovered ? Theme.hover : "transparent"))
            Rectangle {
                visible: navItem.current
                anchors.verticalCenter: parent.verticalCenter
                width: 3
                height: 16
                radius: 1.5
                color: Theme.accent
            }
        }
        contentItem: Row {
            leftPadding: 12
            spacing: 14
            Glyph {
                anchors.verticalCenter: parent.verticalCenter
                width: 18
                height: 18
                kind: navItem.glyph
                color: Theme.text
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: navItem.label
                color: Theme.text
                font.pixelSize: Theme.bodySize
            }
        }
    }
}
