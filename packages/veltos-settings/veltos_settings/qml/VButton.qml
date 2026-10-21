// Windows 11 style button: neutral (default) or accent-filled (primary).
import QtQuick
import QtQuick.Controls
import "."

Rectangle {
    id: button

    property string text
    property bool primary: false
    property bool enabledState: true
    signal clicked()

    implicitWidth: Math.max(96, label.implicitWidth + 32)
    implicitHeight: 32
    radius: 5
    opacity: enabledState ? 1 : 0.5
    color: primary ? (tap.pressed ? Qt.darker(Theme.accent, 1.15) : hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                   : (tap.pressed ? Theme.cardPressed : hover.hovered ? Theme.cardHover : Theme.card)
    border.width: activeFocus ? 2 : (primary ? 0 : 1)
    border.color: activeFocus ? (primary ? "#FFFFFF" : Theme.accent) : Theme.cardBorder
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.onPressAction: if (enabledState) clicked()
    Keys.onReturnPressed: if (enabledState) clicked()
    Keys.onSpacePressed: if (enabledState) clicked()

    Label {
        id: label
        anchors.centerIn: parent
        text: button.text
        color: button.primary ? "#FFFFFF" : Theme.text
        font.pixelSize: 13
    }

    HoverHandler { id: hover; enabled: button.enabledState; cursorShape: Qt.PointingHandCursor }
    // ReleaseWithinBounds: the button takes the tap for itself (a parent's
    // handler does not see it as well).
    TapHandler { id: tap; enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
}
