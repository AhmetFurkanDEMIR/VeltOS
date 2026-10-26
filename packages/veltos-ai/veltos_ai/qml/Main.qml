/*
    VeltOS AI: a pane on the right edge of the screen like Windows 11's
    Copilot. It is a layer-shell surface (org.kde.layershell): anchored to
    the top, the bottom and the right, above windows, and it keeps its
    width free (exclusive zone), so maximised windows make room as they did
    for Copilot. Windows + C and the taskbar button open and close it (the
    backend calls toggle()); Start and search open AppWindow.qml instead.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Window
import org.kde.layershell as LayerShell
import "."

Window {
    id: window
    width: Math.round(440 * Math.min(1.25, Theme.textScale))
    height: 760
    visible: false
    title: backend.text("app_title")
    color: Theme.window

    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                               | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerTop
    LayerShell.Window.exclusionZone: width
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
    LayerShell.Window.scope: "veltos-ai"

    function toggle() {
        if (window.visible) {
            window.hide();
        } else {
            window.show();
            window.requestActivate();
            assistant.focusInput();
        }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: window.hide()
    }

    Assistant {
        id: assistant
        anchors.fill: parent
        docked: true
        onCloseRequested: window.hide()
    }
}
