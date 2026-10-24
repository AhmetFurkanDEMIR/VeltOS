/*
    VeltOS Mail in the layout of Windows 11's new Outlook: the blue header
    with the search box, the app bar (Mail, Calendar, People), the Home /
    View / Help tabs with the simplified ribbon, the folder pane, the
    message list and the reading pane (white cards on a light grey
    canvas). Without an account the window shows "Add your account".
    The window draws its own frame: a soft shadow around it (left out of
    the input region by Python) and resize borders.

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
    property string page: "mail"
    // Set once at start (a binding closed the page before "You're all set!").
    property bool adding: false
    property int listWidth: Math.round(360 * Math.min(1.3, Theme.textScale))

    function toggleMaximized() {
        if (maximized)
            showNormal();
        else
            showMaximized();
    }
    function startAdding() {
        page = "mail";
        adding = true;
        addAccount.reset();
    }

    width: 1360
    height: 860
    minimumWidth: 900
    minimumHeight: 560
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"
    title: backend.text("app_title")

    Connections {
        target: backend
        function onMessage(text) { toast.show(text); }
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
        color: Theme.canvas
        clip: true

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Header {
                id: header
                Layout.fillWidth: true
                window: window
                onOpenSettings: settings.open()
                onCloseWindow: window.close()
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                AppRail {
                    Layout.preferredWidth: 68
                    Layout.fillHeight: true
                    Layout.topMargin: 6
                    current: window.page
                    onChosen: target => {
                        if (target === "calendar")
                            backend.openCalendar();
                        else
                            window.page = target;
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 6
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 8
                    spacing: 8
                    visible: window.page === "mail"

                    Ribbon {
                        id: ribbon
                        Layout.fillWidth: true
                        onShowAbout: info.tell(backend.text("about"), backend.text("about_text"))
                        onShowShortcuts: info.tell(backend.text("shortcuts"), backend.text("shortcuts_text"))
                        onAttach: if (composer.item) composer.item.attach()
                        onFormat: what => { if (composer.item) composer.item.format(what); }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 0

                        FolderPane {
                            Layout.preferredWidth: backend.folderPaneOpen ? Math.round(240 * Math.min(1.3, Theme.textScale)) : 0
                            Layout.fillHeight: true
                            visible: backend.folderPaneOpen
                            onAddAccount: window.startAdding()
                        }

                        MessageList {
                            id: messageList
                            Layout.preferredWidth: window.listWidth
                            Layout.fillHeight: true
                            Layout.leftMargin: backend.folderPaneOpen ? 4 : 6
                        }

                        // Drag to widen or narrow the message list.
                        Item {
                            Layout.preferredWidth: 8
                            Layout.fillHeight: true
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.SplitHCursor
                                property real startX
                                property int startWidth
                                onPressed: mouse => { startX = mapToItem(null, mouse.x, 0).x; startWidth = window.listWidth; }
                                onPositionChanged: mouse => {
                                    if (pressed)
                                        window.listWidth = Math.max(280, Math.min(640, startWidth + mapToItem(null, mouse.x, 0).x - startX));
                                }
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            ReadingPane {
                                anchors.fill: parent
                                visible: backend.compose.mode === undefined
                            }
                            Loader {
                                id: composer
                                anchors.fill: parent
                                active: backend.compose.mode !== undefined
                                sourceComponent: ComposePane { onProblem: text => toast.show(text) }
                            }
                        }
                    }
                }

                PeoplePage {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 6
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 8
                    visible: window.page === "people"
                }
            }
        }

        // Add your account (first start, or "Add account").
        AddAccount {
            id: addAccount
            anchors.fill: parent
            anchors.topMargin: header.height
            visible: window.adding
            onFinished: window.adding = !backend.hasAccounts
            Component.onCompleted: {
                window.adding = !backend.hasAccounts;
                if (window.adding)
                    reset();
            }
        }

        // Messages at the bottom ("Message sent.").
        Rectangle {
            id: toast
            property string text
            function show(value) { text = value; opacity = 1; hideTimer.restart(); }
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 24
            width: Math.min(parent.width - 80, toastText.implicitWidth + 40)
            height: toastText.implicitHeight + 20
            radius: 6
            color: Theme.dark ? "#3D3D3D" : "#242424"
            opacity: 0
            visible: opacity > 0
            Behavior on opacity { enabled: Theme.anim > 0; NumberAnimation { duration: 160 } }
            Text {
                id: toastText
                anchors.centerIn: parent
                width: Math.min(implicitWidth, toast.parent.width - 120)
                text: toast.text
                color: "#FFFFFF"
                font.pixelSize: Theme.fontSize
                wrapMode: Text.Wrap
            }
            Timer { id: hideTimer; interval: 4500; onTriggered: toast.opacity = 0 }
        }

        // The account problem bar (sign-in failed / server unreachable).
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: header.height + 6
            visible: backend.accountError !== "" && !window.adding
            width: Math.min(parent.width - 200, errorText.implicitWidth + 60)
            height: 34
            radius: 6
            color: Theme.warning
            border.width: 1
            border.color: Theme.warningBorder
            RowLayout {
                anchors.centerIn: parent
                spacing: 8
                Glyph { Layout.preferredWidth: 16; Layout.preferredHeight: 16; kind: "warning"; color: Theme.text }
                Text { id: errorText; text: backend.accountError; color: Theme.text; font.pixelSize: Theme.smallFont + 1 }
            }
            TapHandler { onTapped: settings.open() }
        }
    }

    SettingsDialog {
        id: settings
        onAddAccount: window.startAdding()
    }

    Popup {
        id: info
        property string heading
        property string body
        function tell(h, b) { heading = h; body = b; open(); }
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        padding: 24
        Overlay.modal: Scrim {}
        background: Rectangle { radius: 8; color: Theme.card; border.width: 1; border.color: Theme.cardBorder }
        contentItem: ColumnLayout {
            spacing: 14
            Text { text: info.heading; color: Theme.text; font.pixelSize: Math.round(18 * Theme.textScale); font.weight: Font.DemiBold }
            Text { Layout.preferredWidth: 420; text: info.body; color: Theme.text; font.pixelSize: Theme.fontSize; wrapMode: Text.Wrap }
            VButton { Layout.alignment: Qt.AlignRight; primary: true; text: backend.text("ok"); onClicked: info.close() }
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

    // --- Outlook's shortcuts -----------------------------------------------------------
    Shortcut { sequence: "Ctrl+N"; onActivated: backend.newMail() }
    Shortcut { sequence: "Ctrl+R"; enabled: backend.reading.uid !== undefined; onActivated: backend.reply("reply") }
    Shortcut { sequence: "Ctrl+Shift+R"; enabled: backend.reading.uid !== undefined; onActivated: backend.reply("replyAll") }
    Shortcut { sequence: "Ctrl+F"; enabled: backend.reading.uid !== undefined; onActivated: backend.reply("forward") }
    Shortcut { sequence: "Ctrl+Q"; enabled: backend.reading.uid !== undefined; onActivated: backend.toggleRead("", "", 0) }
    Shortcut { sequence: "Ctrl+U"; enabled: backend.reading.uid !== undefined; onActivated: backend.toggleRead("", "", 0) }
    Shortcut { sequence: "Insert"; enabled: backend.reading.uid !== undefined; onActivated: backend.toggleFlag("", "", 0) }
    Shortcut { sequence: "Ctrl+E"; onActivated: header.focusSearch() }
    Shortcut { sequence: "F5"; onActivated: backend.refresh() }
}
