// Open: the places on the left (Recent, This PC, Browse), the recent list
// or the folders of this PC on the right.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: page

    property string place: "recent"

    function entrance() {
        titleReveal.play();
        placesReveal.play();
        contentReveal.play();
    }
    onVisibleChanged: if (visible) entrance()
    Component.onCompleted: entrance()

    readonly property int sideMargin: Math.round(40 * Math.min(1.4, Theme.textScale))

    Reveal {
        id: titleReveal
        x: page.sideMargin
        y: Math.round(28 * Theme.textScale)
        width: page.width - 2 * page.sideMargin
        height: title.implicitHeight
        Text {
            id: title
            text: backend.text("open")
            color: Theme.text
            font.pixelSize: Theme.greetingFont
            font.weight: Font.DemiBold
            renderType: Text.NativeRendering
        }
    }

    Reveal {
        id: placesReveal
        delay: 60
        x: page.sideMargin
        y: titleReveal.y + titleReveal.height + Math.round(24 * Theme.textScale)
        width: Math.round(220 * Theme.textScale)
        height: page.height - y - 24
        Column {
            width: parent.width
            spacing: 2

            component Place: Rectangle {
                id: place
                property string name
                property string glyph
                property bool selectable: true
                readonly property bool selected: selectable && page.place === name
                signal chosen()
                width: parent.width
                height: Math.round(44 * Theme.textScale)
                radius: 4
                color: selected ? Theme.hover : (placeHover.hovered ? Theme.hover : "transparent")
                Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 100 } }
                Accessible.role: Accessible.Button
                Accessible.name: backend.text(name)
                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: 16
                    radius: 1.5
                    color: Theme.accent
                    visible: place.selected
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    spacing: 12
                    Glyph {
                        Layout.preferredWidth: 20
                        Layout.preferredHeight: 20
                        width: 20
                        height: 20
                        kind: place.glyph
                        color: place.selected ? Theme.accent : Theme.text
                    }
                    Text {
                        Layout.fillWidth: true
                        text: backend.text(place.name)
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                        font.weight: place.selected ? Font.DemiBold : Font.Normal
                        renderType: Text.NativeRendering
                    }
                }
                HoverHandler { id: placeHover }
                TapHandler {
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: place.chosen()
                }
            }

            Place { name: "recent"; glyph: "home"; onChosen: page.place = "recent" }
            Place { name: "this_pc"; glyph: "folder"; onChosen: page.place = "this_pc" }
            Place { name: "browse"; glyph: "open"; selectable: false; onChosen: backend.browse() }
        }
    }

    Reveal {
        id: contentReveal
        delay: 120
        x: placesReveal.x + placesReveal.width + Math.round(32 * Theme.textScale)
        y: placesReveal.y
        width: page.width - x - page.sideMargin
        height: page.height - y - 16

        Flickable {
            anchors.fill: parent
            visible: page.place === "recent"
            contentWidth: width
            contentHeight: recentList.height + 24
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { }
            RecentList {
                id: recentList
                width: parent.width
            }
        }

        Column {
            anchors.fill: parent
            visible: page.place === "this_pc"
            spacing: 4
            Text {
                text: backend.text("folders")
                color: Theme.subtext
                font.pixelSize: Theme.smallFont
                font.weight: Font.DemiBold
                bottomPadding: 8
                renderType: Text.NativeRendering
            }
            Repeater {
                model: [
                    { key: "documents", folder: "Documents" },
                    { key: "desktop", folder: "Desktop" },
                    { key: "downloads", folder: "Downloads" },
                ]
                delegate: Rectangle {
                    id: folderRow
                    required property var modelData
                    width: parent.width
                    height: Theme.rowHeight
                    radius: 4
                    color: folderHover.hovered ? Theme.hover : "transparent"
                    Behavior on color { enabled: Theme.anim > 0; ColorAnimation { duration: 100 } }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        spacing: 12
                        Glyph {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            width: 20
                            height: 20
                            kind: "folder"
                            color: Theme.brand
                        }
                        Text {
                            Layout.fillWidth: true
                            text: backend.text(folderRow.modelData.key)
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            renderType: Text.NativeRendering
                        }
                    }
                    HoverHandler { id: folderHover }
                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: backend.browseIn(folderRow.modelData.folder)
                    }
                }
            }
            Item { width: 1; height: 12 }
            VButton {
                text: backend.text("browse")
                onClicked: backend.browse()
            }
        }
    }
}
