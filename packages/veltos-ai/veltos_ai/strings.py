"""Texts of VeltOS AI (English and Turkish), in the words of Windows 11's
Copilot pane."""

import os

TEXTS = {
    "app_title": ("VeltOS AI", "VeltOS AI"),
    "new_chat": ("New chat", "Yeni sohbet"),
    "settings": ("Settings", "Ayarlar"),
    "close": ("Close", "Kapat"),
    "greeting": ("Hi, how can I help?", "Merhaba, nasıl yardımcı olabilirim?"),
    "greeting_desc": ("Ask me anything, or let me change things on this PC for you: I ask before I do.",
                      "Bana her şeyi sorun ya da bu bilgisayarda bir şeyleri değiştirmemi isteyin: yapmadan önce "
                      "sorarım."),
    "ask": ("Ask me anything…", "Bana bir şey sorun…"),
    "send": ("Send", "Gönder"),
    "stop": ("Stop responding", "Yanıtlamayı durdur"),
    "copy": ("Copy", "Kopyala"),
    "copied": ("Copied", "Kopyalandı"),
    "thinking": ("Working on it…", "Üzerinde çalışıyorum…"),
    "suggest_dark": ("Switch to dark mode", "Koyu moda geç"),
    "suggest_info": ("What's in this PC?", "Bu bilgisayarda neler var?"),
    "suggest_bluetooth": ("Turn on Bluetooth", "Bluetooth'u aç"),
    "suggest_mail": ("Write an e-mail inviting my team to lunch", "Ekibimi öğle yemeğine davet eden bir e-posta yaz"),
    # Setup and settings
    "setup_title": ("Choose your AI", "Yapay zekânızı seçin"),
    "setup_desc": ("VeltOS AI works with the service you choose and your own API key. Your messages go to that "
                   "service; the key stays on this PC.",
                   "VeltOS AI seçtiğiniz hizmetle ve kendi API anahtarınızla çalışır. İletileriniz o hizmete "
                   "gider; anahtar bu bilgisayarda kalır."),
    "provider": ("Service", "Hizmet"),
    "api_key": ("API key", "API anahtarı"),
    "api_key_placeholder": ("Paste your API key", "API anahtarınızı yapıştırın"),
    "model": ("Model", "Model"),
    "load_models": ("Show models", "Modelleri göster"),
    "loading_models": ("Getting models…", "Modeller alınıyor…"),
    "endpoint": ("Endpoint", "Uç nokta"),
    "endpoint_placeholder": ("https://your-resource.openai.azure.com", "https://kaynaginiz.openai.azure.com"),
    "deployment": ("Deployment name", "Dağıtım adı"),
    "get_key": ("Get a key", "Anahtar alın"),
    # The local model (local.py, LocalModels.qml)
    "local_default_desc": ("Turkish, English and many more languages; works offline and free once downloaded. "
                           "It can change settings and open apps for you, after you allow it. A small model: "
                           "it may make mistakes.",
                           "Türkçe, İngilizce ve daha birçok dil; indirildikten sonra çevrimdışı ve ücretsiz "
                           "çalışır. İzin verdiğinizde ayarları değiştirebilir, uygulamaları açabilir. Küçük bir "
                           "model: hata yapabilir."),
    "download": ("Download", "İndir"),
    "downloading": ("Downloading the model…", "Model indiriliyor…"),
    "download_progress": ("{done} of {total} · {speed}", "{done} / {total} · {speed}"),
    "download_failed": ("The download didn't finish.", "İndirme tamamlanamadı."),
    "use_model": ("Use", "Kullan"),
    "in_use": ("In use", "Kullanımda"),
    "delete_model": ("Delete this model", "Bu modeli sil"),
    "model_license": ("Licence", "Lisans"),
    "downloaded_models": ("Downloaded models", "İndirilen modeller"),
    "hub_title": ("More models from Hugging Face", "Hugging Face'ten daha fazla model"),
    "hub_desc": ("Search Hugging Face for GGUF models. Bigger models answer better but need more memory "
                 "and time.",
                 "Hugging Face'te GGUF modelleri arayın. Büyük modeller daha iyi yanıt verir ama daha çok bellek "
                 "ve zaman ister."),
    "hub_placeholder": ("For example: qwen 0.5b, gemma, phi", "Örneğin: qwen 0.5b, gemma, phi"),
    "hub_error": ("Can't reach Hugging Face. Check your internet connection.",
                  "Hugging Face'e ulaşılamıyor. İnternet bağlantınızı denetleyin."),
    "search": ("Search", "Ara"),
    "back": ("Back", "Geri"),
    "start_chat": ("Start chatting", "Sohbete başla"),
    "local_note": ("The local model runs on this PC: nothing you write leaves it. It asks before it changes "
                   "anything.",
                   "Yerel model bu bilgisayarda çalışır: yazdıklarınız bilgisayardan çıkmaz. Bir şeyi "
                   "değiştirmeden önce izninizi ister."),
    "local_no_engine": ("The local model engine (veltos-llama) isn't installed. Install it from VeltOS Store.",
                        "Yerel model motoru (veltos-llama) kurulu değil. VeltOS Mağaza'dan kurun."),
    "error_local": ("The local model couldn't start: {detail}", "Yerel model başlatılamadı: {detail}"),
    "error_local_model": ("The chosen model file is missing. Download it again in Settings.",
                          "Seçilen model dosyası yok. Ayarlar'dan yeniden indirin."),
    "save": ("Save", "Kaydet"),
    "cancel": ("Cancel", "İptal"),
    "remove_key": ("Remove key", "Anahtarı kaldır"),
    "key_saved": ("Key saved on this PC", "Anahtar bu bilgisayara kaydedildi"),
    "key_note": ("The key is kept in ~/.config/veltos/ai.json, readable only by your account.",
                 "Anahtar ~/.config/veltos/ai.json dosyasında, yalnızca hesabınızın okuyabileceği şekilde tutulur."),
    "allow_actions": ("Let VeltOS AI change settings and open apps (it asks every time)",
                      "VeltOS AI ayarları değiştirebilsin ve uygulama açabilsin (her seferinde sorar)"),
    "copilot_note": ("Microsoft's Copilot has no API key for personal use; this uses Microsoft's Azure OpenAI "
                     "service with your own resource.",
                     "Microsoft'un Copilot'unun kişisel kullanım için API anahtarı yok; bu seçenek Microsoft'un "
                     "Azure OpenAI hizmetini kendi kaynağınızla kullanır."),
    "privacy_note": ("AI can make mistakes. Check important information.",
                     "Yapay zekâ hata yapabilir. Önemli bilgileri denetleyin."),
    # Actions
    "action_ask": ("VeltOS AI wants to", "VeltOS AI şunu yapmak istiyor"),
    "allow": ("Allow", "İzin ver"),
    "deny": ("Don't allow", "İzin verme"),
    "action_done": ("Done", "Yapıldı"),
    "action_denied": ("Not allowed", "İzin verilmedi"),
    "action_failed": ("Couldn't do it", "Yapılamadı"),
    "action_running": ("Working…", "Yapılıyor…"),
    "act_get_system_info": ("Look at this PC's details", "Bu bilgisayarın ayrıntılarına bak"),
    "act_search_files": ("Search your files for \"{query}\"", "Dosyalarınızda \"{query}\" ara"),
    "act_open_app": ("Open {name}", "{name} uygulamasını aç"),
    "act_open_settings": ("Open Settings: {page}", "Ayarlar'ı aç: {page}"),
    "act_set_theme_dark": ("Switch to dark mode", "Koyu moda geç"),
    "act_set_theme_light": ("Switch to light mode", "Açık moda geç"),
    "act_set_volume": ("Set the volume to {percent}%", "Ses düzeyini %{percent} yap"),
    "act_mute": ("Mute the sound", "Sesi kapat"),
    "act_unmute": ("Unmute the sound", "Sesi aç"),
    "act_wifi_on": ("Turn on Wi-Fi", "Wi-Fi'ı aç"),
    "act_wifi_off": ("Turn off Wi-Fi", "Wi-Fi'ı kapat"),
    "act_bluetooth_on": ("Turn on Bluetooth", "Bluetooth'u aç"),
    "act_bluetooth_off": ("Turn off Bluetooth", "Bluetooth'u kapat"),
    "act_dnd_on": ("Turn on Do not disturb", "Rahatsız etmeyin'i aç"),
    "act_dnd_off": ("Turn off Do not disturb", "Rahatsız etmeyin'i kapat"),
    "act_open_url": ("Open {url}", "{url} adresini aç"),
    "act_open_folder": ("Open {folder} in File Explorer", "{folder} klasörünü Dosya Gezgini'nde aç"),
    "act_screenshot": ("Take a screenshot with Snipping Tool", "Ekran Alıntısı Aracı ile ekran görüntüsü al"),
    "act_night_on": ("Turn on night light", "Gece ışığını aç"),
    "act_night_off": ("Turn off night light", "Gece ışığını kapat"),
    "act_airplane_on": ("Turn on airplane mode", "Uçak modunu aç"),
    "act_airplane_off": ("Turn off airplane mode", "Uçak modunu kapat"),
    "act_power_mode_power_saver": ("Switch to the power saver mode", "Güç tasarrufu moduna geç"),
    "act_power_mode_balanced": ("Switch to the balanced power mode", "Dengeli güç moduna geç"),
    "act_power_mode_performance": ("Switch to the best performance mode", "En iyi performans moduna geç"),
    "act_set_brightness": ("Set the brightness to {percent}%", "Parlaklığı %{percent} yap"),
    "act_list_wifi_networks": ("Look for Wi-Fi networks", "Wi-Fi ağlarını ara"),
    "act_connect_wifi": ("Connect to the Wi-Fi network {name}", "{name} Wi-Fi ağına bağlan"),
    "act_set_wallpaper": ("Set {path} as the desktop background", "{path} resmini masaüstü arka planı yap"),
    "act_set_timezone": ("Set the time zone to {zone}", "Saat dilimini {zone} yap"),
    "act_power_lock": ("Lock the screen", "Ekranı kilitle"),
    "act_power_sleep": ("Put the PC to sleep", "Bilgisayarı uyku moduna al"),
    "act_power_sign_out": ("Sign out", "Oturumu kapat"),
    "act_power_restart": ("Restart the PC", "Bilgisayarı yeniden başlat"),
    "act_power_shut_down": ("Shut down the PC", "Bilgisayarı kapat"),
    "act_install_app": ("Install {package} (asks for the administrator's password)",
                        "{package} paketini yükle (yönetici parolası sorulur)"),
    "act_uninstall_app": ("Uninstall {package} (asks for the administrator's password)",
                          "{package} paketini kaldır (yönetici parolası sorulur)"),
    "act_install_updates": ("Install all updates (asks for the administrator's password)",
                            "Tüm güncelleştirmeleri yükle (yönetici parolası sorulur)"),
    "act_create_folder": ("Create the folder {path}", "{path} klasörünü oluştur"),
    "act_move_to_recycle_bin": ("Move {path} to the Recycle Bin", "{path} öğesini Geri Dönüşüm Kutusu'na taşı"),
    "act_empty_recycle_bin": ("Empty the Recycle Bin", "Geri Dönüşüm Kutusu'nu boşalt"),
    "act_open_file": ("Open {path}", "{path} dosyasını aç"),
    "act_read_text_file": ("Read {path}", "{path} dosyasını oku"),
    "act_write_text_file": ("Write {path}", "{path} dosyasını yaz"),
    "act_run_command": ("Run this command:\n{command}", "Bu komutu çalıştır:\n{command}"),
    "act_run_command_admin": ("Run this command as administrator (asks for the password):\n{command}",
                              "Bu komutu yönetici olarak çalıştır (parola sorulur):\n{command}"),
    # Errors
    "error_key": ("The service didn't accept the API key. Check it in Settings.",
                  "Hizmet API anahtarını kabul etmedi. Ayarlar'dan denetleyin."),
    "error_rate": ("The service is busy or your quota is used up. Try again in a moment.",
                   "Hizmet meşgul ya da kotanız doldu. Biraz sonra yeniden deneyin."),
    "error_network": ("Can't reach the service. Check your internet connection.",
                      "Hizmete ulaşılamıyor. İnternet bağlantınızı denetleyin."),
    "error_model": ("The service doesn't know this model. Choose another one in Settings.",
                    "Hizmet bu modeli tanımıyor. Ayarlar'dan başka bir model seçin."),
    "error_other": ("Something went wrong: {detail}", "Bir sorun oluştu: {detail}"),
    "refused": ("The model declined to answer this request.", "Model bu isteği yanıtlamayı reddetti."),
    "stopped": ("Stopped.", "Durduruldu."),
    "command_done": ("Done.", "Tamam, yapıldı."),
    "no_key": ("Choose a service and enter your API key to start.",
               "Başlamak için bir hizmet seçin ve API anahtarınızı girin."),
}

FOLDERS = {
    "home": ("your home folder", "giriş klasörünüz"), "desktop": ("Desktop", "Masaüstü"),
    "documents": ("Documents", "Belgeler"), "downloads": ("Downloads", "İndirilenler"),
    "pictures": ("Pictures", "Resimler"), "music": ("Music", "Müzik"), "videos": ("Videos", "Videolar"),
    "this_pc": ("This PC", "Bu bilgisayar"), "recycle_bin": ("Recycle Bin", "Geri Dönüşüm Kutusu"),
}


def language(environ=None):
    environ = os.environ if environ is None else environ
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = environ.get(variable)
        if value:
            return "tr" if value.lower().startswith("tr") else "en"
    return "en"


def text(lang, key, **values):
    pair = TEXTS[key]
    result = pair[1] if lang == "tr" else pair[0]
    return result.format(**values) if values else result
