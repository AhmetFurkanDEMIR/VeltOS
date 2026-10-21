// Status bar of Windows 11 Notepad: line and column, characters (or the
// selection), zoom, line ending and encoding. The line ending and the
// encoding open a menu to change them.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: bar

    property int line: 1
    property int column: 1
    property int characters: 0
    property int selected: 0
    signal pickEol(var item)
    signal pickEncoding(var item)

    implicitHeight: 30
    color: Theme.statusBar

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: Theme.separator
    }

    component Part: Rectangle {
        id: part
        property string text
        property bool clickable: false
        signal clicked()
        Layout.fillHeight: true
        Layout.preferredWidth: label.implicitWidth + 28
        color: clickable && hover.hovered ? Theme.hover : "transparent"
        Accessible.role: clickable ? Accessible.Button : Accessible.StaticText
        Accessible.name: text
        Rectangle {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: 1
            height: 14
            color: Theme.separator
        }
        Text {
            id: label
            anchors.centerIn: parent
            text: part.text
            color: Theme.text
            font.pixelSize: Theme.smallFont
        }
        HoverHandler { id: hover; enabled: part.clickable }
        TapHandler { enabled: part.clickable; onTapped: part.clicked() }
    }

    RowLayout {
        anchors.fill: parent
        anchors.topMargin: 1
        spacing: 0

        Text {
            Layout.leftMargin: 14
            Layout.preferredWidth: 150
            text: backend.texts.line_column.replace("{line}", bar.line).replace("{column}", bar.column)
            color: Theme.text
            font.pixelSize: Theme.smallFont
        }
        Part {
            Layout.preferredWidth: Math.max(140, implicitWidth)
            text: bar.selected > 0
                  ? backend.texts.selected_of.replace("{selected}", bar.selected).replace("{count}", bar.characters)
                  : bar.characters === 1 ? backend.texts.one_character
                  : backend.texts.characters.replace("{count}", bar.characters)
        }
        Item { Layout.fillWidth: true }
        Part {
            text: backend.zoom + "%"
        }
        Part {
            id: eolPart
            clickable: true
            text: backend.texts["eol_" + (backend.current.eol || "LF")]
            onClicked: bar.pickEol(eolPart)
        }
        Part {
            id: encodingPart
            clickable: true
            Layout.rightMargin: 8
            text: backend.current.encoding || "UTF-8"
            onClicked: bar.pickEncoding(encodingPart)
        }
    }
}
