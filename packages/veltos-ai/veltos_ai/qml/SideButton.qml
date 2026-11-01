// A row of the wide window's side bar: icon and label, Windows 11's
// navigation look (a soft fill on hover, a stronger one while active).
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: button
    property string icon
    property string label
    property bool enabledState: true
    property bool active: false
    signal clicked()
    implicitHeight: Math.max(38, text.implicitHeight + 16)
    radius: 6
    opacity: enabledState ? 1 : 0.45
    color: active ? Theme.activeFill : hover.hovered && enabledState ? Theme.hover : "transparent"
    Accessible.role: Accessible.Button
    Accessible.name: label
    Behavior on color { ColorAnimation { duration: 120 } }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 10
        Kirigami.Icon {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            source: button.icon
            isMask: true
            color: Theme.text
        }
        Text {
            id: text
            Layout.fillWidth: true
            text: button.label
            color: Theme.text
            font.pixelSize: Theme.bodySize
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
    }
    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler {
        enabled: button.enabledState
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: button.clicked()
    }
}
