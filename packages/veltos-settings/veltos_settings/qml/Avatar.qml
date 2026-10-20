// Round account picture (accounts.py gives the VeltOS default picture for
// accounts without one); without any picture a person silhouette on grey.
import QtQuick
import QtQuick.Effects
import org.kde.kirigami as Kirigami
import "."

Item {
    id: avatar
    property string source: ""
    property int size: 48
    implicitWidth: size
    implicitHeight: size

    Rectangle {
        id: disc
        anchors.fill: parent
        radius: width / 2
        color: Theme.dark ? "#4A4D5E" : "#C9CEDA"
        visible: avatar.source === "" || picture.status === Image.Error
        Kirigami.Icon {
            anchors.centerIn: parent
            width: parent.width * 0.58
            height: width
            source: "avatar-default-symbolic"
            isMask: true
            color: Theme.dark ? "#C9CEDA" : "#FFFFFF"
        }
    }
    Image {
        id: picture
        anchors.fill: parent
        visible: false
        source: avatar.source !== "" ? "file://" + avatar.source : ""
        sourceSize.width: avatar.size * 2
        sourceSize.height: avatar.size * 2
        fillMode: Image.PreserveAspectCrop
        cache: false
    }
    Rectangle {
        id: mask
        anchors.fill: parent
        radius: width / 2
        visible: false
        layer.enabled: true
    }
    MultiEffect {
        anchors.fill: parent
        visible: avatar.source !== "" && picture.status !== Image.Error
        source: picture
        maskEnabled: true
        maskSource: mask
    }
}
