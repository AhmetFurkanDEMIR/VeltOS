// Install / Open button of an app, or the progress of its running job.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property string pkg: ""
    property string appId: ""
    readonly property string appState: backend.state(pkg, backend.revision)
    readonly property int percent: backend.percent(pkg, backend.revision)
    readonly property bool working: appState !== "" && appState !== "installed" && appState !== "failed"
    implicitWidth: 200
    implicitHeight: working ? progress.implicitHeight : button.implicitHeight

    VButton {
        id: button
        visible: !root.working
        anchors.left: parent.left
        anchors.right: parent.right
        accent: root.appState !== "installed"
        text: root.appState === "installed" ? backend.texts.open : backend.texts.install
        onClicked: root.appState === "installed" ? backend.open(root.appId) : backend.install(root.pkg)
    }

    ColumnLayout {
        id: progress
        visible: root.working
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 6
        Text {
            Layout.fillWidth: true
            text: (backend.texts[root.appState] || "") + (root.percent >= 0 ? "  " + root.percent + " %" : "")
            color: Theme.text
            font.pixelSize: Theme.captionSize
            elide: Text.ElideRight
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 4
            radius: 2
            color: Theme.track
            Rectangle {
                height: parent.height
                radius: 2
                color: Theme.accent
                width: root.percent >= 0 ? parent.width * root.percent / 100 : parent.width * 0.3
                x: root.percent >= 0 ? 0 : indeterminate.position * (parent.width - width)
                Behavior on width { NumberAnimation { duration: 200 } }
            }
            // Moving block while the percentage is unknown (waiting, authorising).
            QtObject {
                id: indeterminate
                property real position: 0
            }
            SequentialAnimation {
                running: root.working && root.percent < 0
                loops: Animation.Infinite
                NumberAnimation { target: indeterminate; property: "position"; from: 0; to: 1; duration: 900; easing.type: Easing.InOutQuad }
                NumberAnimation { target: indeterminate; property: "position"; from: 1; to: 0; duration: 900; easing.type: Easing.InOutQuad }
            }
        }
    }
}
