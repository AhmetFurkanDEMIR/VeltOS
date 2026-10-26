// Windows 11 drop-down: a button with the current choice and a chevron,
// opening a rounded list. `options` is a list of {label, value}.
import QtQuick
import QtQuick.Controls
import org.kde.kirigami as Kirigami
import "."

Rectangle {
    id: box

    property var options: []
    property var currentValue
    property bool enabledState: true
    property string accessibleName
    readonly property int currentIndex: {
        for (let i = 0; i < options.length; ++i) {
            if (options[i].value === currentValue)
                return i;
        }
        return -1;
    }
    readonly property string currentLabel: currentIndex >= 0 ? options[currentIndex].label : ""
    signal activated(var value)

    implicitWidth: 240
    implicitHeight: 34
    radius: 5
    opacity: enabledState ? 1 : 0.45
    color: tap.pressed ? Theme.cardPressed : (hover.hovered ? Theme.cardHover : Theme.control)
    border.width: 1
    border.color: Theme.cardBorder
    activeFocusOnTab: true
    Accessible.role: Accessible.ComboBox
    Accessible.name: accessibleName
    Accessible.description: currentLabel
    Accessible.onPressAction: open()
    Keys.onSpacePressed: open()
    Keys.onReturnPressed: open()

    function open() {
        if (!enabledState || options.length === 0)
            return;
        list.currentIndex = Math.max(0, currentIndex);
        popup.open();
        list.positionViewAtIndex(list.currentIndex, ListView.Center);
    }

    Label {
        anchors.left: parent.left
        anchors.right: chevron.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 12
        anchors.rightMargin: 8
        text: box.currentLabel
        color: Theme.text
        font.pixelSize: 13
        elide: Text.ElideRight
    }
    Kirigami.Icon {
        id: chevron
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: 12
        width: 12
        height: 12
        source: "arrow-down"
        color: Theme.subtext
        isMask: true
    }
    Rectangle {
        anchors.fill: parent
        anchors.margins: -3
        radius: 8
        color: "transparent"
        border.width: 2
        border.color: Theme.text
        visible: box.activeFocus && !popup.visible
    }

    HoverHandler { id: hover; enabled: box.enabledState; cursorShape: Qt.PointingHandCursor }
    TapHandler { id: tap; enabled: box.enabledState; onTapped: box.open() }

    Popup {
        id: popup
        y: box.height + 4
        width: Math.max(box.width, 200)
        height: Math.min(list.contentHeight + 2 * padding, 360)
        padding: 4
        // Modal without a dim: a press outside closes the list and goes no
        // further. Not modal, the press reached the row under the list too
        // (TapHandlers take only a passive grab): choosing a colour mode on
        // Settings' Home opened "Browse themes" beneath it (product owner,
        // 2026-10-22).
        modal: true
        dim: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            radius: 8
            color: Theme.popup
            border.width: 1
            border.color: Theme.cardBorder
        }

        contentItem: ListView {
            id: list
            clip: true
            model: box.options
            boundsBehavior: Flickable.StopAtBounds
            keyNavigationEnabled: true
            ScrollBar.vertical: ScrollBar { policy: list.contentHeight > list.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
            Keys.onReturnPressed: choose(currentIndex)
            Keys.onSpacePressed: choose(currentIndex)

            function choose(index) {
                // An option with enabled: false is shown greyed and cannot be chosen.
                if (index >= 0 && box.options[index].enabled === false)
                    return;
                popup.close();
                if (index >= 0 && index !== box.currentIndex)
                    box.activated(box.options[index].value);
                box.forceActiveFocus();
            }

            delegate: Rectangle {
                id: option
                required property var modelData
                required property int index
                readonly property bool chosen: index === box.currentIndex
                readonly property bool usable: modelData.enabled !== false

                width: ListView.view.width
                height: 34
                radius: 5
                opacity: usable ? 1 : 0.45
                color: !usable ? "transparent" : optionTap.pressed ? Theme.cardPressed
                       : (optionHover.hovered || ListView.isCurrentItem) ? Theme.navHover
                       : chosen ? Theme.navSelected : "transparent"

                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: 16
                    radius: 2
                    color: Theme.accent
                    visible: option.chosen
                }
                Label {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    text: option.modelData.label
                    color: Theme.text
                    font.pixelSize: 13
                    elide: Text.ElideRight
                }
                HoverHandler { id: optionHover; cursorShape: option.usable ? Qt.PointingHandCursor : Qt.ArrowCursor }
                // Exclusive grab on press (ReleaseWithinBounds): with the
                // default passive grab the press went on to the row under
                // the list as well, and its tap opened "Browse themes"
                // (VM, 2026-10-22).
                TapHandler { id: optionTap; gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: list.choose(option.index) }
            }
        }
    }
}
