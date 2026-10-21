/*
    "Select an app to open this file", as Windows 11 asks it: the apps that
    open the file's type with their icons, "More apps", then "Always" and
    "Just once". `opener` (openwith.py) lists the apps and opens the file.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    width: 460
    height: 600
    minimumWidth: 380
    minimumHeight: 420
    visible: true
    title: opener.tr("open_with")
    color: Theme.content

    component DialogButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        Layout.fillWidth: true
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
            anchors.centerIn: parent
            text: button.label
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.fontSize
        }
        HoverHandler { id: buttonHover; enabled: button.enabledState }
        TapHandler { enabled: button.enabledState; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.clicked() }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 12

        Text {
            Layout.fillWidth: true
            text: opener.heading
            color: Theme.text
            font.pixelSize: 20
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }
        Text {
            Layout.fillWidth: true
            text: opener.fileName
            color: Theme.subtext
            font.pixelSize: Theme.smallFont
            elide: Text.ElideMiddle
        }

        Text {
            visible: opener.apps.length === 0
            Layout.fillWidth: true
            Layout.topMargin: 8
            text: opener.tr("no_apps")
            color: Theme.text
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 6
            clip: true
            model: opener.apps
            currentIndex: opener.selected
            spacing: 2
            ScrollBar.vertical: ScrollBar {}
            delegate: Rectangle {
                id: row
                required property var modelData
                required property int index
                readonly property bool chosen: index === opener.selected
                width: list.width - 12
                height: 52
                radius: 6
                color: chosen ? Theme.selected : (rowHover.hovered ? Theme.hover : "transparent")
                border.width: chosen ? 1 : 0
                border.color: Theme.selectedBorder
                Accessible.role: Accessible.ListItem
                Accessible.name: modelData.name
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 14
                    Kirigami.Icon {
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        source: row.modelData.icon || "application-x-executable"
                    }
                    Text {
                        Layout.fillWidth: true
                        text: row.modelData.name
                        color: Theme.text
                        font.pixelSize: Theme.fontSize
                        elide: Text.ElideRight
                    }
                }
                HoverHandler { id: rowHover }
                TapHandler {
                    onTapped: opener.select(row.index)
                    onDoubleTapped: opener.open(row.index, false)
                }
            }
        }

        // "More apps ↓", like Windows (the apps that do not claim the type).
        Rectangle {
            visible: opener.hasMore
            Layout.fillWidth: true
            implicitHeight: 36
            radius: 6
            color: moreHover.hovered ? Theme.hover : "transparent"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                spacing: 8
                Text {
                    text: opener.tr("more_apps")
                    color: Theme.accent
                    font.pixelSize: Theme.fontSize
                }
                Kirigami.Icon {
                    Layout.preferredWidth: 12
                    Layout.preferredHeight: 12
                    source: "arrow-down"
                    color: Theme.accent
                    isMask: true
                }
            }
            HoverHandler { id: moreHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: opener.showMore() }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 8
            DialogButton {
                objectName: "always"
                primary: true
                label: opener.tr("always")
                enabledState: opener.selected >= 0
                onClicked: opener.open(opener.selected, true)
            }
            DialogButton {
                objectName: "once"
                label: opener.tr("just_once")
                enabledState: opener.selected >= 0
                onClicked: opener.open(opener.selected, false)
            }
        }
    }

    Shortcut { sequence: "Escape"; onActivated: window.close() }
    Shortcut { sequence: "Return"; onActivated: if (opener.selected >= 0) opener.open(opener.selected, false) }
}
