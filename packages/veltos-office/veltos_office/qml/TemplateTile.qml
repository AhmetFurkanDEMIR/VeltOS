// A template on the Home or New page: the thumbnail on a card that lifts
// on hover (a shadow grows, the card scales up a little), the name below.
// The blank tile shows an empty page with a plus.
import QtQuick
import "."

Item {
    id: tile

    property string name
    property string thumbnail
    property bool blank: false
    property int tileWidth: Theme.tileWidth
    signal chosen()

    width: tileWidth
    height: card.height + 8 + label.implicitHeight + 4
    Accessible.role: Accessible.Button
    Accessible.name: name
    activeFocusOnTab: true
    Keys.onReturnPressed: chosen()
    Keys.onSpacePressed: chosen()

    Item {
        id: cardHolder
        width: tile.tileWidth
        height: Math.round(tile.tileWidth * Theme.thumbRatio)
        scale: tap.pressed ? 0.97 : (hover.hovered ? 1.035 : 1)
        Behavior on scale { enabled: Theme.anim > 0; NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }

        // Shadow: stronger on hover.
        Repeater {
            model: 6
            delegate: Rectangle {
                required property int index
                anchors.fill: card
                anchors.margins: -(index + 1)
                radius: card.radius + index + 1
                color: "transparent"
                border.width: 1
                border.color: Qt.rgba(0, 0, 0, (hover.hovered ? (Theme.dark ? 0.3 : 0.1) : (Theme.dark ? 0.16 : 0.045))
                                      * Math.pow(1 - index / 6, 2))
                Behavior on border.color { enabled: Theme.anim > 0; ColorAnimation { duration: 150 } }
            }
        }

        Rectangle {
            id: card
            anchors.fill: parent
            radius: 4
            color: tile.blank ? Theme.thumbPage : Theme.card
            border.width: 1
            border.color: hover.hovered ? Theme.accent : Theme.cardBorder
            clip: true
            Behavior on border.color { enabled: Theme.anim > 0; ColorAnimation { duration: 120 } }

            Image {
                anchors.fill: parent
                anchors.margins: 1
                source: tile.thumbnail
                visible: !tile.blank && tile.thumbnail !== ""
                fillMode: Image.PreserveAspectCrop
                verticalAlignment: Image.AlignTop
                asynchronous: true
                cache: true
                sourceSize.width: 512
                smooth: true
            }
            // A blank page: faint ruled lines and a plus (Word's "Blank document").
            Column {
                visible: tile.blank
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: Math.round(parent.width * 0.16)
                spacing: Math.round(parent.height * 0.06)
                Repeater {
                    model: Theme.kind === "slides" ? 2 : 6
                    delegate: Rectangle {
                        required property int index
                        width: parent.width * (index === 0 ? 0.55 : 0.9)
                        height: 2
                        radius: 1
                        color: "#E8E8EC"
                    }
                }
            }
            Rectangle {
                visible: tile.blank
                anchors.centerIn: parent
                width: Math.round(parent.width * 0.3)
                height: width
                radius: width / 2
                color: Theme.brand
                Glyph {
                    anchors.centerIn: parent
                    width: parent.width * 0.5
                    height: width
                    kind: "plus"
                    color: "#FFFFFF"
                    lineWidth: 1.6
                }
            }
            Text {
                visible: !tile.blank && tile.thumbnail === ""
                anchors.centerIn: parent
                width: parent.width - 16
                text: tile.name
                color: Theme.subtext
                font.pixelSize: Theme.smallFont
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    Text {
        id: label
        anchors.top: cardHolder.bottom
        anchors.topMargin: 10
        anchors.left: parent.left
        anchors.right: parent.right
        text: tile.name
        color: Theme.text
        font.pixelSize: Theme.smallFont
        elide: Text.ElideRight
        maximumLineCount: 2
        wrapMode: Text.Wrap
        horizontalAlignment: Text.AlignLeft
        renderType: Text.NativeRendering
    }

    HoverHandler { id: hover }
    TapHandler {
        id: tap
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: tile.chosen()
    }
}
