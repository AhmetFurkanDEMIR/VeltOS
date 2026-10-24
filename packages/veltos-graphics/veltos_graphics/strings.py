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
    # Buttons
    "install_driver": ("Install driver", "Sürücüyü yükle"),
    "install_parts": ("Install", "Yükle"),
    "update_driver": ("Check for updates", "Güncelleştirmeleri denetle"),
    "restart_now": ("Restart now", "Şimdi yeniden başlat"),
    "use_open": ("Use the open-source driver", "Açık kaynaklı sürücüyü kullan"),
    "show_properties": ("Properties", "Özellikler"),
    # Progress
    "busy_refresh": ("Getting the package lists…", "Paket listeleri alınıyor…"),
    "busy_detect": ("Finding the right driver for this card…", "Bu kart için doğru sürücü bulunuyor…"),
    "busy_install": ("Installing the driver…", "Sürücü yükleniyor…"),
    "busy_update": ("Updating the driver…", "Sürücü güncelleştiriliyor…"),
    "busy_remove": ("Removing NVIDIA's driver…", "NVIDIA'nın sürücüsü kaldırılıyor…"),
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
