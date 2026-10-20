// Library: updates (Get updates / Update all) and the installed apps with
// Open and Uninstall, as in the Microsoft Store's Library.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: page
    signal opened(string appId)
    contentWidth: availableWidth
    clip: true

    readonly property var job: backend.activeJob
    readonly property bool updating: job.action === "update"

    ColumnLayout {
        width: page.availableWidth
        spacing: 16

        Text {
            Layout.topMargin: 24
            Layout.leftMargin: 32
            text: backend.texts.library
            color: Theme.text
            font.pixelSize: Theme.pageTitleSize
            font.weight: Font.DemiBold
        }

        // Updates.
        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: 32
            Layout.rightMargin: 32
            Layout.preferredHeight: updates.implicitHeight + 40
            radius: Theme.radius
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder
            ColumnLayout {
                id: updates
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 20
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: backend.texts.updates
                            color: Theme.text
                            font.pixelSize: Theme.bodySize + 2
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.updating ? (page.job.status || backend.texts.updating)
                                  : backend.checkingUpdates ? backend.texts.checking
                                  : backend.updates === 0 ? backend.texts.up_to_date
                                  : backend.updates > 0 ? backend.texts.updates_available.replace("%1", backend.updates)
                                  : ""
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize
                            elide: Text.ElideRight
                        }
                    }
                    VButton {
                        visible: backend.updates > 0 && !page.updating
                        accent: true
                        text: backend.texts.update_all
                        onClicked: backend.updateAll()
                    }
                    VButton {
                        enabled: !backend.checkingUpdates && !page.updating
                        accent: backend.updates <= 0
                        text: backend.texts.get_updates
                        onClicked: backend.checkUpdates()
                    }
                }
                Rectangle {
                    visible: page.updating
                    Layout.fillWidth: true
                    implicitHeight: 4
                    radius: 2
                    color: Theme.track
                    Rectangle {
                        height: parent.height
                        radius: 2
                        color: Theme.accent
                        width: parent.width * Math.max(0.05, page.job.percent || 0) / 100
                    }
                }
            }
        }

        Text {
            Layout.topMargin: 8
            Layout.leftMargin: 32
            text: backend.texts.installed_apps
            color: Theme.text
            font.pixelSize: Theme.sectionSize
            font.weight: Font.DemiBold
        }
        Text {
            visible: backend.library.length === 0
            Layout.leftMargin: 32
            text: backend.texts.no_installed
            color: Theme.subtext
            font.pixelSize: Theme.bodySize
        }

        Repeater {
            model: backend.library
            MouseArea {
                id: row
                required property var modelData
                Layout.fillWidth: true
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                Layout.preferredHeight: 64
                hoverEnabled: true
                onClicked: page.opened(modelData.id)
                Rectangle {
                    anchors.fill: parent
                    radius: Theme.radius
                    color: row.containsMouse ? Theme.cardHover : Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 14
                    AppIcon {
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        icon: row.modelData.icon
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: row.modelData.name
                            color: Theme.text
                            font.pixelSize: Theme.bodySize + 1
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: backend.isProtected(row.modelData.pkg, backend.revision)
                                  ? backend.texts.protected : row.modelData.category
                            color: backend.isProtected(row.modelData.pkg, backend.revision) ? Theme.danger : Theme.subtext
                            font.pixelSize: Theme.captionSize
                            elide: Text.ElideRight
                        }
                    }
                    InstallButton {
                        Layout.preferredWidth: 120
                        pkg: row.modelData.pkg
                        appId: row.modelData.id
                    }
                    VButton {
                        visible: backend.state(row.modelData.pkg, backend.revision) === "installed"
                        text: backend.texts.uninstall
                        onClicked: backend.uninstall(row.modelData.pkg)
                    }
                }
            }
        }

        Item { Layout.preferredHeight: 16 }
    }
}
