// Apps > Windows programs: what was installed from .exe/.msi files.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)

    spacing: 6

    Label {
        Layout.fillWidth: true
        Layout.bottomMargin: 12
        text: backend.text("windows_apps_intro")
        color: Theme.subtext
        font.pixelSize: 13
        wrapMode: Text.WordWrap
    }

    Card {
        Layout.fillWidth: true
        visible: backend.windowsApps.length === 0
        Label {
            width: parent.width
            text: backend.text("no_windows_apps")
            color: Theme.text
            font.pixelSize: Theme.titleSize
            wrapMode: Text.WordWrap
        }
    }

    Repeater {
        model: backend.windowsApps
        delegate: Card {
            required property var modelData
            Layout.fillWidth: true
            padding: 16
            RowLayout {
                width: parent.width
                spacing: 16
                Kirigami.Icon {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    source: "application-x-ms-dos-executable"
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: modelData.name
                        color: Theme.text
                        font.pixelSize: Theme.titleSize
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: [modelData.publisher, modelData.version,
                               modelData.installed ? backend.format("installed_on", modelData.installed) : ""]
                              .filter(part => part.length > 0).join("  ·  ")
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                }
                VButton {
                    visible: modelData.shortcut !== ""
                    text: backend.text("open")
                    onClicked: backend.openWindowsApp(modelData.shortcut)
                }
            }
        }
    }

    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 12
        icon: "edit-delete"
        title: backend.text("uninstall_programs")
        description: backend.text("uninstall_desc")
        external: true
        onActivated: page.itemActivated({ action: "uninstall-windows", kcm: "", page: "" })
    }
}
