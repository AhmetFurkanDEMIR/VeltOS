// The first start's Welcome window: a normal window (no full screen) with
// a soft brand-coloured header that drifts slowly, "Welcome to VeltOS",
// cards that rise in one after another and open what they describe, one
// line about the update that runs in the background, and "Get started".
// `backend` is firststart.FirstStart. Animations only move and fade.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import "."

Window {
    id: window
    width: 880
    height: 700
    minimumWidth: 620
    minimumHeight: 560
    visible: true
    title: backend.texts.wl_window
    color: Theme.window

    readonly property real s: Math.min(1.25, backend.textScale)

    // --- header: the VeltOS colours, drifting -------------------------------------------------
    Item {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 230 * window.s
        clip: true

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#4F7CFF" }
                GradientStop { position: 0.55; color: "#5B3FE0" }
                GradientStop { position: 1.0; color: "#2FA8F0" }
            }
        }
        Repeater {
            model: [{ x: 0.12, y: 0.2, d: 14000, c: "#66FFFFFF" }, { x: 0.82, y: 0.85, d: 18000, c: "#4D2FA8F0" },
                    { x: 0.55, y: -0.1, d: 22000, c: "#405B3FE0" }]
            delegate: Rectangle {
                id: glow
                required property var modelData
                width: header.width * 0.55
                height: width
                radius: width / 2
                x: header.width * modelData.x - width / 2
                y: header.height * modelData.y - height / 2
                opacity: 0.55
                gradient: Gradient {
                    GradientStop { position: 0.0; color: glow.modelData.c }
                    GradientStop { position: 1.0; color: "transparent" }
                }
                SequentialAnimation on scale {
                    running: window.visible
                    loops: Animation.Infinite
                    NumberAnimation { from: 0.9; to: 1.12; duration: glow.modelData.d; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 1.12; to: 0.9; duration: glow.modelData.d; easing.type: Easing.InOutSine }
                }
                NumberAnimation on rotation {
                    running: window.visible
                    loops: Animation.Infinite
                    from: 0
                    to: 360
                    duration: glow.modelData.d * 3
                }
            }
        }
        // A soft fade into the window's colour at the bottom.
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 60 * window.s
            gradient: Gradient {
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 1.0; color: Qt.rgba(Theme.window.r, Theme.window.g, Theme.window.b, 0.35) }
            }
        }

        Column {
            id: heading
            anchors.left: parent.left
            anchors.leftMargin: 40 * window.s
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6 * window.s
            opacity: 0
            transform: Translate { id: headingShift; y: 18 }
            Kirigami.Icon {
                width: 56 * window.s
                height: width
                source: "start-here"
            }
            Text {
                objectName: "title"
                text: backend.texts.wl_title
                color: "#FFFFFF"
                font.pixelSize: 34 * window.s
                font.weight: Font.DemiBold
            }
            Text {
                text: backend.texts.wl_slogan
                color: "#E8EEFF"
                font.pixelSize: 17 * window.s
            }
            ParallelAnimation {
                running: true
                NumberAnimation { target: heading; property: "opacity"; to: 1; duration: 700; easing.type: Easing.OutCubic }
                NumberAnimation { target: headingShift; property: "y"; to: 0; duration: 700; easing.type: Easing.OutCubic }
            }
        }
    }

    // --- cards ------------------------------------------------------------------------------
    Flickable {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: footer.top
        contentWidth: width
        contentHeight: body.implicitHeight + 24
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        ColumnLayout {
            id: body
            x: 40 * window.s
            y: 20 * window.s
            width: parent.width - 80 * window.s
            spacing: 14 * window.s

            Text {
                Layout.fillWidth: true
                text: backend.texts.wl_intro
                color: Theme.subtext
                font.pixelSize: Theme.bodySize + 2
                wrapMode: Text.Wrap
            }

            GridLayout {
                id: grid
                objectName: "cards"
                Layout.fillWidth: true
                columns: window.width > 760 ? 2 : 1
                columnSpacing: 12 * window.s
                rowSpacing: 12 * window.s
                Repeater {
                    model: backend.cards
                    delegate: Rectangle {
                        id: card
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredHeight: 88 * window.s
                        radius: Theme.radius
                        color: hover.hovered ? Theme.cardHover : Theme.card
                        border.width: 1
                        border.color: Theme.cardBorder
                        opacity: 0
                        transform: Translate { id: rise; y: 24 }
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.title
                        Behavior on color { ColorAnimation { duration: 120 } }

                        SequentialAnimation {
                            running: true
                            PauseAnimation { duration: 250 + card.index * 110 }
                            ParallelAnimation {
                                NumberAnimation { target: card; property: "opacity"; to: 1; duration: 450
                                                  easing.type: Easing.OutCubic }
                                NumberAnimation { target: rise; property: "y"; to: 0; duration: 450
                                                  easing.type: Easing.OutCubic }
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
                                color: Theme.dark ? "#2F3346" : "#EEF2FF"
                                Kirigami.Icon {
                                    anchors.centerIn: parent
                                    width: 30 * window.s
                                    height: width
                                    source: card.modelData.icon
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
        }
    }

    // --- footer: the update's line and Get started ---------------------------------------------
    Rectangle {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 76 * window.s
        color: Theme.pane
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: Theme.cardBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 40 * window.s
            anchors.rightMargin: 24 * window.s
            spacing: 16
            Kirigami.Icon {
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
                source: "update-none"
            }
            Text {
                objectName: "updateLine"
                Layout.fillWidth: true
                text: backend.updateText
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            VButton {
                objectName: "getStarted"
                accent: true
                text: backend.texts.wl_get_started
                onClicked: backend.close()
            }
        }
    }

    onClosing: backend.close()
}
