// Windows 11 toggle switch, with its "On" / "Off" label on the left.
// It does not change itself: it asks (toggled) and shows `checked`, which
// the backend updates at once.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

RowLayout {
    id: toggle

    property bool checked: false
    property bool enabledState: true
    property bool showLabel: true
    property string accessibleName
    signal toggled(bool checked)

    function flip() {
        if (enabledState)
            toggled(!checked);
    }

    spacing: 12
    opacity: enabledState ? 1 : 0.45

    Label {
        visible: toggle.showLabel
        text: toggle.checked ? backend.text("on") : backend.text("off")
        color: Theme.text
        font.pixelSize: Theme.titleSize
    }

    Rectangle {
        id: track
        Layout.preferredWidth: 40
        Layout.preferredHeight: 20
        radius: 10
        color: toggle.checked ? (hover.hovered ? Qt.lighter(Theme.accent, 1.1) : Theme.accent)
                              : (hover.hovered ? Theme.cardHover : Theme.card)
        border.width: toggle.checked ? 0 : 1
        border.color: Theme.subtext
        activeFocusOnTab: true
        Accessible.role: Accessible.CheckBox
        Accessible.name: toggle.accessibleName
        Accessible.checked: toggle.checked
        Accessible.onToggleAction: toggle.flip()
        Accessible.onPressAction: toggle.flip()
        Keys.onSpacePressed: toggle.flip()
        Keys.onReturnPressed: toggle.flip()

        Rectangle {
            readonly property int size: tap.pressed ? 14 : (hover.hovered ? 14 : 12)
            width: tap.pressed ? 17 : size
            height: size
            radius: size / 2
            anchors.verticalCenter: parent.verticalCenter
            x: toggle.checked ? parent.width - width - 4 : 4
            color: toggle.checked ? "#FFFFFF" : Theme.subtext
            Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            Behavior on width { NumberAnimation { duration: 90 } }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: height / 2
            color: "transparent"
            border.width: 2
            border.color: Theme.text
            visible: track.activeFocus
        }

        HoverHandler { id: hover; enabled: toggle.enabledState; cursorShape: Qt.PointingHandCursor }
        TapHandler { id: tap; enabled: toggle.enabledState; onTapped: toggle.flip() }
    }
}
