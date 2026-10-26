// The local model in VeltOS AI's settings: the recommended small model
// (Gemma 3 270M, 185 MB, Turkish and English) with Download, the
// downloaded models (use, delete), more models from Hugging Face (search,
// a repository's GGUF files), and the download screen with its progress.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: localView
    spacing: 10

    readonly property var dl: backend.download
    readonly property var hub: backend.hub
    property string query: ""

    component Card: Rectangle {
        default property alias content: inner.data
        Layout.fillWidth: true
        implicitHeight: inner.implicitHeight + 24
        radius: 8
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        ColumnLayout {
            id: inner
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 12
            spacing: 6
        }
    }

    component LinkText: Text {
        signal activated()
        color: Theme.accent
        font.pixelSize: Theme.captionSize + 1
        font.underline: linkHover.hovered
        HoverHandler { id: linkHover; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: parent.activated() }
    }

    Text {
        Layout.fillWidth: true
        visible: !backend.localEngine
        text: backend.text("local_no_engine")
        color: Theme.danger
        font.pixelSize: Theme.bodySize
        wrapMode: Text.WordWrap
    }

    // --- the download screen ----------------------------------------------------------------------
    Card {
        objectName: "downloadCard"
        visible: localView.dl.active === true
        Text {
            Layout.fillWidth: true
            text: backend.text("downloading")
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
            font.weight: Font.DemiBold
        }
        Text {
            Layout.fillWidth: true
            text: localView.dl.title || ""
            color: Theme.subtext
            font.pixelSize: Theme.captionSize
            elide: Text.ElideMiddle
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: 4
            implicitHeight: 6
            radius: 3
            color: Theme.hover
            Rectangle {
                width: parent.width * (localView.dl.percent || 0) / 100
                height: parent.height
                radius: 3
                color: Theme.accent
                Behavior on width { NumberAnimation { duration: 200 } }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: (localView.dl.percent || 0) + "% · " + (localView.dl.progress || "")
                color: Theme.subtext
                font.pixelSize: Theme.captionSize
            }
            VButton {
                objectName: "cancelDownload"
                text: backend.text("cancel")
                onClicked: backend.cancelDownload()
            }
        }
    }
    Text {
        Layout.fillWidth: true
        visible: !localView.dl.active && (localView.dl.error || "") !== ""
        text: backend.text("download_failed") + " " + (localView.dl.error || "")
        color: Theme.danger
        font.pixelSize: Theme.captionSize
        wrapMode: Text.WordWrap
    }

    // --- the recommended model ----------------------------------------------------------------------
    Card {
        objectName: "defaultModel"
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Kirigami.Icon {
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                source: "veltos-ai"
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Text {
                    Layout.fillWidth: true
                    text: backend.localDefault.title + " · " + backend.localDefault.size
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    text: backend.text("local_default_desc")
                    color: Theme.subtext
                    font.pixelSize: Theme.captionSize
                    wrapMode: Text.WordWrap
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            VButton {
                objectName: "downloadDefault"
                visible: !backend.localDefault.installed
                primary: true
                enabledState: backend.localEngine && !localView.dl.active
                text: backend.text("download")
                onClicked: backend.downloadDefault()
            }
            VButton {
                visible: backend.localDefault.installed
                         && !(backend.provider === "local" && localView.activeFile === backend.localDefault.file)
                primary: true
                text: backend.text("use_model")
                onClicked: backend.useLocalModel(backend.localDefault.file)
            }
            Text {
                visible: backend.localDefault.installed && backend.provider === "local"
                         && localView.activeFile === backend.localDefault.file
                text: "✓ " + backend.text("in_use")
                color: Theme.success
                font.pixelSize: Theme.bodySize
            }
            Item { Layout.fillWidth: true }
            LinkText {
                text: backend.text("model_license")
                onActivated: backend.openUrl(backend.localDefault.license)
            }
        }
    }
    readonly property string activeFile: {
        const active = backend.localModels.find(m => m.active);
        return active ? active.file : "";
    }

    // --- downloaded models ----------------------------------------------------------------------------
    Text {
        visible: backend.localModels.length > 0
        Layout.topMargin: 4
        text: backend.text("downloaded_models")
        color: Theme.text
        font.pixelSize: Theme.bodySize
        font.weight: Font.DemiBold
    }
    Repeater {
        model: backend.localModels
        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: modelData.file + " · " + modelData.size
                color: Theme.text
                font.pixelSize: Theme.captionSize + 1
                elide: Text.ElideMiddle
            }
            Text {
                visible: modelData.active && backend.provider === "local"
                text: "✓ " + backend.text("in_use")
                color: Theme.success
                font.pixelSize: Theme.captionSize + 1
            }
            VButton {
                visible: !(modelData.active && backend.provider === "local")
                text: backend.text("use_model")
                onClicked: backend.useLocalModel(modelData.file)
            }
            IconButton {
                icon: "edit-delete"
                tip: backend.text("delete_model")
                onClicked: backend.deleteLocalModel(modelData.file)
            }
        }
    }

    // --- more models from Hugging Face ---------------------------------------------------------------
    Text {
        Layout.topMargin: 8
        text: backend.text("hub_title")
        color: Theme.text
        font.pixelSize: Theme.bodySize
        font.weight: Font.DemiBold
    }
    Text {
        Layout.fillWidth: true
        text: backend.text("hub_desc")
        color: Theme.subtext
        font.pixelSize: Theme.captionSize
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 34
            radius: 5
            color: Theme.field
            border.width: 1
            border.color: hubInput.activeFocus ? Theme.accent : Theme.fieldBorder
            TextInput {
                id: hubInput
                objectName: "hubSearch"
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                verticalAlignment: TextInput.AlignVCenter
                color: Theme.text
                font.pixelSize: Theme.bodySize
                selectByMouse: true
                clip: true
                onAccepted: backend.searchHub(text)
                Text {
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    visible: hubInput.text === ""
                    text: backend.text("hub_placeholder")
                    color: Theme.faint
                    font.pixelSize: Theme.bodySize
                    elide: Text.ElideRight
                }
            }
        }
        VButton {
            text: backend.text("search")
            enabledState: hubInput.text.trim() !== "" && !localView.hub.busy
            onClicked: backend.searchHub(hubInput.text)
        }
    }
    Text {
        visible: localView.hub.busy === true
        text: backend.text("loading_models")
        color: Theme.subtext
        font.pixelSize: Theme.captionSize
    }
    Text {
        Layout.fillWidth: true
        visible: (localView.hub.error || "") !== ""
        text: backend.text("hub_error")
        color: Theme.danger
        font.pixelSize: Theme.captionSize
        wrapMode: Text.WordWrap
    }
    // Search results: repositories.
    Repeater {
        model: (localView.hub.repo || "") === "" ? (localView.hub.results || []) : []
        delegate: Rectangle {
            required property var modelData
            Layout.fillWidth: true
            implicitHeight: 38
            radius: 5
            color: repoHover.hovered ? Theme.hover : "transparent"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                Text {
                    Layout.fillWidth: true
                    text: modelData.repo
                    color: Theme.text
                    font.pixelSize: Theme.captionSize + 1
                    elide: Text.ElideMiddle
                }
                Text {
                    text: "↓ " + modelData.downloads
                    color: Theme.faint
                    font.pixelSize: Theme.captionSize
                }
            }
            HoverHandler { id: repoHover; cursorShape: Qt.PointingHandCursor }
            TapHandler {
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: backend.openHubRepo(modelData.repo)
            }
        }
    }
    // A repository's GGUF files.
    RowLayout {
        visible: (localView.hub.repo || "") !== ""
        Layout.fillWidth: true
        IconButton {
            icon: "go-previous"
            tip: backend.text("back")
            onClicked: backend.closeHubRepo()
        }
        Text {
            Layout.fillWidth: true
            text: localView.hub.repo || ""
            color: Theme.text
            font.pixelSize: Theme.bodySize
            font.weight: Font.DemiBold
            elide: Text.ElideMiddle
        }
    }
    Repeater {
        model: (localView.hub.repo || "") !== "" ? (localView.hub.files || []) : []
        delegate: RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: modelData.file + " · " + modelData.sizeText
                color: Theme.text
                font.pixelSize: Theme.captionSize + 1
                elide: Text.ElideMiddle
            }
            VButton {
                text: backend.text("download")
                enabledState: backend.localEngine && !localView.dl.active
                onClicked: backend.downloadHub(localView.hub.repo, modelData.file, modelData.sizeValue,
                                               modelData.sha256 || "")
            }
        }
    }

    Text {
        Layout.fillWidth: true
        Layout.topMargin: 6
        text: backend.text("local_note")
        color: Theme.faint
        font.pixelSize: Theme.captionSize
        wrapMode: Text.WordWrap
    }
}
