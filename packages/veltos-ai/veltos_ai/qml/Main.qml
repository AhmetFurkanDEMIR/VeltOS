/*
    VeltOS AI: a pane on the right edge of the screen like Windows 11's
    Copilot. It is a layer-shell surface (org.kde.layershell): anchored to
    the top, the bottom and the right, above windows, and it keeps its
    width free (exclusive zone), so maximised windows make room as they did
    for Copilot. Windows + C or the Start entry opens and closes it.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import org.kde.layershell as LayerShell
import "."

Window {
    id: window
    width: Math.round(440 * Math.min(1.25, Theme.textScale))
    height: 760
    visible: false
    title: backend.text("app_title")
    color: Theme.window

    property bool settingsOpen: false
    readonly property bool showSettings: settingsOpen || !backend.ready

    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                               | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.exclusionZone: width
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
    LayerShell.Window.scope: "veltos-ai"

    Connections {
        target: backend
        function onToggleRequested() {
            if (window.visible) {
                window.hide();
            } else {
                window.show();
                window.requestActivate();
                composer.focusInput();
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: window.hide()
    }

    // The pane's left edge.
    Rectangle {
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
        anchors.leftMargin: 1
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
                onClicked: window.settingsOpen = !window.settingsOpen
            }
            IconButton {
                icon: "window-close"
                tip: backend.text("close")
                onClicked: window.hide()
            }
        }

        // --- chat or settings -----------------------------------------------------------------------
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: window.showSettings ? 1 : 0
            ChatView {
                id: chatView
                onSuggestion: text => backend.send(text)
            }
            SettingsView {
                objectName: "settingsView"
                onDone: window.settingsOpen = false
            }
        }

        // --- composer -------------------------------------------------------------------------------
        Rectangle {
            id: composer
            objectName: "composer"
            visible: !window.showSettings
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
            visible: !window.showSettings
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
