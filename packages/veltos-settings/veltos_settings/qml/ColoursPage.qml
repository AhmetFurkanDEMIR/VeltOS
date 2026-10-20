// Personalization > Colours: light or dark mode and the accent colour.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var personal: backend.personal
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPersonal()

    SettingRow {
        Layout.fillWidth: true
        icon: "applications-graphics-symbolic"
        title: backend.text("choose_mode")
        description: backend.text("choose_mode_desc")
        VComboBox {
            Layout.preferredWidth: 160
            accessibleName: backend.text("choose_mode")
            options: [{ label: backend.text("light"), value: false }, { label: backend.text("dark"), value: true }]
            currentValue: backend.darkMode
            onActivated: value => backend.setDarkMode(value)
        }
    }

    SettingRow {
        Layout.fillWidth: true
        icon: "preferences-color-symbolic"
        title: backend.text("accent_colour")
        description: backend.text("accent_colour_desc")
        wrapControl: true

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10
            Flow {
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: page.personal.accents
                    delegate: Rectangle {
                        id: swatch
                        required property string modelData
                        required property int index
                        readonly property bool chosen: page.personal.accent !== ""
                                                       ? page.personal.accent.toUpperCase() === modelData.toUpperCase()
                                                       : index === 0
                        width: 40
                        height: 40
                        radius: 5
                        color: modelData
                        border.width: chosen || activeFocus ? 2 : 0
                        border.color: Theme.text
                        activeFocusOnTab: true
                        Accessible.role: Accessible.RadioButton
                        Accessible.name: modelData
                        Accessible.checked: chosen
                        Keys.onSpacePressed: backend.setAccent(modelData)
                        Keys.onReturnPressed: backend.setAccent(modelData)

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 3
                            radius: 3
                            color: "transparent"
                            border.width: swatch.chosen ? 1 : 0
                            border.color: "#FFFFFF"
                        }
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            width: 16
                            height: 16
                            visible: swatch.chosen
                            source: "checkmark"
                            color: "#FFFFFF"
                            isMask: true
                        }
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                        TapHandler { onTapped: backend.setAccent(swatch.modelData) }
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                text: backend.text("accent_note")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }
    }

}
