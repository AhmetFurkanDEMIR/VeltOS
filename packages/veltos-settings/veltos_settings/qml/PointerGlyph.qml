// The Fluent arrow pointer (veltos-fluent-icons' drawing, 32 units) in
// any body and edge colour, for Accessibility > Mouse pointer's tiles.
import QtQuick
import QtQuick.Shapes

Item {
    id: glyph

    property color body: "#FFFFFF"
    property color edge: "#21232B"

    // The arrow's bounds in the 32-unit drawing: it fills the item, centred.
    readonly property real boundsX: 4
    readonly property real boundsY: 4
    readonly property real boundsWidth: 13.1
    readonly property real boundsHeight: 19.6
    readonly property real drawScale: Math.min(width / boundsWidth, height / boundsHeight)

    implicitWidth: 32
    implicitHeight: 32

    Shape {
        width: 32
        height: 32
        x: (glyph.width - glyph.boundsWidth * glyph.drawScale) / 2 - glyph.boundsX * glyph.drawScale
        y: (glyph.height - glyph.boundsHeight * glyph.drawScale) / 2 - glyph.boundsY * glyph.drawScale
        scale: glyph.drawScale
        transformOrigin: Item.TopLeft
        preferredRendererType: Shape.CurveRenderer

        // The edge: the whole outline, the body drawn over it.
        ShapePath {
            fillColor: glyph.edge
            strokeColor: "transparent"
            PathSvg {
                path: "M 5.0039062,4 A 1.0001,1.0001 0 0 0 4,5 v 15.232422 a 1.0001,1.0001 0 0 0 1.3945312,0.917969 "
                      + "c 1.7804531,-0.76319 3.8363028,-0.15053 4.9082028,1.46289 a 1.0001,1.0001 0 0 0 1.226563,0.365235 "
                      + "l 1.988281,-0.851563 a 1.0001,1.0001 0 0 0 0.582031,-1.140625 "
                      + "c -0.429337,-1.889041 0.543666,-3.799322 2.324219,-4.5625 a 1.0001,1.0001 0 0 0 0.296875,-1.644531 "
                      + "L 5.6894531,4.2753906 A 1.0001,1.0001 0 0 0 5.0039062,4 Z"
            }
        }
        ShapePath {
            fillColor: glyph.body
            strokeColor: "transparent"
            PathSvg {
                path: "M 5,5 v 15.231547 c 2.2182209,-0.950838 4.7998468,-0.181486 6.135367,1.828734 "
                      + "l 1.989042,-0.852571 c -0.534876,-2.353403 0.687634,-4.752995 2.90588,-5.703776 Z"
            }
        }
    }
}
