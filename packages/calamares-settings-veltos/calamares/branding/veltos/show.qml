/*
    VeltOS installer slideshow (Calamares slideshow API 2), shown while the
    system is being installed: pictures of the system that is coming
    (Start, Settings, File Explorer, the Store) with a few words about each
    part, in the installer's language (English, Turkish; English is the
    fallback). Each slide animates in (VeltSlide.qml).

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    readonly property bool turkish: Qt.locale().name.substring(0, 2) === "tr"
    function t(english, turkish) { return presentation.turkish ? turkish : english; }

    Timer {
        interval: 11000
        repeat: true
        running: presentation.activatedInCalamares
        onTriggered: presentation.goToNextSlide()
    }

    VeltSlide {
        title: t("Welcome to VeltOS", "VeltOS'a hoş geldiniz")
        body: t("Your PC. No Limits.\nInstallation takes a few minutes. Here is what is waiting for you.",
                "Your PC. No Limits.\nKurulum birkaç dakika sürer. Sizi bekleyenler:")
        points: [t("A desktop that works the way you already know", "Zaten bildiğiniz gibi çalışan bir masaüstü"),
                 t("Your Windows programs, opened with a double-click", "Çift tıkla açılan Windows programlarınız"),
                 t("Free apps from a trusted store", "Güvenilir bir mağazadan ücretsiz uygulamalar")]
    }

    VeltSlide {
        title: t("Familiar from the first minute", "İlk dakikadan tanıdık")
        body: t("Start, the taskbar, search and the windows work as on Windows 11. Pin your favourite apps and find anything by typing.",
                "Başlat, görev çubuğu, arama ve pencereler Windows 11'deki gibi çalışır. Sevdiğiniz uygulamaları sabitleyin, her şeyi yazarak bulun.")
        picture: "images/start.png"
    }

    VeltSlide {
        title: t("Settings you can find", "Kolayca bulunan ayarlar")
        body: t("Wi-Fi, Bluetooth, display, sound, accounts, personalization: every setting on one page you already know, in your language.",
                "Wi-Fi, Bluetooth, ekran, ses, hesaplar, kişiselleştirme: her ayar zaten bildiğiniz tek bir sayfada, kendi dilinizde.")
        picture: "images/settings.png"
    }

    VeltSlide {
        title: t("Your files, your way", "Dosyalarınız, sizin tarzınızda")
        body: t("File Explorer with tabs, Quick access, This PC and the Recycle Bin. Windows drives open as they are.",
                "Sekmeli Dosya Gezgini, Hızlı erişim, Bu bilgisayar ve Geri Dönüşüm Kutusu. Windows sürücüleri olduğu gibi açılır.")
        picture: "images/explorer.png"
    }

    VeltSlide {
        title: t("Apps from a trusted store", "Güvenilir bir mağazadan uygulamalar")
        body: t("Thousands of free apps and games from a signed archive, installed with one click. Updates come from the same place.",
                "İmzalı bir arşivden binlerce ücretsiz uygulama ve oyun, tek tıkla kurulur. Güncelleştirmeler de aynı yerden gelir.")
        picture: "images/store.png"
    }

    VeltSlide {
        title: t("Windows programs and games", "Windows programları ve oyunları")
        body: t("Open an .exe or .msi file with a double-click: VeltOS installs it and adds it to Start. Games use your graphics card directly.",
                "Bir .exe veya .msi dosyasına çift tıklayın: VeltOS onu kurar ve Başlat'a ekler. Oyunlar ekran kartınızı doğrudan kullanır.")
        points: [t("Shared Windows environment, ready in a minute", "Bir dakikada hazır ortak Windows ortamı"),
                 t("Programs appear in Start like any other app", "Programlar Başlat'ta diğer uygulamalar gibi görünür"),
                 t("Not every program works yet; the runner tells you", "Her program henüz çalışmaz; çalıştırıcı size söyler")]
    }

    VeltSlide {
        title: t("Light, safe and up to date", "Hafif, güvenli ve güncel")
        body: t("VeltOS keeps background services to a minimum, so your apps get the power of your PC. Security updates come from a trusted, signed software archive.",
                "VeltOS arka plan hizmetlerini en aza indirir; bilgisayarınızın gücü uygulamalarınıza kalır. Güvenlik güncelleştirmeleri güvenilir, imzalı bir yazılım arşivinden gelir.")
    }

    function onActivate() { }
    function onLeave() { }
}
