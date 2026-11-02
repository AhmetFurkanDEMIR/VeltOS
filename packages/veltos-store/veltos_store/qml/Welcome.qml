// The first start's Welcome window, in the manner of Windows 11's Get
// Started app (product owner, 2026-11-02: "more beautiful and animated,
// like Windows 11"): three pages that slide in turn, over softly drifting
// VeltOS colours -
//   1. a greeting: the logo with a pulse, "Hi.", "Welcome to VeltOS";
//   2. "Make it yours": light or dark mode (two small desktop previews) and
//      the accent colour, applied at once through VeltOS Settings' helpers;
//   3. "Get to know VeltOS": the cards and the background update's line;
// with page dots, Back and Next as in Windows 11's setup. A normal window
// (no full screen). `backend` is firststart.FirstStart. Animations only
// move, scale and fade; the endless ones run while the window is active.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import "."

Window {
    id: window
    width: 940
    height: 660
    minimumWidth: 660
    minimumHeight: 560
    visible: true
    title: backend.texts.wl_window
    color: Theme.window

    readonly property real s: Math.min(1.25, backend.textScale)
    readonly property int pageCount: 3
    property int page: 0
    readonly property bool moving: window.visible && window.active
    // The accent the user chose, or VeltOS blue (the theme's own).
    readonly property string chosenAccent: (backend.accent || "#2F5EE6").toUpperCase()

    function next() {
        if (page < pageCount - 1)
            page += 1;
        else
            backend.close();
    }
    function back() {
        if (page > 0)
            page -= 1;
    }

    // --- the drifting colours behind everything ------------------------------------------------
    Item {
        id: aurora
        anchors.fill: parent
        clip: true
        // Full on the greeting, quieter behind the pages with content.
        opacity: window.page === 0 ? 1 : 0.55
        Behavior on opacity { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }

        Repeater {
            model: [
                { x: 0.10, y: 0.20, size: 0.80, c: "#4F7CFF", dx: 0.10, dy: 0.08, d: 17000 },
                { x: 0.88, y: 0.12, size: 0.70, c: "#5B3FE0", dx: -0.09, dy: 0.10, d: 21000 },
                { x: 0.75, y: 0.95, size: 0.85, c: "#2FA8F0", dx: -0.08, dy: -0.09, d: 24000 },
                { x: 0.22, y: 0.92, size: 0.60, c: "", dx: 0.09, dy: -0.07, d: 19000 }
            ]
            delegate: Canvas {
                id: blob
                required property var modelData
                // The fourth glow takes the accent colour.
                readonly property color tint: modelData.c !== "" ? modelData.c : Theme.accent
                readonly property real baseX: aurora.width * modelData.x - width / 2
                readonly property real baseY: aurora.height * modelData.y - height / 2
                width: Math.max(aurora.width, aurora.height) * modelData.size
                height: width
                x: baseX + driftX
                y: baseY + driftY
                property real driftX: 0
                property real driftY: 0
                opacity: Theme.dark ? 0.55 : 0.5
                onTintChanged: requestPaint()
                onWidthChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    const r = width / 2;
                    const g = ctx.createRadialGradient(r, r, 0, r, r, r);
                    g.addColorStop(0, Qt.rgba(tint.r, tint.g, tint.b, 0.9));
                    g.addColorStop(0.45, Qt.rgba(tint.r, tint.g, tint.b, 0.35));
                    g.addColorStop(1, Qt.rgba(tint.r, tint.g, tint.b, 0));
                    ctx.fillStyle = g;
                    ctx.fillRect(0, 0, width, height);
                }
                SequentialAnimation on driftX {
                    running: window.moving
                    loops: Animation.Infinite
                    NumberAnimation { to: aurora.width * blob.modelData.dx; duration: blob.modelData.d
                                      easing.type: Easing.InOutSine }
                    NumberAnimation { to: 0; duration: blob.modelData.d; easing.type: Easing.InOutSine }
                }
                SequentialAnimation on driftY {
                    running: window.moving
                    loops: Animation.Infinite
                    NumberAnimation { to: aurora.height * blob.modelData.dy; duration: blob.modelData.d * 1.3
                                      easing.type: Easing.InOutSine }
                    NumberAnimation { to: 0; duration: blob.modelData.d * 1.3; easing.type: Easing.InOutSine }
                }
                SequentialAnimation on scale {
                    running: window.moving
                    loops: Animation.Infinite
                    NumberAnimation { from: 0.92; to: 1.08; duration: blob.modelData.d * 0.8; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 1.08; to: 0.92; duration: blob.modelData.d * 0.8; easing.type: Easing.InOutSine }
                }
            }
        }
        // A veil in the window's colour keeps the text readable.
        Rectangle {
            anchors.fill: parent
            color: Theme.window
            opacity: Theme.dark ? 0.42 : 0.34
        }
    }

    // A step of an entrance: fades in and rises a little, after `delay` ms,
    // whenever its page becomes the current one.
    component Entrance: Item {
        id: entrance
        property int delay: 0
        property bool shown: false
        default property alias content: holder.data
        implicitWidth: holder.childrenRect.width
        implicitHeight: holder.childrenRect.height
        opacity: 0
        Item {
            id: holder
            anchors.fill: parent
            transform: Translate { id: lift; y: 22 }
        }
        onShownChanged: {
            if (shown) {
                appear.restart();
            } else {
                appear.stop();
                entrance.opacity = 0;
                lift.y = 22;
            }
        }
        Component.onCompleted: if (shown) appear.restart()
        SequentialAnimation {
            id: appear
            PauseAnimation { duration: entrance.delay }
            ParallelAnimation {
                NumberAnimation { target: entrance; property: "opacity"; to: 1; duration: 520; easing.type: Easing.OutCubic }
                NumberAnimation { target: lift; property: "y"; to: 0; duration: 620; easing.type: Easing.OutQuint }
            }
        }
    }

    // --- the pages ---------------------------------------------------------------------------
    Item {
        id: stage
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: footer.top
        clip: true

        Row {
            id: strip
            x: -window.page * stage.width
            height: stage.height
            Behavior on x { NumberAnimation { duration: 560; easing.type: Easing.OutQuint } }

            // 1. The greeting
            Item {
                id: hello
                objectName: "helloPage"
                readonly property bool current: window.page === 0
                width: stage.width
                height: stage.height
                opacity: current ? 1 : 0.0
                Behavior on opacity { NumberAnimation { duration: 400 } }

                ColumnLayout {
                    anchors.centerIn: parent
                    width: Math.min(parent.width - 80, 620 * window.s)
                    spacing: 10 * window.s

                    Entrance {
                        Layout.alignment: Qt.AlignHCenter
                        shown: hello.current
                        Item {
                            width: 132 * window.s
                            height: width
                            // Windows' soft pulse around the logo.
                            Rectangle {
                                id: pulse
                                anchors.centerIn: parent
                                width: parent.width
                                height: width
                                radius: width / 2
                                color: "transparent"
                                border.width: 2
                                border.color: Theme.accent
                                opacity: 0
                                SequentialAnimation {
                                    running: window.moving && hello.current
                                    loops: Animation.Infinite
                                    ParallelAnimation {
                                        NumberAnimation { target: pulse; property: "scale"; from: 0.7; to: 1.35; duration: 2200
                                                          easing.type: Easing.OutCubic }
                                        NumberAnimation { target: pulse; property: "opacity"; from: 0.55; to: 0; duration: 2200
                                                          easing.type: Easing.OutCubic }
                                    }
                                    PauseAnimation { duration: 600 }
                                }
                            }
                            Rectangle {
                                anchors.centerIn: parent
                                width: parent.width * 0.78
                                height: width
                                radius: width / 2
                                color: Theme.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.75)
                                border.width: 1
                                border.color: Theme.dark ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0, 0, 0, 0.06)
                                Kirigami.Icon {
                                    id: logo
                                    anchors.centerIn: parent
                                    width: parent.width * 0.56
                                    height: width
                                    source: "start-here"
                                    scale: hello.current ? 1 : 0.6
                                    Behavior on scale { NumberAnimation { duration: 900; easing.type: Easing.OutBack } }
                                }
                            }
                        }
                    }
                    Entrance {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 6 * window.s
                        shown: hello.current
                        delay: 250
                        Text {
                            objectName: "hello"
                            text: backend.texts.wl_hello
                            color: Theme.accent
                            font.pixelSize: 54 * window.s
                            font.weight: Font.DemiBold
                        }
                    }
                    Entrance {
                        Layout.alignment: Qt.AlignHCenter
                        shown: hello.current
                        delay: 420
                        Text {
                            objectName: "title"
                            text: backend.texts.wl_title
                            color: Theme.text
                            font.pixelSize: 32 * window.s
                            font.weight: Font.DemiBold
                        }
                    }
                    Entrance {
                        Layout.alignment: Qt.AlignHCenter
                        shown: hello.current
                        delay: 560
                        Text {
                            text: backend.texts.wl_slogan
                            color: Theme.subtext
                            font.pixelSize: 17 * window.s
                        }
                    }
                    Entrance {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 14 * window.s
                        shown: hello.current
                        delay: 700
                        Text {
                            width: Math.min(560 * window.s, hello.width - 80)
                            horizontalAlignment: Text.AlignHCenter
                            text: backend.texts.wl_lead
                            color: Theme.text
                            font.pixelSize: Theme.bodySize + 3
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            // 2. Make it yours: light or dark, the accent
            Item {
                id: personal
                objectName: "personalizePage"
                readonly property bool current: window.page === 1
                width: stage.width
                height: stage.height
                opacity: current ? 1 : 0.0
                Behavior on opacity { NumberAnimation { duration: 400 } }

                ColumnLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 56 * window.s
                    anchors.rightMargin: 56 * window.s
                    anchors.topMargin: 40 * window.s
                    spacing: 8 * window.s

                    Entrance {
                        shown: personal.current
                        Text {
                            text: backend.texts.wl_personalize
                            color: Theme.text
                            font.pixelSize: Theme.pageTitleSize + 4
                            font.weight: Font.DemiBold
                        }
                    }
                    Entrance {
                        Layout.fillWidth: true
                        shown: personal.current
                        delay: 90
                        Text {
                            width: personal.width - 112 * window.s
                            text: backend.texts.wl_mode_intro
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize + 2
                            wrapMode: Text.Wrap
                        }
                    }

                    // Without VeltOS Settings: Settings opens instead.
                    VButton {
                        visible: !backend.canPersonalize
                        Layout.topMargin: 12
                        text: backend.texts.wl_open
                        onClicked: backend.open("personalize")
                    }

                    Entrance {
                        Layout.topMargin: 18 * window.s
                        visible: backend.canPersonalize
                        shown: personal.current
                        delay: 160
                        Text {
                            text: backend.texts.wl_mode
                            color: Theme.text
                            font.pixelSize: Theme.sectionSize - 2
                            font.weight: Font.DemiBold
                        }
                    }
                    Entrance {
                        visible: backend.canPersonalize
                        shown: personal.current
                        delay: 220
                        Row {
                            spacing: 16 * window.s
                            Repeater {
                                model: [false, true]
                                delegate: Item {
                                    id: modeTile
                                    required property bool modelData
                                    readonly property bool selected: backend.wantedDark === modelData
                                    objectName: modelData ? "darkTile" : "lightTile"
                                    width: 236 * window.s
                                    height: 178 * window.s
                                    scale: tileHover.hovered ? 1.025 : 1
                                    Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                                    Accessible.role: Accessible.RadioButton
                                    Accessible.name: modelData ? backend.texts.wl_dark : backend.texts.wl_light
                                    Accessible.checked: selected

                                    Rectangle {
                                        id: frame
                                        anchors.fill: parent
                                        anchors.bottomMargin: 30 * window.s
                                        radius: 10
                                        color: Theme.card
                                        border.width: modeTile.selected ? 2 : 1
                                        border.color: modeTile.selected ? Theme.accent : Theme.cardBorder
                                        Behavior on border.color { ColorAnimation { duration: 200 } }
                                        // A small desktop in that mode.
                                        Rectangle {
                                            anchors.fill: parent
                                            anchors.margins: 6
                                            radius: 6
                                            clip: true
                                            gradient: Gradient {
                                                orientation: Gradient.Horizontal
                                                GradientStop { position: 0; color: modeTile.modelData ? "#0E1846" : "#DCE6FF" }
                                                GradientStop { position: 1; color: modeTile.modelData ? "#2A1F6E" : "#B9CCFF" }
                                            }
                                            Rectangle {
                                                x: parent.width * 0.16
                                                y: parent.height * 0.14
                                                width: parent.width * 0.62
                                                height: parent.height * 0.52
                                                radius: 4
                                                color: modeTile.modelData ? "#2B2B2B" : "#FFFFFF"
                                                Rectangle {
                                                    width: parent.width
                                                    height: parent.height * 0.18
                                                    radius: 4
                                                    color: modeTile.modelData ? "#202020" : "#F3F3F3"
                                                }
                                                Rectangle {
                                                    x: parent.width * 0.1
                                                    y: parent.height * 0.42
                                                    width: parent.width * 0.42
                                                    height: parent.height * 0.14
                                                    radius: 2
                                                    color: Theme.accent
                                                }
                                                Rectangle {
                                                    x: parent.width * 0.1
                                                    y: parent.height * 0.66
                                                    width: parent.width * 0.7
                                                    height: parent.height * 0.08
                                                    radius: 2
                                                    color: modeTile.modelData ? "#4A4A4A" : "#E3E6EE"
                                                }
                                            }
                                            Rectangle {
                                                anchors.left: parent.left
                                                anchors.right: parent.right
                                                anchors.bottom: parent.bottom
                                                height: parent.height * 0.14
                                                color: modeTile.modelData ? "#E6202020" : "#E6F3F3F3"
                                                Row {
                                                    anchors.centerIn: parent
                                                    spacing: 5
                                                    Repeater {
                                                        model: 5
                                                        delegate: Rectangle {
                                                            required property int index
                                                            width: 9
                                                            height: 9
                                                            radius: 2
                                                            color: index === 0 ? Theme.accent
                                                                               : (modeTile.modelData ? "#6A6A6A" : "#B5BAC6")
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    Row {
                                        anchors.left: parent.left
                                        anchors.bottom: parent.bottom
                                        anchors.leftMargin: 4
                                        spacing: 8
                                        Rectangle {
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: 18
                                            height: 18
                                            radius: 9
                                            color: modeTile.selected ? Theme.accent : "transparent"
                                            border.width: modeTile.selected ? 0 : 1
                                            border.color: Theme.subtext
                                            Rectangle {
                                                anchors.centerIn: parent
                                                width: 6
                                                height: 6
                                                radius: 3
                                                color: Theme.accentText
                                                visible: modeTile.selected
                                            }
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modeTile.modelData ? backend.texts.wl_dark : backend.texts.wl_light
                                            color: Theme.text
                                            font.pixelSize: Theme.bodySize + 1
                                        }
                                    }
                                    HoverHandler { id: tileHover; cursorShape: Qt.PointingHandCursor }
                                    TapHandler {
                                        gesturePolicy: TapHandler.ReleaseWithinBounds
                                        onTapped: backend.setDarkMode(modeTile.modelData)
                                    }
                                }
                            }
                        }
                    }

                    Entrance {
                        Layout.topMargin: 18 * window.s
                        visible: backend.canPersonalize
                        shown: personal.current
                        delay: 300
                        Text {
                            text: backend.texts.wl_accent
                            color: Theme.text
                            font.pixelSize: Theme.sectionSize - 2
                            font.weight: Font.DemiBold
                        }
                    }
                    Entrance {
                        Layout.fillWidth: true
                        visible: backend.canPersonalize
                        shown: personal.current
                        delay: 360
                        Flow {
                            objectName: "accents"
                            width: personal.width - 112 * window.s
                            spacing: 10 * window.s
                            Repeater {
                                model: backend.accents
                                delegate: Item {
                                    id: swatch
                                    required property string modelData
                                    readonly property bool selected: modelData.toUpperCase() === window.chosenAccent
                                    width: 38 * window.s
                                    height: width
                                    Accessible.role: Accessible.RadioButton
                                    Accessible.name: modelData
                                    Accessible.checked: selected
                                    Rectangle {
                                        anchors.fill: parent
                                        radius: width / 2
                                        color: "transparent"
                                        border.width: 2
                                        border.color: Theme.text
                                        opacity: swatch.selected ? 0.9 : 0
                                        Behavior on opacity { NumberAnimation { duration: 160 } }
                                    }
                                    Rectangle {
                                        anchors.centerIn: parent
                                        width: parent.width - 8
                                        height: width
                                        radius: width / 2
                                        color: swatch.modelData
                                        scale: swatchHover.hovered ? 1.1 : 1
                                        Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                                        Kirigami.Icon {
                                            anchors.centerIn: parent
                                            width: 14
                                            height: 14
                                            visible: swatch.selected
                                            source: "checkmark-symbolic"
                                            color: "#FFFFFF"
                                            isMask: true
                                        }
                                    }
                                    HoverHandler { id: swatchHover; cursorShape: Qt.PointingHandCursor }
                                    TapHandler {
                                        gesturePolicy: TapHandler.ReleaseWithinBounds
                                        onTapped: backend.setAccent(swatch.modelData)
                                    }
                                }
                            }
                        }
                    }
                    Row {
                        Layout.topMargin: 6
                        spacing: 8
                        opacity: backend.applying ? 1 : 0
                        Behavior on opacity { NumberAnimation { duration: 200 } }
                        BusyIndicator {
                            width: 18
                            height: 18
                            running: backend.applying
                        }
                        Text {
                            objectName: "applying"
                            anchors.verticalCenter: parent.verticalCenter
                            text: backend.texts.wl_applying
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                        }
                    }
                }
            }

            // 3. Get to know VeltOS: the cards
            Item {
                id: explore
                objectName: "explorePage"
                readonly property bool current: window.page === 2
                width: stage.width
                height: stage.height
                opacity: current ? 1 : 0.0
                Behavior on opacity { NumberAnimation { duration: 400 } }

                Flickable {
                    anchors.fill: parent
                    contentWidth: width
                    contentHeight: body.implicitHeight + 40 * window.s
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}

                    ColumnLayout {
                        id: body
                        x: 56 * window.s
                        y: 40 * window.s
                        width: parent.width - 112 * window.s
                        spacing: 8 * window.s

                        Entrance {
                            shown: explore.current
                            Text {
                                text: backend.texts.wl_explore
                                color: Theme.text
                                font.pixelSize: Theme.pageTitleSize + 4
                                font.weight: Font.DemiBold
                            }
                        }
                        Entrance {
                            Layout.fillWidth: true
                            shown: explore.current
                            delay: 90
                            Text {
                                width: body.width
                                text: backend.texts.wl_intro
                                color: Theme.subtext
                                font.pixelSize: Theme.bodySize + 2
                                wrapMode: Text.Wrap
                            }
                        }

                        GridLayout {
                            id: grid
                            objectName: "cards"
                            Layout.fillWidth: true
                            Layout.topMargin: 12 * window.s
                            columns: window.width > 780 ? 2 : 1
                            columnSpacing: 12 * window.s
                            rowSpacing: 12 * window.s
                            Repeater {
                                // "Make it yours" is the page before when Settings' helpers are there.
                                model: backend.cards.filter(c => c.id !== "personalize" || !backend.canPersonalize)
                                delegate: Rectangle {
                                    id: card
                                    required property var modelData
                                    required property int index
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 88 * window.s
                                    radius: Theme.radius
                                    color: hover.hovered ? Theme.cardHover : Theme.card
                                    border.width: 1
                                    border.color: hover.hovered ? Qt.alpha(Theme.accent, 0.6) : Theme.cardBorder
                                    opacity: 0
                                    transform: Translate { id: rise; y: 26 }
                                    Accessible.role: Accessible.Button
                                    Accessible.name: modelData.title
                                    Behavior on color { ColorAnimation { duration: 120 } }
                                    Behavior on border.color { ColorAnimation { duration: 160 } }

                                    readonly property bool shown: explore.current
                                    onShownChanged: {
                                        if (shown) {
                                            enter.restart();
                                        } else {
                                            enter.stop();
                                            card.opacity = 0;
                                            rise.y = 26;
                                        }
                                    }
                                    SequentialAnimation {
                                        id: enter
                                        PauseAnimation { duration: 180 + card.index * 90 }
                                        ParallelAnimation {
                                            NumberAnimation { target: card; property: "opacity"; to: 1; duration: 480
                                                              easing.type: Easing.OutCubic }
                                            NumberAnimation { target: rise; property: "y"; to: 0; duration: 600
                                                              easing.type: Easing.OutQuint }
                                        }
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 18 * window.s
                                        anchors.rightMargin: 18 * window.s
                                        spacing: 16 * window.s
                                        Rectangle {
                                            Layout.preferredWidth: 48 * window.s
                                            Layout.preferredHeight: 48 * window.s
                                            radius: 12 * window.s
                                            color: Qt.alpha(Theme.accent, Theme.dark ? 0.18 : 0.1)
                                            Kirigami.Icon {
                                                anchors.centerIn: parent
                                                width: 30 * window.s
                                                height: width
                                                source: card.modelData.icon
                                                scale: hover.hovered ? 1.08 : 1
                                                Behavior on scale { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 2
                                            Text {
                                                Layout.fillWidth: true
                                                text: card.modelData.title
                                                color: Theme.text
                                                font.pixelSize: Theme.bodySize + 3
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: card.modelData.description
                                                color: Theme.subtext
                                                font.pixelSize: Theme.bodySize
                                                wrapMode: Text.Wrap
                                                maximumLineCount: 2
                                                elide: Text.ElideRight
                                            }
                                        }
                                        Kirigami.Icon {
                                            Layout.preferredWidth: 16
                                            Layout.preferredHeight: 16
                                            source: "go-next-symbolic"
                                            opacity: hover.hovered ? 1 : 0.5
                                            transform: Translate { x: hover.hovered ? 3 : 0
                                                                   Behavior on x { NumberAnimation { duration: 150 } } }
                                        }
                                    }
                                    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
                                    TapHandler {
                                        gesturePolicy: TapHandler.ReleaseWithinBounds
                                        onTapped: backend.open(card.modelData.id)
                                    }
                                }
                            }
                        }

                        Entrance {
                            Layout.fillWidth: true
                            Layout.topMargin: 14 * window.s
                            shown: explore.current
                            delay: 600
                            Row {
                                spacing: 10
                                Kirigami.Icon {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 18
                                    height: 18
                                    source: "update-none"
                                }
                                Text {
                                    objectName: "updateLine"
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: body.width - 30
                                    text: backend.updateText
                                    color: Theme.subtext
                                    font.pixelSize: Theme.bodySize
                                    wrapMode: Text.Wrap
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // --- footer: page dots, Back, Next / Get started ---------------------------------------------
    Rectangle {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 72 * window.s
        color: Qt.alpha(Theme.pane, 0.82)
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: Theme.cardBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 56 * window.s
            anchors.rightMargin: 24 * window.s
            spacing: 10

            // Windows 11's page dots: the current one a longer pill.
            Row {
                objectName: "pageDots"
                spacing: 6
                Accessible.role: Accessible.StaticText
                Accessible.name: backend.texts.wl_page.arg(window.page + 1).arg(window.pageCount)
                Repeater {
                    model: window.pageCount
                    delegate: Rectangle {
                        required property int index
                        anchors.verticalCenter: parent.verticalCenter
                        width: index === window.page ? 22 : 7
                        height: 7
                        radius: 3.5
                        color: index === window.page ? Theme.accent : Qt.alpha(Theme.text, 0.25)
                        Behavior on width { NumberAnimation { duration: 320; easing.type: Easing.OutQuint } }
                        Behavior on color { ColorAnimation { duration: 240 } }
                        TapHandler { onTapped: window.page = index }
                    }
                }
            }
            Item { Layout.fillWidth: true }
            VButton {
                objectName: "back"
                visible: window.page > 0
                text: backend.texts.wl_back
                onClicked: window.back()
            }
            VButton {
                objectName: window.page === window.pageCount - 1 ? "getStarted" : "next"
                accent: true
                implicitWidth: Math.max(120, contentItem.implicitWidth + 40)
                text: window.page === 0 ? backend.texts.wl_lets_go
                      : window.page === window.pageCount - 1 ? backend.texts.wl_get_started : backend.texts.wl_next
                onClicked: window.next()
            }
        }
    }

    // The keyboard: arrows go between pages, Enter goes on.
    Item {
        focus: true
        Keys.onRightPressed: window.page = Math.min(window.pageCount - 1, window.page + 1)
        Keys.onLeftPressed: window.back()
        Keys.onReturnPressed: window.next()
        Keys.onEnterPressed: window.next()
    }

    onClosing: backend.close()
}
