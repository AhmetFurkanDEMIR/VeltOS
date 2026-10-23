// The items of a folder (also search results and the Recycle Bin) in the
// views of Windows 11 File Explorer: Details, Tiles and small to extra
// large icons. Selection with click / Ctrl / Shift and a selection
// rectangle, double-click opens, drag and drop moves or copies, F2 renames
// in place, type-ahead finds.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

FocusScope {
    id: root
    objectName: "folderView"

    readonly property var tab: backend.current
    readonly property var model: tab.items
    readonly property string mode: tab.viewMode
    readonly property bool details: mode === "details"
    readonly property var view: details ? listView : gridView
    property int renameRow: -1
    property string typed: ""
    signal itemMenu(real x, real y)
    signal backgroundMenu(real x, real y)
    signal requestDelete(bool permanently)
    signal showMessage(string text)

    // Columns: [key, title, width (0: fills), right aligned]
    readonly property var columns: tab.kind === "trash"
        ? [["name", backend.text("name"), 0, false], ["original", backend.text("original_location"), 220, false],
           ["deletedText", backend.text("date_deleted"), 170, false], ["sizeText", backend.text("size"), 90, true]]
        : tab.kind === "search"
        ? [["name", backend.text("name"), 0, false], ["modifiedText", backend.text("date_modified"), 160, false],
           ["type", backend.text("type"), 140, false], ["sizeText", backend.text("size"), 90, true],
           ["folder", backend.text("location"), 220, false]]
        : [["name", backend.text("name"), 0, false], ["modifiedText", backend.text("date_modified"), 170, false],
           ["type", backend.text("type"), 160, false], ["sizeText", backend.text("size"), 100, true]]
    readonly property var sortColumn: ({ name: "name", modifiedText: "modified", type: "type", sizeText: "size" })
    readonly property int iconSize: ({ small: 16, medium: 48, large: 96, xlarge: 192, tiles: 48 })[mode] || 16

    function startRename(row) {
        if (row < 0 || tab.kind === "trash")
            return;
        renameRow = row;
        view.positionViewAtIndex(row, ListView.Contain);
    }
    function finishRename(path, text) {
        const message = backend.rename(path, text);
        if (message !== "") {
            showMessage(message);
            return false;
        }
        renameRow = -1;
        root.forceActiveFocus();
        return true;
    }
    function columnsPerRow() {
        return details ? 1 : Math.max(1, Math.floor(gridView.width / gridView.cellWidth));
    }
    function moveCurrent(delta, extend) {
        const count = model.count;
        if (count === 0)
            return;
        let row = model.currentRow < 0 ? 0 : Math.max(0, Math.min(count - 1, model.currentRow + delta));
        model.select(row, extend ? "range" : "single");
        view.positionViewAtIndex(row, ListView.Contain);
    }
    function rowAt(x, y) {
        const p = mapToItem(view, x, y);
        if (p.x < 0 || p.y < 0 || p.x > view.width || p.y > view.height)
            return -1;
        return view.indexAt(p.x + view.contentX, p.y + view.contentY);
    }
    // Rows inside a rectangle of the view (view coordinates).
    function rowsIn(x1, y1, x2, y2) {
        const top = Math.min(y1, y2) + view.contentY, bottom = Math.max(y1, y2) + view.contentY;
        const left = Math.min(x1, x2), right = Math.max(x1, x2);
        const rows = [];
        if (details) {
            const first = Math.max(0, Math.floor(top / Theme.rowHeight));
            const last = Math.min(model.count - 1, Math.floor(bottom / Theme.rowHeight));
            for (let r = first; r <= last; ++r)
                rows.push(r);
            return rows;
        }
        const perRow = columnsPerRow();
        for (let r = 0; r < model.count; ++r) {
            const cx = (r % perRow) * gridView.cellWidth, cy = Math.floor(r / perRow) * gridView.cellHeight;
            if (cx + gridView.cellWidth - 6 > left && cx + 6 < right
                    && cy + gridView.cellHeight - 6 > top && cy + 6 < bottom)
                rows.push(r);
        }
        return rows;
    }
    function pageStep() {
        return details ? Math.max(1, Math.floor(view.height / Theme.rowHeight))
                       : columnsPerRow() * Math.max(1, Math.floor(view.height / gridView.cellHeight));
    }

    Connections {
        target: root.tab
        // A new folder or file: the backend asks once the listing shows it
        // (models.Tab.request_rename), so the row is there; the timer is
        // for a view that is still laying out.
        function onRenameRequested(path) {
            renameLater.path = path;
            if (!renameLater.tryNow())
                renameLater.restart();
        }
        function onChanged() { root.renameRow = -1; }
        // Refresh blinks the items, as Windows 11's File Explorer does.
        function onRefreshed() { blink.restart(); }
    }
    SequentialAnimation {
        id: blink
        NumberAnimation { target: root.view; property: "opacity"; to: 0; duration: 60 }
        NumberAnimation { target: root.view; property: "opacity"; to: 1; duration: 180; easing.type: Easing.OutCubic }
    }
    Timer {
        id: renameLater
        property string path
        interval: 150
        function tryNow() {
            for (let r = 0; r < root.model.count; ++r) {
                if (root.model.get(r).path === path) {
                    root.startRename(r);
                    return true;
                }
            }
            return false;
        }
        onTriggered: tryNow()
    }
    Timer {
        id: typeAhead
        interval: 900
        onTriggered: root.typed = ""
    }

    Keys.onPressed: event => {
        const ctrl = event.modifiers & Qt.ControlModifier, shift = event.modifiers & Qt.ShiftModifier;
        const perRow = columnsPerRow();
        if (event.key === Qt.Key_Down) moveCurrent(perRow, shift);
        else if (event.key === Qt.Key_Up) moveCurrent(-perRow, shift);
        else if (event.key === Qt.Key_Right && !details) moveCurrent(1, shift);
        else if (event.key === Qt.Key_Left && !details) moveCurrent(-1, shift);
        else if (event.key === Qt.Key_Home) moveCurrent(-model.count, shift);
        else if (event.key === Qt.Key_End) moveCurrent(model.count, shift);
        else if (event.key === Qt.Key_PageDown) moveCurrent(pageStep(), shift);
        else if (event.key === Qt.Key_PageUp) moveCurrent(-pageStep(), shift);
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (event.modifiers & Qt.AltModifier) backend.properties(); else backend.openSelection();
        }
        else if (event.key === Qt.Key_Delete) root.requestDelete(shift);
        else if (event.key === Qt.Key_F2) root.startRename(model.currentRow >= 0 ? model.currentRow : -1);
        else if (event.key === Qt.Key_Backspace) tab.back();
        else if (event.key === Qt.Key_Menu) root.itemMenu(width / 3, height / 3);
        else if (event.key === Qt.Key_Space && ctrl) model.select(model.currentRow, "toggle");
        else if (event.text.length === 1 && event.text >= " " && !ctrl && !(event.modifiers & Qt.AltModifier)) {
            root.typed += event.text;
            typeAhead.restart();
            const row = model.findPrefix(root.typed);
            if (row >= 0) {
                model.select(row, "single");
                view.positionViewAtIndex(row, ListView.Contain);
            }
        } else {
            return;
        }
        event.accepted = true;
    }

    // --- Details header ------------------------------------------------------------

    Rectangle {
        id: header
        visible: root.details
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: visible ? 32 : 0
        color: Theme.content

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 16
            spacing: 0
            Repeater {
                model: root.columns
                delegate: Rectangle {
                    id: columnHeader
                    required property var modelData
                    required property int index
                    readonly property string key: root.sortColumn[modelData[0]] || ""
                    Layout.fillWidth: modelData[2] === 0
                    Layout.preferredWidth: modelData[2] === 0 ? 200 : modelData[2]
                    Layout.fillHeight: true
                    color: headerHover.hovered && key !== "" ? Theme.hover : "transparent"
                    Text {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        horizontalAlignment: columnHeader.modelData[3] ? Text.AlignRight : Text.AlignLeft
                        text: columnHeader.modelData[1]
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont
                        elide: Text.ElideRight
                    }
                    Kirigami.Icon {
                        visible: columnHeader.key !== "" && root.tab.sortKey === columnHeader.key
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: 1
                        width: 8
                        height: 8
                        source: root.tab.sortDescending ? "arrow-down" : "arrow-up"
                        color: Theme.subtext
                        isMask: true
                    }
                    Rectangle {
                        visible: columnHeader.index > 0
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: 1
                        height: 18
                        color: Theme.separator
                    }
                    HoverHandler { id: headerHover }
                    TapHandler {
                        enabled: columnHeader.key !== ""
                        onTapped: root.tab.sortBy(columnHeader.key)
                    }
                }
            }
        }
    }

    // Scrolls the current view by a wheel delta (positive: towards the top),
    // vertically or, for the left-to-right "small icons" columns, sideways.
    function scrollBy(delta) {
        const v = root.view;
        if (!v || delta === 0)
            return;
        if (v === gridView && gridView.flow === GridView.FlowTopToBottom) {
            const maxX = Math.max(0, v.contentWidth - v.width);
            v.contentX = Math.max(v.originX, Math.min(v.originX + maxX, v.contentX - delta));
        } else {
            const maxY = Math.max(0, v.contentHeight - v.height);
            v.contentY = Math.max(v.originY, Math.min(v.originY + maxY, v.contentY - delta));
        }
    }

    // --- Views -------------------------------------------------------------------------

    Item {
        id: area
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: parent.bottom
        clip: true

        ListView {
            id: listView
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 4
            visible: root.details
            model: root.details ? root.model : null
            interactive: false
            boundsBehavior: Flickable.StopAtBounds
            reuseItems: true
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: DetailsRow {}
        }

        GridView {
            id: gridView
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 4
            anchors.topMargin: 6
            visible: !root.details
            model: root.details ? null : root.model
            interactive: false
            boundsBehavior: Flickable.StopAtBounds
            cellWidth: root.mode === "tiles" ? 260 : root.mode === "small" ? 240
                       : Math.max(90, root.iconSize + 36)
            cellHeight: root.mode === "tiles" ? 72 : root.mode === "small" ? 28
                        : root.iconSize + 52
            flow: root.mode === "small" ? GridView.FlowTopToBottom : GridView.FlowLeftToRight
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: IconCell {}
        }

        // Empty folder, loading, errors.
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 40
            visible: !root.tab.loading && root.model.count === 0
            text: root.tab.error !== "" ? root.tab.error
                  : root.tab.kind === "search" ? backend.text("no_results") : backend.text("folder_empty")
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
            width: Math.min(implicitWidth, parent.width - 40)
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 40
            visible: root.tab.loading && root.model.count === 0
            text: root.tab.kind === "search" ? backend.text("searching") : ""
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
        }

        // Selection rectangle.
        Rectangle {
            id: band
            visible: false
            color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.18)
            border.width: 1
            border.color: Theme.accent
        }

        // Drag source for the selected items.
        Item {
            id: dragSource
            Drag.dragType: Drag.Automatic
            Drag.supportedActions: Qt.CopyAction | Qt.MoveAction
            Drag.proposedAction: Qt.MoveAction
            Drag.mimeData: ({ "text/uri-list": root.dragUrls.join("\r\n") })
        }

        MouseArea {
            id: mouse

            property int pressRow: -1
            property point pressPos
            property bool banding: false
            property bool dragging: false
            property var deferred: null       // selection change applied on release

            anchors.fill: parent
            anchors.rightMargin: 14           // leave the scroll bar usable
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

            // The mouse wheel scrolls the items. Handled here, for every kind
            // of pointing device: a WheelHandler ignored the wheel of the
            // absolute pointers of virtual machines (QEMU, VirtualBox), so
            // long folders could not be scrolled (VM test 2026-10-20).
            onWheel: wheel => root.scrollBy(wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.pixelDelta.y)

            onPressed: event => {
                root.forceActiveFocus();
                const row = root.rowAt(event.x, event.y + header.height);
                pressRow = row;
                pressPos = Qt.point(event.x, event.y);
                banding = dragging = false;
                deferred = null;
                const ctrl = event.modifiers & Qt.ControlModifier, shift = event.modifiers & Qt.ShiftModifier;
                if (event.button === Qt.MiddleButton) {
                    const item = root.model.get(row);
                    if (row >= 0 && item.isDir)
                        backend.openInNewTab(item.path);
                    return;
                }
                if (event.button === Qt.RightButton) {
                    if (row >= 0 && !root.model.get(row).selected)
                        root.model.select(row, "single");
                    if (row < 0)
                        root.model.selectNone();
                    return;
                }
                if (row < 0) {
                    if (!ctrl)
                        root.model.selectNone();
                    return;
                }
                if (shift)
                    root.model.select(row, ctrl ? "addRange" : "range");
                else if (ctrl)
                    deferred = "toggle";
                else if (root.model.get(row).selected)
                    deferred = "single";
                else
                    root.model.select(row, "single");
            }
            onPositionChanged: event => {
                if (!pressed || event.buttons !== Qt.LeftButton)
                    return;
                const dx = event.x - pressPos.x, dy = event.y - pressPos.y;
                if (!banding && !dragging && Math.abs(dx) + Math.abs(dy) < 8)
                    return;
                if (pressRow >= 0 && !banding && root.tab.kind !== "trash") {
                    if (!dragging) {
                        if (deferred === "toggle")
                            root.model.select(pressRow, "toggle");
                        deferred = null;
                        dragging = true;
                        root.dragUrls = root.model.selectedUrls();
                        dragSource.Drag.active = true;
                    }
                    return;
                }
                if (pressRow < 0) {
                    banding = true;
                    band.visible = true;
                    band.x = Math.min(pressPos.x, event.x);
                    band.y = Math.min(pressPos.y, event.y);
                    band.width = Math.abs(dx);
                    band.height = Math.abs(dy);
                    const offsetX = root.details ? listView.anchors.leftMargin : gridView.anchors.leftMargin;
                    const offsetY = root.details ? 0 : gridView.anchors.topMargin;
                    const rows = root.rowsIn(pressPos.x - offsetX, pressPos.y - offsetY,
                                             event.x - offsetX, event.y - offsetY);
                    root.model.selectRows(rows);
                }
            }
            onReleased: event => {
                if (deferred !== null && pressRow >= 0 && !dragging)
                    root.model.select(pressRow, deferred);
                deferred = null;
                band.visible = false;
                banding = false;
                if (dragging) {
                    dragSource.Drag.active = false;
                    dragging = false;
                }
                if (event.button === Qt.RightButton) {
                    if (pressRow >= 0)
                        root.itemMenu(event.x, event.y + header.height);
                    else
                        root.backgroundMenu(event.x, event.y + header.height);
                }
            }
            onDoubleClicked: event => {
                if (event.button !== Qt.LeftButton)
                    return;
                const row = root.rowAt(event.x, event.y + header.height);
                if (row >= 0) {
                    root.model.select(row, "single");
                    backend.openSelection();
                }
            }
        }

        DropArea {
            anchors.fill: parent
            keys: ["text/uri-list"]
            onDropped: drop => {
                if (!drop.hasUrls || root.tab.kind !== "folder")
                    return;
                const row = root.rowAt(drop.x, drop.y + header.height);
                const item = row >= 0 ? root.model.get(row) : null;
                const target = item && item.isDir ? item.path : root.tab.location;
                backend.drop(drop.urls, target);
                drop.accept(Qt.CopyAction);
            }
        }
    }

    property var dragUrls: []

    // --- Delegates -------------------------------------------------------------------

    component ItemIcon: Item {
        property var item
        property int size: 16
        Image {
            anchors.fill: parent
            visible: parent.item.thumbnail !== "" && parent.size >= 48
            source: visible ? parent.item.thumbnail : ""
            sourceSize.width: parent.size * 2
            sourceSize.height: parent.size * 2
            fillMode: Image.PreserveAspectFit
            asynchronous: true
        }
        Kirigami.Icon {
            anchors.fill: parent
            visible: parent.item.thumbnail === "" || parent.size < 48
            source: parent.item.icon
            fallback: parent.item.isDir ? "folder" : "text-x-generic"
        }
    }

    component RenameField: Rectangle {
        id: field
        property string path
        property string name
        signal done()
        color: Theme.field
        border.width: 1
        border.color: Theme.accent
        radius: 2
        TextInput {
            id: input
            // Like a Windows text box: in the Tab order, the text cursor over it and
            // (in a layout) the full height of its box. A plain TextInput has neither.
            activeFocusOnTab: true
            HoverHandler { cursorShape: Qt.IBeamCursor }
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.text
            selectionColor: Theme.accent
            selectedTextColor: "#FFFFFF"
            font.pixelSize: Theme.fontSize
            clip: true
            text: field.name
            Component.onCompleted: {
                forceActiveFocus();
                // Like Windows: the name without its extension is selected.
                const dot = field.name.lastIndexOf(".");
                select(0, dot > 0 ? dot : field.name.length);
            }
            onAccepted: root.finishRename(field.path, text)
            Keys.onEscapePressed: {
                root.renameRow = -1;
                root.forceActiveFocus();
            }
            onActiveFocusChanged: {
                if (!activeFocus && root.renameRow >= 0 && text !== field.name)
                    root.finishRename(field.path, text);
                else if (!activeFocus)
                    root.renameRow = -1;
            }
        }
    }

    component DetailsRow: Rectangle {
        id: row
        required property int index
        required property string name
        required property string path
        required property bool isDir
        required property string icon
        required property string thumbnail
        required property bool selected
        required property bool cut
        required property var model

        width: listView.width - 12
        height: Theme.rowHeight
        radius: 4
        color: selected ? (rowHover.hovered ? Theme.selectedHover : Theme.selected)
                        : (rowHover.hovered ? Theme.hover : "transparent")
        opacity: cut ? 0.55 : 1
        HoverHandler { id: rowHover }

        DropArea {
            anchors.fill: parent
            enabled: row.isDir && !row.selected
            onDropped: drop => {
                if (drop.hasUrls) {
                    backend.drop(drop.urls, row.path);
                    drop.accept(Qt.CopyAction);
                }
            }
            Rectangle {
                anchors.fill: parent
                radius: 4
                color: "transparent"
                border.width: 1
                border.color: Theme.accent
                visible: parent.containsDrag
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.rightMargin: 4
            spacing: 0
            Repeater {
                model: root.columns
                delegate: Item {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: modelData[2] === 0
                    Layout.preferredWidth: modelData[2] === 0 ? 200 : modelData[2]
                    Layout.fillHeight: true
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 10
                        ItemIcon {
                            visible: index === 0
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 18
                            item: ({ thumbnail: row.thumbnail, icon: row.icon, isDir: row.isDir })
                            size: 18
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: !(index === 0 && root.renameRow === row.index)
                            horizontalAlignment: modelData[3] ? Text.AlignRight : Text.AlignLeft
                            text: index === 0 ? row.name : (row.model[modelData[0]] || "")
                            color: index === 0 ? Theme.text : Theme.subtext
                            font.pixelSize: Theme.fontSize
                            elide: index === 0 ? Text.ElideRight : Text.ElideMiddle
                        }
                        Loader {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 24
                            active: index === 0 && root.renameRow === row.index
                            visible: active
                            sourceComponent: RenameField { path: row.path; name: row.name }
                        }
                    }
                }
            }
        }
    }

    component IconCell: Item {
        id: cell
        required property int index
        required property string name
        required property string path
        required property bool isDir
        required property string icon
        required property string thumbnail
        required property bool selected
        required property bool cut
        required property string type
        required property string sizeText

        readonly property bool tiles: root.mode === "tiles"
        readonly property bool small: root.mode === "small"

        width: gridView.cellWidth
        height: gridView.cellHeight
        opacity: cut ? 0.55 : 1

        Rectangle {
            id: box
            anchors.fill: parent
            anchors.margins: 3
            radius: 4
            color: cell.selected ? (cellHover.hovered ? Theme.selectedHover : Theme.selected)
                                 : (cellHover.hovered ? Theme.hover : "transparent")
            HoverHandler { id: cellHover }
            DropArea {
                anchors.fill: parent
                enabled: cell.isDir && !cell.selected
                onDropped: drop => {
                    if (drop.hasUrls) {
                        backend.drop(drop.urls, cell.path);
                        drop.accept(Qt.CopyAction);
                    }
                }
                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: "transparent"
                    border.width: 1
                    border.color: Theme.accent
                    visible: parent.containsDrag
                }
            }
        }

        // Icon views: icon above the name.
        ColumnLayout {
            visible: !cell.tiles && !cell.small
            anchors.fill: box
            anchors.margins: 4
            spacing: 4
            ItemIcon {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: root.iconSize
                Layout.preferredHeight: root.iconSize
                item: ({ thumbnail: cell.thumbnail, icon: cell.icon, isDir: cell.isDir })
                size: root.iconSize
            }
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.renameRow !== cell.index
                horizontalAlignment: Text.AlignHCenter
                text: cell.name
                color: Theme.text
                font.pixelSize: Theme.smallFont
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            Loader {
                Layout.fillWidth: true
                Layout.preferredHeight: 24
                active: root.renameRow === cell.index && !cell.tiles && !cell.small
                visible: active
                sourceComponent: RenameField { path: cell.path; name: cell.name }
            }
        }

        // Tiles and small icons: icon beside the text.
        RowLayout {
            visible: cell.tiles || cell.small
            anchors.fill: box
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            spacing: cell.tiles ? 10 : 8
            ItemIcon {
                Layout.preferredWidth: cell.tiles ? 48 : 16
                Layout.preferredHeight: cell.tiles ? 48 : 16
                item: ({ thumbnail: cell.thumbnail, icon: cell.icon, isDir: cell.isDir })
                size: cell.tiles ? 48 : 16
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                visible: root.renameRow !== cell.index
                Text {
                    Layout.fillWidth: true
                    text: cell.name
                    color: Theme.text
                    font.pixelSize: Theme.fontSize
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    visible: cell.tiles
                    text: cell.type
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    visible: cell.tiles && cell.sizeText !== ""
                    text: cell.sizeText
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                }
            }
            Loader {
                Layout.fillWidth: true
                Layout.preferredHeight: 24
                active: root.renameRow === cell.index && (cell.tiles || cell.small)
                visible: active
                sourceComponent: RenameField { path: cell.path; name: cell.name }
            }
        }
    }
}
