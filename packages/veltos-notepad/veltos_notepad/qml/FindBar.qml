// Windows 11 Notepad's find and replace panel, floating at the top right of
// the text: the chevron shows the replace row; up and down arrows find the
// previous and next match; the options menu has "Match case" and "Wrap
// around".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: panel

    property bool replacing: false
    property bool matchCase: false
    property bool wrapAround: true
    property alias query: findField.text
    property alias replacement: replaceField.text
    signal findNext(bool forward)
    signal replaceOne()
    signal replaceAll()
    signal closed()

    function show(replace) {
        replacing = replace;
        visible = true;
        findField.forceActiveFocus();
        findField.selectAll();
    }
    function hide() {
        visible = false;
        closed();
    }

    visible: false
    implicitWidth: 420
    implicitHeight: column.implicitHeight + 16
    radius: 8
    color: Theme.menu
    border.width: 1
    border.color: Theme.fieldBorder
    Rectangle {
        z: -1
        anchors.fill: parent
        anchors.margins: -3
        anchors.bottomMargin: -5
        radius: 11
        color: "#000000"
        opacity: Theme.dark ? 0.3 : 0.07
    }

    component Field: TextField {
        Layout.fillWidth: true
        Layout.preferredHeight: 32
        color: Theme.text
        placeholderTextColor: Theme.subtext
        selectByMouse: true
        font.pixelSize: Theme.fontSize
        background: Rectangle {
            radius: 4
            color: Theme.field
            border.width: 1
            border.color: parent.activeFocus ? Theme.accent : Theme.fieldBorder
            Rectangle {
                visible: parent.parent.activeFocus
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 1
                height: 2
                color: Theme.accent
            }
        }
    }

    component SmallButton: Rectangle {
        id: sb
        property string glyph
        property string label
        property string text
        signal clicked()
        implicitWidth: text !== "" ? buttonText.implicitWidth + 24 : 32
        implicitHeight: 32
        radius: 4
        color: sbTap.pressed ? Theme.pressed : (sbHover.hovered ? Theme.hover : "transparent")
        border.width: text !== "" ? 1 : 0
        border.color: Theme.fieldBorder
        Accessible.role: Accessible.Button
        Accessible.name: text !== "" ? text : label
        Glyph {
            visible: sb.glyph !== ""
            anchors.centerIn: parent
            width: 11
            height: 11
            kind: sb.glyph
        }
        Text {
            id: buttonText
            visible: sb.text !== ""
            anchors.centerIn: parent
            text: sb.text
            color: Theme.text
            font.pixelSize: Theme.fontSize
        }
        ToolTip.visible: sb.text === "" && sbHover.hovered
        ToolTip.delay: 600
        ToolTip.text: sb.label
        HoverHandler { id: sbHover }
        TapHandler { id: sbTap; onTapped: sb.clicked() }
    }

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 8
        spacing: 6

        RowLayout {
            spacing: 4
            SmallButton {
                glyph: panel.replacing ? "chevron-up" : "chevron-down"
                label: backend.texts.toggle_replace
                onClicked: panel.replacing = !panel.replacing
            }
            Field {
                id: findField
                placeholderText: backend.texts.find_placeholder
                onAccepted: panel.findNext(true)
                Keys.onEscapePressed: panel.hide()
            }
            SmallButton {
                glyph: "arrow-up"
                label: backend.texts.find_previous
                onClicked: panel.findNext(false)
            }
            SmallButton {
                glyph: "arrow-down"
                label: backend.texts.find_next
                onClicked: panel.findNext(true)
            }
            SmallButton {
                id: optionsButton
                glyph: "gear"
                label: backend.texts.options
                onClicked: options.openAt(optionsButton, 0, optionsButton.height + 4)
            }
            SmallButton {
                glyph: "close"
                label: backend.texts.close
                onClicked: panel.hide()
            }
        }
        RowLayout {
            visible: panel.replacing
            spacing: 4
            Item { Layout.preferredWidth: 32 }
            Field {
                id: replaceField
                placeholderText: backend.texts.replace_placeholder
                onAccepted: panel.replaceOne()
                Keys.onEscapePressed: panel.hide()
            }
            SmallButton {
                text: backend.texts.replace
                onClicked: panel.replaceOne()
            }
            SmallButton {
                text: backend.texts.replace_all
                onClicked: panel.replaceAll()
            }
        }
    }

    WinMenu {
        id: options
        minimumWidth: 220
        items: [
            { text: backend.texts.match_case, checked: panel.matchCase, action: "case" },
            { text: backend.texts.wrap_around, checked: panel.wrapAround, action: "wrap" }
        ]
        onTriggered: action => {
            if (action === "case")
                panel.matchCase = !panel.matchCase;
            else
                panel.wrapAround = !panel.wrapAround;
        }
    }
}
