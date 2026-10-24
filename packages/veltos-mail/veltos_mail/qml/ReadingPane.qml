// Outlook's reading pane: the subject on top, then the message card with
// the sender's picture, name and address, "To:", the date and Reply /
// Reply all / Forward / More; the yellow bar when pictures were blocked;
// the attachments; the message itself (Qt WebEngine with JavaScript off;
// links open in the web browser). With nothing selected: "Select an item
// to read".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import "."

Rectangle {
    id: pane

    readonly property var r: backend.reading
    readonly property bool hasMessage: r.uid !== undefined

    color: Theme.card
    radius: Theme.cardRadius
    border.width: Theme.dark ? 0 : 1
    border.color: Theme.cardBorder

    // Nothing selected.
    ColumnLayout {
        anchors.centerIn: parent
        visible: !pane.hasMessage
        spacing: 10
        Item {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 120
            Layout.preferredHeight: 96
            Rectangle {
                anchors.centerIn: parent
                width: 104
                height: 74
                radius: 10
                color: Theme.brandSoft
                Glyph {
                    anchors.centerIn: parent
                    width: 56
                    height: 56
                    kind: "mail"
                    color: Theme.brandText
                    lineWidth: 1.1
                }
            }
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: backend.text("select_item")
            color: Theme.text
            font.pixelSize: Math.round(16 * Theme.textScale)
            font.weight: Font.DemiBold
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: backend.text("nothing_selected")
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 1
        visible: pane.hasMessage
        spacing: 0

        // Subject
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 12
            Layout.topMargin: 14
            Layout.bottomMargin: 6
            spacing: 6
            Text {
                Layout.fillWidth: true
                text: pane.r.subject || ""
                color: Theme.text
                font.pixelSize: Theme.subjectFont
                font.weight: Font.DemiBold
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            FlatButton {
                icon: "flag"; showText: false; filledIcon: !!pane.r.flagged
                iconColour: pane.r.flagged ? Theme.flag : Theme.subtext
                tip: backend.text(pane.r.flagged ? "clear_flag" : "flag_message")
                onClicked: backend.toggleFlag("", "", 0)
            }
        }

        // The message card: sender, recipients, date, actions.
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 12
            Layout.topMargin: 6
            spacing: 12
            Avatar {
                Layout.alignment: Qt.AlignTop
                size: 40
                initials: pane.r.initials || ""
                tint: pane.r.colour || Theme.brand
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                RowLayout {
                    spacing: 6
                    Text {
                        text: pane.r.fromName || ""
                        color: Theme.text
                        font.pixelSize: Theme.fontSize + 1
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                        Layout.maximumWidth: pane.width * 0.4
                    }
                    Text {
                        text: pane.r.fromAddr ? "<" + pane.r.fromAddr + ">" : ""
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont + 1
                        elide: Text.ElideRight
                        Layout.maximumWidth: pane.width * 0.3
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("to_label") + " " + (pane.r.to || "")
                          + (pane.r.cc ? "   " + backend.text("cc_label") + " " + pane.r.cc : "")
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont + 1
                    elide: Text.ElideRight
                }
            }
            ColumnLayout {
                Layout.alignment: Qt.AlignTop
                spacing: 2
                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 0
                    FlatButton { icon: "reply"; showText: false; tip: backend.text("reply"); iconColour: Theme.brandText
                                 onClicked: backend.reply("reply") }
                    FlatButton { icon: "reply-all"; showText: false; tip: backend.text("reply_all"); iconColour: Theme.brandText
                                 onClicked: backend.reply("replyAll") }
                    FlatButton { icon: "forward"; showText: false; tip: backend.text("forward"); iconColour: Theme.brandText
                                 onClicked: backend.reply("forward") }
                    FlatButton {
                        id: moreButton
                        icon: "more"; showText: false; tip: backend.text("more_actions"); iconColour: Theme.subtext
                        onClicked: moreMenu.openAt(moreButton, 0, moreButton.height + 2)
                    }
                }
                Text {
                    Layout.alignment: Qt.AlignRight
                    text: pane.r.dateLong || ""
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                }
            }
        }

        // Pictures from the internet were left out.
        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 16
            Layout.topMargin: 10
            visible: !!pane.r.blocked
            implicitHeight: blockedRow.implicitHeight + 14
            radius: Theme.radius
            color: Theme.warning
            border.width: 1
            border.color: Theme.warningBorder
            RowLayout {
                id: blockedRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 8
                Glyph { Layout.preferredWidth: 16; Layout.preferredHeight: 16; kind: "info"; color: Theme.text }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("pictures_blocked")
                    color: Theme.text
                    font.pixelSize: Theme.smallFont + 1
                    wrapMode: Text.Wrap
                }
                Text {
                    text: backend.text("show_pictures")
                    color: Theme.brandText
                    font.pixelSize: Theme.smallFont + 1
                    font.underline: showHover.hovered
                    HoverHandler { id: showHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: backend.showPictures() }
                }
            }
        }

        // Attachments
        Flow {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 16
            Layout.topMargin: 10
            visible: (pane.r.attachments || []).length > 0
            spacing: 8
            Repeater {
                model: pane.r.attachments || []
                delegate: Rectangle {
                    id: chip
                    required property var modelData
                    width: Math.min(260, chipRow.implicitWidth + 16)
                    height: 44
                    radius: Theme.radius
                    color: chipHover.hovered ? Theme.hover : Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    RowLayout {
                        id: chipRow
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 4
                        spacing: 8
                        Glyph { Layout.preferredWidth: 20; Layout.preferredHeight: 20; kind: "attach"; color: Theme.brandText }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Text {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 170
                                text: chip.modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.smallFont + 1
                                elide: Text.ElideMiddle
                            }
                            Text {
                                text: chip.modelData.sizeText
                                color: Theme.subtext
                                font.pixelSize: Theme.captionFont
                            }
                        }
                        FlatButton {
                            implicitHeight: 28; icon: "download"; iconSize: 16; showText: false
                            tip: backend.text("save"); iconColour: Theme.subtext
                            onClicked: backend.saveAttachment(chip.modelData.index)
                        }
                    }
                    HoverHandler { id: chipHover }
                    TapHandler { onTapped: backend.openAttachment(chip.modelData.index) }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 16
            Layout.topMargin: 12
            Layout.preferredHeight: 1
            color: Theme.separator
        }

        // The message
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 6
            Layout.bottomMargin: 6

            WebEngineView {
                id: web
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                visible: !!pane.r.page
                url: pane.r.page || "about:blank"
                backgroundColor: Theme.card
                settings.javascriptEnabled: false
                settings.javascriptCanOpenWindows: false
                settings.pluginsEnabled: false
                settings.localContentCanAccessRemoteUrls: false
                settings.localContentCanAccessFileUrls: true
                settings.errorPageEnabled: false
                settings.autoLoadImages: true
                profile: WebEngineProfile {
                    httpCacheType: WebEngineProfile.MemoryHttpCache
                    persistentCookiesPolicy: WebEngineProfile.NoPersistentCookies
                }
                onNavigationRequested: request => {
                    const target = request.url.toString();
                    if (target === (pane.r.page || "") || target === "about:blank")
                        return;
                    request.action = WebEngineNavigationRequest.IgnoreRequest;
                    if (request.navigationType === WebEngineNavigationRequest.LinkClickedNavigation)
                        backend.openUrl(target);
                }
                onNewWindowRequested: request => backend.openUrl(request.requestedUrl.toString())
            }
            BusyIndicator {
                anchors.centerIn: parent
                running: !!pane.r.loading
                visible: running
            }
            Text {
                anchors.centerIn: parent
                visible: !!pane.r.failed
                text: backend.text("load_failed")
                color: Theme.subtext
                font.pixelSize: Theme.fontSize
            }
        }
    }

    WinMenu {
        id: moreMenu
        items: [{ text: backend.text("reply"), icon: "reply", action: "reply" },
                { text: backend.text("reply_all"), icon: "reply-all", action: "replyAll" },
                { text: backend.text("forward"), icon: "forward", action: "forward" },
                { separator: true },
                { text: backend.text("delete"), icon: "delete", action: "delete" },
                { text: backend.text("archive"), icon: "archive", action: "archive" },
                { text: backend.text("report_junk"), icon: "junk", action: "junk" },
                { separator: true },
                { text: backend.text("mark_unread"), icon: "mail", action: "unread" },
                { text: backend.text(pane.r.pinned ? "unpin_message" : "pin_message"), icon: "pin", action: "pin" }]
        onTriggered: action => {
            if (action === "delete") backend.deleteMessage("", "", 0);
            else if (action === "archive") backend.archiveMessage("", "", 0);
            else if (action === "junk") backend.junkMessage("", "", 0);
            else if (action === "unread") backend.toggleRead("", "", 0);
            else if (action === "pin") backend.togglePin("", "", 0);
            else backend.reply(action);
        }
    }
}
