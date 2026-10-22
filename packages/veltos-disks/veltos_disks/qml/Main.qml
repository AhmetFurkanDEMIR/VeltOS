// VeltOS Disk Management window, laid out like Windows 11's Disk
// Management: the volume list on top, the disk map (every disk with its
// partitions and unallocated space to scale) below, a right-click menu on
// each volume and dialogs for Format, Delete, New Simple Volume, label,
// Initialize and Properties.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window
    width: 1040
    height: 720
    minimumWidth: 800
    minimumHeight: 520
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    // The selected segment (a volume, unallocated or free space) or disk.
    property var selected: null
    property string selectedKey: ""
    readonly property real mib: 1024 * 1024

    // Disks are selected as {isDisk: true, ...disk}; segments as they are.
    function keyOf(item) {
        if (!item)
            return "";
        if (item.isDisk)
            return "disk:" + item.object;
        if (item.kind === "volume")
            return item.object;
        return item.disk + "@" + item.offset;
    }
    function select(item) {
        selected = item;
        selectedKey = keyOf(item);
    }
    // For tests and the map: select a volume by its object path.
    function selectVolume(objectPath) {
        for (const volume of backend.volumes) {
            if (volume.object === objectPath) {
                select(volume);
                return true;
            }
        }
        return false;
    }
    // Select a disk's first unallocated or free segment (tests).
    function selectUnallocated(diskObject) {
        for (const disk of backend.disks) {
            if (disk.object !== diskObject)
                continue;
            for (const segment of disk.segments) {
                if (segment.kind !== "volume") {
                    select(segment);
                    return true;
                }
            }
        }
        return false;
    }
    function selectDisk(diskObject) {
        for (const disk of backend.disks) {
            if (disk.object === diskObject) {
                select(Object.assign({isDisk: true}, disk));
                return true;
            }
        }
        return false;
    }
    function menuForSelected() {
        showMenu(selected, 20, 20);
    }
    // The texts of the selected item's menu, "|"-separated (tests).
    function menuTexts() {
        return menuItems(selected).map(entry => entry.separator ? "-" : entry.text + (entry.enabled === false ? " (off)" : "")).join("|");
    }
    function fsOptions() {
        const names = {ntfs: "NTFS", exfat: "exFAT", vfat: "FAT32", ext4: "ext4"};
        return backend.formats.map(fs => ({value: fs, label: names[fs] || fs}));
    }
    function defaultFs(current) {
        if (backend.formats.indexOf(current) >= 0)
            return current;
        return backend.formats.length > 0 ? backend.formats[0] : "";
    }

    // The right-click menu of what is selected.
    function menuItems(item) {
        const t = backend.texts;
        if (!item)
            return [];
        if (item.isDisk) {
            const items = [];
            // (A blank disk's table is None in Python: undefined here, not null.)
            if (!item.table && item.kind !== "cdrom" && !item.readOnly)
                items.push({text: t.initialize, action: "initialize"});
            if (item.removable || item.kind === "cdrom")
                items.push({text: t.eject, action: "eject-disk"});
            items.push({text: t.properties, action: "properties"});
            return items;
        }
        if (item.kind === "unallocated" || item.kind === "free")
            return [{text: t.new_volume, action: "new", enabled: item.table !== "" && item.table !== null}];
        return [
            {text: t.open, action: "open", enabled: item.canOpen},
            {text: t.explore, action: "open", enabled: item.canOpen},
            {separator: true},
            {text: item.mounted ? t.unmount : t.mount, action: item.mounted ? "unmount" : "mount",
             enabled: item.mounted ? item.canUnmount : item.canMount},
            {text: t.eject, action: "eject", enabled: item.canEject},
            {separator: true},
            {text: t.change_label, action: "label", enabled: item.canLabel},
            {text: t.format, action: "format", enabled: item.canFormat},
            {text: t.delete_volume, action: "delete", enabled: item.canDelete},
            {separator: true},
            {text: t.properties, action: "properties"},
        ];
    }
    function showMenu(item, x, y) {
        select(item);
        menu.items = menuItems(item);
        menu.showAt(x, y);
    }
    function run(action) {
        const item = selected, t = backend.texts;
        if (!item)
            return;
        if (action === "open" || action === "mount" || action === "unmount" || action === "eject")
            backend.act(action, item.object, {});
        else if (action === "eject-disk" && item.segments) {
            const volume = item.segments.find(s => s.kind === "volume");
            if (volume)
                backend.act("eject", volume.object, {});
        } else if (action === "format")
            openFormat();
        else if (action === "delete")
            dialog.openWith({title: t.delete_title, message: t.delete_warning, acceptText: t.yes, rejectText: t.no,
                             fields: [], onAccept: values => backend.act("delete", item.object, {})});
        else if (action === "label")
            dialog.openWith({title: t.label_title, fields: [{key: "label", label: t.volume_label, type: "text",
                                                            value: item.label}],
                             onAccept: values => backend.act("label", item.object, {label: values.label})});
        else if (action === "new")
            openNewVolume();
        else if (action === "initialize")
            dialog.openWith({title: t.initialize_title, message: t.initialize_text.replace("{name}", item.title),
                             fields: [{key: "style", label: t.style, type: "choice", value: "gpt",
                                       options: [{value: "gpt", label: t.gpt}, {value: "dos", label: t.mbr}]}],
                             onAccept: values => backend.act("initialize", item.object, {style: values.style})});
        else if (action === "properties")
            openProperties();
    }
    function openFormat() {
        const item = selected, t = backend.texts;
        if (!item || item.kind !== "volume")
            return;
        dialog.openWith({
            title: t.format_title.replace("{name}", item.title || item.device),
            fields: [{key: "label", label: t.volume_label, type: "text", value: item.label},
                     {key: "fs", label: t.fs_choice, type: "choice", value: defaultFs(item.fsType),
                      options: fsOptions()},
                     {key: "quick", label: t.quick_format, type: "check", value: true}],
            onAccept: values => dialog.openWith({
                title: t.format_title.replace("{name}", item.title || item.device), message: t.format_warning,
                acceptText: t.yes, rejectText: t.no, fields: [],
                onAccept: () => backend.act("format", item.object, values)})
        });
    }
    function openNewVolume() {
        const item = selected, t = backend.texts;
        if (!item || (item.kind !== "unallocated" && item.kind !== "free"))
            return;
        const maxMb = Math.floor(item.size / window.mib);
        dialog.openWith({
            title: t.new_volume_title,
            fields: [{key: "sizeMb", label: t.volume_size, type: "number", value: maxMb, max: maxMb,
                      hint: t.max_size.replace("{size}", String(maxMb))},
                     {key: "fs", label: t.fs_choice, type: "choice", value: defaultFs("ntfs"), options: fsOptions()},
                     {key: "label", label: t.volume_label, type: "text", value: ""},
                     {key: "quick", label: t.quick_format, type: "check", value: true}],
            onAccept: values => {
                const sizeMb = Math.max(1, Math.min(maxMb, parseInt(values.sizeMb) || maxMb));
                backend.act("create", item.disk, {offset: item.offset, size: sizeMb >= maxMb ? 0 : sizeMb * window.mib,
                                                  fs: values.fs, label: values.label, quick: values.quick});
            }
        });
    }
    function openProperties() {
        const item = selected, t = backend.texts;
        if (!item)
            return;
        let fields;
        if (item.isDisk) {
            fields = [{key: "model", label: t.prop_model, type: "info", value: item.model || t.unknown},
                      {key: "device", label: t.prop_device, type: "info", value: item.device},
                      {key: "capacity", label: t.capacity, type: "info", value: item.sizeText},
                      {key: "style", label: t.style, type: "info",
                       value: item.table === "gpt" ? "GPT" : (item.table === "dos" ? "MBR" : t.not_initialized)},
                      {key: "status", label: t.status, type: "info", value: item.statusText}];
        } else if (item.kind === "volume") {
            fields = [{key: "fs", label: t.file_system, type: "info", value: item.fsText},
                      {key: "capacity", label: t.capacity, type: "info", value: item.sizeText},
                      {key: "used", label: t.prop_used, type: "info", value: item.usedText || "—"},
                      {key: "free", label: t.free_space, type: "info", value: item.freeText || "—"},
                      {key: "device", label: t.prop_device, type: "info", value: item.device},
                      {key: "mount", label: t.prop_mount, type: "info", value: item.mountText},
                      {key: "disk", label: t.prop_disk, type: "info", value: item.diskTitle + " " + item.diskModel},
                      {key: "status", label: t.status, type: "info", value: item.statusText}];
        } else {
            fields = [{key: "capacity", label: t.capacity, type: "info", value: item.sizeText},
                      {key: "disk", label: t.prop_disk, type: "info", value: item.diskTitle}];
        }
        dialog.openWith({title: t.properties_title.replace("{name}", item.title || item.device || ""),
                         fields: fields, rejectText: "", onAccept: null});
    }

    Connections {
        target: backend
        function onMessage(text) {
            dialog.openWith({title: backend.texts.app_title, message: text, fields: [], rejectText: "", onAccept: null});
        }
        function onChanged() {
            // Keep the selection on the same item after a refresh.
            if (selectedKey === "")
                return;
            for (const disk of backend.disks) {
                if ("disk:" + disk.object === selectedKey) {
                    selected = Object.assign({isDisk: true}, disk);
                    return;
                }
                for (const segment of disk.segments) {
                    if (keyOf(segment) === selectedKey) {
                        selected = segment;
                        return;
                    }
                }
            }
            select(null);
        }
    }

    WinMenu {
        id: menu
        onTriggered: action => window.run(action)
    }
    FormDialog {
        id: dialog
        objectName: "formDialog"
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // The command bar: Refresh / Rescan Disks (Windows' Action menu).
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.round(48 * Theme.textScale)
            color: Theme.toolbar
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 8
                Text {
                    text: backend.texts.app_title
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    font.weight: Font.DemiBold
                }
                Item { Layout.fillWidth: true }
                Text {
                    visible: backend.busy
                    text: backend.busyText
                    color: Theme.subtext
                    font.pixelSize: Theme.smallSize
                }
                BusyIndicator {
                    visible: backend.busy
                    running: backend.busy
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                }
                component BarButton: Rectangle {
                    id: barButton
                    property string label
                    property string iconName
                    signal clicked()
                    Layout.preferredHeight: 32
                    implicitWidth: barRow.implicitWidth + 24
                    radius: 5
                    color: barHover.hovered ? Theme.rowHover : "transparent"
                    enabled: !backend.busy
                    opacity: enabled ? 1 : 0.5
                    RowLayout {
                        id: barRow
                        anchors.centerIn: parent
                        spacing: 8
                        Kirigami.Icon {
                            implicitWidth: 16
                            implicitHeight: 16
                            source: barButton.iconName
                            isMask: true
                            color: Theme.text
                        }
                        Text {
                            text: barButton.label
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                        }
                    }
                    HoverHandler { id: barHover }
                    TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: barButton.clicked() }
                }
                BarButton { label: backend.texts.refresh; iconName: "view-refresh"; onClicked: backend.refresh() }
                BarButton { label: backend.texts.rescan; iconName: "drive-harddisk"; onClicked: backend.refresh() }
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.cardBorder }

        // --- The volume list -----------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.round(window.height * 0.4)
            color: Theme.card
            readonly property var columns: [
                ["title", backend.texts.volume, 220, false], ["layoutText", backend.texts.layout, 80, false],
                ["typeText", backend.texts.type, 80, false], ["fsText", backend.texts.file_system, 110, false],
                ["statusText", backend.texts.status, 0, false], ["sizeText", backend.texts.capacity, 100, true],
                ["freeText", backend.texts.free_space, 100, true], ["percentFree", backend.texts.percent_free, 70, true]]
            function widthOf(index) {
                const column = columns[index];
                if (column[2] > 0)
                    return Math.round(column[2] * Theme.textScale);
                let fixed = 0;
                for (const c of columns)
                    fixed += c[2] > 0 ? Math.round(c[2] * Theme.textScale) : 0;
                return Math.max(120, width - fixed - 24);
            }
            id: table

            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Theme.rowHeight
                    color: Theme.card
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        Repeater {
                            model: table.columns
                            delegate: Item {
                                required property var modelData
                                required property int index
                                width: table.widthOf(index)
                                height: Theme.rowHeight
                                Text {
                                    anchors.fill: parent
                                    anchors.rightMargin: 12
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: modelData[3] ? Text.AlignRight : Text.AlignLeft
                                    text: modelData[1]
                                    color: Theme.subtext
                                    font.pixelSize: Theme.smallSize
                                    elide: Text.ElideRight
                                }
                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 1
                                    height: parent.height - 12
                                    color: Theme.cardBorder
                                }
                            }
                        }
                    }
                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.cardBorder }
                }
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Text {
                        anchors.centerIn: parent
                        visible: backend.volumes.length === 0
                        text: backend.error !== "" ? backend.error : backend.texts.no_disks
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        width: parent.width - 40
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                ListView {
                    id: volumeList
                    anchors.fill: parent
                    clip: true
                    model: backend.volumes
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}
                    delegate: MouseArea {
                        id: volumeRow
                        required property var modelData
                        required property int index
                        width: volumeList.width
                        height: Theme.rowHeight
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onPressed: mouse => {
                            window.select(modelData);
                            if (mouse.button === Qt.RightButton) {
                                const p = mapToItem(null, mouse.x, mouse.y);
                                window.showMenu(modelData, p.x, p.y);
                            }
                        }
                        onDoubleClicked: if (modelData.canOpen) backend.act("open", modelData.object, {})
                        Rectangle {
                            anchors.fill: parent
                            color: window.selectedKey === volumeRow.modelData.object ? Theme.rowSelected
                                 : (volumeRow.containsMouse ? Theme.rowHover : "transparent")
                        }
                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            Repeater {
                                model: table.columns
                                delegate: Item {
                                    required property var modelData
                                    required property int index
                                    width: table.widthOf(index)
                                    height: Theme.rowHeight
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.rightMargin: 12
                                        spacing: 8
                                        Kirigami.Icon {
                                            visible: index === 0
                                            implicitWidth: 16
                                            implicitHeight: 16
                                            source: volumeRow.modelData.diskKind === "cdrom" ? "media-optical"
                                                  : (volumeRow.modelData.removable ? "drive-removable-media" : "drive-harddisk")
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            horizontalAlignment: modelData[3] ? Text.AlignRight : Text.AlignLeft
                                            text: volumeRow.modelData[modelData[0]] || ""
                                            color: Theme.text
                                            font.pixelSize: Theme.bodySize
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                }
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.cardBorder }

        // --- The disk map ---------------------------------------------------
        // A plain Flickable: a ScrollView's padding for its scroll bar made
        // a binding loop with the content's width (VM, 2026-10-22).
        Flickable {
            id: diskScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: diskColumn.height
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}

            Column {
                id: diskColumn
                width: diskScroll.width
                spacing: 8
                topPadding: 12
                bottomPadding: 12
                leftPadding: 12
                rightPadding: 12

                Repeater {
                    model: backend.disks
                    delegate: DiskRow {
                        required property var modelData
                        required property int index
                        disk: modelData
                        width: diskColumn.width - diskColumn.leftPadding - diskColumn.rightPadding
                    }
                }
            }
        }
    }

    // One disk of the map: the header box on the left, the segments to scale.
    component DiskRow: Item {
        id: diskRow
        property var disk: null
        readonly property int headerWidth: Math.round(150 * Theme.textScale)
        readonly property int segmentMin: Math.round(84 * Theme.textScale)
        height: Math.round(92 * Theme.textScale)

        // Widths to scale, each at least segmentMin (taken from the wide ones).
        function widths() {
            const segments = disk ? disk.segments : [];
            const total = width - headerWidth - 4;
            if (segments.length === 0)
                return [];
            const size = segments.reduce((sum, s) => sum + s.size, 0) || 1;
            let result = segments.map(s => Math.max(segmentMin, Math.floor(total * s.size / size)));
            let excess = result.reduce((sum, w) => sum + w, 0) - total;
            if (excess > 0) {
                const big = result.map((w, i) => w > segmentMin ? i : -1).filter(i => i >= 0);
                const bigTotal = big.reduce((sum, i) => sum + result[i] - segmentMin, 0);
                if (bigTotal > 0) {
                    for (const i of big)
                        result[i] = Math.max(segmentMin, result[i] - Math.round(excess * (result[i] - segmentMin) / bigTotal));
                }
            }
            return result;
        }
        readonly property var segmentWidths: widths()

        MouseArea {
            id: header
            width: diskRow.headerWidth
            height: parent.height
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            readonly property var item: Object.assign({isDisk: true}, diskRow.disk)
            onPressed: mouse => {
                window.select(item);
                if (mouse.button === Qt.RightButton) {
                    const p = mapToItem(null, mouse.x, mouse.y);
                    window.showMenu(item, p.x, p.y);
                }
            }
            Rectangle {
                anchors.fill: parent
                radius: 4
                color: window.selectedKey === "disk:" + diskRow.disk.object ? Theme.rowSelected
                     : (header.containsMouse ? Theme.rowHover : Theme.card)
                border.width: 1
                border.color: Theme.cardBorder
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 2
                RowLayout {
                    spacing: 8
                    Kirigami.Icon {
                        implicitWidth: 18
                        implicitHeight: 18
                        source: diskRow.disk.kind === "cdrom" ? "media-optical"
                              : (diskRow.disk.removable ? "drive-removable-media" : "drive-harddisk")
                    }
                    Text {
                        text: diskRow.disk.title
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        font.weight: Font.DemiBold
                    }
                }
                Text { text: diskRow.disk.kindText; color: Theme.text; font.pixelSize: Theme.smallSize }
                Text { text: diskRow.disk.sizeText; color: Theme.text; font.pixelSize: Theme.smallSize }
                Text { text: diskRow.disk.statusText; color: Theme.subtext; font.pixelSize: Theme.smallSize }
                Item { Layout.fillHeight: true }
            }
        }

        Row {
            anchors.left: header.right
            anchors.leftMargin: 4
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            spacing: 0
            Repeater {
                model: diskRow.disk ? diskRow.disk.segments : []
                delegate: MouseArea {
                    id: segment
                    required property var modelData
                    required property int index
                    readonly property bool volume: modelData.kind === "volume"
                    readonly property bool selected: window.selectedKey === window.keyOf(modelData)
                    readonly property color stripe: modelData.kind === "unallocated" ? Theme.unallocated
                                                  : modelData.kind === "free" ? Theme.freeSpace
                                                  : modelData.role === "logical" ? Theme.logical : Theme.primary
                    width: diskRow.segmentWidths[index] || diskRow.segmentMin
                    height: diskRow.height
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onPressed: mouse => {
                        window.select(modelData);
                        if (mouse.button === Qt.RightButton) {
                            const p = mapToItem(null, mouse.x, mouse.y);
                            window.showMenu(modelData, p.x, p.y);
                        }
                    }
                    onDoubleClicked: if (volume && modelData.canOpen) backend.act("open", modelData.object, {})

                    Rectangle {
                        anchors.fill: parent
                        anchors.rightMargin: 2
                        color: segment.volume || segment.modelData.kind === "free" ? Theme.segmentBody : Theme.unallocated
                        border.width: segment.selected ? 2 : 1
                        border.color: segment.selected ? Theme.accent : Theme.cardBorder
                        // The coloured stripe of Disk Management over every volume.
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: segment.selected ? 2 : 1
                            height: 9
                            color: segment.stripe
                        }
                        // Unallocated space is hatched, as in Windows.
                        Canvas {
                            anchors.fill: parent
                            anchors.margins: 1
                            visible: segment.modelData.kind === "unallocated" || segment.selected
                            opacity: segment.modelData.kind === "unallocated" ? 1 : 0.18
                            onPaint: {
                                const ctx = getContext("2d");
                                ctx.clearRect(0, 0, width, height);
                                ctx.strokeStyle = segment.modelData.kind === "unallocated" ? "#5A5A5A" : Theme.accent;
                                ctx.lineWidth = 1;
                                for (let x = -height; x < width; x += 8) {
                                    ctx.beginPath();
                                    ctx.moveTo(x, height);
                                    ctx.lineTo(x + height, 0);
                                    ctx.stroke();
                                }
                            }
                            onWidthChanged: requestPaint()
                            onHeightChanged: requestPaint()
                            onVisibleChanged: requestPaint()
                        }
                        Rectangle {
                            anchors.fill: parent
                            color: Theme.text
                            opacity: segment.containsMouse ? 0.05 : 0
                        }
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            anchors.topMargin: 16
                            spacing: 1
                            Text {
                                Layout.fillWidth: true
                                text: segment.modelData.title || ""
                                color: segment.volume || segment.modelData.kind === "free" ? Theme.text : "#F2F2F2"
                                font.pixelSize: Theme.smallSize
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: segment.modelData.sizeText + (segment.modelData.fsText ? " " + segment.modelData.fsText : "")
                                color: segment.volume || segment.modelData.kind === "free" ? Theme.text : "#F2F2F2"
                                font.pixelSize: Theme.smallSize
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: text !== ""
                                text: segment.volume ? segment.modelData.statusText
                                    : (segment.modelData.kind === "unallocated" ? backend.texts.unallocated : "")
                                color: segment.volume ? Theme.subtext : "#F2F2F2"
                                font.pixelSize: Theme.smallSize
                                elide: Text.ElideRight
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }
            }
        }
    }
}
