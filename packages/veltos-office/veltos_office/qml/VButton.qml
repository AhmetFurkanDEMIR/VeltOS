// A Windows 11 button: accent (filled) or standard (light with a border).
import QtQuick
import "."

Rectangle {
    id: button

    property string text
    property bool accent: false
    property bool enabledState: true
    signal clicked()

    implicitWidth: Math.max(Math.round(96 * Theme.textScale), label.implicitWidth + 32)
    implicitHeight: Math.round(32 * Theme.textScale)
    radius: Theme.radius
    color: !enabledState ? (accent ? Theme.disabled : Theme.hover)
           : accent ? (tap.pressed ? Qt.darker(Theme.accent, 1.15) : hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                    : (tap.pressed ? Theme.pressed : hover.hovered ? Theme.hover : Theme.card)
    border.width: accent ? 0 : 1
    border.color: Theme.cardBorder
    Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 80 } }
    Accessible.role: Accessible.Button
    Accessible.name: text
    activeFocusOnTab: enabledState
    Keys.onReturnPressed: if (enabledState) clicked()
    Keys.onSpacePressed: if (enabledState) clicked()

    Text {
        id: label
        anchors.centerIn: parent
        text: button.text
        color: button.accent ? "#FFFFFF" : (button.enabledState ? Theme.text : Theme.disabled)
        font.pixelSize: Theme.fontSize
        renderType: Text.NativeRendering
    }
    HoverHandler { id: hover; enabled: button.enabledState }
    TapHandler {
        id: tap
        enabled: button.enabledState
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
}
