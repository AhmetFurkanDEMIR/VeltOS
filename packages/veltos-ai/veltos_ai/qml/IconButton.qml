// A square icon button of the pane's header, with a tooltip.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: button
    property string icon
    property string tip
    property bool enabledState: true
    signal clicked()
    implicitWidth: 34
    implicitHeight: 34
    radius: 5
    opacity: enabledState ? 1 : 0.4
    color: hover.hovered && enabledState ? Theme.hover : "transparent"
    Accessible.role: Accessible.Button
    Accessible.name: tip
    Kirigami.Icon {
        anchors.centerIn: parent
        width: 16
        height: 16
        source: button.icon
        isMask: true
        color: Theme.text
    }
    HoverHandler { id: hover }
    TapHandler {
        enabled: button.enabledState
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
    ToolTip.visible: hover.hovered && tip !== ""
    ToolTip.delay: 500
    ToolTip.text: tip
}
