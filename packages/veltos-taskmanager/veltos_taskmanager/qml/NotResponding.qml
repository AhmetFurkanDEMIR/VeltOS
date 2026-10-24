// Windows 11's "is not responding" window: the program's icon and name,
// what closing means, and "Close the program" / "Wait for the program to
// respond" in the button bar at the bottom. Esc waits.
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami
import "."

Window {
    id: win

    readonly property int contentWidth: Math.round(480 * Theme.textScale)
    title: backend.appName
    flags: Qt.Dialog
    color: Theme.card
    // A fixed size: the window cannot be resized or maximised.
    readonly property int contentHeight: column.implicitHeight + bar.height
    width: contentWidth
    height: contentHeight
    minimumWidth: contentWidth
    maximumWidth: contentWidth
    minimumHeight: contentHeight
    maximumHeight: contentHeight
    visible: true

    component DialogButton: Rectangle {
        id: button
        property string label
        property bool primary: false
        signal activated()
        implicitHeight: Math.max(Math.round(32 * Theme.textScale), caption.implicitHeight + 12)
        radius: 4
        color: primary ? (tap.pressed ? Qt.darker(Theme.accent, 1.15) : hover.hovered ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                       : (tap.pressed ? Theme.rowSelected : hover.hovered ? Theme.rowHover : Theme.control)
        border.width: primary ? 0 : 1
        border.color: Theme.cardBorder
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: label
        Keys.onReturnPressed: activated()
        Keys.onEnterPressed: activated()
        Keys.onSpacePressed: activated()
        Text {
            id: caption
            anchors.centerIn: parent
            width: parent.width - 16
            text: button.label
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.bodySize + 1
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 6
            color: "transparent"
            border.width: 2
            border.color: Theme.text
            // The accent marks the default button; the ring shows where Tab went.
            visible: button.activeFocus && !button.primary
        }
        HoverHandler { id: hover }
        TapHandler { id: tap; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: button.activated() }
    }

    Item {
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: backend.wait()

        ColumnLayout {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: Math.round(24 * Theme.textScale)
                Layout.bottomMargin: Math.round(28 * Theme.textScale)
                spacing: Math.round(16 * Theme.textScale)

                Item {
                    Layout.alignment: Qt.AlignTop
                    Layout.preferredWidth: Math.round(40 * Theme.textScale)
                    Layout.preferredHeight: Math.round(40 * Theme.textScale)
                    Kirigami.Icon {
                        anchors.fill: parent
                        source: backend.appIcon
                    }
                    // Windows marks the frozen program with a warning badge.
                    Kirigami.Icon {
                        width: parent.width * 0.5
                        height: width
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: -width * 0.15
                        source: "emblem-warning"
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Math.round(10 * Theme.textScale)
                    Text {
                        objectName: "heading"
                        Layout.fillWidth: true
                        text: backend.heading
                        color: Theme.text
                        font.pixelSize: Math.round(20 * Theme.textScale)
                        font.weight: Font.DemiBold
                        wrapMode: Text.Wrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: backend.text("nr_body")
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize + 1
                        lineHeight: 1.15
                        wrapMode: Text.Wrap
                    }
                }
            }
        }

        // Windows 11 dialogs keep their buttons in a grey bar at the bottom.
        Rectangle {
            id: bar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: buttons.implicitHeight + Math.round(48 * Theme.textScale)
            color: Theme.window
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                height: 1
                color: Theme.cardBorder
            }
            // Equal buttons across the bar, as Windows 11's dialogs have.
            RowLayout {
                id: buttons
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: Math.round(24 * Theme.textScale)
                anchors.rightMargin: Math.round(24 * Theme.textScale)
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                uniformCellSizes: true
                DialogButton {
                    id: closeButton
                    objectName: "closeButton"
                    Layout.fillWidth: true
                    primary: true
                    label: backend.text("nr_close")
                    focus: true
                    onActivated: backend.closeProgram()
                }
                DialogButton {
                    objectName: "waitButton"
                    Layout.fillWidth: true
                    label: backend.text("nr_wait")
                    onActivated: backend.wait()
                }
            }
        }
    }

    onClosing: backend.wait()
    Component.onCompleted: closeButton.forceActiveFocus()
}
