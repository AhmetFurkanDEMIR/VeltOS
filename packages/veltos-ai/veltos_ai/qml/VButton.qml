// A Windows 11 button: standard (card) or accent.
import QtQuick
import "."

Rectangle {
    id: button
    property string text
    property bool primary: false
    property bool enabledState: true
    signal clicked()
    implicitWidth: Math.max(88, label.implicitWidth + 28)
    implicitHeight: 32
    radius: 5
    opacity: enabledState ? 1 : 0.5
    color: primary ? (hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                   : (hover.hovered ? Theme.cardHover : Theme.card)
    border.width: primary ? 0 : 1
    border.color: Theme.cardBorder
    Accessible.role: Accessible.Button
    Accessible.name: text
    Text {
        id: label
        anchors.centerIn: parent
        text: button.text
        color: button.primary ? Theme.accentText : Theme.text
        font.pixelSize: Theme.bodySize
    }
    HoverHandler { id: hover; enabled: button.enabledState }
    TapHandler {
        enabled: button.enabledState
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
}
