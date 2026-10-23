/*
    VeltOS installer: last page (Calamares module finishedq).

    When the installation worked: "VeltOS is ready" with rings pulsing out
    of a check mark, and Restart now / Restart later, as Windows Setup
    ends. When a step failed (Calamares then also shows its error window):
    what went wrong and the failed step's output in a terminal-style box,
    the only place the installer ever shows command output (the product
    owner: logs only when something fails). The installer's navigation
    buttons are hidden on this page (calamares-navigation.qml); the
    page's own buttons end the installer.

    Calamares provides `config` (finished module): failed, failureMessage,
    failureDetails, restartNowWanted, doRestart(bool); and ViewManager
    (quit(), logFilePath).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

import "VeltTheme.js" as Theme

VeltPage {
    id: page

    readonly property bool failed: config.failed

    picture: failed ? "ill-error.svg" : "ill-done.svg"
    celebrate: !failed
    title: failed ? t("VeltOS couldn't be installed", "VeltOS kurulamadı")
                  : t("VeltOS is ready", "VeltOS hazır")
    subtitle: failed
              ? t("Something went wrong during the installation. The output below shows what happened. You can close the installer and try again, or keep using VeltOS from the installation media.",
                  "Kurulum sırasında bir sorun oluştu. Aşağıdaki çıktı ne olduğunu gösteriyor. Kurulum programını kapatıp yeniden deneyebilir veya VeltOS'u kurulum ortamından kullanmaya devam edebilirsiniz.")
              : t("Restart your PC to start using VeltOS. Remove the USB stick or DVD when the screen goes dark.",
                  "VeltOS'u kullanmaya başlamak için bilgisayarınızı yeniden başlatın. Ekran karardığında USB belleği veya DVD'yi çıkarın.")

    function restartLater() {
        // Calamares restarts when it quits if restartNowWanted is set.
        config.restartNowWanted = false;
        ViewManager.quit();
    }

    // Success: what comes next.
    Repeater {
        model: page.failed ? [] : [
            page.t("Your files and settings start fresh on the new system.", "Yeni sistemde dosyalarınız ve ayarlarınız sıfırdan başlar."),
            page.t("Sign in with the account you created.", "Oluşturduğunuz hesapla oturum açın."),
            page.t("Updates and new apps come from VeltOS Store.", "Güncelleştirmeler ve yeni uygulamalar VeltOS Store'dan gelir.")
        ]
        delegate: RowLayout {
            required property var modelData
            required property int index
            Layout.fillWidth: true
            spacing: 10
            opacity: 0
            Rectangle {
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
                radius: 10
                color: Theme.c.successBack
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        ctx.strokeStyle = Theme.c.success;
                        ctx.lineWidth = 1.6;
                        ctx.lineCap = "round";
                        ctx.lineJoin = "round";
                        ctx.beginPath();
                        ctx.moveTo(5.5, 10.5);
                        ctx.lineTo(8.5, 13.5);
                        ctx.lineTo(14.5, 7);
                        ctx.stroke();
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                text: modelData
                color: Theme.c.text
                font.family: "Inter"
                font.pixelSize: 14
                wrapMode: Text.WordWrap
            }
            SequentialAnimation on opacity {
                running: page.visible
                PauseAnimation { duration: 450 + index * 180 }
                NumberAnimation { from: 0; to: 1; duration: 320; easing.type: Easing.OutCubic }
            }
        }
    }

    // Failure: the message and the failed step's output.
    Text {
        Layout.fillWidth: true
        visible: page.failed && text !== ""
        text: config.failureMessage
        color: Theme.c.error
        font.family: "Inter"
        font.pixelSize: 14
        font.weight: Font.DemiBold
        wrapMode: Text.WordWrap
        textFormat: Text.StyledText
    }
    Rectangle {
        id: terminal
        visible: page.failed
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 160
        radius: 8
        color: "#0C0C0C"
        border.width: 1
        border.color: "#2B2B2B"
        clip: true

        // A tab-like header, as Windows Terminal draws it.
        Rectangle {
            id: header
            width: parent.width
            height: 34
            radius: 8
            color: "#1F1F1F"
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 8
                color: "#1F1F1F"
            }
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                text: page.t("Output of the failed step", "Başarısız adımın çıktısı")
                color: "#CCCCCC"
                font.family: "Inter"
                font.pixelSize: 12
            }
            Rectangle {
                id: copyButton
                anchors.right: parent.right
                anchors.rightMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                width: copyLabel.implicitWidth + 24
                height: 24
                radius: 4
                color: copyMouse.pressed ? "#3A3A3A" : (copyMouse.containsMouse ? "#2D2D2D" : "transparent")
                property bool copied: false
                Text {
                    id: copyLabel
                    anchors.centerIn: parent
                    text: copyButton.copied ? page.t("Copied", "Kopyalandı") : page.t("Copy", "Kopyala")
                    color: "#CCCCCC"
                    font.family: "Inter"
                    font.pixelSize: 12
                }
                MouseArea {
                    id: copyMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        output.selectAll();
                        output.copy();
                        output.deselect();
                        copyButton.copied = true;
                    }
                }
            }
        }
        Flickable {
            id: flick
            anchors.fill: parent
            anchors.topMargin: header.height + 6
            anchors.leftMargin: 14
            anchors.rightMargin: 6
            anchors.bottomMargin: 10
            contentWidth: width - 12
            contentHeight: output.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            TextEdit {
                id: output
                width: flick.width - 12
                readOnly: true
                selectByMouse: true
                selectionColor: "#264F78"
                selectedTextColor: "#FFFFFF"
                wrapMode: TextEdit.WrapAnywhere
                textFormat: TextEdit.PlainText
                // Calamares marks up the failed command ("Command <i>...</i> finished with
                // exit code 1."); the box shows plain terminal text.
                text: config.failureDetails !== ""
                      ? config.failureDetails.replace(/<br\s*\/?>/g, "\n").replace(/<\/?(i|b|code|strong)>/g, "")
                      : page.t("The step did not report any output.", "Adım herhangi bir çıktı bildirmedi.")
                color: "#CCCCCC"
                font.family: "Cascadia Mono"
                font.pixelSize: 12
            }
        }
    }
    Text {
        Layout.fillWidth: true
        visible: page.failed && ViewManager.logFilePath !== ""
        text: page.t("The installer's full log: ", "Kurulum programının tam günlüğü: ") + ViewManager.logFilePath
        color: Theme.c.subtext
        font.family: "Inter"
        font.pixelSize: 12
        wrapMode: Text.WrapAnywhere
    }

    Item {
        visible: !page.failed
        Layout.fillHeight: true
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 8
        spacing: 8
        Item { Layout.fillWidth: true }
        VeltButton {
            visible: !page.failed
            primary: true
            label: page.t("Restart now", "Şimdi yeniden başlat")
            onActivated: config.doRestart(true)
        }
        VeltButton {
            visible: !page.failed
            label: page.t("Restart later", "Daha sonra yeniden başlat")
            onActivated: page.restartLater()
        }
        VeltButton {
            visible: page.failed
            primary: true
            label: page.t("Close", "Kapat")
            onActivated: page.restartLater()
        }
    }
}
