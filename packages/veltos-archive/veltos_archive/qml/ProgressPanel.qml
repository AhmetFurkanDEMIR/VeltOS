// WinRAR's progress window contents: what is being done, a Windows 11
// progress bar, the elapsed time and Background/Cancel. `job` is app.Job.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: panel
    property var job: null
    signal backgroundRequested()
    spacing: 10

    Text {
        Layout.fillWidth: true
        text: panel.job ? panel.job.title : ""
        color: Theme.text
        font.pixelSize: 15
        font.weight: Font.DemiBold
        elide: Text.ElideMiddle
    }
    Item {
        objectName: "progressBar"
        Layout.fillWidth: true
        implicitHeight: 6
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            height: 1
            color: Theme.subtext
            opacity: 0.6
        }
        Rectangle {
            height: 4
            radius: 2
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width * (panel.job ? panel.job.percent : 0) / 100
            color: Theme.accent
            Behavior on width { NumberAnimation { duration: 150 } }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Text {
            Layout.fillWidth: true
            text: panel.job ? backend.texts.elapsed.replace("{time}", panel.job.elapsed) : ""
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
        }
        Text {
            text: panel.job ? panel.job.percent + "%" : ""
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 6
        spacing: 8
        Item { Layout.fillWidth: true }
        WinButton {
            text: backend.texts.background
            onClicked: panel.backgroundRequested()
        }
        WinButton {
            objectName: "cancelJob"
            text: backend.texts.cancel
            onClicked: backend.cancelJob()
        }
    }
}
