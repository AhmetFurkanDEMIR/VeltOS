/*
    Windows 11's copy window (`backend` is transferwindow.TransferBackend):
    "37% complete", what goes from where to where, the bar with Pause and
    Cancel, and with "More details" the speed graph, the name, the time and
    the items remaining. A conflict asks "Replace or Skip Files"; errors
    stay with Close.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    width: 480
    height: column.implicitHeight
    minimumWidth: 480
    maximumWidth: 480
    minimumHeight: column.implicitHeight
    maximumHeight: column.implicitHeight
    visible: false
    title: backend.finished && backend.failed ? backend.text("transfer_errors_title") : backend.title
    color: Theme.content

    component DialogButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        signal clicked()
        implicitWidth: Math.max(96, buttonText.implicitWidth + 32)
        implicitHeight: 32
        radius: 5
        color: primary ? (hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                       : (hover.hovered ? Theme.hover : Theme.field)
        border.width: primary ? 0 : 1
        border.color: Theme.fieldBorder
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: label
        Keys.onReturnPressed: clicked()
        Keys.onSpacePressed: clicked()
        Text {
            id: buttonText
            anchors.centerIn: parent
            text: button.label
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.fontSize
        }
        HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
        TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    // A round icon button beside the bar (Pause, Cancel).
    component RoundButton: Rectangle {
        id: round
        property string iconName
        property string tip
        signal clicked()
        width: 32
        height: 32
        radius: 16
        color: roundTap.pressed ? Theme.pressed : roundHover.hovered ? Theme.hover : "transparent"
        Accessible.role: Accessible.Button
        Accessible.name: tip
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 16
            height: 16
            source: round.iconName
            isMask: true
            color: Theme.text
        }
        HoverHandler { id: roundHover; cursorShape: Qt.PointingHandCursor }
        TapHandler { id: roundTap; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: round.clicked() }
        ToolTip.visible: roundHover.hovered
        ToolTip.delay: 500
        ToolTip.text: tip
    }

    Shortcut { sequence: "Escape"; onActivated: backend.finished ? Qt.quit() : backend.cancel() }
    onClosing: if (!backend.finished) backend.cancel()

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 0

        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 22
            spacing: 10

            Text {
                Layout.fillWidth: true
                text: backend.heading
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
                visible: !(backend.finished && backend.failed)
            }

            // The bar (and in details, the speed graph) with Pause and Cancel.
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: !backend.finished
                Rectangle {
                    id: area
                    Layout.fillWidth: true
                    Layout.preferredHeight: backend.details ? 84 : 26
                    radius: 4
                    color: Theme.field
                    border.width: 1
                    border.color: Theme.fieldBorder
                    clip: true
                    Behavior on Layout.preferredHeight { NumberAnimation { duration: 150 } }

                    // Done part, in Windows' green.
                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.margins: 1
                        width: (parent.width - 2) * backend.percent / 100
                        color: backend.paused ? "#E8B02A" : "#06B025"
                        opacity: backend.details ? 0.18 : 1
                        Behavior on width { NumberAnimation { duration: 140 } }
                    }
                    // The speed over the time so far, as a filled line.
                    Canvas {
                        id: graph
                        anchors.fill: parent
                        visible: backend.details
                        property var points: backend.graph
                        onPointsChanged: requestPaint()
                        onPaint: {
                            const ctx = getContext("2d");
                            ctx.reset();
                            const n = points.length;
                            if (n < 2)
                                return;
                            const doneWidth = (width - 2) * backend.percent / 100;
                            ctx.beginPath();
                            ctx.moveTo(1, height - 1);
                            for (let i = 0; i < n; ++i)
                                ctx.lineTo(1 + doneWidth * i / (n - 1), height - 4 - (height - 12) * points[i]);
                            ctx.lineTo(1 + doneWidth, height - 1);
                            ctx.closePath();
                            ctx.fillStyle = Qt.rgba(0.024, 0.69, 0.145, 0.55);
                            ctx.fill();
                        }
                    }
                    Text {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 6
                        visible: backend.details && backend.speedText !== ""
                        text: backend.speedText
                        color: Theme.text
                        font.pixelSize: Theme.fontSize - 1
                    }
                }
                RoundButton {
                    objectName: "pauseButton"
                    iconName: backend.paused ? "media-playback-start-symbolic" : "media-playback-pause-symbolic"
                    tip: backend.paused ? backend.text("transfer_resume") : backend.text("transfer_pause")
                    onClicked: backend.togglePause()
                }
                RoundButton {
                    objectName: "cancelButton"
                    iconName: "window-close-symbolic"
                    tip: backend.text("cancel")
                    onClicked: backend.cancel()
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                visible: backend.details && !backend.finished
                Text { text: backend.name; color: Theme.text; font.pixelSize: Theme.fontSize; elide: Text.ElideMiddle; Layout.fillWidth: true }
                Text { text: backend.remaining; color: Theme.text; font.pixelSize: Theme.fontSize }
                Text { text: backend.itemsLeft; color: Theme.text; font.pixelSize: Theme.fontSize }
            }

            // "Replace or Skip Files".
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                visible: backend.conflict
                Text {
                    text: backend.text("transfer_replace_or_skip")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize + 4
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.conflictText
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.WordWrap
                }
                Repeater {
                    model: [["replace", "transfer_replace", "checkmark-symbolic"], ["skip", "transfer_skip", "go-next-skip-symbolic"]]
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 44
                        radius: 5
                        color: choiceHover.hovered ? Theme.hover : Theme.field
                        border.width: 1
                        border.color: Theme.fieldBorder
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.text(modelData[1])
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            spacing: 12
                            Kirigami.Icon {
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                source: modelData[2]
                                isMask: true
                                color: Theme.accent
                            }
                            Text {
                                Layout.fillWidth: true
                                text: backend.text(modelData[1])
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                            }
                        }
                        HoverHandler { id: choiceHover; cursorShape: Qt.PointingHandCursor }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: backend.answer(modelData[0], forAll.checked)
                        }
                    }
                }
                CheckBox {
                    id: forAll
                    text: backend.text("transfer_for_all")
                }
            }

            // Errors at the end.
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                visible: backend.finished && backend.failed
                Text {
                    text: backend.text("transfer_errors_title")
                    color: Theme.text
                    font.pixelSize: Theme.fontSize + 4
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.errorText
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            color: Theme.toolbar
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 20
                spacing: 8
                // "More details" / "Fewer details", a chevron and a link.
                Rectangle {
                    visible: !backend.finished
                    Layout.preferredHeight: 32
                    Layout.preferredWidth: detailsRow.implicitWidth + 16
                    radius: 5
                    color: detailsHover.hovered ? Theme.hover : "transparent"
                    Accessible.role: Accessible.Button
                    Accessible.name: detailsLabel.text
                    RowLayout {
                        id: detailsRow
                        anchors.centerIn: parent
                        spacing: 8
                        Kirigami.Icon {
                            Layout.preferredWidth: 12
                            Layout.preferredHeight: 12
                            source: backend.details ? "arrow-up" : "arrow-down"
                            isMask: true
                            color: Theme.text
                        }
                        Text {
                            id: detailsLabel
                            text: backend.details ? backend.text("transfer_fewer") : backend.text("transfer_more")
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                        }
                    }
                    HoverHandler { id: detailsHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: backend.toggleDetails() }
                }
                Item { Layout.fillWidth: true }
                DialogButton {
                    visible: backend.finished
                    primary: true
                    label: backend.text("close")
                    onClicked: Qt.quit()
                }
            }
        }
    }
}
