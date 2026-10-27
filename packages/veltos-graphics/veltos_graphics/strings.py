"""Texts of VeltOS Graphics Cards (English, Turkish)."""

import os

TEXTS = {
    "app_title": ("Graphics Cards", "Ekran Kartları"),
    "subtitle": ("Your graphics cards, their drivers and properties",
                 "Ekran kartlarınız, sürücüleri ve özellikleri"),
    "refresh": ("Refresh", "Yenile"),
    "loading": ("Looking for graphics cards…", "Ekran kartları aranıyor…"),
    "no_cards": ("No graphics card was found.", "Ekran kartı bulunamadı."),
    "driver_in_use": ("Driver: {driver}", "Sürücü: {driver}"),
    "no_driver": ("No driver in use", "Kullanılan sürücü yok"),
    # Driver names
    "drv_nvidia": ("NVIDIA (proprietary)", "NVIDIA (kapalı kaynak)"),
    "drv_nouveau": ("Nouveau (open source)", "Nouveau (açık kaynak)"),
    "drv_amdgpu": ("AMDGPU (open source)", "AMDGPU (açık kaynak)"),
    "drv_radeon": ("Radeon (open source)", "Radeon (açık kaynak)"),
    "drv_i915": ("Intel i915 (open source)", "Intel i915 (açık kaynak)"),
    "drv_xe": ("Intel Xe (open source)", "Intel Xe (açık kaynak)"),
    "drv_virtual": ("Virtual machine's display", "Sanal makinenin ekranı"),
    # States
    "st_proprietary": ("NVIDIA's driver is installed and in use.",
                       "NVIDIA'nın sürücüsü kurulu ve kullanılıyor."),
    "st_restart": ("NVIDIA's driver is installed. Restart the PC to start using it.",
                   "NVIDIA'nın sürücüsü kuruldu. Kullanmaya başlamak için bilgisayarı yeniden başlatın."),
    "st_available": ("NVIDIA's driver is available for this card. It gives the best performance in games "
                     "and 3D apps.",
                     "Bu kart için NVIDIA'nın sürücüsü var. Oyunlarda ve 3B uygulamalarda en iyi performansı "
                     "verir."),
    "st_missing": ("Some parts of this card's driver are not installed: {packages}.",
                   "Bu kartın sürücüsünün bazı parçaları kurulu değil: {packages}."),
    "st_ready": ("The driver is complete and comes with VeltOS.",
                 "Sürücü eksiksiz ve VeltOS ile birlikte geliyor."),
    "st_unsupported": ("This card needs an older NVIDIA driver that Debian 13 no longer has. It keeps "
                       "using the open-source Nouveau driver.",
                       "Bu kart, Debian 13'te artık olmayan eski bir NVIDIA sürücüsü istiyor. Açık kaynaklı "
                       "Nouveau sürücüsünü kullanmaya devam eder."),
    "st_virtual": ("This is a virtual machine's display; no driver needs to be installed.",
                   "Bu bir sanal makinenin ekranı; sürücü kurmak gerekmez."),
    "st_unknown": ("No driver is offered for this card.", "Bu kart için sürücü sunulmuyor."),
    "st_failed_key": ("NVIDIA's driver did not start: Secure Boot does not accept its key yet. Register the "
                      "key below, then restart.",
                      "NVIDIA'nın sürücüsü başlamadı: Güvenli Önyükleme anahtarını henüz kabul etmiyor. "
                      "Anahtarı aşağıda kaydedip yeniden başlatın."),
    "st_failed_build": ("NVIDIA's driver did not start: it was not built for this version of Linux. Repair "
                        "builds it again.",
                        "NVIDIA'nın sürücüsü başlamadı: Linux'un bu sürümü için derlenmemiş. Onar, sürücüyü "
                        "yeniden derler."),
    "st_failed_start": ("NVIDIA's driver is installed but did not start. The driver log tells why; the "
                        "open-source driver works without it.",
                        "NVIDIA'nın sürücüsü kurulu ama başlamadı. Nedenini sürücü günlüğünde görebilirsiniz; "
                        "açık kaynaklı sürücü onsuz çalışır."),
    # Buttons
    "install_driver": ("Install driver", "Sürücüyü yükle"),
    "install_parts": ("Install", "Yükle"),
    "update_driver": ("Check for updates", "Güncelleştirmeleri denetle"),
    "restart_now": ("Restart now", "Şimdi yeniden başlat"),
    "use_open": ("Use the open-source driver", "Açık kaynaklı sürücüyü kullan"),
    "show_properties": ("Properties", "Özellikler"),
    "repair_driver": ("Repair", "Onar"),
    "details": ("Details", "Ayrıntılar"),
    "driver_log": ("Driver log", "Sürücü günlüğü"),
    # The driver log window
    "log_title": ("Driver log", "Sürücü günlüğü"),
    "log_intro": ("What VeltOS did with the drivers and what the system says about them. Copy or save it "
                  "to ask for help.",
                  "VeltOS'un sürücülerle yaptıkları ve sistemin onlar hakkında söyledikleri. Yardım istemek "
                  "için kopyalayın veya kaydedin."),
    "log_kernel": ("Add kernel messages", "Çekirdek iletilerini ekle"),
    "log_copy": ("Copy", "Kopyala"),
    "log_save": ("Save and open", "Kaydet ve aç"),
    "log_close": ("Close", "Kapat"),
    "log_copied": ("The log was copied.", "Günlük kopyalandı."),
    "log_saved": ("Saved as {path}", "Kaydedildi: {path}"),
    "log_save_failed": ("The log could not be saved.", "Günlük kaydedilemedi."),
    "log_kernel_failed": ("The kernel messages could not be read (administrator permission is needed).",
                          "Çekirdek iletileri okunamadı (yönetici izni gerekir)."),
    "log_file": ("Graphics driver log", "Ekran kartı sürücü günlüğü"),
    # Progress
    "busy_refresh": ("Getting the package lists…", "Paket listeleri alınıyor…"),
    "busy_detect": ("Finding the right driver for this card…", "Bu kart için doğru sürücü bulunuyor…"),
    "busy_install": ("Installing the driver…", "Sürücü yükleniyor…"),
    "busy_update": ("Updating the driver…", "Sürücü güncelleştiriliyor…"),
    "busy_remove": ("Removing NVIDIA's driver…", "NVIDIA'nın sürücüsü kaldırılıyor…"),
    "busy_dkms": ("Building NVIDIA's driver for this version of Linux…",
                  "NVIDIA'nın sürücüsü Linux'un bu sürümü için derleniyor…"),
    "done_repair": ("Done. Restart the PC to use NVIDIA's driver.",
                    "Bitti. NVIDIA'nın sürücüsünü kullanmak için bilgisayarı yeniden başlatın."),
    "failed_repair": ("NVIDIA's driver could not be built. {detail} The driver log shows the build's "
                      "messages.",
                      "NVIDIA'nın sürücüsü derlenemedi. {detail} Derleme iletileri sürücü günlüğündedir."),
    "done_current": ("The driver is up to date.", "Sürücü güncel."),
    "done_update": ("The driver was updated to its newest version.",
                    "Sürücü en yeni sürümüne güncelleştirildi."),
    "done_install": ("Done. Restart the PC to use the new driver.",
                     "Bitti. Yeni sürücüyü kullanmak için bilgisayarı yeniden başlatın."),
    "done_remove": ("Done. After a restart the card uses Nouveau.",
                    "Bitti. Yeniden başlattıktan sonra kart Nouveau'yu kullanır."),
    "failed_install": ("The driver could not be installed. {detail}", "Sürücü yüklenemedi. {detail}"),
    "failed_update": ("The driver could not be updated. {detail}", "Sürücü güncelleştirilemedi. {detail}"),
    "failed_remove": ("NVIDIA's driver could not be removed. {detail}",
                      "NVIDIA'nın sürücüsü kaldırılamadı. {detail}"),
    "failed_auth": ("Administrator permission was not given.", "Yönetici izni verilmedi."),
    "failed_network": ("Check the internet connection and try again.",
                       "İnternet bağlantısını denetleyip yeniden deneyin."),
    # Secure Boot
    "sb_title": ("Secure Boot is on", "Güvenli Önyükleme açık"),
    "sb_text": ("To load NVIDIA's driver, VeltOS must register its driver key with the PC's firmware. "
                "Choose a one-time password; at the next restart a blue screen asks for it: choose "
                "“Enroll MOK”, “Continue”, “Yes” and type this password.",
                "NVIDIA'nın sürücüsünü yüklemek için VeltOS'un sürücü anahtarını bilgisayarın üretici "
                "yazılımına kaydetmesi gerekir. Tek kullanımlık bir parola seçin; bir sonraki yeniden "
                "başlatmada mavi bir ekran bu parolayı sorar: “Enroll MOK”, “Continue”, "
                "“Yes” seçeneklerini seçip parolayı yazın."),
    "sb_password": ("One-time password", "Tek kullanımlık parola"),
    "sb_confirm": ("Confirm password", "Parolayı onaylayın"),
    "sb_register": ("Register key", "Anahtarı kaydet"),
    "sb_registered": ("The key will be registered at the next restart.",
                      "Anahtar bir sonraki yeniden başlatmada kaydedilecek."),
    "sb_mismatch": ("The passwords do not match.", "Parolalar eşleşmiyor."),
    "sb_failed": ("The key could not be registered.", "Anahtar kaydedilemedi."),
    # Properties
    "p_manufacturer": ("Manufacturer", "Üretici"),
    "p_model": ("Model", "Model"),
    "p_board": ("Board", "Kart"),
    "p_pci": ("PCI ID", "PCI kimliği"),
    "p_slot": ("Location", "Konum"),
    "p_kernel_driver": ("Kernel driver", "Çekirdek sürücüsü"),
    "p_modules": ("Kernel modules", "Çekirdek modülleri"),
    "p_driver_version": ("Driver version", "Sürücü sürümü"),
    "p_package": ("Driver package", "Sürücü paketi"),
    "p_memory": ("Video memory", "Video belleği"),
    "p_renderer": ("OpenGL renderer", "OpenGL işleyicisi"),
    "p_gl": ("OpenGL version", "OpenGL sürümü"),
    "p_mesa": ("Mesa", "Mesa"),
    "p_vulkan": ("Vulkan", "Vulkan"),
    "p_secure_boot": ("Secure Boot", "Güvenli Önyükleme"),
    "on": ("On", "Açık"),
    "off": ("Off", "Kapalı"),
    "footer": ("Drivers come from Debian's archive. NVIDIA's driver is proprietary software.",
               "Sürücüler Debian'ın arşivinden gelir. NVIDIA'nın sürücüsü kapalı kaynaklı yazılımdır."),
    "settings_row": ("Graphics cards", "Ekran kartları"),
}


def language():
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable, "")
        if value:
            return "tr" if value.split(":")[0].startswith("tr") else "en"
    return "en"


def texts(lang):
    index = 1 if lang == "tr" else 0
    return {key: pair[index] for key, pair in TEXTS.items()}
