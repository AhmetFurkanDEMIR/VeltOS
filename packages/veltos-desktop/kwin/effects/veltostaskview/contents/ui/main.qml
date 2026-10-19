/*
    VeltOS Task View: Windows 11's Task View as a KWin scene effect.

    The desktop dims behind an acrylic-like layer; the windows of the
    current desktop appear as large thumbnails with their icon and title,
    a close button on hover; the virtual desktops are cards at the bottom
    with "New desktop". Click a window to switch to it, a desktop to show
    its windows; Esc or a click on the background closes the view.
    Meta+Tab (Windows key + Tab) and the taskbar's Task View button open it.

    Uses KWin's public QML API (org.kde.kwin) only.
    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Layouts
import QtQml.Models
import org.kde.kwin as KWin
import org.kde.kirigami as Kirigami

KWin.SceneEffect {
    id: effect

    readonly property bool turkish: Qt.locale().name.startsWith("tr")
    function tr(en, trText) {
        return turkish ? trText : en;
    }
    function close() {
        visible = false;
    }

    KWin.ShortcutHandler {
        name: "VeltOS Task View"
        text: effect.tr("Task View", "Görev Görünümü")
        sequence: "Meta+Tab"
        onActivated: effect.visible = !effect.visible
    }

    delegate: FocusScope {
        id: view

        readonly property QtObject screen: KWin.SceneView.screen
        readonly property int stripHeight: Math.round(Kirigami.Units.gridUnit * 9)
        focus: true
        opacity: 0
        scale: 0.97
        Component.onCompleted: {
            forceActiveFocus();
            opacity = 1;
            scale = 1;
        }
        Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
        Keys.onEscapePressed: effect.close()

        KWin.DesktopBackground {
            anchors.fill: parent
            activity: KWin.Workspace.currentActivity
            desktop: KWin.Workspace.currentDesktop
            outputName: view.screen.name
        }
        Rectangle {
            anchors.fill: parent
            color: "#1c1c1c"
            opacity: 0.72
        }
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: effect.close()
        }

        KWin.WindowModel {
            id: allWindows
        }

        KWin.WindowFilterModel {
            id: windows
            activity: KWin.Workspace.currentActivity
            desktop: KWin.Workspace.currentDesktop
            screenName: view.screen.name
            windowModel: allWindows
            minimizedWindows: true
            windowType: ~KWin.WindowFilterModel.Dock
                        & ~KWin.WindowFilterModel.Desktop
                        & ~KWin.WindowFilterModel.Notification
                        & ~KWin.WindowFilterModel.CriticalNotification
        }

        // Windows that also appear in Alt+Tab (helper windows such as
        // screen-recording bridges are left out).
        DelegateModel {
            id: shown
            model: windows
            groups: [
                DelegateModelGroup {
                    name: "switchable"
                }
            ]
            filterOnGroup: "switchable"
            delegate: windowDelegate
            function refresh() {
                for (let i = 0; i < items.count; ++i) {
                    const item = items.get(i);
                    item.inSwitchable = !item.model.window.skipSwitcher;
                }
            }
            items.onChanged: refresh()
            Component.onCompleted: refresh()
        }

        // --- Windows -------------------------------------------------------

        Item {
            id: area
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                bottom: strip.top
                margins: Kirigami.Units.gridUnit * 3
                bottomMargin: Kirigami.Units.gridUnit
            }

            readonly property int count: shown.count
            readonly property int titleHeight: Math.round(Kirigami.Units.gridUnit * 2)
            // Columns that give the largest thumbnails for 16:10 windows.
            readonly property int columns: {
                let best = 1, bestSize = 0;
                for (let c = 1; c <= Math.max(1, count); ++c) {
                    const rows = Math.ceil(count / c);
                    const size = Math.min(width / c, (height / rows - titleHeight) * 1.6);
                    if (size > bestSize) {
                        bestSize = size;
                        best = c;
                    }
                }
                return best;
            }
            readonly property int rows: Math.max(1, Math.ceil(count / columns))
            readonly property real cellWidth: Math.min(width / columns, Kirigami.Units.gridUnit * 38)
            readonly property real cellHeight: Math.min(height / rows, cellWidth / 1.6 + titleHeight)

            Text {
                anchors.centerIn: parent
                visible: area.count === 0
                text: effect.tr("No open windows", "Açık pencere yok")
                color: "white"
                opacity: 0.8
                font.pixelSize: 18
            }

            Repeater {
                id: repeater
                model: shown
            }

            Component {
                id: windowDelegate
                MouseArea {
                    id: cell
                    required property QtObject window
                    // Position among the windows that are shown.
                    readonly property int slot: DelegateModel.switchableIndex

                    readonly property int row: Math.floor(slot / area.columns)
                    readonly property int inRow: row === area.rows - 1
                                                 ? area.count - row * area.columns : area.columns
                    readonly property real aspect: window.width / Math.max(1, window.height)
                    readonly property real maxThumbWidth: area.cellWidth - Kirigami.Units.gridUnit
                    readonly property real maxThumbHeight: area.cellHeight - area.titleHeight - Kirigami.Units.gridUnit
                    readonly property real thumbWidth: Math.min(maxThumbWidth, maxThumbHeight * aspect)
                    readonly property real thumbHeight: thumbWidth / aspect

                    width: thumbWidth + Kirigami.Units.smallSpacing * 2
                    height: thumbHeight + area.titleHeight + Kirigami.Units.smallSpacing
                    // Rows are centred, the whole grid too.
                    x: (area.width - inRow * area.cellWidth) / 2 + (slot - row * area.columns) * area.cellWidth
                       + (area.cellWidth - width) / 2
                    y: (area.height - area.rows * area.cellHeight) / 2 + row * area.cellHeight
                       + (area.cellHeight - height) / 2

                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                    onClicked: mouse => {
                        if (mouse.button === Qt.MiddleButton) {
                            window.closeWindow();
                        } else {
                            KWin.Workspace.activeWindow = window;
                            effect.close();
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 8
                        color: "white"
                        opacity: cell.pressed ? 0.06 : (cell.containsMouse ? 0.12 : 0)
                        border.width: cell.containsMouse ? 2 : 0
                        border.color: Qt.rgba(1, 1, 1, 0.5)
                    }

                    RowLayout {
                        id: title
                        anchors {
                            left: parent.left
                            right: parent.right
                            top: parent.top
                            leftMargin: Kirigami.Units.smallSpacing * 2
                            rightMargin: Kirigami.Units.smallSpacing
                        }
                        height: area.titleHeight
                        spacing: Kirigami.Units.smallSpacing * 2
                        Kirigami.Icon {
                            implicitWidth: Kirigami.Units.iconSizes.small
                            implicitHeight: implicitWidth
                            source: cell.window.icon
                        }
                        Text {
                            Layout.fillWidth: true
                            text: cell.window.caption
                            color: "white"
                            elide: Text.ElideRight
                            font.pixelSize: 13
                        }
                        // Close button like a Windows 11 caption button.
                        MouseArea {
                            id: closeButton
                            visible: cell.containsMouse
                            implicitWidth: area.titleHeight
                            implicitHeight: area.titleHeight - Kirigami.Units.smallSpacing
                            hoverEnabled: true
                            onClicked: cell.window.closeWindow()
                            Rectangle {
                                anchors.fill: parent
                                radius: 4
                                color: "#c42b1c"
                                visible: closeButton.containsMouse
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✕"
                                color: "white"
                                font.pixelSize: 12
                            }
                        }
                    }

                    KWin.WindowThumbnail {
                        anchors.top: title.bottom
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: cell.thumbWidth
                        height: cell.thumbHeight
                        wId: cell.window.internalId
                    }
                }
            }
        }

        // --- Desktops ------------------------------------------------------

        Item {
            id: strip
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: view.stripHeight

            Rectangle {
                anchors.centerIn: desktops
                width: desktops.width + Kirigami.Units.gridUnit * 2
                height: desktops.height + Kirigami.Units.gridUnit
                radius: 8
                color: "white"
                opacity: 0.08
            }

            Row {
                id: desktops
                anchors.centerIn: parent
                spacing: Kirigami.Units.gridUnit

                Repeater {
                    model: KWin.Workspace.desktops

                    delegate: MouseArea {
                        id: card
                        required property int index
                        required property QtObject modelData
                        readonly property bool current: modelData === KWin.Workspace.currentDesktop
                        width: Math.round(Kirigami.Units.gridUnit * 9)
                        height: Math.round(width * view.height / view.width) + Kirigami.Units.gridUnit * 1.6
                        hoverEnabled: true
                        onClicked: KWin.Workspace.currentDesktop = modelData

                        Rectangle {
                            id: frame
                            width: parent.width
                            height: parent.width * view.height / view.width
                            radius: 6
                            color: "transparent"
                            border.width: card.current ? 2 : (card.containsMouse ? 1 : 0)
                            border.color: card.current ? Kirigami.Theme.highlightColor : Qt.rgba(1, 1, 1, 0.6)
                            clip: true

                            KWin.DesktopBackground {
                                anchors.fill: parent
                                anchors.margins: frame.border.width
                                activity: KWin.Workspace.currentActivity
                                desktop: card.modelData
                                outputName: view.screen.name
                            }
                        }
                        Text {
                            anchors.top: frame.bottom
                            anchors.topMargin: Kirigami.Units.smallSpacing
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: parent.width
                            horizontalAlignment: Text.AlignHCenter
                            text: card.modelData.name
                            color: "white"
                            elide: Text.ElideRight
                            font.pixelSize: 12
                        }
                        // Remove (only when there is more than one desktop).
                        MouseArea {
                            visible: card.containsMouse && KWin.Workspace.desktops.length > 1
                            anchors.right: frame.right
                            anchors.top: frame.top
                            width: Kirigami.Units.gridUnit * 1.4
                            height: width
                            onClicked: KWin.Workspace.removeDesktop(card.modelData)
                            Rectangle {
                                anchors.fill: parent
                                radius: 4
                                color: "#c42b1c"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✕"
                                color: "white"
                                font.pixelSize: 10
                            }
                        }
                    }
                }

                // "New desktop", like Windows 11.
                MouseArea {
                    id: addDesktop
                    width: Math.round(Kirigami.Units.gridUnit * 9)
                    height: Math.round(width * view.height / view.width) + Kirigami.Units.gridUnit * 1.6
                    hoverEnabled: true
                    onClicked: KWin.Workspace.createDesktop(KWin.Workspace.desktops.length,
                        effect.tr("Desktop %1", "Masaüstü %1").arg(KWin.Workspace.desktops.length + 1))

                    Rectangle {
                        id: addFrame
                        width: parent.width
                        height: parent.width * view.height / view.width
                        radius: 6
                        color: "white"
                        opacity: addDesktop.containsMouse ? 0.16 : 0.08
                    }
                    Text {
                        anchors.centerIn: addFrame
                        text: "+"
                        color: "white"
                        font.pixelSize: 28
                    }
                    Text {
                        anchors.top: addFrame.bottom
                        anchors.topMargin: Kirigami.Units.smallSpacing
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: effect.tr("New desktop", "Yeni masaüstü")
                        color: "white"
                        font.pixelSize: 12
                    }
                }
            }
        }
    }
}
