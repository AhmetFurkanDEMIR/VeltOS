// Favorite places, as cards with their weather now (Windows 11 Weather's
// Favorites). A click opens the place; the bin removes it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Flickable {
    id: page
    contentWidth: width
    contentHeight: column.implicitHeight + 48
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}

    ColumnLayout {
        id: column
        x: 24
        y: 8
        width: page.width - 48
        spacing: 16

        Text {
            text: backend.text("favorites")
            color: Theme.text
            font.pixelSize: Theme.subtitleSize + 2
            font.weight: Font.DemiBold
        }
        Text {
            visible: backend.favorites.length === 0
            Layout.fillWidth: true
            text: backend.text("no_favorites")
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
            wrapMode: Text.WordWrap
        }
        Flow {
            objectName: "favoriteCards"
            Layout.fillWidth: true
            spacing: 12
            Repeater {
                model: backend.favorites
                delegate: Rectangle {
                    id: favorite
                    required property var modelData
                    required property int index
                    width: 280
                    height: 150
                    radius: Theme.radius
                    color: favHover.hovered ? Theme.cardHover : Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.name

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 4
                        RowLayout {
                            spacing: 6
                            Glyph { visible: favorite.modelData.home; name: "home"; tint: Theme.subtext }
                            Text {
                                Layout.fillWidth: true
                                text: favorite.modelData.name
                                color: Theme.text
                                font.pixelSize: Theme.subtitleSize
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: favorite.modelData.detail
                            color: Theme.subtext
                            font.pixelSize: Theme.captionSize
                            elide: Text.ElideRight
                        }
                        Item { Layout.fillHeight: true }
                        RowLayout {
                            spacing: 10
                            WeatherIcon {
                                name: favorite.modelData.icon
                                Layout.preferredWidth: 44
                                Layout.preferredHeight: 44
                            }
                            Text {
                                text: favorite.modelData.temperature
                                color: Theme.text
                                font.pixelSize: Theme.titleSize
                                font.weight: Font.DemiBold
                            }
                            ColumnLayout {
                                spacing: 0
                                Text { text: favorite.modelData.condition; color: Theme.text; font.pixelSize: Theme.captionSize + 1 }
                                Text {
                                    text: favorite.modelData.high !== "" ? favorite.modelData.high + " / " + favorite.modelData.low : ""
                                    color: Theme.subtext
                                    font.pixelSize: Theme.captionSize
                                }
                            }
                        }
                    }
                    Rectangle {
                        visible: favHover.hovered
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 8
                        width: 30
                        height: 30
                        radius: 5
                        color: binHover.hovered ? Theme.navHover : "transparent"
                        Glyph { anchors.centerIn: parent; name: "delete"; tint: Theme.subtext }
                        HoverHandler { id: binHover }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: backend.removeFavorite(favorite.index)
                        }
                        ToolTip.visible: binHover.hovered
                        ToolTip.text: backend.text("remove_favorite")
                    }
                    HoverHandler { id: favHover }
                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: point => {
                            if (!binHover.hovered)
                                backend.openFavorite(favorite.index);
                        }
                    }
                }
            }
        }
    }
}
