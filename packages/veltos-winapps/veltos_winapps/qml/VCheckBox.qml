// Windows 11 check box: a rounded square, filled with the accent colour
// and a white tick when checked.
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: box
    checkable: true
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    implicitWidth: indicator.width + 8 + label.implicitWidth
    implicitHeight: 32
    Accessible.role: Accessible.CheckBox
    Accessible.name: text
    Keys.onSpacePressed: toggle()

    contentItem: Item {
        Rectangle {
            id: indicator
            anchors.verticalCenter: parent.verticalCenter
            width: 20
            height: 20
            radius: Theme.smallRadius
            color: box.checked ? (box.down ? Qt.darker(Theme.accent, 1.12) : (box.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent))
                               : (box.hovered ? Theme.controlHover : Theme.control)
            border.width: box.checked ? 0 : 1
            border.color: Theme.controlBorder
            Behavior on color { ColorAnimation { duration: 83 } }

            // The tick: two strokes.
            Canvas {
                id: tick
                anchors.fill: parent
                visible: box.checked
                property color colour: Theme.accentText
                onColourChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = colour;
                    ctx.lineWidth = 1.5;
                    ctx.lineCap = "round";
                    ctx.lineJoin = "round";
                    ctx.beginPath();
                    ctx.moveTo(5.5, 10.5);
                    ctx.lineTo(8.5, 13.5);
                    ctx.lineTo(14.5, 6.5);
                    ctx.stroke();
                }
            }
            Rectangle {
                visible: box.visualFocus
                anchors.fill: parent
                anchors.margins: -3
                radius: Theme.smallRadius + 2
                color: "transparent"
                border.width: 2
                border.color: Theme.text
            }
        }
        Text {
            id: label
            anchors.left: indicator.right
            anchors.leftMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            text: box.text
            color: Theme.text
            font.pixelSize: Theme.bodySize
        }
    }
}
