// A flat command (the simplified ribbon, the reading pane's actions, the
// message list's hover actions): icon, optional label, optional drop-down
// chevron; light background on hover. "split" shows the chevron as its own
// part (Outlook's New mail ▾).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: button

    property string icon: ""
    property string text: ""
    property string tip: text
    property bool showText: true
    property bool dropDown: false
    property bool active: true
    property bool toggled: false
    property bool filledIcon: false
    property color iconColour: Theme.text
    property color hoverColour: Theme.hover
    property int iconSize: 18
    signal clicked()
    signal chevronClicked()

    implicitWidth: row.implicitWidth + (showText && text !== "" ? 16 : 12)
    implicitHeight: 32
    radius: Theme.radius
    color: tap.pressed && active ? Theme.pressed : (hover.hovered && active ? hoverColour
           : (toggled ? Theme.selectedFolder : "transparent"))
    Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 80 } }
    Accessible.role: Accessible.Button
    Accessible.name: tip
    ToolTip.visible: hover.hovered && !(showText && text !== "") && tip !== ""
    ToolTip.delay: 600
    ToolTip.text: tip

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 6
        Glyph {
            visible: button.icon !== ""
            Layout.preferredWidth: button.iconSize
            Layout.preferredHeight: button.iconSize
            kind: button.icon
            filled: button.filledIcon
            color: button.active ? button.iconColour : Theme.disabled
        }
        Text {
            visible: button.showText && button.text !== ""
            text: button.text
            color: button.active ? Theme.text : Theme.disabled
            font.pixelSize: Theme.fontSize
        }
        Glyph {
            visible: button.dropDown
            Layout.preferredWidth: 12
            Layout.preferredHeight: 12
            kind: "chevron-down"
            color: button.active ? Theme.subtext : Theme.disabled
        }
    }
    HoverHandler { id: hover; enabled: button.active }
    TapHandler {
        id: tap
        enabled: button.active
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
}
