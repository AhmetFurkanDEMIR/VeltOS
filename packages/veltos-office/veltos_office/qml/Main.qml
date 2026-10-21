/*
    VeltOS Office start screen: the Home / New / Open / Account / Options
    pages of Microsoft 365's apps on Windows 11, in front of LibreOffice.
    The window draws its own frame (title bar and rail in the app's
    colour): a soft shadow around it, which Python excludes from the input
    region, and resize borders that hand resizing to the window manager.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "."

ApplicationWindow {
    id: window

    readonly property bool maximized: visibility === Window.Maximized || visibility === Window.FullScreen
    readonly property int shadow: maximized ? 0 : 12
    readonly property var pages: ["home", "new", "open", "account", "options"]

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }

    width: 1120
    height: 740
    minimumWidth: 800
    minimumHeight: 540
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: backend.appTitle

    Connections {
        target: backend
        function onMessage(text) { dialog.tell(text); }
    }

    // --- Shadow ----------------------------------------------------------------------
    Repeater {
        model: window.shadow
        delegate: Rectangle {
            required property int index
            anchors.fill: frame
            anchors.margins: -(index + 1)
            radius: frame.radius + index + 1
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(0, 0, 0, (Theme.dark ? 0.22 : 0.075) * Math.pow(1 - index / window.shadow, 2))
        }
    }

    Rectangle {
        id: frame
        anchors.fill: parent
        anchors.margins: window.shadow
        radius: window.maximized ? 0 : 8
        color: Theme.chrome
        clip: true

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            TitleBar {
                Layout.fillWidth: true
                window: window
                radius: frame.radius
                onCloseWindow: window.close()
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                Rail {
                    Layout.preferredWidth: Theme.railWidth
                    Layout.fillHeight: true
                    onChosen: page => backend.setPage(page)
                }

                // The pages: light, with a rounded top left corner where they meet the rail.
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.page
                    topLeftRadius: 8
                    bottomRightRadius: window.maximized ? 0 : frame.radius - 1

                    StackLayout {
                        id: stack
                        anchors.fill: parent
                        currentIndex: Math.max(0, window.pages.indexOf(backend.page))
                        HomePage { }
                        NewPage { }
                        OpenPage { }
                        AccountPage { }
                        OptionsPage { }
                    }

                    // While LibreOffice brings its window up: a Windows 11 indeterminate bar.
                    Item {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 3
                        clip: true
                        visible: backend.busy
                        Rectangle {
                            id: runner
                            width: parent.width / 3
                            height: parent.height
                            radius: 1.5
                            color: Theme.accent
                            NumberAnimation on x {
                                running: backend.busy
                                loops: Animation.Infinite
                                from: -runner.width
                                to: runner.parent.width
                                duration: 1200
                                easing.type: Easing.InOutQuad
                            }
                        }
                    }
                }
            }
        }
    }

    // --- Message ---------------------------------------------------------------------
    Popup {
        id: dialog
        property string message
        function tell(text) { message = text; open(); }
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        padding: 24
        closePolicy: Popup.CloseOnEscape
        Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.35) }
        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 150 * Theme.anim }
            NumberAnimation { property: "scale"; from: 0.95; to: 1; duration: 180 * Theme.anim; easing.type: Easing.OutCubic }
        }
        background: Rectangle {
            radius: 8
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder
        }
        contentItem: ColumnLayout {
            spacing: 20
            Text {
                Layout.preferredWidth: Math.round(360 * Theme.textScale)
                text: dialog.message
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.Wrap
                renderType: Text.NativeRendering
            }
            VButton {
                Layout.alignment: Qt.AlignRight
                accent: true
                text: backend.text("ok")
                onClicked: dialog.close()
            }
        }
    }

    // --- Resize borders --------------------------------------------------------------
    component Edge: MouseArea {
        property int edges
        enabled: !window.maximized
        hoverEnabled: true
        onPressed: window.startSystemResize(edges)
    }
    readonly property int grip: 6
    Edge { edges: Qt.LeftEdge; cursorShape: Qt.SizeHorCursor
           x: window.shadow - grip; y: window.shadow + grip; width: 2 * grip; height: window.height - 2 * window.shadow - 2 * grip }
    Edge { edges: Qt.RightEdge; cursorShape: Qt.SizeHorCursor
           x: window.width - window.shadow - grip; y: window.shadow + grip; width: 2 * grip; height: window.height - 2 * window.shadow - 2 * grip }
    Edge { edges: Qt.TopEdge; cursorShape: Qt.SizeVerCursor
           x: window.shadow + grip; y: window.shadow - grip; width: window.width - 2 * window.shadow - 2 * grip; height: grip + 2 }
    Edge { edges: Qt.BottomEdge; cursorShape: Qt.SizeVerCursor
           x: window.shadow + grip; y: window.height - window.shadow - grip; width: window.width - 2 * window.shadow - 2 * grip; height: 2 * grip }
    Edge { edges: Qt.TopEdge | Qt.LeftEdge; cursorShape: Qt.SizeFDiagCursor
           x: window.shadow - grip; y: window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.TopEdge | Qt.RightEdge; cursorShape: Qt.SizeBDiagCursor
           x: window.width - window.shadow - grip; y: window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.BottomEdge | Qt.LeftEdge; cursorShape: Qt.SizeBDiagCursor
           x: window.shadow - grip; y: window.height - window.shadow - grip; width: 2 * grip; height: 2 * grip }
    Edge { edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor
           x: window.width - window.shadow - grip; y: window.height - window.shadow - grip; width: 2 * grip; height: 2 * grip }

    Shortcut { sequence: "Ctrl+N"; onActivated: backend.newBlank() }
    Shortcut { sequence: "Ctrl+O"; onActivated: backend.browse() }
    Shortcut { sequence: "Ctrl+W"; onActivated: window.close() }
}
