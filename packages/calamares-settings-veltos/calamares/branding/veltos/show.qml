/*
    VeltOS installer slideshow (Calamares slideshow API 2), shown while the
    system is being installed, in the manner of Windows 11's setup screens:
    the VeltOS wallpapers crossfade behind the slides with a slow zoom,
    each slide shows a part of the system that is coming (Start, File
    Explorer, Settings, the Store, Office, Photos, Windows programs) with a
    few words, and the bottom of the screen says, beside a spinning
    progress ring, that VeltOS is being installed and the PC must stay on.
    The installer's own progress bar runs below the slideshow.

    Texts follow the installer's language (English, Turkish; English is
    the fallback). They are read again when the slideshow starts, after
    the language was chosen on the first page (Calamares retranslates only
    qsTr() texts).

    The wallpapers come from veltos-desktop (/usr/share/wallpapers); the
    navy gradient stays when one is missing.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

import QtQuick 2.15
import calamares.slideshow 1.0

import "VeltTheme.js" as Theme

Presentation {
    id: presentation

    function t(english, turkish) {
        void presentation.activatedInCalamares;
        return Qt.locale().name.substring(0, 2) === "tr" ? turkish : english;
    }

    readonly property var wallpapers: ["VeltOS", "VeltOS-Flow", "VeltOS-Glow", "VeltOS-Lake",
                                       "VeltOS-Nebula", "VeltOS-Tide", "VeltOS-Dawn", "VeltOS-Ember"]
    function wallpaper(slide) {
        const name = wallpapers[slide % wallpapers.length];
        return "file:///usr/share/wallpapers/" + name + "/contents/images_dark/1920x1080.png";
    }

    Timer {
        interval: 10000
        repeat: true
        running: presentation.activatedInCalamares
        onTriggered: presentation.goToNextSlide()
    }

    // Slides cross-fade (Calamares' Presentation only toggles `visible`).
    function switchSlides(from, to, forward) {
        // A click during a fade: settle every other slide first.
        for (const slide of presentation.slides) {
            if (slide !== from && slide !== to) {
                slide.visible = false;
                slide.opacity = 1;
            }
        }
        fade.from = from;
        fade.to = to;
        fade.restart();
        backdrop.show(presentation.currentSlide);
        return true;
    }

    SequentialAnimation {
        id: fade
        property Item from
        property Item to
        ScriptAction {
            script: {
                fade.to.opacity = 0;
                fade.to.visible = true;
            }
        }
        ParallelAnimation {
            NumberAnimation { target: fade.from; property: "opacity"; to: 0; duration: 450; easing.type: Easing.InCubic }
            NumberAnimation { target: fade.to; property: "opacity"; to: 1; duration: 650; easing.type: Easing.OutCubic }
        }
        ScriptAction {
            script: {
                fade.from.visible = false;
                fade.from.opacity = 1;
            }
        }
    }

    // The navy of the VeltOS brand, under everything.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#050818" }
            GradientStop { position: 1.0; color: "#0E1846" }
        }
    }

    // Wallpapers: two layers; the hidden one loads the next picture and
    // fades in over the other, each zooming slowly while it is shown.
    Item {
        id: backdrop
        anchors.fill: parent
        clip: true
        property int front: 0

        function show(slide) {
            const next = front === 0 ? layerB : layerA;
            next.source = presentation.wallpaper(slide);
            next.start();
            front = front === 0 ? 1 : 0;
        }

        component Layer: Image {
            id: layer
            property real zoom: 1
            anchors.centerIn: parent
            width: parent.width
            height: parent.height
            fillMode: Image.PreserveAspectCrop
            sourceSize.width: 1920
            sourceSize.height: 1080
            asynchronous: true
            opacity: 0
            scale: zoom
            property bool pending: false
            // Fade in once the picture has been read (it loads in the background).
            function start() {
                pending = true;
                if (status === Image.Ready)
                    begin();
            }
            function begin() {
                pending = false;
                drift.restart();
            }
            onStatusChanged: if (status === Image.Ready && pending) begin()
            ParallelAnimation {
                id: drift
                NumberAnimation { target: layer; property: "opacity"; from: 0; to: 1; duration: 1400; easing.type: Easing.InOutQuad }
                NumberAnimation { target: layer; property: "zoom"; from: 1.0; to: Theme.software ? 1.0 : 1.12; duration: Theme.software ? 0 : 14000; easing.type: Easing.Linear }
            }
            // The slow zoom repaints the whole screen; drawn in software
            // (no GPU) it advances ten times a second instead, a fraction
            // of a pixel at the edges each time, which looks the same and
            // leaves the CPU to the installation.
            Timer {
                running: Theme.software && layer.zoom < 1.12 && layer.opacity > 0 && presentation.activatedInCalamares
                interval: 100
                repeat: true
                onTriggered: layer.zoom = Math.min(1.12, layer.zoom + 0.12 / 140)
            }
        }
        Layer {
            id: layerA
            z: backdrop.front === 0 ? 1 : 0
        }
        Layer {
            id: layerB
            z: backdrop.front === 1 ? 1 : 0
        }
        // Calamares loads the slideshow when it starts; the first wallpaper
        // fades in when the slideshow is shown, not behind the other pages.
        Component.onCompleted: layerA.source = presentation.wallpaper(0)
    }
    onActivatedInCalamaresChanged: if (activatedInCalamares && layerA.opacity === 0) layerA.start()

    // Shade for the words: darker on the left, where the text is.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#D9050818" }
            GradientStop { position: 0.55; color: "#8C050818" }
            GradientStop { position: 1.0; color: "#40050818" }
        }
    }
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 110
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#00050818" }
            GradientStop { position: 1.0; color: "#B3050818" }
        }
    }

    VeltSlide {
        title: t("Welcome to VeltOS", "VeltOS'a hoş geldiniz")
        body: t("Your PC. No Limits.\nWhile VeltOS is being installed, here is what is waiting for you.",
                "Your PC. No Limits.\nVeltOS kurulurken sizi bekleyenlere bir göz atın.")
        points: [t("A desktop that works the way you already know", "Zaten bildiğiniz gibi çalışan bir masaüstü"),
                 t("Your Windows programs, opened with a double-click", "Çift tıkla açılan Windows programlarınız"),
                 t("Free apps from a trusted store", "Güvenilir bir mağazadan ücretsiz uygulamalar")]
    }

    VeltSlide {
        title: t("Familiar from the first minute", "İlk dakikadan tanıdık")
        body: t("Start, the taskbar, search and Task View work as on Windows 11. Pin your favourite apps and find anything by typing.",
                "Başlat, görev çubuğu, arama ve Görev Görünümü Windows 11'deki gibi çalışır. Sevdiğiniz uygulamaları sabitleyin, her şeyi yazarak bulun.")
        picture: "images/start.png"
    }

    VeltSlide {
        title: t("Your files, your way", "Dosyalarınız, sizin tarzınızda")
        body: t("File Explorer with tabs, Home, This PC and the Recycle Bin. Windows drives and USB sticks open as they are.",
                "Sekmeli Dosya Gezgini; Giriş, Bu bilgisayar ve Geri Dönüşüm Kutusu. Windows sürücüleri ve USB bellekler olduğu gibi açılır.")
        picture: "images/explorer.png"
    }

    VeltSlide {
        title: t("Settings you can find", "Kolayca bulunan ayarlar")
        body: t("Wi-Fi, Bluetooth, display, sound, accounts, personalization: every setting on one page you already know, in your language.",
                "Wi-Fi, Bluetooth, ekran, ses, hesaplar, kişiselleştirme: her ayar zaten bildiğiniz tek bir sayfada, kendi dilinizde.")
        picture: "images/settings.png"
    }

    VeltSlide {
        title: t("Apps from a trusted store", "Güvenilir bir mağazadan uygulamalar")
        body: t("Thousands of free apps and games from a signed archive, installed with one click. Updates come from the same place.",
                "İmzalı bir arşivden binlerce ücretsiz uygulama ve oyun, tek tıkla kurulur. Güncelleştirmeler de aynı yerden gelir.")
        picture: "images/store.png"
    }

    VeltSlide {
        title: t("Office, ready to work", "Office, çalışmaya hazır")
        body: t("Word, Excel and PowerPoint documents open in VeltOS Office and are saved in the same formats.",
                "Word, Excel ve PowerPoint belgeleri VeltOS Office'te açılır ve aynı biçimlerde kaydedilir.")
        picture: "images/office.png"
    }

    VeltSlide {
        title: t("Photos, music and videos", "Fotoğraflar, müzik ve videolar")
        body: t("Photos sorts your pictures by month, Media Player plays your music and videos, Camera and Snipping Tool are one click away.",
                "Fotoğraflar resimlerinizi aylara göre sıralar, Medya Oynatıcı müziklerinizi ve videolarınızı çalar; Kamera ve Ekran Alıntısı Aracı bir tık uzağınızda.")
        picture: "images/photos.png"
    }

    VeltSlide {
        title: t("Windows programs and games", "Windows programları ve oyunları")
        body: t("Open an .exe or .msi file with a double-click: VeltOS installs it and adds it to Start.",
                "Bir .exe veya .msi dosyasına çift tıklayın: VeltOS onu kurar ve Başlat'a ekler.")
        points: [t("Programs appear in Start like any other app", "Programlar Başlat'ta diğer uygulamalar gibi görünür"),
                 t("Uninstall them in Settings, as on Windows", "Windows'taki gibi Ayarlar'dan kaldırın"),
                 t("Not every program works yet; VeltOS tells you", "Her program henüz çalışmaz; VeltOS size söyler")]
    }

    VeltSlide {
        title: t("Light, safe and up to date", "Hafif, güvenli ve güncel")
        body: t("VeltOS keeps background services to a minimum, so your apps get the power of your PC. Security updates come from a trusted, signed software archive.",
                "VeltOS arka plan hizmetlerini en aza indirir; bilgisayarınızın gücü uygulamalarınıza kalır. Güvenlik güncelleştirmeleri güvenilir, imzalı bir yazılım arşivinden gelir.")
    }

    // Bottom: what is happening, as Windows Setup says it, and the slide pips.
    Item {
        id: status
        z: 10
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: parent.width * 0.07
        anchors.rightMargin: parent.width * 0.05
        anchors.bottomMargin: 22
        height: 44

        // Windows 11's progress ring, in the accent colour.
        VeltSpinner {
            id: ring
            width: 30
            height: 30
            anchors.verticalCenter: parent.verticalCenter
            color: Theme.accentOnDark
            trackColor: "#33FFFFFF"
            running: presentation.activatedInCalamares
        }
        Column {
            anchors.left: ring.right
            anchors.leftMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text {
                text: presentation.t("Installing VeltOS", "VeltOS yükleniyor")
                color: "#FFFFFF"
                font.family: "Inter"
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Text {
                text: presentation.t("This might take several minutes. Don't turn off your PC.",
                                     "Bu işlem birkaç dakika sürebilir. Bilgisayarınızı kapatmayın.")
                color: "#C9D4F5"
                font.family: "Inter"
                font.pixelSize: 13
            }
        }
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            Repeater {
                model: presentation.slides.length
                delegate: Rectangle {
                    required property int index
                    readonly property bool current: index === presentation.currentSlide
                    anchors.verticalCenter: parent.verticalCenter
                    width: current ? 18 : 6
                    height: 6
                    radius: 3
                    color: current ? "#FFFFFF" : "#66FFFFFF"
                    Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
                }
            }
        }
    }

    function onActivate() { }
    function onLeave() { }
}
