// System > Sound: where sound plays and comes from, and how loud.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

ColumnLayout {
    id: page

    readonly property var snd: backend.sound
    signal itemActivated(var item)

    function current(list) {
        for (const device of list) {
            if (device.default)
                return device;
        }
        return list.length ? list[0] : null;
    }

    spacing: 4
    Component.onCompleted: backend.refreshSound()

    component DeviceGroup: ColumnLayout {
        id: group

        property string kind          // "sink" or "source"
        property var devices: []
        property string chooseText
        property string emptyText
        property string deviceIcon
        readonly property var device: page.current(devices)

        Layout.fillWidth: true
        spacing: 4

        SettingRow {
            Layout.fillWidth: true
            icon: group.deviceIcon
            title: group.chooseText
            description: group.devices.length === 0 && page.snd.loaded ? group.emptyText : ""
            VComboBox {
                Layout.preferredWidth: 300
                visible: group.devices.length > 0
                accessibleName: group.chooseText
                options: group.devices.map(d => ({ label: d.description, value: d.name }))
                currentValue: group.device ? group.device.name : ""
                onActivated: value => backend.setSoundDevice(group.kind, value)
            }
        }
        SettingRow {
            Layout.fillWidth: true
            visible: group.device !== null
            title: backend.text("volume")
            Rectangle {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 32
                radius: 5
                color: muteHover.hovered ? Theme.navHover : "transparent"
                Accessible.role: Accessible.Button
                Accessible.name: group.device && group.device.muted ? backend.text("unmute") : backend.text("mute")
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    source: group.kind === "sink"
                            ? (group.device && group.device.muted ? "audio-volume-muted" : "audio-volume-high")
                            : (group.device && group.device.muted ? "microphone-sensitivity-muted" : "audio-input-microphone")
                }
                HoverHandler { id: muteHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: backend.setMuted(group.kind, !group.device.muted) }
            }
            VSlider {
                id: volume
                Layout.preferredWidth: 260
                accessibleName: backend.text("volume")
                value: group.device ? group.device.volume : 0
                onMoved: pending.restart()
                onReleased: backend.setVolume(group.kind, Math.round(value))
            }
            Label {
                Layout.preferredWidth: 34
                horizontalAlignment: Text.AlignRight
                text: Math.round(volume.value)
                color: Theme.text
                font.pixelSize: Theme.titleSize
            }
            Timer {
                // Change the volume while dragging, at most ~10 times a second.
                id: pending
                interval: 90
                onTriggered: backend.setVolume(group.kind, Math.round(volume.value))
            }
        }
    }

    SectionLabel {
        Layout.topMargin: 0
        text: backend.text("output")
    }
    DeviceGroup {
        kind: "sink"
        devices: page.snd.outputs
        chooseText: backend.text("choose_output")
        emptyText: backend.text("no_output")
        deviceIcon: "audio-volume-high"
    }

    SectionLabel {
        text: backend.text("input")
    }
    DeviceGroup {
        kind: "source"
        devices: page.snd.inputs
        chooseText: backend.text("choose_input")
        emptyText: backend.text("no_input")
        deviceIcon: "audio-input-microphone"
    }

    SettingCard {
        Layout.fillWidth: true
        Layout.topMargin: 18
        icon: "preferences-desktop-sound"
        title: backend.text("more_sound")
        description: backend.text("more_sound_desc")
        external: true
        onActivated: page.itemActivated({ kcm: "kcm_pulseaudio", action: "", page: "" })
    }
}
