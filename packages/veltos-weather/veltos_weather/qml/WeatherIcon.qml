// A coloured weather picture (icons/<name>.svg, conditions.ICONS).
import QtQuick

Image {
    property string name
    source: name !== "" ? backend.iconDir + name + ".svg" : ""
    sourceSize.width: width * 2
    sourceSize.height: height * 2
    fillMode: Image.PreserveAspectFit
    smooth: true
    asynchronous: false
}
