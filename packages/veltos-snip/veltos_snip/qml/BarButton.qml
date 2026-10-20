// Command bar button of Windows 11 apps: a glyph (and optional text, an
// optional chevron), transparent until pointed at; "checked" shows the
// selected tool with an accent line below it, like Snipping Tool.
import QtQuick
import QtQuick.Controls

AbstractButton {
    id: button
    property string glyph: ""
    property string tip: ""
    property bool chevron: false
    property color dot: "transparent"     // colour of a pen tool
    property bool showDot: false
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    implicitHeight: 36
    implicitWidth: row.implicitWidth + 16
    Accessible.name: tip || text

    background: Rectangle {
        radius: Theme.smallRadius
        color: button.down ? Theme.pressed : (button.checked ? Theme.selected : (button.hovered ? Theme.hover : "transparent"))
        Behavior on color { ColorAnimation { duration: 83 } }
        Rectangle {
            visible: button.checked
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 2
            width: 16
            height: 3
            radius: 1.5
            color: Theme.accent
        }
        Rectangle {
            visible: button.visualFocus
            anchors.fill: parent
            radius: Theme.smallRadius
            color: "transparent"
            border.width: 2
            border.color: Theme.text
        }
    }
    contentItem: Item {
        implicitWidth: row.implicitWidth
        implicitHeight: row.implicitHeight
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 6
            Item {
                visible: button.glyph !== ""
                width: 20
                height: 20
                anchors.verticalCenter: parent.verticalCenter
                Glyph {
                    anchors.fill: parent
                    kind: button.glyph
                    color: button.enabled ? Theme.text : Theme.subtext
                }
                Rectangle {
                    visible: button.showDot
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: -2
                    width: 8
                    height: 8
                    radius: 4
                    color: button.dot
                    border.width: 1
                    border.color: Theme.card
                }
            }
            Text {
                visible: button.text !== ""
                anchors.verticalCenter: parent.verticalCenter
                text: button.text
                color: button.enabled ? Theme.text : Theme.subtext
                font.pixelSize: Theme.bodySize
            }
            Glyph {
                visible: button.chevron
                anchors.verticalCenter: parent.verticalCenter
                width: 12
                height: 12
                kind: "chevron"
                color: Theme.subtext
            }
        }
    }
    ToolTip.visible: tip !== "" && hovered
    ToolTip.delay: 600
    ToolTip.text: tip
}
