// Accessibility > Mouse pointer: Windows 11's "Mouse pointer and touch"
// page (pointer.py): the pointer style, recommended colours for a custom
// pointer, and its size. "Colour mode" (the default) follows light and
// dark mode (product owner, 2026-10-31).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ColumnLayout {
    id: page

    readonly property var p: backend.prefs
    signal itemActivated(var item)

    spacing: 4
    Component.onCompleted: backend.refreshPrefs()

    SettingRow {
        Layout.fillWidth: true
        icon: "input-mouse-symbolic"
        title: backend.text("pointer_style")
        description: page.pointerStyle === "theme" ? backend.text("pointer_theme_desc")
                                                    : backend.text("pointer_style_desc")
        wrapControl: true

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12

            Flow {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    model: [
                        { style: "theme", label: backend.text("pointer_theme") },
                        { style: "white", label: backend.text("pointer_white") },
                        { style: "black", label: backend.text("pointer_black") },
                        { style: "custom", label: backend.text("pointer_custom") }
                    ]
                    delegate: Rectangle {
                        id: tile
                        required property var modelData
                        readonly property bool chosen: page.pointerStyle === modelData.style
                        width: 92
                        height: 92
                        radius: Theme.radius
                        color: hover.hovered ? Theme.cardHover : Theme.control
                        border.width: chosen || activeFocus ? 2 : 1
                        border.color: chosen || activeFocus ? Theme.accent : Theme.cardBorder
                        activeFocusOnTab: true
                        opacity: page.p.loaded === true ? 1 : 0.45
                        Accessible.role: Accessible.RadioButton
                        Accessible.name: modelData.label
                        Accessible.checked: chosen
                        Keys.onSpacePressed: page.choosePointer(modelData.style)
                        Keys.onReturnPressed: page.choosePointer(modelData.style)

                        // "Colour mode": the light desktop's pointer on light,
                        // the dark desktop's on dark.
                        Rectangle {
                            visible: tile.modelData.style === "theme"
                            x: 1
                            y: 1
                            width: (parent.width - 2) / 2
                            height: 62
                            topLeftRadius: Theme.radius - 1
                            color: "#F3F3F3"
                        }
                        Rectangle {
                            visible: tile.modelData.style === "theme"
                            x: parent.width / 2
                            y: 1
                            width: (parent.width - 2) / 2
                            height: 62
                            topRightRadius: Theme.radius - 1
                            color: "#202020"
                        }
                        Row {
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: tile.modelData.style === "theme" ? 17 : 13
                            spacing: tile.modelData.style === "theme" ? 22 : 0
                            PointerGlyph {
                                width: tile.modelData.style === "theme" ? 24 : 40
                                height: tile.modelData.style === "theme" ? 30 : 40
                                body: tile.modelData.style === "white" ? "#FFFFFF"
                                    : tile.modelData.style === "custom" ? page.customColour
                                    : "#333333"
                                edge: tile.modelData.style === "white"
                                      || (tile.modelData.style === "custom" && !page.darkColour(page.customColour))
                                      ? "#21232B" : "#FFFFFF"
                            }
                            PointerGlyph {
                                visible: tile.modelData.style === "theme"
                                width: 24
                                height: 30
                                body: "#FFFFFF"
                                edge: "#21232B"
                            }
                        }
                        Label {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 8
                            width: parent.width - 8
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            text: tile.modelData.label
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                        }
                        HoverHandler {
                            id: hover
                            cursorShape: Qt.PointingHandCursor
                        }
                        TapHandler {
                            gesturePolicy: TapHandler.ReleaseWithinBounds
                            onTapped: page.choosePointer(tile.modelData.style)
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                visible: page.pointerStyle === "custom"
                spacing: 8
                Label {
                    text: backend.text("pointer_colours")
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: page.p.pointerColours || []
                        delegate: Rectangle {
                            id: swatch
                            required property string modelData
                            readonly property bool chosen: page.customColour.toUpperCase() === modelData.toUpperCase()
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
                            Keys.onSpacePressed: backend.setPointerStyle("custom", modelData)
                            Keys.onReturnPressed: backend.setPointerStyle("custom", modelData)
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 3
                                radius: 3
                                color: "transparent"
                                border.width: swatch.chosen ? 1 : 0
                                border.color: page.darkColour(swatch.modelData) ? "#FFFFFF" : "#000000"
                            }
                            HoverHandler { cursorShape: Qt.PointingHandCursor }
                            TapHandler { onTapped: backend.setPointerStyle("custom", swatch.modelData) }
                        }
                    }
                }
            }
        }
    }
    SettingRow {
        Layout.fillWidth: true
        icon: "zoom-in-symbolic"
        title: backend.text("pointer_size")
        wrapControl: true
        VSlider {
            id: pointerSize
            Layout.fillWidth: true
            from: 1
            to: page.p.pointerSizes || 7
            stepSize: 1
            value: page.p.pointerSize || 1
            enabledState: page.p.loaded === true
            accessibleName: backend.text("pointer_size")
            onReleased: v => backend.setPointerSize(Math.round(v))
        }
        Label {
            text: Math.round(pointerSize.value)
            color: Theme.text
            font.pixelSize: Theme.titleSize
        }
    }

    readonly property string pointerStyle: p.pointerStyle || "theme"
    readonly property string customColour: p.pointerColour || (p.pointerColours ? p.pointerColours[0] : "#B4FF00")

    function darkColour(colour) {
        const c = Qt.color(colour);
        return 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b < 90 / 255;
    }

    function choosePointer(style) {
        if (p.loaded !== true)
            return;
        backend.setPointerStyle(style, style === "custom" ? customColour : "");
    }
}
