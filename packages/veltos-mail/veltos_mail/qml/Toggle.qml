// The Windows 11 toggle switch.
import QtQuick
import "."

Rectangle {
    id: toggle

    property bool on: false
    signal toggled(bool on)

    implicitWidth: 40
    implicitHeight: 20
    radius: 10
    color: on ? (hover.hovered ? Theme.brandHover : Theme.brand) : "transparent"
    border.width: on ? 0 : 1
    border.color: Theme.subtext
    Accessible.role: Accessible.CheckBox
    Accessible.checked: on
    Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 100 } }

    Rectangle {
        width: hover.hovered ? 14 : 12
        height: width
        radius: width / 2
        anchors.verticalCenter: parent.verticalCenter
        x: toggle.on ? toggle.width - width - 4 : 4
        color: toggle.on ? "#FFFFFF" : Theme.subtext
        Behavior on x { enabled: Theme.anim > 0; NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        Behavior on width { enabled: Theme.anim > 0; NumberAnimation { duration: 90 } }
    }
    HoverHandler { id: hover }
    TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: toggle.toggled(!toggle.on) }
}
