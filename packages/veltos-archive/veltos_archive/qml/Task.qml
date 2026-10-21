/*
    VeltOS Archive's small window for File Explorer's commands (WinRAR's
    progress window): "Extract here", "Extract to <name>\", "Add to
    archive..." and "Add to <name>.zip". `task` is {mode, files}; the
    window closes itself when everything is done and stays open with the
    message if something failed.

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window

    readonly property bool adding: task.mode === "--add"
    width: adding && !started ? 600 : 480
    height: adding && !started ? 560 : 190
    visible: true
    title: backend.texts.app_title
    color: Theme.card

    property var queue: []
    property string current: ""
    property bool started: false
    property string failure: ""

    function finishOne() {
        if (queue.length === 0) {
            Qt.quit();
            return;
        }
        current = queue[0];
        queue = queue.slice(1);
        backend.openArchive(current);
    }

    Component.onCompleted: {
        if (task.mode === "--extract-here" || task.mode === "--extract-to-folder") {
            queue = task.files;
            started = true;
            finishOne();
        } else if (task.mode === "--add-to" && task.files.length > 1) {
            started = true;
            backend.createArchive(task.files.slice(1), task.files[0], "", "normal", "", false);
        } else if (adding) {
            addDialog.prepare(task.files);
            addDialog.open();
        }
    }

    Connections {
        target: backend
        function onOpened() {
            // An archive to extract was listed: extract all of it.
            if (window.current !== "") {
                backend.extract(task.mode === "--extract-here" ? backend.archiveFolder() : backend.defaultDestination(),
                                [], "rename");
            }
        }
        function onExtracted(folder) {
            if (window.adding || task.mode === "--add-to") {
                Qt.quit();
            } else {
                window.finishOne();
            }
        }
        function onJobChanged() {
            if (backend.job !== null && !backend.job.running && !backend.job.ok
                    && backend.job.errorKind === "cancelled") {
                Qt.quit();
            }
        }
        function onNotice(title, body) {
            window.failure = body || title;
        }
        function onPasswordNeeded(reason) {
            passwordDialog.mode = reason;
            passwordDialog.archiveName = backend.archiveName;
            passwordDialog.open();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        visible: window.started
        ProgressPanel {
            visible: window.failure === ""
            Layout.fillWidth: true
            job: backend.job
            onBackgroundRequested: window.showMinimized()
        }
        Text {
            objectName: "failureText"
            visible: window.failure !== ""
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: window.failure
            color: Theme.text
            font.pixelSize: Theme.bodySize
            wrapMode: Text.Wrap
        }
        WinButton {
            visible: window.failure !== ""
            Layout.alignment: Qt.AlignRight
            accent: true
            text: backend.texts.close
            onClicked: Qt.quit()
        }
    }

    AddDialog {
        id: addDialog
        closePolicy: Popup.NoAutoClose
        onAccepted: (name, format, level, password, names) => {
            window.started = true;
            backend.createArchive(sources, name, format, level, password, names);
        }
        onRejected: Qt.quit()
    }

    PasswordDialog {
        id: passwordDialog
        onAccepted: (password, names) => backend.setPassword(password)
        onRejected: Qt.quit()
    }
}
