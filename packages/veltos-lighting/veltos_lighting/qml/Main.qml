// VeltOS Keyboard Lighting, in the layout of Windows 11's Dynamic Lighting
// (Settings > Personalization): the keyboard as a card, then rows with a
// switch, the brightness slider, effects, "Match my accent colour" and the
// colour swatches with a custom colour. `backend` is app.Backend.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ApplicationWindow {
    id: window
    width: 860
    height: 720
    minimumWidth: 560
    minimumHeight: 460
    visible: true
    title: backend.texts.app_title
    color: Theme.window

    readonly property var kb: backend.keyboard
    readonly property var pick: backend.choice
    readonly property bool present: backend.keyboards.length > 0
    readonly property bool coloured: present && kb.colorKind !== ""

    // Windows 11 toggle switch with its On/Off label on the left.
    component Toggle: Item {
        id: toggle
        property bool checked: false
        signal toggled(bool on)
        implicitWidth: label.implicitWidth + 52
        implicitHeight: 24
        activeFocusOnTab: true
        Accessible.role: Accessible.CheckBox
        Accessible.checked: checked
        Keys.onSpacePressed: toggled(!checked)
        Label {
            id: label
            anchors.verticalCenter: parent.verticalCenter
            text: toggle.checked ? backend.texts.on : backend.texts.off
            color: Theme.text
            font.pixelSize: Theme.bodySize + 1
        }
        Rectangle {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            width: 40
            height: 20
            radius: 10
            color: toggle.checked ? Theme.accent : "transparent"
            border.width: toggle.checked ? 0 : 1
            border.color: Theme.subtext
            Rectangle {
                width: 12
                height: 12
                radius: 6
                anchors.verticalCenter: parent.verticalCenter
                x: toggle.checked ? parent.width - width - 4 : 4
                color: toggle.checked ? "#FFFFFF" : Theme.subtext
                Behavior on x { NumberAnimation { duration: 120 } }
            }
        }
        TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: toggle.toggled(!toggle.checked) }
        HoverHandler { cursorShape: Qt.PointingHandCursor }
    }

    // Windows 11 slider: accent track up to the thumb.
    component VSlider: Item {
        id: slider
        property real value: 0          // 0..1
        property var track: null        // a gradient instead of the accent (hue)
        signal moved(real value)
        implicitWidth: 240
        implicitHeight: 24
        activeFocusOnTab: true
        Accessible.role: Accessible.Slider
        Keys.onLeftPressed: moved(Math.max(0, value - 0.05))
        Keys.onRightPressed: moved(Math.min(1, value + 0.05))
        function at(x) { return Math.max(0, Math.min(1, (x - 10) / (width - 20))); }
        Rectangle {
            id: groove
            x: 10
            width: parent.width - 20
            height: slider.track ? 8 : 4
            radius: height / 2
            anchors.verticalCenter: parent.verticalCenter
            color: Theme.track
            gradient: slider.track
            Rectangle {
                visible: !slider.track
                width: parent.width * slider.value
                height: parent.height
                radius: parent.radius
                color: Theme.accent
            }
        }
        Rectangle {
            width: 20
            height: 20
            radius: 10
            x: 10 + groove.width * slider.value - 10
            anchors.verticalCenter: parent.verticalCenter
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder
            Rectangle {
                anchors.centerIn: parent
                width: drag.active || tap.pressed ? 10 : 12
                height: width
                radius: width / 2
                color: Theme.accent
            }
        }
        DragHandler {
            id: drag
            target: null
            xAxis.enabled: true
            yAxis.enabled: false
            grabPermissions: PointerHandler.CanTakeOverFromAnything
            onCentroidChanged: if (active) slider.moved(slider.at(centroid.position.x))
        }
        TapHandler { id: tap; onTapped: point => slider.moved(slider.at(point.position.x)) }
    }

    // A settings row: title and description left, the control right.
    component SettingRow: Rectangle {
        id: row
        property string title
        property string description
        default property alias control: holder.data
        Layout.fillWidth: true
        implicitHeight: Math.max(Math.round(64 * Theme.textScale), texts.implicitHeight + 24)
        radius: 4
        color: Theme.card
        border.width: 1
        border.color: Theme.cardBorder
        ColumnLayout {
            id: texts
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.right: holder.left
            anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Label {
                Layout.fillWidth: true
                text: row.title
                color: Theme.text
                font.pixelSize: Theme.titleSize
                wrapMode: Text.Wrap
            }
            Label {
                Layout.fillWidth: true
                visible: text !== ""
                text: row.description
                color: Theme.subtext
                font.pixelSize: Theme.bodySize
                wrapMode: Text.Wrap
            }
        }
        Item {
            id: holder
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: childrenRect.width
            implicitHeight: childrenRect.height
            width: childrenRect.width
            height: childrenRect.height
        }
    }

    Flickable {
        id: flick
        anchors.fill: parent
        contentWidth: width
        contentHeight: page.implicitHeight + 64
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        ColumnLayout {
            id: page
            x: 36
            y: 28
            width: flick.width - 72
            spacing: 4

            Label {
                text: backend.texts.app_title
                color: Theme.text
                font.pixelSize: Theme.pageTitleSize
                font.weight: Font.DemiBold
            }
            Label {
                Layout.fillWidth: true
                Layout.bottomMargin: 16
                text: backend.texts.subtitle
                color: Theme.subtext
                font.pixelSize: Theme.bodySize + 1
                wrapMode: Text.Wrap
            }

            // No keyboard light.
            Rectangle {
                objectName: "noKeyboard"
                Layout.fillWidth: true
                visible: !window.present
                implicitHeight: none.implicitHeight + 40
                radius: Theme.radius
                color: Theme.card
                border.color: Theme.cardBorder
                RowLayout {
                    id: none
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 18
                    Kirigami.Icon {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: 56
                        Layout.preferredHeight: 56
                        source: "veltos-lighting"
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Label {
                            text: backend.texts.none_title
                            color: Theme.text
                            font.pixelSize: Theme.nameSize
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.fillWidth: true
                            text: backend.texts.none_text
                            color: Theme.subtext
                            font.pixelSize: Theme.bodySize + 1
                            wrapMode: Text.Wrap
                        }
                        VButton {
                            text: backend.texts.refresh
                            onClicked: backend.refresh()
                        }
                    }
                }
            }

            // An MSI laptop: MSI's driver (msi-ec) lights its keyboard (msi.py).
            Rectangle {
                id: msiCard
                objectName: "msiCard"
                readonly property var msi: backend.msi
                Layout.fillWidth: true
                visible: !window.present && ["offer", "unsupported", "busy", "key", "restart", "failed", "checking"]
                         .indexOf(msi.state) !== -1
                implicitHeight: msiColumn.implicitHeight + 40
                radius: Theme.radius
                color: Theme.card
                border.color: Theme.cardBorder
                ColumnLayout {
                    id: msiColumn
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 10
                    Label {
                        text: backend.texts.msi_title
                        color: Theme.text
                        font.pixelSize: Theme.nameSize
                        font.weight: Font.DemiBold
                    }
                    Label {
                        objectName: "msiText"
                        Layout.fillWidth: true
                        text: msiCard.msi.text
                        color: Theme.text
                        font.pixelSize: Theme.bodySize + 1
                        wrapMode: Text.Wrap
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: text !== ""
                        text: msiCard.msi.detail
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.Wrap
                    }
                    // Windows 11 progress bar: the percentage when pkcon gives one.
                    Rectangle {
                        Layout.fillWidth: true
                        visible: msiCard.msi.state === "busy" || msiCard.msi.state === "checking"
                        implicitHeight: 3
                        radius: 1.5
                        color: Theme.cardBorder
                        clip: true
                        Rectangle {
                            id: runner
                            height: parent.height
                            radius: 1.5
                            color: Theme.accent
                            width: msiCard.msi.percent >= 0 ? parent.width * msiCard.msi.percent / 100 : parent.width * 0.3
                            NumberAnimation on x {
                                running: msiCard.visible && msiCard.msi.percent < 0
                                         && (msiCard.msi.state === "busy" || msiCard.msi.state === "checking")
                                loops: Animation.Infinite
                                from: -runner.width
                                to: msiCard.width
                                duration: 1600
                            }
                        }
                    }
                    // Secure Boot: a one-time password for the firmware's key enrolment.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: msiCard.msi.state === "key"
                        spacing: 8
                        TextField {
                            id: keyPassword
                            Layout.preferredWidth: 220
                            echoMode: TextInput.Password
                            placeholderText: backend.texts.msi_key_password
                        }
                        TextField {
                            id: keyConfirm
                            Layout.preferredWidth: 220
                            echoMode: TextInput.Password
                            placeholderText: backend.texts.msi_key_confirm
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: msiCard.msi.state === "key" && text !== ""
                        text: msiCard.msi.keyMessage
                        color: Theme.errorIcon
                        font.pixelSize: Theme.bodySize
                        wrapMode: Text.Wrap
                    }
                    RowLayout {
                        spacing: 8
                        VButton {
                            objectName: "msiInstall"
                            primary: true
                            visible: msiCard.msi.state === "offer" || msiCard.msi.state === "failed"
                            text: msiCard.msi.state === "failed" ? backend.texts.msi_try_again : backend.texts.msi_install
                            onClicked: msiCard.msi.install()
                        }
                        VButton {
                            primary: true
                            visible: msiCard.msi.state === "key"
                            text: backend.texts.msi_key_register
                            onClicked: msiCard.msi.registerKey(keyPassword.text, keyConfirm.text)
                        }
                        VButton {
                            primary: true
                            visible: msiCard.msi.state === "restart"
                            text: backend.texts.msi_restart_now
                            onClicked: msiCard.msi.restart()
                        }
                    }
                }
            }

            // The keyboards (Windows lists the devices as cards).
            Flow {
                Layout.fillWidth: true
                Layout.bottomMargin: 12
                visible: window.present
                spacing: 8
                Repeater {
                    model: backend.keyboards
                    delegate: Rectangle {
                        id: device
                        required property var modelData
                        required property int index
                        readonly property bool chosen: index === backend.selected
                        width: 220
                        height: 132
                        radius: Theme.radius
                        color: chosen ? Theme.cardHover : Theme.card
                        border.width: chosen ? 2 : 1
                        border.color: chosen ? Theme.accent : Theme.cardBorder
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 6
                            Kirigami.Icon {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.preferredWidth: 56
                                Layout.preferredHeight: 56
                                source: "veltos-lighting"
                            }
                            Label {
                                Layout.alignment: Qt.AlignHCenter
                                text: device.modelData.maker ? device.modelData.maker + " " + backend.texts.keyboard
                                                             : backend.texts.built_in
                                color: Theme.text
                                font.pixelSize: Theme.titleSize
                            }
                            Label {
                                Layout.alignment: Qt.AlignHCenter
                                text: device.modelData.colorKind !== "" ? backend.texts.rgb : backend.texts.one_colour
                                color: Theme.subtext
                                font.pixelSize: Theme.bodySize
                            }
                        }
                        TapHandler { onTapped: backend.select(device.index) }
                    }
                }
            }

            SettingRow {
                visible: window.present
                title: backend.texts.lighting
                description: backend.texts.lighting_desc
                Toggle {
                    objectName: "lightingToggle"
                    checked: !!window.pick.on
                    onToggled: on => backend.setOn(on)
                }
            }
            SettingRow {
                visible: window.present
                title: backend.texts.brightness
                RowLayout {
                    spacing: 12
                    VSlider {
                        objectName: "brightness"
                        Layout.preferredWidth: 240
                        value: window.pick.on ? (window.pick.brightness || 0) / 100 : 0
                        onMoved: v => backend.setBrightness(Math.round(Math.max(0.01, v) * 100))
                    }
                    Label {
                        Layout.preferredWidth: 40
                        text: (window.pick.on ? window.pick.brightness : 0) + "%"
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize + 1
                    }
                }
            }
            SettingRow {
                visible: window.coloured && (window.kb.effects || []).length > 1
                title: backend.texts.effects
                description: backend.texts.effects_desc
                ComboBox {
                    id: effects
                    objectName: "effects"
                    implicitWidth: 200
                    model: (window.kb.effects || []).map(e => ({ value: e, text: backend.texts["effect_" + e] }))
                    textRole: "text"
                    valueRole: "value"
                    currentIndex: Math.max(0, (window.kb.effects || []).indexOf(window.pick.effect))
                    onActivated: backend.setEffect(currentValue)
                }
            }
            SettingRow {
                visible: window.coloured && window.pick.effect !== "static" && (window.kb.effects || []).length > 1
                title: backend.texts.speed
                RowLayout {
                    spacing: 12
                    VSlider {
                        Layout.preferredWidth: 200
                        value: (window.pick.speed || 0) / 2
                        onMoved: v => backend.setSpeed(Math.round(v * 2))
                    }
                    Label {
                        Layout.preferredWidth: 60
                        text: backend.texts["speed_" + (window.pick.speed || 0)]
                        color: Theme.subtext
                        font.pixelSize: Theme.bodySize + 1
                    }
                }
            }
            SettingRow {
                visible: window.coloured && backend.accent !== ""
                title: backend.texts.match_accent
                description: backend.texts.match_accent_desc
                Toggle {
                    objectName: "matchAccent"
                    checked: !!window.pick.matchAccent
                    onToggled: on => backend.setMatchAccent(on)
                }
            }

            // Colours, as Windows' palette, and a custom colour by hue.
            Rectangle {
                objectName: "colours"
                Layout.fillWidth: true
                visible: window.coloured && window.pick.effect !== "cycle"
                implicitHeight: colourColumn.implicitHeight + 32
                radius: 4
                color: Theme.card
                border.width: 1
                border.color: Theme.cardBorder
                ColumnLayout {
                    id: colourColumn
                    x: 20
                    y: 16
                    width: parent.width - 40
                    spacing: 12
                    Label {
                        text: backend.texts.colour
                        color: Theme.text
                        font.pixelSize: Theme.titleSize
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: backend.swatches
                            delegate: Rectangle {
                                id: swatch
                                required property string modelData
                                readonly property bool chosen: (window.pick.color || "").toUpperCase() === modelData
                                width: 40
                                height: 40
                                radius: 6
                                color: modelData
                                border.width: chosen ? 3 : 1
                                border.color: chosen ? Theme.text : Theme.cardBorder
                                Accessible.role: Accessible.Button
                                Accessible.name: modelData
                                TapHandler { onTapped: backend.setColor(swatch.modelData) }
                                HoverHandler { cursorShape: Qt.PointingHandCursor }
                            }
                        }
                    }
                    RowLayout {
                        spacing: 12
                        Label {
                            text: backend.texts.custom_colour
                            color: Theme.text
                            font.pixelSize: Theme.bodySize + 1
                        }
                        VSlider {
                            id: hue
                            objectName: "hue"
                            Layout.preferredWidth: 260
                            value: Qt.color(window.pick.color || "#FF0000").hsvHue >= 0 ? Qt.color(window.pick.color || "#FF0000").hsvHue : 0
                            track: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: "#FF0000" }
                                GradientStop { position: 0.17; color: "#FFFF00" }
                                GradientStop { position: 0.33; color: "#00FF00" }
                                GradientStop { position: 0.5; color: "#00FFFF" }
                                GradientStop { position: 0.67; color: "#0000FF" }
                                GradientStop { position: 0.83; color: "#FF00FF" }
                                GradientStop { position: 1.0; color: "#FF0000" }
                            }
                            onMoved: v => {
                                const c = Qt.hsva(Math.min(0.999, v), 1, 1, 1);
                                const hex = n => ("0" + Math.round(n * 255).toString(16)).slice(-2);
                                backend.setColor("#" + hex(c.r) + hex(c.g) + hex(c.b));
                            }
                        }
                        Rectangle {
                            width: 28
                            height: 28
                            radius: 14
                            color: window.pick.color || "#FFFFFF"
                            border.color: Theme.cardBorder
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.topMargin: 8
                visible: backend.error !== ""
                text: backend.error
                color: Theme.errorIcon
                font.pixelSize: Theme.bodySize + 1
                wrapMode: Text.Wrap
            }
        }
    }
}
