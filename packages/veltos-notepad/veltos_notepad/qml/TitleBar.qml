// Title bar with tabs, as in Windows 11 Notepad: one tab per file (its
// name; a dot while it has unsaved changes, the close button on hover),
// "+" for a new tab, then minimise, maximise and close. The empty part
// moves the window; double-clicking it maximises.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: bar

    property var window
    signal closeTab(int index)
    signal closeWindow()

    implicitHeight: 40
    color: Theme.tabStrip

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        spacing: 0

        Repeater {
            model: backend.tabs
            delegate: Item {
                id: tabItem

                required property int index
                required property string title
                required property bool modified
                readonly property bool current: index === backend.currentIndex

                Layout.alignment: Qt.AlignBottom
                Layout.preferredWidth: Math.min(220, Math.max(110, (bar.width - 260) / Math.max(1, backend.tabCount)))
                Layout.preferredHeight: 34
                Accessible.role: Accessible.PageTab
                Accessible.name: title
                Accessible.selected: current

                // The current tab joins the menu row below it.
                Rectangle {
                    anchors.fill: parent
                    anchors.bottomMargin: tabItem.current ? -1 : 4
                    radius: 8
                    color: tabItem.current ? Theme.toolbar : (tabHover.hovered ? Theme.hover : "transparent")
                    Rectangle {
                        visible: tabItem.current
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 8
                        color: Theme.toolbar
                    }
                }
                Rectangle {
                    visible: !tabItem.current && tabItem.index + 1 !== backend.currentIndex
                             && tabItem.index < backend.tabCount - 1
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: -2
                    width: 1
                    height: 16
                    color: Theme.separator
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 6
                    anchors.bottomMargin: tabItem.current ? 0 : 4
                    spacing: 8
                    Text {
                        Layout.fillWidth: true
                        text: tabItem.title
                        color: Theme.text
                        font.pixelSize: Theme.smallFont
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 24
                        radius: 4
                        color: closeHover.hovered ? Theme.pressed : "transparent"
                        visible: tabItem.current || tabHover.hovered || tabItem.modified
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.close_tab
                        // Unsaved: a dot, the close button under the pointer.
                        Glyph {
                            anchors.centerIn: parent
                            visible: tabItem.modified && !tabHover.hovered
                            width: 7
                            height: 7
                            kind: "dot"
                        }
                        Glyph {
                            anchors.centerIn: parent
                            visible: !tabItem.modified || tabHover.hovered
                            width: 9
                            height: 9
                            kind: "close"
                        }
                        HoverHandler { id: closeHover }
                        TapHandler { onTapped: bar.closeTab(tabItem.index) }
                    }
                }

                HoverHandler { id: tabHover }
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onTapped: backend.setCurrentIndex(tabItem.index)
                }
                TapHandler {
                    acceptedButtons: Qt.MiddleButton
                    onTapped: bar.closeTab(tabItem.index)
                }
            }
        }

        Rectangle {
            Layout.leftMargin: 4
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            radius: Theme.radius
            color: addTap.pressed ? Theme.pressed : (addHover.hovered ? Theme.hover : "transparent")
            Accessible.role: Accessible.Button
            Accessible.name: backend.texts.add_tab
            Glyph {
                anchors.centerIn: parent
                width: 11
                height: 11
                kind: "add"
            }
            HoverHandler { id: addHover }
            TapHandler { id: addTap; onTapped: backend.newTab() }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            DragHandler {
                target: null
                onActiveChanged: if (active) bar.window.startSystemMove()
            }
            TapHandler {
                onDoubleTapped: bar.window.toggleMaximized()
            }
        }

        component WindowButton: Rectangle {
            id: wb
            property string glyph
            property string label
            property bool danger: false
            signal clicked()
            Layout.preferredWidth: 46
            Layout.fillHeight: true
            color: wbHover.hovered ? (danger ? Theme.closeHover : Theme.hover) : "transparent"
            Accessible.role: Accessible.Button
            Accessible.name: label
            Glyph {
                anchors.centerIn: parent
                width: 10
                height: 10
                kind: wb.glyph
                color: wbHover.hovered && wb.danger ? "#FFFFFF" : Theme.text
            }
            HoverHandler { id: wbHover }
            TapHandler { onTapped: wb.clicked() }
        }

        WindowButton {
            glyph: "minimize"
            label: backend.texts.minimize
            onClicked: bar.window.showMinimized()
        }
        WindowButton {
            glyph: bar.window && bar.window.maximized ? "restore" : "maximize"
            label: bar.window && bar.window.maximized ? backend.texts.restore_down : backend.texts.maximize
            onClicked: bar.window.toggleMaximized()
        }
        WindowButton {
            glyph: "close"
            label: backend.texts.close
            danger: true
            onClicked: bar.closeWindow()
        }
    }
}
