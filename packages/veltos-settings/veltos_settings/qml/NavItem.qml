// One entry of the navigation pane: icon + label, a rounded highlight and
// an accent bar on the left when selected (as in Windows 11 Settings).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: item

    property string icon
    property string text
    property bool selected: false
    property bool external: false
    signal clicked()

    implicitHeight: 40
    radius: 6
    color: selected ? Theme.navSelected : (hover.hovered ? Theme.navHover : "transparent")
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.onPressAction: clicked()
    Keys.onReturnPressed: clicked()
    Keys.onSpacePressed: clicked()

    Rectangle {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: 3
        height: item.selected ? 18 : 0
        radius: 2
        color: Theme.accent
        Behavior on height { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 10
        spacing: 12

        Kirigami.Icon {
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            source: item.icon
        }
        Label {
            Layout.fillWidth: true
            text: item.text
            color: Theme.text
            font.pixelSize: 14
            font.weight: item.selected ? Font.DemiBold : Font.Normal
            elide: Text.ElideRight
        }
        Kirigami.Icon {
            visible: item.external
            Layout.preferredWidth: 14
            Layout.preferredHeight: 14
            source: "window-new"
            color: Theme.subtext
            isMask: true
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        border.width: item.activeFocus ? 2 : 0
        border.color: Theme.accent
    }

    HoverHandler { id: hover }
    TapHandler { onTapped: item.clicked() }
}
