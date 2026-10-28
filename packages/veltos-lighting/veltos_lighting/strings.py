"""Texts of VeltOS Keyboard Lighting (English, Turkish), in the words of
Windows 11's Dynamic Lighting where it has them."""

import os

TEXTS = {
    "app_title": ("Keyboard Lighting", "Klavye Aydınlatması"),
    "subtitle": ("Turn your keyboard's lights on or off and choose their brightness and colour",
                 "Klavyenizin ışıklarını açın veya kapatın; parlaklığını ve rengini seçin"),
    "keyboard": ("Keyboard", "Klavye"),
    "built_in": ("Built-in keyboard", "Yerleşik klavye"),
    "one_colour": ("One colour: brightness only", "Tek renk: yalnızca parlaklık"),
    "rgb": ("Colour lighting", "Renkli aydınlatma"),
    "lighting": ("Lighting", "Aydınlatma"),
    "lighting_desc": ("Turn the keyboard's lights on or off", "Klavye ışıklarını açın veya kapatın"),
    "on": ("On", "Açık"),
    "off": ("Off", "Kapalı"),
    "brightness": ("Brightness", "Parlaklık"),
    "effects": ("Effects", "Efektler"),
    "effects_desc": ("Choose how the lights look", "Işıkların nasıl görüneceğini seçin"),
    "effect_static": ("Solid colour", "Düz renk"),
    "effect_breathing": ("Breathing", "Nefes alma"),
    "effect_cycle": ("Colour cycle", "Renk döngüsü"),
    "speed": ("Effect speed", "Efekt hızı"),
    "speed_0": ("Slow", "Yavaş"),
    "speed_1": ("Medium", "Orta"),
    "speed_2": ("Fast", "Hızlı"),
    "match_accent": ("Match my accent colour", "Vurgu rengimle eşleştir"),
    "match_accent_desc": ("The keyboard takes the accent colour of Personalization > Colours",
                          "Klavye, Kişiselleştirme > Renkler'deki vurgu rengini alır"),
    "colour": ("Colour", "Renk"),
    "custom_colour": ("Custom colour", "Özel renk"),
    "hue": ("Hue", "Ton"),
    "none_title": ("No keyboard lighting was found", "Klavye aydınlatması bulunamadı"),
    "none_text": ("This PC's keyboard has no lights VeltOS can control. Laptops whose keyboard lights up "
                  "show it here (ThinkPad, Dell, HP, Lenovo, ASUS, MSI, System76 and others). Keyboards "
                  "with their own controller (USB gaming keyboards) need their maker's app.",
                  "Bu bilgisayarın klavyesinde VeltOS'un denetleyebileceği ışık yok. Klavyesi ışıklı "
                  "dizüstü bilgisayarlar burada görünür (ThinkPad, Dell, HP, Lenovo, ASUS, MSI, System76 ve "
                  "diğerleri). Kendi denetleyicisi olan klavyeler (USB oyun klavyeleri) üreticisinin "
                  "uygulamasını ister."),
    # MSI laptops (msi.py): Debian's kernel lights no MSI keyboard.
    "msi_title": ("MSI keyboard light", "MSI klavye ışığı"),
    "msi_checking": ("Looking at this MSI laptop…", "Bu MSI dizüstü bilgisayar inceleniyor…"),
    "msi_offer": ("The keyboard light of this {model} needs MSI's laptop driver (msi-ec), which VeltOS builds for "
                  "this PC. DKMS and the kernel headers are downloaded from Debian first (about 75 MB; an "
                  "internet connection is needed).",
                  "Bu {model} cihazının klavye ışığı MSI'ın dizüstü sürücüsünü (msi-ec) ister; VeltOS onu bu "
                  "bilgisayar için derler. Önce Debian'dan DKMS ve çekirdek başlık dosyaları indirilir (yaklaşık "
                  "75 MB; internet bağlantısı gerekir)."),
    "msi_firmware": ("Firmware {firmware}", "Üretici yazılımı {firmware}"),
    "msi_firmware_unread": ("VeltOS could not read the laptop's firmware version, so it cannot tell beforehand "
                            "whether msi-ec knows it.",
                            "VeltOS dizüstü bilgisayarın üretici yazılımı sürümünü okuyamadı; msi-ec'in onu "
                            "tanıyıp tanımadığı önceden bilinemiyor."),
    "msi_install": ("Install MSI driver", "MSI sürücüsünü yükle"),
    "msi_downloading": ("Downloading DKMS and the kernel headers…", "DKMS ve çekirdek başlık dosyaları indiriliyor…"),
    "msi_building": ("Building and starting MSI's driver…", "MSI sürücüsü derleniyor ve başlatılıyor…"),
    "msi_done": ("MSI's driver is running.", "MSI sürücüsü çalışıyor."),
    "msi_no_light": ("MSI's driver (msi-ec) cannot control the keyboard light of the {model} yet: its RGB "
                     "keyboard has a controller of its own.",
                     "MSI sürücüsü (msi-ec), {model} cihazının klavye ışığını henüz denetleyemiyor: RGB klavyesinin "
                     "kendi denetleyicisi var."),
    "msi_unknown": ("MSI's driver (msi-ec) does not know this {model} yet, so VeltOS cannot control its keyboard "
                    "light.",
                    "MSI sürücüsü (msi-ec) bu {model} cihazını henüz tanımıyor; bu yüzden VeltOS klavye ışığını "
                    "denetleyemiyor."),
    "msi_failed_auth": ("Administrator permission was not given.", "Yönetici izni verilmedi."),
    "msi_failed_network": ("DKMS and the kernel headers could not be downloaded. Check the internet connection.",
                           "DKMS ve çekirdek başlık dosyaları indirilemedi. İnternet bağlantısını denetleyin."),
    "msi_failed_packages": ("DKMS and the kernel headers could not be installed.",
                            "DKMS ve çekirdek başlık dosyaları yüklenemedi."),
    "msi_failed_build": ("MSI's driver could not be built or started.", "MSI sürücüsü derlenemedi veya başlatılamadı."),
    "msi_try_again": ("Try again", "Yeniden dene"),
    "msi_key": ("Secure Boot is on: VeltOS must register the driver's key with the PC's firmware. Choose a "
                "one-time password; at the next restart a blue screen asks for it: choose “Enroll MOK”, "
                "“Continue”, “Yes” and type this password.",
                "Güvenli Önyükleme açık: VeltOS'un sürücü anahtarını bilgisayarın üretici yazılımına kaydetmesi "
                "gerekir. Tek kullanımlık bir parola seçin; bir sonraki yeniden başlatmada mavi bir ekran bu "
                "parolayı sorar: “Enroll MOK”, “Continue”, “Yes” seçeneklerini seçip parolayı yazın."),
    "msi_key_password": ("One-time password", "Tek kullanımlık parola"),
    "msi_key_confirm": ("Confirm password", "Parolayı onaylayın"),
    "msi_key_register": ("Register key", "Anahtarı kaydet"),
    "msi_key_mismatch": ("The passwords do not match.", "Parolalar eşleşmiyor."),
    "msi_key_failed": ("The key could not be registered.", "Anahtar kaydedilemedi."),
    "msi_restart": ("The key will be registered at the next restart; the keyboard light works after it.",
                    "Anahtar bir sonraki yeniden başlatmada kaydedilecek; klavye ışığı ondan sonra çalışır."),
    "msi_restart_now": ("Restart now", "Şimdi yeniden başlat"),
    "failed": ("The keyboard lighting could not be changed.", "Klavye aydınlatması değiştirilemedi."),
    "refresh": ("Refresh", "Yenile"),
    "settings_row": ("Keyboard lighting", "Klavye aydınlatması"),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable, "")
        if value:
            return "tr" if value.split(":")[0].lower().startswith("tr") else "en"
    return "en"


def texts(lang):
    index = 1 if lang == "tr" else 0
    return {key: pair[index] for key, pair in TEXTS.items()}
