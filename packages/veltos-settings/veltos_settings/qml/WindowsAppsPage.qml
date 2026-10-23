// Apps > Windows programs, like Windows 11's Settings > Apps > Installed
// apps: every installed Windows program with its icon, publisher, version,
// date and size, read from the Windows environment at once (no slow
// Wine window); its "..." offers Open and Uninstall, and Uninstall asks
// first, in a small flyout, as Windows does. The program's own
// uninstaller then runs; the list follows when it is done.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)

    spacing: 6
    Component.onCompleted: backend.refresh()

    function sizeText(kb) {
        if (!kb)
            return "";
        if (kb >= 1024 * 1024)
            return (kb / 1024 / 1024).toFixed(1) + " GB";
        if (kb >= 1024)
            return (kb / 1024).toFixed(1) + " MB";
        return kb + " KB";
    }

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
            id: row
            required property var modelData
            readonly property bool busy: backend.uninstalling.indexOf(modelData.key) >= 0
            Layout.fillWidth: true
            padding: 14
            RowLayout {
                width: parent.width
                spacing: 16
                Image {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    visible: row.modelData.icon !== ""
                    source: row.modelData.icon !== "" ? "file://" + row.modelData.icon : ""
                    sourceSize: Qt.size(64, 64)
                    smooth: true
                }
                Kirigami.Icon {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    visible: row.modelData.icon === ""
                    source: "application-x-ms-dos-executable"
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: row.modelData.name
                        color: Theme.text
                        font.pixelSize: Theme.titleSize
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: row.busy ? backend.text("uninstalling")
                              : [row.modelData.publisher, row.modelData.version,
                                 row.modelData.installed ? backend.format("installed_on", row.modelData.installed) : ""]
                                .filter(part => part.length > 0).join("  ·  ")
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                }
                Label {
                    visible: text !== "" && !row.busy
                    text: page.sizeText(row.modelData.sizeKb)
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                }
                BusyIndicator {
                    visible: row.busy
                    running: visible
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                }
                // Windows 11's "..." button of an installed app.
                Rectangle {
                    id: more
                    visible: !row.busy && (row.modelData.key !== "" || row.modelData.shortcut !== "")
                    implicitWidth: 36
                    implicitHeight: 32
                    radius: 5
                    color: moreHover.hovered ? Theme.navHover : "transparent"
                    activeFocusOnTab: true
                    Accessible.role: Accessible.Button
                    Accessible.name: backend.text("more_options")
                    Keys.onReturnPressed: menu.open()
                    Keys.onSpacePressed: menu.open()
                    Text {
                        anchors.centerIn: parent
                        text: "···"
                        color: Theme.text
                        font.pixelSize: 16
                        font.weight: Font.Bold
                    }
                    HoverHandler { id: moreHover }
                    TapHandler { onTapped: menu.open() }

                    Popup {
                        id: menu
                        y: more.height + 4
                        x: more.width - width
                        padding: 4
                        width: 200
                        property bool confirming: false
                        onClosed: confirming = false
                        background: Rectangle {
                            radius: 8
                            color: Theme.card
                            border.width: 1
                            border.color: Theme.cardBorder
                        }
                        contentItem: ColumnLayout {
                            spacing: 0
                            // The menu.
                            Repeater {
                                model: menu.confirming ? [] : [
                                    { id: "open", text: backend.text("open"), shown: row.modelData.shortcut !== "" },
                                    { id: "uninstall", text: backend.text("uninstall"), shown: row.modelData.key !== "" }
                                ].filter(entry => entry.shown)
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    implicitHeight: 34
                                    radius: 4
                                    color: entryHover.hovered ? Theme.navHover : "transparent"
                                    Accessible.role: Accessible.MenuItem
                                    Accessible.name: modelData.text
                                    Label {
                                        anchors.verticalCenter: parent.verticalCenter
                                        x: 12
                                        text: modelData.text
                                        color: Theme.text
                                        font.pixelSize: Theme.bodySize
                                    }
                                    HoverHandler { id: entryHover }
                                    TapHandler {
                                        onTapped: {
                                            if (modelData.id === "open") {
                                                backend.openWindowsApp(row.modelData.shortcut);
                                                menu.close();
                                            } else {
                                                menu.confirming = true;
                                            }
                                        }
                                    }
                                }
                            }
                            // "This app and its related info will be uninstalled."
                            ColumnLayout {
                                visible: menu.confirming
                                Layout.fillWidth: true
                                Layout.margins: 10
                                spacing: 12
                                Label {
                                    Layout.fillWidth: true
                                    text: backend.text("uninstall_question")
                                    color: Theme.text
                                    font.pixelSize: Theme.bodySize
                                    wrapMode: Text.WordWrap
                                }
                                VButton {
                                    Layout.alignment: Qt.AlignRight
                                    text: backend.text("uninstall")
                                    primary: true
                                    onClicked: {
                                        menu.close();
                                        backend.uninstallWindowsApp(row.modelData.key);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
