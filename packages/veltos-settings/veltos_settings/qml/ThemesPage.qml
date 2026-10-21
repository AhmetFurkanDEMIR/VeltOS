// Personalization > Themes, like Windows 11's: a preview of the desktop with
// what the theme is made of (background, colour, sounds, mouse cursor), the
// themes to choose from, and related settings.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    signal itemActivated(var item)
    signal openSubPage(string pageId, string subPage)

    readonly property var personal: backend.personal
    readonly property var theme: {
        for (const t of backend.themes) {
            if (t.id === backend.currentTheme)
                return t;
        }
        return null;
    }
    readonly property var wallpaper: {
        const current = personal.wallpaper || "VeltOS";
        const id = current.split("/").filter(part => part.length > 0).pop();
        for (const w of personal.wallpapers || []) {
            if (w.name === id)
                return w;
        }
        return null;
    }
    readonly property string previewUrl: wallpaper ? "file://" + (Theme.dark ? wallpaper.previewDark : wallpaper.preview)
                                         : /^\/.*\.(png|jpe?g|webp|avif|jxl)$/i.test(personal.wallpaper || "")
                                           ? "file://" + personal.wallpaper : ""
    readonly property string colourName: {
        if (theme)
            return theme.colour;
        const accent = (personal.accent || "#2F5EE6").toUpperCase();
        for (const t of backend.themes) {
            if (t.accent.toUpperCase() === accent)
                return t.colour;
        }
        return backend.text("custom");
    }
    property bool expanded: true

    spacing: 4
    Component.onCompleted: backend.refreshPersonal()

    // One part of the theme: icon, name and value; opens its page.
    component Part: RowLayout {
        id: part
        property string icon
        property string title
        property string value
        signal clicked()
        spacing: 14
        Accessible.role: Accessible.Button
        Accessible.name: title
        Kirigami.Icon {
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
            Layout.alignment: Qt.AlignTop
            source: part.icon
            isMask: true
            color: Theme.accent
        }
        ColumnLayout {
            spacing: 1
            Label {
                text: part.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
            }
            Label {
                text: part.value
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
            }
        }
        HoverHandler { cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: part.clicked() }
    }

    // --- The current theme --------------------------------------------------------
    RowLayout {
        Layout.fillWidth: true
        Layout.bottomMargin: 20
        spacing: 32

        // A small monitor: the wallpaper with a window in the theme's colours.
        Rectangle {
            Layout.preferredWidth: 252
            Layout.preferredHeight: 146
            radius: 10
            color: "#0B0B0D"
            Rectangle {
                anchors.fill: parent
                anchors.margins: 6
                radius: 5
                clip: true
                color: Theme.dark ? "#0E1846" : "#CFE0FF"
                Image {
                    anchors.fill: parent
                    source: page.previewUrl
                    fillMode: Image.PreserveAspectCrop
                    sourceSize.width: 480
                    asynchronous: true
                }
                Rectangle {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: 14
                    anchors.topMargin: 12
                    width: parent.width * 0.4
                    height: parent.height * 0.72
                    radius: 3
                    color: Theme.dark ? "#202230" : "#F7F8FB"
                    opacity: 0.95
                    Column {
                        x: 10
                        y: 12
                        spacing: 6
                        Repeater {
                            model: 4
                            Rectangle {
                                required property int index
                                width: index === 3 ? 30 : 64
                                height: 2
                                color: Theme.subtext
                                opacity: 0.6
                            }
                        }
                    }
                    Rectangle {
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 10
                        width: 26
                        height: 8
                        radius: 2
                        color: Theme.accent
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            columns: 2
            columnSpacing: 40
            rowSpacing: 18
            Part {
                icon: "preferences-desktop-wallpaper-symbolic"
                title: backend.text("theme_background")
                value: page.wallpaper ? page.wallpaper.title
                       : (page.personal.wallpaper || "").split("/").pop() || backend.text("custom_picture")
                onClicked: page.openSubPage("personalization", "background")
            }
            Part {
                icon: "preferences-color-symbolic"
                title: backend.text("theme_colour")
                value: page.colourName
                onClicked: page.openSubPage("personalization", "colours")
            }
            Part {
                icon: "audio-volume-high-symbolic"
                title: backend.text("theme_sounds")
                value: backend.text("veltos_default")
                onClicked: page.openSubPage("system", "sound")
            }
            Part {
                icon: "input-mouse-symbolic"
                title: backend.text("theme_cursor")
                value: backend.text("veltos_default")
                onClicked: page.openSubPage("devices", "mouse")
            }
        }
    }

    // --- Themes to choose from ------------------------------------------------------
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: themesColumn.implicitHeight
        radius: Theme.radius
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder

        ColumnLayout {
            id: themesColumn
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 68
                Layout.leftMargin: 18
                Layout.rightMargin: 18
                spacing: 16
                Kirigami.Icon {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    source: "preferences-desktop-theme-symbolic"
                    fallback: "applications-graphics-symbolic"
                    isMask: true
                    color: Theme.text
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: backend.text("current_theme")
                        color: Theme.text
                        font.pixelSize: Theme.titleSize
                    }
                    Label {
                        Layout.fillWidth: true
                        text: backend.text("current_theme_desc")
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        elide: Text.ElideRight
                    }
                }
                Label {
                    text: page.theme ? page.theme.title : backend.text("custom")
                    color: Theme.text
                    font.pixelSize: Theme.titleSize
                }
                Kirigami.Icon {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    source: page.expanded ? "go-up" : "go-down"
                    isMask: true
                    color: Theme.subtext
                }
                HoverHandler { cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: page.expanded = !page.expanded }
            }
            Rectangle {
                visible: page.expanded
                Layout.fillWidth: true
                height: 1
                color: Theme.cardBorder
            }
            Flow {
                visible: page.expanded
                Layout.fillWidth: true
                Layout.leftMargin: 56
                Layout.rightMargin: 18
                Layout.topMargin: 22
                Layout.bottomMargin: 10
                spacing: 10
                Repeater {
                    model: backend.themes
                    delegate: ThemeTile {
                        required property var modelData
                        theme: modelData
                        width: 118
                        height: 96
                    }
                }
            }
            Label {
                visible: page.expanded
                Layout.fillWidth: true
                Layout.leftMargin: 56
                Layout.rightMargin: 18
                Layout.bottomMargin: 18
                text: backend.text("theme_note")
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.WordWrap
            }
        }
    }

    SectionLabel {
        text: backend.text("related_settings")
    }
    SettingCard {
        Layout.fillWidth: true
        icon: "preferences-desktop-accessibility-symbolic"
        title: backend.text("contrast_themes")
        description: backend.text("contrast_themes_desc")
        onActivated: page.openSubPage("accessibility", "accessibility")
    }
}
