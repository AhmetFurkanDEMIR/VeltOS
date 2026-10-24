// A round picture with the person's initials on their colour, as Outlook
// shows senders that have no photo.
import QtQuick
import "."

Rectangle {
    id: avatar

    property string initials: ""
    property color tint: Theme.brand
    property int size: 32

    width: size
    height: size
    radius: size / 2
    color: Qt.lighter(tint, Theme.dark ? 1.0 : 1.0)
    Text {
        anchors.centerIn: parent
        text: avatar.initials
        color: "#FFFFFF"
        font.pixelSize: Math.round(avatar.size * 0.38)
        font.weight: Font.DemiBold
    }
}
