// The viewer of Windows 11 Photos: the toolbar (zoom, rotate, edit,
// delete, heart, file information, more), the picture (fit to the window;
// the wheel zooms where the pointer is, dragging pans), previous and next
// buttons at the sides, the filmstrip and the zoom level at the bottom,
// the file information panel, the editor and the slideshow.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    id: viewer

    property bool slideshow: false
    property bool infoOpen: false
    property bool editing: false
    property real scaleFactor: 1          // 1 = actual pixels
    property bool fitted: true
    readonly property var current: backend.viewerItem
    readonly property bool isVideo: current.kind === "video"
    readonly property real fitScale: image.implicitWidth > 0
        ? Math.min(1, stage.width / image.implicitWidth, stage.height / image.implicitHeight) : 1
    readonly property real shownScale: fitted ? fitScale : scaleFactor
    signal deleteRequested(string path)
    signal slideshowEnded()
    signal fullScreen(bool on)

    function zoomBy(factor, x, y) {
        const old = shownScale;
        const target = Math.max(fitScale * 0.5, Math.min(8, old * factor));
        const px = x === undefined ? flick.width / 2 : x;
        const py = y === undefined ? flick.height / 2 : y;
        const cx = (flick.contentX + px) / old, cy = (flick.contentY + py) / old;
        fitted = false;
        scaleFactor = target;
        flick.contentX = Math.max(0, cx * target - px);
        flick.contentY = Math.max(0, cy * target - py);
    }
    function fit() {
        fitted = true;
        flick.contentX = 0;
        flick.contentY = 0;
    }
    function step(delta) {
        if (backend.viewerItems.length === 0)
            return;
        if (slideshow) {
            backend.viewerGo((backend.viewerIndex + delta + backend.viewerItems.length) % backend.viewerItems.length);
        } else {
            backend.viewerStep(delta);
        }
    }
    function startSlideshow() {
        if (backend.viewerIndex < 0) {
            const first = backend.firstVisible();
            if (first === "")
                return;
            backend.openInViewer(first);
        }
        fullScreen(true);
        slideshowTimer.restart();
    }
    function stopSlideshow() {
        slideshowTimer.stop();
        slideshowEnded();
    }

    onCurrentChanged: {
        fit();
        editing = false;
        if (backend.viewerIndex >= 0)
            strip.positionViewAtIndex(backend.viewerIndex, ListView.Contain);
    }

    Rectangle {
        anchors.fill: parent
        color: viewer.slideshow ? "#000000" : Theme.content
    }

    component ToolButton: Rectangle {
        id: tb
        property string glyph
        property string label
        property color glyphColor: Theme.text
        property bool enabledState: true
        signal clicked()
        implicitWidth: 40
        implicitHeight: 36
        radius: 4
        opacity: enabledState ? 1 : 0.4
        color: enabledState && tap.pressed ? Theme.pressed : (enabledState && hover.hovered ? Theme.hover : "transparent")
        Accessible.role: Accessible.Button
        Accessible.name: label
        Glyph { anchors.centerIn: parent; width: 16; height: 16; kind: tb.glyph; color: tb.glyphColor }
        ToolTip.visible: hover.hovered
        ToolTip.delay: 600
        ToolTip.text: label
        HoverHandler { id: hover }
        TapHandler { id: tap; enabled: tb.enabledState; onTapped: tb.clicked() }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.rightMargin: viewer.infoOpen && !viewer.slideshow ? info.width : 0
        spacing: 0

        // --- Toolbar ------------------------------------------------------------------
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            visible: !viewer.slideshow && !viewer.editing
            RowLayout {
                anchors.centerIn: parent
                spacing: 2
                ToolButton { glyph: "zoom-out"; label: backend.texts.zoom_out; enabledState: !viewer.isVideo
                             onClicked: viewer.zoomBy(1 / 1.25) }
                ToolButton { glyph: "zoom-in"; label: backend.texts.zoom_in; enabledState: !viewer.isVideo
                             onClicked: viewer.zoomBy(1.25) }
                Rectangle { width: 1; height: 20; color: Theme.separator; Layout.leftMargin: 6; Layout.rightMargin: 6 }
                ToolButton { glyph: "rotate"; label: backend.texts.rotate; enabledState: !viewer.isVideo
                             onClicked: backend.rotate(viewer.current.path) }
                ToolButton { glyph: "edit"; label: backend.texts.edit; enabledState: !viewer.isVideo
                             onClicked: viewer.editing = true }
                ToolButton { glyph: "delete"; label: backend.texts.delete
                             onClicked: viewer.deleteRequested(viewer.current.path) }
                ToolButton {
                    readonly property bool fav: backend.favorites.indexOf(viewer.current.path) >= 0
                    glyph: fav ? "heart-filled" : "heart"
                    glyphColor: fav ? Theme.heart : Theme.text
                    label: fav ? backend.texts.unfavorite : backend.texts.favorite
                    onClicked: backend.toggleFavorite(viewer.current.path)
                }
                ToolButton { glyph: "info"; label: backend.texts.file_info; onClicked: viewer.infoOpen = !viewer.infoOpen }
                ToolButton {
                    id: moreButton
                    glyph: "more"
                    label: backend.texts.more
                    onClicked: moreMenu.openAt(moreButton, 0, moreButton.height + 4)
                }
            }
        }

        // --- The picture --------------------------------------------------------------
        Item {
            id: stage
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Flickable {
                id: flick
                anchors.fill: parent
                contentWidth: Math.max(width, image.implicitWidth * viewer.shownScale)
                contentHeight: Math.max(height, image.implicitHeight * viewer.shownScale)
                interactive: !viewer.fitted
                boundsBehavior: Flickable.StopAtBounds
                visible: !viewer.editing

                Image {
                    id: image
                    width: implicitWidth * viewer.shownScale
                    height: implicitHeight * viewer.shownScale
                    x: Math.max(0, (flick.contentWidth - width) / 2)
                    y: Math.max(0, (flick.contentHeight - height) / 2)
                    source: viewer.current.path
                            ? (viewer.isVideo ? backend.bigThumbUrl(viewer.current.path, "video", viewer.current.mtime)
                                              : backend.fileUrl(viewer.current.path, viewer.current.mtime))
                            : ""
                    sourceSize.width: 8192
                    sourceSize.height: 8192
                    autoTransform: true
                    asynchronous: true
                    cache: false
                    smooth: true
                    mipmap: viewer.shownScale < 0.5
                    opacity: status === Image.Ready ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: viewer.slideshow ? 400 : 100 } }
                }
                WheelHandler {
                    target: null
                    enabled: !viewer.isVideo
                    onWheel: event => viewer.zoomBy(event.angleDelta.y > 0 ? 1.15 : 1 / 1.15,
                                                    event.x - flick.contentX, event.y - flick.contentY)
                }
                TapHandler {
                    onDoubleTapped: viewer.fitted ? viewer.zoomBy(2) : viewer.fit()
                    onTapped: if (viewer.slideshow) viewer.stopSlideshow()
                }
            }

            // Video: the frame with a play button (Media Player plays it).
            Rectangle {
                visible: viewer.isVideo && !viewer.slideshow
                anchors.centerIn: parent
                width: 72
                height: 72
                radius: 36
                color: playHover.hovered ? "#CC000000" : "#99000000"
                Accessible.role: Accessible.Button
                Accessible.name: backend.texts.play_video
                Glyph { anchors.centerIn: parent; anchors.horizontalCenterOffset: 3; width: 28; height: 28; kind: "play"; color: "#FFFFFF" }
                HoverHandler { id: playHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: backend.playVideo(viewer.current.path) }
            }

            Text {
                anchors.centerIn: parent
                visible: image.status === Image.Error && !viewer.isVideo
                text: backend.texts.cant_open
                color: Theme.subtext
                font.pixelSize: 16
            }

            // Previous / next at the sides, shown under the pointer.
            HoverHandler { id: stageHover }
            component SideButton: Rectangle {
                id: sb
                property string glyph
                property string label
                signal clicked()
                width: 36
                height: 64
                radius: 6
                anchors.verticalCenter: parent.verticalCenter
                color: Theme.dark ? "#CC2A2C38" : "#E6FFFFFF"
                border.width: 1
                border.color: Theme.cardBorder
                visible: stageHover.hovered && !viewer.slideshow && !viewer.editing
                Accessible.role: Accessible.Button
                Accessible.name: label
                Glyph { anchors.centerIn: parent; width: 14; height: 14; kind: sb.glyph }
                TapHandler { onTapped: sb.clicked() }
            }
            SideButton {
                anchors.left: parent.left
                anchors.leftMargin: 12
                glyph: "chevron-left"
                label: backend.texts.previous
                opacity: backend.viewerIndex > 0 ? 1 : 0.35
                onClicked: viewer.step(-1)
            }
            SideButton {
                anchors.right: parent.right
                anchors.rightMargin: 12
                glyph: "chevron-right"
                label: backend.texts.next
                opacity: backend.viewerIndex < backend.viewerItems.length - 1 ? 1 : 0.35
                onClicked: viewer.step(1)
            }

            EditView {
                anchors.fill: parent
                visible: viewer.editing
                active: viewer.editing
                item: viewer.current
                onDone: viewer.editing = false
            }
        }

        // --- Filmstrip and zoom ------------------------------------------------------
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            visible: !viewer.slideshow && !viewer.editing

            ListView {
                id: strip
                anchors.centerIn: parent
                width: Math.min(parent.width - 360, count * 64)
                height: 60
                orientation: ListView.Horizontal
                spacing: 4
                clip: true
                model: backend.viewerItems
                currentIndex: backend.viewerIndex
                delegate: Rectangle {
                    required property var modelData
                    required property int index
                    width: 60
                    height: 60
                    radius: 4
                    color: Theme.tile
                    border.width: index === backend.viewerIndex ? 2 : 0
                    border.color: Theme.accent
                    Image {
                        anchors.fill: parent
                        anchors.margins: index === backend.viewerIndex ? 3 : 0
                        source: backend.thumbUrl(modelData.path, modelData.kind, modelData.mtime || 0)
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        sourceSize: Qt.size(120, 120)
                    }
                    TapHandler { onTapped: backend.viewerGo(index) }
                }
            }

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                visible: !viewer.isVideo
                Text {
                    text: Math.round(viewer.shownScale * 100) + "%"
                    color: Theme.text
                    font.pixelSize: Theme.smallFont
                    Layout.rightMargin: 4
                }
                ToolButton {
                    glyph: "fit"
                    label: viewer.fitted ? backend.texts.actual_size : backend.texts.fit
                    onClicked: {
                        if (viewer.fitted) {
                            viewer.fitted = false;
                            viewer.scaleFactor = 1;
                        } else {
                            viewer.fit();
                        }
                    }
                }
            }
        }
    }

    // --- File information ----------------------------------------------------------------
    Rectangle {
        id: info
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 320
        visible: viewer.infoOpen && !viewer.slideshow
        color: Theme.window
        readonly property var facts: visible && viewer.current.path ? backend.fileInfo(viewer.current.path) : ({})
        Rectangle { anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom; width: 1; color: Theme.separator }
        ScrollView {
            anchors.fill: parent
            anchors.margins: 20
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width
                spacing: 16
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: backend.texts.file_info
                        color: Theme.text
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    ToolButton { glyph: "close"; label: backend.texts.close; onClicked: viewer.infoOpen = false }
                }
                Repeater {
                    model: [
                        ["file_name", info.facts.name], ["date_taken", info.facts.taken],
                        ["date_modified", info.facts.modified],
                        ["dimensions", info.facts.dimensions ? info.facts.dimensions + "  ·  " + info.facts.megapixels : ""],
                        ["file_size", info.facts.size], ["camera", info.facts.camera], ["lens", info.facts.lens],
                        ["exposure", info.facts.exposure], ["location", info.facts.location]
                    ]
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        visible: !!modelData[1]
                        spacing: 2
                        Text { text: backend.texts[modelData[0]]; color: Theme.subtext; font.pixelSize: Theme.smallFont }
                        Text {
                            Layout.fillWidth: true
                            text: modelData[1] || ""
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            wrapMode: Text.WrapAnywhere
                        }
                    }
                }
            }
        }
    }

    WinMenu {
        id: moreMenu
        minimumWidth: 260
        items: viewer.isVideo
            ? [{ text: backend.texts.play_video, action: "play" },
               { text: backend.texts.show_in_folder, action: "folder" },
               { text: backend.texts.slideshow, action: "slideshow" }]
            : [{ text: backend.texts.copy, shortcut: "Ctrl+C", action: "copy" },
               { text: backend.texts.set_background, action: "background" },
               { text: backend.texts.set_lock_screen, action: "lock" },
               { separator: true },
               { text: backend.texts.show_in_folder, action: "folder" },
               { text: backend.texts.slideshow, shortcut: "F5", action: "slideshow" }]
        onTriggered: action => {
            const p = viewer.current.path;
            if (action === "copy") backend.copyImage(p);
            else if (action === "background") backend.setBackground(p);
            else if (action === "lock") backend.setLockScreen(p);
            else if (action === "folder") backend.showInFolder(p);
            else if (action === "play") backend.playVideo(p);
            else if (action === "slideshow") viewer.startSlideshow();
        }
    }

    Timer {
        id: slideshowTimer
        interval: 4000
        repeat: true
        onTriggered: viewer.step(1)
    }

    // Keyboard, as in Windows Photos.
    focus: visible
    Keys.onPressed: event => {
        if (viewer.editing)
            return;
        if (viewer.slideshow) {
            viewer.stopSlideshow();
            event.accepted = true;
            return;
        }
        if (event.key === Qt.Key_Left) { viewer.step(-1); event.accepted = true; }
        else if (event.key === Qt.Key_Right) { viewer.step(1); event.accepted = true; }
        else if (event.key === Qt.Key_Plus || event.key === Qt.Key_Equal) { viewer.zoomBy(1.25); event.accepted = true; }
        else if (event.key === Qt.Key_Minus) { viewer.zoomBy(1 / 1.25); event.accepted = true; }
        else if (event.key === Qt.Key_0) { viewer.fit(); event.accepted = true; }
        else if (event.key === Qt.Key_Delete) { viewer.deleteRequested(viewer.current.path); event.accepted = true; }
        else if (event.key === Qt.Key_F5) { viewer.startSlideshow(); event.accepted = true; }
        else if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) {
            backend.rotate(viewer.current.path); event.accepted = true;
        } else if (event.key === Qt.Key_E && (event.modifiers & Qt.ControlModifier)) {
            viewer.editing = !viewer.isVideo; event.accepted = true;
        } else if (event.key === Qt.Key_C && (event.modifiers & Qt.ControlModifier)) {
            backend.copyImage(viewer.current.path); event.accepted = true;
        }
    }
    onVisibleChanged: if (visible) forceActiveFocus()
}
