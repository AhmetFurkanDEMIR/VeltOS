// A Windows 11 settings row: icon, title and description on the left and a
// control (toggle, drop-down, button, ...) on the right, or under the text
// with `wrapControl`. Clickable rows behave like SettingCard.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: row

    default property alias control: slot.data
    property string icon
    property string title
    property string description
    property bool clickable: false
    property bool wrapControl: false
    signal clicked()

    implicitHeight: Math.max(68, layout.implicitHeight + 24)
    radius: Theme.radius
    color: clickable && tap.pressed ? Theme.cardPressed : (clickable && hover.hovered ? Theme.cardHover : Theme.card)
    border.width: activeFocus ? 2 : 1
    border.color: activeFocus ? Theme.accent : Theme.cardBorder
    activeFocusOnTab: clickable
    Accessible.role: clickable ? Accessible.Button : Accessible.Grouping
    Accessible.name: title
    Accessible.description: description
    Accessible.onPressAction: if (clickable) clicked()
    Keys.onReturnPressed: if (clickable) clicked()
    Keys.onSpacePressed: if (clickable) clicked()

    Behavior on color { ColorAnimation { duration: 90 } }

    GridLayout {
        id: layout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        columns: row.wrapControl ? 2 : 3
        columnSpacing: 16
        rowSpacing: 12

        Kirigami.Icon {
            visible: row.icon !== ""
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            source: row.icon
            isMask: row.icon.endsWith("-symbolic")
            color: Theme.text
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 1
            Label {
                Layout.fillWidth: true
                text: row.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: text.length > 0
                text: row.description
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }
        RowLayout {
            id: slot
            Layout.columnSpan: row.wrapControl ? 2 : 1
            Layout.fillWidth: row.wrapControl
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            Layout.leftMargin: row.wrapControl && row.icon !== "" ? 38 : 0
            spacing: 8
        }
    }

    HoverHandler { id: hover; enabled: row.clickable; cursorShape: Qt.PointingHandCursor }
    TapHandler {
        id: tap
        enabled: row.clickable
        // A tap on the control (button, toggle, drop-down) is the control's
        // alone: TapHandlers do not take an exclusive grab, so the row's
        // handler saw those taps too and undid what the control did (the
        // "Change" password button toggled its panel open and shut again).
        onTapped: eventPoint => {
            const p = slot.mapFromItem(row, eventPoint.position.x, eventPoint.position.y);
            if (p.x >= 0 && p.y >= 0 && p.x <= slot.width && p.y <= slot.height)
                return;
            row.clicked();
        }
    }
}
