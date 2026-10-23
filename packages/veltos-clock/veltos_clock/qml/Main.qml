/*
    VeltOS Clock in the layout of Windows 11's Clock app: a navigation
    pane (Focus sessions, Timer, Alarm, Stopwatch, World clock) and one
    page at a time. `backend` (app.py) keeps alarms, timers and clocks;
    the stopwatch runs here.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window

    property string page: backend.startPage
    property int tickCount: 0

    width: 980
    height: 680
    minimumWidth: 640
    minimumHeight: 480
    visible: true
    title: backend.text("app_title")
    color: theme.window

    Connections {
        target: backend
        function onTick() { window.tickCount += 1; }
        function onMessage(summary, body) { toast.show(summary, body); }
    }

    // --- Colours and sizes (Windows 11 proportions, VeltOS palette) ------------------
    QtObject {
        id: theme
        readonly property bool dark: backend.darkMode
        readonly property real scale: backend.textScale
        readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
        readonly property color pane: dark ? "#1C1D26" : "#F3F5FA"
        readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
        readonly property color cardHover: dark ? "#323544" : "#F8F9FD"
        readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
        readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
        readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
        readonly property color accent: backend.accent !== "" ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                                              : (dark ? "#6E95FF" : "#2F5EE6")
        readonly property color navSelected: dark ? "#2C2F3D" : "#E4E8F3"
        readonly property color navHover: dark ? "#262835" : "#EBEEF6"
        readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
        readonly property color fieldBorder: dark ? "#4A4D5E" : "#8A90A2"
        readonly property color track: dark ? "#3A3D4E" : "#E1E5EE"
        readonly property color danger: dark ? "#FF99A4" : "#C42B1C"
        readonly property int radius: 8
        readonly property int titleSize: Math.round(28 * scale)
        readonly property int bodySize: Math.round(14 * scale)
        readonly property int captionSize: Math.round(12 * scale)
        readonly property int bigSize: Math.round(44 * scale)
    }

    // --- Shared controls --------------------------------------------------------------
    component VButton: Rectangle {
        id: button
        property string text
        property string icon
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        implicitWidth: Math.max(96, buttonRow.implicitWidth + 32)
        implicitHeight: 34
        radius: 5
        opacity: enabledState ? 1 : 0.5
        color: primary ? (buttonHover.hovered ? Qt.lighter(theme.accent, 1.08) : theme.accent)
                       : (buttonHover.hovered ? theme.cardHover : theme.card)
        border.width: primary ? 0 : 1
        border.color: theme.cardBorder
        Accessible.role: Accessible.Button
        Accessible.name: text
        RowLayout {
            id: buttonRow
            anchors.centerIn: parent
            spacing: 8
            Kirigami.Icon {
                visible: button.icon !== ""
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                source: button.icon
                color: button.primary ? "#FFFFFF" : theme.text
                isMask: true
            }
            Text {
                visible: button.text !== ""
                text: button.text
                color: button.primary ? "#FFFFFF" : theme.text
                font.pixelSize: theme.bodySize
            }
        }
        HoverHandler { id: buttonHover; enabled: button.enabledState }
        TapHandler { enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    component CircleButton: Rectangle {
        id: round
        property string icon
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        implicitWidth: 48
        implicitHeight: 48
        radius: 24
        opacity: enabledState ? 1 : 0.5
        color: primary ? (roundHover.hovered ? Qt.lighter(theme.accent, 1.08) : theme.accent)
                       : (roundHover.hovered ? theme.cardHover : theme.card)
        border.width: primary ? 0 : 1
        border.color: theme.cardBorder
        Accessible.role: Accessible.Button
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 20
            height: 20
            source: round.icon
            color: round.primary ? "#FFFFFF" : theme.text
            isMask: true
        }
        HoverHandler { id: roundHover; enabled: round.enabledState }
        TapHandler { enabled: round.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: round.clicked() }
    }

    component Toggle: Rectangle {
        id: toggle
        property bool checked: false
        signal toggled(bool on)
        implicitWidth: 44
        implicitHeight: 22
        radius: 11
        color: checked ? theme.accent : "transparent"
        border.width: checked ? 0 : 1
        border.color: theme.fieldBorder
        Accessible.role: Accessible.CheckBox
        Accessible.checked: checked
        Rectangle {
            x: toggle.checked ? parent.width - width - 4 : 4
            anchors.verticalCenter: parent.verticalCenter
            width: 14
            height: 14
            radius: 7
            color: toggle.checked ? "#FFFFFF" : theme.subtext
            Behavior on x { NumberAnimation { duration: 120 } }
        }
        TapHandler { onTapped: toggle.toggled(!toggle.checked) }
    }

    component Field: Rectangle {
        id: field
        property alias text: input.text
        property string placeholder
        function focusInput() { input.forceActiveFocus(); }
        implicitHeight: 34
        radius: 4
        color: theme.field
        border.width: 1
        border.color: input.activeFocus ? theme.accent : theme.fieldBorder
        TextInput {
            id: input
            // Like a Windows text box: in the Tab order, the text cursor over it and
            // (in a layout) the full height of its box. A plain TextInput has neither.
            activeFocusOnTab: true
            HoverHandler { cursorShape: Qt.IBeamCursor }
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: TextInput.AlignVCenter
            color: theme.text
            selectionColor: theme.accent
            selectedTextColor: "#FFFFFF"
            font.pixelSize: theme.bodySize
            clip: true
            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: input.text === "" && !input.activeFocus
                text: field.placeholder
                color: theme.subtext
                font.pixelSize: theme.bodySize
            }
        }
    }

    // A number with up/down arrows, as in Windows' time pickers.
    component Stepper: ColumnLayout {
        id: stepper
        property int value: 0
        property int from: 0
        property int to: 59
        property string label
        property bool pad: true
        spacing: 2
        function step(delta) {
            const span = to - from + 1;
            value = from + (((value - from + delta) % span) + span) % span;
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: stepper.label
            color: theme.subtext
            font.pixelSize: theme.captionSize
        }
        CircleButton { Layout.alignment: Qt.AlignHCenter; implicitWidth: 36; implicitHeight: 32; icon: "arrow-up"; onClicked: stepper.step(1) }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: stepper.pad ? String(stepper.value).padStart(2, "0") : String(stepper.value)
            color: theme.text
            font.pixelSize: Math.round(32 * theme.scale)
            font.weight: Font.DemiBold
        }
        CircleButton { Layout.alignment: Qt.AlignHCenter; implicitWidth: 36; implicitHeight: 32; icon: "arrow-down"; onClicked: stepper.step(-1) }
        WheelHandler { onWheel: event => stepper.step(event.angleDelta.y > 0 ? 1 : -1) }
    }

    component PageTitle: Text {
        Layout.fillWidth: true
        color: theme.text
        font.pixelSize: theme.titleSize
        font.weight: Font.DemiBold
    }

    component AddButton: CircleButton {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        implicitWidth: 56
        implicitHeight: 56
        radius: 28
        primary: true
        icon: "list-add"
        Accessible.name: backend.text("add_alarm")
    }

    // --- Window -----------------------------------------------------------------------
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Navigation pane (a layout inside a layout fills the width by
        // default: it took the whole window and the page got 3 px).
        ColumnLayout {
            Layout.preferredWidth: 220
            Layout.maximumWidth: 220
            Layout.fillWidth: false
            Layout.fillHeight: true
            Layout.topMargin: 16
            Layout.leftMargin: 8
            spacing: 2
            Repeater {
                model: [["focus", "focus", "chronometer"], ["timer", "timer", "chronometer"],
                        ["alarm", "alarm", "notifications"], ["stopwatch", "stopwatch", "media-playback-start"],
                        ["world", "world", "globe"]]
                delegate: Rectangle {
                    id: navItem
                    required property var modelData
                    readonly property bool current: window.page === modelData[0]
                    Layout.fillWidth: true
                    implicitHeight: 38
                    radius: 6
                    color: current ? theme.navSelected : (navHover.hovered ? theme.navHover : "transparent")
                    Accessible.role: Accessible.Button
                    Accessible.name: backend.text(modelData[1])
                    Rectangle {
                        visible: navItem.current
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: 3
                        height: 16
                        radius: 1.5
                        color: theme.accent
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        spacing: 12
                        Kirigami.Icon {
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 18
                            source: navItem.modelData[2]
                            color: theme.text
                            isMask: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: backend.text(navItem.modelData[1])
                            color: theme.text
                            font.pixelSize: theme.bodySize
                            elide: Text.ElideRight
                        }
                    }
                    HoverHandler { id: navHover }
                    TapHandler { onTapped: window.page = navItem.modelData[0] }
                }
            }
            Item { Layout.fillHeight: true }
        }

        // Pages
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Loader {
                anchors.fill: parent
                anchors.margins: 28
                sourceComponent: window.page === "alarm" ? alarmPage : window.page === "timer" ? timerPage
                                 : window.page === "stopwatch" ? stopwatchPage : window.page === "world" ? worldPage
                                 : focusPage
            }
        }
    }

    // --- Alarm ------------------------------------------------------------------------
    Component {
        id: alarmPage
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 16
                PageTitle { text: backend.text("alarm") }
                Text {
                    visible: backend.alarms.length === 0
                    text: backend.text("no_alarms")
                    color: theme.subtext
                    font.pixelSize: theme.bodySize
                }
                GridView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    cellWidth: Math.max(260, Math.floor(width / Math.max(1, Math.floor(width / 300))))
                    cellHeight: 150
                    model: backend.alarms
                    delegate: Item {
                        id: alarmCell
                        required property var modelData
                        width: GridView.view.cellWidth
                        height: GridView.view.cellHeight
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 8
                            radius: theme.radius
                            color: alarmHover.hovered ? theme.cardHover : theme.card
                            border.width: 1
                            border.color: theme.cardBorder
                            opacity: alarmCell.modelData.enabled ? 1 : 0.7
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 2
                                Text {
                                    text: alarmCell.modelData.clockText
                                    color: theme.text
                                    font.pixelSize: theme.bigSize
                                    font.weight: Font.Light
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: alarmCell.modelData.name || backend.text("alarm")
                                    color: theme.text
                                    font.pixelSize: theme.bodySize
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: alarmCell.modelData.repeatText + " · " + alarmCell.modelData.ringsIn
                                    color: theme.subtext
                                    font.pixelSize: theme.captionSize
                                    elide: Text.ElideRight
                                }
                            }
                            Toggle {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 16
                                checked: alarmCell.modelData.enabled
                                onToggled: on => backend.enableAlarm(alarmCell.modelData.id, on)
                            }
                            HoverHandler { id: alarmHover }
                            TapHandler { onTapped: alarmEditor.edit(alarmCell.modelData) }
                        }
                    }
                }
            }
            AddButton { onClicked: alarmEditor.edit(null) }
        }
    }

    // --- Timer ------------------------------------------------------------------------
    Component {
        id: timerPage
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 16
                PageTitle { text: backend.text("timer") }
                Text {
                    visible: backend.timers.length === 0
                    text: backend.text("no_timers")
                    color: theme.subtext
                    font.pixelSize: theme.bodySize
                }
                GridView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    cellWidth: Math.max(280, Math.floor(width / Math.max(1, Math.floor(width / 320))))
                    cellHeight: 210
                    model: backend.timers
                    delegate: Item {
                        id: timerCell
                        required property var modelData
                        readonly property real secondsLeft: window.tickCount >= 0 ? backend.timerLeft(modelData.id) : 0
                        readonly property bool running: modelData.state === "running"
                        width: GridView.view.cellWidth
                        height: GridView.view.cellHeight
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 8
                            radius: theme.radius
                            color: theme.card
                            border.width: 1
                            border.color: theme.cardBorder
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 16
                                // Progress ring, as in Windows' timer cards.
                                Item {
                                    Layout.preferredWidth: 120
                                    Layout.preferredHeight: 120
                                    Canvas {
                                        id: ring
                                        anchors.fill: parent
                                        readonly property real fraction: timerCell.modelData.seconds > 0
                                                                         ? timerCell.secondsLeft / timerCell.modelData.seconds : 0
                                        onFractionChanged: requestPaint()
                                        onPaint: {
                                            const ctx = getContext("2d");
                                            ctx.reset();
                                            const c = width / 2, r = c - 5;
                                            ctx.lineWidth = 5;
                                            ctx.strokeStyle = theme.track;
                                            ctx.beginPath();
                                            ctx.arc(c, c, r, 0, 2 * Math.PI);
                                            ctx.stroke();
                                            ctx.strokeStyle = theme.accent;
                                            ctx.lineCap = "round";
                                            ctx.beginPath();
                                            ctx.arc(c, c, r, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * fraction);
                                            ctx.stroke();
                                        }
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        text: backend.durationText(timerCell.secondsLeft)
                                        color: theme.text
                                        font.pixelSize: Math.round(22 * theme.scale)
                                        font.weight: Font.DemiBold
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Text {
                                        Layout.fillWidth: true
                                        text: timerCell.modelData.name || backend.text("timer")
                                        color: theme.text
                                        font.pixelSize: theme.bodySize
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: backend.durationText(timerCell.modelData.seconds)
                                        color: theme.subtext
                                        font.pixelSize: theme.captionSize
                                    }
                                    RowLayout {
                                        spacing: 8
                                        CircleButton {
                                            primary: true
                                            icon: timerCell.running ? "media-playback-pause" : "media-playback-start"
                                            onClicked: backend.timerAction(timerCell.modelData.id, timerCell.running ? "pause" : "start")
                                        }
                                        CircleButton { icon: "view-refresh"; onClicked: backend.timerAction(timerCell.modelData.id, "reset") }
                                        CircleButton { icon: "edit-delete"; onClicked: backend.timerAction(timerCell.modelData.id, "delete") }
                                    }
                                }
                            }
                            TapHandler { acceptedButtons: Qt.RightButton; onTapped: timerEditor.edit(timerCell.modelData) }
                        }
                    }
                }
            }
            AddButton { onClicked: timerEditor.edit(null) }
        }
    }

    // --- Stopwatch --------------------------------------------------------------------
    property real stopwatchStart: 0
    property real stopwatchBase: 0
    property bool stopwatchRunning: false
    property var laps: []
    readonly property real stopwatchElapsed: stopwatchBase + (stopwatchRunning ? (Date.now() - stopwatchStart) / 1000 : 0)
    Timer { interval: 33; repeat: true; running: window.stopwatchRunning; onTriggered: window.stopwatchTick += 1 }
    property int stopwatchTick: 0
    function stopwatchText(seconds) {
        const total = Math.max(0, seconds);
        const h = Math.floor(total / 3600), m = Math.floor(total % 3600 / 60), s = Math.floor(total % 60);
        const cs = Math.floor((total - Math.floor(total)) * 100);
        return (h > 0 ? h + ":" : "") + String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0") + "."
               + String(cs).padStart(2, "0");
    }

    Component {
        id: stopwatchPage
        ColumnLayout {
            spacing: 16
            PageTitle { text: backend.text("stopwatch") }
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 24
                text: window.stopwatchTick >= 0 ? window.stopwatchText(window.stopwatchElapsed) : ""
                color: theme.text
                font.pixelSize: Math.round(72 * theme.scale)
                font.weight: Font.Light
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 12
                CircleButton {
                    implicitWidth: 64
                    implicitHeight: 64
                    radius: 32
                    primary: true
                    icon: window.stopwatchRunning ? "media-playback-pause" : "media-playback-start"
                    onClicked: {
                        if (window.stopwatchRunning) {
                            window.stopwatchBase = window.stopwatchElapsed;
                            window.stopwatchRunning = false;
                        } else {
                            window.stopwatchStart = Date.now();
                            window.stopwatchRunning = true;
                        }
                    }
                }
                CircleButton {
                    icon: "flag"
                    enabledState: window.stopwatchRunning
                    Accessible.name: backend.text("lap")
                    onClicked: {
                        const total = window.stopwatchElapsed;
                        const previous = window.laps.length > 0 ? window.laps[0].total : 0;
                        window.laps = [{ number: window.laps.length + 1, lap: total - previous, total: total }].concat(window.laps);
                    }
                }
                CircleButton {
                    icon: "view-refresh"
                    enabledState: window.stopwatchElapsed > 0
                    Accessible.name: backend.text("reset")
                    onClicked: {
                        window.stopwatchRunning = false;
                        window.stopwatchBase = 0;
                        window.laps = [];
                    }
                }
            }
            Rectangle {
                visible: window.laps.length > 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.topMargin: 16
                radius: theme.radius
                color: theme.card
                border.width: 1
                border.color: theme.cardBorder
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 4
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.preferredWidth: 80; text: backend.text("laps"); color: theme.subtext; font.pixelSize: theme.captionSize }
                        Text { Layout.fillWidth: true; text: backend.text("lap_time"); color: theme.subtext; font.pixelSize: theme.captionSize }
                        Text { Layout.preferredWidth: 140; text: backend.text("total"); color: theme.subtext; font.pixelSize: theme.captionSize }
                    }
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: window.laps
                        delegate: RowLayout {
                            required property var modelData
                            width: ListView.view.width
                            height: 30
                            Text { Layout.preferredWidth: 80; text: modelData.number; color: theme.text; font.pixelSize: theme.bodySize }
                            Text { Layout.fillWidth: true; text: window.stopwatchText(modelData.lap); color: theme.text; font.pixelSize: theme.bodySize }
                            Text { Layout.preferredWidth: 140; text: window.stopwatchText(modelData.total); color: theme.text; font.pixelSize: theme.bodySize }
                        }
                    }
                }
            }
            Item { Layout.fillHeight: true; visible: window.laps.length === 0 }
        }
    }

    // --- World clock ------------------------------------------------------------------
    Component {
        id: worldPage
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 16
                PageTitle { text: backend.text("world") }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 96
                    radius: theme.radius
                    color: theme.card
                    border.width: 1
                    border.color: theme.cardBorder
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text { text: backend.text("local_time"); color: theme.subtext; font.pixelSize: theme.captionSize }
                            Text { text: backend.localDate; color: theme.text; font.pixelSize: theme.bodySize }
                        }
                        Text { text: backend.localTime; color: theme.text; font.pixelSize: theme.bigSize; font.weight: Font.Light }
                    }
                }
                Text {
                    visible: backend.clocks.length === 0
                    text: backend.text("no_clocks")
                    color: theme.subtext
                    font.pixelSize: theme.bodySize
                }
                GridView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    cellWidth: Math.max(260, Math.floor(width / Math.max(1, Math.floor(width / 300))))
                    cellHeight: 120
                    model: backend.clockTimes(String(window.tickCount))
                    delegate: Item {
                        id: clockCell
                        required property var modelData
                        width: GridView.view.cellWidth
                        height: GridView.view.cellHeight
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 8
                            radius: theme.radius
                            color: clockHover.hovered ? theme.cardHover : theme.card
                            border.width: 1
                            border.color: theme.cardBorder
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 2
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        Layout.fillWidth: true
                                        text: clockCell.modelData.city
                                        color: theme.text
                                        font.pixelSize: theme.bodySize
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Text { text: clockCell.modelData.time; color: theme.text; font.pixelSize: Math.round(26 * theme.scale); font.weight: Font.Light }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: clockCell.modelData.offset + (clockCell.modelData.day ? " · " + clockCell.modelData.day : "")
                                    color: theme.subtext
                                    font.pixelSize: theme.captionSize
                                    elide: Text.ElideRight
                                }
                            }
                            CircleButton {
                                visible: clockHover.hovered
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                anchors.margins: 8
                                implicitWidth: 32
                                implicitHeight: 32
                                radius: 16
                                icon: "edit-delete"
                                onClicked: backend.removeClock(clockCell.modelData.zone)
                            }
                            HoverHandler { id: clockHover }
                        }
                    }
                }
            }
            AddButton { onClicked: cityPicker.open() }
        }
    }

    // --- Focus sessions ---------------------------------------------------------------
    Component {
        id: focusPage
        ColumnLayout {
            spacing: 16
            PageTitle { text: backend.text("focus") }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 520
                Layout.maximumWidth: 560
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 24
                implicitHeight: focusColumn.implicitHeight + 48
                radius: theme.radius
                color: theme.card
                border.width: 1
                border.color: theme.cardBorder
                ColumnLayout {
                    id: focusColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 24
                    spacing: 14
                    Text {
                        Layout.fillWidth: true
                        text: backend.focusRunning ? backend.text("focus_running") : backend.text("focus_title")
                        color: theme.text
                        font.pixelSize: Math.round(20 * theme.scale)
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Text {
                        visible: !backend.focusRunning
                        Layout.fillWidth: true
                        text: backend.text("focus_desc")
                        color: theme.subtext
                        font.pixelSize: theme.bodySize
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Text {
                        visible: backend.focusRunning
                        Layout.alignment: Qt.AlignHCenter
                        text: backend.durationText(backend.focusLeft)
                        color: theme.text
                        font.pixelSize: Math.round(64 * theme.scale)
                        font.weight: Font.Light
                    }
                    RowLayout {
                        visible: !backend.focusRunning
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 16
                        Text { text: backend.text("session_length"); color: theme.text; font.pixelSize: theme.bodySize }
                        CircleButton { implicitWidth: 36; implicitHeight: 36; radius: 18; icon: "list-remove"; onClicked: backend.setFocusMinutes(backend.focusMinutes - 5) }
                        Text { text: backend.focusMinutes + " min"; color: theme.text; font.pixelSize: Math.round(20 * theme.scale); font.weight: Font.DemiBold }
                        CircleButton { implicitWidth: 36; implicitHeight: 36; radius: 18; icon: "list-add"; onClicked: backend.setFocusMinutes(backend.focusMinutes + 5) }
                    }
                    VButton {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 8
                        primary: !backend.focusRunning
                        text: backend.focusRunning ? backend.text("end_focus") : backend.text("start_focus")
                        onClicked: backend.focusRunning ? backend.endFocus() : backend.startFocus()
                    }
                }
            }
            Item { Layout.fillHeight: true }
        }
    }

    // --- Dialogs ----------------------------------------------------------------------
    component DialogFrame: Popup {
        id: frame
        property string title
        default property alias content: body.data
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 40)
        modal: true
        padding: 0
        closePolicy: Popup.CloseOnEscape
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, theme.dark ? 0.45 : 0.3) }
        background: Rectangle { radius: 8; color: theme.card; border.width: 1; border.color: theme.cardBorder }
        contentItem: ColumnLayout {
            spacing: 0
            Text {
                Layout.fillWidth: true
                Layout.margins: 24
                Layout.bottomMargin: 12
                text: frame.title
                color: theme.text
                font.pixelSize: Math.round(20 * theme.scale)
                font.weight: Font.DemiBold
            }
            ColumnLayout {
                id: body
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.bottomMargin: 24
                spacing: 12
            }
        }
    }

    DialogFrame {
        id: alarmEditor
        property string alarmId: ""
        property var days: []
        title: alarmId === "" ? backend.text("add_alarm") : backend.text("edit_alarm")
        function edit(alarm) {
            alarmId = alarm ? alarm.id : "";
            hourStep.value = alarm ? parseInt(alarm.time.split(":")[0]) : 7;
            minuteStep.value = alarm ? parseInt(alarm.time.split(":")[1]) : 0;
            alarmName.text = alarm ? alarm.name : "";
            days = alarm ? alarm.days.slice() : [];
            snoozeIndex = alarm ? Math.max(0, snoozeChoices.indexOf(alarm.snooze)) : 1;
            open();
        }
        readonly property var snoozeChoices: [5, 10, 15, 20, 30, 60]
        property int snoozeIndex: 1
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 24
            Stepper { id: hourStep; from: 0; to: 23; label: backend.text("hours") }
            Text { text: ":"; color: theme.text; font.pixelSize: Math.round(32 * theme.scale) }
            Stepper { id: minuteStep; from: 0; to: 59; label: backend.text("minutes") }
        }
        Field { id: alarmName; Layout.fillWidth: true; placeholder: backend.text("alarm_name") }
        Text { text: backend.text("repeat"); color: theme.subtext; font.pixelSize: theme.captionSize }
        RowLayout {
            spacing: 6
            Repeater {
                model: backend.text("app_title") === "Saat" ? ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]
                                                            : ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                delegate: Rectangle {
                    id: dayChip
                    required property int index
                    required property string modelData
                    readonly property bool on: alarmEditor.days.indexOf(index) >= 0
                    implicitWidth: 40
                    implicitHeight: 32
                    radius: 16
                    color: on ? theme.accent : theme.field
                    border.width: on ? 0 : 1
                    border.color: theme.fieldBorder
                    Text { anchors.centerIn: parent; text: dayChip.modelData; color: dayChip.on ? "#FFFFFF" : theme.text; font.pixelSize: theme.captionSize }
                    TapHandler {
                        onTapped: {
                            const days = alarmEditor.days.slice();
                            const at = days.indexOf(dayChip.index);
                            if (at >= 0) days.splice(at, 1); else days.push(dayChip.index);
                            alarmEditor.days = days;
                        }
                    }
                }
            }
        }
        RowLayout {
            Text { text: backend.text("snooze_time"); color: theme.subtext; font.pixelSize: theme.captionSize }
            VButton {
                text: backend.format("minutes_short", "n", String(alarmEditor.snoozeChoices[alarmEditor.snoozeIndex]))
                onClicked: alarmEditor.snoozeIndex = (alarmEditor.snoozeIndex + 1) % alarmEditor.snoozeChoices.length
            }
        }
        RowLayout {
            Layout.topMargin: 8
            spacing: 8
            VButton {
                visible: alarmEditor.alarmId !== ""
                text: backend.text("delete")
                onClicked: { backend.deleteAlarm(alarmEditor.alarmId); alarmEditor.close(); }
            }
            Item { Layout.fillWidth: true }
            VButton {
                primary: true
                text: backend.text("save")
                onClicked: {
                    const hhmm = String(hourStep.value).padStart(2, "0") + ":" + String(minuteStep.value).padStart(2, "0");
                    backend.saveAlarm(alarmEditor.alarmId, hhmm, alarmName.text, alarmEditor.days,
                                      alarmEditor.snoozeChoices[alarmEditor.snoozeIndex]);
                    alarmEditor.close();
                }
            }
            VButton { text: backend.text("cancel"); onClicked: alarmEditor.close() }
        }
    }

    DialogFrame {
        id: timerEditor
        property string timerId: ""
        title: timerId === "" ? backend.text("add_timer") : backend.text("edit_timer")
        function edit(timer) {
            timerId = timer ? timer.id : "";
            const total = timer ? timer.seconds : 600;
            tHours.value = Math.floor(total / 3600);
            tMinutes.value = Math.floor(total % 3600 / 60);
            tSeconds.value = total % 60;
            timerName.text = timer ? timer.name : "";
            open();
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 20
            Stepper { id: tHours; from: 0; to: 99; label: backend.text("hours") }
            Stepper { id: tMinutes; from: 0; to: 59; label: backend.text("minutes") }
            Stepper { id: tSeconds; from: 0; to: 59; label: backend.text("seconds") }
        }
        Field { id: timerName; Layout.fillWidth: true; placeholder: backend.text("timer_name") }
        RowLayout {
            Layout.topMargin: 8
            spacing: 8
            Item { Layout.fillWidth: true }
            VButton {
                primary: true
                text: backend.text("save")
                enabledState: tHours.value + tMinutes.value + tSeconds.value > 0
                onClicked: {
                    backend.saveTimer(timerEditor.timerId, tHours.value * 3600 + tMinutes.value * 60 + tSeconds.value, timerName.text);
                    timerEditor.close();
                }
            }
            VButton { text: backend.text("cancel"); onClicked: timerEditor.close() }
        }
    }

    DialogFrame {
        id: cityPicker
        title: backend.text("add_clock")
        onOpened: { cityField.text = ""; cityField.focusInput(); }
        Field { id: cityField; Layout.fillWidth: true; placeholder: backend.text("search_city"); onTextChanged: citySearch.text = text }
        Item { id: citySearch; property string text: "" }
        ListView {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(240, count * 40)
            clip: true
            model: backend.searchZones(citySearch.text)
            delegate: Rectangle {
                id: zoneRow
                required property var modelData
                width: ListView.view.width
                height: 40
                radius: 6
                color: zoneHover.hovered ? theme.cardHover : "transparent"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    Text { Layout.fillWidth: true; text: zoneRow.modelData.city; color: theme.text; font.pixelSize: theme.bodySize; elide: Text.ElideRight }
                    Text { text: zoneRow.modelData.region; color: theme.subtext; font.pixelSize: theme.captionSize }
                }
                HoverHandler { id: zoneHover }
                TapHandler { onTapped: { backend.addClock(zoneRow.modelData.zone); cityPicker.close(); } }
            }
        }
        RowLayout {
            Item { Layout.fillWidth: true }
            VButton { text: backend.text("cancel"); onClicked: cityPicker.close() }
        }
    }

    // In-window notice (the focus session ended).
    Rectangle {
        id: toast
        property string summary
        property string body
        function show(summary, body) { toast.summary = summary; toast.body = body; toast.opacity = 1; toastTimer.restart(); }
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: 360
        height: 64
        radius: theme.radius
        color: theme.card
        border.width: 1
        border.color: theme.cardBorder
        opacity: 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        Timer { id: toastTimer; interval: 6000; onTriggered: toast.opacity = 0 }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 2
            Text { text: toast.summary; color: theme.text; font.pixelSize: theme.bodySize; font.weight: Font.DemiBold }
            Text { text: toast.body; color: theme.subtext; font.pixelSize: theme.captionSize }
        }
    }
}
