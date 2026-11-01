/*
    VeltOS AI's content: the header, the conversation or the settings, and
    the message box. Main.qml shows it in the pane at the right edge (the
    taskbar button, Windows + C); AppWindow.qml in a normal window (Start,
    search). Both share one conversation (`backend`).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Item {
    id: assistant
    objectName: "assistant"

    property bool docked: true
    property bool settingsOpen: false
    readonly property bool showSettings: settingsOpen || !backend.ready
    // A wide window (maximised, full screen) gets a side bar and a wider
    // conversation; one narrow upright column looked lost there (product
    // owner, 2026-11-01).
    readonly property bool wide: !docked && width >= 1000
    readonly property int columnWidth: wide ? Math.min(Math.round(1040 * Math.min(1.25, Theme.textScale)),
                                                       main.width - 96)
                                            : Theme.chatWidth
    signal closeRequested()

    function focusInput() { composer.focusInput(); }

    // The pane's left edge.
    Rectangle {
        visible: assistant.docked
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1
        color: Theme.edge
    }
    // A touch of the VeltOS AI colours at the top, as Copilot's pane had.
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 180
        opacity: Theme.dark ? 0.22 : 0.12
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.brandB }
            GradientStop { position: 1; color: "transparent" }
        }
    }

    // --- side bar (wide windows) ----------------------------------------------------------------
    Rectangle {
        id: sidebar
        objectName: "sidebar"
        visible: assistant.wide
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: visible ? Math.round(280 * Math.min(1.25, Theme.textScale)) : 0
        color: Theme.dark ? "#191A23" : "#ECEFF7"
        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 1
            color: Theme.edge
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 6
            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 12
                spacing: 10
                Kirigami.Icon {
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    source: "veltos-ai"
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("app_title")
                    color: Theme.text
                    font.pixelSize: Theme.headingSize + 2
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
            }
            SideButton {
                objectName: "sideNewChat"
                Layout.fillWidth: true
                icon: "document-new"
                label: backend.text("new_chat")
                enabledState: backend.chat.count > 0
                onClicked: {
                    assistant.settingsOpen = false;
                    backend.newChat();
                }
            }
            Text {
                Layout.topMargin: 16
                Layout.leftMargin: 6
                text: backend.text("try_asking")
                color: Theme.subtext
                font.pixelSize: Theme.captionSize
                font.weight: Font.DemiBold
            }
            Repeater {
                model: ["suggest_dark", "suggest_info", "suggest_bluetooth", "suggest_mail"]
                delegate: SideButton {
                    required property string modelData
                    Layout.fillWidth: true
                    icon: "chat-message-new"
                    label: backend.text(modelData)
                    enabledState: !backend.busy && backend.ready
                    onClicked: {
                        assistant.settingsOpen = false;
                        backend.send(backend.text(modelData));
                    }
                }
            }
            Item { Layout.fillHeight: true }
            SideButton {
                objectName: "sideSettings"
                Layout.fillWidth: true
                icon: "configure"
                label: backend.text("settings")
                active: assistant.showSettings
                onClicked: assistant.settingsOpen = !assistant.settingsOpen
            }
        }
    }

    ColumnLayout {
        id: main
        anchors.left: sidebar.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.leftMargin: assistant.docked ? 1 : 0
        spacing: 0

        // --- header -----------------------------------------------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            Layout.leftMargin: 16
            Layout.rightMargin: 8
            spacing: 8
            Kirigami.Icon {
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                source: "veltos-ai"
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Text {
                    Layout.fillWidth: true
                    text: backend.text("app_title")
                    color: Theme.text
                    font.pixelSize: Theme.headingSize
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Text {
                    objectName: "providerTitle"
                    Layout.fillWidth: true
                    visible: backend.providerTitle !== ""
                    text: backend.providerTitle
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                    elide: Text.ElideRight
                }
            }
            IconButton {
                objectName: "newChat"
                icon: "document-new"
                tip: backend.text("new_chat")
                enabledState: backend.chat.count > 0
                onClicked: backend.newChat()
            }
            IconButton {
                objectName: "settingsButton"
                icon: "configure"
                tip: backend.text("settings")
                // Shown pressed while the settings are open: with no service
                // ready they stay open, and a click seemed to do nothing.
                active: assistant.showSettings
                onClicked: {
                    if (!backend.ready)
                        settingsHint.restart();
                    assistant.settingsOpen = !assistant.settingsOpen;
                }
            }
            IconButton {
                visible: assistant.docked
                icon: "window-close"
                tip: backend.text("close")
                onClicked: assistant.closeRequested()
            }
        }

        // With no service ready the settings stay open: say why when the
        // settings button is pressed.
        Rectangle {
            id: settingsBar
            objectName: "settingsHint"
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.preferredHeight: visible ? hintText.implicitHeight + 16 : 0
            visible: opacity > 0
            opacity: 0
            radius: 6
            color: Theme.dark ? "#2B2F45" : "#E8EEFF"
            Text {
                id: hintText
                anchors.fill: parent
                anchors.margins: 8
                text: backend.text("settings_first")
                color: Theme.text
                font.pixelSize: Theme.captionSize
                wrapMode: Text.Wrap
            }
            SequentialAnimation {
                id: settingsHint
                NumberAnimation { target: settingsBar; property: "opacity"; to: 1; duration: 150 }
                PauseAnimation { duration: 3500 }
                NumberAnimation { target: settingsBar; property: "opacity"; to: 0; duration: 300 }
            }
        }

        // --- chat or settings -----------------------------------------------------------------------
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: assistant.showSettings ? 1 : 0
            ChatView {
                id: chatView
                columnWidth: assistant.columnWidth
                onSuggestion: text => backend.send(text)
            }
            SettingsView {
                objectName: "settingsView"
                onDone: assistant.settingsOpen = false
            }
        }

        // --- composer -------------------------------------------------------------------------------
        Rectangle {
            id: composer
            objectName: "composer"
            visible: !assistant.showSettings
            Layout.fillWidth: true
            Layout.maximumWidth: assistant.columnWidth - 28
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 14
            Layout.rightMargin: 14
            Layout.topMargin: 6
            Layout.preferredHeight: Math.min(160, Math.max(52, input.contentHeight + 30))
            radius: 12
            color: Theme.field
            border.width: 1
            border.color: input.activeFocus ? Theme.accent : Theme.fieldBorder
            function focusInput() { input.forceActiveFocus(); }
            function submit() {
                const text = input.text.trim();
                if (text === "" || backend.busy)
                    return;
                backend.send(text);
                input.text = "";
            }

            Flickable {
                id: inputScroll
                anchors.left: parent.left
                anchors.right: sendButton.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 12
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                contentWidth: width
                contentHeight: input.contentHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                // The line being written stays in view once the box is at
                // its tallest.
                function ensureVisible(r) {
                    if (contentY >= r.y)
                        contentY = r.y;
                    else if (contentY + height <= r.y + r.height)
                        contentY = r.y + r.height - height;
                }
                TextEdit {
                    id: input
                    objectName: "input"
                    width: inputScroll.width
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    selectionColor: Theme.accent
                    textFormat: TextEdit.PlainText
                    Keys.onReturnPressed: event => {
                        if (event.modifiers & Qt.ShiftModifier)
                            event.accepted = false;
                        else
                            composer.submit();
                    }
                    Keys.onEnterPressed: composer.submit()
                    onTextChanged: if (length > 4000) remove(4000, length)
                    onCursorRectangleChanged: inputScroll.ensureVisible(cursorRectangle)
                    Text {
                        anchors.fill: parent
                        visible: input.text === "" && !input.preeditText
                        text: backend.text("ask")
                        color: Theme.faint
                        font.pixelSize: Theme.bodySize
                    }
                    Accessible.role: Accessible.EditableText
                    Accessible.name: backend.text("ask")
                }
            }
            Rectangle {
                id: sendButton
                objectName: "sendButton"
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 8
                width: 34
                height: 34
                radius: 17
                readonly property bool stopping: backend.busy
                readonly property bool active: stopping || input.text.trim() !== ""
                color: active ? Theme.accent : "transparent"
                Accessible.role: Accessible.Button
                Accessible.name: stopping ? backend.text("stop") : backend.text("send")
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 16
                    height: 16
                    isMask: true
                    color: sendButton.active ? Theme.accentText : Theme.faint
                    source: sendButton.stopping ? "media-playback-stop" : "document-send"
                }
                TapHandler {
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: sendButton.stopping ? backend.stop() : composer.submit()
                }
                HoverHandler { id: sendHover }
                ToolTip.visible: sendHover.hovered
                ToolTip.delay: 500
                ToolTip.text: Accessible.name
            }
        }
        RowLayout {
            visible: !assistant.showSettings
            Layout.fillWidth: true
            Layout.maximumWidth: assistant.columnWidth - 36
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 18
            Layout.rightMargin: 18
            Layout.topMargin: 4
            Layout.bottomMargin: 10
            Text {
                Layout.fillWidth: true
                text: backend.text("privacy_note")
                color: Theme.faint
                font.pixelSize: Theme.captionSize
                elide: Text.ElideRight
            }
            Text {
                text: input.length + "/4000"
                color: Theme.faint
                font.pixelSize: Theme.captionSize
            }
        }
    }
}
