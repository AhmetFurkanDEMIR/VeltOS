/*
    VeltOS AI as a normal window (Start, search: `veltos-ai --window`), with
    the system's title bar; the same conversation as the pane.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import "."

ApplicationWindow {
    id: window
    objectName: "appWindow"
    width: Math.round(560 * Math.min(1.25, Theme.textScale))
    height: 780
    minimumWidth: 420
    minimumHeight: 520
    visible: false
    title: backend.text("app_title")
    color: Theme.window

    onVisibleChanged: if (visible) assistant.focusInput()

    Assistant {
        id: assistant
        anchors.fill: parent
        docked: false
        onCloseRequested: window.close()
    }
}
