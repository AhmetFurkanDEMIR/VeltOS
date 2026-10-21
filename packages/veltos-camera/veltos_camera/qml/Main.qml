/*
    VeltOS Camera window, in the layout of Windows 11's Camera: the camera
    picture fills the window; on the right a dark column with "Change
    camera" (when there is more than one), the Photo/Video switch, the
    shutter and the last photo or video; on the left Settings and, for
    photos, the timer. Without a camera the window says so, as Windows does.
    `backend` is app.Backend.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtMultimedia

ApplicationWindow {
    id: window

    width: 960
    height: 600
    minimumWidth: 520
    minimumHeight: 380
    visible: true
    title: backend.texts.app_title
    color: "#000000"

    readonly property var cameras: devices.videoInputs
    readonly property bool hasCamera: cameras.length > 0
    readonly property int cameraIndex: indexOfCamera(backend.cameraId)
    readonly property bool videoMode: backend.mode === "video"
    readonly property bool recording: recorder.recorderState === MediaRecorder.RecordingState
    property string cameraError: ""
    property int countdown: 0
    property bool settingsOpen: false
    property string message: ""

    function indexOfCamera(id) {
        for (let i = 0; i < cameras.length; ++i) {
            if (cameras[i].description === id) {
                return i;
            }
        }
        return 0;
    }
    function changeCamera() {
        if (cameras.length > 1) {
            backend.setCameraId(cameras[(cameraIndex + 1) % cameras.length].description);
        }
    }
    function showMessage(text) {
        message = text;
        messageTimer.restart();
    }
    function takePhoto() {
        flash.opacity = 0.8;
        flashFade.restart();
        imageCapture.captureToFile(backend.newPhotoPath(""));
    }
    function shutter() {
        if (!hasCamera || cameraError !== "") {
            return;
        }
        if (videoMode) {
            if (recording) {
                recorder.stop();
            } else {
                recorder.outputLocation = backend.newVideoUrl();
                recorder.record();
            }
        } else if (countdown > 0) {
            countdown = 0;                  // a second press cancels the timer
            countdownTimer.stop();
        } else if (backend.timer > 0) {
            countdown = backend.timer;
            countdownTimer.restart();
        } else {
            takePhoto();
        }
    }
    function timeText(ms) {
        const seconds = Math.floor(ms / 1000);
        const pad = n => (n < 10 ? "0" : "") + n;
        return pad(Math.floor(seconds / 60)) + ":" + pad(seconds % 60);
    }

    MediaDevices {
        id: devices
    }

    CaptureSession {
        id: session
        camera: Camera {
            id: camera
            cameraDevice: window.hasCamera ? window.cameras[window.cameraIndex] : devices.defaultVideoInput
            active: window.hasCamera && window.visibility !== Window.Minimized
            onErrorOccurred: (error, errorString) => window.cameraError = errorString
            onCameraDeviceChanged: window.cameraError = ""
        }
        imageCapture: ImageCapture {
            id: imageCapture
            onImageSaved: (requestId, path) => backend.captured(path)
            onErrorOccurred: (requestId, error, message) => window.showMessage(backend.texts.save_failed)
        }
        recorder: MediaRecorder {
            id: recorder
            // H.264 + AAC in MP4, as Windows' Camera saves videos: Qt chose
            // H.265 by default, which many players cannot open (VM, 2026-10-21).
            mediaFormat {
                fileFormat: MediaFormat.MPEG4
                videoCodec: MediaFormat.VideoCodec.H264
                audioCodec: MediaFormat.AudioCodec.AAC
            }
            onRecorderStateChanged: {
                if (recorderState === MediaRecorder.StoppedState && actualLocation.toString() !== "") {
                    backend.captured(actualLocation.toString());
                }
            }
            onErrorOccurred: (error, errorString) => window.showMessage(backend.texts.save_failed)
        }
        audioInput: window.videoMode && backend.recordAudio ? microphone : null
        videoOutput: preview
    }

    AudioInput {
        id: microphone
    }

    Timer {
        id: countdownTimer
        interval: 1000
        repeat: true
        onTriggered: {
            window.countdown -= 1;
            if (window.countdown <= 0) {
                stop();
                window.takePhoto();
            }
        }
    }
    Timer {
        id: messageTimer
        interval: 4000
        onTriggered: window.message = ""
    }

    Item {
        id: root
        anchors.fill: parent
        focus: true
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Space || event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                window.shutter();
                event.accepted = true;
            } else if (event.key === Qt.Key_Escape && window.settingsOpen) {
                window.settingsOpen = false;
                event.accepted = true;
            }
        }

        VideoOutput {
            id: preview
            objectName: "preview"
            anchors.fill: parent
            anchors.rightMargin: controls.width
            fillMode: VideoOutput.PreserveAspectFit
        }

        // Framing grid over the picture
        Canvas {
            id: gridLines
            objectName: "grid"
            visible: backend.grid !== "none" && window.hasCamera
            x: preview.x + preview.contentRect.x
            y: preview.y + preview.contentRect.y
            width: preview.contentRect.width
            height: preview.contentRect.height
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            Connections {
                target: backend
                function onChanged() { gridLines.requestPaint(); }
            }
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.55);
                ctx.lineWidth = 1;
                const w = width, h = height;
                ctx.beginPath();
                if (backend.grid === "thirds") {
                    for (const f of [1 / 3, 2 / 3]) {
                        ctx.moveTo(w * f, 0); ctx.lineTo(w * f, h);
                        ctx.moveTo(0, h * f); ctx.lineTo(w, h * f);
                    }
                } else if (backend.grid === "square") {
                    const s = Math.min(w, h) * 0.8;
                    ctx.rect((w - s) / 2, (h - s) / 2, s, s);
                } else if (backend.grid === "cross") {
                    ctx.moveTo(w / 2 - 24, h / 2); ctx.lineTo(w / 2 + 24, h / 2);
                    ctx.moveTo(w / 2, h / 2 - 24); ctx.lineTo(w / 2, h / 2 + 24);
                }
                ctx.stroke();
            }
        }

        // White flash when a photo is taken
        Rectangle {
            id: flash
            anchors.fill: preview
            color: "#FFFFFF"
            opacity: 0
            NumberAnimation on opacity {
                id: flashFade
                running: false
                to: 0
                duration: 250
            }
        }

        // No camera / camera problem, as Windows says it
        ColumnLayout {
            objectName: "noCamera"
            visible: !window.hasCamera || window.cameraError !== ""
            anchors.centerIn: preview
            width: Math.min(preview.width - 64, 460)
            spacing: 10
            Glyph {
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 8
                Layout.preferredWidth: 56
                Layout.preferredHeight: 56
                kind: "cameraoff"
                color: "#C8CBD4"
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                text: window.hasCamera ? backend.texts.camera_error : backend.texts.no_camera_title
                color: "#FFFFFF"
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                text: window.hasCamera ? window.cameraError : backend.texts.no_camera_body
                color: "#C8CBD4"
                font.pixelSize: 14
            }
        }

        // Timer count-down
        Text {
            visible: window.countdown > 0
            anchors.centerIn: preview
            text: window.countdown
            color: "#FFFFFF"
            style: Text.Outline
            styleColor: Qt.rgba(0, 0, 0, 0.35)
            font.pixelSize: 120
            font.weight: Font.DemiBold
        }

        // Recording time
        Rectangle {
            objectName: "recordingTime"
            visible: window.recording
            anchors.top: parent.top
            anchors.topMargin: 16
            anchors.horizontalCenter: preview.horizontalCenter
            width: timeRow.implicitWidth + 28
            height: 32
            radius: 16
            color: Qt.rgba(0, 0, 0, 0.55)
            Row {
                id: timeRow
                anchors.centerIn: parent
                spacing: 8
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: 10
                    height: 10
                    radius: 5
                    color: "#E81123"
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: window.timeText(recorder.duration)
                    color: "#FFFFFF"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
            }
        }

        // Left: settings and the photo timer
        Column {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: 16
            spacing: 12
            RoundButton {
                objectName: "settingsButton"
                glyph: "settings"
                tip: backend.texts.settings
                enabled: !window.recording
                onClicked: window.settingsOpen = !window.settingsOpen
            }
            RoundButton {
                objectName: "timerButton"
                visible: !window.videoMode
                glyph: "timer"
                tip: backend.texts.timer
                badge: backend.timer > 0 ? backend.texts.seconds.replace("{n}", backend.timer) : ""
                onClicked: backend.nextTimer()
            }
        }

        // Right: change camera, Photo/Video, shutter, last capture
        Rectangle {
            id: controls
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 104
            color: Qt.rgba(0, 0, 0, 0.42)

            RoundButton {
                objectName: "changeCameraButton"
                visible: window.cameras.length > 1
                anchors.top: parent.top
                anchors.topMargin: 16
                anchors.horizontalCenter: parent.horizontalCenter
                glyph: "switch"
                tip: backend.texts.change_camera
                enabled: !window.recording
                onClicked: window.changeCamera()
            }

            Column {
                anchors.centerIn: parent
                spacing: 20

                // Photo / Video
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 52
                    height: 104
                    radius: 26
                    color: Qt.rgba(1, 1, 1, 0.12)
                    Column {
                        anchors.fill: parent
                        Repeater {
                            model: [{ mode: "photo", glyph: "camera" }, { mode: "video", glyph: "video" }]
                            delegate: AbstractButton {
                                id: modeButton
                                required property var modelData
                                readonly property bool current: backend.mode === modelData.mode
                                objectName: "mode_" + modelData.mode
                                width: 52
                                height: 52
                                hoverEnabled: true
                                focusPolicy: Qt.NoFocus
                                enabled: !window.recording && window.countdown === 0
                                Accessible.name: backend.texts[modelData.mode]
                                ToolTip.visible: hovered
                                ToolTip.delay: 600
                                ToolTip.text: backend.texts[modelData.mode]
                                onClicked: backend.setMode(modelData.mode)
                                background: Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    radius: width / 2
                                    color: modeButton.current ? "#FFFFFF"
                                           : (modeButton.hovered ? Qt.rgba(1, 1, 1, 0.14) : "transparent")
                                }
                                contentItem: Item {
                                    Glyph {
                                        anchors.centerIn: parent
                                        width: 22
                                        height: 22
                                        kind: modeButton.modelData.glyph
                                        color: modeButton.current ? "#1B1D24" : "#FFFFFF"
                                    }
                                }
                            }
                        }
                    }
                }

                // Shutter: a white ring around a white (photo) or red (video)
                // disc; a red square while recording.
                AbstractButton {
                    id: shutterButton
                    objectName: "shutter"
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 72
                    height: 72
                    hoverEnabled: true
                    focusPolicy: Qt.NoFocus
                    enabled: window.hasCamera && window.cameraError === ""
                    opacity: enabled ? 1 : 0.4
                    Accessible.name: window.videoMode ? (window.recording ? backend.texts.stop_video
                                                                          : backend.texts.start_video)
                                                      : backend.texts.take_photo
                    ToolTip.visible: hovered
                    ToolTip.delay: 600
                    ToolTip.text: Accessible.name
                    onClicked: window.shutter()
                    background: Rectangle {
                        radius: width / 2
                        color: "transparent"
                        border.width: 3
                        border.color: "#FFFFFF"
                        Rectangle {
                            anchors.centerIn: parent
                            width: window.recording ? 26 : (shutterButton.down ? 50 : 56)
                            height: width
                            radius: window.recording ? 6 : width / 2
                            color: window.videoMode ? "#E81123" : (shutterButton.hovered ? "#F1F3F8" : "#FFFFFF")
                            Behavior on width { NumberAnimation { duration: 120 } }
                            Behavior on radius { NumberAnimation { duration: 120 } }
                        }
                    }
                    contentItem: Item {}
                }
            }

            // The last photo or video; opens it
            AbstractButton {
                objectName: "lastCapture"
                visible: backend.lastCapture !== ""
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 20
                anchors.horizontalCenter: parent.horizontalCenter
                width: 52
                height: 52
                hoverEnabled: true
                focusPolicy: Qt.NoFocus
                Accessible.name: backend.texts.last_capture
                ToolTip.visible: hovered
                ToolTip.delay: 600
                ToolTip.text: backend.texts.last_capture
                onClicked: backend.openLast()
                background: Rectangle {
                    radius: 8
                    color: "#2A2C38"
                    border.width: 2
                    border.color: parent.hovered ? "#FFFFFF" : Qt.rgba(1, 1, 1, 0.7)
                    clip: true
                    Image {
                        anchors.fill: parent
                        anchors.margins: 2
                        visible: !backend.lastIsVideo
                        source: backend.lastIsVideo ? "" : backend.lastCaptureUrl
                        sourceSize.width: 104
                        sourceSize.height: 104
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        cache: false
                    }
                    Glyph {
                        anchors.centerIn: parent
                        visible: backend.lastIsVideo
                        width: 24
                        height: 24
                        kind: "video"
                    }
                }
                contentItem: Item {}
            }
        }

        // Message (e.g. a file could not be saved)
        Rectangle {
            visible: window.message !== ""
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 24
            anchors.horizontalCenter: preview.horizontalCenter
            width: messageText.implicitWidth + 32
            height: 40
            radius: 8
            color: "#2B2B2B"
            border.color: Qt.rgba(1, 1, 1, 0.12)
            Text {
                id: messageText
                anchors.centerIn: parent
                text: window.message
                color: "#FFFFFF"
                font.pixelSize: 14
            }
        }

        // Settings, from the left like Windows' Camera
        MouseArea {
            visible: window.settingsOpen
            anchors.fill: parent
            onClicked: window.settingsOpen = false
        }
        Rectangle {
            id: settingsPanel
            objectName: "settingsPanel"
            visible: x > -width
            x: window.settingsOpen ? 0 : -width - 2
            width: Math.min(360, window.width - 120)
            height: parent.height
            color: "#202020"
            border.color: Qt.rgba(1, 1, 1, 0.08)
            Behavior on x { NumberAnimation { duration: 167; easing.type: Easing.OutCubic } }
            MouseArea { anchors.fill: parent }

            RowLayout {
                id: settingsHeader
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                Text {
                    Layout.fillWidth: true
                    text: backend.texts.settings
                    color: "#FFFFFF"
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                RoundButton {
                    objectName: "closeSettings"
                    size: 36
                    glyph: "close"
                    tip: backend.texts.close
                    onClicked: window.settingsOpen = false
                }
            }

            Flickable {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: settingsHeader.bottom
                anchors.bottom: parent.bottom
                anchors.topMargin: 12
                contentHeight: settingsColumn.implicitHeight + 24
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ColumnLayout {
                    id: settingsColumn
                    x: 16
                    width: parent.width - 32
                    spacing: 6

                    SectionTitle { text: backend.texts.camera_settings }
                    Text {
                        text: backend.texts.framing_grid
                        color: "#FFFFFF"
                        font.pixelSize: 14
                        Layout.topMargin: 4
                    }
                    Repeater {
                        model: [{ value: "none", label: backend.texts.grid_none },
                                { value: "thirds", label: backend.texts.grid_thirds },
                                { value: "square", label: backend.texts.grid_square },
                                { value: "cross", label: backend.texts.grid_cross }]
                        delegate: OptionRow {
                            required property var modelData
                            objectName: "grid_" + modelData.value
                            label: modelData.label
                            selected: backend.grid === modelData.value
                            onClicked: backend.setGrid(modelData.value)
                        }
                    }

                    SectionTitle { text: backend.texts.video_settings }
                    OptionRow {
                        objectName: "recordAudio"
                        checkbox: true
                        label: backend.texts.record_audio
                        selected: backend.recordAudio
                        onClicked: backend.setRecordAudio(!backend.recordAudio)
                    }

                    SectionTitle { text: backend.texts.save_location }
                    Text {
                        Layout.fillWidth: true
                        text: backend.texts.save_location_body.replace("{folder}", backend.folderName)
                        color: "#C8CBD4"
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                    }
                    AbstractButton {
                        id: openFolder
                        objectName: "openFolder"
                        Layout.topMargin: 6
                        implicitWidth: folderRow.implicitWidth + 28
                        implicitHeight: 32
                        hoverEnabled: true
                        focusPolicy: Qt.NoFocus
                        onClicked: backend.openFolder()
                        background: Rectangle {
                            radius: 4
                            color: openFolder.down ? "#2A2A2A" : (openFolder.hovered ? "#3A3A3A" : "#2F2F2F")
                            border.color: Qt.rgba(1, 1, 1, 0.1)
                        }
                        contentItem: Item {
                            Row {
                                id: folderRow
                                anchors.centerIn: parent
                                spacing: 8
                                Glyph {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 16
                                    height: 16
                                    kind: "folder"
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: backend.texts.open_folder
                                    color: "#FFFFFF"
                                    font.pixelSize: 14
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Round icon button over the picture (Windows 11 Camera)
    component RoundButton: AbstractButton {
        id: roundButton
        property string glyph: ""
        property string tip: ""
        property string badge: ""
        property int size: 44
        width: size
        height: size
        hoverEnabled: true
        focusPolicy: Qt.NoFocus
        opacity: enabled ? 1 : 0.4
        Accessible.name: tip
        ToolTip.visible: hovered && tip !== ""
        ToolTip.delay: 600
        ToolTip.text: tip
        background: Rectangle {
            radius: width / 2
            color: roundButton.down ? Qt.rgba(0, 0, 0, 0.6) : (roundButton.hovered ? Qt.rgba(0, 0, 0, 0.55)
                                                                                   : Qt.rgba(0, 0, 0, 0.38))
            border.color: Qt.rgba(1, 1, 1, 0.14)
        }
        contentItem: Item {
            Glyph {
                anchors.centerIn: parent
                width: 20
                height: 20
                kind: roundButton.glyph
            }
            Rectangle {
                visible: roundButton.badge !== ""
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.bottom
                anchors.topMargin: 2
                width: badgeText.implicitWidth + 10
                height: 18
                radius: 9
                color: Qt.rgba(0, 0, 0, 0.55)
                Text {
                    id: badgeText
                    anchors.centerIn: parent
                    text: roundButton.badge
                    color: "#FFFFFF"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
            }
        }
    }

    component SectionTitle: Text {
        Layout.topMargin: 14
        color: "#FFFFFF"
        font.pixelSize: 14
        font.weight: Font.DemiBold
    }

    // A radio or check row of the settings panel (Windows 11 controls)
    component OptionRow: AbstractButton {
        id: option
        property string label: ""
        property bool selected: false
        property bool checkbox: false
        Layout.fillWidth: true
        implicitHeight: 34
        hoverEnabled: true
        focusPolicy: Qt.NoFocus
        Accessible.name: label
        background: Rectangle {
            radius: 4
            color: option.hovered ? Qt.rgba(1, 1, 1, 0.05) : "transparent"
        }
        contentItem: Row {
            spacing: 10
            leftPadding: 4
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 20
                height: 20
                radius: option.checkbox ? 4 : 10
                color: option.selected ? "#6E95FF" : "transparent"
                border.width: option.selected ? 0 : 1
                border.color: "#C8CBD4"
                Rectangle {
                    visible: option.selected && !option.checkbox
                    anchors.centerIn: parent
                    width: 8
                    height: 8
                    radius: 4
                    color: "#0B1020"
                }
                Text {
                    visible: option.selected && option.checkbox
                    anchors.centerIn: parent
                    text: "✓"
                    color: "#0B1020"
                    font.pixelSize: 13
                    font.weight: Font.Bold
                }
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: option.label
                color: "#FFFFFF"
                font.pixelSize: 14
            }
        }
    }
}
