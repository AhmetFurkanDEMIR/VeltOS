// Choose your AI: the local model (free, offline: LocalModels.qml) or a
// service with its API key, the model (from the service's own list) and,
// for Azure OpenAI, the endpoint and deployment; whether VeltOS AI may act
// on the computer.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: view
    signal done()
    property string chosen: backend.provider !== "" ? backend.provider : "local"
    readonly property bool isLocal: chosen === "local"
    readonly property var service: backend.services.find(s => s.id === chosen) || ({})
    contentWidth: width
    contentHeight: column.implicitHeight + 32
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}

    function fill() {
        const entry = backend.services.find(s => s.id === chosen) || {};
        keyField.text = "";
        modelField.text = entry.model || "";
        endpointField.text = entry.endpoint || "";
    }
    onChosenChanged: fill()
    Component.onCompleted: fill()

    component Field: Rectangle {
        id: field
        property alias text: input.text
        property alias echoMode: input.echoMode
        property string placeholder
        property alias input: input
        Layout.fillWidth: true
        implicitHeight: 34
        radius: 5
        color: Theme.field
        border.width: 1
        border.color: input.activeFocus ? Theme.accent : Theme.fieldBorder
        TextInput {
            id: input
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.text
            font.pixelSize: Theme.bodySize
            selectByMouse: true
            clip: true
            selectionColor: Theme.accent
            Text {
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                visible: input.text === ""
                text: field.placeholder
                color: Theme.faint
                font.pixelSize: Theme.bodySize
                elide: Text.ElideRight
            }
        }
    }

    ColumnLayout {
        id: column
        x: 20
        y: 16
        width: view.width - 40
        spacing: 10

        Text {
            text: backend.text("setup_title")
            color: Theme.text
            font.pixelSize: Theme.titleSize
            font.weight: Font.DemiBold
        }
        Text {
            Layout.fillWidth: true
            text: backend.text("setup_desc")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.topMargin: 6
            text: backend.text("provider")
            color: Theme.text
            font.pixelSize: Theme.bodySize
            font.weight: Font.DemiBold
        }
        Repeater {
            model: backend.services
            delegate: Rectangle {
                id: option
                required property var modelData
                readonly property bool selected: view.chosen === modelData.id
                Layout.fillWidth: true
                Layout.preferredHeight: 42
                radius: 5
                color: selected ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.12)
                                : (optionHover.hovered ? Theme.hover : "transparent")
                Accessible.role: Accessible.RadioButton
                Accessible.name: modelData.title
                Accessible.checked: selected
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 10
                    Rectangle {
                        width: 18
                        height: 18
                        radius: 9
                        color: option.selected ? Theme.accent : "transparent"
                        border.width: option.selected ? 0 : 1.5
                        border.color: Theme.faint
                        Rectangle {
                            visible: option.selected
                            anchors.centerIn: parent
                            width: 7
                            height: 7
                            radius: 3.5
                            color: "#FFFFFF"
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: option.modelData.title
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                    Text {
                        visible: option.modelData.hasKey || (option.modelData.id === "local" && backend.localModels.length > 0)
                        text: "✓"
                        color: Theme.success
                        font.pixelSize: Theme.bodySize
                    }
                }
                HoverHandler { id: optionHover }
                TapHandler {
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: view.chosen = option.modelData.id
                }
            }
        }

        Text {
            visible: view.chosen === "copilot"
            Layout.fillWidth: true
            text: backend.text("copilot_note")
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
            wrapMode: Text.WordWrap
        }

        LocalModels {
            objectName: "localModels"
            visible: view.isLocal
            Layout.fillWidth: true
            Layout.topMargin: 6
        }
        VButton {
            visible: view.isLocal && backend.ready
            Layout.topMargin: 4
            primary: true
            text: backend.text("start_chat")
            onClicked: view.done()
        }

        RowLayout {
            visible: !view.isLocal
            Layout.topMargin: 6
            Text {
                Layout.fillWidth: true
                text: backend.text("api_key")
                color: Theme.text
                font.pixelSize: Theme.bodySize
                font.weight: Font.DemiBold
            }
            Text {
                text: backend.text("get_key")
                color: Theme.accent
                font.pixelSize: Theme.captionSize + 1
                font.underline: keyLinkHover.hovered
                HoverHandler { id: keyLinkHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: backend.openUrl(view.service.keyUrl || "") }
            }
        }
        Field {
            id: keyField
            objectName: "keyField"
            visible: !view.isLocal
            echoMode: TextInput.Password
            placeholder: view.service.hasKey ? backend.text("key_saved") + " " + view.service.keyHint
                                             : backend.text("api_key_placeholder")
        }

        Text {
            visible: view.chosen === "copilot"
            text: backend.text("endpoint")
            color: Theme.text
            font.pixelSize: Theme.bodySize
            font.weight: Font.DemiBold
        }
        Field {
            id: endpointField
            visible: view.chosen === "copilot"
            placeholder: backend.text("endpoint_placeholder")
        }

        RowLayout {
            visible: !view.isLocal
            Layout.topMargin: 6
            Text {
                Layout.fillWidth: true
                text: view.chosen === "copilot" ? backend.text("deployment") : backend.text("model")
                color: Theme.text
                font.pixelSize: Theme.bodySize
                font.weight: Font.DemiBold
            }
            Text {
                visible: view.chosen !== "copilot"
                text: backend.modelsBusy ? backend.text("loading_models") : backend.text("load_models")
                color: Theme.accent
                font.pixelSize: Theme.captionSize + 1
                font.underline: modelsHover.hovered
                HoverHandler { id: modelsHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: backend.loadModels(view.chosen, keyField.text, endpointField.text) }
            }
        }
        Field {
            id: modelField
            objectName: "modelField"
            visible: !view.isLocal
        }
        Text {
            visible: backend.modelsError !== ""
            Layout.fillWidth: true
            text: backend.modelsError
            color: Theme.danger
            font.pixelSize: Theme.captionSize
            wrapMode: Text.WordWrap
        }
        Flow {
            Layout.fillWidth: true
            spacing: 6
            visible: backend.models.length > 0 && !view.isLocal
            Repeater {
                model: backend.models.slice(0, 24)
                delegate: Rectangle {
                    id: modelChip
                    required property string modelData
                    width: modelText.implicitWidth + 20
                    height: 28
                    radius: 14
                    color: modelField.text === modelData ? Theme.accent : (chipHover.hovered ? Theme.hover : Theme.card)
                    border.width: 1
                    border.color: Theme.cardBorder
                    Text {
                        id: modelText
                        anchors.centerIn: parent
                        text: modelChip.modelData
                        color: modelField.text === modelChip.modelData ? Theme.accentText : Theme.text
                        font.pixelSize: Theme.captionSize
                    }
                    HoverHandler { id: chipHover }
                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: modelField.text = modelChip.modelData
                    }
                }
            }
        }

        RowLayout {
            visible: !view.isLocal
            Layout.topMargin: 8
            spacing: 10
            Switch {
                id: actionsSwitch
                checked: backend.actionsAllowed
                onToggled: backend.setActionsAllowed(checked)
            }
            Text {
                Layout.fillWidth: true
                text: backend.text("allow_actions")
                color: Theme.text
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }

        Text {
            visible: !view.isLocal
            Layout.fillWidth: true
            Layout.topMargin: 4
            text: backend.text("key_note")
            color: Theme.faint
            font.pixelSize: Theme.captionSize
            wrapMode: Text.WordWrap
        }

        RowLayout {
            visible: !view.isLocal
            Layout.topMargin: 8
            spacing: 8
            VButton {
                objectName: "saveButton"
                primary: true
                text: backend.text("save")
                enabledState: keyField.text !== "" || view.service.hasKey
                onClicked: {
                    backend.saveService(view.chosen, keyField.text, modelField.text, endpointField.text);
                    keyField.text = "";
                    view.done();
                }
            }
            VButton {
                visible: backend.ready
                text: backend.text("cancel")
                onClicked: view.done()
            }
            Item { Layout.fillWidth: true }
            VButton {
                visible: view.service.hasKey === true
                text: backend.text("remove_key")
                onClicked: backend.removeKey(view.chosen)
            }
        }
    }
}
