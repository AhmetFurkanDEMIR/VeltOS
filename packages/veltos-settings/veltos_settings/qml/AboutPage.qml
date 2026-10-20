// System > About: device and VeltOS specifications, rename this PC.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var about: backend.about
    readonly property var deviceRows: {
        const rows = [[backend.text("device_name"), about.pcName]];
        if (about.model)
            rows.push([backend.text("model"), about.model]);
        rows.push([backend.text("processor"),
                   (about.cpu || backend.text("unknown")) +
                   (about.threads ? "  (" + backend.format("threads", String(about.threads)) + ")" : "")]);
        rows.push([backend.text("installed_ram"), about.memory]);
        const gpus = about.gpus || [];
        rows.push([backend.text("graphics"), gpus.length ? gpus.join("\n") : backend.text("unknown")]);
        rows.push([backend.text("system_type"), about.architecture]);
        return rows;
    }
    readonly property var osRows: [
        [backend.text("edition"), about.os],
        [backend.text("version"), about.version || backend.text("unknown")],
        [backend.text("os_build"), about.build || backend.text("unknown")],
        [backend.text("developer"), "Ahmet Furkan Demir"],
        [backend.text("email"), "1ahmetfurkandemir@gmail.com"],
        [backend.text("website"), "https://ahmetfurkandemir.com/"]
    ]

    function rowsText(rows) {
        return rows.map(r => r[0] + ": " + r[1].replace(/\n/g, ", ")).join("\n");
    }

    // Web addresses and email addresses open in the browser / mail program.
    function linked(value) {
        if (/^https?:\/\/\S+$/.test(value))
            return "<a href=\"" + value + "\">" + value + "</a>";
        if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value))
            return "<a href=\"mailto:" + value + "\">" + value + "</a>";
        return value;
    }

    spacing: 12

    component SpecCard: Card {
        id: spec

        property string heading
        property var rows: []
        property bool copied: false

        Layout.fillWidth: true
        ColumnLayout {
            width: parent.width
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: spec.heading
                    color: Theme.text
                    font.pixelSize: Theme.titleSize
                    font.weight: Font.DemiBold
                }
                VButton {
                    text: spec.copied ? backend.text("copied") : backend.text("copy")
                    onClicked: {
                        backend.copyText(page.rowsText(spec.rows));
                        spec.copied = true;
                    }
                }
            }
            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 24
                rowSpacing: 8
                Repeater {
                    model: spec.rows.length * 2
                    delegate: Label {
                        required property int index
                        readonly property bool isKey: index % 2 === 0
                        Layout.preferredWidth: isKey ? 170 : -1
                        Layout.fillWidth: !isKey
                        Layout.alignment: Qt.AlignTop
                        readonly property string value: spec.rows[Math.floor(index / 2)][isKey ? 0 : 1]
                        text: isKey ? value : page.linked(value)
                        textFormat: isKey ? Text.PlainText : Text.StyledText
                        linkColor: Theme.accent
                        color: isKey ? Theme.subtext : Theme.text
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                        onLinkActivated: link => Qt.openUrlExternally(link)
                        HoverHandler {
                            enabled: parent.hoveredLink !== ""
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        RowLayout {
            width: parent.width
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    text: page.about.pcName
                    color: Theme.text
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: page.about.model
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                }
            }
            VButton {
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                text: backend.text("rename_pc")
                onClicked: renameDialog.open()
            }
        }
    }

    SpecCard {
        heading: backend.text("device_specs")
        rows: page.deviceRows
    }
    SpecCard {
        heading: backend.text("os_specs")
        rows: page.osRows
    }

    Popup {
        id: renameDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 420
        modal: true
        focus: true
        padding: 24
        onOpened: {
            nameField.text = page.about.pcName;
            nameField.selectAll();
            nameField.forceActiveFocus();
        }
        background: Rectangle {
            radius: Theme.radius
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder
        }
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: backend.text("rename_pc")
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }
            TextField {
                id: nameField
                Layout.fillWidth: true
                maximumLength: 63
                onAccepted: okButton.clicked()
            }
            Label {
                Layout.fillWidth: true
                text: backend.text("rename_hint")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                VButton {
                    id: okButton
                    primary: true
                    text: backend.text("ok")
                    enabledState: nameField.text.trim().length > 0
                    onClicked: {
                        if (backend.renamePc(nameField.text))
                            renameDialog.close();
                    }
                }
                VButton {
                    text: backend.text("cancel")
                    onClicked: renameDialog.close()
                }
            }
        }
    }
}
