// The text caret as on Windows: it blinks while typing and stays on five
// seconds after the last key or move (Windows' CaretTimeout). Qt's caret
// blinks for ever, and every blink repaints the see-through window with
// the blur behind it (2026-11-08). A TextInput's cursorDelegate; Qt then
// leaves the blinking to it.
import QtQuick
import "."

Rectangle {
    id: caret

    readonly property Item field: parent
    property bool on: true
    property int blinks: 0

    function restart() {
        blinks = 0;
        on = true;
    }

    width: 1
    color: Theme.text
    visible: !!field && field.cursorVisible && on

    Timer {
        interval: Math.max(250, Qt.styleHints.cursorFlashTime / 2)
        repeat: true
        running: !!caret.field && caret.field.cursorVisible && caret.blinks < 10
        onTriggered: {
            caret.blinks += 1;
            caret.on = caret.blinks >= 10 ? true : !caret.on;
        }
    }

    Connections {
        target: caret.field
        function onCursorPositionChanged() { caret.restart(); }
        function onTextChanged() { caret.restart(); }
        function onCursorVisibleChanged() { caret.restart(); }
    }
}
