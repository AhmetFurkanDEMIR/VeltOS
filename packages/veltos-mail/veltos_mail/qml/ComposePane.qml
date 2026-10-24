// New mail, reply and forward in the reading pane, as in Outlook: Send
// (blue) and Discard on top, From (with several accounts), To with Cc and
// Bcc, "Add a subject", the attached files, and the message (rich text;
// Bold, Italic, Underline, Bullets and Numbering on the Message tab).
// Addresses typed into To/Cc/Bcc are completed from people you got mail
// from.
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "."

Rectangle {
    id: pane

    readonly property var c: backend.compose
    property bool showCc: false
    signal problem(string text)

    function attach() { fileDialog.open(); }
    function format(what) {
        backend.applyFormat(body.textDocument, body.selectionStart, body.selectionEnd, body.cursorPosition, what);
        body.forceActiveFocus();
    }
    function sendNow() {
        backend.setComposeField("body", body.text);
        const problemKey = backend.send();
        if (problemKey !== "")
            pane.problem(backend.text(problemKey));
    }

    color: Theme.card
    radius: Theme.cardRadius
    border.width: Theme.dark ? 0 : 1
    border.color: Theme.cardBorder

    onCChanged: {
        if (c.mode === undefined)
            return;
        if (toRow.text !== c.to) toRow.text = c.to;
        if (ccRow.text !== c.cc) ccRow.text = c.cc;
        if (bccRow.text !== c.bcc) bccRow.text = c.bcc;
        if (subjectInput.text !== c.subject) subjectInput.text = c.subject;
        showCc = showCc || !!c.showCc;
    }
    Component.onCompleted: { loadBody(); }
    function loadBody() {
        if (c.mode !== undefined) {
            body.text = c.body;
            if (c.mode === "new" && c.to === "")
                toRow.field.forceActiveFocus();
            else {
                body.forceActiveFocus();
                body.cursorPosition = 0;
            }
        }
    }
    Connections {
        target: backend
        function onComposeStarted() { pane.showCc = !!backend.compose.showCc; pane.loadBody(); }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 1
        spacing: 0

        // Send / Discard
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 12
            Layout.topMargin: 12
            spacing: 8
            VButton {
                primary: true
                icon: "sent"
                text: pane.c.sending ? backend.text("sending") : backend.text("send")
                active: !pane.c.sending
                onClicked: pane.sendNow()
            }
            Item { Layout.fillWidth: true }
            Text {
                text: backend.text("draft")
                color: Theme.subtext
                font.pixelSize: Theme.smallFont
            }
            FlatButton {
                icon: "attach"; showText: false; tip: backend.text("attach"); iconColour: Theme.subtext
                onClicked: pane.attach()
            }
            FlatButton {
                icon: "delete"; showText: false; tip: backend.text("discard"); iconColour: Theme.subtext
                onClicked: backend.discard()
            }
        }

        component AddressRow: RowLayout {
            id: addressRow
            property alias field: input
            property string label
            property alias text: input.text
            property string key
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            spacing: 0
            Rectangle {
                Layout.preferredWidth: labelText.implicitWidth + 20
                Layout.preferredHeight: 30
                radius: Theme.radius
                border.width: 1
                border.color: Theme.fieldBorder
                color: "transparent"
                Text {
                    id: labelText
                    anchors.centerIn: parent
                    text: addressRow.label
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                }
            }
            TextInput {
                id: input
                Layout.fillWidth: true
                Layout.leftMargin: 10
                Layout.preferredHeight: 36
                verticalAlignment: TextInput.AlignVCenter
                color: Theme.text
                selectionColor: Theme.brand
                selectedTextColor: "#FFFFFF"
                font.pixelSize: Theme.fontSize
                selectByMouse: true
                clip: true
                onTextEdited: {
                    backend.setComposeField(addressRow.key, text);
                    const last = text.split(/[,;]/).pop();
                    suggestions.show(addressRow, input, last);
                }
                Keys.onEscapePressed: suggestions.close()
                Keys.onDownPressed: if (suggestions.opened) suggestions.forceActiveFocus()
            }
        }

        AddressRow {
            id: fromRow
            visible: backend.accountList.length > 1
            label: backend.text("from_label")
            key: "account"
            Layout.topMargin: 10
            field.readOnly: true
            text: pane.c.from || ""
            TapHandler {
                onTapped: {
                    fromMenu.items = backend.accountList.map(a => ({ text: a.email, action: a.id,
                                                                     checked: a.email === pane.c.from }));
                    fromMenu.openAt(fromRow, 80, fromRow.height);
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: fromRow.visible ? 4 : 10
            spacing: 0
            AddressRow {
                id: toRow
                Layout.fillWidth: true
                Layout.rightMargin: 4
                label: backend.text("to")
                key: "to"
            }
            Text {
                visible: !pane.showCc
                Layout.rightMargin: 16
                text: backend.text("cc") + "   " + backend.text("bcc")
                color: Theme.brandText
                font.pixelSize: Theme.smallFont + 1
                HoverHandler { cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: pane.showCc = true }
            }
        }
        AddressRow { id: ccRow; visible: pane.showCc; label: backend.text("cc"); key: "cc"; Layout.topMargin: 4 }
        AddressRow { id: bccRow; visible: pane.showCc; label: backend.text("bcc"); key: "bcc"; Layout.topMargin: 4 }

        Rectangle { Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16; Layout.topMargin: 6
                    Layout.preferredHeight: 1; color: Theme.separator }

        TextInput {
            id: subjectInput
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.preferredHeight: 40
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.text
            selectionColor: Theme.brand
            selectedTextColor: "#FFFFFF"
            font.pixelSize: Math.round(16 * Theme.textScale)
            selectByMouse: true
            clip: true
            onTextEdited: backend.setComposeField("subject", text)
            Text {
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                visible: parent.text === ""
                text: backend.text("add_subject")
                color: Theme.tertiary
                font.pixelSize: parent.font.pixelSize
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16
                    Layout.preferredHeight: 1; color: Theme.separator }

        // Attached files
        Flow {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.topMargin: 8
            visible: (pane.c.attachments || []).length > 0
            spacing: 8
            Repeater {
                model: pane.c.attachments || []
                delegate: Rectangle {
                    id: chip
                    required property var modelData
                    required property int index
                    width: Math.min(240, chipRow.implicitWidth + 12)
                    height: 40
                    radius: Theme.radius
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    RowLayout {
                        id: chipRow
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 2
                        spacing: 6
                        Glyph { Layout.preferredWidth: 18; Layout.preferredHeight: 18; kind: "attach"; color: Theme.brandText }
                        ColumnLayout {
                            spacing: 0
                            Text { text: chip.modelData.name; color: Theme.text; font.pixelSize: Theme.smallFont + 1
                                   elide: Text.ElideMiddle; Layout.maximumWidth: 150 }
                            Text { text: chip.modelData.sizeText; color: Theme.subtext; font.pixelSize: Theme.captionFont }
                        }
                        FlatButton {
                            implicitHeight: 26; icon: "close"; iconSize: 12; showText: false; tip: backend.text("remove")
                            iconColour: Theme.subtext
                            onClicked: backend.removeAttachment(chip.index)
                        }
                    }
                }
            }
        }

        // A Flickable, not a ScrollView: Breeze's ScrollView looped on its
        // scroll bar's x ("Binding loop detected", AGENTS.md).
        Flickable {
            id: bodyFlick
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 10
            Layout.rightMargin: 6
            Layout.topMargin: 4
            Layout.bottomMargin: 6
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            TextArea.flickable: TextArea {
                id: body
                textFormat: TextEdit.RichText
                wrapMode: TextEdit.Wrap
                color: Theme.text
                selectionColor: Theme.brand
                selectedTextColor: "#FFFFFF"
                font.pixelSize: Math.round(14.5 * Theme.textScale)
                background: null
                selectByMouse: true
                persistentSelection: true
                Keys.onPressed: event => {
                    if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
                            && (event.modifiers & Qt.ControlModifier)) {
                        pane.sendNow();
                        event.accepted = true;
                    }
                }
            }
        }
    }

    // Address completion.
    Popup {
        id: suggestions
        property var row
        property var input
        property var found: []
        function show(row, input, text) {
            found = backend.suggestions(text);
            if (found.length === 0) { close(); return; }
            suggestions.row = row;
            suggestions.input = input;
            const point = input.mapToItem(pane, 0, input.height);
            x = point.x;
            y = point.y + 2;
            open();
        }
        function choose(address) {
            const parts = input.text.split(/[,;]/).map(s => s.trim()).filter(s => s !== "");
            parts.pop();
            parts.push(address);
            input.text = parts.join(", ") + ", ";
            backend.setComposeField(row.key, input.text);
            close();
            input.forceActiveFocus();
        }
        width: 320
        padding: 4
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 8; color: Theme.menu; border.width: 1; border.color: Theme.fieldBorder }
        contentItem: ColumnLayout {
            spacing: 0
            Repeater {
                model: suggestions.found
                delegate: Rectangle {
                    id: s
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 44
                    radius: Theme.radius
                    color: sHover.hovered ? Theme.hover : "transparent"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        spacing: 10
                        Avatar { size: 28; initials: s.modelData.initials; tint: s.modelData.colour }
                        ColumnLayout {
                            spacing: 0
                            Text { text: s.modelData.name; color: Theme.text; font.pixelSize: Theme.fontSize }
                            Text { text: s.modelData.address; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                        }
                    }
                    HoverHandler { id: sHover }
                    TapHandler { onTapped: suggestions.choose(s.modelData.address) }
                }
            }
        }
    }

    WinMenu {
        id: fromMenu
        onTriggered: action => backend.setComposeField("account", action)
    }

    FileDialog {
        id: fileDialog
        fileMode: FileDialog.OpenFiles
        onAccepted: backend.attachFiles(selectedFiles.map(u => u.toString()))
    }

    Shortcut { sequences: ["Ctrl+Return", "Ctrl+Enter"]; enabled: pane.visible; onActivated: pane.sendNow() }
}
