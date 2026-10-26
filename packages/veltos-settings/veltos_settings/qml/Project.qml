/*
    Windows + P: Windows 11's Project flyout at the bottom right, above the
    taskbar (a layer-shell surface): PC screen only, Duplicate, Extend,
    Second screen only as tiles, the current one marked. Arrow keys and
    Windows + P again move the choice, Enter or a click applies it, Escape
    or a click elsewhere closes the flyout. `backend` is project.ProjectBackend.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import org.kde.layershell as LayerShell

Window {
    id: flyout
    width: 392
    height: card.implicitHeight + 24
    visible: false
    color: "transparent"
    title: backend.text("project")

    readonly property bool dark: backend.darkMode
    readonly property color accent: backend.accent !== "" ? (dark ? Qt.lighter(backend.accent, 1.35) : backend.accent)
                                                          : (dark ? "#6E95FF" : "#2F5EE6")
    readonly property color surface: dark ? "#272934" : "#F7F8FB"
    readonly property color tile: dark ? "#33364A" : "#FFFFFF"
    readonly property color tileHover: dark ? "#3B3F55" : "#F0F2F8"
    readonly property color text: dark ? "#F2F3F7" : "#1B1D24"
    readonly property color subtext: dark ? "#AEB3C5" : "#5D6475"
    readonly property color edge: dark ? "#3A3D50" : "#DADFE8"
    property int highlighted: Math.max(0, backend.modes.findIndex(m => m.key === backend.current))
    property bool seen: false

    LayerShell.Window.anchors: LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorRight
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
    LayerShell.Window.scope: "veltos-project"

    // A click elsewhere takes the focus away: the flyout closes, as on Windows.
    onActiveChanged: {
        if (active)
            seen = true;
        else if (seen)
            Qt.quit();
    }

    Connections {
        target: backend
        function onAdvance() { flyout.highlighted = (flyout.highlighted + 1) % backend.modes.length; }
    }

    // Windows 11's Project glyphs: always two line-drawn monitors on stands,
    // so every tile is symmetric (product owner, 2026-10-27: PC screen only
    // showed one monitor off to the left), the picture filled in where it
    // is shown: the first screen (PC screen only), both (Duplicate), one
    // picture across both and the gap (Extend), the second (Second screen
    // only).
    component Monitor: Item {
        id: monitor
        property color ink
        property bool shown
        width: 34
        height: 32
        Rectangle {
            id: frame
            width: parent.width
            height: 23
            radius: 3
            color: "transparent"
            border.width: 1.5
            border.color: monitor.ink
        }
        Rectangle {
            visible: monitor.shown
            x: 3.5
            y: 3.5
            width: frame.width - 7
            height: frame.height - 7
            radius: 1.5
            color: monitor.ink
        }
        Rectangle {
            x: (parent.width - width) / 2
            y: frame.height
            width: 1.5
            height: 4
            color: monitor.ink
        }
        Rectangle {
            x: (parent.width - width) / 2
            y: frame.height + 4
            width: 14
            height: 1.5
            radius: 0.75
            color: monitor.ink
        }
    }
    component Screens: Item {
        id: screens
        property string kind
        property color ink
        implicitWidth: 80
        implicitHeight: 32
        // Extend: one picture across both screens and the gap between them.
        Rectangle {
            visible: screens.kind === "extend"
            x: 3.5
            y: 3.5
            width: screens.implicitWidth - 7
            height: 16
            radius: 1.5
            color: screens.ink
        }
        Monitor {
            x: 0
            ink: screens.ink
            shown: screens.kind === "pc" || screens.kind === "duplicate"
        }
        Monitor {
            x: screens.implicitWidth - width
            ink: screens.ink
            shown: screens.kind === "second" || screens.kind === "duplicate"
        }
    }

    Rectangle {
        id: card
        anchors.fill: parent
        anchors.margins: 12
        implicitHeight: column.implicitHeight + 32
        radius: 8
        color: flyout.surface
        border.width: 1
        border.color: flyout.edge

        ColumnLayout {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 16
            spacing: 12
            Text {
                text: backend.text("project")
                color: flyout.text
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Text {
                visible: backend.count < 2
                Layout.fillWidth: true
                text: backend.text("one_display")
                color: flyout.subtext
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 8
                rowSpacing: 8
                Repeater {
                    model: backend.modes
                    delegate: Rectangle {
                        id: tile
                        required property var modelData
                        required property int index
                        readonly property bool current: backend.current === modelData.key
                        readonly property bool focused: flyout.highlighted === index
                        objectName: "mode-" + modelData.key
                        Layout.fillWidth: true
                        Layout.preferredHeight: 92
                        radius: 6
                        color: current ? flyout.accent : (tileHover.hovered || focused ? flyout.tileHover : flyout.tile)
                        border.width: focused ? 2 : 1
                        border.color: focused ? (current ? Qt.lighter(flyout.accent, 1.4) : flyout.accent) : flyout.edge
                        opacity: backend.count < 2 && modelData.key !== "pc" ? 0.5 : 1
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.title
                        Accessible.checked: current
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            Screens {
                                Layout.alignment: Qt.AlignHCenter
                                kind: tile.modelData.key
                                ink: tile.current ? "#FFFFFF" : flyout.text
                            }
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: tile.modelData.title
                                color: tile.current ? "#FFFFFF" : flyout.text
                                font.pixelSize: 12
                            }
                        }
                        HoverHandler { id: tileHover }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: backend.choose(tile.modelData.key)
                        }
                    }
                }
            }
            Text {
                text: backend.text("display_settings")
                color: flyout.accent
                font.pixelSize: 12
                font.underline: linkHover.hovered
                HoverHandler { id: linkHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: backend.openSettings() }
            }
        }
    }

    Item {
        focus: true
        Keys.onPressed: event => {
            const count = backend.modes.length;
            if (event.key === Qt.Key_Escape) {
                Qt.quit();
            } else if (event.key === Qt.Key_Right || event.key === Qt.Key_Down || event.key === Qt.Key_P
                       || event.key === Qt.Key_Tab) {
                flyout.highlighted = (flyout.highlighted + 1) % count;
            } else if (event.key === Qt.Key_Left || event.key === Qt.Key_Up || event.key === Qt.Key_Backtab) {
                flyout.highlighted = (flyout.highlighted + count - 1) % count;
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
                backend.choose(backend.modes[flyout.highlighted].key);
            } else {
                return;
            }
            event.accepted = true;
        }
    }
}
