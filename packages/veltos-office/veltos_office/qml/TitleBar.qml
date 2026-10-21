// The title bar of the start screen: the app's colour, the app name in
// the middle, white minimise / maximise / close buttons (Windows 11
// proportions, 46 x 32). Dragging it moves the window; double-clicking
// maximises.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: bar

    property var window
    property int radius: 8
    signal closeWindow()

    implicitHeight: Theme.titleBarHeight
    color: Theme.chrome

    // Square lower corners (the rail continues below in the same colour).
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: bar.radius
        color: Theme.chrome
    }

    Kirigami.Icon {
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        width: 16
        height: 16
        source: backend.appIcon
    }

    Text {
        anchors.centerIn: parent
        text: backend.appTitle
        color: Theme.chromeText
        font.pixelSize: Theme.smallFont
        font.weight: Font.DemiBold
        renderType: Text.NativeRendering
    }

    // Empty part: moves the window.
    Item {
        anchors.fill: parent
        anchors.rightMargin: buttons.width
        DragHandler {
            target: null
            onActiveChanged: if (active) bar.window.startSystemMove()
        }
        TapHandler {
            onDoubleTapped: bar.window.toggleMaximized()
        }
    }

    RowLayout {
        id: buttons
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: 0

        component WindowButton: Rectangle {
            id: wb
            property string glyph
            property string label
            property bool danger: false
            signal clicked()
            Layout.preferredWidth: 46
            Layout.fillHeight: true
            color: wbTap.pressed ? (danger ? Qt.darker(Theme.closeHover, 1.2) : Theme.chromePressed)
                   : wbHover.hovered ? (danger ? Theme.closeHover : Theme.chromeHover) : "transparent"
            Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 80 } }
            Accessible.role: Accessible.Button
            Accessible.name: label
            Glyph {
                anchors.centerIn: parent
                width: 10
                height: 10
                kind: wb.glyph
                color: Theme.chromeText
            }
            HoverHandler { id: wbHover }
            TapHandler {
                id: wbTap
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: wb.clicked()
            }
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
