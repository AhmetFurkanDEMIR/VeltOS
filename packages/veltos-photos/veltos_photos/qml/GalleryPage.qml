// The gallery of Windows 11 Photos: the page title with the number of
// items, the Filter, Sort, View and Slideshow buttons, then the pictures
// and videos grouped by month. Rows come from Python (backend.galleryRows)
// for the number of columns that fit, so the list stays light for
// thousands of pictures.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    property string title
    signal open(var item)
    signal contextMenu(var item, var target, real x, real y)
    signal slideshow()

    readonly property int tile: backend.tilePixels
    readonly property int gap: 4
    readonly property int columns: Math.max(1, Math.floor((list.width + gap) / (tile + gap)))
    onColumnsChanged: backend.setColumns(columns)
    Component.onCompleted: backend.setColumns(columns)

    component ToolButton: Rectangle {
        id: tb
        property string glyph
        property string text
        signal clicked()
        implicitWidth: row.implicitWidth + 20
        implicitHeight: 32
        radius: 4
        color: tap.pressed ? Theme.pressed : (hover.hovered ? Theme.hover : "transparent")
        Accessible.role: Accessible.Button
        Accessible.name: text
        RowLayout {
            id: row
            anchors.centerIn: parent
            spacing: 8
            Glyph { Layout.preferredWidth: 16; Layout.preferredHeight: 16; kind: tb.glyph }
            Text { text: tb.text; color: Theme.text; font.pixelSize: Theme.fontSize }
        }
        HoverHandler { id: hover }
        TapHandler { id: tap; onTapped: tb.clicked() }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 28
            Layout.rightMargin: 20
            Layout.topMargin: 18
            Layout.bottomMargin: 10
            spacing: 6
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: page.title
                    color: Theme.text
                    font.pixelSize: 28
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Text {
                    text: backend.scanning ? backend.texts.scanning : backend.countText(backend.count)
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                }
            }
            ToolButton {
                id: filterButton
                glyph: "filter"
                text: backend.texts.filter
                onClicked: filterMenu.openAt(filterButton, 0, filterButton.height + 4)
            }
            ToolButton {
                id: sortButton
                glyph: "sort"
                text: backend.texts.sort
                onClicked: sortMenu.openAt(sortButton, 0, sortButton.height + 4)
            }
            ToolButton {
                id: viewButton
                glyph: "grid"
                text: backend.texts.view
                onClicked: viewMenu.openAt(viewButton, 0, viewButton.height + 4)
            }
            ToolButton {
                glyph: "play-outline"
                text: backend.texts.slideshow
                onClicked: page.slideshow()
            }
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 28
            Layout.rightMargin: 12
            clip: true
            model: backend.galleryRows
            boundsBehavior: Flickable.StopAtBounds
            cacheBuffer: 800
            ScrollBar.vertical: ScrollBar {}

            delegate: Loader {
                required property string type
                required property string title
                required property var items
                width: ListView.view.width - 16
                sourceComponent: type === "header" ? headerComponent : rowComponent
                onLoaded: {
                    item.title = title;
                    item.items = items;
                }
            }

            Component {
                id: headerComponent
                Item {
                    property string title
                    property var items
                    implicitHeight: 52
                    Text {
                        anchors.left: parent.left
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 10
                        text: parent.title
                        color: Theme.text
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                }
            }

            Component {
                id: rowComponent
                Row {
                    property string title
                    property var items: []
                    spacing: page.gap
                    bottomPadding: page.gap
                    Repeater {
                        model: parent.items
                        delegate: Tile {
                            id: tileItem
                            required property var modelData
                            item: modelData
                            width: page.tile
                            height: page.tile
                            onOpen: page.open(modelData)
                            onContextMenu: (x, y) => page.contextMenu(modelData, tileItem, x, y)
                        }
                    }
                }
            }
        }
    }

    // Empty gallery, favorites or search.
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(460, parent.width - 60)
        visible: !backend.scanning && backend.count === 0
        spacing: 8
        Glyph {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 48
            Layout.preferredHeight: 48
            kind: backend.page === "favorites" ? "heart" : "gallery"
            color: Theme.subtext
            lineWidth: 1.4
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: backend.query !== "" ? backend.texts.no_results.replace("{text}", backend.query)
                  : backend.page === "favorites" ? backend.texts.no_favorites : backend.texts.empty_title
            color: Theme.text
            font.pixelSize: 16
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }
        Text {
            Layout.fillWidth: true
            visible: backend.query === "" && backend.page !== "favorites"
            horizontalAlignment: Text.AlignHCenter
            text: backend.texts.empty_text
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }
    }

    WinMenu {
        id: filterMenu
        items: [
            { text: backend.texts.all_items, checked: backend.filter === "all", action: "all" },
            { text: backend.texts.photos_only, checked: backend.filter === "image", action: "image" },
            { text: backend.texts.videos_only, checked: backend.filter === "video", action: "video" }
        ]
        onTriggered: action => backend.setFilter(action)
    }
    WinMenu {
        id: sortMenu
        minimumWidth: 280
        items: [
            { text: backend.texts.newest, checked: backend.sort === "newest", action: "newest" },
            { text: backend.texts.oldest, checked: backend.sort === "oldest", action: "oldest" }
        ]
        onTriggered: action => backend.setSort(action)
    }
    WinMenu {
        id: viewMenu
        minimumWidth: 160
        items: [
            { text: backend.texts.small, checked: backend.tileSize === "small", action: "small" },
            { text: backend.texts.medium, checked: backend.tileSize === "medium", action: "medium" },
            { text: backend.texts.large, checked: backend.tileSize === "large", action: "large" }
        ]
        onTriggered: action => backend.setTileSize(action)
    }
}
