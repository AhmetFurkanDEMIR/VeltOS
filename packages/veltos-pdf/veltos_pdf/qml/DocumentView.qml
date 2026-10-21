// One open PDF: thumbnails or bookmarks on the left, the pages in the
// middle (continuous, text can be selected and copied, search results
// highlighted), the quick tool rail on the right (search, thumbnails,
// bookmarks, rotate, print, properties) and the floating page and zoom bar
// at the bottom right, as in modern PDF readers.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Pdf
import "."

Item {
    id: view

    property string path
    property string url
    property string password
    property bool readMode: false
    property string panel: ""               // "", "thumbnails", "bookmarks", "search"
    readonly property alias document: doc
    readonly property int pageCount: doc.pageCount
    signal printRequested()
    signal propertiesRequested()

    // "width" or "page" keeps the pages fitted when the window or the side
    // panel changes their room; zooming by hand ends it. A tab that is not
    // shown has no size yet and is fitted when it gets one (a scale from a
    // zero width made the page view's rows empty).
    property string fitMode: "width"
    function zoomBy(factor) {
        fitMode = "";
        pages.renderScale = Math.max(0.1, Math.min(8, pages.renderScale * factor));
    }
    function fitWidth() {
        fitMode = "width";
        refit();
    }
    function fitPage() {
        fitMode = "page";
        refit();
    }
    function refit() {
        if (pages.width < 120 || pages.height < 120 || doc.status !== PdfDocument.Ready)
            return;
        if (fitMode === "width")
            pages.scaleToWidth(pages.width - 40, pages.height);
        else if (fitMode === "page")
            pages.scaleToPage(pages.width - 40, pages.height - 20);
    }
    Timer { id: refitTimer; interval: 60; onTriggered: view.refit() }
    // Qt 6.8's PdfMultiPageView lays its pages out again when the scale
    // changes, but before its column width (pageHolderWidth) has followed
    // the new scale: after zooming out the pages sat off-centre, partly
    // outside the window (VM, 2026-10-21). Lay them out once more.
    function relayoutPages() {
        for (const child of pages.children) {
            if (child.forceLayout !== undefined) {
                child.forceLayout();
                child.returnToBounds();
            }
        }
    }

    function togglePanel(name) {
        panel = panel === name ? "" : name;
        if (name === "search" && panel === "search")
            Qt.callLater(() => searchField.forceActiveFocus());
    }

    PdfDocument {
        id: doc
        source: view.url
        password: view.password
        onStatusChanged: if (doc.status === PdfDocument.Ready) refitTimer.restart()
    }

    component RailButton: Rectangle {
        id: rb
        property string glyph
        property string label
        property bool active: false
        signal clicked()
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
        radius: 6
        color: active ? Theme.selected : (rbHover.hovered ? Theme.hover : "transparent")
        Accessible.role: Accessible.Button
        Accessible.name: label
        Glyph { anchors.centerIn: parent; width: 18; height: 18; kind: rb.glyph; color: rb.active ? Theme.accent : Theme.text }
        ToolTip.visible: rbHover.hovered
        ToolTip.delay: 500
        ToolTip.text: label
        HoverHandler { id: rbHover }
        TapHandler { onTapped: rb.clicked() }
    }

    Rectangle { anchors.fill: parent; color: Theme.dark ? "#1A1B22" : "#E9ECF2" }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- Left panel: thumbnails, bookmarks, search results -------------------------------
        Rectangle {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            visible: view.panel !== "" && !view.readMode
            color: Theme.content
            Rectangle { anchors.right: parent.right; height: parent.height; width: 1; color: Theme.separator }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: view.panel === "thumbnails" ? backend.texts.thumbnails
                              : view.panel === "bookmarks" ? backend.texts.bookmarks : backend.texts.search
                        color: Theme.text
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Rectangle {
                        implicitWidth: 28; implicitHeight: 28; radius: 4
                        color: closeHover.hovered ? Theme.hover : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: backend.texts.close
                        Glyph { anchors.centerIn: parent; width: 10; height: 10; kind: "close" }
                        HoverHandler { id: closeHover }
                        TapHandler { onTapped: view.panel = "" }
                    }
                }

                // Search.
                Rectangle {
                    visible: view.panel === "search"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    radius: 4
                    color: Theme.field
                    border.width: 1
                    border.color: searchField.activeFocus ? Theme.accent : Theme.fieldBorder
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 6
                        TextInput {
                            id: searchField
                            Layout.fillWidth: true
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            clip: true
                            selectByMouse: true
                            onTextChanged: searchDelay.restart()
                            onAccepted: pages.searchForward()
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                visible: searchField.text === ""
                                text: backend.texts.find_placeholder
                                color: Theme.subtext
                                font.pixelSize: Theme.fontSize
                            }
                        }
                        Glyph { Layout.preferredWidth: 14; Layout.preferredHeight: 14; kind: "search"; color: Theme.subtext }
                    }
                    Timer { id: searchDelay; interval: 300; onTriggered: pages.searchString = searchField.text }
                }
                RowLayout {
                    visible: view.panel === "search" && pages.searchString !== ""
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: pages.searchModel.count === 0 ? backend.texts.no_results
                              : pages.searchModel.count === 1 ? backend.texts.one_result
                              : backend.texts.results.replace("{count}", pages.searchModel.count)
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont
                    }
                    RailButton { glyph: "chevron-up"; label: backend.texts.previous_page; onClicked: pages.searchBack() }
                    RailButton { glyph: "chevron-down"; label: backend.texts.next_page; onClicked: pages.searchForward() }
                }
                ListView {
                    id: results
                    visible: view.panel === "search"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 2
                    model: pages.searchModel
                    delegate: Rectangle {
                        required property int index
                        required property int page
                        required property string contextBefore
                        required property string contextAfter
                        width: results.width
                        implicitHeight: resultColumn.implicitHeight + 14
                        radius: 4
                        color: index === pages.searchModel.currentResult ? Theme.selected
                               : (resultHover.hovered ? Theme.hover : "transparent")
                        ColumnLayout {
                            id: resultColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.margins: 8
                            spacing: 2
                            Text { text: backend.texts.page_short.replace("{page}", page + 1); color: Theme.subtext
                                   font.pixelSize: Theme.smallFont }
                            Text {
                                Layout.fillWidth: true
                                // QtPdf marks line breaks in the context with a return symbol.
                                text: (contextBefore + "<b>" + pages.searchString + "</b>" + contextAfter).replace(/[\u21b5\u23ce\n]/g, " ")
                                textFormat: Text.StyledText
                                color: Theme.text
                                font.pixelSize: Theme.smallFont
                                elide: Text.ElideRight
                                maximumLineCount: 2
                                wrapMode: Text.WordWrap
                            }
                        }
                        HoverHandler { id: resultHover }
                        TapHandler { onTapped: pages.searchModel.currentResult = index }
                    }
                }

                // Thumbnails.
                ListView {
                    id: thumbs
                    visible: view.panel === "thumbnails"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 12
                    model: doc.pageCount
                    delegate: Column {
                        required property int index
                        width: thumbs.width
                        spacing: 4
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: thumb.width + 8
                            height: thumb.height + 8
                            radius: 4
                            color: "transparent"
                            border.width: index === pages.currentPage ? 2 : 0
                            border.color: Theme.accent
                            PdfPageImage {
                                id: thumb
                                anchors.centerIn: parent
                                document: doc
                                currentFrame: index
                                asynchronous: true
                                width: 140
                                height: width * (doc.pagePointSize(index).height / Math.max(1, doc.pagePointSize(index).width))
                                sourceSize.width: 280
                                fillMode: Image.PreserveAspectFit
                            }
                            TapHandler { onTapped: pages.goToPage(index) }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: index + 1
                            color: Theme.subtext
                            font.pixelSize: Theme.smallFont
                        }
                    }
                }

                // Bookmarks (the document outline).
                TreeView {
                    id: outline
                    visible: view.panel === "bookmarks"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: PdfBookmarkModel { document: doc }
                    delegate: Item {
                        id: entry
                        required property TreeView treeView
                        required property bool isTreeNode
                        required property bool expanded
                        required property bool hasChildren
                        required property int depth
                        required property int row
                        required property string title
                        required property int page
                        required property point location
                        required property real zoom
                        implicitWidth: outline.width
                        implicitHeight: 34
                        Rectangle {
                            anchors.fill: parent
                            radius: 4
                            color: markHover.hovered ? Theme.hover : "transparent"
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 6 + entry.depth * 14
                            spacing: 6
                            Glyph {
                                Layout.preferredWidth: 10; Layout.preferredHeight: 10
                                opacity: entry.hasChildren ? 1 : 0
                                kind: entry.expanded ? "chevron-down" : "chevron-right"
                                TapHandler { onTapped: entry.treeView.toggleExpanded(entry.row) }
                            }
                            Text { Layout.fillWidth: true; text: entry.title; color: Theme.text; font.pixelSize: Theme.fontSize
                                   elide: Text.ElideRight }
                        }
                        HoverHandler { id: markHover }
                        TapHandler { onTapped: pages.goToLocation(entry.page, entry.location, entry.zoom) }
                    }
                }
                Text {
                    visible: view.panel === "bookmarks" && outline.rows === 0
                    Layout.fillWidth: true
                    text: backend.texts.no_bookmarks
                    color: Theme.subtext
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.WordWrap
                }
            }
        }

        // --- The pages -----------------------------------------------------------------------
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            PdfMultiPageView {
                id: pages
                anchors.fill: parent
                document: doc
                onWidthChanged: if (view.fitMode !== "") refitTimer.restart()
                onHeightChanged: if (view.fitMode === "page") refitTimer.restart()
                onRenderScaleChanged: Qt.callLater(view.relayoutPages)
            }

            BusyIndicator {
                anchors.centerIn: parent
                running: doc.status === PdfDocument.Loading
                visible: running
            }
            Text {
                anchors.centerIn: parent
                visible: doc.status === PdfDocument.Error
                text: backend.texts.cant_open.replace("{name}", view.path.split("/").pop())
                color: Theme.subtext
                font.pixelSize: 15
                width: Math.min(parent.width - 60, 480)
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            // Floating page and zoom bar.
            Rectangle {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 24
                anchors.rightMargin: 36
                width: bar.implicitWidth + 16
                height: 44
                radius: 22
                color: Theme.card
                border.width: 1
                border.color: Theme.cardBorder
                visible: doc.status === PdfDocument.Ready
                Rectangle {
                    z: -1
                    anchors.fill: parent
                    anchors.topMargin: 2
                    anchors.bottomMargin: -4
                    radius: 24
                    color: "#000000"
                    opacity: Theme.dark ? 0.35 : 0.1
                }
                RowLayout {
                    id: bar
                    anchors.centerIn: parent
                    spacing: 2
                    RailButton { Layout.preferredWidth: 32; Layout.preferredHeight: 32; glyph: "chevron-up"
                                 label: backend.texts.previous_page; onClicked: pages.goToPage(Math.max(0, pages.currentPage - 1)) }
                    TextInput {
                        id: pageField
                        Layout.preferredWidth: 34
                        horizontalAlignment: Text.AlignRight
                        text: String(pages.currentPage + 1)
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                        validator: IntValidator { bottom: 1; top: Math.max(1, doc.pageCount) }
                        selectByMouse: true
                        onAccepted: pages.goToPage(parseInt(text) - 1)
                    }
                    Text { text: " / " + doc.pageCount; color: Theme.subtext; font.pixelSize: Theme.fontSize }
                    RailButton { Layout.preferredWidth: 32; Layout.preferredHeight: 32; glyph: "chevron-down"
                                 label: backend.texts.next_page
                                 onClicked: pages.goToPage(Math.min(doc.pageCount - 1, pages.currentPage + 1)) }
                    Rectangle { width: 1; height: 20; color: Theme.separator; Layout.leftMargin: 4; Layout.rightMargin: 4 }
                    RailButton { Layout.preferredWidth: 32; Layout.preferredHeight: 32; glyph: "zoom-out"
                                 label: backend.texts.zoom_out; onClicked: view.zoomBy(1 / 1.2) }
                    Text {
                        Layout.preferredWidth: 44
                        horizontalAlignment: Text.AlignHCenter
                        text: Math.round(pages.renderScale * 100) + "%"
                        color: Theme.text
                        font.pixelSize: Theme.smallFont
                    }
                    RailButton { Layout.preferredWidth: 32; Layout.preferredHeight: 32; glyph: "zoom-in"
                                 label: backend.texts.zoom_in; onClicked: view.zoomBy(1.2) }
                    RailButton { Layout.preferredWidth: 32; Layout.preferredHeight: 32; glyph: "fit"
                                 label: backend.texts.fit_page; onClicked: view.fitPage() }
                }
            }
        }

        // --- Quick tool rail ---------------------------------------------------------------------
        Rectangle {
            Layout.preferredWidth: 56
            Layout.fillHeight: true
            visible: !view.readMode
            color: Theme.content
            Rectangle { anchors.left: parent.left; height: parent.height; width: 1; color: Theme.separator }
            ColumnLayout {
                anchors.top: parent.top
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.topMargin: 10
                spacing: 6
                RailButton { glyph: "search"; label: backend.texts.search; active: view.panel === "search"
                             onClicked: view.togglePanel("search") }
                RailButton { glyph: "grid"; label: backend.texts.thumbnails; active: view.panel === "thumbnails"
                             onClicked: view.togglePanel("thumbnails") }
                RailButton { glyph: "bookmark"; label: backend.texts.bookmarks; active: view.panel === "bookmarks"
                             onClicked: view.togglePanel("bookmarks") }
                Rectangle { Layout.alignment: Qt.AlignHCenter; width: 24; height: 1; color: Theme.separator }
                RailButton { glyph: "rotate"; label: backend.texts.rotate; onClicked: pages.pageRotation = (pages.pageRotation + 90) % 360 }
                RailButton { glyph: "fit"; label: backend.texts.fit_width; onClicked: view.fitWidth() }
                RailButton { glyph: "print"; label: backend.texts.print; onClicked: view.printRequested() }
                RailButton { glyph: "info"; label: backend.texts.properties; onClicked: view.propertiesRequested() }
            }
        }
    }

    // Copy (Ctrl+C) and Select all (Ctrl+A) of the selected text.
    Shortcut { sequences: [StandardKey.Copy]; enabled: view.visible; onActivated: pages.copySelectionToClipboard() }
    Shortcut { sequences: [StandardKey.SelectAll]; enabled: view.visible; onActivated: pages.selectAll() }
    Shortcut { sequences: [StandardKey.Find]; enabled: view.visible
               onActivated: { view.panel = "search"; searchField.forceActiveFocus(); } }
    Shortcut { sequence: "Ctrl+="; enabled: view.visible; onActivated: view.zoomBy(1.2) }
    Shortcut { sequence: "Ctrl++"; enabled: view.visible; onActivated: view.zoomBy(1.2) }
    Shortcut { sequence: "Ctrl+-"; enabled: view.visible; onActivated: view.zoomBy(1 / 1.2) }
    Shortcut { sequence: "Ctrl+0"; enabled: view.visible; onActivated: view.fitPage() }
    Shortcut { sequence: "Ctrl+2"; enabled: view.visible; onActivated: view.fitWidth() }
}
