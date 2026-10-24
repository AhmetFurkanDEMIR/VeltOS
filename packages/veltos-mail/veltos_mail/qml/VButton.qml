// A Fluent button: "primary" filled with Outlook's blue, or standard
// (white with a light border); optional icon before the text.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: button

    property string text
    property string icon: ""
    property bool primary: false
    property bool active: true
    signal clicked()

    implicitWidth: Math.max(Math.round(80 * Theme.textScale), row.implicitWidth + 24)
    implicitHeight: Math.round(32 * Theme.textScale)
    radius: Theme.radius
    color: !active ? (primary ? Theme.disabled : Theme.hover)
           : primary ? (tap.pressed ? Theme.brandPressed : hover.hovered ? Theme.brandHover : Theme.brand)
                     : (tap.pressed ? Theme.pressed : hover.hovered ? Theme.hover : Theme.card)
    border.width: primary ? 0 : 1
    border.color: Theme.fieldBorder
    Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 90 } }
    Accessible.role: Accessible.Button
    Accessible.name: text
    activeFocusOnTab: active
    Keys.onReturnPressed: if (active) clicked()
    Keys.onSpacePressed: if (active) clicked()

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 6
        Glyph {
            visible: button.icon !== ""
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            kind: button.icon
            color: label.color
        }
        Text {
            id: label
            text: button.text
            color: button.primary ? "#FFFFFF" : (button.active ? Theme.text : Theme.disabled)
            font.pixelSize: Theme.fontSize
            font.weight: button.primary ? Font.DemiBold : Font.Normal
        }
    }
    HoverHandler { id: hover; enabled: button.active; cursorShape: Qt.PointingHandCursor }
    TapHandler {
        id: tap
        enabled: button.active
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
}
