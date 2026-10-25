// The conversation: the greeting with suggestions while it is empty, then
// the user's messages (right, accent), the answers (left, Markdown, copy),
// the actions VeltOS AI asks to run (Allow / Don't allow) and errors.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Item {
    id: chat
    signal suggestion(string text)

    // --- greeting -----------------------------------------------------------------------------------
    ColumnLayout {
        objectName: "greeting"
        visible: backend.messages.length === 0
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.margins: 20
        spacing: 14

        Kirigami.Icon {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            source: "veltos-ai"
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: backend.text("greeting")
            color: Theme.text
            font.pixelSize: Theme.titleSize
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: backend.text("greeting_desc")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
            wrapMode: Text.WordWrap
        }
        Repeater {
            model: ["suggest_dark", "suggest_info", "suggest_bluetooth", "suggest_mail"]
            delegate: Rectangle {
                id: chip
                required property string modelData
                Layout.fillWidth: true
                Layout.preferredHeight: chipText.implicitHeight + 22
                radius: Theme.radius
                color: chipHover.hovered ? Theme.cardHover : Theme.card
                border.width: 1
                border.color: Theme.cardBorder
                Text {
                    id: chipText
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    verticalAlignment: Text.AlignVCenter
                    text: backend.text(chip.modelData)
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
                HoverHandler { id: chipHover }
                TapHandler {
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: chat.suggestion(backend.text(chip.modelData))
                }
            }
        }
    }

    // --- messages -----------------------------------------------------------------------------------
    ListView {
        id: list
        objectName: "messages"
        anchors.fill: parent
        visible: backend.messages.length > 0
        clip: true
        spacing: 12
        topMargin: 12
        bottomMargin: 12
        boundsBehavior: Flickable.StopAtBounds
        model: backend.messages
        ScrollBar.vertical: ScrollBar {}
        onCountChanged: Qt.callLater(positionViewAtEnd)
        onContentHeightChanged: if (atYEnd || backend.busy) Qt.callLater(positionViewAtEnd)

        delegate: Item {
            id: row
            required property var modelData
            required property int index
            width: ListView.view.width
            height: loader.item ? loader.item.implicitHeight : 0
            Loader {
                id: loader
                width: parent.width
                sourceComponent: row.modelData.kind === "user" ? userBubble
                               : row.modelData.kind === "assistant" ? answer
                               : row.modelData.kind === "action" ? action : problem
                property var message: row.modelData
            }
        }
    }

    Component {
        id: userBubble
        Item {
            readonly property var message: parent && parent.message ? parent.message : ({})
            implicitHeight: bubble.height
            Rectangle {
                id: bubble
                anchors.right: parent.right
                anchors.rightMargin: 16
                width: Math.min(parent.width * 0.85, userText.implicitWidth + 28)
                height: userText.implicitHeight + 20
                radius: Theme.bubbleRadius
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: Theme.accent }
                    GradientStop { position: 1; color: Qt.darker(Theme.accent, 1.08) }
                }
                TextEdit {
                    id: userText
                    x: 14
                    y: 10
                    width: Math.min(implicitWidth, bubble.parent.width * 0.85 - 28)
                    text: message.text
                    color: Theme.accentText
                    font.pixelSize: Theme.bodySize
                    wrapMode: TextEdit.Wrap
                    readOnly: true
                    selectByMouse: true
                    selectionColor: Qt.darker(Theme.accent, 1.4)
                }
            }
        }
    }

    Component {
        id: answer
        Item {
            readonly property var message: parent && parent.message ? parent.message : ({})
            implicitHeight: card.height + copyRow.height
            Rectangle {
                id: card
                anchors.left: parent.left
                anchors.leftMargin: 16
                width: parent.width - 32
                height: answerColumn.implicitHeight + 24
                radius: Theme.bubbleRadius
                color: Theme.card
                border.width: 1
                border.color: Theme.cardBorder
                Column {
                    id: answerColumn
                    x: 14
                    y: 12
                    width: card.width - 28
                    spacing: 6
                    Row {
                        spacing: 8
                        visible: message.state === "streaming" && message.text === ""
                        BusyIndicator { width: 18; height: 18; running: parent.visible }
                        Text {
                            text: backend.text("thinking")
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    TextEdit {
                        width: parent.width
                        visible: message.text !== ""
                        text: message.text
                        textFormat: message.state === "refused" ? TextEdit.PlainText : TextEdit.MarkdownText
                        color: message.state === "refused" ? Theme.subtext : Theme.text
                        font.pixelSize: Theme.bodySize
                        wrapMode: TextEdit.Wrap
                        readOnly: true
                        selectByMouse: true
                        selectionColor: Theme.accent
                        selectedTextColor: Theme.accentText
                        onLinkActivated: link => backend.openUrl(link)
                        HoverHandler {
                            cursorShape: parent.hoveredLink !== "" ? Qt.PointingHandCursor : Qt.IBeamCursor
                        }
                    }
                }
            }
            Row {
                id: copyRow
                anchors.top: card.bottom
                anchors.left: card.left
                anchors.topMargin: 2
                height: visible ? 30 : 0
                visible: message.state === "" && message.text !== ""
                IconButton {
                    width: 28
                    height: 28
                    icon: "edit-copy"
                    tip: backend.text("copy")
                    onClicked: backend.copyText(message.text)
                }
            }
        }
    }

    Component {
        id: action
        Item {
            readonly property var message: parent && parent.message ? parent.message : ({})
            implicitHeight: actionCard.height
            Rectangle {
                id: actionCard
                anchors.left: parent.left
                anchors.leftMargin: 16
                width: parent.width - 32
                height: actionColumn.implicitHeight + 24
                radius: Theme.radius
                color: Theme.card
                border.width: message.state === "ask" ? 2 : 1
                border.color: message.state === "ask" ? Theme.accent : Theme.cardBorder
                Accessible.role: Accessible.Grouping
                Accessible.name: message.title
                ColumnLayout {
                    id: actionColumn
                    x: 14
                    y: 12
                    width: actionCard.width - 28
                    spacing: 8
                    Text {
                        visible: message.state === "ask"
                        text: backend.text("action_ask")
                        color: Theme.subtext
                        font.pixelSize: Theme.captionSize
                    }
                    RowLayout {
                        spacing: 10
                        Rectangle {
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 26
                            radius: 13
                            color: message.state === "done" ? Theme.success
                                 : message.state === "failed" || message.state === "denied" ? Theme.faint
                                 : Theme.accent
                            Kirigami.Icon {
                                anchors.centerIn: parent
                                width: 14
                                height: 14
                                isMask: true
                                color: "#FFFFFF"
                                source: message.state === "done" ? "dialog-ok-apply"
                                      : message.state === "failed" || message.state === "denied" ? "dialog-cancel"
                                      : "system-run"
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: message.title
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                    }
                    RowLayout {
                        visible: message.state === "ask"
                        spacing: 8
                        VButton {
                            objectName: "allow"
                            primary: true
                            text: backend.text("allow")
                            onClicked: backend.allowAction(message.id)
                        }
                        VButton {
                            objectName: "deny"
                            text: backend.text("deny")
                            onClicked: backend.denyAction(message.id)
                        }
                    }
                    Row {
                        visible: message.state !== "ask"
                        spacing: 6
                        BusyIndicator {
                            visible: message.state === "running" || message.state === ""
                            running: visible
                            width: 16
                            height: 16
                        }
                        Text {
                            text: message.state === "done" ? backend.text("action_done")
                                : message.state === "denied" ? backend.text("action_denied")
                                : message.state === "failed" ? backend.text("action_failed")
                                : backend.text("action_running")
                            color: message.state === "failed" ? Theme.danger : Theme.subtext
                            font.pixelSize: Theme.captionSize
                        }
                    }
                }
            }
        }
    }

    Component {
        id: problem
        Item {
            readonly property var message: parent && parent.message ? parent.message : ({})
            implicitHeight: problemCard.height
            Rectangle {
                id: problemCard
                anchors.left: parent.left
                anchors.leftMargin: 16
                width: parent.width - 32
                height: problemText.implicitHeight + 20
                radius: Theme.radius
                color: Theme.dangerSoft
                Text {
                    id: problemText
                    x: 12
                    y: 10
                    width: parent.width - 24
                    text: message.text
                    color: Theme.danger
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
