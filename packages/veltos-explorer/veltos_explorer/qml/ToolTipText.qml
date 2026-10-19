// A small Windows 11 style tooltip under its parent, shown after a moment.
import QtQuick
import "."

Rectangle {
    id: tip

    property string text
    property bool shown: false

    z: 1000
    visible: opacity > 0
    opacity: 0
    width: label.implicitWidth + 16
    height: label.implicitHeight + 10
    x: Math.round((parent.width - width) / 2)
    y: parent.height + 6
    radius: 4
    color: Theme.menu
    border.width: 1
    border.color: Theme.fieldBorder

    Text {
        id: label
        anchors.centerIn: parent
        text: tip.text
        color: Theme.text
        font.pixelSize: Theme.smallFont
    }

    Timer {
        id: delay
        interval: 600
        onTriggered: tip.opacity = 1
    }
    onShownChanged: {
        if (shown) {
            delay.restart();
        } else {
            delay.stop();
            opacity = 0;
        }
    }
    Behavior on opacity { NumberAnimation { duration: 120 } }
}
