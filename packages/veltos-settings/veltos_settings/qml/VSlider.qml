// Windows 11 slider: thin track, accent fill, round thumb with an accent
// dot that grows on hover. `moved` is sent while dragging; `released` once.
import QtQuick
import "."

Item {
    id: slider

    property real from: 0
    property real to: 100
    property real value: 0
    property real stepSize: 1
    property bool enabledState: true
    property string accessibleName
    readonly property bool pressed: drag.active || tap.pressed
    readonly property real position: to > from ? (value - from) / (to - from) : 0
    signal moved(real value)
    signal released(real value)

    function setFromX(x) {
        const fraction = Math.max(0, Math.min(1, (x - thumb.width / 2) / (width - thumb.width)));
        let next = from + fraction * (to - from);
        next = Math.round(next / stepSize) * stepSize;
        if (next !== value) {
            value = next;
            moved(value);
        }
    }

    function step(delta) {
        value = Math.max(from, Math.min(to, value + delta));
        moved(value);
        released(value);
    }

    implicitWidth: 240
    implicitHeight: 32
    opacity: enabledState ? 1 : 0.45
    activeFocusOnTab: true
    Accessible.role: Accessible.Slider
    Accessible.name: accessibleName
    Keys.onLeftPressed: step(-stepSize)
    Keys.onRightPressed: step(stepSize)
    Keys.onDownPressed: step(-stepSize)
    Keys.onUpPressed: step(stepSize)

    Rectangle {
        id: track
        anchors.verticalCenter: parent.verticalCenter
        x: thumb.width / 2
        width: parent.width - thumb.width
        height: 4
        radius: 2
        color: Theme.trackStrong

        Rectangle {
            width: parent.width * slider.position
            height: parent.height
            radius: 2
            color: Theme.accent
        }
    }

    Rectangle {
        id: thumb
        width: 20
        height: 20
        radius: 10
        anchors.verticalCenter: parent.verticalCenter
        x: slider.position * (slider.width - width)
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder

        Rectangle {
            anchors.centerIn: parent
            width: slider.pressed ? 10 : (hover.hovered ? 14 : 12)
            height: width
            radius: width / 2
            color: Theme.accent
            Behavior on width { NumberAnimation { duration: 90 } }
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: -2
        radius: 6
        color: "transparent"
        border.width: 2
        border.color: Theme.text
        visible: slider.activeFocus
    }

    HoverHandler { id: hover; enabled: slider.enabledState; cursorShape: Qt.PointingHandCursor }
    TapHandler {
        id: tap
        enabled: slider.enabledState
        onPressedChanged: {
            if (pressed)
                slider.setFromX(point.position.x);
            else
                slider.released(slider.value);
        }
    }
    DragHandler {
        id: drag
        enabled: slider.enabledState
        target: null
        xAxis.enabled: true
        yAxis.enabled: false
        onCentroidChanged: if (active) slider.setFromX(centroid.position.x)
        onActiveChanged: if (!active) slider.released(slider.value)
    }
    WheelHandler {
        enabled: slider.enabledState
        onWheel: event => slider.step(event.angleDelta.y > 0 ? slider.stepSize * 2 : -slider.stepSize * 2)
    }
}
