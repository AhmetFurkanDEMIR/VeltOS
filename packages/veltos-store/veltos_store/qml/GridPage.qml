// A page of app tiles: all apps (with category chips), games, or search
// results.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: page
    property string title: ""
    property string source: ""          // "" (all apps) or "games"
    property string searchText: ""       // set: search results
    property bool showCategories: false
    property string category: ""
    signal opened(string appId)

    readonly property var items: {
        backend.appCount;   // again when the catalogue has loaded
        return searchText !== "" ? backend.search(searchText)
                                 : backend.browse(category !== "" ? category : source);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        Text {
            Layout.topMargin: 24
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.fillWidth: true
            text: page.title
            color: Theme.text
            font.pixelSize: Theme.pageTitleSize
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }

        // Category chips (Apps page).
        Flow {
            visible: page.showCategories
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: [{"id": "", "title": backend.texts.all_categories, "icon": "view-app-grid-symbolic"}]
                       .concat(backend.categories)
                MouseArea {
                    id: chip
                    required property var modelData
                    readonly property bool selected: page.category === modelData.id
                    width: chipRow.implicitWidth + 24
                    height: 32
                    hoverEnabled: true
                    onClicked: page.category = modelData.id
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.title
                    Rectangle {
                        anchors.fill: parent
                        radius: height / 2
                        color: chip.selected ? Theme.accent : (chip.containsMouse ? Theme.controlHover : Theme.control)
                        border.width: chip.selected ? 0 : 1
                        border.color: Theme.cardBorder
                    }
                    Row {
                        id: chipRow
                        anchors.centerIn: parent
                        spacing: 6
                        Kirigami.Icon {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 14
                            height: 14
                            source: chip.modelData.icon
                            isMask: true
                            color: chip.selected ? Theme.accentText : Theme.text
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: chip.modelData.title
                            color: chip.selected ? Theme.accentText : Theme.text
                            font.pixelSize: Theme.bodySize
                        }
                    }
                }
            }
        }

        Text {
            visible: page.items.length === 0 && page.searchText !== ""
            Layout.leftMargin: 32
            text: backend.texts.no_results
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
        }

        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 32 - 6
            Layout.rightMargin: 32 - 6
            clip: true
            cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 196)))
            cellHeight: 236
            model: page.items
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            delegate: Item {
                required property var modelData
                width: grid.cellWidth
                height: grid.cellHeight
                AppCard {
                    anchors.fill: parent
                    anchors.margins: 6
                    app: parent.modelData
                    onOpened: appId => page.opened(appId)
                }
            }
        }
    }
}
