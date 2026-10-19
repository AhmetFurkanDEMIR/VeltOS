// A flat Windows 11 toolbar button: an icon, optionally a text and a
// drop-down chevron; rounded highlight on hover.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: button

    property string icon
    property string glyph              // drawn instead of an icon (Glyph.qml)
    property string text
    property string tooltip
    property bool chevron: false
    property bool enabledState: true
    property bool checked: false
    property int iconSize: 16
    signal clicked()

    implicitWidth: row.implicitWidth + (text !== "" ? 20 : 16)
    implicitHeight: 32
    radius: Theme.radius
    color: !enabledState ? "transparent"
           : (tap.pressed || checked) ? Theme.pressed : (hover.hovered ? Theme.hover : "transparent")
    activeFocusOnTab: enabledState
    Accessible.role: Accessible.Button
    Accessible.name: text !== "" ? text : tooltip
    Keys.onReturnPressed: if (enabledState) clicked()
    Keys.onSpacePressed: if (enabledState) clicked()

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Glyph {
            visible: button.glyph !== ""
            Layout.preferredWidth: 14
            Layout.preferredHeight: 6
            width: 14
            height: 6
            kind: button.glyph
            color: button.enabledState ? Theme.text : Theme.disabled
        }
        Kirigami.Icon {
            visible: button.icon !== ""
            Layout.preferredWidth: button.iconSize
            Layout.preferredHeight: button.iconSize
            source: button.icon
            opacity: button.enabledState ? 1 : 0.35
        }
        Text {
            visible: button.text !== ""
            text: button.text
            color: button.enabledState ? Theme.text : Theme.disabled
            font.pixelSize: Theme.fontSize
        }
        Kirigami.Icon {
            visible: button.chevron
            Layout.preferredWidth: 10
            Layout.preferredHeight: 10
            source: "arrow-down"
            color: button.enabledState ? Theme.subtext : Theme.disabled
            isMask: true
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        border.width: 2
        border.color: Theme.text
        visible: button.activeFocus
    }

    ToolTipText { text: button.tooltip; shown: hover.hovered && button.tooltip !== "" && button.text === "" }

    HoverHandler { id: hover }
    TapHandler { id: tap; enabled: button.enabledState; onTapped: button.clicked() }
}
