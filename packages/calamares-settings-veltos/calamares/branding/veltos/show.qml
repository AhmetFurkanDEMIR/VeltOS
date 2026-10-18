/*
    VeltOS installer slideshow (Calamares slideshow API 2), shown while the
    system is being installed. Texts follow the installer language
    (English, Turkish); English is the fallback.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    readonly property bool turkish: Qt.locale().name.substring(0, 2) === "tr"

    Timer {
        interval: 9000
        repeat: true
        running: presentation.activatedInCalamares
        onTriggered: presentation.goToNextSlide()
    }

    VeltSlide {
        title: presentation.turkish ? "VeltOS'a hoş geldiniz" : "Welcome to VeltOS"
        body: presentation.turkish
            ? "Your PC. No Limits.\nKurulum birkaç dakika sürer. Bittiğinde bilgisayarınızı yeniden başlatın."
            : "Your PC. No Limits.\nInstallation takes a few minutes. Restart your computer when it is done."
    }

    VeltSlide {
        title: presentation.turkish ? "İlk dakikadan tanıdık" : "Familiar from the first minute"
        body: presentation.turkish
            ? "Başlat menüsü, görev çubuğu, pencereler ve dosyalar alıştığınız gibi çalışır."
            : "Start menu, taskbar, windows and files work the way you already know."
    }

    VeltSlide {
        title: presentation.turkish ? "Hafif ve hızlı" : "Light and fast"
        body: presentation.turkish
            ? "VeltOS arka plan hizmetlerini en aza indirir; bilgisayarınızın gücü uygulamalarınıza kalır."
            : "VeltOS keeps background services to a minimum, so your apps get the power of your PC."
    }

    VeltSlide {
        title: presentation.turkish ? "Güvenli ve güncel" : "Safe and up to date"
        body: presentation.turkish
            ? "Güvenlik güncellemeleri güvenilir, imzalı bir yazılım arşivinden gelir."
            : "Security updates come from a trusted, signed software archive."
    }

    function onActivate() { }
    function onLeave() { }
}
