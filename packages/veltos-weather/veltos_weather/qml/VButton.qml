// A Windows 11 button: standard (card) or accent.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: button
    property string text
    property string glyph
    property bool primary: false
    property bool enabledState: true
    signal clicked()
    implicitWidth: Math.max(96, row.implicitWidth + 32)
    implicitHeight: 32
    radius: 5
    opacity: enabledState ? 1 : 0.5
    color: primary ? (hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                   : (hover.hovered ? Theme.cardHover : Theme.card)
    border.width: primary ? 0 : 1
    border.color: Theme.cardBorder
    Accessible.role: Accessible.Button
    Accessible.name: text
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Glyph {
            visible: button.glyph !== ""
            name: button.glyph
            tint: button.primary ? "#FFFFFF" : Theme.text
        }
        Text {
            visible: button.text !== ""
            text: button.text
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.bodySize
        }
    }
    HoverHandler { id: hover; enabled: button.enabledState }
    TapHandler {
        enabled: button.enabledState
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
}
