// Title bar with tabs, as in Windows 11 File Explorer: one tab per open
// location (icon, name, close), "+" for a new tab, then minimise,
// maximise and close. Dragging the empty part moves the window;
// double-clicking it maximises.
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: bar

    property var window
    signal closeWindow()

    implicitHeight: 40
    color: Theme.titleBar

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        spacing: 0

        Repeater {
            model: backend.tabs
            delegate: Item {
                id: tabItem

                required property var modelData
                required property int index
                readonly property bool current: index === backend.currentIndex

                Layout.alignment: Qt.AlignBottom
                Layout.preferredWidth: Math.min(240, Math.max(120, (bar.width - 300) / Math.max(1, backend.tabs.length)))
                Layout.preferredHeight: 34

                // The current tab joins the command bar below it.
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
                    // Divider between inactive tabs.
                    visible: !tabItem.current && tabItem.index + 1 !== backend.currentIndex
                             && tabItem.index < backend.tabs.length - 1
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: -2
                    width: 1
                    height: 16
                    color: Theme.separator
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 6
                    anchors.bottomMargin: tabItem.current ? 0 : 4
                    spacing: 8
                    Kirigami.Icon {
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                        source: tabItem.modelData.icon
                    }
                    Text {
                        Layout.fillWidth: true
                        text: tabItem.modelData.query !== ""
                              ? backend.format("search_results", "name", tabItem.modelData.title)
                              : tabItem.modelData.title
                        color: Theme.text
                        font.pixelSize: Theme.smallFont
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 24
                        radius: 4
                        color: closeHover.hovered ? Theme.pressed : "transparent"
                        visible: tabItem.current || tabHover.hovered
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.text("close_tab")
                        Glyph {
                            anchors.centerIn: parent
                            width: 8
                            height: 8
                            kind: "close"
                        }
                        HoverHandler { id: closeHover }
                        TapHandler {
                            onTapped: {
                                if (!backend.closeTab(tabItem.index))
                                    bar.closeWindow();
                            }
                        }
                    }
                }

                HoverHandler { id: tabHover }
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onTapped: backend.setCurrentIndex(tabItem.index)
                }
                TapHandler {
                    acceptedButtons: Qt.MiddleButton
                    onTapped: if (!backend.closeTab(tabItem.index)) bar.closeWindow()
                }
            }
        }

        IconButton {
            Layout.leftMargin: 4
            Layout.preferredWidth: 32
            icon: "list-add"
            tooltip: backend.text("new_tab")
            onClicked: backend.newTab("home:")
        }

        // Empty part: moves the window.
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
                kind: wb.glyph
                color: wbHover.hovered && wb.danger ? "#FFFFFF" : Theme.text
            }
            HoverHandler { id: wbHover }
            TapHandler { onTapped: wb.clicked() }
        }

        WindowButton {
            glyph: "minimize"
            label: backend.text("minimize")
            onClicked: bar.window.showMinimized()
        }
        WindowButton {
            glyph: bar.window && bar.window.maximized ? "restore" : "maximize"
            label: bar.window && bar.window.maximized ? backend.text("restore_down") : backend.text("maximize")
            onClicked: bar.window.toggleMaximized()
        }
        WindowButton {
            glyph: "close"
            label: backend.text("close")
            danger: true
            onClicked: bar.closeWindow()
        }
    }
}
