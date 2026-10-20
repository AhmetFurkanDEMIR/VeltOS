// Home: this PC at a glance, the theme, and the settings people change most.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)
    signal openSubPage(string pageId, string subPage)

    // Shortcuts shown on Home: [page id, item id].
    readonly property var recommended: [
        ["network", "wifi"], ["devices", "bluetooth"], ["system", "display"],
        ["system", "sound"], ["apps", "windows-apps"], ["update", "updates"]
    ]

    function findItem(pageId, itemId) {
        for (const p of backend.pages) {
            if (p.id !== pageId)
                continue;
            for (const item of p.items) {
                if (item.id === itemId)
                    return Object.assign({ pageId: pageId }, item);
            }
        }
        return null;
    }

    spacing: 6

    Card {
        Layout.fillWidth: true
        Layout.bottomMargin: 18
        RowLayout {
            width: parent.width
            spacing: 20

            Rectangle {
                Layout.preferredWidth: 132
                Layout.preferredHeight: 84
                radius: 6
                gradient: Gradient {
                    GradientStop { position: 0; color: Theme.dark ? "#0E1846" : "#CFE0FF" }
                    GradientStop { position: 1; color: Theme.dark ? "#2B3FA8" : "#5B86F5" }
                }
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 40
                    height: 40
                    source: "veltos-logo"
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    text: backend.about.pcName
                    color: Theme.text
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: backend.about.model
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    text: backend.about.os
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    elide: Text.ElideRight
                }
            }
            VButton {
                text: backend.text("rename")
                onClicked: page.openSubPage("system", "about")
            }
        }
    }

    Card {
        Layout.fillWidth: true
        Layout.bottomMargin: 18
        ColumnLayout {
            width: parent.width
            spacing: 4
            Label {
                text: backend.text("theme")
                color: Theme.text
                font.pixelSize: Theme.titleSize
                font.weight: Font.DemiBold
            }
            Label {
                text: backend.text("theme_desc")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                Layout.bottomMargin: 10
            }
            ThemePicker {}
        }
    }

    Label {
        text: backend.text("recommended")
        color: Theme.text
        font.pixelSize: Theme.sectionSize
        font.weight: Font.DemiBold
        Layout.bottomMargin: 4
    }

    Repeater {
        model: page.recommended
        delegate: SettingCard {
            required property var modelData
            readonly property var item: page.findItem(modelData[0], modelData[1])
            Layout.fillWidth: true
            visible: item !== null
            icon: item ? item.icon : ""
            title: item ? item.title : ""
            description: !item ? "" : (item.id === "windows-apps" && backend.windowsApps.length > 0
                         ? backend.format("windows_programs_count", String(backend.windowsApps.length))
                         : item.description)
            external: item !== null && item.action !== ""
            onActivated: page.itemActivated(item)
        }
    }
}
