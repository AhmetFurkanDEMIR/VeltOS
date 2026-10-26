// Windows 11's Format window, a window of its own (product owner,
// 2026-10-26): capacity, file system, volume label, "Quick Format", a
// progress bar and Start / Close. Start asks first (all data is erased);
// while the volume is formatted the bar runs and the window stays open,
// then it says "Format complete." File Explorer's Format (veltos-disks
// --format DEVICE) opens only this window; Disk Management opens it for the
// chosen volume. UDisks reports no progress for making a file system, so
// the bar moves without a percentage, as Windows' quick format does.
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "."

Window {
    id: win
    objectName: "formatWindow"

    // A backend.volumes entry; null when the device cannot be formatted.
    property var volume: null
    // "ready", "confirm", "formatting", "done" or "failed".
    property string phase: volume && volume.canFormat ? "ready" : "unavailable"
    property string failure: ""
    property string label: volume ? (volume.label || "") : ""
    property string fs: ""
    property bool quick: true
    readonly property bool working: phase === "formatting"
    readonly property var t: backend.texts

    function start() {
        if (phase === "ready" || phase === "done" || phase === "failed")
            phase = "confirm";
    }
    function confirm() {
        failure = "";
        phase = "formatting";
        if (!backend.act("format", volume.object, {label: label, fs: fs, quick: quick})) {
            phase = "failed";
            failure = t.format_unavailable;
        }
    }
    function names() {
        return {"ntfs": "NTFS", "exfat": "exFAT", "vfat": "FAT32", "ext4": "ext4", "btrfs": "Btrfs", "xfs": "XFS"};
    }

    title: t.format_title.replace("{name}", volume ? (volume.title || volume.device)
                                                   : (typeof formatDeviceRequest === "undefined" ? "" : formatDeviceRequest))
    color: Theme.window
    flags: Qt.Dialog
    // A fixed size: Windows' Format window cannot be resized or maximised.
    // Size and limits follow one computed value each (bound to each other
    // they loop).
    readonly property int fixedWidth: Math.round(420 * Math.min(1.25, Theme.textScale))
    readonly property int fixedHeight: column.implicitHeight + 48
    width: fixedWidth
    height: fixedHeight
    minimumWidth: fixedWidth
    maximumWidth: fixedWidth
    minimumHeight: fixedHeight
    maximumHeight: fixedHeight

    Component.onCompleted: {
        const choices = backend.formats;
        const current = volume ? volume.fsType : "";
        fs = choices.indexOf(current) >= 0 ? current : (choices.indexOf("ntfs") >= 0 ? "ntfs" : (choices[0] || ""));
    }
    onClosing: close => {
        if (working)
            close.accepted = false;      // the volume is being formatted
    }

    Connections {
        target: backend
        function onActionFinished(action, target, ok) {
            if (action !== "format" || !win.volume || target !== win.volume.object || !win.working)
                return;
            win.phase = ok ? "done" : "failed";
        }
        function onMessage(text) {
            if (win.working || win.phase === "failed")
                win.failure = text;
        }
    }

    component Label: Text {
        color: Theme.text
        font.pixelSize: Theme.bodySize
    }
    component Button: Rectangle {
        id: button
        property string text
        property bool primary: false
        property bool enabledState: true
        signal clicked()
        implicitWidth: Math.max(96, caption.implicitWidth + 32)
        implicitHeight: Math.round(32 * Theme.textScale)
        radius: 5
        opacity: enabledState ? 1 : 0.45
        color: primary ? (hover.hovered && enabledState ? Qt.lighter(Theme.accent, 1.08) : Theme.accent)
                       : (hover.hovered && enabledState ? Theme.rowHover : Theme.field)
        border.width: primary ? 0 : 1
        border.color: Theme.fieldBorder
        activeFocusOnTab: enabledState
        Accessible.role: Accessible.Button
        Accessible.name: text
        Keys.onReturnPressed: if (enabledState) clicked()
        Keys.onSpacePressed: if (enabledState) clicked()
        Text {
            id: caption
            anchors.centerIn: parent
            text: button.text
            color: button.primary ? "#FFFFFF" : Theme.text
            font.pixelSize: Theme.bodySize
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 8
            color: "transparent"
            border.width: 2
            border.color: Theme.text
            visible: button.activeFocus
        }
        HoverHandler { id: hover }
        TapHandler {
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: if (button.enabledState) button.clicked()
        }
    }

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 24
        spacing: 14
        enabled: !win.working && win.phase !== "confirm"

        Label {
            text: win.t.capacity
            color: Theme.subtext
            font.pixelSize: Theme.smallSize
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: -8
            implicitHeight: Math.round(32 * Theme.textScale)
            radius: 4
            color: Theme.control
            border.width: 1
            border.color: Theme.fieldBorder
            Label {
                objectName: "capacity"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 10
                text: win.volume ? win.volume.sizeText : ""
            }
        }

        Label {
            text: win.t.fs_choice
            color: Theme.subtext
            font.pixelSize: Theme.smallSize
        }
        Flow {
            Layout.fillWidth: true
            Layout.topMargin: -8
            spacing: 8
            Repeater {
                model: backend.formats
                delegate: Rectangle {
                    id: option
                    required property string modelData
                    readonly property bool chosen: win.fs === modelData
                    width: optionText.implicitWidth + 28
                    height: Math.round(30 * Theme.textScale)
                    radius: height / 2
                    color: chosen ? Theme.accent : (optionHover.hovered ? Theme.rowHover : Theme.control)
                    border.width: chosen ? 0 : 1
                    border.color: Theme.fieldBorder
                    Accessible.role: Accessible.RadioButton
                    Accessible.name: optionText.text
                    Text {
                        id: optionText
                        anchors.centerIn: parent
                        text: win.names()[option.modelData] || option.modelData
                        color: option.chosen ? "#FFFFFF" : Theme.text
                        font.pixelSize: Theme.bodySize
                    }
                    HoverHandler { id: optionHover }
                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: win.fs = option.modelData
                    }
                }
            }
        }

        Label {
            text: win.t.volume_label
            color: Theme.subtext
            font.pixelSize: Theme.smallSize
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: -8
            implicitHeight: Math.round(32 * Theme.textScale)
            radius: 4
            color: Theme.field
            border.width: 1
            border.color: labelInput.activeFocus ? Theme.accent : Theme.fieldBorder
            TextInput {
                id: labelInput
                objectName: "labelInput"
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                verticalAlignment: TextInput.AlignVCenter
                activeFocusOnTab: true
                color: Theme.text
                selectionColor: Theme.accent
                selectedTextColor: "#FFFFFF"
                font.pixelSize: Theme.bodySize
                clip: true
                text: win.label
                onTextEdited: win.label = text
                HoverHandler { cursorShape: Qt.IBeamCursor }
            }
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 1
                height: labelInput.activeFocus ? 2 : 0
                color: Theme.accent
            }
        }

        Label {
            text: win.t.format_options
            color: Theme.subtext
            font.pixelSize: Theme.smallSize
        }
        RowLayout {
            Layout.topMargin: -6
            spacing: 10
            Rectangle {
                id: box
                objectName: "quickBox"
                width: 20
                height: 20
                radius: 4
                color: win.quick ? Theme.accent : Theme.field
                border.width: win.quick ? 0 : 1
                border.color: Theme.fieldBorder
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 14
                    height: 14
                    visible: win.quick
                    source: "dialog-ok-apply-symbolic"
                    color: "#FFFFFF"
                    isMask: true
                }
            }
            Label { text: win.t.quick_format }
            TapHandler {
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: win.quick = !win.quick
            }
        }

        // The progress bar: empty, running while formatting, full when done.
        Rectangle {
            id: track
            objectName: "progressBar"
            Layout.fillWidth: true
            Layout.topMargin: 10
            implicitHeight: 4
            radius: 2
            clip: true
            color: Theme.cardBorder
            Rectangle {
                visible: win.phase === "done"
                width: parent.width
                height: parent.height
                radius: 2
                color: Theme.accent
            }
            Rectangle {
                id: runner
                visible: win.working
                width: parent.width * 0.35
                height: parent.height
                radius: 2
                color: Theme.accent
                SequentialAnimation on x {
                    running: win.working
                    loops: Animation.Infinite
                    NumberAnimation {
                        from: -track.width * 0.35
                        to: track.width
                        duration: 1500
                        easing.type: Easing.InOutCubic
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: -6
            spacing: 6
            Kirigami.Icon {
                visible: win.phase === "done" || win.phase === "failed"
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                source: win.phase === "done" ? "dialog-ok-apply" : "dialog-error"
            }
            Text {
                objectName: "status"
                Layout.fillWidth: true
                text: win.phase === "formatting" ? win.t.formatting
                      : win.phase === "done" ? win.t.format_complete
                      : win.phase === "failed" ? (win.failure || win.t.format_failed)
                      : win.phase === "unavailable" ? win.t.format_unavailable : ""
                color: win.phase === "failed" ? "#C42B1C" : Theme.subtext
                font.pixelSize: Theme.smallSize
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 6
            spacing: 8
            Item { Layout.fillWidth: true }
            Button {
                objectName: "startButton"
                primary: true
                text: win.t.start
                enabledState: win.phase !== "unavailable" && !win.working && win.fs !== ""
                onClicked: win.start()
            }
            Button {
                objectName: "closeButton"
                text: win.t.close
                enabledState: !win.working
                onClicked: win.close()
            }
        }
    }

    // "Formatting will erase ALL data": asked inside the window, over a dimmed
    // window, as a Windows 11 content dialog.
    Rectangle {
        anchors.fill: parent
        visible: win.phase === "confirm"
        color: Qt.rgba(0, 0, 0, 0.3)
        TapHandler {}
        Rectangle {
            objectName: "confirmCard"
            anchors.centerIn: parent
            width: parent.width - 48
            height: confirmColumn.implicitHeight + 40
            radius: 8
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder
            ColumnLayout {
                id: confirmColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 20
                spacing: 14
                RowLayout {
                    spacing: 10
                    Kirigami.Icon {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        source: "dialog-warning"
                    }
                    Text {
                        Layout.fillWidth: true
                        text: win.t.format_title.replace("{name}", win.volume ? (win.volume.title || win.volume.device) : "")
                        color: Theme.text
                        font.pixelSize: Theme.bodySize + 2
                        font.weight: Font.DemiBold
                        wrapMode: Text.WordWrap
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: win.t.format_warning
                    color: Theme.text
                    font.pixelSize: Theme.bodySize
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Item { Layout.fillWidth: true }
                    Button {
                        objectName: "confirmButton"
                        primary: true
                        text: win.t.ok
                        onClicked: win.confirm()
                    }
                    Button {
                        text: win.t.cancel
                        onClicked: win.phase = "ready"
                    }
                }
            }
        }
    }
}
