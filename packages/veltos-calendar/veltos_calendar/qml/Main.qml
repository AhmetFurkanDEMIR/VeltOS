/*
    VeltOS Calendar in the layout of Windows 11's Calendar app: "New
    event", a small month and the calendars on the left; "Today", the
    arrows, the month and Day / Work week / Week / Month / Year above the
    calendar. Clicking a free time or a day opens the quick "New event"
    card; an event opens its card (Edit, Delete); "More details" is the
    full editor. `backend` is app.Backend.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: window

    // The event being edited in the full editor (a form from the backend), or null.
    property var editing: null
    readonly property bool wide: width >= 940

    width: 1180
    height: 760
    minimumWidth: 760
    minimumHeight: 540
    visible: true
    title: backend.tr("app_title")
    color: theme.window

    // --- Colours and sizes (Windows 11 proportions, VeltOS palette) -------------------
    QtObject {
        id: theme
        readonly property bool dark: backend.darkMode
        readonly property real scale: backend.textScale
        readonly property color window: dark ? "#1C1D26" : "#F3F5FA"
        readonly property color card: dark ? "#2A2C38" : "#FFFFFF"
        readonly property color cardHover: dark ? "#323544" : "#F5F7FC"
        readonly property color cardBorder: dark ? "#363949" : "#E3E6EE"
        readonly property color grid: dark ? "#363949" : "#E6E9F0"
        readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
        readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
        readonly property color faint: dark ? "#6E7386" : "#A2A8B8"
        readonly property color accent: backend.accent !== "" ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                                              : (dark ? "#6E95FF" : "#2F5EE6")
        readonly property color accentSoft: Qt.alpha(accent, dark ? 0.28 : 0.14)
        readonly property color navHover: dark ? "#262835" : "#EBEEF6"
        readonly property color field: dark ? "#2C2E3A" : "#FFFFFF"
        readonly property color fieldBorder: dark ? "#4A4D5E" : "#C4C9D4"
        readonly property color danger: dark ? "#FF99A4" : "#C42B1C"
        readonly property int radius: 8
        readonly property int titleSize: Math.round(20 * scale)
        readonly property int bodySize: Math.round(14 * scale)
        readonly property int captionSize: Math.round(12 * scale)
        readonly property int hourHeight: 52
    }

    // --- Small controls ------------------------------------------------------------------
    component VButton: Rectangle {
        id: button
        property string text
        property string icon
        property bool primary: false
        property bool flat: false
        property bool checked: false
        property bool enabledState: true
        signal clicked()
        implicitWidth: Math.max(flat ? 32 : 84, buttonRow.implicitWidth + (text !== "" ? 28 : 12))
        implicitHeight: 32
        radius: 5
        opacity: enabledState ? 1 : 0.5
        color: primary ? (buttonHover.hovered ? Qt.lighter(theme.accent, 1.08) : theme.accent)
             : checked ? theme.accentSoft
             : flat ? (buttonHover.hovered ? theme.navHover : "transparent")
             : (buttonHover.hovered ? theme.cardHover : theme.card)
        border.width: primary || flat || checked ? 0 : 1
        border.color: theme.cardBorder
        activeFocusOnTab: enabledState
        Accessible.role: Accessible.Button
        Accessible.name: text
        Keys.onReturnPressed: if (enabledState) clicked()
        Keys.onSpacePressed: if (enabledState) clicked()
        RowLayout {
            id: buttonRow
            anchors.centerIn: parent
            spacing: 8
            Kirigami.Icon {
                visible: button.icon !== ""
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                source: button.icon
                isMask: true
                color: button.primary ? "#FFFFFF" : (button.checked ? theme.accent : theme.text)
            }
            Text {
                visible: button.text !== ""
                text: button.text
                color: button.primary ? "#FFFFFF" : (button.checked ? theme.accent : theme.text)
                font.pixelSize: theme.bodySize
                font.weight: button.checked ? Font.DemiBold : Font.Normal
            }
        }
        Rectangle {
            visible: button.activeFocus
            anchors.fill: parent
            anchors.margins: -3
            radius: 7
            color: "transparent"
            border.width: 2
            border.color: theme.text
        }
        HoverHandler { id: buttonHover; enabled: button.enabledState }
        TapHandler { enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    component Field: TextField {
        color: theme.text
        font.pixelSize: theme.bodySize
        selectByMouse: true
        placeholderTextColor: theme.faint
        background: Rectangle {
            radius: 5
            color: theme.field
            border.width: 1
            border.color: parent.activeFocus ? theme.accent : theme.fieldBorder
            Rectangle {
                visible: parent.parent.activeFocus
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 1
                height: 2
                color: theme.accent
            }
        }
    }

    component Choice: ComboBox {
        id: choice
        property var options: []
        property var current
        signal chosen(var value)
        model: options
        textRole: "label"
        valueRole: "value"
        currentIndex: Math.max(0, options.findIndex(o => o.value === current))
        onActivated: index => chosen(options[index].value)
        font.pixelSize: theme.bodySize
    }

    component Check: Rectangle {
        id: check
        property string label
        property bool checked: false
        signal toggled(bool on)
        implicitWidth: checkRow.implicitWidth
        implicitHeight: 30
        color: "transparent"
        activeFocusOnTab: true
        Accessible.role: Accessible.CheckBox
        Accessible.name: label
        Accessible.checked: checked
        Keys.onSpacePressed: toggled(!checked)
        RowLayout {
            id: checkRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            Rectangle {
                implicitWidth: 20
                implicitHeight: 20
                radius: 4
                color: check.checked ? theme.accent : theme.field
                border.width: check.checked ? 0 : 1
                border.color: check.activeFocus ? theme.accent : theme.fieldBorder
                Text {
                    anchors.centerIn: parent
                    visible: check.checked
                    text: "✓"
                    color: "#FFFFFF"
                    font.pixelSize: 13
                }
            }
            Text {
                text: check.label
                color: theme.text
                font.pixelSize: theme.bodySize
            }
        }
        TapHandler { onTapped: check.toggled(!check.checked) }
    }

    // A date button that opens a small month to pick from.
    component DateField: VButton {
        id: dateField
        property string date        // YYYY-MM-DD
        signal picked(string date)
        text: {
            const d = new Date(date + "T00:00:00");
            return isNaN(d) ? date : d.toLocaleDateString(Qt.locale(backend.tr("app_title") === "Takvim" ? "tr_TR" : "en_US"),
                                                           Locale.ShortFormat);
        }
        icon: "view-calendar-symbolic"
        implicitWidth: 150
        onClicked: datePopup.open()
        Popup {
            id: datePopup
            y: dateField.height + 4
            padding: 10
            background: Rectangle { radius: 8; color: theme.card; border.width: 1; border.color: theme.cardBorder }
            property date month: new Date(dateField.date + "T00:00:00")
            onAboutToShow: month = new Date(dateField.date + "T00:00:00")
            contentItem: ColumnLayout {
                spacing: 6
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: datePopup.month.toLocaleDateString(Qt.locale(), "MMMM yyyy")
                        color: theme.text
                        font.pixelSize: theme.bodySize
                        font.weight: Font.DemiBold
                    }
                    VButton { flat: true; icon: "go-up-symbolic"; onClicked: datePopup.month = new Date(datePopup.month.getFullYear(), datePopup.month.getMonth() - 1, 1) }
                    VButton { flat: true; icon: "go-down-symbolic"; onClicked: datePopup.month = new Date(datePopup.month.getFullYear(), datePopup.month.getMonth() + 1, 1) }
                }
                Grid {
                    columns: 7
                    spacing: 2
                    Repeater {
                        model: {
                            const first = new Date(datePopup.month.getFullYear(), datePopup.month.getMonth(), 1);
                            const shift = (first.getDay() + 6) % 7;
                            const days = [];
                            for (let i = 0; i < 42; ++i)
                                days.push(new Date(first.getFullYear(), first.getMonth(), 1 - shift + i));
                            return days;
                        }
                        delegate: Rectangle {
                            required property var modelData
                            readonly property string isoDate: Qt.formatDate(modelData, "yyyy-MM-dd")
                            width: 32
                            height: 32
                            radius: 16
                            color: isoDate === dateField.date ? theme.accent : (dayHover.hovered ? theme.navHover : "transparent")
                            Text {
                                anchors.centerIn: parent
                                text: parent.modelData.getDate()
                                color: parent.isoDate === dateField.date ? "#FFFFFF"
                                     : parent.modelData.getMonth() === datePopup.month.getMonth() ? theme.text : theme.faint
                                font.pixelSize: theme.captionSize
                            }
                            HoverHandler { id: dayHover }
                            TapHandler {
                                onTapped: {
                                    dateField.picked(parent.isoDate);
                                    datePopup.close();
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    function openDraft(day, minute, anchor) {
        quick.form = backend.draft(day, minute);
        quick.isNew = true;
        quick.anchorItem = anchor;
        quick.open();
    }
    function openEvent(uid, occurrence, anchor) {
        const form = backend.eventForm(uid, occurrence);
        if (!form.uid)
            return;
        quick.form = form;
        quick.isNew = false;
        quick.anchorItem = anchor;
        quick.open();
    }
    function openEditor(form) {
        quick.close();
        window.editing = Object.assign({}, form);
    }

    Component.onCompleted: {
        if (backend.startWithNewEvent)
            window.openEditor(backend.draft(backend.cursor, 9 * 60));
    }

    Shortcut { sequence: "Ctrl+N"; onActivated: window.openEditor(backend.draft(backend.cursor, 9 * 60)) }
    Shortcut { sequence: "Ctrl+T"; enabled: window.editing === null; onActivated: backend.goToday() }
    Shortcut { sequences: ["Alt+Left", "PgUp"]; enabled: window.editing === null; onActivated: backend.step(-1) }
    Shortcut { sequences: ["Alt+Right", "PgDown"]; enabled: window.editing === null; onActivated: backend.step(1) }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- Left pane: New event, the small month, the calendars ------------------
        // Fixed width: a layout whose children fill their width expands
        // itself unless told not to, and took the window's width from the
        // calendar (VM, 2026-10-23).
        ColumnLayout {
            objectName: "sidePane"
            visible: window.wide
            Layout.preferredWidth: 288
            Layout.maximumWidth: 288
            Layout.fillWidth: false
            Layout.fillHeight: true
            Layout.margins: 12
            spacing: 14

            VButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                text: backend.tr("new_event")
                icon: "list-add-symbolic"
                checked: true
                onClicked: window.openEditor(backend.draft(backend.cursor, 9 * 60))
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        Layout.leftMargin: 6
                        text: backend.miniTitle
                        color: theme.text
                        font.pixelSize: theme.bodySize
                        font.weight: Font.DemiBold
                    }
                    VButton { flat: true; icon: "go-up-symbolic"; onClicked: backend.stepMini(-1); Accessible.name: backend.tr("previous") }
                    VButton { flat: true; icon: "go-down-symbolic"; onClicked: backend.stepMini(1); Accessible.name: backend.tr("next") }
                }
                Grid {
                    Layout.alignment: Qt.AlignHCenter
                    columns: 7
                    spacing: 2
                    Repeater {
                        model: backend.weekDayNames
                        delegate: Text {
                            required property var modelData
                            width: 36
                            height: 26
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.mini
                            color: theme.subtext
                            font.pixelSize: theme.captionSize
                        }
                    }
                    Repeater {
                        model: backend.miniCells
                        delegate: Rectangle {
                            id: miniDay
                            required property var modelData
                            width: 36
                            height: 36
                            radius: 18
                            color: modelData.today ? theme.accent
                                 : modelData.selected ? theme.accentSoft
                                 : (miniHover.hovered ? theme.navHover : "transparent")
                            Accessible.role: Accessible.Button
                            Accessible.name: modelData.date
                            Text {
                                anchors.centerIn: parent
                                text: miniDay.modelData.day
                                color: miniDay.modelData.today ? "#FFFFFF"
                                     : miniDay.modelData.inMonth ? theme.text : theme.faint
                                font.pixelSize: theme.captionSize
                                font.weight: miniDay.modelData.today ? Font.DemiBold : Font.Normal
                            }
                            HoverHandler { id: miniHover }
                            TapHandler { onTapped: backend.select(miniDay.modelData.date) }
                        }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: theme.cardBorder }

            Text {
                Layout.leftMargin: 6
                text: backend.tr("calendars")
                color: theme.subtext
                font.pixelSize: theme.captionSize
                font.weight: Font.DemiBold
            }
            RowLayout {
                Layout.leftMargin: 6
                spacing: 10
                Rectangle { implicitWidth: 14; implicitHeight: 14; radius: 3; color: theme.accent }
                Text { text: backend.tr("my_calendar"); color: theme.text; font.pixelSize: theme.bodySize }
            }
            Item { Layout.fillHeight: true }
        }

        // --- The calendar --------------------------------------------------------------
        Rectangle {
            objectName: "calendarView"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 8
            Layout.rightMargin: 8
            Layout.bottomMargin: 8
            Layout.leftMargin: window.wide ? 0 : 8
            radius: theme.radius
            color: theme.card
            border.width: 1
            border.color: theme.cardBorder
            clip: true

            ColumnLayout {
                anchors.fill: parent
                visible: window.editing === null
                spacing: 0

                // Today, arrows, title, views.
                RowLayout {
                    Layout.fillWidth: true
                    Layout.margins: 10
                    spacing: 6
                    VButton { text: backend.tr("today"); icon: "go-jump-today-symbolic"; flat: true; onClicked: backend.goToday() }
                    VButton { flat: true; icon: "go-up-symbolic"; onClicked: backend.step(-1); Accessible.name: backend.tr("previous") }
                    VButton { flat: true; icon: "go-down-symbolic"; onClicked: backend.step(1); Accessible.name: backend.tr("next") }
                    Text {
                        Layout.fillWidth: true
                        Layout.leftMargin: 6
                        text: backend.title
                        color: theme.text
                        font.pixelSize: theme.titleSize
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Repeater {
                        model: ["day", "workweek", "week", "month", "year"]
                        delegate: VButton {
                            required property string modelData
                            flat: true
                            checked: backend.view === modelData
                            text: backend.tr(modelData === "workweek" ? "work_week" : modelData)
                            onClicked: backend.setView(modelData)
                        }
                    }
                }
                Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: theme.cardBorder }

                Loader {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    sourceComponent: backend.view === "month" ? monthView
                                   : backend.view === "year" ? yearView : weekView
                }
            }

            Loader {
                anchors.fill: parent
                active: window.editing !== null
                sourceComponent: editorComponent
            }
        }
    }

    // --- Month ---------------------------------------------------------------------------
    Component {
        id: monthView
        ColumnLayout {
            spacing: 0
            Row {
                Layout.fillWidth: true
                Repeater {
                    model: backend.weekDayNames
                    delegate: Text {
                        required property var modelData
                        width: (parent.parent.width) / 7
                        height: 32
                        leftPadding: 10
                        verticalAlignment: Text.AlignVCenter
                        text: parent.parent.width > 900 ? modelData.long : modelData.short
                        color: theme.subtext
                        font.pixelSize: theme.captionSize
                        elide: Text.ElideRight
                    }
                }
            }
            Grid {
                id: monthGrid
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 7
                readonly property real cellWidth: width / 7
                readonly property real cellHeight: height / 6
                Repeater {
                    model: backend.monthCells
                    delegate: Rectangle {
                        id: cell
                        required property var modelData
                        width: monthGrid.cellWidth
                        height: monthGrid.cellHeight
                        color: cellHover.hovered ? theme.cardHover : "transparent"
                        border.width: 0
                        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: theme.grid }
                        Rectangle { anchors.left: parent.left; height: parent.height; width: 1; color: theme.grid }
                        HoverHandler { id: cellHover }
                        TapHandler { onTapped: window.openDraft(cell.modelData.date, -1, cell) }

                        Rectangle {
                            id: dayBadge
                            x: 6
                            y: 6
                            height: 26
                            width: Math.max(26, dayText.implicitWidth + 14)
                            radius: 13
                            color: cell.modelData.today ? theme.accent : "transparent"
                            Text {
                                id: dayText
                                anchors.centerIn: parent
                                text: cell.modelData.label
                                color: cell.modelData.today ? "#FFFFFF" : (cell.modelData.inMonth ? theme.text : theme.faint)
                                font.pixelSize: theme.captionSize
                                font.weight: cell.modelData.today || cell.modelData.selected ? Font.DemiBold : Font.Normal
                            }
                            TapHandler {
                                onTapped: {
                                    backend.select(cell.modelData.date);
                                    backend.setView("day");
                                }
                            }
                        }
                        Column {
                            anchors.top: dayBadge.bottom
                            anchors.topMargin: 4
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.leftMargin: 6
                            anchors.rightMargin: 6
                            spacing: 3
                            Repeater {
                                model: cell.modelData.events
                                delegate: Rectangle {
                                    id: chip
                                    required property var modelData
                                    width: parent.width
                                    height: 22
                                    radius: 4
                                    color: modelData.allDay ? Qt.alpha(modelData.colour, chipHover.hovered ? 0.32 : 0.2)
                                                            : (chipHover.hovered ? theme.navHover : "transparent")
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 6
                                        anchors.rightMargin: 4
                                        spacing: 6
                                        Rectangle {
                                            visible: !chip.modelData.allDay
                                            implicitWidth: 8
                                            implicitHeight: 8
                                            radius: 4
                                            color: chip.modelData.colour
                                        }
                                        Text {
                                            visible: chip.modelData.time !== ""
                                            text: chip.modelData.time
                                            color: theme.subtext
                                            font.pixelSize: theme.captionSize
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: chip.modelData.title
                                            color: theme.text
                                            font.pixelSize: theme.captionSize
                                            elide: Text.ElideRight
                                        }
                                    }
                                    HoverHandler { id: chipHover }
                                    TapHandler { onTapped: window.openEvent(chip.modelData.uid, chip.modelData.start, chip) }
                                }
                            }
                            Text {
                                visible: cell.modelData.more > 0
                                leftPadding: 6
                                text: backend.trCount("more_events", cell.modelData.more)
                                color: theme.accent
                                font.pixelSize: theme.captionSize
                                TapHandler {
                                    onTapped: {
                                        backend.select(cell.modelData.date);
                                        backend.setView("day");
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // --- Day, work week, week ---------------------------------------------------------
    Component {
        id: weekView
        ColumnLayout {
            id: week
            spacing: 0
            readonly property int gutter: 64
            readonly property real dayWidth: (width - gutter - 14) / Math.max(1, backend.columns.length)

            // Day names and the whole-day events.
            Row {
                Layout.fillWidth: true
                Layout.leftMargin: week.gutter
                Repeater {
                    model: backend.columns
                    delegate: Column {
                        id: head
                        required property var modelData
                        width: week.dayWidth
                        spacing: 4
                        RowLayout {
                            width: parent.width
                            height: 52
                            spacing: 8
                            Rectangle {
                                Layout.leftMargin: 10
                                implicitWidth: 36
                                implicitHeight: 36
                                radius: 18
                                color: head.modelData.today ? theme.accent : "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: head.modelData.number
                                    color: head.modelData.today ? "#FFFFFF" : theme.text
                                    font.pixelSize: theme.titleSize
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: week.dayWidth > 120 ? head.modelData.name : head.modelData.short
                                color: head.modelData.today ? theme.accent : theme.subtext
                                font.pixelSize: theme.captionSize
                                elide: Text.ElideRight
                            }
                        }
                        Repeater {
                            model: head.modelData.allDay
                            delegate: Rectangle {
                                id: allDayChip
                                required property var modelData
                                x: 4
                                width: parent.width - 8
                                height: 24
                                radius: 4
                                color: Qt.alpha(modelData.colour, 0.22)
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    x: 8
                                    width: parent.width - 12
                                    text: allDayChip.modelData.title
                                    color: theme.text
                                    font.pixelSize: theme.captionSize
                                    elide: Text.ElideRight
                                }
                                TapHandler { onTapped: window.openEvent(allDayChip.modelData.uid, allDayChip.modelData.start, allDayChip) }
                            }
                        }
                        Item { width: 1; height: 4 }
                    }
                }
            }
            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: theme.cardBorder }

            Flickable {
                id: hours
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentHeight: 24 * theme.hourHeight
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                Component.onCompleted: contentY = Math.min(contentHeight - height, 8 * theme.hourHeight)

                // Hour labels and lines.
                Repeater {
                    model: 24
                    delegate: Item {
                        required property int index
                        y: index * theme.hourHeight
                        width: hours.width
                        height: theme.hourHeight
                        Text {
                            visible: index > 0
                            x: 8
                            y: -height / 2
                            width: week.gutter - 16
                            horizontalAlignment: Text.AlignRight
                            text: backend.timeOptions[index * 2].label
                            color: theme.subtext
                            font.pixelSize: theme.captionSize
                        }
                        Rectangle { x: week.gutter; width: parent.width - week.gutter; height: 1; color: theme.grid }
                    }
                }
                Repeater {
                    model: backend.columns
                    delegate: Item {
                        id: column
                        required property var modelData
                        required property int index
                        x: week.gutter + index * week.dayWidth
                        width: week.dayWidth
                        height: 24 * theme.hourHeight
                        Rectangle { width: 1; height: parent.height; color: theme.grid }
                        // A click on a free half hour starts a new event there.
                        TapHandler {
                            onTapped: (point) => window.openDraft(column.modelData.date,
                                                                  Math.floor(point.position.y / (theme.hourHeight / 2)) * 30, column)
                        }
                        // Now, on today's column.
                        Rectangle {
                            visible: column.modelData.today
                            readonly property date now: new Date()
                            y: (now.getHours() * 60 + now.getMinutes()) / 60 * theme.hourHeight
                            width: parent.width
                            height: 2
                            color: theme.accent
                            Rectangle { x: -5; y: -4; width: 10; height: 10; radius: 5; color: theme.accent }
                        }
                        Repeater {
                            model: column.modelData.timed
                            delegate: Rectangle {
                                id: block
                                required property var modelData
                                readonly property real laneWidth: (column.width - 8) / modelData.lanes
                                x: 4 + modelData.lane * laneWidth
                                y: modelData.from / 60 * theme.hourHeight + 1
                                width: laneWidth - 2
                                height: Math.max(20, (modelData.to - modelData.from) / 60 * theme.hourHeight - 2)
                                radius: 4
                                color: Qt.alpha(modelData.colour, blockHover.hovered ? 0.32 : 0.2)
                                Rectangle { width: 3; height: parent.height; radius: 1.5; color: block.modelData.colour }
                                Column {
                                    x: 9
                                    y: 4
                                    width: parent.width - 12
                                    spacing: 1
                                    Text {
                                        width: parent.width
                                        text: block.modelData.title
                                        color: theme.text
                                        font.pixelSize: theme.captionSize
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        visible: block.height > 40
                                        width: parent.width
                                        text: block.modelData.range + (block.modelData.location ? "  ·  " + block.modelData.location : "")
                                        color: theme.subtext
                                        font.pixelSize: theme.captionSize
                                        elide: Text.ElideRight
                                    }
                                }
                                HoverHandler { id: blockHover }
                                TapHandler { onTapped: window.openEvent(block.modelData.uid, block.modelData.start, block) }
                            }
                        }
                    }
                }
            }
        }
    }

    // --- Year ----------------------------------------------------------------------------
    Component {
        id: yearView
        Flickable {
            clip: true
            contentHeight: yearGrid.implicitHeight + 24
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            GridLayout {
                id: yearGrid
                x: 16
                y: 12
                width: parent.width - 32
                columns: width > 1000 ? 4 : 3
                columnSpacing: 24
                rowSpacing: 18
                Repeater {
                    model: backend.yearMonths
                    delegate: ColumnLayout {
                        id: yearMonth
                        required property var modelData
                        Layout.alignment: Qt.AlignTop
                        spacing: 4
                        Text {
                            text: yearMonth.modelData.name
                            color: theme.accent
                            font.pixelSize: theme.bodySize
                            font.weight: Font.DemiBold
                            TapHandler {
                                onTapped: {
                                    backend.select(yearMonth.modelData.cells[10].date.slice(0, 8) + "01");
                                    backend.setView("month");
                                }
                            }
                        }
                        Grid {
                            columns: 7
                            spacing: 1
                            Repeater {
                                model: yearMonth.modelData.cells
                                delegate: Rectangle {
                                    id: yearDay
                                    required property var modelData
                                    width: 30
                                    height: 26
                                    radius: 13
                                    color: modelData.today ? theme.accent : (yearHover.hovered ? theme.navHover : "transparent")
                                    Text {
                                        anchors.centerIn: parent
                                        text: yearDay.modelData.inMonth ? yearDay.modelData.day : ""
                                        color: yearDay.modelData.today ? "#FFFFFF" : theme.text
                                        font.pixelSize: theme.captionSize
                                    }
                                    HoverHandler { id: yearHover }
                                    TapHandler {
                                        enabled: yearDay.modelData.inMonth
                                        onTapped: {
                                            backend.select(yearDay.modelData.date);
                                            backend.setView("day");
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // --- The quick card: a new event, or an event's summary --------------------------
    Popup {
        id: quick
        property var form: ({})
        property bool isNew: true
        property Item anchorItem: null
        parent: Overlay.overlay
        width: 380
        padding: 16
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        x: {
            if (!anchorItem)
                return (window.width - width) / 2;
            const p = anchorItem.mapToItem(Overlay.overlay, anchorItem.width, 0);
            return p.x + width + 8 < window.width ? p.x + 8 : Math.max(8, anchorItem.mapToItem(Overlay.overlay, 0, 0).x - width - 8);
        }
        y: {
            if (!anchorItem)
                return (window.height - height) / 2;
            const p = anchorItem.mapToItem(Overlay.overlay, 0, 0);
            return Math.max(8, Math.min(window.height - height - 8, p.y));
        }
        onOpened: if (isNew) quickTitle.forceActiveFocus()
        background: Rectangle {
            radius: 8
            color: theme.card
            border.width: 1
            border.color: theme.cardBorder
            Rectangle {
                z: -1
                anchors.fill: parent
                anchors.margins: -4
                anchors.topMargin: -2
                anchors.bottomMargin: -8
                radius: 12
                color: "#000000"
                opacity: theme.dark ? 0.4 : 0.1
            }
        }
        contentItem: ColumnLayout {
            spacing: 12

            // A new event.
            ColumnLayout {
                visible: quick.isNew
                Layout.fillWidth: true
                spacing: 10
                Field {
                    id: quickTitle
                    Layout.fillWidth: true
                    placeholderText: backend.tr("event_name")
                    text: quick.form.title || ""
                    onTextEdited: quick.form.title = text
                    Keys.onReturnPressed: quickSave.clicked()
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    DateField {
                        date: quick.form.startDate || ""
                        onPicked: d => { const f = quick.form; f.startDate = d; f.endDate = d; quick.form = Object.assign({}, f); }
                    }
                    Choice {
                        visible: !quick.form.allDay
                        Layout.fillWidth: true
                        options: backend.timeOptions
                        current: quick.form.startTime
                        onChosen: v => {
                            const f = quick.form;
                            f.startTime = v;
                            const s = v.split(":"), minutes = Number(s[0]) * 60 + Number(s[1]) + 30;
                            f.endTime = ("0" + Math.floor(Math.min(minutes, 23 * 60 + 30) / 60)).slice(-2) + ":"
                                        + ("0" + (Math.min(minutes, 23 * 60 + 30) % 60)).slice(-2);
                            quick.form = Object.assign({}, f);
                        }
                    }
                    Choice {
                        visible: !quick.form.allDay
                        Layout.fillWidth: true
                        options: backend.timeOptions
                        current: quick.form.endTime
                        onChosen: v => { const f = quick.form; f.endTime = v; quick.form = Object.assign({}, f); }
                    }
                }
                Check {
                    label: backend.tr("all_day")
                    checked: quick.form.allDay === true
                    onToggled: on => { const f = quick.form; f.allDay = on; quick.form = Object.assign({}, f); }
                }
                Field {
                    Layout.fillWidth: true
                    placeholderText: backend.tr("add_location")
                    text: quick.form.location || ""
                    onTextEdited: quick.form.location = text
                }
                Choice {
                    Layout.fillWidth: true
                    options: backend.reminderOptions
                    current: quick.form.reminder
                    onChosen: v => quick.form.reminder = v
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    VButton {
                        text: backend.tr("more_details")
                        flat: true
                        onClicked: window.openEditor(quick.form)
                    }
                    Item { Layout.fillWidth: true }
                    VButton {
                        id: quickSave
                        text: backend.tr("save")
                        primary: true
                        onClicked: {
                            if (backend.save(quick.form))
                                quick.close();
                        }
                    }
                }
            }

            // An existing event.
            ColumnLayout {
                visible: !quick.isNew
                Layout.fillWidth: true
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Rectangle { implicitWidth: 4; Layout.fillHeight: true; radius: 2; color: theme.accent }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            Layout.fillWidth: true
                            text: quick.form.title || backend.tr("no_title")
                            color: theme.text
                            font.pixelSize: theme.titleSize
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: quick.form.when || ""
                            color: theme.subtext
                            font.pixelSize: theme.bodySize
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: text !== ""
                            text: quick.form.location || ""
                            color: theme.subtext
                            font.pixelSize: theme.bodySize
                            wrapMode: Text.WordWrap
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    spacing: 8
                    Item { Layout.fillWidth: true }
                    VButton { text: backend.tr("delete"); icon: "edit-delete-symbolic"; onClicked: confirmDelete.ask(quick.form) }
                    VButton { text: backend.tr("edit"); icon: "document-edit-symbolic"; primary: true; onClicked: window.openEditor(quick.form) }
                }
            }
        }
    }

    // --- The full editor ("More details") ---------------------------------------------
    Component {
        id: editorComponent
        ColumnLayout {
            id: editor
            spacing: 0
            property var form: window.editing
            function update(key, value) {
                const f = Object.assign({}, editor.form);
                f[key] = value;
                window.editing = f;
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 10
                spacing: 8
                VButton {
                    text: backend.tr("save_and_close")
                    icon: "document-save-symbolic"
                    primary: true
                    onClicked: {
                        if (backend.save(editor.form))
                            window.editing = null;
                    }
                }
                VButton {
                    visible: (editor.form.uid || "") !== ""
                    text: backend.tr("delete")
                    icon: "edit-delete-symbolic"
                    flat: true
                    onClicked: confirmDelete.ask(editor.form)
                }
                Item { Layout.fillWidth: true }
                Text { text: backend.tr("reminder"); color: theme.subtext; font.pixelSize: theme.bodySize }
                Choice {
                    Layout.preferredWidth: 190
                    options: backend.reminderOptions
                    current: editor.form.reminder
                    onChosen: v => editor.update("reminder", v)
                }
                Text { text: backend.tr("repeat"); color: theme.subtext; font.pixelSize: theme.bodySize }
                Choice {
                    Layout.preferredWidth: 170
                    options: backend.repeatOptions
                    current: editor.form.repeat
                    onChosen: v => editor.update("repeat", v)
                }
                VButton { flat: true; icon: "window-close-symbolic"; onClicked: window.editing = null; Accessible.name: backend.tr("close") }
            }
            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: theme.cardBorder }

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentHeight: fields.implicitHeight + 40
                boundsBehavior: Flickable.StopAtBounds
                ColumnLayout {
                    id: fields
                    x: 24
                    y: 20
                    width: Math.min(720, parent.width - 48)
                    spacing: 14
                    Field {
                        Layout.fillWidth: true
                        font.pixelSize: theme.titleSize
                        placeholderText: backend.tr("event_name")
                        text: editor.form.title || ""
                        onTextEdited: editor.form.title = text
                        Component.onCompleted: forceActiveFocus()
                    }
                    Field {
                        Layout.fillWidth: true
                        placeholderText: backend.tr("add_location")
                        text: editor.form.location || ""
                        onTextEdited: editor.form.location = text
                    }
                    GridLayout {
                        columns: 4
                        columnSpacing: 10
                        rowSpacing: 10
                        Text { text: backend.tr("start"); color: theme.subtext; font.pixelSize: theme.bodySize }
                        DateField {
                            date: editor.form.startDate || ""
                            onPicked: d => {
                                const f = Object.assign({}, editor.form);
                                if (f.endDate < d)
                                    f.endDate = d;
                                f.startDate = d;
                                window.editing = f;
                            }
                        }
                        Choice {
                            visible: !editor.form.allDay
                            Layout.preferredWidth: 140
                            options: backend.timeOptions
                            current: editor.form.startTime
                            onChosen: v => editor.update("startTime", v)
                        }
                        Check {
                            label: backend.tr("all_day")
                            checked: editor.form.allDay === true
                            onToggled: on => editor.update("allDay", on)
                        }
                        Text { text: backend.tr("end"); color: theme.subtext; font.pixelSize: theme.bodySize }
                        DateField {
                            date: editor.form.endDate || ""
                            onPicked: d => editor.update("endDate", d)
                        }
                        Choice {
                            visible: !editor.form.allDay
                            Layout.preferredWidth: 140
                            options: backend.timeOptions
                            current: editor.form.endTime
                            onChosen: v => editor.update("endTime", v)
                        }
                        Item { implicitWidth: 1 }
                    }
                    TextArea {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 220
                        placeholderText: backend.tr("notes")
                        placeholderTextColor: theme.faint
                        text: editor.form.notes || ""
                        onTextChanged: editor.form.notes = text
                        wrapMode: TextEdit.Wrap
                        color: theme.text
                        font.pixelSize: theme.bodySize
                        background: Rectangle {
                            radius: 5
                            color: theme.field
                            border.width: 1
                            border.color: parent.activeFocus ? theme.accent : theme.fieldBorder
                        }
                    }
                }
            }
        }
    }

    // --- Delete? ----------------------------------------------------------------------------
    Popup {
        id: confirmDelete
        property var form: ({})
        function ask(form) {
            confirmDelete.form = form;
            quick.close();
            open();
        }
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 380
        modal: true
        padding: 22
        background: Rectangle { radius: 8; color: theme.card; border.width: 1; border.color: theme.cardBorder }
        contentItem: ColumnLayout {
            spacing: 16
            Text {
                Layout.fillWidth: true
                text: backend.tr("delete_question")
                color: theme.text
                font.pixelSize: theme.titleSize
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                visible: !!confirmDelete.form.repeat && confirmDelete.form.repeat !== "none"
                text: backend.tr("delete_repeating")
                color: theme.subtext
                font.pixelSize: theme.bodySize
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                VButton {
                    Layout.fillWidth: true
                    text: backend.tr("delete")
                    primary: true
                    onClicked: {
                        backend.remove(confirmDelete.form.uid);
                        confirmDelete.close();
                        window.editing = null;
                    }
                }
                VButton {
                    Layout.fillWidth: true
                    text: backend.tr("cancel")
                    onClicked: confirmDelete.close()
                }
            }
        }
    }
}
