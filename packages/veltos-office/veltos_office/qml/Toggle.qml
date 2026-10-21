// A Windows 11 toggle switch (40 x 20, the knob grows on hover).
import QtQuick
import "."

Item {
    id: toggle

    property bool checked: false
    property string label
    signal toggled(bool on)

    implicitWidth: 40
    implicitHeight: 20
    Accessible.role: Accessible.CheckBox
    Accessible.name: label
    Accessible.checked: checked
    activeFocusOnTab: true
    Keys.onSpacePressed: toggled(!checked)
    Keys.onReturnPressed: toggled(!checked)

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: toggle.checked ? (hover.hovered ? Qt.lighter(Theme.accent, 1.1) : Theme.accent)
                              : (hover.hovered ? Theme.hover : "transparent")
        border.width: toggle.checked ? 0 : 1
        border.color: Theme.subtext
        Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 120 } }
    }
    Rectangle {
        id: knob
        readonly property int size: hover.hovered ? 14 : 12
        width: tap.pressed ? size + 4 : size
        height: size
        radius: height / 2
        anchors.verticalCenter: parent.verticalCenter
        x: toggle.checked ? parent.width - width - 4 : 4
        color: toggle.checked ? "#FFFFFF" : Theme.subtext
        Behavior on x { enabled: Theme.anim > 0; NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
        Behavior on width { enabled: Theme.anim > 0; NumberAnimation { duration: 100 } }
        Behavior on height { enabled: Theme.anim > 0; NumberAnimation { duration: 100 } }
    }
    HoverHandler { id: hover }
    TapHandler {
        id: tap
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: toggle.toggled(!toggle.checked)
    }
}
