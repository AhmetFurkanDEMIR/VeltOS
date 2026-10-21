// A WinRAR toolbar button: a large colourful picture above its name, flat
// with Windows 11's hover and pressed fills.
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: button
    property string picture: ""
    implicitWidth: Math.max(68, label.implicitWidth + 16)
    implicitHeight: 70
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    Accessible.name: text

    background: Rectangle {
        radius: Theme.smallRadius
        color: button.down ? Theme.pressed : (button.hovered && button.enabled ? Theme.hover : "transparent")
        Behavior on color { ColorAnimation { duration: 83 } }
    }
    contentItem: Item {
        opacity: button.enabled ? 1 : 0.4
        Image {
            id: image
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 6
            width: 32
            height: 32
            sourceSize.width: 64
            sourceSize.height: 64
            source: Qt.resolvedUrl("icons/" + button.picture + ".svg")
        }
        Text {
            id: label
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: image.bottom
            anchors.topMargin: 5
            text: button.text
            color: Theme.text
            font.pixelSize: Theme.captionSize
        }
    }
}
