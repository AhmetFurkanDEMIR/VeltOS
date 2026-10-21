// Entrance animation of a page section, as Windows 11 and Microsoft 365
// bring content in: it fades in while gliding up a little. Sections play
// one after the other (delay).
import QtQuick
import "."

Item {
    id: reveal

    property int delay: 0
    default property alias content: inner.data

    implicitWidth: inner.implicitWidth
    implicitHeight: inner.implicitHeight
    opacity: Theme.anim > 0 ? 0 : 1

    function play() {
        if (Theme.anim <= 0) {
            opacity = 1;
            slide.y = 0;
            return;
        }
        animation.restart();
    }

    Item {
        id: inner
        anchors.fill: parent
        transform: Translate { id: slide; y: Theme.anim > 0 ? 28 : 0 }
    }

    SequentialAnimation {
        id: animation
        PauseAnimation { duration: reveal.delay }
        ParallelAnimation {
            NumberAnimation { target: reveal; property: "opacity"; from: 0; to: 1; duration: 280; easing.type: Easing.OutCubic }
            NumberAnimation { target: slide; property: "y"; from: 28; to: 0; duration: 420; easing.type: Easing.OutQuint }
        }
    }
}
