// Settings, as a page of the window like Windows 11 Notepad's: app theme,
// font (family, style, size with a preview), word wrap, how files open and
// what happens at start, and "About this app".
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: page

    signal back()

    color: Theme.page

    component SectionTitle: Text {
        Layout.topMargin: 14
        Layout.bottomMargin: 2
        color: Theme.text
        font.pixelSize: 14
        font.weight: Font.DemiBold
    }

    component Card: Rectangle {
        id: card
        property string title
        property string description
        default property alias controls: controlsRow.data
        Layout.fillWidth: true
        implicitHeight: Math.max(66, cardRow.implicitHeight + 24)
        radius: 6
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        RowLayout {
            id: cardRow
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            spacing: 16
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: card.title
                    color: Theme.text
                    font.pixelSize: 14
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    visible: text !== ""
                    text: card.description
                    color: Theme.subtext
                    font.pixelSize: Theme.smallFont
                    wrapMode: Text.WordWrap
                }
            }
            RowLayout {
                id: controlsRow
                spacing: 8
            }
        }
    }

    component Choice: ComboBox {
        id: choice
        Layout.preferredWidth: 230
        implicitHeight: 32
        font.pixelSize: Theme.fontSize
        background: Rectangle {
            radius: 4
            color: choice.hovered ? Theme.hover : Theme.field
            border.width: 1
            border.color: choice.activeFocus ? Theme.accent : Theme.fieldBorder
        }
        contentItem: Text {
            leftPadding: 10
            rightPadding: 28
            text: choice.displayText
            color: Theme.text
            font: choice.font
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        indicator: Glyph {
            x: choice.width - width - 12
            y: (choice.height - height) / 2
            width: 10
            height: 10
            kind: "chevron-down"
        }
    }

    component Toggle: Rectangle {
        id: toggle
        property bool on: false
        signal toggled(bool on)
        implicitWidth: 40
        implicitHeight: 20
        radius: 10
        color: on ? Theme.accent : "transparent"
        border.width: on ? 0 : 1
        border.color: Theme.subtext
        Accessible.role: Accessible.CheckBox
        Accessible.checked: on
        Rectangle {
            width: toggle.on ? 12 : 10
            height: width
            radius: width / 2
            anchors.verticalCenter: parent.verticalCenter
            x: toggle.on ? parent.width - width - 4 : 5
            color: toggle.on ? Theme.accentText : Theme.subtext
            Behavior on x { NumberAnimation { duration: 120 } }
        }
        TapHandler { onTapped: toggle.toggled(!toggle.on) }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            width: Math.min(parent.width, 1000)
            x: Math.max(0, (parent.width - width) / 2)
            spacing: 4

            RowLayout {
                Layout.leftMargin: 32
                Layout.topMargin: 20
                Layout.bottomMargin: 10
                spacing: 14
                Rectangle {
                    implicitWidth: 34
                    implicitHeight: 32
                    radius: 4
                    color: backHover.hovered ? Theme.hover : "transparent"
                    Accessible.role: Accessible.Button
                    Accessible.name: backend.texts.back
                    Glyph {
                        anchors.centerIn: parent
                        width: 12
                        height: 12
                        kind: "back"
                    }
                    HoverHandler { id: backHover }
                    TapHandler { onTapped: page.back() }
                }
                Text {
                    text: backend.texts.settings
                    color: Theme.text
                    font.pixelSize: 28
                    font.weight: Font.DemiBold
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                Layout.bottomMargin: 32
                spacing: 4

                Card {
                    title: backend.texts.app_theme
                    description: backend.texts.app_theme_desc
                    Choice {
                        model: [backend.texts.theme_light, backend.texts.theme_dark, backend.texts.theme_system]
                        currentIndex: ["light", "dark", "system"].indexOf(backend.theme)
                        onActivated: index => backend.setTheme(["light", "dark", "system"][index])
                    }
                }

                SectionTitle { text: backend.texts.font }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: fontColumn.implicitHeight + 32
                    radius: 6
                    color: Theme.card
                    border.width: 1
                    border.color: Theme.cardBorder
                    ColumnLayout {
                        id: fontColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 10
                        GridLayout {
                            columns: 2
                            columnSpacing: 16
                            rowSpacing: 8
                            Text { text: backend.texts.font_family; color: Theme.text; font.pixelSize: Theme.fontSize }
                            Choice {
                                id: familyChoice
                                model: backend.fontFamilies
                                currentIndex: backend.fontFamilies.indexOf(backend.fontFamily)
                                onActivated: index => backend.setFont(backend.fontFamilies[index], backend.fontSize, backend.fontStyle)
                            }
                            Text { text: backend.texts.font_style; color: Theme.text; font.pixelSize: Theme.fontSize }
                            Choice {
                                readonly property var styles: ["regular", "italic", "bold", "bold_italic"]
                                model: [backend.texts.style_regular, backend.texts.style_italic,
                                        backend.texts.style_bold, backend.texts.style_bold_italic]
                                currentIndex: styles.indexOf(backend.fontStyle)
                                onActivated: index => backend.setFont(backend.fontFamily, backend.fontSize, styles[index])
                            }
                            Text { text: backend.texts.font_size; color: Theme.text; font.pixelSize: Theme.fontSize }
                            Choice {
                                readonly property var sizes: [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
                                model: sizes.map(String)
                                currentIndex: sizes.indexOf(backend.fontSize)
                                onActivated: index => backend.setFont(backend.fontFamily, sizes[index], backend.fontStyle)
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            Layout.topMargin: 6
                            text: backend.texts.font_preview
                            color: Theme.text
                            font.family: backend.fontFamily
                            font.pointSize: backend.fontSize
                            font.bold: backend.fontStyle.indexOf("bold") === 0
                            font.italic: backend.fontStyle.indexOf("italic") >= 0
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                SectionTitle { text: backend.texts.text_formatting }
                Card {
                    title: backend.texts.word_wrap
                    description: backend.texts.word_wrap_desc
                    Toggle {
                        on: backend.wordWrap
                        onToggled: on => backend.setWordWrap(on)
                    }
                }

                SectionTitle { text: backend.texts.opening_notepad }
                Card {
                    title: backend.texts.opening_files
                    Choice {
                        model: [backend.texts.open_in_tab, backend.texts.open_in_window]
                        currentIndex: backend.openInNewWindow ? 1 : 0
                        onActivated: index => backend.setOpenInNewWindow(index === 1)
                    }
                }
                Card {
                    title: backend.texts.when_starts
                    Choice {
                        Layout.preferredWidth: 300
                        model: [backend.texts.continue_session, backend.texts.new_session]
                        currentIndex: backend.continueSession ? 0 : 1
                        onActivated: index => backend.setContinueSession(index === 0)
                    }
                }

                SectionTitle { text: backend.texts.about_this_app }
                Card {
                    title: backend.texts.app_title
                    description: backend.texts.about_text.replace("{version}", backend.version)
                }
            }
        }
    }
}
