/*
    VeltOS installer: how Windows programs open (Calamares module
    packagechooserq, instance "windowsapps"; product owner, 2026-10-27:
    "the user chooses Wine or Bottles during the installation"). Two cards
    in the layout of Windows 11's setup choices:

    - Wine (built in, the default): VeltOS' own Windows environment, a
      double-click on an .exe or .msi installs or opens it. Works offline.
    - Bottles: a separate app that keeps programs in "bottles" of their
      own. It comes from Flathub (not from VeltOS' sources), so it is installed at
      the first start of the new system, with an internet connection.

    The choice goes to `config.packageChoice` ("wine" or "bottles");
    Calamares keeps it as packagechooser_windowsapps and the windows-apps
    job writes it to the new system (/etc/veltos/windows-apps.conf).

    SPDX-License-Identifier: GPL-3.0-or-later
*/
import io.calamares.core 1.0
import io.calamares.ui 1.0

import QtQuick
import QtQuick.Layouts

import "VeltTheme.js" as Theme

VeltPage {
    id: page

    picture: "ill-windows-apps.svg"
    title: t(".exe programs: how should they open?", ".exe programları nasıl açılsın?")
    subtitle: t("VeltOS opens .exe and .msi files with a double-click. Choose how. You can change it later in Settings.",
                "VeltOS .exe ve .msi dosyalarını çift tıklamayla açar. Nasıl açılacağını seçin. Daha sonra Ayarlar'dan değiştirebilirsiniz.")

    property string choice: "wine"
    onChoiceChanged: config.packageChoice = choice
    Component.onCompleted: config.packageChoice = choice

    component Choice: Rectangle {
        id: card
        property string value
        property string heading
        property string detail
        property string note
        readonly property bool chosen: page.choice === value
        Layout.fillWidth: true
        implicitHeight: column.implicitHeight + 32
        radius: 8
        color: chosen ? Theme.accentSoft : (mouse.containsMouse ? Theme.c.cardHover : Theme.c.card)
        border.width: chosen ? 2 : 1
        border.color: chosen ? Theme.accent : Theme.c.border
        activeFocusOnTab: true
        Accessible.role: Accessible.RadioButton
        Accessible.name: heading
        Accessible.checked: chosen
        Keys.onSpacePressed: page.choice = value
        Behavior on color { ColorAnimation { duration: 120 } }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 14
            // Windows 11 radio mark.
            Rectangle {
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 2
                width: 20
                height: 20
                radius: 10
                color: card.chosen ? Theme.accent : "transparent"
                border.width: card.chosen ? 0 : 1
                border.color: Theme.c.knob
                Rectangle {
                    anchors.centerIn: parent
                    width: card.chosen ? 8 : 0
                    height: width
                    radius: width / 2
                    color: Theme.onAccent
                    Behavior on width { NumberAnimation { duration: 120 } }
                }
            }
            ColumnLayout {
                id: column
                Layout.fillWidth: true
                spacing: 4
                Text {
                    Layout.fillWidth: true
                    text: card.heading
                    color: Theme.c.text
                    font.family: "Inter"
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    text: card.detail
                    color: Theme.c.subtext
                    font.family: "Inter"
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    visible: text !== ""
                    text: card.note
                    color: Theme.c.muted
                    font.family: "Inter"
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: page.choice = card.value
        }
    }

    Choice {
        objectName: "choiceWine"
        value: "wine"
        heading: page.t("Wine, built in (recommended)", "Yerleşik Wine (önerilir)")
        detail: page.t("A double-click installs or opens the program in VeltOS' own Wine environment, in VeltOS' installer window. Works without the internet.",
                       "Çift tıklama, programı VeltOS'un kendi Wine ortamında, VeltOS'un yükleyici penceresinde yükler veya açar. İnternetsiz çalışır.")
    }
    Choice {
        objectName: "choiceBottles"
        value: "bottles"
        heading: page.t("Bottles", "Bottles")
        detail: page.t("A separate app that keeps each program in a \"bottle\" of its own, with its own settings. Good for games and programs that need special settings.",
                       "Her programı kendi ayarlarıyla ayrı bir \"şişe\"de tutan ayrı bir uygulama. Oyunlar ve özel ayar isteyen programlar için uygundur.")
        note: page.t("Bottles comes from Flathub, not from VeltOS' own package sources: it is downloaded at the first start (more than 1.5 GB with its Wine environment; an internet connection is needed).",
                     "Bottles VeltOS'un kendi paket kaynaklarından değil, Flathub'dan gelir: ilk açılışta indirilir (Wine ortamıyla birlikte 1,5 GB'tan fazla; internet bağlantısı gerekir).")
    }

    Text {
        Layout.fillWidth: true
        Layout.topMargin: 4
        text: page.t(".exe programs can read and change your files: open only programs you trust.",
                     ".exe programları dosyalarınızı okuyup değiştirebilir: yalnızca güvendiğiniz programları açın.")
        color: Theme.c.subtext
        font.family: "Inter"
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }

    Item {
        Layout.fillHeight: true
    }
}
