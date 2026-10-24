// Outlook's tabs (Home, View, Help; Message while writing) and the
// simplified ribbon under them: one row of commands in a white card. The
// labels give way to icons when the window is narrow.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: ribbon

    property string tab: "home"
    readonly property bool composing: backend.compose.mode !== undefined
    readonly property bool hasMessage: backend.reading.uid !== undefined
    // Labels when they fit (Turkish labels are longer than English ones),
    // else icons only, as Outlook's simplified ribbon does.
    readonly property var labelKeys: ["delete", "archive", "report", "move_to", "reply", "reply_all", "forward",
                                      "read_unread", "flag", "pin"]
    readonly property real labelsWidth: {
        let total = 0;
        for (const key of labelKeys)
            total += metrics.advanceWidth(backend.text(key)) + 46;
        return total + metrics.advanceWidth(backend.text("new_mail")) + 70 + 4 * 9 + 60;
    }
    readonly property bool wide: width - 24 > labelsWidth
    FontMetrics { id: metrics; font.pixelSize: Theme.fontSize }
    signal showAbout()
    signal showShortcuts()
    signal attach()
    signal format(string what)

    spacing: 6
    onComposingChanged: tab = composing ? "message" : "home"

    // --- tabs -----------------------------------------------------------------------------------
    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 4
        spacing: 2
        FlatButton {
            icon: "hamburger"
            showText: false
            tip: backend.text("folder_pane")
            hoverColour: Theme.hoverCanvas
            onClicked: backend.toggleFolderPane()
        }
        Repeater {
            model: ribbon.composing ? ["home", "view", "help", "message"] : ["home", "view", "help"]
            delegate: Item {
                id: tabItem
                required property string modelData
                readonly property bool current: ribbon.tab === modelData
                implicitWidth: tabLabel.implicitWidth + 20
                implicitHeight: 32
                Rectangle {
                    anchors.fill: parent
                    radius: Theme.radius
                    color: tabHover.hovered && !tabItem.current ? Theme.hoverCanvas : "transparent"
                }
                Text {
                    id: tabLabel
                    anchors.centerIn: parent
                    text: backend.text("tab_" + tabItem.modelData)
                    color: tabItem.current ? Theme.text : Theme.subtext
                    font.pixelSize: Theme.fontSize
                    font.weight: tabItem.current ? Font.DemiBold : Font.Normal
                }
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 2
                    width: tabItem.current ? tabLabel.implicitWidth : 0
                    height: 3
                    radius: 1.5
                    color: Theme.brand
                    Behavior on width { enabled: Theme.anim > 0; NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
                }
                HoverHandler { id: tabHover }
                TapHandler { onTapped: ribbon.tab = tabItem.modelData }
                Accessible.role: Accessible.PageTab
                Accessible.name: tabLabel.text
            }
        }
        Item { Layout.fillWidth: true }
    }

    // --- the commands -----------------------------------------------------------------------------
    Rectangle {
        Layout.fillWidth: true
        Layout.leftMargin: 6
        Layout.rightMargin: 6
        implicitHeight: 44
        radius: Theme.cardRadius
        color: Theme.card
        border.width: Theme.dark ? 0 : 1
        border.color: Theme.cardBorder

        component Divider: Rectangle {
            Layout.preferredWidth: 1
            Layout.preferredHeight: 20
            Layout.leftMargin: 4
            Layout.rightMargin: 4
            color: Theme.separator
        }

        // Home
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            spacing: 2
            visible: ribbon.tab === "home"

            // New mail: Outlook's filled split button.
            Rectangle {
                id: newMail
                implicitWidth: newRow.implicitWidth + 24
                implicitHeight: 32
                radius: Theme.radius
                color: newTap.pressed ? Theme.brandPressed : newHover.hovered ? Theme.brandHover : Theme.brand
                Accessible.role: Accessible.Button
                Accessible.name: backend.text("new_mail")
                RowLayout {
                    id: newRow
                    anchors.centerIn: parent
                    spacing: 6
                    Glyph { Layout.preferredWidth: 18; Layout.preferredHeight: 18; kind: "new-mail"; color: "#FFFFFF" }
                    Text {
                        text: backend.text("new_mail")
                        color: "#FFFFFF"
                        font.pixelSize: Theme.fontSize
                        font.weight: Font.DemiBold
                    }
                }
                HoverHandler { id: newHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { id: newTap; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: backend.newMail() }
            }
            Divider {}
            FlatButton {
                icon: "delete"; text: backend.text("delete"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.danger
                onClicked: backend.deleteMessage("", "", 0)
            }
            FlatButton {
                icon: "archive"; text: backend.text("archive"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.brandText
                onClicked: backend.archiveMessage("", "", 0)
            }
            FlatButton {
                id: reportButton
                icon: "report"; text: backend.text("report"); showText: ribbon.wide; dropDown: true
                active: ribbon.hasMessage; iconColour: Theme.danger
                onClicked: reportMenu.openAt(reportButton, 0, reportButton.height + 2)
            }
            FlatButton {
                id: moveButton
                icon: "move"; text: backend.text("move_to"); showText: ribbon.wide; dropDown: true
                active: ribbon.hasMessage; iconColour: Theme.brandText
                onClicked: {
                    moveMenu.items = backend.moveTargets().map(t => ({ text: t.label, icon: t.icon, action: t.folder }));
                    moveMenu.openAt(moveButton, 0, moveButton.height + 2);
                }
            }
            Divider {}
            FlatButton {
                icon: "reply"; text: backend.text("reply"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.brandText
                onClicked: backend.reply("reply")
            }
            FlatButton {
                icon: "reply-all"; text: backend.text("reply_all"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.brandText
                onClicked: backend.reply("replyAll")
            }
            FlatButton {
                icon: "forward"; text: backend.text("forward"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.brandText
                onClicked: backend.reply("forward")
            }
            Divider {}
            FlatButton {
                icon: "mail-read"; text: backend.text("read_unread"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.brandText
                onClicked: backend.toggleRead("", "", 0)
            }
            FlatButton {
                icon: "flag"; text: backend.text("flag"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.flag; filledIcon: !!backend.reading.flagged
                onClicked: backend.toggleFlag("", "", 0)
            }
            FlatButton {
                icon: "pin"; text: backend.text("pin"); showText: ribbon.wide; active: ribbon.hasMessage
                iconColour: Theme.brandText
                onClicked: backend.togglePin("", "", 0)
            }
            Item { Layout.fillWidth: true }
            FlatButton {
                id: moreButton
                icon: "more"; showText: false; tip: backend.text("more_actions")
                onClicked: moreMenu.openAt(moreButton, 0, moreButton.height + 2)
            }
        }

        // View
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            spacing: 2
            visible: ribbon.tab === "view"
            FlatButton {
                icon: "hamburger"; text: backend.text("folder_pane"); toggled: backend.folderPaneOpen
                onClicked: backend.toggleFolderPane()
            }
            Divider {}
            FlatButton {
                icon: "inbox"; text: backend.text("focused_inbox"); toggled: backend.focusedInbox
                onClicked: backend.setFocusedInbox(!backend.focusedInbox)
            }
            FlatButton {
                icon: "filter"; text: backend.text("message_preview"); toggled: backend.showPreview
                onClicked: backend.setShowPreview(!backend.showPreview)
            }
            FlatButton {
                icon: "person"; text: backend.text("sender_images"); toggled: backend.showAvatars
                onClicked: backend.setShowAvatars(!backend.showAvatars)
            }
            Divider {}
            FlatButton {
                icon: "sync"; text: backend.text("sync"); iconColour: Theme.brandText
                onClicked: backend.refresh()
            }
            Item { Layout.fillWidth: true }
        }

        // Help
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            spacing: 2
            visible: ribbon.tab === "help"
            FlatButton { icon: "help"; text: backend.text("about"); iconColour: Theme.brandText; onClicked: ribbon.showAbout() }
            FlatButton { icon: "info"; text: backend.text("shortcuts"); iconColour: Theme.brandText; onClicked: ribbon.showShortcuts() }
            Item { Layout.fillWidth: true }
        }

        // Message (writing)
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            spacing: 2
            visible: ribbon.tab === "message"
            FlatButton { icon: "attach"; text: backend.text("attach"); iconColour: Theme.brandText; onClicked: ribbon.attach() }
            Divider {}
            FlatButton { icon: "bold"; showText: false; tip: backend.text("bold"); onClicked: ribbon.format("bold") }
            FlatButton { icon: "italic"; showText: false; tip: backend.text("italic"); onClicked: ribbon.format("italic") }
            FlatButton { icon: "underline"; showText: false; tip: backend.text("underline"); onClicked: ribbon.format("underline") }
            Divider {}
            FlatButton { icon: "bullets"; showText: false; tip: backend.text("bullets"); onClicked: ribbon.format("bullets") }
            FlatButton { icon: "numbering"; showText: false; tip: backend.text("numbering"); onClicked: ribbon.format("numbering") }
            Divider {}
            FlatButton { icon: "delete"; text: backend.text("discard"); iconColour: Theme.danger; onClicked: backend.discard() }
            Item { Layout.fillWidth: true }
        }
    }

    WinMenu {
        id: reportMenu
        items: [{ text: backend.text("report_junk"), icon: "junk", action: "junk" }]
        onTriggered: backend.junkMessage("", "", 0)
    }
    WinMenu {
        id: moveMenu
        onTriggered: action => backend.moveMessage(action, "", "", 0)
    }
    WinMenu {
        id: moreMenu
        items: [{ text: backend.text("mark_all_read"), icon: "mail-read", action: "allread" },
                { text: backend.text("sync"), icon: "sync", action: "sync", shortcut: "F5" }]
        onTriggered: action => action === "allread" ? backend.markAllRead() : backend.refresh()
    }
}
