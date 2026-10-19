// Light / Dark choice with small previews (Personalization and Home).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    spacing: 12

    component Preview: Rectangle {
        id: preview

        property bool darkPreview
        property string label
        readonly property bool chosen: Theme.dark === darkPreview

        Layout.preferredWidth: 200
        Layout.preferredHeight: 150
        radius: Theme.radius
        color: Theme.card
        border.width: chosen || activeFocus ? 2 : 1
        border.color: chosen || activeFocus ? Theme.accent : Theme.cardBorder
        activeFocusOnTab: true
        Accessible.role: Accessible.RadioButton
        Accessible.name: label
        Accessible.checked: chosen
        Accessible.onPressAction: backend.setDarkMode(darkPreview)
        Keys.onReturnPressed: backend.setDarkMode(darkPreview)
        Keys.onSpacePressed: backend.setDarkMode(darkPreview)

        // Miniature desktop: wallpaper, a window, a taskbar.
        Rectangle {
            id: screen
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 8
            height: 100
            radius: 4
            gradient: Gradient {
                GradientStop { position: 0; color: preview.darkPreview ? "#0E1846" : "#CFE0FF" }
                GradientStop { position: 1; color: preview.darkPreview ? "#2B3FA8" : "#5B86F5" }
            }
            Rectangle {
                x: 22; y: 16; width: 110; height: 62; radius: 3
                color: preview.darkPreview ? "#2A2C38" : "#FFFFFF"
                Rectangle { x: 8; y: 10; width: 60; height: 6; radius: 3; color: preview.darkPreview ? "#5D6475" : "#C9CEDB" }
                Rectangle { x: 8; y: 22; width: 86; height: 6; radius: 3; color: preview.darkPreview ? "#454859" : "#E1E5EE" }
                Rectangle { x: 8; y: 40; width: 34; height: 12; radius: 3; color: Theme.accent }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 12
                radius: 2
                color: preview.darkPreview ? "#1C1D26" : "#F3F5FA"
                opacity: 0.95
            }
        }
        RowLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 12
            Rectangle {
                width: 16; height: 16; radius: 8
                color: "transparent"
                border.width: preview.chosen ? 5 : 1
                border.color: preview.chosen ? Theme.accent : Theme.subtext
            }
            Label {
                text: preview.label
                color: Theme.text
                font.pixelSize: Theme.titleSize
            }
        }

        HoverHandler { cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: backend.setDarkMode(preview.darkPreview) }
    }

    RowLayout {
        spacing: 16
        Preview { darkPreview: false; label: backend.text("light") }
        Preview { darkPreview: true; label: backend.text("dark") }
    }
    Label {
        text: backend.text("theme_note")
        color: Theme.subtext
        font.pixelSize: Theme.bodySize
    }
}
