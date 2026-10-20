// An app tile (Microsoft Store layout): icon, name, category, and "Free",
// "Installed" or the progress of its job. Clicking opens the app page.
import QtQuick
import QtQuick.Layouts

MouseArea {
    id: card
    required property var app
    signal opened(string appId)
    implicitWidth: 180
    implicitHeight: 220
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    onClicked: opened(app.id)
    Accessible.role: Accessible.Button
    Accessible.name: app.name

    readonly property string appState: backend.state(app.pkg, backend.revision)

    Rectangle {
        id: face
        anchors.fill: parent
        radius: Theme.radius
        color: card.containsMouse ? Theme.cardHover : Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        // Lifts a little on hover, like the Store's cards.
        transform: Translate { y: card.containsMouse ? -2 : 0 }
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 4
        AppIcon {
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            Layout.bottomMargin: 10
            icon: card.app.icon
        }
        Text {
            Layout.fillWidth: true
            text: card.app.name
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
            font.weight: Font.DemiBold
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
        Text {
            Layout.fillWidth: true
            text: card.app.category
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
            elide: Text.ElideRight
        }
        Item { Layout.fillHeight: true }
        Text {
            Layout.fillWidth: true
            text: card.appState === "installed" ? backend.texts.installed
                : card.appState === "" || card.appState === "failed" ? backend.texts.free
                : (backend.texts[card.appState] || "")
            color: card.appState === "installed" || card.appState === "" || card.appState === "failed"
                   ? Theme.subtext : Theme.accent
            font.pixelSize: Theme.captionSize
            elide: Text.ElideRight
        }
    }
}
