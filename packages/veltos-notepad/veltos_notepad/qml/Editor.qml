// The text of one tab. Plain text in the chosen font, word wrap and zoom;
// its QTextDocument is handed to Python (saving, find and replace, line
// numbers). Ctrl + wheel zooms, the right button opens the edit menu.
import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import "."

Item {
    id: editor

    required property int index
    required property int tabId
    required property string initialText
    required property int cursor
    readonly property alias area: area
    signal contextMenu(real x, real y)
    signal cursorMoved()

    ScrollView {
        id: scroll
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: backend.wordWrap ? ScrollBar.AlwaysOff : ScrollBar.AsNeeded

        // The template, not the style's TextArea: KDE's style opens its own
        // menu (Spell checking, Undo, Cut ...) on the right button and the
        // Menu key, so two menus opened over each other (product owner,
        // 2026-10-23). Notepad's menu is the only one, as on Windows.
        T.TextArea {
            id: area
            implicitWidth: Math.max(contentWidth + leftPadding + rightPadding,
                                    implicitBackgroundWidth + leftInset + rightInset)
            implicitHeight: Math.max(contentHeight + topPadding + bottomPadding,
                                     implicitBackgroundHeight + topInset + bottomInset)
            textFormat: TextEdit.PlainText
            wrapMode: backend.wordWrap ? TextEdit.Wrap : TextEdit.NoWrap
            font.family: backend.fontFamily
            font.pointSize: Math.max(4, backend.fontSize * backend.zoom / 100)
            font.bold: backend.fontStyle.indexOf("bold") === 0
            font.italic: backend.fontStyle.indexOf("italic") >= 0
            color: Theme.text
            selectionColor: Theme.selection
            selectedTextColor: Theme.text
            selectByMouse: true
            persistentSelection: true
            leftPadding: 14
            rightPadding: 14
            topPadding: 10
            bottomPadding: 10
            tabStopDistance: fontInfo.advanceWidth("        ")
            background: Rectangle { color: Theme.editor }
            Accessible.name: backend.texts.app_title

            FontMetrics {
                id: fontInfo
                font: area.font
            }

            Component.onCompleted: {
                text = editor.initialText;
                backend.attach(editor.tabId, textDocument);
                cursorPosition = Math.min(editor.cursor, length);
            }
            onCursorPositionChanged: editor.cursorMoved()
            onSelectedTextChanged: editor.cursorMoved()
            onLengthChanged: editor.cursorMoved()

            TapHandler {
                acceptedButtons: Qt.RightButton
                onTapped: point => editor.contextMenu(point.position.x, point.position.y)
            }
            // The Menu key and Shift+F10 open it at the text cursor.
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Menu
                        || (event.key === Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier))) {
                    editor.contextMenu(cursorRectangle.x, cursorRectangle.y + cursorRectangle.height);
                    event.accepted = true;
                }
            }
        }
    }

    WheelHandler {
        acceptedModifiers: Qt.ControlModifier
        onWheel: event => backend.stepZoom(event.angleDelta.y > 0 ? 1 : -1)
    }
}
