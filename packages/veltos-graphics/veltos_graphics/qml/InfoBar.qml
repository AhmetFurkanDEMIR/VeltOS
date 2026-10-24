// Windows 11 InfoBar: a tinted strip with a round severity mark, the
// message and, on the right, the buttons given as children.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Rectangle {
    id: bar

    // "info", "success", "warning" or "error"
    property string severity: "info"
    property string text
    default property alias buttons: buttonRow.data
    readonly property color mark: severity === "success" ? Theme.successIcon
                                  : severity === "warning" ? Theme.warningIcon
                                  : severity === "error" ? Theme.errorIcon : Theme.accent

    implicitHeight: Math.max(Math.round(48 * Theme.textScale), row.implicitHeight + 20)
    radius: 6
    color: severity === "success" ? Theme.successBack
           : severity === "warning" ? Theme.warningBack
           : severity === "error" ? Theme.errorBack : Theme.infoBack
    border.width: 1
    border.color: Theme.dark ? Qt.rgba(1, 1, 1, 0.06) : Qt.rgba(0, 0, 0, 0.06)
    Accessible.role: Accessible.AlertMessage
    Accessible.name: text

    FontMetrics {
        id: metrics
        font.pixelSize: Theme.bodySize + 1
    }

    RowLayout {
        id: row
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 10
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        spacing: 12

        // The severity mark: a filled circle with "✓", "i" or "!" drawn in it.
        Rectangle {
            // Beside the first line of a longer message, as Windows does.
            Layout.alignment: message.lineCount > 1 ? Qt.AlignTop : Qt.AlignVCenter
            Layout.topMargin: message.lineCount > 1 ? Math.max(0, (metrics.height - 18) / 2) : 0
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
            radius: 9
            color: bar.mark
            Canvas {
                id: glyph
                anchors.fill: parent
                property string kind: bar.severity
                property color ink: Theme.dark ? "#1C1D26" : "#FFFFFF"
                onKindChanged: requestPaint()
                onInkChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = ink;
                    ctx.fillStyle = ink;
                    ctx.lineWidth = 1.8;
                    ctx.lineCap = "round";
                    ctx.lineJoin = "round";
                    ctx.beginPath();
                    if (kind === "success") {
                        ctx.moveTo(5, 9.2);
                        ctx.lineTo(7.8, 12);
                        ctx.lineTo(13, 6.4);
                        ctx.stroke();
                    } else if (kind === "info") {
                        ctx.moveTo(9, 8.4);
                        ctx.lineTo(9, 13);
                        ctx.stroke();
                        ctx.beginPath();
                        ctx.arc(9, 5.4, 1.1, 0, 2 * Math.PI);
                        ctx.fill();
                    } else {
                        ctx.moveTo(9, 4.8);
                        ctx.lineTo(9, 9.8);
                        ctx.stroke();
                        ctx.beginPath();
                        ctx.arc(9, 12.8, 1.1, 0, 2 * Math.PI);
                        ctx.fill();
                    }
                }
            }
        }
        Label {
            id: message
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            text: bar.text
            color: Theme.text
            wrapMode: Text.Wrap
            font.pixelSize: Theme.bodySize + 1
        }
        RowLayout {
            id: buttonRow
            Layout.alignment: Qt.AlignVCenter
            spacing: 8
        }
    }
}
