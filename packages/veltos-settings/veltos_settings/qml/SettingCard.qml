// One setting: icon, title, description and a chevron (opens a page) or an
// "opens in a new window" mark (opens a settings module or an app).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: card

    property string icon
    property string title
    property string description
    property string note       // small text under the description (e.g. page name in search)
    property bool external: false
    signal activated()

    implicitHeight: Math.max(68, content.implicitHeight + 24)
    radius: Theme.radius
    color: tap.pressed ? Theme.cardPressed : (hover.hovered ? Theme.cardHover : Theme.card)
    border.width: card.activeFocus ? 2 : 1
    border.color: card.activeFocus ? Theme.accent : Theme.cardBorder
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: title
    Accessible.description: description
    Accessible.onPressAction: activated()
    Keys.onReturnPressed: activated()
    Keys.onSpacePressed: activated()

    Behavior on color { ColorAnimation { duration: 90 } }

    RowLayout {
        id: content
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        spacing: 16

        Kirigami.Icon {
            Layout.preferredWidth: 26
            Layout.preferredHeight: 26
            source: card.icon
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label {
                Layout.fillWidth: true
                text: card.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: text.length > 0
                text: card.description
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: text.length > 0
                text: card.note
                color: Theme.accent
                font.pixelSize: Theme.bodySize
                elide: Text.ElideRight
            }
        }
        Kirigami.Icon {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            source: card.external ? "window-new" : "go-next"
            color: Theme.subtext
            isMask: true
        }
    }

    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { id: tap; onTapped: card.activated() }
}
