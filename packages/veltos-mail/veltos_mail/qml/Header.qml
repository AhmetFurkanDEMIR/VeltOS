// Outlook's header: the brand blue band with the app's name on the left,
// the search box in the middle of the window, Settings and the window
// buttons on the right. Dragging the band moves the window.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: bar

    property var window
    property alias searchText: searchInput.text
    signal openSettings()
    signal closeWindow()

    function focusSearch() { searchInput.forceActiveFocus(); searchInput.selectAll(); }

    implicitHeight: Theme.headerHeight
    color: Theme.header

    // Empty parts: move the window; double click maximises.
    Item {
        anchors.fill: parent
        DragHandler {
            target: null
            onActiveChanged: if (active) bar.window.startSystemMove()
        }
        TapHandler { onDoubleTapped: bar.window.toggleMaximized() }
    }

    RowLayout {
        anchors.left: parent.left
        anchors.leftMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10
        Text {
            text: backend.text("app_title")
            color: Theme.headerText
            font.pixelSize: Math.round(15 * Theme.textScale)
            font.weight: Font.DemiBold
        }
    }

    // Search, centred on the window like Outlook's.
    Rectangle {
        id: searchBox
        anchors.centerIn: parent
        width: Math.min(Math.round(520 * Theme.textScale), bar.width - 2 * (buttons.width + 190))
        height: 32
        radius: Theme.radius
        visible: width > 160
        color: Theme.dark ? (searchInput.activeFocus ? "#3D3D3D" : "#333333") : "#FFFFFF"
        opacity: searchInput.activeFocus || searchHover.hovered || searchInput.text !== "" || Theme.dark ? 1 : 0.94
        border.width: searchInput.activeFocus ? 1 : 0
        border.color: Theme.dark ? "#5C5C5C" : "#FFFFFF"
        Glyph {
            id: searchIcon
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            width: 16
            height: 16
            kind: "search"
            color: Theme.dark ? "#ADADAD" : Theme.brand
        }
        TextInput {
            id: searchInput
            anchors.left: searchIcon.right
            anchors.leftMargin: 8
            anchors.right: clear.left
            anchors.rightMargin: 4
            anchors.verticalCenter: parent.verticalCenter
            color: Theme.dark ? "#FFFFFF" : "#242424"
            selectionColor: Theme.brand
            font.pixelSize: Theme.fontSize
            clip: true
            selectByMouse: true
            onTextChanged: searchDelay.restart()
            onAccepted: backend.search(text)
            Keys.onEscapePressed: { text = ""; focus = false; }
        }
        Text {
            anchors.fill: searchInput
            verticalAlignment: Text.AlignVCenter
            visible: searchInput.text === ""
            text: backend.text("search")
            color: Theme.dark ? "#ADADAD" : "#616161"
            font.pixelSize: Theme.fontSize
        }
        FlatButton {
            id: clear
            anchors.right: parent.right
            anchors.rightMargin: 2
            anchors.verticalCenter: parent.verticalCenter
            implicitHeight: 28
            visible: searchInput.text !== ""
            icon: "close"
            iconSize: 12
            showText: false
            tip: backend.text("close")
            iconColour: Theme.dark ? "#FFFFFF" : "#424242"
            onClicked: { searchInput.text = ""; backend.search(""); }
        }
        HoverHandler { id: searchHover }
        Timer { id: searchDelay; interval: 300; onTriggered: backend.search(searchInput.text) }
    }

    RowLayout {
        id: buttons
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: 0

        component HeaderButton: Rectangle {
            id: hb
            property string glyph
            property string label
            property bool danger: false
            property int glyphSize: 10
            signal clicked()
            Layout.preferredWidth: 46
            Layout.fillHeight: true
            color: hbTap.pressed ? (danger ? Qt.darker(Theme.closeHover, 1.2) : Theme.headerPressed)
                   : hbHover.hovered ? (danger ? Theme.closeHover : Theme.headerHover) : "transparent"
            Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 80 } }
            Accessible.role: Accessible.Button
            Accessible.name: label
            Glyph {
                anchors.centerIn: parent
                width: hb.glyphSize
                height: hb.glyphSize
                kind: hb.glyph
                color: Theme.headerText
            }
            HoverHandler { id: hbHover }
            TapHandler { id: hbTap; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: hb.clicked() }
        }

        HeaderButton {
            glyph: "settings"
            glyphSize: 18
            label: backend.text("settings")
            onClicked: bar.openSettings()
        }
        Item { Layout.preferredWidth: 8 }
        HeaderButton {
            glyph: "minimize"
            label: backend.text("minimize")
            onClicked: bar.window.showMinimized()
        }
        HeaderButton {
            glyph: bar.window && bar.window.maximized ? "restore" : "maximize"
            label: bar.window && bar.window.maximized ? backend.text("restore") : backend.text("maximize")
            onClicked: bar.window.toggleMaximized()
        }
        HeaderButton {
            glyph: "close-caption"
            label: backend.text("close")
            danger: true
            onClicked: bar.closeWindow()
        }
    }
}
