// "Find a setting" box in the middle of the title bar, as in Windows 11
// Settings: see-through on the window's acrylic or Mica, also while
// typing (with an accent underline then).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: box

    property alias text: input.text
    property string placeholder

    implicitHeight: 32
    radius: 5
    color: input.activeFocus ? Theme.fieldActive : (hover.hovered ? Theme.cardHover : Theme.control)
    border.width: 1
    border.color: Theme.cardBorder

    HoverHandler { id: hover }

    Rectangle {
        // The bottom edge: a thin line, the accent while typing.
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: input.activeFocus ? 2 : 1
        radius: 1
        color: input.activeFocus ? Theme.accent : (Theme.dark ? Qt.rgba(1, 1, 1, 0.14) : Qt.rgba(0, 0, 0, 0.16))
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 4
        spacing: 4

        TextInput {
            id: input
            cursorDelegate: Caret {}  // stops blinking like Windows' caret
            // Like a Windows text box: in the Tab order, the text cursor over it and
            // (in a layout) the full height of its box. A plain TextInput has neither.
            activeFocusOnTab: true
            HoverHandler { cursorShape: Qt.IBeamCursor }
            Layout.fillHeight: true
            verticalAlignment: TextInput.AlignVCenter
            Layout.fillWidth: true
            color: Theme.text
            selectionColor: Theme.accent
            selectedTextColor: "#FFFFFF"
            font.pixelSize: 14
            clip: true
            Accessible.role: Accessible.EditableText
            Accessible.name: box.placeholder
            Keys.onEscapePressed: text = ""

            Text {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width
                text: box.placeholder
                color: Theme.subtext
                font.pixelSize: 14
                elide: Text.ElideRight
                visible: input.text.length === 0
            }
        }
        Rectangle {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 24
            radius: 4
            color: input.text.length > 0 && clearHover.hovered ? Theme.hover : "transparent"
            Accessible.role: input.text.length > 0 ? Accessible.Button : Accessible.Graphic
            Accessible.name: box.placeholder
            Glyph {
                anchors.centerIn: parent
                width: input.text.length > 0 ? 10 : 15
                height: width
                lineWidth: input.text.length > 0 ? 1.2 : 1.3
                kind: input.text.length > 0 ? "close" : "search"
                color: Theme.subtext
            }
            HoverHandler { id: clearHover }
            TapHandler {
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: {
                    if (input.text.length > 0)
                        input.text = "";
                    input.forceActiveFocus();
                }
            }
        }
    }

    function forceInputFocus() {
        input.forceActiveFocus();
    }
}
