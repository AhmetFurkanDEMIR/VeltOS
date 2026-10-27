// The package installer window (a .deb opened from File Explorer), in the
// layout of Windows 11's App Installer: the question ("Install VLC?") with
// publisher, version and size on the left, the app's icon on the right,
// the package's description, the trust note, a thin progress bar while it
// installs and the buttons at the bottom right. `backend` is
// installer.Installer.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window

    width: 640
    height: 440
    minimumWidth: width
    minimumHeight: height
    maximumWidth: width
    maximumHeight: height
    visible: true
    title: backend.texts.pkg_window_title
    color: Theme.window

    readonly property string page: backend.page
    readonly property bool working: page === "working"
    readonly property bool problem: ["failed", "invalid", "wrongarch"].includes(page)

    onClosing: close => {
        // An installation in progress finishes; the window stays until then.
        if (working)
            close.accepted = false;
    }
    Connections {
        target: backend
        function onCloseRequested() { window.close(); }
    }

    // Header: question and package details left, icon right.
    RowLayout {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 28
        anchors.leftMargin: 32
        anchors.rightMargin: 32
        spacing: 24

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 4
            Text {
                objectName: "title"
                Layout.fillWidth: true
                Layout.bottomMargin: 8
                text: backend.title
                color: Theme.text
                font.pixelSize: Math.round(24 * Theme.textScale)
                font.weight: Font.DemiBold
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            Repeater {
                model: backend.details
                delegate: Text {
                    required property string modelData
                    Layout.fillWidth: true
                    text: modelData
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    elide: Text.ElideRight
                }
            }
        }
        Item {
            Layout.alignment: Qt.AlignTop
            implicitWidth: 88
            implicitHeight: 88
            Image {
                anchors.fill: parent
                source: backend.iconUrl
                visible: backend.iconUrl !== "" && status === Image.Ready
                fillMode: Image.PreserveAspectFit
                sourceSize.width: 176
                sourceSize.height: 176
                smooth: true
                mipmap: true
            }
            Kirigami.Icon {
                anchors.fill: parent
                source: "application-x-deb"
                fallback: "package-x-generic"
                visible: backend.iconUrl === ""
            }
        }
    }

    // The description, the result or pkcon's output.
    ColumnLayout {
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        anchors.topMargin: 16
        anchors.leftMargin: 32
        anchors.rightMargin: 32
        anchors.bottomMargin: 12
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: !backend.showLog
            spacing: 10
            // Result mark, as in Windows' status messages.
            Rectangle {
                visible: window.page === "done" || window.problem
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 1
                implicitWidth: 18
                implicitHeight: 18
                radius: 9
                color: window.page === "done" ? (Theme.dark ? "#6CCB5F" : "#0F7B0F") : Theme.danger
                Text {
                    anchors.centerIn: parent
                    text: window.page === "done" ? "✓" : "!"
                    color: Theme.dark ? "#000000" : "#FFFFFF"
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
            }
            // A Flickable: a long description scrolls inside the window.
            Flickable {
                id: bodyFlick
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: Math.min(body.implicitHeight, 150)
                contentWidth: width
                contentHeight: body.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { policy: bodyFlick.contentHeight > bodyFlick.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff }
                Text {
                    id: body
                    objectName: "body"
                    width: bodyFlick.width - 12
                    text: backend.body
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.Wrap
                    lineHeight: 1.15
                }
            }
        }

        // pkcon's output after a failure (Details).
        Rectangle {
            visible: backend.showLog
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.smallRadius
            color: Theme.card
            border.color: Theme.cardBorder
            Flickable {
                id: logFlick
                anchors.fill: parent
                anchors.margins: 8
                contentWidth: width
                contentHeight: logText.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                TextEdit {
                    id: logText
                    width: logFlick.width - 12
                    text: backend.log
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextEdit.WrapAnywhere
                    color: Theme.text
                    font.family: "monospace"
                    font.pixelSize: Theme.captionSize
                }
            }
        }

        // Information bar (Windows 11 InfoBar): who the package comes from matters.
        Rectangle {
            Layout.fillWidth: true
            visible: window.page === "ready"
            implicitHeight: note.implicitHeight + 24
            radius: Theme.smallRadius
            color: Theme.card
            border.color: Theme.cardBorder
            Rectangle {
                id: infoMark
                x: 14
                y: 13
                width: 16
                height: 16
                radius: 8
                color: Theme.accent
                Text {
                    anchors.centerIn: parent
                    text: "i"
                    color: Theme.accentText
                    font.pixelSize: 11
                    font.weight: Font.Bold
                }
            }
            Text {
                id: note
                anchors.left: infoMark.right
                anchors.right: parent.right
                anchors.leftMargin: 10
                anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                text: backend.texts.pkg_trust
                color: Theme.text
                font.pixelSize: Theme.captionSize
                wrapMode: Text.Wrap
            }
        }
    }

    // Footer: progress while busy; option on the left, buttons on the right.
    ColumnLayout {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 32
        anchors.rightMargin: 32
        anchors.bottomMargin: 24
        spacing: 16

        // Windows 11 progress bar: the percentage when pkcon gives one, a
        // short bar running along the track until then.
        Item {
            objectName: "progress"
            Layout.fillWidth: true
            visible: window.working
            implicitHeight: 3
            clip: true
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width
                height: 1
                color: Theme.track
            }
            Rectangle {
                visible: backend.percent >= 0
                height: 3
                radius: 1.5
                width: parent.width * Math.max(0, backend.percent) / 100
                color: Theme.accent
                Behavior on width { NumberAnimation { duration: 200 } }
            }
            Rectangle {
                id: runningBar
                visible: backend.percent < 0
                height: 3
                radius: 1.5
                width: parent.width * 0.35
                color: Theme.accent
                NumberAnimation on x {
                    running: window.working && backend.percent < 0 && window.visible
                    loops: Animation.Infinite
                    from: -runningBar.width
                    to: footer.width
                    duration: 1600
                    easing.type: Easing.InOutQuad
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            // "Launch when ready", as Windows' App Installer has it.
            CheckBox {
                id: launchBox
                objectName: "launch"
                visible: window.page === "ready" && backend.status !== "same"
                checked: backend.launch
                text: backend.texts.pkg_launch
                font.pixelSize: Theme.bodySize
                onToggled: backend.launch = checked
            }
            VButton {
                visible: window.page === "failed"
                text: backend.showLog ? backend.texts.pkg_hide_details : backend.texts.pkg_details
                onClicked: backend.toggleLog()
            }
            Item { Layout.fillWidth: true }
            Repeater {
                model: backend.apps
                delegate: VButton {
                    required property int index
                    required property var modelData
                    accent: window.page === "done" && index === 0
                    text: backend.apps.length > 1 ? backend.texts.open + " " + modelData.name : backend.texts.open
                    onClicked: {
                        backend.openApp(index);
                        backend.close();
                    }
                }
            }
            VButton {
                objectName: "primary"
                visible: window.page === "ready"
                accent: true
                focus: true
                text: backend.primaryText
                onClicked: backend.install()
            }
            VButton {
                objectName: "close"
                visible: !window.working
                text: window.page === "ready" ? backend.texts.cancel : backend.texts.close
                onClicked: backend.close()
            }
        }
    }
}
