// The icon of a place: File Explorer's Home is drawn here in the system's
// accent colour (Settings > Personalization > Colours; product owner,
// 2026-10-22), in the tab, the navigation pane and the address bar alike;
// every other place takes its icon from the icon theme.
import QtQuick
import QtQuick.Shapes
import org.kde.kirigami as Kirigami
import "."

Item {
    id: icon

    property string name
    property bool isMask: false
    property color color: "transparent"
    readonly property bool home: name === "veltos-home"

    implicitWidth: 16
    implicitHeight: 16

    Kirigami.Icon {
        anchors.fill: parent
        visible: !icon.home
        source: icon.home ? "" : icon.name
        isMask: icon.isMask
        color: icon.color
    }

    // The house of the 16 px "veltos-home" icon (veltos-fluent-icons), in
    // the accent: lighter walls, the roof in the accent itself, a white door.
    Shape {
        id: house
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height)
        height: width
        visible: icon.home
        preferredRendererType: Shape.CurveRenderer
        readonly property real unit: width / 16

        ShapePath {
            scale: Qt.size(house.unit, house.unit)
            strokeColor: "transparent"
            fillColor: Qt.lighter(Theme.accent, Theme.dark ? 1.1 : 1.35)
            PathSvg { path: "M 3.5 7.4 L 8 3.6 L 12.5 7.4 V 13 Q 12.5 13.8 11.7 13.8 H 4.3 Q 3.5 13.8 3.5 13 Z" }
        }
        ShapePath {
            scale: Qt.size(house.unit, house.unit)
            strokeColor: Theme.accent
            strokeWidth: 1.5
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: "M 1.8 7.6 L 8 2.4 L 14.2 7.6" }
        }
        ShapePath {
            scale: Qt.size(house.unit, house.unit)
            strokeColor: "transparent"
            fillColor: "#FFFFFF"
            PathSvg { path: "M 6.7 13.8 V 10.6 Q 6.7 10 7.3 10 H 8.7 Q 9.3 10 9.3 10.6 V 13.8 Z" }
        }
    }
}
