/*
    VeltOS Snipping Tool: the frozen, dimmed screen of Windows + Shift + S.

    One window per screen shows that screen's part of the screenshot,
    dimmed; the snipping bar at the top of the first screen picks
    Rectangle, Window, Full screen or Freeform, or closes. Rectangle: drag;
    Window: click the window under the pointer (it is shown undimmed);
    Freeform: draw a shape. Esc cancels. `backend` is app.Snipper; all
    coordinates sent to it are global (desktop) coordinates.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Window
import QtQml.Models

Item {
    id: root
    property bool active: true

    Instantiator {
        model: Qt.application.screens

        delegate: Window {
            id: shot
            required property var modelData
            required property int index

            screen: modelData
            x: modelData.virtualX
            y: modelData.virtualY
            width: modelData.width
            height: modelData.height
            flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            visibility: root.active ? Window.FullScreen : Window.Hidden
            color: "black"
            title: backend.texts.app_title

            property bool dragging: false
            property real startX: 0
            property real startY: 0
            property real endX: 0
            property real endY: 0
            property var freePoints: []
            property int hovered: -1

            readonly property rect clearRect: {
                if (backend.mode === "rect" && dragging) {
                    return Qt.rect(Math.min(startX, endX), Math.min(startY, endY),
                                   Math.abs(endX - startX), Math.abs(endY - startY));
                }
                if (backend.mode === "window" && hovered >= 0 && hovered < backend.windows.length) {
                    const w = backend.windows[hovered];
                    return Qt.rect(w.x - modelData.virtualX, w.y - modelData.virtualY, w.width, w.height);
                }
                return Qt.rect(0, 0, 0, 0);
            }

            Component.onCompleted: requestActivate()

            Image {
                anchors.fill: parent
                source: backend.screenImage(shot.index)
                cache: false
                smooth: true
            }

            // The screen dimmed around the part being snipped.
            Item {
                anchors.fill: parent
                readonly property rect r: shot.clearRect
                Rectangle { x: 0; y: 0; width: parent.width; height: Math.max(0, parent.r.y); color: Theme.dim }
                Rectangle {
                    x: 0
                    y: parent.r.y + parent.r.height
                    width: parent.width
                    height: Math.max(0, parent.height - y)
                    color: Theme.dim
                }
                Rectangle { x: 0; y: parent.r.y; width: Math.max(0, parent.r.x); height: parent.r.height; color: Theme.dim }
                Rectangle {
                    x: parent.r.x + parent.r.width
                    y: parent.r.y
                    width: Math.max(0, parent.width - x)
                    height: parent.r.height
                    color: Theme.dim
                }
                Rectangle {
                    visible: parent.r.width > 0 && parent.r.height > 0
                    x: parent.r.x - 1
                    y: parent.r.y - 1
                    width: parent.r.width + 2
                    height: parent.r.height + 2
                    color: "transparent"
                    border.width: 1
                    border.color: Qt.rgba(1, 1, 1, 0.85)
                }
            }

            // Freeform outline while drawing.
            Canvas {
                id: lasso
                anchors.fill: parent
                visible: backend.mode === "free"
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    const p = shot.freePoints;
                    if (p.length < 4) {
                        return;
                    }
                    ctx.strokeStyle = "white";
                    ctx.lineWidth = 2;
                    ctx.lineJoin = "round";
                    ctx.beginPath();
                    ctx.moveTo(p[0], p[1]);
                    for (let i = 2; i < p.length - 1; i += 2) {
                        ctx.lineTo(p[i], p[i + 1]);
                    }
                    ctx.stroke();
                }
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.CrossCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onPressed: mouse => {
                    if (mouse.button === Qt.RightButton) {
                        backend.cancel();
                        return;
                    }
                    shot.startX = shot.endX = mouse.x;
                    shot.startY = shot.endY = mouse.y;
                    shot.dragging = true;
                    if (backend.mode === "free") {
                        shot.freePoints = [mouse.x, mouse.y];
                        lasso.requestPaint();
                    }
                }
                onPositionChanged: mouse => {
                    if (backend.mode === "window") {
                        shot.hovered = backend.windowAt(mouse.x + shot.modelData.virtualX,
                                                        mouse.y + shot.modelData.virtualY);
                    }
                    if (!shot.dragging) {
                        return;
                    }
                    shot.endX = Math.max(0, Math.min(shot.width, mouse.x));
                    shot.endY = Math.max(0, Math.min(shot.height, mouse.y));
                    if (backend.mode === "free") {
                        shot.freePoints = shot.freePoints.concat([shot.endX, shot.endY]);
                        lasso.requestPaint();
                    }
                }
                onReleased: mouse => {
                    if (!shot.dragging || mouse.button !== Qt.LeftButton) {
                        return;
                    }
                    shot.dragging = false;
                    const gx = shot.modelData.virtualX, gy = shot.modelData.virtualY;
                    if (backend.mode === "rect") {
                        const w = Math.abs(shot.endX - shot.startX), h = Math.abs(shot.endY - shot.startY);
                        if (w >= 2 && h >= 2) {
                            backend.captureRect(Math.min(shot.startX, shot.endX) + gx,
                                                Math.min(shot.startY, shot.endY) + gy, w, h);
                        }
                    } else if (backend.mode === "window") {
                        const index = backend.windowAt(mouse.x + gx, mouse.y + gy);
                        if (index >= 0) {
                            backend.captureWindow(index);
                        } else {
                            backend.captureFull();
                        }
                    } else if (backend.mode === "free") {
                        const global = [];
                        for (let i = 0; i < shot.freePoints.length - 1; i += 2) {
                            global.push(shot.freePoints[i] + gx, shot.freePoints[i + 1] + gy);
                        }
                        shot.freePoints = [];
                        lasso.requestPaint();
                        if (global.length >= 6) {
                            backend.captureFree(global);
                        }
                    }
                }
            }

            // Snipping bar, top centre of the first screen.
            Rectangle {
                id: bar
                visible: shot.index === 0
                anchors.top: parent.top
                anchors.topMargin: 12
                anchors.horizontalCenter: parent.horizontalCenter
                width: modes.implicitWidth + 12
                height: 48
                radius: Theme.radius
                color: Theme.bar
                border.color: Theme.cardBorder

                Row {
                    id: modes
                    anchors.centerIn: parent
                    spacing: 2

                    Repeater {
                        model: [["rect", "mode_rect"], ["window", "mode_window"],
                                ["full", "mode_full"], ["free", "mode_free"]]
                        delegate: BarButton {
                            required property var modelData
                            objectName: "mode-" + modelData[0]
                            width: 44
                            glyph: modelData[0]
                            tip: backend.texts[modelData[1]]
                            checked: backend.mode === modelData[0]
                            onClicked: backend.setMode(modelData[0])
                        }
                    }
                    Rectangle {
                        width: 1
                        height: 24
                        anchors.verticalCenter: parent.verticalCenter
                        color: Theme.cardBorder
                    }
                    BarButton {
                        objectName: "close"
                        width: 44
                        glyph: "close"
                        tip: backend.texts.close
                        onClicked: backend.cancel()
                    }
                }
            }

            Item {
                anchors.fill: parent
                focus: true
                Keys.onEscapePressed: backend.cancel()
            }
        }
    }
}
