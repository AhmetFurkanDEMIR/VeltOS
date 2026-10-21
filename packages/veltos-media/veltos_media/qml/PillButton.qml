// A Windows 11 button of the media pages: accent-filled (primary, e.g.
// "Shuffle and play") or plain, with an optional glyph.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: button

    property string text
    property string glyph
    property bool primary: false
    property bool enabledState: true
    signal clicked()

    implicitWidth: row.implicitWidth + 28
    implicitHeight: 32
    radius: 4
    opacity: enabledState ? 1 : 0.45
    color: primary ? (tap.pressed ? Qt.darker(Theme.accent, 1.1) : hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                   : (tap.pressed ? Theme.pressed : hover.hovered ? Theme.hover : Theme.field)
    border.width: primary ? 0 : 1
    border.color: Theme.fieldBorder
    Accessible.role: Accessible.Button
    Accessible.name: text

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Glyph {
            visible: button.glyph !== ""
            Layout.preferredWidth: 14
            Layout.preferredHeight: 14
            kind: button.glyph
            color: button.primary ? Theme.accentText : Theme.text
        }
        Text { text: button.text; color: button.primary ? Theme.accentText : Theme.text; font.pixelSize: Theme.fontSize }
    }
    HoverHandler { id: hover }
    TapHandler { id: tap; enabled: button.enabledState; onTapped: button.clicked() }
}
