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
