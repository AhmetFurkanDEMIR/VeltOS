// Home: the greeting, "New" with the blank tile and featured templates,
// "More templates", then the Recent / Pinned list with search.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: page

    function entrance() {
        greetingReveal.play();
        newReveal.play();
        recentReveal.play();
    }
    onVisibleChanged: if (visible) entrance()
    Component.onCompleted: entrance()

    contentWidth: width
    contentHeight: column.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { }

    readonly property int sideMargin: Math.round(40 * Math.min(1.4, Theme.textScale))

    Column {
        id: column
        x: page.sideMargin
        width: page.width - 2 * page.sideMargin
        topPadding: Math.round(28 * Theme.textScale)
        bottomPadding: 32
        spacing: 0

        Reveal {
            id: greetingReveal
            width: parent.width
            height: greeting.implicitHeight
            Text {
                id: greeting
                text: backend.greeting
                color: Theme.text
                font.pixelSize: Theme.greetingFont
                font.weight: Font.DemiBold
                renderType: Text.NativeRendering
            }
        }

        Item { width: 1; height: Math.round(24 * Theme.textScale) }

        Reveal {
            id: newReveal
            delay: 60
            width: parent.width
            height: newColumn.height
            Column {
                id: newColumn
                width: parent.width
                spacing: 12
                RowLayout {
                    width: parent.width
                    Text {
                        text: backend.text("new")
                        color: Theme.text
                        font.pixelSize: Theme.sectionFont
                        font.weight: Font.DemiBold
                        renderType: Text.NativeRendering
                    }
                    Item { Layout.fillWidth: true }
                    Row {
                        spacing: 6
                        Text {
                            id: moreLink
                            text: backend.text("more_templates")
                            color: Theme.link
                            font.pixelSize: Theme.fontSize
                            font.underline: moreHover.hovered
                            renderType: Text.NativeRendering
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Glyph {
                            width: 14
                            height: 14
                            kind: "forward"
                            color: Theme.link
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        HoverHandler { id: moreHover; cursorShape: Qt.PointingHandCursor }
                        TapHandler { onTapped: backend.setPage("new") }
                    }
                }
                // The row shows as many tiles as fit; the rest are on New.
                Item {
                    width: parent.width
                    height: tiles.height
                    clip: true
                    Row {
                        id: tiles
                        spacing: 20
                        TemplateTile {
                            blank: true
                            name: backend.blankName
                            onChosen: backend.newBlank()
                        }
                        Repeater {
                            model: backend.featuredTemplates
                            delegate: TemplateTile {
                                required property var modelData
                                name: modelData.name
                                thumbnail: modelData.thumbnail
                                visible: x + width <= tiles.parent.width
                                onChosen: backend.newFromTemplate(modelData.path)
                            }
                        }
                    }
                }
            }
        }

        Item { width: 1; height: Math.round(30 * Theme.textScale) }

        Reveal {
            id: recentReveal
            delay: 120
            width: parent.width
            height: recentList.height
            RecentList {
                id: recentList
                width: parent.width
            }
        }
    }
}
