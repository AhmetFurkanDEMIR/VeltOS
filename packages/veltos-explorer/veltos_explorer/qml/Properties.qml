/*
    Windows 11's Properties window for files, folders, several items,
    drives and Recycle Bin items: General (icon and name, type, "Opens
    with" and Change..., location, size, size on disk, contents, dates,
    Read-only and Hidden; a used / free pie for drives), Security (owner,
    group, permissions) and Details, with OK, Cancel and Apply.
    `properties` is properties.Properties.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    readonly property var info: properties.info
    readonly property string kind: info.kind
    property int tab: 0
    // What the user changed and has not applied yet.
    property string editedName: info.name
    property bool editedReadOnly: info.readOnly
    property bool editedHidden: info.hidden
    property int editedMode: info.mode
    readonly property bool dirty: (kind !== "multiple" && editedName !== info.name) || editedReadOnly !== info.readOnly
                                  || editedHidden !== info.hidden || editedMode !== info.mode
    readonly property int labelWidth: 112

    // A fixed size like Windows' Properties (KWin then offers no maximize).
    width: 480
    height: 580
    minimumWidth: 480
    maximumWidth: 480
    minimumHeight: 580
    maximumHeight: 580
    visible: true
    title: properties.title
    color: Theme.pane
    flags: Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    function apply() {
        if (!dirty)
            return true;
        if (!properties.apply(editedName, editedReadOnly, editedHidden, editedMode))
            return false;
        editedName = Qt.binding(() => info.name);
        editedReadOnly = Qt.binding(() => info.readOnly);
        editedHidden = Qt.binding(() => info.hidden);
        editedMode = Qt.binding(() => info.mode);
        return true;
    }

    Shortcut { sequence: "Escape"; onActivated: properties.close() }
    Connections {
        target: properties
        function onMessage(text) {
            messageBox.text = text;
            messageBox.open();
        }
    }
    onClosing: properties.stop()

    component DialogButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        implicitWidth: Math.max(88, buttonText.implicitWidth + 32)
        implicitHeight: 32
        radius: 5
        opacity: enabledState ? 1 : 0.5
        color: primary ? (buttonHover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                       : (buttonHover.hovered ? Theme.hover : Theme.field)
        border.width: primary ? 0 : 1
        border.color: Theme.fieldBorder
        activeFocusOnTab: enabledState
        Accessible.role: Accessible.Button
        Accessible.name: label
        Keys.onReturnPressed: if (enabledState) clicked()
        Keys.onSpacePressed: if (enabledState) clicked()
        Text {
            id: buttonText
            anchors.centerIn: parent
            text: button.label
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.fontSize
        }
        HoverHandler { id: buttonHover; enabled: button.enabledState }
        TapHandler { enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    // A label and its value, as Windows lines them up.
    component Fact: RowLayout {
        property string label
        property string value
        visible: value !== ""
        Layout.fillWidth: true
        spacing: 12
        Text {
            Layout.preferredWidth: window.labelWidth
            Layout.alignment: Qt.AlignTop
            text: parent.label
            color: Theme.subtext
            font.pixelSize: Theme.fontSize
        }
        TextEdit {
            Layout.fillWidth: true
            text: parent.value
            color: Theme.text
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WrapAnywhere
            readOnly: true
            selectByMouse: true
            selectedTextColor: "#FFFFFF"
            selectionColor: Theme.accent
            activeFocusOnTab: false
        }
    }

    component Line: Rectangle {
        Layout.fillWidth: true
        Layout.topMargin: 6
        Layout.bottomMargin: 6
        implicitHeight: 1
        color: Theme.separator
    }

    component Check: Rectangle {
        id: check
        property string label
        property bool checked: false
        property bool enabledState: true
        signal toggled(bool on)
        implicitWidth: row.implicitWidth
        implicitHeight: 28
        color: "transparent"
        opacity: enabledState ? 1 : 0.5
        activeFocusOnTab: enabledState
        Accessible.role: Accessible.CheckBox
        Accessible.name: label
        Accessible.checked: checked
        Keys.onSpacePressed: if (enabledState) toggled(!checked)
        RowLayout {
            id: row
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            Rectangle {
                implicitWidth: 18
                implicitHeight: 18
                radius: 4
                color: check.checked ? Theme.accent : Theme.field
                border.width: check.checked ? 0 : 1
                border.color: check.activeFocus ? Theme.accent : Theme.fieldBorder
                Text {
                    anchors.centerIn: parent
                    visible: check.checked
                    text: "✓"
                    color: "#FFFFFF"
                    font.pixelSize: 13
                }
            }
            Text {
                text: check.label
                color: Theme.text
                font.pixelSize: Theme.fontSize
            }
        }
        TapHandler { enabled: check.enabledState; onTapped: check.toggled(!check.checked) }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Tabs, as WinUI draws them: the chosen one underlined in the accent.
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.topMargin: 10
            spacing: 4
            Repeater {
                model: [properties.tr("general"), properties.tr("security"), properties.tr("details")]
                delegate: Rectangle {
                    id: tabButton
                    required property string modelData
                    required property int index
                    readonly property bool current: window.tab === index
                    implicitWidth: tabLabel.implicitWidth + 24
                    implicitHeight: 36
                    radius: 5
                    color: tabHover.hovered && !current ? Theme.hover : "transparent"
                    activeFocusOnTab: true
                    Accessible.role: Accessible.PageTab
                    Accessible.name: modelData
                    Keys.onSpacePressed: window.tab = index
                    Text {
                        id: tabLabel
                        anchors.centerIn: parent
                        text: tabButton.modelData
                        color: tabButton.current ? Theme.text : Theme.subtext
                        font.pixelSize: Theme.fontSize
                        font.weight: tabButton.current ? Font.DemiBold : Font.Normal
                    }
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        width: tabButton.current ? 16 : 0
                        height: 3
                        radius: 1.5
                        color: Theme.accent
                        Behavior on width { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                    }
                    HoverHandler { id: tabHover }
                    TapHandler { onTapped: window.tab = tabButton.index }
                }
            }
        }

        // The page, on a card as in Windows 11 Settings-style dialogs.
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 12
            radius: 8
            color: Theme.content
            border.width: 1
            border.color: Theme.separator

            Flickable {
                anchors.fill: parent
                anchors.margins: 16
                clip: true
                contentHeight: [page, securityPage, detailsPage][window.tab].implicitHeight
                boundsBehavior: Flickable.StopAtBounds

                // --- General --------------------------------------------------------
                ColumnLayout {
                    id: page
                    width: parent.width
                    spacing: 6
                    visible: window.tab === 0

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14
                        Kirigami.Icon {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            source: window.info.icon
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 32
                            radius: 5
                            color: window.info.canRename ? Theme.field : "transparent"
                            border.width: window.info.canRename ? 1 : 0
                            border.color: nameInput.activeFocus ? Theme.accent : Theme.fieldBorder
                            TextInput {
                                id: nameInput
                                anchors.fill: parent
                                anchors.leftMargin: window.info.canRename ? 10 : 0
                                anchors.rightMargin: 10
                                verticalAlignment: TextInput.AlignVCenter
                                text: window.editedName
                                readOnly: !window.info.canRename
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                                selectByMouse: true
                                selectionColor: Theme.accent
                                selectedTextColor: "#FFFFFF"
                                clip: true
                                activeFocusOnTab: window.info.canRename
                                onTextEdited: window.editedName = text
                                Accessible.name: properties.tr("name")
                                HoverHandler { cursorShape: window.info.canRename ? Qt.IBeamCursor : Qt.ArrowCursor }
                            }
                        }
                    }
                    Line {}
                    Fact { label: properties.tr(window.kind === "file" ? "type_of_file" : "prop_type"); value: window.info.typeName }
                    RowLayout {
                        visible: window.kind === "file"
                        Layout.fillWidth: true
                        spacing: 12
                        Text {
                            Layout.preferredWidth: window.labelWidth
                            text: properties.tr("opens_with")
                            color: Theme.subtext
                            font.pixelSize: Theme.fontSize
                        }
                        Kirigami.Icon {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            visible: !!window.info.opensWith
                            source: window.info.opensWith ? window.info.opensWith.icon : ""
                        }
                        Text {
                            Layout.fillWidth: true
                            text: window.info.opensWith ? window.info.opensWith.name : properties.tr("no_app")
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            elide: Text.ElideRight
                        }
                        DialogButton {
                            label: properties.tr("change")
                            implicitWidth: 88
                            onClicked: properties.changeApp()
                        }
                    }
                    Line { visible: window.kind !== "drive" }
                    Fact { label: properties.tr("prop_location"); value: window.kind === "drive" ? "" : window.info.location }
                    Fact { label: properties.tr("prop_original"); value: window.info.original }
                    Fact { label: properties.tr("prop_deleted"); value: window.info.deleted }
                    Fact {
                        label: properties.tr("prop_size")
                        value: window.kind === "drive" ? "" : properties.sizeText + (properties.counting ? " …" : "")
                    }
                    Fact {
                        label: properties.tr("size_on_disk")
                        value: window.kind === "drive" ? "" : properties.sizeOnDiskText
                    }
                    Fact {
                        label: properties.tr("contains")
                        value: window.kind === "folder" || window.kind === "multiple" ? properties.containsText : ""
                    }

                    // A drive: file system, used / free / capacity and the pie.
                    Fact { label: properties.tr("file_system"); value: window.kind === "drive" ? window.info.fileSystem : "" }
                    ColumnLayout {
                        visible: window.kind === "drive"
                        Layout.fillWidth: true
                        spacing: 6
                        Line {}
                        Repeater {
                            model: [
                                { label: properties.tr("used_space"), value: properties.drive.used, swatch: Theme.accent },
                                { label: properties.tr("free_space"), value: properties.drive.free, swatch: Theme.separator }
                            ]
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 12
                                Rectangle {
                                    implicitWidth: 12
                                    implicitHeight: 12
                                    radius: 3
                                    color: modelData.swatch
                                }
                                Text {
                                    Layout.preferredWidth: window.labelWidth - 24
                                    text: modelData.label
                                    color: Theme.subtext
                                    font.pixelSize: Theme.fontSize
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.value
                                    color: Theme.text
                                    font.pixelSize: Theme.fontSize
                                    elide: Text.ElideRight
                                }
                            }
                        }
                        Line {}
                        Fact { label: properties.tr("capacity"); value: properties.drive.capacity }
                        // Used and free as a ring, as Windows draws the drive.
                        Item {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.topMargin: 8
                            implicitWidth: 120
                            implicitHeight: 120
                            Shape {
                                anchors.fill: parent
                                preferredRendererType: Shape.CurveRenderer
                                ShapePath {
                                    strokeColor: Theme.separator
                                    strokeWidth: 18
                                    fillColor: "transparent"
                                    PathAngleArc { centerX: 60; centerY: 60; radiusX: 50; radiusY: 50; startAngle: 0; sweepAngle: 360 }
                                }
                                ShapePath {
                                    strokeColor: Theme.accent
                                    strokeWidth: 18
                                    fillColor: "transparent"
                                    capStyle: ShapePath.FlatCap
                                    PathAngleArc {
                                        centerX: 60; centerY: 60; radiusX: 50; radiusY: 50
                                        startAngle: -90
                                        sweepAngle: 360 * Math.max(0, Math.min(1, properties.drive.usedFraction))
                                    }
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: Math.round(100 * properties.drive.usedFraction) + " %"
                                color: Theme.text
                                font.pixelSize: Theme.fontSize
                                font.weight: Font.DemiBold
                            }
                        }
                    }

                    Line { visible: window.kind === "file" || window.kind === "folder" }
                    Fact { label: properties.tr("created"); value: window.kind === "multiple" ? "" : window.info.created }
                    Fact { label: properties.tr("modified"); value: window.kind === "multiple" ? "" : window.info.modified }
                    Fact { label: properties.tr("accessed"); value: window.kind === "file" ? window.info.accessed : "" }
                    Line { visible: attributes.visible }
                    RowLayout {
                        id: attributes
                        visible: window.kind === "file" || window.kind === "folder" || window.kind === "multiple"
                        Layout.fillWidth: true
                        spacing: 12
                        Text {
                            Layout.preferredWidth: window.labelWidth
                            text: properties.tr("attributes")
                            color: Theme.subtext
                            font.pixelSize: Theme.fontSize
                        }
                        Check {
                            label: properties.tr("read_only")
                            checked: window.editedReadOnly
                            enabledState: window.info.canChangeMode
                            onToggled: on => window.editedReadOnly = on
                        }
                        Check {
                            label: properties.tr("hidden")
                            checked: window.editedHidden
                            enabledState: window.info.canRename || window.kind === "multiple"
                            onToggled: on => window.editedHidden = on
                        }
                    }
                }

                // --- Security ------------------------------------------------------
                ColumnLayout {
                    id: securityPage
                    width: parent.width
                    spacing: 6
                    visible: window.tab === 1

                    Fact { label: properties.tr("object_name"); value: window.kind === "multiple" ? "" : window.info.location + "/" + window.info.name }
                    Fact { label: properties.tr("owner"); value: window.info.owner }
                    Fact { label: properties.tr("group"); value: window.info.group }
                    Line {}
                    Text {
                        text: properties.tr("permissions")
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                        font.weight: Font.DemiBold
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 4
                        columnSpacing: 12
                        rowSpacing: 4
                        Item { Layout.preferredWidth: window.labelWidth - 20; implicitHeight: 1 }
                        Repeater {
                            model: [properties.tr("perm_read"), properties.tr("perm_write"), properties.tr("perm_run")]
                            delegate: Text {
                                required property string modelData
                                text: modelData
                                color: Theme.subtext
                                font.pixelSize: Theme.smallFont
                            }
                        }
                        Repeater {
                            model: [
                                { label: properties.tr("perm_owner"), shift: 6 },
                                { label: properties.tr("perm_group"), shift: 3 },
                                { label: properties.tr("perm_everyone"), shift: 0 }
                            ]
                            delegate: Item {
                                id: permRow
                                required property var modelData
                                Layout.columnSpan: 4
                                Layout.fillWidth: true
                                implicitHeight: 30
                                RowLayout {
                                    anchors.fill: parent
                                    spacing: 12
                                    Text {
                                        Layout.preferredWidth: window.labelWidth - 20
                                        text: permRow.modelData.label
                                        color: Theme.text
                                        font.pixelSize: Theme.fontSize
                                    }
                                    Repeater {
                                        model: [4, 2, 1]
                                        delegate: Check {
                                            required property int modelData
                                            readonly property int bit: modelData << permRow.modelData.shift
                                            Layout.preferredWidth: 60
                                            label: ""
                                            checked: (window.editedMode & bit) !== 0
                                            enabledState: window.info.canChangeMode && window.kind !== "multiple"
                                            onToggled: on => window.editedMode = on ? (window.editedMode | bit) : (window.editedMode & ~bit)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        Layout.topMargin: 8
                        visible: !window.info.canChangeMode
                        text: properties.tr("only_owner_changes")
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont
                        wrapMode: Text.WordWrap
                    }
                }

                // --- Details -------------------------------------------------------
                ColumnLayout {
                    id: detailsPage
                    width: parent.width
                    spacing: 2
                    visible: window.tab === 2
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.bottomMargin: 6
                        Text {
                            Layout.preferredWidth: window.labelWidth
                            text: properties.tr("property")
                            color: Theme.subtext
                            font.pixelSize: Theme.smallFont
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: properties.tr("value")
                            color: Theme.subtext
                            font.pixelSize: Theme.smallFont
                            font.weight: Font.DemiBold
                        }
                    }
                    Repeater {
                        model: window.info.details
                        delegate: Fact {
                            required property var modelData
                            label: modelData.label
                            value: modelData.value
                        }
                    }
                }
            }
        }

        // OK, Cancel, Apply.
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 12
            spacing: 8
            Item { Layout.fillWidth: true }
            DialogButton {
                label: properties.tr("ok")
                primary: true
                onClicked: {
                    if (window.apply())
                        properties.close();
                }
            }
            DialogButton {
                label: properties.tr("cancel")
                onClicked: properties.close()
            }
            DialogButton {
                label: properties.tr("apply")
                enabledState: window.dirty
                onClicked: window.apply()
            }
        }
    }

    Popup {
        id: messageBox
        property alias text: messageText.text
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 340
        modal: true
        padding: 20
        background: Rectangle {
            radius: 8
            color: Theme.content
            border.width: 1
            border.color: Theme.separator
        }
        contentItem: ColumnLayout {
            spacing: 16
            Text {
                id: messageText
                Layout.fillWidth: true
                color: Theme.text
                font.pixelSize: Theme.fontSize
                wrapMode: Text.WordWrap
            }
            DialogButton {
                Layout.alignment: Qt.AlignRight
                label: properties.tr("ok")
                primary: true
                onClicked: messageBox.close()
            }
        }
    }
}
