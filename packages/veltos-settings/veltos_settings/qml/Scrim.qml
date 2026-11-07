// The dimmed layer behind a dialog. It covers the window only, not the
// shadow the window draws around itself (the window's `shadow` margin).
import QtQuick

Item {
    id: scrim

    property color color: "#40000000"
    readonly property real margin: Window.window && Window.window.shadow !== undefined ? Window.window.shadow : 0

    Rectangle {
        anchors.fill: parent
        anchors.margins: scrim.margin
        radius: scrim.margin > 0 ? 8 : 0
        color: scrim.color
    }
}
