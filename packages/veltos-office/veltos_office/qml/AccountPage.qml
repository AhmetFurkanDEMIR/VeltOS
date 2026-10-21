// Account: the user's picture and name, the Office theme, product information.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import org.kde.kirigami as Kirigami
import "."

Flickable {
    id: page

    function entrance() {
        titleReveal.play();
        bodyReveal.play();
    }
    onVisibleChanged: if (visible) entrance()
    Component.onCompleted: entrance()

    contentWidth: width
    contentHeight: column.height
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { }

    readonly property int sideMargin: Math.round(40 * Math.min(1.4, Theme.textScale))

    component SectionTitle: Text {
        color: Theme.text
        font.pixelSize: Theme.sectionFont
        font.weight: Font.DemiBold
        renderType: Text.NativeRendering
    }

    Column {
        id: column
        x: page.sideMargin
        width: page.width - 2 * page.sideMargin
        topPadding: Math.round(28 * Theme.textScale)
        bottomPadding: 32
        spacing: 0

        Reveal {
            id: titleReveal
            width: parent.width
            height: title.implicitHeight
            Text {
                id: title
                text: backend.text("account")
                color: Theme.text
                font.pixelSize: Theme.greetingFont
                font.weight: Font.DemiBold
                renderType: Text.NativeRendering
            }
        }

        Item { width: 1; height: Math.round(28 * Theme.textScale) }

        Reveal {
            id: bodyReveal
            delay: 60
            width: parent.width
            height: body.height
            RowLayout {
                id: body
                width: parent.width
                spacing: Math.round(48 * Theme.textScale)

                // User information and the theme.
                ColumnLayout {
                    Layout.alignment: Qt.AlignTop
                    Layout.preferredWidth: Math.round(360 * Theme.textScale)
                    spacing: 10
                    SectionTitle { text: backend.text("user_information") }
                    RowLayout {
                        spacing: 16
                        Layout.topMargin: 6
                        Item {
                            Layout.preferredWidth: 72
                            Layout.preferredHeight: 72
                            Rectangle {
                                anchors.fill: parent
                                radius: width / 2
                                color: Theme.brand
                                Glyph {
                                    anchors.centerIn: parent
                                    width: 34
                                    height: 34
                                    kind: "account"
                                    color: "#FFFFFF"
                                    lineWidth: 1.6
                                }
                            }
                            Image {
                                id: photo
                                anchors.fill: parent
                                source: backend.userPicture
                                visible: false
                                fillMode: Image.PreserveAspectCrop
                                sourceSize.width: 144
                                sourceSize.height: 144
                            }
                            Rectangle {
                                id: photoMask
                                anchors.fill: parent
                                radius: width / 2
                                visible: false
                            }
                            OpacityMask {
                                anchors.fill: parent
                                source: photo
                                maskSource: photoMask
                                visible: backend.userPicture !== "" && photo.status === Image.Ready
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: backend.userName
                                color: Theme.text
                                font.pixelSize: Theme.sectionFont
                                font.weight: Font.DemiBold
                                renderType: Text.NativeRendering
                            }
                            Text {
                                text: backend.text("local_account")
                                color: Theme.subtext
                                font.pixelSize: Theme.smallFont
                                renderType: Text.NativeRendering
                            }
                            Text {
                                Layout.topMargin: 4
                                text: backend.text("manage_account")
                                color: Theme.link
                                font.pixelSize: Theme.smallFont
                                font.underline: manageHover.hovered
                                renderType: Text.NativeRendering
                                HoverHandler { id: manageHover; cursorShape: Qt.PointingHandCursor }
                                TapHandler { onTapped: backend.openAccount() }
                            }
                        }
                    }

                    SectionTitle { Layout.topMargin: 28; text: backend.text("office_theme") }
                    Rectangle {
                        Layout.preferredWidth: Math.round(260 * Theme.textScale)
                        Layout.preferredHeight: Math.round(32 * Theme.textScale)
                        radius: Theme.radius
                        color: Theme.field
                        border.width: 1
                        border.color: Theme.fieldBorder
                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            text: backend.text("theme_system") + " — " + backend.text(Theme.dark ? "theme_dark" : "theme_colorful")
                            color: Theme.text
                            font.pixelSize: Theme.fontSize
                            renderType: Text.NativeRendering
                        }
                    }
                    Text {
                        Layout.preferredWidth: Math.round(360 * Theme.textScale)
                        text: backend.text("theme_note")
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont
                        wrapMode: Text.Wrap
                        renderType: Text.NativeRendering
                    }
                }

                // Product information.
                ColumnLayout {
                    Layout.alignment: Qt.AlignTop
                    Layout.fillWidth: true
                    spacing: 10
                    SectionTitle { text: backend.text("product_information") }
                    RowLayout {
                        spacing: 16
                        Layout.topMargin: 6
                        Kirigami.Icon {
                            Layout.preferredWidth: 56
                            Layout.preferredHeight: 56
                            source: backend.appIcon
                        }
                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: backend.text("office") + " · " + backend.appTitle
                                color: Theme.text
                                font.pixelSize: Theme.sectionFont
                                font.weight: Font.DemiBold
                                renderType: Text.NativeRendering
                            }
                            Text {
                                text: "LibreOffice " + backend.version
                                color: Theme.subtext
                                font.pixelSize: Theme.smallFont
                                renderType: Text.NativeRendering
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        Layout.maximumWidth: Math.round(420 * Theme.textScale)
                        text: backend.format("about_text", "version", backend.version)
                        color: Theme.subtext
                        font.pixelSize: Theme.smallFont
                        wrapMode: Text.Wrap
                        renderType: Text.NativeRendering
                    }
                }
            }
        }
    }
}
