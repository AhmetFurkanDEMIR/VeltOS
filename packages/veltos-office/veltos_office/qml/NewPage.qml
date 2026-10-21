// New: every template as a grid, with a search box; the blank document first.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: page

    property string query: ""
    readonly property var templates: backend.templates.length >= 0 ? backend.searchTemplates(query) : []

    function entrance() {
        titleReveal.play();
        gridReveal.play();
    }
    onVisibleChanged: if (visible) entrance()
    Component.onCompleted: entrance()

    contentWidth: width
    contentHeight: column.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { }

    readonly property int sideMargin: Math.round(40 * Math.min(1.4, Theme.textScale))
    readonly property int tileWidth: Math.round(Theme.tileWidth * 1.2)

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
            height: titleRow.height
            RowLayout {
                id: titleRow
                width: parent.width
                Text {
                    text: backend.text("new")
                    color: Theme.text
                    font.pixelSize: Theme.greetingFont
                    font.weight: Font.DemiBold
                    renderType: Text.NativeRendering
                }
                Item { Layout.fillWidth: true }
                SearchBox {
                    Layout.preferredWidth: Math.round(280 * Theme.textScale)
                    placeholder: backend.text("search_templates")
                    onTextChanged: page.query = text
                }
            }
        }

        Item { width: 1; height: Math.round(24 * Theme.textScale) }

        Reveal {
            id: gridReveal
            delay: 60
            width: parent.width
            height: grid.height
            Flow {
                id: grid
                width: parent.width
                spacing: 24
                TemplateTile {
                    visible: page.query === ""
                    blank: true
                    tileWidth: page.tileWidth
                    name: backend.blankName
                    onChosen: backend.newBlank()
                }
                Repeater {
                    model: page.templates
                    delegate: TemplateTile {
                        required property var modelData
                        tileWidth: page.tileWidth
                        name: modelData.name
                        thumbnail: modelData.thumbnail
                        onChosen: backend.newFromTemplate(modelData.path)
                    }
                }
                Text {
                    visible: page.templates.length === 0 && page.query !== ""
                    text: backend.text("no_templates")
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                    renderType: Text.NativeRendering
                }
            }
        }
    }
}
