// The driver log: what VeltOS Graphics Cards ran, pkcon's and DKMS's
// output and the system's driver state as selectable text, with Copy,
// Save and open (Notepad) and "Add kernel messages" (asks for the
// administrator's password).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Window {
    id: logWindow
    width: 820
    height: 600
    minimumWidth: 520
    minimumHeight: 360
    title: backend.texts.log_title
    color: Theme.window

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 12

        Label {
            text: backend.texts.log_title
            color: Theme.text
            font.pixelSize: Math.round(20 * Theme.textScale)
            font.weight: Font.DemiBold
        }
        Label {
            Layout.fillWidth: true
            text: backend.texts.log_intro
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.Wrap
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.radius
            color: Theme.card
            border.width: 1
            border.color: Theme.cardBorder
            clip: true

            // A Flickable, not a ScrollView: its padding loops with a
            // wrapping text (AGENTS.md).
            Flickable {
                id: logFlick
                anchors.fill: parent
                anchors.margins: 12
                contentWidth: width
                contentHeight: logText.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                TextEdit {
                    id: logText
                    objectName: "logText"
                    width: logFlick.width - 14
                    text: backend.logText
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextEdit.WrapAnywhere
                    color: Theme.text
                    selectionColor: Theme.accent
                    selectedTextColor: "#FFFFFF"
                    font.family: "monospace"
                    font.pixelSize: Theme.bodySize
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: text !== ""
            text: backend.logNote
            color: Theme.subtext
            font.pixelSize: Theme.bodySize + 1
            wrapMode: Text.Wrap
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            VButton {
                text: backend.texts.log_kernel
                onClicked: backend.kernelLog()
            }
            Item { Layout.fillWidth: true }
            VButton {
                text: backend.texts.log_copy
                onClicked: backend.copyLog()
            }
            VButton {
                text: backend.texts.log_save
                onClicked: backend.saveLog()
            }
            VButton {
                text: backend.texts.log_close
                primary: true
                onClicked: logWindow.close()
            }
        }
    }
}
