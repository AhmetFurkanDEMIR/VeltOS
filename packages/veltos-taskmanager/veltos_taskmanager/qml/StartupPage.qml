// Startup apps: like Windows 11 - each app that starts at sign-in with its
// status and an Enable/Disable button.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: page
    spacing: 0

    Label {
        Layout.margins: 16
        Layout.bottomMargin: 4
        text: backend.texts.startup
        font.pixelSize: Theme.pageTitleSize
        font.weight: Font.DemiBold
        color: Theme.text
    }
    Label {
        Layout.leftMargin: 16
        Layout.bottomMargin: 12
        text: backend.texts.startup_note
        color: Theme.subtext
    }

    ListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        clip: true
        spacing: 4
        model: backend.startupApps
        ScrollBar.vertical: ScrollBar {}

        Label {
            anchors.centerIn: parent
            visible: parent.count === 0
            text: backend.texts.no_startup
            color: Theme.subtext
        }

        delegate: Rectangle {
            id: entry
            required property var modelData
            width: ListView.view.width
            height: 56
            radius: Theme.radius
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 12
                spacing: 12
                Kirigami.Icon {
                    implicitWidth: 24
                    implicitHeight: 24
                    source: entry.modelData.icon
                }
                Label {
                    Layout.fillWidth: true
                    text: entry.modelData.name
                    elide: Text.ElideRight
                    color: Theme.text
                }
                Label {
                    Layout.preferredWidth: 110
                    text: entry.modelData.enabled ? backend.texts.enabled : backend.texts.disabled
                    color: Theme.subtext
                }
                Button {
                    Layout.preferredWidth: 140
                    text: entry.modelData.enabled ? backend.texts.disable : backend.texts.enable
                    onClicked: backend.setStartupEnabled(entry.modelData.id, !entry.modelData.enabled)
                }
            }
        }
    }
}
