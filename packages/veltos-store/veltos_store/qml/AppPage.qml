// An app's page, Microsoft Store layout: a card with the icon, name,
// publisher and the Install / Open button on the left; screenshots,
// description and details on the right.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: page
    property string appId: ""
    signal back()
    signal opened(string appId)

    readonly property var app: {
        backend.appCount;
        return backend.details(appId);
    }
    readonly property string appState: backend.state(app.pkg || "", backend.revision)
    // Screenshots that could not be loaded (old catalogue addresses) are
    // left out; without any, the section is hidden.
    property int shotErrors: 0
    onAppIdChanged: shotErrors = 0
    readonly property bool hasShots: (app.screenshots || []).length > shotErrors

    Rectangle {
        anchors.fill: parent
        color: Theme.pane
    }

    // Back button.
    MouseArea {
        id: backButton
        x: 16
        y: 14
        width: 36
        height: 32
        hoverEnabled: true
        onClicked: page.back()
        Accessible.role: Accessible.Button
        Accessible.name: backend.texts.back
        Rectangle {
            anchors.fill: parent
            radius: Theme.smallRadius
            color: backButton.containsMouse ? Theme.navHover : "transparent"
        }
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 16
            height: 16
            source: "go-previous-symbolic"
            isMask: true
            color: Theme.text
        }
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        anchors.topMargin: 52
        contentWidth: availableWidth
        clip: true

        RowLayout {
            width: scroll.availableWidth
            spacing: 24

            // Left: the app card.
            Rectangle {
                Layout.alignment: Qt.AlignTop
                Layout.leftMargin: 32
                Layout.preferredWidth: 320
                Layout.preferredHeight: card.implicitHeight + 48
                radius: Theme.radius
                color: Theme.card
                border.width: 1
                border.color: Theme.cardBorder

                ColumnLayout {
                    id: card
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 24
                    spacing: 8

                    AppIcon {
                        Layout.preferredWidth: 112
                        Layout.preferredHeight: 112
                        Layout.bottomMargin: 8
                        icon: page.app.icon || ""
                    }
                    Text {
                        Layout.fillWidth: true
                        text: page.app.name || ""
                        color: Theme.text
                        font.pixelSize: 24
                        font.weight: Font.DemiBold
                        wrapMode: Text.Wrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: page.app.developer || ""
                        color: Theme.accent
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                    Text {
                        Layout.fillWidth: true
                        text: page.app.summary || ""
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.Wrap
                    }
                    InstallButton {
                        Layout.fillWidth: true
                        Layout.topMargin: 12
                        pkg: page.app.pkg || ""
                        appId: page.appId
                    }
                    Text {
                        visible: backend.hasFailure(page.app.pkg || "", backend.revision)
                        Layout.fillWidth: true
                        text: backend.failureText(page.app.pkg || "", backend.revision)
                        color: Theme.danger
                        font.pixelSize: Theme.captionSize
                        wrapMode: Text.Wrap
                    }
                    VButton {
                        visible: page.appState === "installed"
                        Layout.fillWidth: true
                        text: backend.texts.uninstall
                        onClicked: backend.uninstall(page.app.pkg)
                    }
                    Text {
                        visible: backend.isProtected(page.app.pkg || "", backend.revision)
                        Layout.fillWidth: true
                        text: backend.texts.protected
                        color: Theme.danger
                        font.pixelSize: Theme.captionSize
                        wrapMode: Text.Wrap
                    }
                    Text {
                        visible: page.appState === "" || page.appState === "failed"
                        text: backend.texts.free
                        color: Theme.subtext
                        font.pixelSize: Theme.captionSize
                    }
                }
            }

            // Right: screenshots, description, information.
            ColumnLayout {
                Layout.alignment: Qt.AlignTop
                Layout.fillWidth: true
                Layout.rightMargin: 32
                Layout.bottomMargin: 32
                spacing: 14

                Text {
                    visible: page.hasShots
                    text: backend.texts.screenshots
                    color: Theme.text
                    font.pixelSize: Theme.sectionSize
                    font.weight: Font.DemiBold
                }
                ListView {
                    visible: page.hasShots
                    Layout.fillWidth: true
                    Layout.preferredHeight: 260
                    orientation: ListView.Horizontal
                    spacing: 12
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    model: page.app.screenshots || []
                    delegate: Rectangle {
                        required property string modelData
                        visible: shot.status !== Image.Error
                        width: shot.status === Image.Error ? 0
                             : Math.max(260, shot.status === Image.Ready
                                             ? shot.implicitWidth * height / Math.max(1, shot.implicitHeight) : 416)
                        height: 260
                        radius: Theme.radius
                        color: Theme.card
                        border.width: 1
                        border.color: Theme.cardBorder
                        clip: true
                        Image {
                            id: shot
                            anchors.fill: parent
                            anchors.margins: 1
                            source: parent.modelData
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                            cache: true
                            sourceSize.height: 520
                            onStatusChanged: if (status === Image.Error) page.shotErrors += 1
                        }
                        BusyIndicator {
                            anchors.centerIn: parent
                            running: shot.status === Image.Loading
                            visible: running
                        }
                    }
                }

                Text {
                    Layout.topMargin: 8
                    text: backend.texts.description
                    color: Theme.text
                    font.pixelSize: Theme.sectionSize
                    font.weight: Font.DemiBold
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: description.implicitHeight + 40
                    radius: Theme.radius
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    Text {
                        id: description
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 20
                        text: page.app.description || page.app.summary || ""
                        textFormat: Text.RichText
                        color: Theme.text
                        font.pixelSize: Theme.bodySize + 1
                        lineHeight: 1.2
                        wrapMode: Text.Wrap
                    }
                }

                Text {
                    Layout.topMargin: 8
                    text: backend.texts.more_info
                    color: Theme.text
                    font.pixelSize: Theme.sectionSize
                    font.weight: Font.DemiBold
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: info.implicitHeight + 40
                    radius: Theme.radius
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    GridLayout {
                        id: info
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 20
                        columns: 3
                        columnSpacing: 24
                        rowSpacing: 16
                        Repeater {
                            model: [
                                [backend.texts.published_by, page.app.developer || ""],
                                [backend.texts.category, page.app.category || ""],
                                [backend.texts.package, page.app.pkg || ""],
                                [backend.texts.license, page.app.license || ""],
                                [backend.texts.website, page.app.homepage || ""],
                            ].filter(row => row[1] !== "")
                            ColumnLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredWidth: 1
                                Layout.alignment: Qt.AlignTop
                                spacing: 2
                                Text {
                                    text: parent.modelData[0]
                                    color: Theme.text
                                    font.pixelSize: Theme.bodySize
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: parent.modelData[1]
                                    color: parent.modelData[1].startsWith("http") ? Theme.accent : Theme.subtext
                                    font.pixelSize: Theme.bodySize
                                    elide: Text.ElideRight
                                    MouseArea {
                                        anchors.fill: parent
                                        enabled: parent.text.startsWith("http")
                                        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                        onClicked: Qt.openUrlExternally(parent.text)
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
