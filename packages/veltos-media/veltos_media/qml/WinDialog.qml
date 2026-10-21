// A Windows 11 style message box inside the window: a title, a text and up
// to three buttons (the first is the accent-coloured default), e.g.
// "Save" / "Don't save" / "Cancel".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Popup {
    id: dialog

    property string title
    property string text
    property var buttons: []        // [{text, action}], first = default
    signal chosen(string action)

    function ask(title, text, buttons) {
        dialog.title = title;
        dialog.text = text;
        dialog.buttons = buttons;
        open();
    }

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(480, parent.width - 40)
    modal: true
    padding: 0
    closePolicy: Popup.CloseOnEscape
    Overlay.modal: Rectangle { color: "#40000000" }
    onAboutToHide: if (!picked) dialog.chosen("cancel")
    onAboutToShow: picked = false
    property bool picked: false

    background: Rectangle {
        radius: 8
        color: Theme.card
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
                visible: text !== ""
                text: dialog.text
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: Theme.statusBar
            radius: 8
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 8
                color: Theme.statusBar
            }
            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 8
                Repeater {
                    model: dialog.buttons
                    delegate: Rectangle {
                        id: button
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        radius: 4
                        color: index === 0 ? (tap.pressed ? Qt.darker(Theme.accent, 1.1) : hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                                           : (tap.pressed ? Theme.pressed : hover.hovered ? Theme.hover : Theme.field)
                        border.width: index === 0 ? 0 : 1
                        border.color: Theme.fieldBorder
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData.text
                        Keys.onReturnPressed: activate()
                        function activate() {
                            dialog.picked = true;
                            dialog.close();
                            dialog.chosen(button.modelData.action);
                        }
                        Text {
                            anchors.centerIn: parent
                            text: button.modelData.text
                            color: button.index === 0 ? Theme.accentText : Theme.text
                            font.pixelSize: Theme.fontSize
                        }
                        HoverHandler { id: hover }
                        TapHandler {
                            id: tap
                            onTapped: button.activate()
                        }
                    }
                }
            }
        }
    }
}
