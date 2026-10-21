// Options: the start screen switch, the recent list, where the rest lives.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: page

    function entrance() {
        titleReveal.play();
        bodyReveal.play();
    }
    onVisibleChanged: if (visible) entrance()
    Component.onCompleted: entrance()

    contentWidth: width
    contentHeight: column.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { }

    readonly property int sideMargin: Math.round(40 * Math.min(1.4, Theme.textScale))

    component SectionTitle: Text {
        color: Theme.text
        font.pixelSize: Theme.sectionFont
        font.weight: Font.DemiBold
        renderType: Text.NativeRendering
    }

    // A Windows 11 settings card: title and note on the left, a control on the right.
    component Card: Rectangle {
        id: card
        property string title
        property string note
        default property alias control: slot.data
        width: Math.min(column.width, Math.round(720 * Theme.textScale))
        height: Math.max(Math.round(64 * Theme.textScale), cardText.implicitHeight + 24)
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 16
            ColumnLayout {
                id: cardText
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: card.title
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                    renderType: Text.NativeRendering
                }
                Text {
                    Layout.fillWidth: true
                    visible: card.note !== ""
                    text: card.note
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    wrapMode: Text.Wrap
                    renderType: Text.NativeRendering
                }
            }
            Item {
                id: slot
                Layout.preferredWidth: childrenRect.width
                Layout.preferredHeight: childrenRect.height
            }
        }
    }

    Column {
        id: column
        x: page.sideMargin
        width: page.width - 2 * page.sideMargin
        topPadding: Math.round(28 * Theme.textScale)
        bottomPadding: 32
        spacing: 0

        Reveal {
            id: titleReveal
            width: parent.width
            height: title.implicitHeight
            Text {
                id: title
                text: backend.text("options")
                color: Theme.text
                font.pixelSize: Theme.greetingFont
                font.weight: Font.DemiBold
                renderType: Text.NativeRendering
            }
        }

        Item { width: 1; height: Math.round(24 * Theme.textScale) }

        Reveal {
            id: bodyReveal
            delay: 60
            width: parent.width
            height: body.height
            Column {
                id: body
                width: parent.width
                spacing: 8

                SectionTitle { text: backend.text("start_up_options"); bottomPadding: 6 }
                Card {
                    title: backend.text("show_start_screen")
                    note: backend.text("show_start_screen_note")
                    Toggle {
                        checked: backend.showHome
                        label: backend.text("show_start_screen")
                        onToggled: on => backend.setShowHome(on)
                    }
                }

                SectionTitle { topPadding: 20; text: backend.text("recent_files_options"); bottomPadding: 6 }
                Card {
                    title: backend.text("clear_recent")
                    note: cleared.running ? backend.text("cleared") : backend.text("clear_recent_note")
                    VButton {
                        text: backend.text("clear")
                        enabledState: backend.recent.length > 0
                        onClicked: { backend.clearRecent(); cleared.restart(); }
                    }
                }
                Timer { id: cleared; interval: 4000 }

                SectionTitle { topPadding: 20; text: backend.text("file_formats"); bottomPadding: 6 }
                Card {
                    title: backend.text("file_formats_note")
                }

                SectionTitle { topPadding: 20; text: backend.text("more_options"); bottomPadding: 6 }
                Card {
                    title: backend.text("more_options_note")
                }
            }
        }
    }
}
