// Home, laid out like Windows 11 Settings' Home: this PC (its wallpaper,
// name and model, Rename), the network and VeltOS Update at the top right,
// then cards: VeltOS apps, recently used settings, Bluetooth devices and
// "Personalize your device" with the themes.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)
    signal openSubPage(string pageId, string subPage)

    readonly property bool wide: width >= 640
    readonly property bool headerWide: width >= 860
    readonly property var net: backend.network
    readonly property var bt: backend.bluetooth
    readonly property var personal: backend.personal

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

    // The desktop picture of this PC (light or dark preview).
    function wallpaperUrl() {
        const current = personal.wallpaper || "VeltOS";
        const id = current.split("/").filter(part => part.length > 0).pop();
        for (const w of personal.wallpapers || []) {
            if (w.name === id)
                return "file://" + (Theme.dark ? w.previewDark : w.preview);
        }
        // A picture of the user's own (not a wallpaper package).
        return /^\/.*\.(png|jpe?g|webp|avif|jxl)$/i.test(current) ? "file://" + current : "";
    }

    spacing: 16
    Component.onCompleted: {
        backend.refreshNetwork(false);
        backend.refreshBluetooth();
        backend.refreshPersonal();
    }

    // A status at the top right: an icon, a title and a line under it.
    component Status: RowLayout {
        id: status
        property string icon
        property string title
        property string subtitle
        signal clicked()
        spacing: 12
        Accessible.role: Accessible.Button
        Accessible.name: title
        Kirigami.Icon {
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            source: status.icon
            isMask: true
            color: Theme.accent
        }
        ColumnLayout {
            spacing: 0
            Label {
                text: status.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
                font.weight: Font.DemiBold
            }
            Label {
                text: status.subtitle
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
            }
        }
        HoverHandler { cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: status.clicked() }
    }

    // A card with a heading and full-width rows below a divider.
    component HomeCard: Rectangle {
        id: homeCard
        property string title
        property string description
        default property alias rows: body.data
        Layout.fillWidth: true
        implicitHeight: column.implicitHeight
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        ColumnLayout {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 0
            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 22
                Layout.rightMargin: 22
                Layout.topMargin: 20
                text: homeCard.title
                color: Theme.text
                font.pixelSize: 20
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 22
                Layout.rightMargin: 22
                Layout.topMargin: 4
                Layout.bottomMargin: 16
                visible: text.length > 0
                text: homeCard.description
                color: Theme.subtext
                font.pixelSize: Theme.bodySize + 1
                wrapMode: Text.WordWrap
            }
            ColumnLayout {
                id: body
                Layout.fillWidth: true
                spacing: 0
            }
        }
    }

    // A row of a card: divider above, icon, text, optional controls, chevron.
    component CardRow: Rectangle {
        id: row
        property string icon
        property string title
        property string subtitle
        property bool chevron: true
        property bool clickable: true
        default property alias controls: extra.data
        signal clicked()
        Layout.fillWidth: true
        implicitHeight: Math.max(60, line.implicitHeight + 24)
        color: clickable && tap.pressed ? Theme.cardPressed : (clickable && hover.hovered ? Theme.cardHover : "transparent")
        radius: Theme.radius
        Accessible.role: Accessible.Button
        Accessible.name: title
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: Theme.cardBorder
        }
        RowLayout {
            id: line
            anchors.fill: parent
            anchors.leftMargin: 22
            anchors.rightMargin: 18
            spacing: 16
            Kirigami.Icon {
                visible: row.icon.length > 0
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
                source: row.icon
                isMask: row.icon.endsWith("-symbolic")
                color: Theme.text
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Label {
                    Layout.fillWidth: true
                    text: row.title
                    color: Theme.text
                    font.pixelSize: Theme.titleSize
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: row.subtitle
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    elide: Text.ElideRight
                }
            }
            RowLayout {
                id: extra
                spacing: 12
            }
            Kirigami.Icon {
                visible: row.chevron
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                source: "go-next"
                color: Theme.subtext
                isMask: true
            }
        }
        HoverHandler { id: hover; enabled: row.clickable; cursorShape: Qt.PointingHandCursor }
        TapHandler { id: tap; enabled: row.clickable; onTapped: row.clicked() }
    }

    // --- This PC, network, VeltOS Update ---------------------------------------
    GridLayout {
        Layout.fillWidth: true
        Layout.bottomMargin: 6
        columns: page.headerWide ? 4 : 2
        columnSpacing: 32
        rowSpacing: 16

        RowLayout {
            Layout.columnSpan: page.headerWide ? 1 : 2
            spacing: 18
            Rectangle {
                Layout.preferredWidth: 124
                Layout.preferredHeight: 72
                radius: 6
                color: "#101010"
                Image {
                    anchors.fill: parent
                    anchors.margins: 3
                    source: page.wallpaperUrl()
                    fillMode: Image.PreserveAspectCrop
                    sourceSize.width: 248
                    asynchronous: true
                }
            }
            ColumnLayout {
                spacing: 1
                Label {
                    text: backend.about.pcName
                    color: Theme.text
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
                Label {
                    visible: text.length > 0
                    text: backend.about.model
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                }
                Label {
                    text: backend.text("rename")
                    color: Theme.accent
                    font.pixelSize: Theme.bodySize + 1
                    HoverHandler { cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: page.openSubPage("system", "about") }
                }
            }
        }
        Item { Layout.fillWidth: true; visible: page.headerWide }
        Status {
            icon: page.net.connection && page.net.connection.type === "ethernet"
                  ? "network-wired-symbolic" : "network-wireless-symbolic"
            title: page.net.connection && page.net.connection.name ? page.net.connection.name
                   : backend.text("not_connected")
            subtitle: page.net.connection && page.net.connection.name
                      ? (page.net.connection.type === "wifi" ? backend.text("connected_secured")
                                                             : backend.text("connected"))
                      : ""
            onClicked: page.openSubPage("network", "wifi")
        }
        Status {
            icon: "view-refresh-symbolic"
            title: backend.text("update_title")
            subtitle: backend.updateChecked
            onClicked: page.openSubPage("update", "")
        }
    }

    // --- The cards ------------------------------------------------------------------
    GridLayout {
        Layout.fillWidth: true
        columns: page.wide ? 2 : 1
        columnSpacing: 16
        rowSpacing: 16

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.alignment: Qt.AlignTop
            spacing: 16

            // VeltOS' counterpart of Windows' Microsoft account card.
            HomeCard {
                title: backend.text("promo_title")
                description: backend.text("promo_desc")
                RowLayout {
                    Layout.leftMargin: 22
                    Layout.bottomMargin: 18
                    spacing: 10
                    Repeater {
                        model: ["veltos-store", "veltos-mail", "veltos-explorer", "org.kde.gwenview",
                                "veltos-camera", "veltos-calculator", "veltos-snip", "veltos-archive"]
                        delegate: Kirigami.Icon {
                            required property string modelData
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 26
                            source: modelData
                        }
                    }
                }
                VButton {
                    Layout.leftMargin: 22
                    Layout.bottomMargin: 22
                    text: backend.text("open_store")
                    onClicked: backend.runAction("store")
                }
            }

            HomeCard {
                title: backend.text("bt_devices")
                description: backend.text("bt_devices_desc")
                CardRow {
                    icon: "bluetooth-symbolic"
                    title: "Bluetooth"
                    subtitle: !page.bt.available ? backend.text("bt_unavailable")
                              : page.bt.powered ? backend.text("bt_discoverable").replace("{name}", backend.about.pcName)
                              : backend.text("bt_off")
                    chevron: false
                    clickable: false
                    ToggleSwitch {
                        visible: page.bt.available
                        checked: page.bt.powered
                        accessibleName: "Bluetooth"
                        onToggled: on => backend.setBluetooth(on)
                    }
                }
                Repeater {
                    model: page.bt.available ? page.bt.devices.slice(0, 3) : []
                    delegate: CardRow {
                        required property var modelData
                        icon: modelData.icon + "-symbolic"
                        title: modelData.name
                        subtitle: modelData.connected ? backend.text("connected") : backend.text("paired")
                        onClicked: page.openSubPage("devices", "bluetooth")
                    }
                }
                CardRow {
                    title: backend.text("view_all_devices")
                    onClicked: page.openSubPage("devices", "bluetooth")
                    VButton {
                        visible: page.bt.available
                        text: backend.text("add_device")
                        enabledState: page.bt.powered
                        onClicked: addDialog.open()
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.alignment: Qt.AlignTop
            spacing: 16

            HomeCard {
                title: backend.text("recommended")
                description: backend.text("recommended_desc")
                Repeater {
                    model: backend.recentSettings
                    delegate: CardRow {
                        required property var modelData
                        readonly property var item: page.findItem(modelData[0], modelData[1])
                        visible: item !== null
                        icon: item ? item.icon : ""
                        title: item ? item.title : ""
                        onClicked: page.itemActivated(item)
                    }
                }
            }

            HomeCard {
                title: backend.text("personalize_title")
                GridLayout {
                    id: themeGrid
                    Layout.fillWidth: true
                    Layout.leftMargin: 22
                    Layout.rightMargin: 22
                    Layout.topMargin: 14
                    Layout.bottomMargin: 18
                    columns: 3
                    columnSpacing: 10
                    rowSpacing: 10
                    Repeater {
                        model: backend.themes.slice(0, 6)
                        delegate: ThemeTile {
                            required property var modelData
                            theme: modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.round((themeGrid.width - 20) / 3 * 0.66)
                        }
                    }
                }
                CardRow {
                    icon: "preferences-color-symbolic"
                    title: backend.text("colour_mode")
                    chevron: false
                    clickable: false
                    VComboBox {
                        Layout.preferredWidth: 140
                        accessibleName: backend.text("colour_mode")
                        options: [{ label: backend.text("light"), value: false },
                                  { label: backend.text("dark"), value: true }]
                        currentValue: backend.darkMode
                        onActivated: value => backend.setDarkMode(value)
                    }
                }
                CardRow {
                    title: backend.text("browse_themes")
                    onClicked: page.openSubPage("personalization", "themes")
                }
            }
        }
    }

    AddDeviceDialog {
        id: addDialog
    }
}
