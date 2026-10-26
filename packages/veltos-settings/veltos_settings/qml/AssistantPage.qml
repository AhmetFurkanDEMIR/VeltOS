// Apps > VeltOS AI: open the assistant, its taskbar button, the AI service
// with the user's own API key and model, and whether it may act on the PC
// (veltos-ai's settings file; keys never reach this page, only "saved").
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var a: backend.assistant
    // The service shown below; the chosen one at first.
    property string service: ""
    readonly property string shownService: service !== "" ? service : (a.provider || "openai")
    readonly property var entry: (a.services || {})[shownService] || ({})
    readonly property var info: (a.providers || []).find(p => p.value === shownService) || ({})
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: {
        backend.refreshAssistant();
        backend.refreshTaskbar();
    }

    // The assistant itself, like the top of Windows 11's app pages.
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: header.implicitHeight + 36
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        RowLayout {
            id: header
            anchors.fill: parent
            anchors.margins: 18
            spacing: 18
            Kirigami.Icon {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                source: "veltos-ai"
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Label {
                    text: backend.text("ai_title")
                    color: Theme.text
                    font.pixelSize: Theme.titleSize + 4
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: backend.text("ai_desc")
                    color: Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
                Label {
                    Layout.fillWidth: true
                    visible: page.a.loaded === true && page.a.available === true
                    text: page.a.ready
                          ? backend.format("ai_ready", ((page.a.providers || []).find(p => p.value === page.a.provider) || {}).label || "")
                          : backend.text("ai_not_ready")
                    color: page.a.ready ? Theme.accent : Theme.subtext
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
            }
            VButton {
                primary: true
                text: backend.text("ai_open")
                enabledState: page.a.available === true
                onClicked: backend.openAssistant()
            }
        }
    }

    Card {
        Layout.fillWidth: true
        visible: page.a.loaded === true && page.a.available !== true
        Label {
            width: parent.width
            text: backend.text("ai_missing")
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.WordWrap
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "view-dual-symbolic"
        title: backend.text("ai_taskbar")
        ToggleSwitch {
            checked: backend.taskbar.aiButton !== false
            enabledState: backend.taskbar.available === true
            accessibleName: backend.text("ai_taskbar")
            onToggled: on => backend.setTaskbar("aiButton", on)
        }
    }

    SectionLabel {
        visible: page.a.available === true
        text: backend.text("ai_service")
    }
    SettingRow {
        Layout.fillWidth: true
        visible: page.a.available === true
        icon: "network-server-symbolic"
        title: backend.text("ai_service")
        description: backend.text("ai_service_desc")
        VComboBox {
            Layout.preferredWidth: 280
            accessibleName: backend.text("ai_service")
            options: page.a.providers || []
            currentValue: page.shownService
            onActivated: value => {
                page.service = value;
                keyField.text = "";
                modelField.text = (page.entry.model || "");
                endpointField.text = (page.entry.endpoint || "");
            }
        }
    }

    // The chosen service's key, model and (Azure) endpoint.
    Rectangle {
        Layout.fillWidth: true
        visible: page.a.available === true
        implicitHeight: form.implicitHeight + 36
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder

        ColumnLayout {
            id: form
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 18
            spacing: 6

            Label { text: backend.text("ai_key"); color: Theme.text; font.pixelSize: Theme.bodySize }
            RowLayout {
                spacing: 8
                VTextField {
                    id: keyField
                    Layout.preferredWidth: 360
                    password: true
                    placeholder: page.entry.hasKey ? "••••••••••••" : "sk-…"
                }
                VButton {
                    text: backend.text("ai_get_key")
                    visible: (page.info.keysUrl || "") !== ""
                    onClicked: Qt.openUrlExternally(page.info.keysUrl)
                }
            }
            Label {
                Layout.fillWidth: true
                text: page.entry.hasKey ? backend.text("ai_key_saved") : backend.text("ai_key_missing")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.topMargin: 6
                text: page.shownService === "copilot" ? backend.text("ai_deployment") : backend.text("ai_model")
                color: Theme.text
                font.pixelSize: Theme.bodySize
            }
            VTextField {
                id: modelField
                Layout.preferredWidth: 360
                text: page.entry.model || ""
                placeholder: page.info.defaultModel || ""
            }
            Label {
                Layout.topMargin: 6
                visible: page.shownService === "copilot"
                text: backend.text("ai_endpoint")
                color: Theme.text
                font.pixelSize: Theme.bodySize
            }
            VTextField {
                id: endpointField
                Layout.preferredWidth: 360
                visible: page.shownService === "copilot"
                text: page.entry.endpoint || ""
                placeholder: "https://<resource>.openai.azure.com/"
            }
            RowLayout {
                Layout.topMargin: 8
                spacing: 8
                VButton {
                    primary: true
                    text: backend.text("save")
                    enabledState: page.entry.hasKey === true || keyField.text.trim().length > 0
                    onClicked: {
                        backend.saveAiService(page.shownService, keyField.text, modelField.text, endpointField.text);
                        keyField.text = "";
                    }
                }
                VButton {
                    visible: page.entry.hasKey === true
                    text: backend.text("ai_remove_key")
                    onClicked: backend.removeAiKey(page.shownService)
                }
            }
            Label {
                Layout.fillWidth: true
                visible: page.a.saveFailed === true
                text: backend.text("ai_save_failed")
                color: Theme.danger
                font.pixelSize: Theme.bodySize
            }
            Label {
                Layout.fillWidth: true
                Layout.topMargin: 4
                text: backend.text("ai_storage_note")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }
    }

    SettingRow {
        Layout.fillWidth: true
        Layout.topMargin: 10
        visible: page.a.available === true
        icon: "dialog-ok-apply-symbolic"
        title: backend.text("ai_actions")
        description: backend.text("ai_actions_desc")
        ToggleSwitch {
            checked: page.a.actions !== false
            accessibleName: backend.text("ai_actions")
            onToggled: on => backend.setAiActions(on)
        }
    }
}
