// A Windows 11 style dialog inside the window: title, a message, a form
// (text fields, a choice, a check box, information rows) and two buttons.
// `openWith({title, message, fields, acceptText, rejectText})` shows it;
// `accepted(values)` carries the field values by key.
//   field: {key, label, type: "text"|"number"|"choice"|"check"|"info",
//           value, options: [{value, label}], max, hint}
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Popup {
    id: dialog

    property string title
    property string message
    property var fields: []
    property string acceptText: backend.texts.ok
    property string rejectText: backend.texts.cancel
    property var values: ({})
    // spec.onAccept(values) runs when the first button is pressed.
    property var callback: null
    signal accepted(var values)

    function openWith(spec) {
        title = spec.title || "";
        message = spec.message || "";
        fields = spec.fields || [];
        acceptText = spec.acceptText || backend.texts.ok;
        rejectText = spec.rejectText === undefined ? backend.texts.cancel : spec.rejectText;
        callback = spec.onAccept || null;
        const initial = {};
        for (const field of fields)
            initial[field.key] = field.value;
        values = initial;
        open();
        acceptButton.forceActiveFocus();
    }
    function set(key, value) {
        const next = Object.assign({}, values);
        next[key] = value;
        values = next;
    }

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(520, parent.width - 40)
    modal: true
    padding: 0
    closePolicy: Popup.CloseOnEscape
    Overlay.modal: Rectangle { color: Qt.rgba(0, 0, 0, 0.3) }

    background: Rectangle {
        radius: 8
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
    }

    contentItem: ColumnLayout {
        spacing: 0
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 24
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: dialog.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                visible: text !== ""
                text: dialog.message
                color: Theme.text
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            Repeater {
                model: dialog.fields
                delegate: ColumnLayout {
                    id: field
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 6

                    Text {
                        visible: field.modelData.type !== "check"
                        text: field.modelData.label || ""
                        color: Theme.subtext
                        font.pixelSize: Theme.smallSize
                    }
                    // Information row
                    Text {
                        visible: field.modelData.type === "info"
                        Layout.fillWidth: true
                        text: field.modelData.value || ""
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.WrapAnywhere
                    }
                    // Text or number
                    Rectangle {
                        visible: field.modelData.type === "text" || field.modelData.type === "number"
                        Layout.fillWidth: true
                        implicitHeight: Math.round(32 * Theme.textScale)
                        radius: 4
                        color: Theme.field
                        border.width: 1
                        border.color: input.activeFocus ? Theme.accent : Theme.fieldBorder
                        TextInput {
                            id: input
                            // Like a Windows text box: in the Tab order, the text cursor over it and
                            // (in a layout) the full height of its box. A plain TextInput has neither.
                            activeFocusOnTab: true
                            HoverHandler { cursorShape: Qt.IBeamCursor }
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            verticalAlignment: TextInput.AlignVCenter
                            color: Theme.text
                            selectionColor: Theme.accent
                            selectedTextColor: "#FFFFFF"
                            font.pixelSize: Theme.bodySize
                            clip: true
                            text: field.modelData.value === undefined ? "" : String(field.modelData.value)
                            inputMethodHints: field.modelData.type === "number" ? Qt.ImhDigitsOnly : Qt.ImhNone
                            validator: field.modelData.type === "number"
                                       ? intValidator : null
                            onTextChanged: dialog.set(field.modelData.key,
                                                      field.modelData.type === "number" ? parseInt(text) || 0 : text)
                            IntValidator { id: intValidator; bottom: 1; top: field.modelData.max || 2147483647 }
                        }
                        Rectangle {
                            anchors.bottom: parent.bottom
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.margins: 1
                            height: input.activeFocus ? 2 : 0
                            color: Theme.accent
                        }
                    }
                    Text {
                        visible: field.modelData.type === "number" && !!field.modelData.hint
                        text: field.modelData.hint || ""
                        color: Theme.subtext
                        font.pixelSize: Theme.smallSize
                    }
                    // Choice: one pill per option
                    Flow {
                        visible: field.modelData.type === "choice"
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: field.modelData.type === "choice" ? field.modelData.options : []
                            delegate: Rectangle {
                                id: option
                                required property var modelData
                                readonly property bool chosen: dialog.values[field.modelData.key] === modelData.value
                                width: optionText.implicitWidth + 28
                                height: Math.round(30 * Theme.textScale)
                                radius: height / 2
                                color: chosen ? Theme.accent : (optionHover.hovered ? Theme.rowHover : Theme.control)
                                border.width: chosen ? 0 : 1
                                border.color: Theme.fieldBorder
                                Text {
                                    id: optionText
                                    anchors.centerIn: parent
                                    text: option.modelData.label
                                    color: option.chosen ? "#FFFFFF" : Theme.text
                                    font.pixelSize: Theme.bodySize
                                }
                                HoverHandler { id: optionHover }
                                TapHandler {
                                    gesturePolicy: TapHandler.ReleaseWithinBounds
                                    onTapped: dialog.set(field.modelData.key, option.modelData.value)
                                }
                            }
                        }
                    }
                    // Check box
                    RowLayout {
                        visible: field.modelData.type === "check"
                        spacing: 10
                        Rectangle {
                            id: box
                            readonly property bool checked: dialog.values[field.modelData.key] === true
                            width: 20
                            height: 20
                            radius: 4
                            color: checked ? Theme.accent : Theme.field
                            border.width: checked ? 0 : 1
                            border.color: Theme.fieldBorder
                            Text {
                                anchors.centerIn: parent
                                visible: box.checked
                                text: "✓"
                                color: "#FFFFFF"
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                        Text {
                            text: field.modelData.label || ""
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                        }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: dialog.set(field.modelData.key, !box.checked)
                        }
                    }
                }
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
                                   : (hover.hovered ? Theme.rowHover : Theme.field)
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
                        font.pixelSize: Theme.bodySize
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
                    id: acceptButton
                    objectName: "acceptButton"
                    primary: true
                    label: dialog.acceptText
                    onClicked: {
                        const result = dialog.values, action = dialog.callback;
                        dialog.callback = null;
                        dialog.close();
                        dialog.accepted(result);
                        if (action)
                            action(result);
                    }
                }
                DialogButton {
                    objectName: "rejectButton"
                    visible: dialog.rejectText !== ""
                    label: dialog.rejectText
                    onClicked: dialog.close()
                }
            }
        }
    }
}
