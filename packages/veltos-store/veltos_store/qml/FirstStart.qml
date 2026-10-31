// The first start's "Getting everything ready" screen, as Windows 11 shows
// its out-of-box screens: full screen, dark navy with soft colour that
// drifts slowly, "Hi." and the big line, the moving dots while the update
// runs, then a check mark and "You're ready to go" before it closes.
// Without a network: "Let's connect you to a network" with Connect to
// Wi-Fi (VeltOS Settings) and Continue without internet.
// `backend` is firststart.FirstStart. Animations only move and fade
// (transform/opacity) and stop with the window.
import QtQuick
import QtQuick.Window

Window {
    id: window
    visible: true
    visibility: Window.FullScreen
    flags: Qt.FramelessWindowHint
    color: "#050818"
    title: backend.texts.fs_title

    readonly property bool ready: backend.ready
    readonly property bool offline: backend.offline
    readonly property bool animate: window.visible
    readonly property real s: Math.max(0.75, Math.min(width / 1920, height / 1080)) * backend.textScale

    // Brand colours drifting behind the text.
    Repeater {
        model: [{ c: "#CC4F7CFF", e: "#004F7CFF", x: 0.18, y: 0.25, d: 18000 },
                { c: "#CC5B3FE0", e: "#005B3FE0", x: 0.78, y: 0.30, d: 23000 },
                { c: "#B32FA8F0", e: "#002FA8F0", x: 0.55, y: 0.85, d: 27000 }]
        delegate: Rectangle {
            id: blob
            required property var modelData
            width: window.width * 0.7
            height: width
            radius: width / 2
            x: window.width * modelData.x - width / 2
            y: window.height * modelData.y - height / 2
            opacity: 0.0
            gradient: Gradient {
                GradientStop { position: 0.0; color: blob.modelData.c }
                GradientStop { position: 1.0; color: blob.modelData.e }
            }
            NumberAnimation on opacity { to: 0.7; duration: 1600; easing.type: Easing.OutCubic }
            SequentialAnimation on scale {
                running: window.animate
                loops: Animation.Infinite
                NumberAnimation { from: 0.85; to: 1.15; duration: blob.modelData.d; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.15; to: 0.85; duration: blob.modelData.d; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on rotation {
                running: window.animate
                loops: Animation.Infinite
                NumberAnimation { from: 0; to: 360; duration: blob.modelData.d * 3 }
            }
        }
    }
    // A dark veil keeps the text readable over the colour.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#59050818" }
            GradientStop { position: 1.0; color: "#99050818" }
        }
    }

    Column {
        id: content
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -40 * window.s
        width: Math.min(window.width - 80, 1100 * window.s)
        spacing: 22 * window.s

        Text {
            objectName: "hello"
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: window.ready ? "" : backend.texts.fs_hi
            visible: text !== ""
            color: "#FFFFFF"
            opacity: 0.85
            font.pixelSize: 34 * window.s
            font.weight: Font.Light
        }
        Text {
            objectName: "title"
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: window.ready ? backend.texts.fs_ready
                  : window.offline ? backend.texts.fs_offline_title : backend.texts.fs_title
            color: "#FFFFFF"
            font.pixelSize: 46 * window.s
            font.weight: Font.Normal
            Behavior on text {
                SequentialAnimation {
                    NumberAnimation { target: content; property: "opacity"; to: 0; duration: 250 }
                    PropertyAction {}
                    NumberAnimation { target: content; property: "opacity"; to: 1; duration: 350 }
                }
            }
        }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: window.ready ? backend.texts["fs_" + backend.state + "_sub"]
                  : window.offline ? (backend.bottles ? backend.texts.fs_offline_bottles_sub
                                                      : backend.texts.fs_offline_sub)
                  : backend.texts.fs_sub
            color: "#C9D3F2"
            font.pixelSize: 20 * window.s
        }

        // Windows' loading dots: five dots running round a circle.
        Item {
            id: spinner
            anchors.horizontalCenter: parent.horizontalCenter
            width: 64 * window.s
            height: width
            visible: !window.ready && !window.offline
            Repeater {
                model: 5
                delegate: Item {
                    id: dot
                    required property int index
                    anchors.fill: parent
                    rotation: 0
                    opacity: 0
                    Rectangle {
                        width: 7 * window.s
                        height: width
                        radius: width / 2
                        color: "#FFFFFF"
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    SequentialAnimation {
                        running: window.animate && spinner.visible
                        loops: Animation.Infinite
                        PauseAnimation { duration: dot.index * 120 }
                        PropertyAction { target: dot; property: "opacity"; value: 1 }
                        NumberAnimation { target: dot; property: "rotation"; from: 0; to: 360; duration: 1900;
                                          easing.type: Easing.InOutCubic }
                        PropertyAction { target: dot; property: "opacity"; value: 0 }
                        PauseAnimation { duration: (4 - dot.index) * 120 + 300 }
                    }
                }
            }
        }

        // The check mark when everything is ready.
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 64 * window.s
            height: width
            visible: window.ready
            Rectangle {
                id: check
                anchors.fill: parent
                radius: width / 2
                color: backend.state === "done" ? "#4F7CFF" : "#5B6380"
                scale: window.ready ? 1 : 0.4
                Behavior on scale { NumberAnimation { duration: 450; easing.type: Easing.OutBack } }
                Text {
                    anchors.centerIn: parent
                    text: "✓"
                    color: "#FFFFFF"
                    font.pixelSize: 34 * window.s
                    font.weight: Font.DemiBold
                }
            }
        }

        Text {
            objectName: "detail"
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: window.ready || window.offline ? "" : backend.detail
            visible: text !== ""
            color: "#9FB0E0"
            font.pixelSize: 17 * window.s
        }

        // No network: connect (VeltOS Settings at Wi-Fi) or go on without.
        Row {
            objectName: "offlineButtons"
            anchors.horizontalCenter: parent.horizontalCenter
            visible: window.offline
            spacing: 14 * window.s
            Repeater {
                model: [{ key: "fs_connect", primary: true }, { key: "fs_skip", primary: false }]
                delegate: Rectangle {
                    id: choice
                    required property var modelData
                    width: label.implicitWidth + 48 * window.s
                    height: 46 * window.s
                    radius: height / 2
                    color: modelData.primary ? (hover.hovered ? "#E6ECFF" : "#FFFFFF")
                                             : (hover.hovered ? "#26FFFFFF" : "transparent")
                    border.width: modelData.primary ? 0 : 1
                    border.color: "#99FFFFFF"
                    Accessible.role: Accessible.Button
                    Accessible.name: label.text
                    Text {
                        id: label
                        anchors.centerIn: parent
                        text: backend.texts[choice.modelData.key]
                        color: choice.modelData.primary ? "#0E1846" : "#FFFFFF"
                        font.pixelSize: 17 * window.s
                        font.weight: Font.DemiBold
                    }
                    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: choice.modelData.primary ? backend.connectNetwork() : backend.close()
                    }
                }
            }
        }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            visible: window.offline
            text: backend.texts.fs_skip_note
            color: "#9FB0E0"
            font.pixelSize: 15 * window.s
        }
    }

    Connections {
        target: backend
        function onHideWindow() { window.hide(); }
        function onShowWindow() {
            window.showFullScreen();
            window.raise();
            window.requestActivate();
        }
    }

    // A thin bar along the bottom with the update's progress.
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 120 * window.s
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(window.width * 0.4, 520 * window.s)
        height: 3
        radius: 1.5
        color: "#33FFFFFF"
        visible: !window.ready && (backend.state === "download" || backend.state === "install")
        Rectangle {
            width: parent.width * backend.percent / 100
            height: parent.height
            radius: parent.radius
            color: "#FFFFFF"
            Behavior on width { NumberAnimation { duration: 400 } }
        }
    }

    Text {
        objectName: "background"
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 56 * window.s
        anchors.horizontalCenter: parent.horizontalCenter
        visible: backend.canHide
        text: backend.texts.fs_hide
        color: "#C9D3F2"
        font.pixelSize: 16 * window.s
        font.underline: hideHover.hovered
        HoverHandler { id: hideHover; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: backend.close() }
    }
}
