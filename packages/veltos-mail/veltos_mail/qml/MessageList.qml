// Outlook's message list: the folder's name, Focused / Other, messages in
// date groups (Today, Yesterday, ...). A message: the sender's picture,
// name, subject and the start of the text; unread ones with a blue bar,
// bold name and a blue subject; hovering shows Delete, Read/Unread, Flag
// and Pin; right-click opens the actions menu.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: pane

    color: Theme.card
    radius: Theme.cardRadius
    border.width: Theme.dark ? 0 : 1
    border.color: Theme.cardBorder

    function moveSelection(step) {
        const rows = backend.messages;
        let index = list.currentIndex < 0 ? -1 : list.currentIndex;
        for (let i = index + step; i >= 0 && i < list.count; i += step) {
            const row = rows.get(i);
            if (row.kind === "message") {
                list.currentIndex = i;
                list.positionViewAtIndex(i, ListView.Contain);
                backend.openMessage(row.account, row.folder, row.uid);
                return;
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 10
        spacing: 4

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 8
            spacing: 6
            Text {
                Layout.fillWidth: true
                text: backend.currentFolderLabel
                color: Theme.text
                font.pixelSize: Math.round(18 * Theme.textScale)
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            BusyIndicator {
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
                running: backend.syncing
                visible: running
            }
            FlatButton {
                icon: "sync"; showText: false; tip: backend.text("sync"); iconColour: Theme.subtext
                onClicked: backend.refresh()
            }
            FlatButton {
                id: filterButton
                icon: "filter"; showText: false; tip: backend.text("filter"); iconColour: Theme.subtext
                onClicked: listMenu.openAt(filterButton, 0, filterButton.height + 2)
            }
        }

        // Focused / Other
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            visible: backend.tabsShown
            spacing: 4
            Repeater {
                model: ["focused", "other"]
                delegate: Item {
                    id: tabItem
                    required property string modelData
                    readonly property bool current: backend.tab === modelData
                    implicitWidth: tabText.implicitWidth + 16
                    implicitHeight: 32
                    Text {
                        id: tabText
                        anchors.centerIn: parent
                        text: backend.text(tabItem.modelData)
                        color: tabItem.current ? Theme.text : Theme.subtext
                        font.pixelSize: Theme.fontSize
                        font.weight: tabItem.current ? Font.DemiBold : Font.Normal
                    }
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: tabItem.current ? tabText.implicitWidth : 0
                        height: 3
                        radius: 1.5
                        color: Theme.brand
                        Behavior on width { enabled: Theme.anim > 0; NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
                    }
                    HoverHandler { cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: backend.setTab(tabItem.modelData) }
                }
            }
            Item { Layout.fillWidth: true }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.separator }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: backend.messages
            currentIndex: -1
            boundsBehavior: Flickable.StopAtBounds
            keyNavigationEnabled: false
            focus: true
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            Keys.onUpPressed: pane.moveSelection(-1)
            Keys.onDownPressed: pane.moveSelection(1)
            Keys.onDeletePressed: backend.deleteMessage("", "", 0)

            // Each row reads its message as a plain object (the model's
            // QObject wrappers were deleted under the bindings when the
            // list was reset, "Cannot read property ... of null").
            delegate: Loader {
                id: rowLoader
                required property int index
                required property string kind
                readonly property var row: { backend.messages.revision; return backend.messages.get(index); }
                width: list.width
                height: item ? item.height : 0
                sourceComponent: kind === "header" ? headerRow : messageRow
            }

            add: Transition {
                enabled: Theme.anim > 0
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 160 }
            }
        }
    }

    // Nothing in the list.
    ColumnLayout {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 40
        visible: backend.listCount === 0 && backend.hasAccounts
        spacing: 8
        Glyph {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            kind: backend.query !== "" ? "search" : "mail-read"
            color: Theme.disabled
            lineWidth: 0.9
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: backend.text(backend.query !== "" ? "empty_search" : "empty_list")
            color: Theme.text
            font.pixelSize: Math.round(16 * Theme.textScale)
            font.weight: Font.DemiBold
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: backend.text(backend.query !== "" ? "empty_search_sub" : "empty_list_sub")
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
        }
    }

    Component {
        id: headerRow
        Item {
            readonly property var row: parent && parent.row ? parent.row : ({})
            width: parent ? parent.width : 0
            height: 34
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                spacing: 6
                Glyph {
                    Layout.preferredWidth: 12
                    Layout.preferredHeight: 12
                    kind: row.collapsed ? "chevron-right" : "chevron-down"
                    color: Theme.subtext
                }
                Text {
                    Layout.fillWidth: true
                    text: row.label || ""
                    color: Theme.text
                    font.pixelSize: Theme.smallFont + 1
                    font.weight: Font.DemiBold
                }
            }
            TapHandler { onTapped: backend.toggleGroup((row.key || "").substring(2)) }
        }
    }

    Component {
        id: messageRow
        Item {
            id: item
            readonly property var row: parent && parent.row ? parent.row : ({})
            readonly property int rowIndex: parent ? parent.index : -1
            width: parent ? parent.width : 0
            height: backend.showPreview ? Math.round(76 * Theme.textScale) : Math.round(56 * Theme.textScale)

            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                radius: Theme.radius
                color: item.row.selected ? (hover.hovered ? Theme.brandSoftHover : Theme.brandSoft)
                       : (hover.hovered ? Theme.hover : "transparent")
                Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 80 } }
            }
            // Unread: the blue bar on the left.
            Rectangle {
                visible: item.row.seen === false
                anchors.left: parent.left
                anchors.leftMargin: 4
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.topMargin: 6
                anchors.bottomMargin: 6
                width: 3
                radius: 1.5
                color: Theme.brand
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.leftMargin: 16
                anchors.rightMargin: 12
                height: 1
                color: Theme.separator
                visible: !item.row.selected
            }

            Avatar {
                id: avatar
                visible: backend.showAvatars
                anchors.left: parent.left
                anchors.leftMargin: 16
                anchors.top: parent.top
                anchors.topMargin: 10
                size: 32
                initials: item.row.initials || ""
                tint: item.row.colour || Theme.brand
            }

            ColumnLayout {
                anchors.left: backend.showAvatars ? avatar.right : parent.left
                anchors.leftMargin: backend.showAvatars ? 12 : 18
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.top: parent.top
                anchors.topMargin: 8
                spacing: 1

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        Layout.fillWidth: true
                        text: item.row.fromName || ""
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                        font.weight: item.row.seen ? Font.Normal : Font.DemiBold
                        elide: Text.ElideRight
                    }
                    // Quick actions while the pointer is on the message.
                    RowLayout {
                        visible: hover.hovered
                        spacing: 0
                        FlatButton {
                            implicitHeight: 24; icon: "delete"; iconSize: 16; showText: false
                            tip: backend.text("delete"); iconColour: Theme.subtext
                            onClicked: backend.deleteMessage(item.row.account, item.row.folder, item.row.uid)
                        }
                        FlatButton {
                            implicitHeight: 24; icon: item.row.seen ? "mail" : "mail-read"; iconSize: 16; showText: false
                            tip: backend.text(item.row.seen ? "mark_unread" : "mark_read"); iconColour: Theme.subtext
                            onClicked: backend.toggleRead(item.row.account, item.row.folder, item.row.uid)
                        }
                        FlatButton {
                            implicitHeight: 24; icon: "flag"; iconSize: 16; showText: false; filledIcon: !!item.row.flagged
                            tip: backend.text(item.row.flagged ? "clear_flag" : "flag_message")
                            iconColour: item.row.flagged ? Theme.flag : Theme.subtext
                            onClicked: backend.toggleFlag(item.row.account, item.row.folder, item.row.uid)
                        }
                        FlatButton {
                            implicitHeight: 24; icon: "pin"; iconSize: 16; showText: false; filledIcon: !!item.row.pinned
                            tip: backend.text(item.row.pinned ? "unpin_message" : "pin_message"); iconColour: Theme.subtext
                            onClicked: backend.togglePin(item.row.account, item.row.folder, item.row.uid)
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        Layout.fillWidth: true
                        text: item.row.subject || ""
                        color: item.row.seen ? Theme.text : Theme.brandText
                        font.pixelSize: Theme.fontSize - 1
                        font.weight: item.row.seen ? Font.Normal : Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Glyph {
                        visible: !!item.row.answered
                        Layout.preferredWidth: 14; Layout.preferredHeight: 14
                        kind: "reply"; color: Theme.subtext
                    }
                    Glyph {
                        visible: !!item.row.attachments
                        Layout.preferredWidth: 14; Layout.preferredHeight: 14
                        kind: "attach"; color: Theme.subtext
                    }
                    Glyph {
                        visible: !!item.row.flagged && !hover.hovered
                        Layout.preferredWidth: 14; Layout.preferredHeight: 14
                        kind: "flag"; filled: true; color: Theme.flag
                    }
                    Glyph {
                        visible: !!item.row.pinned && !hover.hovered
                        Layout.preferredWidth: 14; Layout.preferredHeight: 14
                        kind: "pin"; filled: true; color: Theme.subtext
                    }
                    Text {
                        text: item.row.time || ""
                        color: item.row.seen ? Theme.subtext : Theme.text
                        font.pixelSize: Theme.smallFont
                        font.weight: item.row.seen ? Font.Normal : Font.DemiBold
                    }
                }
                Text {
                    Layout.fillWidth: true
                    visible: backend.showPreview
                    text: item.row.preview || ""
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont + 1
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
            }

            HoverHandler { id: hover }
            TapHandler {
                acceptedButtons: Qt.LeftButton
                onTapped: {
                    list.currentIndex = item.rowIndex;
                    list.forceActiveFocus();
                    backend.openMessage(item.row.account, item.row.folder, item.row.uid);
                }
            }
            TapHandler {
                acceptedButtons: Qt.RightButton
                onTapped: (point) => {
                    contextMenu.target = item.row;
                    contextMenu.items = [
                        { text: backend.text("reply"), icon: "reply", action: "reply" },
                        { text: backend.text("reply_all"), icon: "reply-all", action: "replyAll" },
                        { text: backend.text("forward"), icon: "forward", action: "forward" },
                        { separator: true },
                        { text: backend.text("delete"), icon: "delete", action: "delete", shortcut: "Del" },
                        { text: backend.text("archive"), icon: "archive", action: "archive" },
                        { text: backend.text("move_to"), icon: "move",
                          submenu: backend.moveTargets().map(t => ({ text: t.label, icon: t.icon, action: "move:" + t.folder })) },
                        { text: backend.text("report_junk"), icon: "junk", action: "junk" },
                        { separator: true },
                        { text: backend.text(item.row.seen ? "mark_unread" : "mark_read"), icon: "mail-read", action: "read" },
                        { text: backend.text(item.row.flagged ? "clear_flag" : "flag_message"), icon: "flag", action: "flag" },
                        { text: backend.text(item.row.pinned ? "unpin_message" : "pin_message"), icon: "pin", action: "pin" }];
                    contextMenu.openAt(item, point.position.x, point.position.y);
                }
            }
            Accessible.role: Accessible.ListItem
            Accessible.name: (item.row.fromName || "") + ", " + (item.row.subject || "")
        }
    }

    WinMenu {
        id: contextMenu
        property var target: ({})
        onTriggered: action => {
            const t = target;
            if (action === "delete") backend.deleteMessage(t.account, t.folder, t.uid);
            else if (action === "archive") backend.archiveMessage(t.account, t.folder, t.uid);
            else if (action === "junk") backend.junkMessage(t.account, t.folder, t.uid);
            else if (action === "read") backend.toggleRead(t.account, t.folder, t.uid);
            else if (action === "flag") backend.toggleFlag(t.account, t.folder, t.uid);
            else if (action === "pin") backend.togglePin(t.account, t.folder, t.uid);
            else if (action.indexOf("move:") === 0) backend.moveMessage(action.substring(5), t.account, t.folder, t.uid);
            else {
                backend.openMessage(t.account, t.folder, t.uid);
                replyAfterOpen.mode = action;
                replyAfterOpen.restart();
            }
        }
    }
    // Reply/forward need the message's text: wait until it is open.
    Timer {
        id: replyAfterOpen
        property string mode
        interval: 150
        repeat: true
        onTriggered: {
            if (backend.reading.loading === false) {
                stop();
                backend.reply(mode);
            }
        }
    }
    WinMenu {
        id: listMenu
        items: [{ text: backend.text("focused_inbox"), checked: backend.focusedInbox, action: "focused" },
                { text: backend.text("message_preview"), checked: backend.showPreview, action: "preview" },
                { text: backend.text("sender_images"), checked: backend.showAvatars, action: "avatars" },
                { separator: true },
                { text: backend.text("mark_all_read"), icon: "mail-read", action: "allread" }]
        onTriggered: action => {
            if (action === "focused") backend.setFocusedInbox(!backend.focusedInbox);
            else if (action === "preview") backend.setShowPreview(!backend.showPreview);
            else if (action === "avatars") backend.setShowAvatars(!backend.showAvatars);
            else backend.markAllRead();
        }
    }
}
