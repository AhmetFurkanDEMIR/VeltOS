// VeltOS Update, in the layout of Windows 11's Windows Update: whether this
// PC is up to date or a newer VeltOS (or other updates) is ready, with
// "Check for updates", "Download & install" or "Restart now"; the progress
// while it works; what is new (the release's notes); the daily
// notification switch. backend.veltosUpdate (app.py, veltos_update).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var u: backend.veltosUpdate
    readonly property bool busy: u.state === "checking" || u.state === "installing"
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.openVeltosUpdate()

    Card {
        objectName: "updateStatus"
        Layout.fillWidth: true
        RowLayout {
            width: parent.width
            spacing: 18

            Rectangle {
                Layout.preferredWidth: 56
                Layout.preferredHeight: 56
                Layout.alignment: Qt.AlignTop
                radius: 28
                color: page.u.state === "uptodate" ? "#0F7B0F" : page.u.state === "failed" ? Theme.danger
                                                   : Theme.accent
                Kirigami.Icon {
                    id: statusIcon
                    anchors.centerIn: parent
                    width: 28
                    height: 28
                    source: page.u.state === "uptodate" ? "dialog-ok-apply-symbolic"
                            : page.u.state === "restart" ? "system-reboot-symbolic"
                            : page.u.state === "failed" ? "dialog-warning-symbolic" : "view-refresh-symbolic"
                    isMask: true
                    color: "#FFFFFF"
                    RotationAnimator on rotation {
                        running: page.busy && page.visible
                        from: 0
                        to: 360
                        duration: 1400
                        loops: Animation.Infinite
                    }
                    rotation: 0
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Label {
                    objectName: "updateTitle"
                    Layout.fillWidth: true
                    text: page.u.title || ""
                    color: Theme.text
                    font.pixelSize: Theme.titleSize + 6
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Label {
                    Layout.fillWidth: true
                    visible: text !== ""
                    text: page.u.subtitle || ""
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize + 1
                    wrapMode: Text.WordWrap
                }
                // Windows 11's thin progress bar: the percentage when pkcon
                // gives one, a running stripe otherwise.
                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    visible: page.busy
                    implicitHeight: 4
                    radius: 2
                    color: Theme.track
                    clip: true
                    Rectangle {
                        id: stripe
                        height: parent.height
                        radius: 2
                        color: Theme.accent
                        width: page.u.percent >= 0 ? parent.width * page.u.percent / 100 : parent.width * 0.3
                        Behavior on width { NumberAnimation { duration: 250 } }
                        NumberAnimation on x {
                            running: page.busy && page.visible && !(page.u.percent >= 0)
                            from: -stripe.width
                            to: stripe.parent.width
                            duration: 1500
                            loops: Animation.Infinite
                        }
                    }
                }
            }

            VButton {
                objectName: "updateButton"
                Layout.alignment: Qt.AlignTop
                visible: (page.u.button || "") !== ""
                primary: page.u.state === "available" || page.u.state === "restart"
                enabledState: !page.busy
                text: page.u.button || ""
                onClicked: backend.veltosUpdateAction()
            }
        }
    }

    // What is new in the release (its notes from GitHub, Markdown).
    Card {
        objectName: "updateNotes"
        Layout.fillWidth: true
        Layout.topMargin: 8
        visible: (page.u.notes || "") !== ""
        ColumnLayout {
            width: parent.width
            spacing: 10
            Label {
                Layout.fillWidth: true
                text: page.u.notesTitle || ""
                color: Theme.text
                font.pixelSize: Theme.titleSize + 2
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                visible: text !== ""
                text: page.u.published || ""
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
            }
            Label {
                Layout.fillWidth: true
                text: page.u.notes || ""
                textFormat: Text.MarkdownText
                color: Theme.text
                linkColor: Theme.accent
                font.pixelSize: Theme.bodySize + 1
                lineHeight: 1.15
                wrapMode: Text.WordWrap
                onLinkActivated: link => Qt.openUrlExternally(link)
            }
            Label {
                text: "<a href=\"#\">" + backend.text("vu_release_page") + "</a>"
                textFormat: Text.StyledText
                linkColor: Theme.accent
                font.pixelSize: Theme.bodySize + 1
                onLinkActivated: backend.openVeltosRelease()
                HoverHandler { cursorShape: Qt.PointingHandCursor }
            }
        }
    }

    SectionLabel {
        text: backend.text("vu_more")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-desktop-notification-symbolic"
        title: backend.text("vu_notify")
        description: backend.text("vu_notify_desc")
        ToggleSwitch {
            checked: page.u.notify === true
            accessibleName: backend.text("vu_notify")
            onToggled: on => backend.setVeltosUpdateNotify(on)
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "dialog-information-symbolic"
        title: backend.text("vu_how")
        description: backend.text("vu_how_desc")
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "internet-web-browser-symbolic"
        title: backend.text("vu_website")
        description: backend.text("vu_website_desc")
        clickable: true
        onClicked: backend.runAction("website")
    }
}
