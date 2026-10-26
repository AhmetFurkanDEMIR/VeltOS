/*
    "Empty Recycle Bin" asked from the desktop (the Recycle Bin icon's menu,
    veltos-desktop) and "Delete File" (the desktop's Shift+Delete):
    Windows 11's question in a small window of its own; Yes empties the bin
    or deletes the items (`backend` is app.EmptyBinBackend). File Explorer
    asks the same inside its window (WinDialog.qml).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ApplicationWindow {
    id: window

    // A fixed size, like Windows' question: KWin then offers no maximize
    // button (the window flags below are not passed on by Wayland; the
    // title bar kept minimize and maximize with them alone, VM 2026-10-22).
    width: 460
    height: column.implicitHeight
    minimumWidth: 460
    maximumWidth: 460
    minimumHeight: column.implicitHeight
    maximumHeight: column.implicitHeight
    visible: true
    title: backend.heading
    color: Theme.content
    flags: Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    function answer(yes) {
        if (yes)
            backend.confirm();
        Qt.quit();
    }

    Shortcut { sequence: "Escape"; onActivated: window.answer(false) }

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 0

        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 24
            spacing: 12
            Text {
                Layout.fillWidth: true
                text: backend.heading
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                text: backend.question
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: Theme.toolbar
            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 8
                component DialogButton: Rectangle {
                    id: button
                    property string label
                    property bool primary: false
                    signal clicked()
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
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
                        anchors.centerIn: parent
                        text: button.label
                        color: button.primary ? "#FFFFFF" : Theme.text
                        font.pixelSize: Theme.fontSize
                    }
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: -3
                        radius: 8
                        color: "transparent"
                        border.width: 2
                        border.color: Theme.text
                        visible: button.activeFocus
                    }
                    HoverHandler { id: hover }
                    TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
                }
                DialogButton {
                    id: yesButton
                    objectName: "yesButton"
                    primary: true
                    label: backend.text("yes")
                    focus: true
                    onClicked: window.answer(true)
                    Component.onCompleted: forceActiveFocus()
                }
                DialogButton {
                    objectName: "noButton"
                    label: backend.text("no")
                    onClicked: window.answer(false)
                }
            }
        }
    }
}
