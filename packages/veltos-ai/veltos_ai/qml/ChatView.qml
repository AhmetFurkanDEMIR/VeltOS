// The conversation: the greeting with suggestions while it is empty, then
// the user's messages (right, accent), the answers (left, Markdown, copy),
// the actions VeltOS AI asks to run (Allow / Don't allow) and errors. In a
// wide window the conversation is a column of reading width in the middle
// (Theme.chatWidth): maximised, its lines ran across the whole screen.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Item {
    id: chat
    signal suggestion(string text)
    // The conversation's reading width (the window's wide layout sets it).
    property int columnWidth: Theme.chatWidth

    // --- greeting -----------------------------------------------------------------------------------
    ColumnLayout {
        objectName: "greeting"
        visible: backend.chat.count === 0
        width: Math.min(parent.width - 40, Theme.greetingWidth)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
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
    // A Column of every message, not a ListView: rows made lazily guessed
    // the content height, so "go to the end" fell short while an answer
    // grew; and the rows change in place (backend.chat, a list model).
    Flickable {
        id: list
        objectName: "messageView"
        anchors.fill: parent
        visible: backend.chat.count > 0
        clip: true
        contentWidth: width
        contentHeight: column.height + 24
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        // The view follows the newest words while it is at the end. A user
        // who scrolls up to read stays there (the answer kept pulling the
        // view down) until they come back down or send a message.
        property bool follow: true
        property bool movingItself: false
        // Glide down softly instead of jumping (product owner, 2026-11-01).
        property bool glide: true
        readonly property real endY: Math.max(0, contentHeight - height)
        readonly property bool atEnd: contentY >= endY - 32
        function toEnd() {
            scroller.stop();
            movingItself = true;
            contentY = endY;
            movingItself = false;
            follow = true;
        }
        function glideToEnd() {
            if (!glide || !visible)
                return toEnd();
            follow = true;
            if (Math.abs(contentY - endY) < 1)
                return;
            scroller.stop();
            scroller.from = contentY;
            scroller.to = endY;
            scroller.start();
        }
        NumberAnimation {
            id: scroller
            target: list
            property: "contentY"
            duration: 280
            easing.type: Easing.OutCubic
        }
        // (atEnd may not have followed contentY yet when this runs)
        onContentYChanged: if (!movingItself && !scroller.running) follow = contentY >= endY - 32
        onContentHeightChanged: if (follow) Qt.callLater(glideToEnd)
        onHeightChanged: if (follow) Qt.callLater(toEnd)
        onMovementStarted: scroller.stop()

        Connections {
            target: backend
            function onSent() {
                list.follow = true;
                Qt.callLater(list.glideToEnd);
            }
        }

        Column {
            id: column
            y: 12
            x: Math.max(0, Math.round((list.width - width) / 2))
            width: Math.min(list.width, chat.columnWidth)
            spacing: 12
            Repeater {
                objectName: "messages"
                model: backend.chat
                delegate: Item {
                    id: row
                    required property int mid
                    required property string kind
                    required property string body
                    required property string status
                    required property string title
                    required property string detail
                    width: column.width
                    height: loader.item ? loader.item.implicitHeight : 0
                    Loader {
                        id: loader
                        width: parent.width
                        sourceComponent: row.kind === "user" ? userBubble
                                       : row.kind === "assistant" ? answer
                                       : row.kind === "action" ? action : problem
                        property var message: ({ id: row.mid, kind: row.kind, text: row.body,
                                                 state: row.status, title: row.title, detail: row.detail })
                    }
                }
            }
        }
    }

    // Back to the newest message, when the view is scrolled up.
    Rectangle {
        objectName: "toLatest"
        visible: list.visible && !list.atEnd
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 10
        width: 36
        height: 36
        radius: 18
        color: toLatestHover.hovered ? Theme.cardHover : Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        Accessible.role: Accessible.Button
        Accessible.name: backend.text("to_latest")
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 16
            height: 16
            isMask: true
            color: Theme.text
            source: "go-down-symbolic"
        }
        HoverHandler { id: toLatestHover; cursorShape: Qt.PointingHandCursor }
        TapHandler {
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: list.toEnd()
        }
        ToolTip.visible: toLatestHover.hovered
        ToolTip.delay: 500
        ToolTip.text: Accessible.name
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
            id: answerItem
            readonly property var message: parent && parent.message ? parent.message : ({})
            implicitHeight: card.height + copyRow.height
            // The words appear smoothly as they come, a few letters a frame
            // (more when far behind), instead of a block every 60 ms.
            readonly property string full: message.text || ""
            property int shown: 0
            Component.onCompleted: if (message.state !== "streaming") shown = full.length
            onFullChanged: if (shown > full.length) shown = full.length
            Timer {
                interval: 16
                repeat: true
                running: answerItem.shown < answerItem.full.length
                onTriggered: answerItem.shown = Math.min(answerItem.full.length,
                    answerItem.shown + Math.max(2, Math.ceil((answerItem.full.length - answerItem.shown) / 10)))
            }
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
                    // Three dots that rise in turn while the answer is coming.
                    Row {
                        objectName: "typing"
                        spacing: 5
                        height: 18
                        visible: message.state === "streaming" && message.text === ""
                        Accessible.name: backend.text("thinking")
                        Repeater {
                            model: 3
                            delegate: Rectangle {
                                id: dot
                                required property int index
                                width: 7
                                height: 7
                                radius: 3.5
                                y: 6
                                color: Theme.accent
                                opacity: 0.35
                                SequentialAnimation {
                                    running: dot.visible
                                    loops: Animation.Infinite
                                    PauseAnimation { duration: dot.index * 160 }
                                    ParallelAnimation {
                                        NumberAnimation { target: dot; property: "y"; to: 0; duration: 260
                                                          easing.type: Easing.OutQuad }
                                        NumberAnimation { target: dot; property: "opacity"; to: 1; duration: 260 }
                                    }
                                    ParallelAnimation {
                                        NumberAnimation { target: dot; property: "y"; to: 6; duration: 260
                                                          easing.type: Easing.InQuad }
                                        NumberAnimation { target: dot; property: "opacity"; to: 0.35; duration: 260 }
                                    }
                                    PauseAnimation { duration: (2 - dot.index) * 160 + 200 }
                                }
                            }
                        }
                    }
                    TextEdit {
                        width: parent.width
                        visible: message.text !== ""
                        text: list.glide ? answerItem.full.substring(0, answerItem.shown) : answerItem.full
                        textFormat: message.state === "refused" ? TextEdit.PlainText : TextEdit.MarkdownText
                        color: message.state === "refused" ? Theme.subtext : Theme.text
                        font.pixelSize: Theme.bodySize
                        // Long words and command lines wrap too, never wider than the card.
                        wrapMode: TextEdit.WrapAtWordBoundaryOrAnywhere
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
                            // A long command wraps inside the card.
                            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                            maximumLineCount: 4
                            elide: Text.ElideRight
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
                    // A command's output: folded away, and at most a few
                    // lines tall when shown (long output stretched the
                    // conversation, product owner 2026-11-01).
                    Text {
                        id: outputToggle
                        objectName: "outputToggle"
                        property bool open: false
                        visible: !!message.detail
                        text: (open ? "▾ " : "▸ ") + backend.text(open ? "hide_output" : "show_output")
                        color: Theme.accent
                        font.pixelSize: Theme.captionSize
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: outputToggle.open = !outputToggle.open
                        }
                    }
                    Rectangle {
                        objectName: "output"
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(220, outputText.implicitHeight + 16)
                        visible: outputToggle.visible && outputToggle.open
                        radius: 6
                        color: Theme.dark ? "#1A1B24" : "#F4F6FA"
                        border.width: 1
                        border.color: Theme.cardBorder
                        clip: true
                        Flickable {
                            id: outputScroll
                            anchors.fill: parent
                            anchors.margins: 8
                            contentWidth: width
                            contentHeight: outputText.implicitHeight
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar {}
                            TextEdit {
                                id: outputText
                                width: outputScroll.width
                                text: message.detail || ""
                                textFormat: TextEdit.PlainText
                                color: Theme.text
                                font.family: "monospace"
                                font.pixelSize: Theme.captionSize
                                wrapMode: TextEdit.WrapAtWordBoundaryOrAnywhere
                                readOnly: true
                                selectByMouse: true
                                selectionColor: Theme.accent
                                selectedTextColor: Theme.accentText
                            }
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
