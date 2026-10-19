// VeltOS live session welcome window (see veltos-live-welcome).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: root

    readonly property bool dark: palette.window.hslLightness < 0.5
    readonly property color accent: dark ? "#4F7CFF" : "#2F5EE6"
    readonly property color cardColor: dark ? "#2B2D3A" : "#FFFFFF"
    readonly property color cardBorder: dark ? "#3A3D4E" : "#E3E6EE"
    readonly property color subtle: dark ? "#B7BDD0" : "#5B6275"

    title: "VeltOS"
    width: 900
    height: 560
    minimumWidth: 760
    minimumHeight: 520
    visible: true
    color: dark ? "#1E1F29" : "#F3F5FA"

    component Choice: Rectangle {
        id: card

        property string heading
        property string body
        property string iconName
        signal chosen()

        Layout.fillWidth: true
        Layout.preferredHeight: 230
        radius: 12
        color: hover.hovered || activeFocus ? Qt.tint(root.cardColor, Qt.rgba(0.31, 0.49, 1, 0.08))
                                            : root.cardColor
        border.width: activeFocus ? 2 : 1
        border.color: activeFocus || hover.hovered ? root.accent : root.cardBorder
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: heading
        Accessible.description: body
        Accessible.onPressAction: chosen()
        Keys.onReturnPressed: chosen()
        Keys.onEnterPressed: chosen()
        Keys.onSpacePressed: chosen()

        Behavior on color { ColorAnimation { duration: 120 } }

        HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: card.chosen() }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 56
                Layout.preferredHeight: 56
                radius: 28
                color: root.dark ? "#3A3D4E" : "#EEF1F8"

                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 32
                    height: 32
                    source: card.iconName
                }
            }
            Label {
                text: card.heading
                font.pixelSize: 20
                font.weight: Font.DemiBold
                color: root.palette.windowText
            }
            Label {
                Layout.fillWidth: true
                text: card.body
                wrapMode: Text.WordWrap
                font.pixelSize: 14
                lineHeight: 1.15
                color: root.subtle
            }
            Item { Layout.fillHeight: true }
        }
    }

    // Language of the live session (it signs in again in that language).
    Row {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 16
        spacing: 6
        z: 1

        Repeater {
            model: [{ code: "en", name: "English" }, { code: "tr", name: "Türkçe" }]
            delegate: Rectangle {
                required property var modelData
                readonly property bool current: welcome.language() === modelData.code
                width: label.implicitWidth + 24
                height: 30
                radius: 15
                color: current ? root.accent : (langHover.hovered ? root.cardColor : "transparent")
                border.width: current ? 0 : 1
                border.color: root.cardBorder
                activeFocusOnTab: !current
                Accessible.role: Accessible.Button
                Accessible.name: modelData.name
                Keys.onReturnPressed: if (!current) welcome.switchLanguage(modelData.code)
                Label {
                    id: label
                    anchors.centerIn: parent
                    text: modelData.name
                    color: parent.current ? "#FFFFFF" : root.palette.windowText
                    font.pixelSize: 13
                }
                HoverHandler { id: langHover; enabled: !parent.current; cursorShape: Qt.PointingHandCursor }
                TapHandler { enabled: !parent.current; onTapped: welcome.switchLanguage(modelData.code) }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 48
        spacing: 0

        Image {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 72
            Layout.preferredHeight: 72
            sourceSize: Qt.size(144, 144)
            source: welcome.logo()
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 18
            text: welcome.text("title")
            font.pixelSize: 30
            font.weight: Font.DemiBold
            color: root.palette.windowText
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 6
            text: welcome.text("tagline")
            font.pixelSize: 15
            color: root.subtle
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 36
            spacing: 20

            Choice {
                id: tryCard
                heading: welcome.text("try")
                body: welcome.text("try_body")
                iconName: "computer"
                onChosen: welcome.close()
            }
            Choice {
                id: installCard
                focus: true
                heading: welcome.text("install")
                body: welcome.text("install_body")
                iconName: "system-software-install"
                onChosen: welcome.install()
            }
        }

        Item { Layout.fillHeight: true }

        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: welcome.text("later")
            font.pixelSize: 13
            color: root.subtle
        }
    }

    Component.onCompleted: installCard.forceActiveFocus()
}
