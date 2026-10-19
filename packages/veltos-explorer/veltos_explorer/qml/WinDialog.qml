// A Windows 11 style message box inside the window: title, text and up to
// two buttons (the first one is the accent-coloured default).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Popup {
    id: dialog

    property string title
    property string text
    property string acceptText: backend.text("ok")
    property string rejectText: ""
    property var onAccept: null

    function ask(title, text, acceptText, rejectText, onAccept) {
        dialog.title = title;
        dialog.text = text;
        dialog.acceptText = acceptText;
        dialog.rejectText = rejectText;
        dialog.onAccept = onAccept;
        open();
        acceptButton.forceActiveFocus();
    }
    function tell(text) {
        ask(backend.text("app_title"), text, backend.text("ok"), "", null);
    }

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(460, parent.width - 40)
    modal: true
    padding: 0
    closePolicy: Popup.CloseOnEscape
    Overlay.modal: Rectangle { color: "#40000000" }

    background: Rectangle {
        radius: 8
        color: Theme.content
        border.width: 1
        border.color: Theme.fieldBorder
    }

    contentItem: ColumnLayout {
        spacing: 0
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 24
            spacing: 12
            Text {
                Layout.fillWidth: true
                text: dialog.title
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                text: dialog.text
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: Theme.toolbar
            radius: 8
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 8
                color: Theme.toolbar
            }
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
                    TapHandler { onTapped: button.clicked() }
                }
                DialogButton {
                    id: acceptButton
                    primary: true
                    label: dialog.acceptText
                    onClicked: {
                        const action = dialog.onAccept;
                        dialog.close();
                        if (action)
                            action();
                    }
                }
                DialogButton {
                    visible: dialog.rejectText !== ""
                    label: dialog.rejectText
                    onClicked: dialog.close()
                }
            }
        }
    }
}
