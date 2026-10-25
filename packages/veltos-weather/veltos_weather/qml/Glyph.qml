// A small line glyph of the app (icons/glyph-*.svg) in a colour.
import QtQuick
import org.kde.kirigami as Kirigami
import "."

Kirigami.Icon {
    property string name
    property color tint: Theme.text
    implicitWidth: 16
    implicitHeight: 16
    source: name !== "" ? backend.iconDir + "glyph-" + name + ".svg" : ""
    isMask: true
    color: tint
}
