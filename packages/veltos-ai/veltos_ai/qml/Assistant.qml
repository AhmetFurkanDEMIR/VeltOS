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

    ColumnLayout {
        anchors.fill: parent
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
                    text: backend.text("app_title")
                    color: Theme.text
                    font.pixelSize: Theme.headingSize
                    font.weight: Font.DemiBold
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
                enabledState: backend.messages.length > 0
                onClicked: backend.newChat()
            }
            IconButton {
                objectName: "settingsButton"
                icon: "configure"
                tip: backend.text("settings")
                onClicked: assistant.settingsOpen = !assistant.settingsOpen
            }
            IconButton {
                visible: assistant.docked
                icon: "window-close"
                tip: backend.text("close")
                onClicked: assistant.closeRequested()
            }
        }

        // --- chat or settings -----------------------------------------------------------------------
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: assistant.showSettings ? 1 : 0
            ChatView {
                id: chatView
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
